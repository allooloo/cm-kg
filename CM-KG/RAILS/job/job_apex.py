r"""ORDER-031 (2026-10-17) — the apex job (East US, shared resource group), fired later the same Friday (CEO clock) after the eleven node jobs.
Reads the eleven done-markers (sweeps/<market date>/<cc>/done.json in each node's store); rebuilds the apex index for every node that landed
(build_index.py reads every regional store's door/ files as they stand, so a node with no marker keeps last week's as_of on the wire); deploys
the apex and the estate (wrangler, non-interactive); appends the nodes' NUMBERS LOG and SPEND lines; snapshots the surfaces; writes the sweep
close line and sweepREVIEW-<market date>.md (machine half from the job logs, X line STAGED, never posted) and lands all of it in the shared apex
store (sweeps/<market date>/...) and, when enabled, the apex ark bucket. The laptop pulls the same files into the repo with pull_sweep.py.
No fallback, no retry: a node without a marker is written as "did not land". A missing ark object is a failed close."""
import os, sys, json, subprocess, datetime, re, io, traceback
ROOT = os.environ.get('CMKG_ROOT', '/job/ALLOOLOO'); RAILS = f'{ROOT}/CM-KG/RAILS'; HERE = os.path.dirname(os.path.abspath(__file__))
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
NODES_TYPED_BEFORE_ENUM01 = [('nl', 'westeurope'), ('ch', 'switzerlandnorth'), ('fr', 'francecentral'), ('de', 'germanywestcentral'), ('sg', 'southeastasia'), ('au', 'australiaeast'), ('uk', 'uksouth'), ('ca', 'canadacentral'), ('jp', 'japaneast'), ('kr', 'koreacentral'), ('us', 'eastus'), ('hk', 'eastasia')]   # hk: ORDER-035 (2026-10-22)
# NODE-EU (DAY ORDER 4, 2026-10-24): the European nodes join here when their door is live (RAILS\eu-node\live.json: {cc: region})
import json as _j
# ENUM-01 (DAY ORDER 6, 2026-10-25): the nodes are the roster of record (list_nodes / nodes.json); the typed list above is kept as the record of what it was
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import roster   # ENUM-01 (DAY ORDER 6): the roster of record
NODES = [(roster.cc_of(n), (n.get('region') or {}).get('store')) for n in roster.load()]
DRY = os.environ.get('APEX_DRY', '0') == '1'   # dry run: build and report from the staging markers, deploy nothing, write under dry/<date>/, no ark
CONT = os.environ.get('STORAGE_CONTAINER', 'pond'); APEX_SA = os.environ.get('APEX_STORAGE_ACCOUNT', 'allooloocmkgapex'); APEX_CONT = os.environ.get('APEX_CONTAINER', 'sweeps')
T0 = datetime.datetime.now(datetime.timezone.utc); TODAY = T0.date()
def friday_on_or_before(d): return d - datetime.timedelta(days=(d.weekday() - 4) % 7)
# ORDER-036 NIGHTLY (2026-10-22): the apex fires every night after the last region; NIGHT = its UTC date = every node's local date at its own 02:00 fire;
# the markers it reads are sweeps/<night>/<cc>/; MDATE = the last trading date before the night (weekends roll back to Friday), the as_of every node stamps
def last_trading(d):
    while d.weekday() >= 5: d -= datetime.timedelta(days=1)
    return d
NIGHT = os.environ.get('NIGHT') or TODAY.isoformat()
MDATE = os.environ.get('MARKET_DATE') or last_trading(datetime.date.fromisoformat(NIGHT) - datetime.timedelta(days=1)).isoformat()
EXEC = os.environ.get('CONTAINER_APP_JOB_EXECUTION_NAME', os.environ.get('HOSTNAME', '?')); IMAGE_TAG = os.environ.get('IMAGE_TAG', '?')
os.environ.setdefault('AZURE_CONFIG_DIR', '/tmp/.azure'); os.environ['AZURE_CORE_COLLECT_TELEMETRY'] = 'false'
LOG = []
def log(*a):
    s = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')} " + ' '.join(str(x) for x in a); print(s, flush=True); LOG.append(s)
def sh(args, cwd=None, env=None, check=True):
    p = subprocess.Popen(args, cwd=cwd, env={**os.environ, **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    out = []
    for line in p.stdout:
        line = line.rstrip('\n'); out.append(line)
        if line: log('  ' + line)
    rc = p.wait()
    if check and rc != 0: raise RuntimeError(f"{' '.join(str(a) for a in args[:3])} exit {rc}")
    return rc, '\n'.join(out)
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0: raise RuntimeError(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-400:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
from azure.storage.blob import BlobServiceClient, ContentSettings
def client(sa, key, cont): return BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client(cont)
def get_json(c, name):
    try: return json.loads(c.get_blob_client(name).download_blob().readall().decode('utf-8'))
    except Exception: return None
def put(c, name, data, ct='application/json'):
    c.upload_blob(name, data.encode('utf-8') if isinstance(data, str) else data, overwrite=True, content_settings=ContentSettings(content_type=ct))

def main():
    log(f'ORDER-036 nightly apex job: night {NIGHT}, market date {MDATE}, node container {CONT}, image {IMAGE_TAG}, execution {EXEC}{" — DRY RUN: nothing deployed, nothing written to the ark" if DRY else ""}')
    sh(['az', 'login', '--identity', '-o', 'none']); sh(['az', 'account', 'set', '-s', SUB])
    acct = az('account', 'show')
    if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
    markers = {}; failed = {}; skipped = {}
    for cc, reg in NODES:
        sa = f'allooloocmkg{cc}pond'; key = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', f'allooloo-cmkg-{reg}', '--query', '[0].value', '-o', 'tsv', raw=True)
        c = client(sa, key, CONT); d = get_json(c, f'sweeps/{NIGHT}/{cc}/done.json')
        if d: markers[cc] = d
        else:
            f = get_json(c, f'sweeps/{NIGHT}/{cc}/failed.json'); s = get_json(c, f'sweeps/{NIGHT}/{cc}/skipped.json')
            if f: failed[cc] = f
            if s: skipped[cc] = s
        log(f"{cc}: {'landed' if cc in markers else ('FAILED' if cc in failed else ('skipped' if cc in skipped else 'did not land'))}")
    # apex index for every node that landed; nodes without a marker keep last week's door files (build_index reads the stores as they stand)
    sh(['/usr/local/bin/python3', 'build_index.py'], cwd=f'{ROOT}/CM-KG/DOOR/apex')
    # SHELF-01 step 6 (2026-10-27): the shelf lights itself as each market seals — Replay, Score, Bench, Review per the ledger (holds in shelf/hold.json)
    rc_shelf = sh(['/usr/local/bin/python3', '-X', 'utf8', 'auto.py'], cwd=f'{ROOT}/CM-KG/RAILS/shelf', check=False); log('shelf auto exit', rc_shelf if not isinstance(rc_shelf, tuple) else rc_shelf[0])
    apex_dep = 'Version ID: dry-run-not-deployed' if DRY else sh(['npx', '--yes', 'wrangler', 'deploy'], cwd=f'{ROOT}/CM-KG/DOOR/apex', check=False)[1]; apex_ver = (re.search(r'Version ID:\s*([0-9a-f-]+)', apex_dep) or re.search(r'Current Version ID:\s*([0-9a-f-]+)', apex_dep) or [None, 'see log'])[1]
    # NUMBERS LOG: the nodes' own lines (computed against what each door served before the upload), appended to the boot block; the asset mirrored
    boot = f'{ROOT}/START_ME_UP/NODE-SURFACES.md'; s = open(boot, encoding='utf-8').read(); m = re.search(r'(## 9 NUMBERS LOG[\s\S]*?```\n)([\s\S]*?)(```)', s)
    lines = [l for l in m.group(2).splitlines() if l.strip()]; added = []
    for cc, _ in NODES:
        if cc in markers and markers[cc].get('numbers_line') and markers[cc]['numbers_line'] not in lines: lines.append(markers[cc]['numbers_line']); added.append(markers[cc]['numbers_line'])
    s = s[:m.start(2)] + '\n'.join(lines) + '\n' + s[m.start(3):]; open(boot, 'w', encoding='utf-8').write(s)
    sh(['/usr/local/bin/python3', 'numbers_log.py'], cwd=RAILS, check=False)   # mirror only -> CM-KG/ESTATE/public/numbers-log.json
    # ORDER-032 C.4: the agent-swap logs of record live in the shared apex store (sweeps/swap/); pull them before the estate deploy so a Friday deploy never
    # rolls back a swap logged since the image was built, add tonight's ark writes, write ark.json back (dry run: read only, nothing written back)
    try:
        akey = az('storage', 'account', 'keys', 'list', '-n', APEX_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True); ac = client(APEX_SA, akey, APEX_CONT)
        swd = f'{ROOT}/CM-KG/ESTATE/public/swap'; os.makedirs(swd, exist_ok=True)
        for fn in ('swaps.json', 'ark.json'):
            j = get_json(ac, f'swap/{fn}')
            if j is not None: json.dump(j, open(f'{swd}/{fn}', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        arkp = f'{swd}/ark.json'; arkj = json.load(open(arkp, encoding='utf-8')) if os.path.exists(arkp) else {'about': 'last write of each node record to its ark bucket (AWS); written at the sweep close and by the backfill', 'nodes': {}}
        for cc_, _ in NODES:
            a_ = (markers.get(cc_) or {}).get('ark') or {}
            if a_.get('enabled') and a_.get('objects') and not a_.get('error'):
                arkj['nodes'][f'{cc_}-cm-kg'] = {'last_write': TODAY.isoformat(), 'bucket': a_['objects'][0]['bucket'], 'objects': len(a_['objects']), 'market_date': MDATE}
        json.dump(arkj, open(arkp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        if not DRY: put(ac, 'swap/ark.json', json.dumps(arkj, ensure_ascii=False, indent=1))
        log('agent-swap logs pulled from the apex store; ark.json', 'updated' if not DRY else 'read (dry)')
    except Exception as e: log('agent-swap logs not refreshed (flag):', repr(e)[:200])
    # SPEND: the nodes' lines + the run-level Tavily reading (start = the last reading in SPEND.md, end = now)
    md = f'{ROOT}/CM-KG/SPEND/SPEND.md'; spend = []
    for cc, _ in NODES:
        for l in (markers.get(cc) or {}).get('spend_lines') or []: spend.append(l)
    tav = None
    try:
        import requests
        r = requests.get('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + os.environ.get('TAVILY_API_KEY', '')}, timeout=30)
        jj = r.json() if r.status_code == 200 else {}; j = jj.get('account', {}); tav = int(j['plan_usage']) if j.get('plan_usage') is not None else None
        if jj: json.dump(jj, open('/tmp/tavily-usage.json', 'w', encoding='utf-8'))   # RADAR-02: the meter answer (spend.json no longer written, RADAR-01)
    except Exception: pass
    prev = re.findall(r'plan ([\d,]+) of', open(md, encoding='utf-8').read()) if os.path.exists(md) else []
    prev = int(prev[-1].replace(',', '')) if prev else None
    if tav is not None: spend.append(f"sweep {MDATE} · Tavily (run level) · {(tav - prev) if prev is not None else '?'} credits used · plan {tav:,} of 200,000, {200000 - tav:,} remaining · meter: GET /usage plan counter read by the apex job at close{' (estimated: start = last SPEND.md reading)' if prev is not None else ''}")
    else: spend.append(f'sweep {MDATE} · Tavily (run level) · counter not read at close (flag) · no figure written')
    if os.path.exists(md):
        t = open(md, encoding='utf-8').read(); i = t.rstrip().rfind('```')
        t = t[:i] + '\n'.join(spend) + '\n' + t[i:]; open(md, 'w', encoding='utf-8').write(t)
    # RADAR-02 (2026-10-23): RADAR §09 read nightly — filings.json rewritten from what answers, written before the estate deploy so tonight's deploy carries it.
    # RADAR-01 (2026-10-26): spend is no longer written into the public estate (spend_json.py not run here; SPEND.md stays in cm-kg-ops)
    sh(['/usr/local/bin/python3', 'filings_json.py'], cwd=RAILS, check=False)
    estate_dep = 'Version ID: dry-run-not-deployed' if DRY else sh(['npx', '--yes', 'wrangler', 'deploy'], cwd=f'{ROOT}/CM-KG/ESTATE', check=False)[1]; estate_ver = (re.search(r'Version ID:\s*([0-9a-f-]+)', estate_dep) or re.search(r'Current Version ID:\s*([0-9a-f-]+)', estate_dep) or [None, 'see log'])[1]
    # surfaces snapshot to the pond (estate), uploaded to the shared store
    sh(['/usr/local/bin/python3', 'snapshot_surfaces.py'], cwd=RAILS, check=False)
    # sweepREVIEW — machine half from the job logs
    rows = []; tot_r = tot_e = 0
    for cc, reg in NODES:
        if cc in markers:
            d = markers[cc]; rows.append(f"| {cc}-cm-kg | {d.get('as_of') or MDATE} | {d['records']:,} | {d['events']:,} | records {d['records_delta']:+d} · events {d['events_delta']:+d}{' · HELD' if d.get('held') else ''} |"); tot_r += d['records']; tot_e += d['events']
        else: rows.append(f"| {cc}-cm-kg | — | — | — | did not land ({'failed: ' + (failed[cc].get('error') or '')[:80] if cc in failed else ('skipped: ' + skipped[cc].get('why', '') if cc in skipped else 'no marker')}) — the wire keeps last week's as_of |")
    held = [f"- {cc}-cm-kg: {markers[cc]['held_flag'].strip()}" for cc, _ in NODES if markers.get(cc, {}).get('held_flag')]
    ark_lines = []; ark_ok = True
    for cc, _ in NODES:
        a = (markers.get(cc) or {}).get('ark') or {}
        if not a.get('enabled'): ark_lines.append(f'- {cc}-cm-kg: ark not enabled'); continue
        if a.get('error') or not a.get('objects'): ark_ok = False; ark_lines.append(f"- {cc}-cm-kg: ARK FAILED — {a.get('error') or 'no objects'}")
        else: ark_lines.append(f"- {cc}-cm-kg: " + '; '.join(f"s3://{o['bucket']}/{o['key']} v={o['version_id']}" for o in a['objects']))
    landed = [cc for cc, _ in NODES if cc in markers]
    close = f"SWEEP CLOSE {MDATE} · {len(landed)} of {len(NODES)} landed ({' '.join(landed) or 'none'}) · {tot_r:,} records · {tot_e:,} events on the landed doors · apex {apex_ver} · estate {estate_ver} · ark {'complete' if ark_ok and any((markers.get(cc) or {}).get('ark', {}).get('enabled') for cc, _ in NODES) else ('FAILED CLOSE' if not ark_ok else 'not enabled')}"
    x_line = f"get_issuer · sweep of {MDATE} · {len(landed)}/{len(NODES)} markets · {tot_r:,} issuers · {tot_e:,} disclosure events · one date on every door · https://getissuer.ai"
    rep = [f'# sweepREVIEW · night of {NIGHT} · market date {MDATE} · reviewed ', '', f'*(Machine half written by the apex job {EXEC} on {TODAY.isoformat()}, image {IMAGE_TAG}. The reviewed date is written by the CEO go. Human half: X line, spend, zones, deletions, rules, registry publishes.)*', '',
           '## Doors (from the node jobs\' done-markers)', '', '| node | as of | records | events | this sweep |', '|---|---|---|---|---|', *rows, '', f'**Close line:** {close}', '',
           '## NUMBERS LOG lines written', '', '```', *(added or ['(no new lines)']), '```', '', '## SPEND lines written', '', '```', *spend, '```', '',
           '## Flags', '', *(held or ['- no door held']), *([f"- {cc}-cm-kg FAILED: {failed[cc].get('error')}" for cc in failed]), *([f"- {cc}-cm-kg skipped: {skipped[cc].get('why')}" for cc in skipped]), '',
           '## Ark (AWS)', '', *ark_lines, '', '## X line (STAGED — the CEO posts from @allooloo_ai, https://x.com/allooloo_ai)', '', '```', x_line, '```', '']
    report = '\n'.join(rep); rp = f'{ROOT}/START_ME_UP/sweepREVIEW-{NIGHT}.md'; open(rp, 'w', encoding='utf-8').write(report)
    key = az('storage', 'account', 'keys', 'list', '-n', APEX_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True); c = client(APEX_SA, key, APEX_CONT)
    pre = (f'dry/{NIGHT}/' if DRY else f'{NIGHT}/')
    put(c, pre + f'sweepREVIEW-{NIGHT}.md', report, 'text/markdown'); put(c, pre + 'NODE-SURFACES.md', open(boot, encoding='utf-8').read(), 'text/markdown')
    put(c, pre + 'SPEND.md', open(md, encoding='utf-8').read(), 'text/markdown'); put(c, pre + 'numbers-log.json', open(f'{ROOT}/CM-KG/ESTATE/public/numbers-log.json', 'rb').read())
    for fn in ('index.json', 'nodes.json'): put(c, pre + f'apex-{fn}', open(f'{ROOT}/CM-KG/DOOR/apex/static/{fn}', 'rb').read())
    snaps = f'{ROOT}/CM-KG/POND/estate/surfaces'
    if os.path.isdir(snaps):
        for d in sorted(os.listdir(snaps)):
            for r_, _, fs in os.walk(os.path.join(snaps, d)):
                for f in fs:
                    p = os.path.join(r_, f); put(c, pre + 'surfaces/' + os.path.relpath(p, snaps).replace(os.sep, '/'), open(p, 'rb').read(), 'application/octet-stream')
    ark = {'enabled': os.environ.get('ARK_ENABLED', '0') == '1' and not DRY, 'objects': []}
    if ark['enabled']:
        try:
            import boto3
            s3 = boto3.client('s3', region_name=os.environ['ARK_REGION']); b = os.environ['ARK_BUCKET']
            for p, k in ((rp, f'apex/reports/sweepREVIEW-{NIGHT}.md'), (f'{ROOT}/CM-KG/DOOR/apex/static/index.json', f'apex/index/{NIGHT}/index.json'), (f'{ROOT}/CM-KG/DOOR/apex/static/nodes.json', f'apex/index/{NIGHT}/nodes.json')):   # ark layout of record (ORDER-033)
                with open(p, 'rb') as f: r = s3.put_object(Bucket=b, Key=k, Body=f)
                ark['objects'].append({'bucket': b, 'key': k, 'version_id': r.get('VersionId')})
            log(f"ark: {len(ark['objects'])} apex objects written")
        except Exception as e: ark['error'] = repr(e)[:300]; log('ark write FAILED:', ark['error']); close += ' · APEX ARK FAILED'
    done = {'night': NIGHT, 'market_date': MDATE, 'landed': landed, 'failed': list(failed), 'skipped': list(skipped), 'records': tot_r, 'events': tot_e, 'apex_version': apex_ver, 'estate_version': estate_ver, 'close_line': close, 'x_line_staged': x_line, 'ark': ark, 'image': IMAGE_TAG, 'execution': EXEC, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    put(c, pre + 'apex-done.json', json.dumps(done, ensure_ascii=False, indent=1)); log(close); log('X line STAGED:', x_line); return 0

if __name__ == '__main__':
    try: rc = main()
    except SystemExit as e: rc = e.code if isinstance(e.code, int) else 1; log('STOP', e)
    except Exception as e: rc = 1; log('FAILED', repr(e)[:400]); log(traceback.format_exc()[-2000:])
    try:
        key = az('storage', 'account', 'keys', 'list', '-n', APEX_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True)
        put(client(APEX_SA, key, APEX_CONT), (f'dry/{NIGHT}' if DRY else NIGHT) + f'/apex-job-{EXEC}.log', '\n'.join(LOG) + '\n', 'text/plain')
    except Exception: pass
    sys.exit(rc)
