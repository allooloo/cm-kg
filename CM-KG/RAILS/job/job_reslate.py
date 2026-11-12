r"""job_reslate.py — RESLATE-01 (2026-11-12): one estate, one schedule. The one job (cmkg-apex-rail, Saturday 06:00 UTC — after every market's Friday close in
its own time zone: by then it is Saturday in every market on the roster) that re-slates the whole Allooloo estate, and writes the one digest.
  1  the Tavily meter. $500 per run (RESLATE_TAVILY_USD) = 62,500 credits at $0.008: the account counter is read (GET /usage, free) and every market job's
     guard is given TAVILY_ACCOUNT_CEILING = counter + 62,500, so the whole run stops at the meter wherever it is reached. Each market keeps its own
     approved run ceiling inside that.
  2  YIELD FIRST. Markets are started in order of yield — records and events on the door per credit of the market's run ceiling, highest first — so if the
     meter is reached the reads that return least are the ones left. The unread set (each guard's denied count, per market) is the tail: named in the
     digest, picked up by the next run in the same order.
  3  every market's job (cmkg-<cc>-rail) is started for NIGHT (this job's UTC date; market date = the market's last trading day before it, the Friday close),
     Fill + Confirm depth, an eight-day window; each runs its sweep, publishes its door and runs its Data Research chain (pull, roll-up, coverage, writer).
     The Perplexity meter of the coverage read ($500 per run, RESLATE_PPLX_USD) is shared out by issuers on the record; yield first inside each market.
  4  waits for every market to end (done / failed / skipped marker), then the estate's other re-slates are started (ECO rebuild and refresh, the Book of
     Markets, Book of Operations, each market's backfill) — the jobs that used to carry their own clocks.
  5  the apex: job_apex.py for NIGHT (index, router, estate pages, sweepREVIEW).
  6  the page store: publish_stores.py (the research pages each market wrote) — needs the page-store token (CLOUDFLARE_KV_TOKEN); without it the pages
     stay written in the stores and the digest says so.
  7  the digest: order lines (ops/digest/lines/<night>/) for the re-slate, the Tavily and Perplexity $ and tails, the research pages; then job_digest.py.
Environment: NIGHT (override), RESLATE_ONLY (comma list of markets), RESLATE_DRY=1 (plan only: nothing started), RESLATE_WAIT_HOURS (default 11),
RESLATE_SKIP (apex,others,publish,digest). Exit 1 when a market failed or the apex failed; the digest is written either way."""
import os, sys, json, time, subprocess, datetime, traceback
ROOT = os.environ.get('CMKG_ROOT', '/job/ALLOOLOO'); RAILS = f'{ROOT}/CM-KG/RAILS'; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import roster
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
T0 = datetime.datetime.now(datetime.timezone.utc); NIGHT = os.environ.get('NIGHT') or T0.date().isoformat(); datetime.date.fromisoformat(NIGHT)
DRY = os.environ.get('RESLATE_DRY') == '1'; ONLY = [x for x in (os.environ.get('RESLATE_ONLY') or '').split(',') if x]; SKIP = set((os.environ.get('RESLATE_SKIP') or '').split(','))
TAV_USD = float(os.environ.get('RESLATE_TAVILY_USD', '500')); USD_PER_CREDIT = 0.008; TAV_CREDITS = int(TAV_USD / USD_PER_CREDIT); PPLX_USD = float(os.environ.get('RESLATE_PPLX_USD', '500'))
WAIT_H = float(os.environ.get('RESLATE_WAIT_HOURS', '11')); APEX_SA = os.environ.get('APEX_STORAGE_ACCOUNT', 'allooloocmkgapex'); PY = '/usr/local/bin/python3' if os.name != 'nt' else sys.executable
OTHERS = [('cmkg-eco-ops', 'allooloo-cmkg-eastus'), ('eco-refresh', 'allooloo-cmkg-eastus'), ('book-of-markets', 'allooloo-cmkg-shared'), ('bookops-weekly', 'allooloo-cmkg-shared')]
os.environ.setdefault('AZURE_CONFIG_DIR', '/tmp/.azure'); os.environ['AZURE_CORE_COLLECT_TELEMETRY'] = 'false'; LOG = []
def log(*a):
    s = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')} " + ' '.join(str(x) for x in a); print(s, flush=True); LOG.append(s)
def az(*a, raw=False, check=True):
    p = subprocess.run((['az'] if os.name != 'nt' else [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']) + list(a) + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0:
        if check: raise RuntimeError(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-300:]}")
        return None
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
from azure.storage.blob import BlobServiceClient, ContentSettings
_K = {}
def cont(sa, rg, name):
    if sa not in _K: _K[sa] = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', rg, '--query', '[0].value', '-o', 'tsv', raw=True)
    return BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=_K[sa]).get_container_client(name)
def gj(c, name):
    try: return json.loads(c.get_blob_client(name).download_blob().readall().decode('utf-8'))
    except Exception: return None
def put(c, name, data, ct='text/plain'): c.upload_blob(name, data.encode('utf-8') if isinstance(data, str) else data, overwrite=True, content_settings=ContentSettings(content_type=ct))
def tavily_used():
    try:
        import urllib.request
        j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + os.environ.get('TAVILY_API_KEY', '')}), timeout=30).read()); a = j.get('account') or {}
        return (a.get('plan_usage') or 0) + (a.get('paygo_usage') or 0), a
    except Exception as e: return None, {'error': repr(e)[:120]}
def main():
    log(f'RESLATE-01 the one job: night {NIGHT}, Tavily meter ${TAV_USD:.0f} = {TAV_CREDITS} credits, Perplexity meter ${PPLX_USD:.0f}{" — DRY: nothing is started" if DRY else ""}')
    if os.name != 'nt': az('login', '--identity', raw=True); az('account', 'set', '-s', SUB, raw=True)
    acct = az('account', 'show')
    if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
    nodes = [(roster.cc_of(n), (n.get('region') or {}).get('store'), n) for n in roster.load()]
    if ONLY: nodes = [x for x in nodes if x[0] in ONLY]
    S = {'order': 'RESLATE-01', 'night': NIGHT, 'started_utc': T0.isoformat(), 'tavily': {'meter_usd': TAV_USD, 'meter_credits': TAV_CREDITS}, 'perplexity': {'meter_usd': PPLX_USD}, 'markets': {}, 'others': {}}
    used0, acc = tavily_used(); S['tavily']['account_at_start'] = acc; ceiling = (used0 + TAV_CREDITS) if used0 is not None else None; S['tavily']['account_ceiling_set'] = ceiling
    log('Tavily account counter at start:', used0, '-> the run stops at', ceiling)
    # yield order: what a market's door holds per credit of its run ceiling, highest first
    plan = []; tot_rec = sum(int(n.get('records') or 0) for _, _, n in nodes) or 1
    for cc, reg, n in nodes:
        rg = f'allooloo-cmkg-{reg}'; job = f'cmkg-{cc}-rail'; j = az('containerapp', 'job', 'show', '-n', job, '-g', rg, check=False)
        if not j: S['markets'][cc] = {'state': 'no job'}; log(cc, 'no job', job); continue
        env = {e['name']: e.get('value') for e in j['properties']['template']['containers'][0].get('env', [])}; rc = int(env.get('TAVILY_RUN_CEILING') or 0)
        y = (int(n.get('records') or 0) + int(n.get('events') or 0) / 100.0) / max(rc, 1)
        plan.append({'cc': cc, 'rg': rg, 'job': job, 'store': f'allooloocmkg{cc}pond', 'run_ceiling': rc, 'yield': round(y, 3), 'records_before': int(n.get('records') or 0), 'events_before': int(n.get('events') or 0), 'as_of_before': n.get('as_of'), 'pplx_meter': round(PPLX_USD * int(n.get('records') or 0) / tot_rec, 2)})
    plan.sort(key=lambda p: (-p['yield'], p['cc'])); S['yield_order'] = [p['cc'] for p in plan]; log('yield order:', ' '.join(S['yield_order']))
    if DRY: print(json.dumps({'plan': plan, 'tavily': S['tavily']}, indent=1)); return 0
    for p in plan:
        envs = [f'NIGHT={NIGHT}', 'FILL_CONFIRM=1', 'NIGHTLY_WINDOW_DAYS=8', f"RESEARCH_PPLX_METER={p['pplx_meter']}", 'RESEARCH_CHAIN=1'] + ([f'TAVILY_ACCOUNT_CEILING={ceiling}'] if ceiling else [])
        try:
            az('containerapp', 'job', 'update', '-n', p['job'], '-g', p['rg'], '--set-env-vars', *envs)
            x = az('containerapp', 'job', 'start', '-n', p['job'], '-g', p['rg']); p['execution'] = x.get('name') or x.get('id', '').split('/')[-1]; log(p['cc'], 'started', p['execution'], 'run ceiling', p['run_ceiling'], 'yield', p['yield'])
        except Exception as e: p['start_error'] = repr(e)[:300]; log(p['cc'], 'NOT STARTED', p['start_error'])
        time.sleep(8)
    deadline = time.time() + WAIT_H * 3600; left = [p for p in plan if p.get('execution')]
    while left and time.time() < deadline:
        time.sleep(240); nxt = []
        for p in left:
            c = cont(p['store'], p['rg'], 'pond'); d = gj(c, f"sweeps/{NIGHT}/{p['cc']}/done.json"); f = None if d else gj(c, f"sweeps/{NIGHT}/{p['cc']}/failed.json"); s_ = None if (d or f) else gj(c, f"sweeps/{NIGHT}/{p['cc']}/skipped.json")
            if d: p['done'] = d; log(p['cc'], 'landed', d.get('records'), d.get('events'), 'held' if d.get('held') else '')
            elif f: p['failed'] = f; log(p['cc'], 'FAILED', str(f.get('error'))[:160])
            elif s_: p['skipped'] = s_; log(p['cc'], 'skipped', s_.get('why'))
            else:
                try: st = az('containerapp', 'job', 'execution', 'show', '-n', p['job'], '-g', p['rg'], '--job-execution-name', p['execution'], check=False); st = ((st or {}).get('properties') or {}).get('status')
                except Exception: st = None
                if st in ('Failed', 'Stopped', 'Degraded'): p['failed'] = {'error': f'execution {st} with no marker'}; log(p['cc'], 'FAILED (execution', st, ', no marker)')
                else: nxt.append(p)
        left = nxt
    for p in left: p['failed'] = {'error': f'no marker after {WAIT_H} hours'}; log(p['cc'], 'did not land in', WAIT_H, 'hours')
    for p in plan:   # the per-run settings come off the jobs: the next run sets its own
        az('containerapp', 'job', 'update', '-n', p['job'], '-g', p['rg'], '--remove-env-vars', 'NIGHT', 'FILL_CONFIRM', 'NIGHTLY_WINDOW_DAYS', 'RESEARCH_PPLX_METER', check=False)
    used1, acc1 = tavily_used(); S['tavily']['account_at_end'] = acc1; cr = (used1 - used0) if used0 is not None and used1 is not None else None
    tail_t = []; tail_p = []; pp_usd = 0.0; pp_calls = 0; pages = 0; pg_changed = 0; pg_new = 0; rs_fail = []
    for p in plan:
        d = p.get('done') or {}; g = d.get('tavily_guard') or {}; r = d.get('research') or {}; cv = r.get('coverage') or {}; pg = r.get('pages') or {}
        if g.get('denied'): tail_t.append(f"{p['cc']} {g['denied']} reads" + (f" ({g['stopped']})" if g.get('stopped') else ''))
        if cv.get('tail_unread'): tail_p.append(f"{p['cc']} {cv['tail_unread']} issuers")
        pp_usd += cv.get('perplexity_usd') or 0; pp_calls += cv.get('perplexity_calls') or 0; pages += pg.get('pages') or 0; pg_changed += pg.get('changed') or 0; pg_new += pg.get('new') or 0
        if p.get('done') and not d.get('held') and not r.get('ok'): rs_fail.append(p['cc'])
        S['markets'][p['cc']] = {'state': 'landed' if p.get('done') else 'failed' if p.get('failed') else 'skipped' if p.get('skipped') else 'not started', 'held': bool(d.get('held')), 'records_before': (d.get('served_before') or {}).get('records', p['records_before']), 'records': d.get('records'), 'events_before': (d.get('served_before') or {}).get('events', p['events_before']), 'events': d.get('events'),
                                 'as_of_before': (d.get('served_before') or {}).get('as_of', p['as_of_before']), 'as_of': d.get('as_of'), 'market_date': d.get('market_date'), 'tavily_guard': g, 'research': {'ok': r.get('ok'), **pg, 'coverage': cv, 'error': r.get('error') or r.get('failed')}, 'error': (p.get('failed') or {}).get('error') or p.get('start_error'), 'execution': p.get('execution'), 'yield': p['yield']}
    S['tavily'].update({'credits_this_run': cr, 'usd_this_run': round(cr * USD_PER_CREDIT, 2) if cr is not None else None, 'tail': tail_t}); S['perplexity'].update({'calls': pp_calls, 'usd': round(pp_usd, 2), 'tail': tail_p})
    landed = [c for c, m in S['markets'].items() if m['state'] == 'landed']; failed = [c for c, m in S['markets'].items() if m['state'] in ('failed', 'not started')]; held = [c for c, m in S['markets'].items() if m.get('held')]
    if 'others' not in SKIP:
        for job, rg in OTHERS + [(f"cmkg-{p['cc']}-backfill", p['rg']) for p in plan if p.get('done')]:
            x = az('containerapp', 'job', 'start', '-n', job, '-g', rg, check=False); S['others'][job] = (x or {}).get('name') or 'not started'
        log('other re-slates started:', sum(1 for v in S['others'].values() if v != 'not started'), 'of', len(S['others']))
    apex_rc = None
    if 'apex' not in SKIP:
        apex_rc = subprocess.run([PY, f'{RAILS}/job/job_apex.py'], env={**os.environ, 'NIGHT': NIGHT, 'APEX_WAIT_UNTIL': '00:00'}).returncode; log('apex exit', apex_rc)
    S['apex_exit'] = apex_rc
    if 'publish' not in SKIP:
        if os.environ.get('CLOUDFLARE_KV_TOKEN'):
            r = subprocess.run([PY, '-X', 'utf8', f'{RAILS}/research/publish_stores.py', NIGHT] + landed, capture_output=True, text=True, encoding='utf-8', errors='replace'); S['publish'] = {'exit': r.returncode, 'last': (r.stdout or '').strip().splitlines()[-1:]}; log('page store publish exit', r.returncode)
        else: S['publish'] = {'exit': None, 'note': 'not published: no page-store token (CLOUDFLARE_KV_TOKEN) in this job; the pages are written in each market store (research/state/pages.jsonl)'}; log(S['publish']['note'])
    S['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ops = cont(APEX_SA, 'allooloo-cmkg-shared', os.environ.get('OPS_CONTAINER', 'ops'))
    L = {'10-reslate.txt': f"RESLATE {NIGHT}: {len(landed)} of {len(plan)} markets landed" + (f" · held {' '.join(held)}" if held else '') + (f" · FAILED {' '.join(failed)}" if failed else '') + f" · apex {'ok' if apex_rc == 0 else 'not run' if apex_rc is None else 'FAILED'} · one job (cmkg-apex-rail), next run the Saturday after",
         '20-tavily.txt': f"Tavily this run: {cr if cr is not None else 'not read'} credits" + (f" = ${cr * USD_PER_CREDIT:.2f}" if cr is not None else '') + f" of the ${TAV_USD:.0f} meter · tail (unread at the meter or the ceiling): " + ('; '.join(tail_t) if tail_t else 'none'),
         '30-research.txt': f"Data Research: {pages} pages in {sum(1 for m in S['markets'].values() if (m.get('research') or {}).get('ok'))} markets ({pg_new} new, {pg_changed} rewritten on change)" + (f" · chain FAILED in {' '.join(rs_fail)}" if rs_fail else '') + f" · Perplexity {pp_calls} calls ${pp_usd:.2f} of the ${PPLX_USD:.0f} meter · tail: " + ('; '.join(tail_p) if tail_p else 'none') + ' · page store: ' + ('published' if (S.get('publish') or {}).get('exit') == 0 else 'NOT published (' + str((S.get('publish') or {}).get('note') or (S.get('publish') or {}).get('exit')) + ')')}
    for k, v in L.items(): put(ops, f"digest/{'lines-partial' if ONLY else 'lines'}/{NIGHT}/{k}", v + '\n')   # a partial run (RESLATE_ONLY) is not the estate's line
    put(ops, f'{NIGHT}/RESLATE-{NIGHT}.json', json.dumps(S, ensure_ascii=False, indent=1), 'application/json'); put(ops, f'{NIGHT}/reslate-job.log', '\n'.join(LOG) + '\n')
    for v in L.values(): log(v)
    if 'digest' not in SKIP:
        rc = subprocess.run([PY, f'{RAILS}/job/job_digest.py'], env={**os.environ, 'NIGHT': NIGHT, 'MODE': 'daily', 'OPS_CONTAINER': os.environ.get('OPS_CONTAINER', 'ops')}).returncode; log('digest exit', rc)
    return 1 if failed or (apex_rc not in (0, None)) else 0
if __name__ == '__main__':
    try: rc = main()
    except SystemExit as e: rc = e.code if isinstance(e.code, int) else 1; log('STOP', e)
    except Exception as e: rc = 1; log('FAILED', repr(e)[:400]); log(traceback.format_exc()[-1500:])
    sys.exit(rc)
