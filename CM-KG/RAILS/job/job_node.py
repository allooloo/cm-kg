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
# ORDER-036 NIGHTLY (2026-10-22): every regional job fires at 02:00 its own region's local STANDARD time (fixed UTC cron, never moved for daylight time),
# seven nights a week. NIGHT = the local calendar date at the fire (the key of the night's markers: sweeps/<night>/<cc>/ — a Saturday or Sunday night never
# lands on Friday's marker); MDATE = the market date = the last trading date before the night (weekends roll back to Friday; exchange holidays are not
# carried — the run that night reads the window and the as_of stays the date the rule gives). Supersedes the Friday-on-or-before rule (ORDER-027 A1).
STD_OFFSET = {'ca': -5, 'us': -5, 'uk': 0, 'de': 1, 'fr': 1, 'nl': 1, 'ch': 1, 'au': 10, 'sg': 8, 'hk': 8, 'jp': 9, 'kr': 9}
STD_OFFSET.update({'it': 1, 'es': 1, 'se': 1, 'dk': 1, 'no': 1, 'fi': 2, 'be': 1, 'ie': 0, 'at': 1, 'pl': 1, 'pt': 0, 'lu': 1, 'gr': 2, 'cz': 1})   # NODE-EU (2026-10-24)
STD_OFFSET.update({'ky': -5, 'bm': -4, 'je': 0, 'in': 5.5, 'tw': 8, 'sa': 3, 'ae': 4, 'br': -3, 'mx': -6})   # NODE-ROW (DAY ORDER 5, 2026-10-24)
def last_trading(d):
    while d.weekday() >= 5: d -= datetime.timedelta(days=1)
    return d
NIGHT = os.environ.get('NIGHT') or (T0 + datetime.timedelta(hours=STD_OFFSET.get(CC, 0))).date().isoformat(); datetime.date.fromisoformat(NIGHT)
# DAY ORDER 5 (CEO 2026-10-24): a job armed ahead of its first night (NOT_BEFORE=<UTC date>) exits clean, writing no marker, on a fire before that date
# ENUM-01 (DAY ORDER 6, 2026-10-25): the market clock is policy keyed by market — a roster node with no STD_OFFSET line refuses to run (named), never defaults
# to UTC; and a NOT_BEFORE guard on a node the roster already shows live reads as cleared (the guard existed only to wait for a node's first night)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import roster
if CC != 'apex' and CC not in STD_OFFSET: raise SystemExit(f'ROSTER POLICY GAP · market clock (STD_OFFSET) · no line for: {CC} — rail refused')
if os.environ.get('NOT_BEFORE') and T0.date().isoformat() < os.environ['NOT_BEFORE']:
    try: _live = CC in roster.codes()
    except Exception: _live = False
    if _live: print(f"NOT_BEFORE {os.environ['NOT_BEFORE']} reads as cleared: {CC}-cm-kg is live on the roster of record", flush=True); os.environ.pop('NOT_BEFORE')
if os.environ.get('NOT_BEFORE') and T0.date().isoformat() < os.environ['NOT_BEFORE']: print(f"not before {os.environ['NOT_BEFORE']}: fire of {T0.isoformat()} exits clean, no marker", flush=True); sys.exit(0)
MDATE = os.environ.get('MARKET_DATE') or last_trading(datetime.date.fromisoformat(NIGHT) - datetime.timedelta(days=1)).isoformat(); datetime.date.fromisoformat(MDATE)
# depth gated by day inside the job: the Width 1 read runs every night over a three-day window (a 48-hour window plus the weekend margin); the Fill +
# Confirm passes (Canada's rail carries them) run on the node's rotation night only — CC's rotation of record, logged in done.json
os.environ.setdefault('WINDOW_DAYS', os.environ.get('NIGHTLY_WINDOW_DAYS', '3'))
FILL_ROTATION = {'ca': 4, 'us': 4, 'uk': 4, 'de': 4, 'fr': 4, 'nl': 4, 'ch': 4, 'au': 4, 'sg': 4, 'hk': 4, 'jp': 4, 'kr': 4}   # market-date weekday of the Fill + Confirm night (4 = Friday: the depth the weekly sweep ran)
FILL_ROTATION.update({c: 4 for c in STD_OFFSET if c not in FILL_ROTATION})   # ENUM-01: every market with a clock line carries a rotation line (Friday, as the twelve), written rather than a silent .get default
FILL_CONFIRM = os.environ.get('FILL_CONFIRM') or ('1' if datetime.date.fromisoformat(MDATE).weekday() == FILL_ROTATION.get(CC, 4) and datetime.date.fromisoformat(NIGHT).weekday() == (FILL_ROTATION.get(CC, 4) + 1) % 7 else '0')
os.environ['FILL_CONFIRM'] = FILL_CONFIRM
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
    """files: [(local path, key under <prefix>/)] -> [{bucket, key, version_id, bytes, skipped}]. Put only, never overwrite (ORDER-033 rule): the bucket's
    listing (ark-writer may list its own prefix) gives each key's ETag; same MD5 = skipped, a differing object is written beside as <name>-2, -3 ..."""
    import boto3, hashlib, base64
    s3 = boto3.client('s3', region_name=os.environ['ARK_REGION']); b = os.environ['ARK_BUCKET']; out = []; have = {}
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=b, Prefix=prefix + '/'):
        for o in page.get('Contents', []): have[o['Key']] = o['ETag'].strip('"')
    for p, key in files:
        data = open(p, 'rb').read(); md5 = hashlib.md5(data).hexdigest(); k = f'{prefix}/{key}'
        if have.get(k) == md5: out.append({'bucket': b, 'key': k, 'version_id': None, 'bytes': len(data), 'skipped': True}); continue
        n = 1; base = k
        while k in have and have[k] != md5: n += 1; k = f'{base}-{n}'
        if have.get(k) == md5: out.append({'bucket': b, 'key': k, 'version_id': None, 'bytes': len(data), 'skipped': True}); continue
        r = s3.put_object(Bucket=b, Key=k, Body=data, ContentMD5=base64.b64encode(bytes.fromhex(md5)).decode())
        have[k] = md5; out.append({'bucket': b, 'key': k, 'version_id': r.get('VersionId'), 'bytes': len(data), 'skipped': False})
    return out

def main():
    global _key
    log(f'ORDER-036 nightly node job {NODE} region {REGION} store {SA}/{CONT} night {NIGHT} market date {MDATE} window {os.environ.get("WINDOW_DAYS")} days fill+confirm {FILL_CONFIRM} image {IMAGE_TAG} execution {EXEC}')
    sh(['az', 'login', '--identity', '-o', 'none'], quiet=True); sh(['az', 'account', 'set', '-s', SUB], quiet=True)
    acct = az('account', 'show')
    if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
    _key = az('storage', 'account', 'keys', 'list', '-n', SA, '-g', RG, '--query', '[0].value', '-o', 'tsv', raw=True)
    os.environ['STORAGE_ACCOUNT'] = SA; os.environ['STORAGE_KEY'] = _key
    # BACKFILL-01 (DAY ORDER 7, 2026-10-25): the node's backfill job (cmkg-<cc>-backfill) is this image with JOB_MODE=backfill — the pond inputs synced as the
    # live night syncs them, then RAILS\backfill\backfill.py run <cc> (B-3 order gate, newest year first, resumable, paced to the archive). It never touches
    # door/, the live markers, Issuerwire or the digest counts; its marker is sweeps-backfill/<night>/<cc>/done.json (or failed.json) in the node's store.
    if os.environ.get('JOB_MODE') == 'backfill':
        if CC != 'us': sync_pond()
        t1 = datetime.datetime.now(datetime.timezone.utc)
        p = subprocess.run(['/usr/local/bin/python3', '-X', 'utf8', 'backfill.py', 'run', CC], cwd=f'{RAILS}/backfill', capture_output=True, text=True, encoding='utf-8', errors='replace')
        for l in (p.stdout + p.stderr).splitlines()[-200:]: log('backfill |', l)
        mk = {'node': NODE, 'night': NIGHT, 'mode': 'backfill', 'exit': p.returncode, 'tail': (p.stdout + p.stderr)[-3000:], 'image': IMAGE_TAG, 'execution': EXEC, 'started_utc': t1.isoformat(), 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        blob_put(f'sweeps-backfill/{NIGHT}/{CC}/{"done" if p.returncode == 0 else "failed"}.json', json.dumps(mk, ensure_ascii=False, indent=1))
        return p.returncode
    tav0 = tavily_usage(); log('tavily plan counter at start:', tav0)
    old = blob_json('door/facts.json'); o_rec, o_ev, o_asof = counts(old); log(f'door serves now: records {o_rec} events {o_ev} as_of {o_asof}')
    hold = ''; gate = 0; result = {}
    if CC == 'us':
        rc = sh(['/usr/local/bin/python3', 'us_pipeline.py'], cwd=f'{RAILS}/us-job', check=False, env={'REGION': REGION, 'CONTACT': os.environ.get('CONTACT', 'developers@allooloo.ai')})
        if rc != 0: raise RuntimeError(f'us_pipeline exit {rc}')
        gate = sh(['/usr/local/bin/python3', 'door_gate.py', 'us', REGION, MDATE, '--after-job'], cwd=f'{RAILS}/door', check=False); log('gate exit', gate)
        if gate == 0: sh(['/usr/local/bin/python3', 'restamp_asof.py', 'us', REGION, MDATE], cwd=f'{RAILS}/door')
        else: hold = MDATE
        # DOORS-03 (2026-10-26): one record per listed company — the us pipeline publishes from inside the job, so the fold runs on the store after the gate
        if not hold: rc_fold = sh(['/usr/local/bin/python3', 'fold_listings.py', 'us', '--store'], cwd=f'{RAILS}/door', check=False); log('fold exit', rc_fold); result['fold'] = rc_fold   # store key: STORAGE_KEY, set above
        new = blob_json('door/facts.json')
        # the drop this run wrote: the newest pond/width0/<today>[-n] (the pipeline writes the next drop beside when an earlier one of the day had another window)
        _ds = sorted({b.name.split('/')[2] for b in store().list_blobs(name_starts_with=f'pond/width0/{TODAY.isoformat()}')}, key=lambda d: (d[:10], int(d[11:] or 0)))
        drop = _ds[-1] if _ds else TODAY.isoformat()
    else:
        sync_pond()
        if os.path.exists(os.path.join(POND, NODE, '.lock')):
            log('DONE skipped on the node lock'); blob_put(f'sweeps/{NIGHT}/{CC}/skipped.json', json.dumps({'node': NODE, 'market_date': MDATE, 'why': 'node lock in the store', 'at': T0.isoformat()})); return 0
        before = newest_drop('assembled')
        rail = f'{RAILS}/{CC}-width1'
        rc = sh(['pwsh', '-NoProfile', '-NonInteractive', '-Command', "& './run_refresh.ps1'; exit $LASTEXITCODE"], cwd=rail, check=False)
        log('harvest rail exit', rc)
        if rc != 0: raise RuntimeError(f'harvest rail exit {rc}: door, store and apex left as they were (close-out 2026-10-10 rule)')
        drop = newest_drop('width1'); after = newest_drop('assembled'); log(f'pond drop {drop}; assembled before {before} after {after}')
        if not after or after == before: raise RuntimeError('no new assembled drop from this run (the door would be rebuilt from an older assembly)')
        sh(['/usr/local/bin/python3', 'load_nodes.py', CC], cwd=f'{RAILS}/door', env={f'AS_OF_{CC.upper()}': MDATE})
        # DAY ORDER 4 (2026-10-24): NODE-HALT-01 — every record carries tonight's halt state from the market's own list; NODE-ISIN-01 — kr ISINs from KRX
        rc_en = sh(['/usr/local/bin/python3', 'enrich_node.py', CC], cwd=f'{RAILS}/door', check=False); log('enrich exit', rc_en); result['enrich'] = rc_en
        # DOORS-03 (2026-10-26): one record per listed company — listing lines of one issuer under one ISIN fold into one record before the gate reads the counts
        rc_fold = sh(['/usr/local/bin/python3', 'fold_listings.py', CC, '--data'], cwd=f'{RAILS}/door', check=False); log('fold exit', rc_fold); result['fold'] = rc_fold
        gate =sh(['/usr/local/bin/python3', 'door_gate.py', CC, REGION, MDATE], cwd=f'{RAILS}/door', check=False); log('gate exit', gate)
        if gate != 0: hold = MDATE
        sh(['/usr/local/bin/python3', 'provision_region.py', CC, REGION, 'upload'], cwd=f'{ROOT}/AZURE', env=({'DOOR_HOLD': hold} if hold else {}))
        new = json.load(open(f'{DOOR}/data/facts.json', encoding='utf-8'))
        if not hold:   # SHELF-01 (2026-10-27): beside the record, after it is published — the lifecycle index (Events) and the score (a FAIL never holds the record)
            rc_lc = sh(['/usr/local/bin/python3', '-X', 'utf8', 'lifecycle.py', 'build', CC, '--store'], cwd=f'{RAILS}/shelf', check=False); log('lifecycle exit', rc_lc); result['lifecycle'] = rc_lc
            rc_sc = sh(['/usr/local/bin/python3', '-X', 'utf8', 'score.py', CC], cwd=f'{RAILS}/shelf', check=False); log('score exit', rc_sc); result['score'] = rc_sc
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
        md = f'{ROOT}/CM-KG/SPEND/SPEND.md'; before = set(open(md, encoding='utf-8').read().splitlines()) if os.path.exists(md) else set()
        args = ['/usr/local/bin/python3', 'spend_line.py', f'sweep {MDATE} {CC} (Azure job)', TODAY.isoformat(), '--note', 'in-country job; Tavily share read on this job only (the counter is shared by the parallel jobs)']
        # never write zero: the Tavily plan counter lags a few minutes and is shared by the parallel jobs, so an unchanged reading at close is not
        # "0 credits used" — the job writes its reading and says so; the run-level credits are the apex job's line (dry run 1, 2026-10-18)
        moved = tav0 is not None and tav1 is not None and tav1 > tav0
        # each node writes its own labs (and Tavily when its reading moved) — never the United States job's line (France dry run 2026-10-18: it printed on every node)
        if moved: args += ['--tavily-start', str(tav0), '--tavily-end', str(tav1), '--estimated', '--only', 'Grok,ChatGPT,Gemini,Mistral,Perplexity,Claude,Tavily']
        else: args += ['--only', 'Grok,ChatGPT,Gemini,Mistral,Perplexity,Claude']
        try:
            # spend_line.py inserts its lines before the closing fence of SPEND.md, so the new lines are the ones not there before — not the file's tail
            # (the tail slice dropped the first new line, Grok, on every node; found on the Canada dry run 2026-10-18)
            sh(args, cwd=RAILS, check=False, quiet=True); spend_lines = [l for l in open(md, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('```') and l not in before]
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
        # ark layout of record (ORDER-033, 2026-10-18) — the same keys the backfill writes, so the ark reads like the pond:
        #   <node>/pond/<source>/<drop>/<file>   every pond drop this run created, paths identical to the pond
        #   <node>/door/<as_of>/door-bundle.tar.gz   the door as published (records, events, index, facts, nodes)
        #   <node>/numbers/<market date>.txt   the NUMBERS LOG line
        try:
            files = []
            if CC != 'us':
                for source in sorted(os.listdir(os.path.join(POND, NODE))):
                    sd = os.path.join(POND, NODE, source)
                    if not os.path.isdir(sd) or source.startswith('.'): continue
                    for dr in os.listdir(sd):
                        if not dr.startswith(TODAY.isoformat()): continue   # drops this run created
                        dd = os.path.join(sd, dr)
                        for r_, _, fs in os.walk(dd):
                            for f in fs:
                                if f == '.open': continue
                                files.append((os.path.join(r_, f), f'pond/{source}/{dr}/' + os.path.relpath(os.path.join(r_, f), dd).replace(os.sep, '/')))
                door_src = [(f'{DOOR}/data/{sub}/{NODE}', f'door/{sub}') for sub in ('records', 'events')]   # the store's own layout door/<sub>/<EX>/<code>.json — what a door reads + [(f'{DOOR}/data/{fn}', f'door/{fn}') for fn in ('index.json', 'facts.json', 'nodes.json')]
            else:
                tmpd = f'/tmp/{NODE}-ark'; os.makedirs(tmpd, exist_ok=True)
                drop_names = [b.name for b in store().list_blobs(name_starts_with=f'pond/width0/{drop}/')]   # the drop this run wrote, never an earlier drop of the day
                door_names = [b.name for b in store().list_blobs(name_starts_with='door/')]
                def one(n):
                    p = os.path.join(tmpd, n); os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, 'wb') as f: store().get_blob_client(n).download_blob().readinto(f)
                with ThreadPoolExecutor(max_workers=32) as ex: list(ex.map(one, drop_names + door_names))
                files += [(os.path.join(tmpd, n), n) for n in drop_names]
                door_src = [(os.path.join(tmpd, 'door'), 'door')]
            tb = f'/tmp/{NODE}-door-bundle.tar.gz'
            with tarfile.open(tb, 'w:gz') as t:
                for src, arc in door_src:
                    if os.path.exists(src): t.add(src, arcname=arc)
            files.append((tb, f'door/{n_asof or MDATE}/door-bundle.tar.gz'))
            open(f'/tmp/{NODE}-numbers.txt', 'w', encoding='utf-8').write(line + '\n'); files.append((f'/tmp/{NODE}-numbers.txt', f'numbers/{NIGHT}.txt'))
            ark['objects'] = ark_write(files, NODE); log(f"ark: {len(ark['objects'])} objects written to s3://{os.environ['ARK_BUCKET']}/{NODE}/")
        except Exception as e: ark['error'] = repr(e)[:300]; log('ark write FAILED (a failed close for the apex):', ark['error'])
    done = {'node': NODE, 'night': NIGHT, 'market_date': MDATE, 'window_days': os.environ.get('WINDOW_DAYS'), 'fill_confirm': FILL_CONFIRM, 'region': REGION, 'store': f'{SA}/{CONT}', 'pond_drop': drop, 'records': n_rec, 'events': n_ev, 'as_of': n_asof, 'records_delta': n_rec - o_rec, 'events_delta': n_ev - o_ev,
            'served_before': {'records': o_rec, 'events': o_ev, 'as_of': o_asof}, 'gate_exit': gate, 'held': bool(hold), 'held_flag': held_flag, 'numbers_line': line, 'spend_lines': spend_lines,
            'tavily': {'start': tav0, 'end': tav1}, 'ark': ark, 'image': IMAGE_TAG, 'execution': EXEC, 'started_utc': T0.isoformat(), 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), **result}
    blob_put(f'sweeps/{NIGHT}/{CC}/done.json', json.dumps(done, ensure_ascii=False, indent=1)); blob_put(f'sweeps/{NIGHT}/{CC}/numbers.txt', line + '\n', 'text/plain'); blob_put(f'sweeps/{NIGHT}/{CC}/spend.txt', '\n'.join(spend_lines) + '\n', 'text/plain')
    if held_flag: blob_put(f'sweeps/{NIGHT}/{CC}/held.txt', held_flag, 'text/plain')
    log(f'DONE {NODE} night {NIGHT} market date {MDATE}: marker sweeps/{NIGHT}/{CC}/done.json'); return 0

if __name__ == '__main__':
    try: rc = main()
    except SystemExit as e: rc = e.code if isinstance(e.code, int) else 1; log('STOP', e)
    except Exception as e:
        rc = 1; log('FAILED', repr(e)[:400]); log(traceback.format_exc()[-2000:])
        try: blob_put(f'{"sweeps-backfill" if os.environ.get("JOB_MODE") == "backfill" else "sweeps"}/{NIGHT}/{CC}/failed.json', json.dumps({'node': NODE, 'market_date': MDATE, 'error': repr(e)[:400], 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'execution': EXEC}))
        except Exception: pass
    try: blob_put(f'{"sweeps-backfill" if os.environ.get("JOB_MODE") == "backfill" else "sweeps"}/{NIGHT}/{CC}/job-{EXEC}.log', '\n'.join(LOG) + '\n', 'text/plain')
    except Exception: pass
    sys.exit(rc)
