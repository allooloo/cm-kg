r"""ORDER-031 (2026-10-17) — one node's weekly sweep as an Azure Container Apps Job, in that node's own region. The job image carries the
laptop rails unchanged (the sitecustomize shim translates paths and serves keys from the vault-fed environment); this runner is sweep_node.ps1
for the container: the same steps, in the same order, with the node id as the only parameter.

  harvest (<cc>-width1\run_refresh.ps1 under pwsh; Canada's script carries Fill + Confirm)  ->  pond drop (local, then uploaded)
  -> rebuild from this run's own assembly (the assembler writes a new assembled\<date>\ drop; checked)  ->  door data (load_nodes.py)
  -> forward-only gate (door_gate.py; HOLD = DOOR_HOLD, new index beside)  ->  upload (provision_region.py upload: newest drop per source + door/)
  -> door revision restart (clears the no-expiry issuer-event cache)  ->  NUMBERS LOG + SPEND lines  ->  ark write (AWS, when enabled)
  -> done-marker blob dated to the pond (sweeps/<market date>/<cc>/done.json) with the job log beside it.
United States: the same image runs us-job\us_pipeline.py (it publishes from inside the container), then the gate --after-job, the market-date
restamp, the lines and the marker — the US job is brought to the same image and schedule, nothing else.

Environment (set on the job; secrets come from the region's Key Vault through the job's managed identity, never from a file):
  NODE_CC  REGION  STORAGE_ACCOUNT  STORAGE_CONTAINER (pond | staging for the dry run)  MARKET_DATE (optional; default the Friday on or before today UTC)
  DOOR_RESTART (1|0)  ARK_ENABLED (1|0)  ARK_BUCKET  ARK_REGION  AWS_ACCESS_KEY_ID  AWS_SECRET_ACCESS_KEY  TAVILY_API_KEY  XAI_API_KEY ... (lab keys)
Reads and writes stay in-region: the pond is pulled from and pushed to the node's own store; the only cross-border calls are the rails' own
search and lab calls, one public read of the apex node list (to keep the other nodes' lines in nodes.json), and the ark write.
Never: a key printed, a drop overwritten, a retry loop around an external clock. Exit code: 0 landed (or skipped on a lock), non-zero failed."""
import os, sys, json, subprocess, datetime, time, re, shutil, tarfile, io, traceback
from concurrent.futures import ThreadPoolExecutor

ROOT = os.environ.get('CMKG_ROOT', '/job/ALLOOLOO'); RAILS = f'{ROOT}/CM-KG/RAILS'; DOOR = f'{ROOT}/CM-KG/DOOR'; POND = f'{ROOT}/CM-KG/POND'; HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.environ['NODE_CC']; REGION = os.environ['REGION']; NODE = f'{CC}-cm-kg'; RG = f'allooloo-cmkg-{REGION}'
SA = os.environ.get('STORAGE_ACCOUNT') or f'allooloocmkg{CC}pond'; CONT = os.environ.get('STORAGE_CONTAINER', 'pond')
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
IMAGE_TAG = os.environ.get('IMAGE_TAG', '?'); EXEC = os.environ.get('CONTAINER_APP_JOB_EXECUTION_NAME', os.environ.get('HOSTNAME', '?'))
T0 = datetime.datetime.now(datetime.timezone.utc); TODAY = T0.date()
def friday_on_or_before(d): return d - datetime.timedelta(days=(d.weekday() - 4) % 7)
MDATE = os.environ.get('MARKET_DATE') or friday_on_or_before(TODAY).isoformat(); datetime.date.fromisoformat(MDATE)
os.environ['SWEEP_MARKET_DATE'] = MDATE; os.environ['STORAGE_CONTAINER'] = CONT; os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['AZURE_CORE_OUTPUT'] = 'json'; os.environ['AZURE_CORE_COLLECT_TELEMETRY'] = 'false'; os.environ.setdefault('AZURE_CONFIG_DIR', '/tmp/.azure')
LOG = []; LOGF = f'/tmp/{NODE}-{MDATE}-job.log'
def log(*a):
    s = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')} " + ' '.join(str(x) for x in a); print(s, flush=True); LOG.append(s)
    open(LOGF, 'a', encoding='utf-8').write(s + '\n')
def sh(args, cwd=None, env=None, check=True, quiet=False):
    """run a command, stream its output into the log, return the exit code (raise when check and non-zero)"""
    p = subprocess.Popen(args, cwd=cwd, env={**os.environ, **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    for line in p.stdout:
        line = line.rstrip('\n')
        if line and not quiet: log('  ' + line)
    rc = p.wait()
    if check and rc != 0: raise RuntimeError(f"{' '.join(str(a) for a in args[:3])} exit {rc}")
    return rc
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0: raise RuntimeError(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-400:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)

# ---------------- store
from azure.storage.blob import BlobServiceClient, ContentSettings
_bsc = None; _key = None
def store():
    global _bsc
    if _bsc is None: _bsc = BlobServiceClient(f'https://{SA}.blob.core.windows.net', credential=_key)
    return _bsc.get_container_client(CONT)
def blob_get(name):
    try: return store().get_blob_client(name).download_blob().readall()
    except Exception: return None
def blob_put(name, data, ct='application/json', overwrite=True):
    if isinstance(data, str): data = data.encode('utf-8')
    store().upload_blob(name, data, overwrite=overwrite, content_settings=ContentSettings(content_type=ct))
def blob_json(name):
    b = blob_get(name); return json.loads(b.decode('utf-8')) if b else None

def sync_pond():
    """pull the parts of the node's pond the weekly rails read: every width0 json/jsonl, every width1 drop (no page caches), the newest assembled
    drop holding each input, and (Canada) every fill-confirm drop. The canonical ISSUERS / DISCLOSURE inputs are materialised from the newest
    assembled drop (the loader prefers the pond's copy, exactly as on the laptop). A node lock in the store (locks/<node>.lock) is honoured."""
    cc_ = store(); names = {}
    for b in cc_.list_blobs(name_starts_with='pond/'): names[b.name] = b.size
    plan = []
    want_assembled = {f'{CC}-events.jsonl', f'{CC}-issuers.xlsx', f'{CC}-ref-records.jsonl', f'{CC}-ref-events.jsonl', f'{CC}-events-width1.jsonl', f'{CC}-disclosure.xlsx'}
    newest_for = {}
    for n in names:
        parts = n.split('/')
        if len(parts) < 4: continue
        _, source, drop, *rest = parts; fn = rest[-1]; ext = fn.rsplit('.', 1)[-1].lower() if '.' in fn else ''
        if source == 'width0' and ext in ('json', 'jsonl', 'txt', 'md'): plan.append(n)
        elif source == 'width1' and ext not in ('html', 'htm', 'pdf'): plan.append(n)
        elif source == 'assembled' and fn in want_assembled and len(rest) == 1:
            k = (drop[:10], int(drop[11:] or 0))
            if fn not in newest_for or k > newest_for[fn][0]: newest_for[fn] = (k, n)
        elif source == 'fill-confirm' and CC == 'ca': plan.append(n)
    plan += [n for _, n in newest_for.values()]
    log(f'pond sync: {len(plan)} blobs of {len(names)} under pond/ (width0 json, width1 drops, newest assembled inputs{", fill-confirm" if CC == "ca" else ""})')
    def one(n):
        p = os.path.join(POND, NODE, n[len('pond/'):]); os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f: cc_.get_blob_client(n).download_blob().readinto(f)
    with ThreadPoolExecutor(max_workers=32) as ex: list(ex.map(one, plan))
    for fn, (_, n) in newest_for.items():
        src = os.path.join(POND, NODE, n[len('pond/'):])
        if fn.endswith('-issuers.xlsx'): dst = f'{ROOT}/CM-KG/ISSUERS/{fn}'
        elif fn.endswith('-events.jsonl') or fn.endswith('-events-width1.jsonl') or fn.endswith('-ref-events.jsonl') or fn.endswith('-ref-records.jsonl'): dst = f'{ROOT}/CM-KG/DISCLOSURE/events/{fn}'
        else: dst = f'{ROOT}/CM-KG/DISCLOSURE/{fn}'
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst); log(f'  canonical {fn} <- {n}')
    if blob_get(f'locks/{NODE}.lock') is not None:
        os.makedirs(os.path.join(POND, NODE), exist_ok=True); open(os.path.join(POND, NODE, '.lock'), 'w').write('store lock\n'); log('node lock present in the store: the rails will skip')
    # the loader keeps every node not loaded in this run from the previous facts/nodes: seed from the image, overlay the apex's live node list
    os.makedirs(f'{DOOR}/data', exist_ok=True)
    facts = json.load(open(os.path.join(HERE, 'seed-facts.json'), encoding='utf-8')); nodes = json.load(open(os.path.join(HERE, 'seed-nodes.json'), encoding='utf-8'))
    try:
        import requests
        r = requests.post('https://mcp.capitalmarketsknowledgegraph.ai/mcp', headers={'content-type': 'application/json', 'accept': 'application/json'}, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'list_nodes', 'arguments': {}}}, timeout=60).json()
        live = {n['node']: n for n in r['result']['structuredContent']['nodes']}
        for k, v in live.items():
            if k in facts['nodes'] and v.get('live'): facts['nodes'][k].update({kk: v[kk] for kk in ('as_of', 'records', 'events', 'issuers_with_events', 'exchanges') if kk in v})
        log(f'seed overlay: apex list_nodes read, {len(live)} nodes')
    except Exception as e: log('seed overlay: apex not read, image seed kept:', repr(e)[:120])
    json.dump(facts, open(f'{DOOR}/data/facts.json', 'w', encoding='utf-8'), indent=1); json.dump(nodes, open(f'{DOOR}/data/nodes.json', 'w', encoding='utf-8'), indent=1)

def newest_drop(source):
    base = os.path.join(POND, NODE, source)
    if not os.path.isdir(base): return None
    ds = [d for d in os.listdir(base) if re.match(r'^\d{4}-\d{2}-\d{2}(-\d+)?$', d)]
    return max(ds, key=lambda d: (d[:10], int(d[11:] or 0))) if ds else None
def counts(facts):
    n = ((facts or {}).get('nodes') or {}).get(NODE) or {}; return int(n.get('records') or 0), int(n.get('events') or 0), n.get('as_of')
def tavily_usage():
    try:
        import requests
        r = requests.get('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + os.environ.get('TAVILY_API_KEY', '')}, timeout=30)
        j = r.json().get('account', {}) if r.status_code == 200 else {}; return int(j['plan_usage']) if j.get('plan_usage') is not None else None
    except Exception: return None

def ark_write(files, prefix):
    """files: [(local path, key under <node>/<market date>/)]; returns [{key, version_id, bytes}] — Object Lock on the bucket keeps every version"""
    import boto3
    s3 = boto3.client('s3', region_name=os.environ['ARK_REGION']); b = os.environ['ARK_BUCKET']; out = []
    for p, key in files:
        k = f'{prefix}/{key}'
        with open(p, 'rb') as f: r = s3.put_object(Bucket=b, Key=k, Body=f)
        out.append({'bucket': b, 'key': k, 'version_id': r.get('VersionId'), 'bytes': os.path.getsize(p)})
    return out

def main():
    global _key
    log(f'ORDER-031 node job {NODE} region {REGION} store {SA}/{CONT} market date {MDATE} image {IMAGE_TAG} execution {EXEC}')
    sh(['az', 'login', '--identity', '-o', 'none'], quiet=True); sh(['az', 'account', 'set', '-s', SUB], quiet=True)
    acct = az('account', 'show')
    if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
    _key = az('storage', 'account', 'keys', 'list', '-n', SA, '-g', RG, '--query', '[0].value', '-o', 'tsv', raw=True)
    os.environ['STORAGE_ACCOUNT'] = SA; os.environ['STORAGE_KEY'] = _key
    tav0 = tavily_usage(); log('tavily plan counter at start:', tav0)
    old = blob_json('door/facts.json'); o_rec, o_ev, o_asof = counts(old); log(f'door serves now: records {o_rec} events {o_ev} as_of {o_asof}')
    hold = ''; gate = 0; result = {}
    if CC == 'us':
        rc = sh(['/usr/local/bin/python3', 'us_pipeline.py'], cwd=f'{RAILS}/us-job', check=False, env={'REGION': REGION, 'CONTACT': os.environ.get('CONTACT', 'developers@allooloo.ai')})
        if rc != 0: raise RuntimeError(f'us_pipeline exit {rc}')
        gate = sh(['/usr/local/bin/python3', 'door_gate.py', 'us', REGION, MDATE, '--after-job'], cwd=f'{RAILS}/door', check=False); log('gate exit', gate)
        if gate == 0: sh(['/usr/local/bin/python3', 'restamp_asof.py', 'us', REGION, MDATE], cwd=f'{RAILS}/door')
        else: hold = MDATE
        new = blob_json('door/facts.json'); drop = TODAY.isoformat()
    else:
        sync_pond()
        if os.path.exists(os.path.join(POND, NODE, '.lock')):
            log('DONE skipped on the node lock'); blob_put(f'sweeps/{MDATE}/{CC}/skipped.json', json.dumps({'node': NODE, 'market_date': MDATE, 'why': 'node lock in the store', 'at': T0.isoformat()})); return 0
        before = newest_drop('assembled')
        rail = f'{RAILS}/{CC}-width1'
        rc = sh(['pwsh', '-NoProfile', '-NonInteractive', '-Command', "& './run_refresh.ps1'; exit $LASTEXITCODE"], cwd=rail, check=False)
        log('harvest rail exit', rc)
        if rc != 0: raise RuntimeError(f'harvest rail exit {rc}: door, store and apex left as they were (close-out 2026-10-10 rule)')
        drop = newest_drop('width1'); after = newest_drop('assembled'); log(f'pond drop {drop}; assembled before {before} after {after}')
        if not after or after == before: raise RuntimeError('no new assembled drop from this run (the door would be rebuilt from an older assembly)')
        sh(['/usr/local/bin/python3', 'load_nodes.py', CC], cwd=f'{RAILS}/door', env={f'AS_OF_{CC.upper()}': MDATE})
        gate = sh(['/usr/local/bin/python3', 'door_gate.py', CC, REGION, MDATE], cwd=f'{RAILS}/door', check=False); log('gate exit', gate)
        if gate != 0: hold = MDATE
        sh(['/usr/local/bin/python3', 'provision_region.py', CC, REGION, 'upload'], cwd=f'{ROOT}/AZURE', env=({'DOOR_HOLD': hold} if hold else {}))
        new = json.load(open(f'{DOOR}/data/facts.json', encoding='utf-8'))
    if os.environ.get('DOOR_RESTART', '1') == '1' and CONT == 'pond' and not hold:
        try:
            rev = az('containerapp', 'show', '-g', RG, '-n', f'cmkg-door-{CC}', '--query', 'properties.latestRevisionName', '-o', 'tsv', raw=True)
            az('containerapp', 'revision', 'restart', '-g', RG, '-n', f'cmkg-door-{CC}', '--revision', rev, raw=True); log('door revision restarted:', rev)
        except Exception as e: log('door restart failed (flagged):', repr(e)[:200]); result['door_restart'] = 'failed'
    elif hold: log('door HELD: no restart, as-of stays', o_asof)
    else: log('door restart skipped (staging / DOOR_RESTART=0)')
    n_rec, n_ev, n_asof = counts(new)
    if hold: n_rec, n_ev, n_asof = o_rec, o_ev, o_asof
    line = f"{NODE} · {n_asof or MDATE} · {n_rec} · {n_ev} · records {n_rec - o_rec:+d} · events {n_ev - o_ev:+d} (sweep {MDATE}, Azure job {REGION}{', HELD' if hold else ''})"
    log('NUMBERS LOG', line)
    # SPEND: the node's own lab lines from its drops (Canada carries the labs; the others call Tavily only) + its share of the Tavily counter
    tav1 = tavily_usage(); spend_lines = []
    if CC != 'us':
        md = f'{ROOT}/CM-KG/SPEND/SPEND.md'; n0 = len(open(md, encoding='utf-8').read().splitlines()) if os.path.exists(md) else 0
        args = ['/usr/local/bin/python3', 'spend_line.py', f'sweep {MDATE} {CC} (Azure job)', TODAY.isoformat(), '--note', 'in-country job; Tavily share read on this job only (the counter is shared by the parallel jobs)']
        # never write zero: the Tavily plan counter lags a few minutes and is shared by the parallel jobs, so an unchanged reading at close is not
        # "0 credits used" — the job writes its reading and says so; the run-level credits are the apex job's line (dry run 1, 2026-10-18)
        moved = tav0 is not None and tav1 is not None and tav1 > tav0
        # each node writes its own labs (and Tavily when its reading moved) — never the United States job's line (France dry run 2026-10-18: it printed on every node)
        if moved: args += ['--tavily-start', str(tav0), '--tavily-end', str(tav1), '--estimated', '--only', 'Grok,ChatGPT,Gemini,Mistral,Perplexity,Claude,Tavily']
        else: args += ['--only', 'Grok,ChatGPT,Gemini,Mistral,Perplexity,Claude']
        try:
            sh(args, cwd=RAILS, check=False, quiet=True); spend_lines = [l for l in open(md, encoding='utf-8').read().splitlines()[n0:] if l.strip() and not l.startswith('```')]
        except Exception as e: log('spend line failed (flagged):', repr(e)[:160])
        if not moved: spend_lines.append(f"sweep {MDATE} {CC} (Azure job) · Tavily · credits not attributed to this job (plan counter {tav1 if tav1 is not None else 'not read'} of 200,000 at close, unchanged from the start reading; the counter lags and is shared by the parallel jobs) · the run-level Tavily line is the apex job's")
    else: spend_lines = [f'sweep {MDATE} · United States job (EDGAR, Gemini, Perplexity) · no meter · lab calls run in the East US container job and are not counted here']
    for l in spend_lines: log('SPEND', l)
    held_flag = None
    if hold:
        fp = f'{ROOT}/CM-KG/SWEEPS/HELD-{NODE}-{MDATE}.txt'
        if os.path.exists(fp): held_flag = open(fp, encoding='utf-8').read()
    # ark (AWS): that night's record — the pond drop, the door bundle, the numbers line
    # the ark holds the record of the night: only a run against the live store writes it (Object Lock keeps every object a year; a staging
    # dry run must never land there) — CEO attach 2026-10-18, guard added before the ark was switched on
    ark = {'enabled': os.environ.get('ARK_ENABLED', '0') == '1' and CONT == 'pond', 'objects': []}
    if os.environ.get('ARK_ENABLED', '0') == '1' and CONT != 'pond': log(f'ark skipped: container {CONT} is not the live store')
    if ark['enabled']:
        try:
            files = []; prefix = f'{NODE}/{MDATE}'
            if CC != 'us':
                dd = os.path.join(POND, NODE, 'width1', drop)
                for r_, _, fs in os.walk(dd):
                    for f in fs: files.append((os.path.join(r_, f), f'pond/width1/{drop}/' + os.path.relpath(os.path.join(r_, f), dd).replace(os.sep, '/')))
                tb = f'/tmp/{NODE}-door-bundle.tar.gz'
                with tarfile.open(tb, 'w:gz') as t:
                    for sub in ('records', 'events'):
                        d = f'{DOOR}/data/{sub}/{NODE}'
                        if os.path.isdir(d): t.add(d, arcname=f'door/{sub}/{NODE}')
                    for fn in ('index.json', 'facts.json', 'nodes.json'): t.add(f'{DOOR}/data/{fn}', arcname=f'door/{fn}')
                files.append((tb, 'door/door-bundle.tar.gz'))
            else:
                tb = f'/tmp/{NODE}-door-bundle.tar.gz'; tmpd = f'/tmp/{NODE}-door'; os.makedirs(tmpd, exist_ok=True)
                names = [b.name for b in store().list_blobs(name_starts_with='door/')] + [b.name for b in store().list_blobs(name_starts_with=f'pond/width0/{drop}/')]
                def one(n):
                    p = os.path.join(tmpd, n); os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, 'wb') as f: store().get_blob_client(n).download_blob().readinto(f)
                with ThreadPoolExecutor(max_workers=32) as ex: list(ex.map(one, names))
                with tarfile.open(tb, 'w:gz') as t: t.add(tmpd, arcname='.')
                files.append((tb, 'door-and-drop-bundle.tar.gz'))
            open(f'/tmp/{NODE}-numbers.txt', 'w', encoding='utf-8').write(line + '\n'); files.append((f'/tmp/{NODE}-numbers.txt', 'numbers.txt'))
            ark['objects'] = ark_write(files, prefix); log(f"ark: {len(ark['objects'])} objects written to s3://{os.environ['ARK_BUCKET']}/{prefix}/")
        except Exception as e: ark['error'] = repr(e)[:300]; log('ark write FAILED (a failed close for the apex):', ark['error'])
    done = {'node': NODE, 'market_date': MDATE, 'region': REGION, 'store': f'{SA}/{CONT}', 'pond_drop': drop, 'records': n_rec, 'events': n_ev, 'as_of': n_asof, 'records_delta': n_rec - o_rec, 'events_delta': n_ev - o_ev,
            'served_before': {'records': o_rec, 'events': o_ev, 'as_of': o_asof}, 'gate_exit': gate, 'held': bool(hold), 'held_flag': held_flag, 'numbers_line': line, 'spend_lines': spend_lines,
            'tavily': {'start': tav0, 'end': tav1}, 'ark': ark, 'image': IMAGE_TAG, 'execution': EXEC, 'started_utc': T0.isoformat(), 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), **result}
    blob_put(f'sweeps/{MDATE}/{CC}/done.json', json.dumps(done, ensure_ascii=False, indent=1)); blob_put(f'sweeps/{MDATE}/{CC}/numbers.txt', line + '\n', 'text/plain'); blob_put(f'sweeps/{MDATE}/{CC}/spend.txt', '\n'.join(spend_lines) + '\n', 'text/plain')
    if held_flag: blob_put(f'sweeps/{MDATE}/{CC}/held.txt', held_flag, 'text/plain')
    log(f'DONE {NODE} {MDATE}: marker sweeps/{MDATE}/{CC}/done.json'); return 0

if __name__ == '__main__':
    try: rc = main()
    except SystemExit as e: rc = e.code if isinstance(e.code, int) else 1; log('STOP', e)
    except Exception as e:
        rc = 1; log('FAILED', repr(e)[:400]); log(traceback.format_exc()[-2000:])
        try: blob_put(f'sweeps/{MDATE}/{CC}/failed.json', json.dumps({'node': NODE, 'market_date': MDATE, 'error': repr(e)[:400], 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'execution': EXEC}))
        except Exception: pass
    try: blob_put(f'sweeps/{MDATE}/{CC}/job-{EXEC}.log', '\n'.join(LOG) + '\n', 'text/plain')
    except Exception: pass
    sys.exit(rc)
