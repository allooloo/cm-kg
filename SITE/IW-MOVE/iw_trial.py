r"""iw_trial.py — IW-MOVE-01 step 6: one cycle on both sides, in the Ops Agents' own staging mode (CEO 2026-11-12: accepted; old jobs back to live the
moment the cycle is read). Staging mode = STORAGE_CONTAINER=staging: output to the staging container, working tables in schema ops_staging, the record
schema read only, NO ledger event (the chain is not forked), ark refused.
  run       old side: each job's STORAGE_CONTAINER pond -> staging (the before-state is saved first). Then, job by job in the cycle's order, the old job
            and its twin are started together and awaited. Then — whatever happened — every old job is set back to pond and read back to confirm.
  restore   only the set-back-to-pond step (safe to repeat)
  snap      both sides' staging containers are brought to trial\old\ and trial\new\, and every ops_staging table to trial\<side>\db\<table>.jsonl
Usage: python -X utf8 -I iw_trial.py run|restore|snap"""
import json, os, subprocess, sys, time, pathlib, datetime
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']; H = pathlib.Path(__file__).parent; T = H / 'trial'; T.mkdir(exist_ok=True)
OLD = (dict(os.environ, AZURE_CONFIG_DIR=r'C:\A2AAMN\.azure', MSYS_NO_PATHCONV='1'), 'rg-amn-frc', ['--subscription', '9e406344-81a4-4624-98de-a9c642a75d69'], 'amn')
NEW = (dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'), 'allooloo-iw-francecentral', [], 'iw')
ORDER = ['standing', 'filings', 'coverage', 'claims', 'receipts', 'ark', 'stores', 'close']
def say(*a): print(datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S'), *a, flush=True)
def az(side, *a, check=True):
    r = subprocess.run([*AZ, *a, *side[2], '-o', 'json'], capture_output=True, text=True, env=side[0], encoding='utf-8', errors='replace')
    if r.returncode:
        if check: raise RuntimeError(f'az {" ".join(a[:4])}: {r.stderr[-400:]}')
        return None
    return json.loads(r.stdout) if r.stdout.strip() else None
def cont_of(side, x):
    j = az(side, 'containerapp', 'job', 'show', '-n', f'{side[3]}-{x}-rail', '-g', side[1]); return next(e.get('value') for e in j['properties']['template']['containers'][0]['env'] if e['name'] == 'STORAGE_CONTAINER')
def restore():
    bad = []
    for x in ORDER:
        for attempt in range(3):
            try:
                if cont_of(OLD, x) != 'pond': az(OLD, 'containerapp', 'job', 'update', '-n', f'amn-{x}-rail', '-g', OLD[1], '--set-env-vars', 'STORAGE_CONTAINER=pond')
                if cont_of(OLD, x) == 'pond': break
            except Exception as e: say('restore retry', x, repr(e)[:160]); time.sleep(10)
        else: bad.append(x)
    say('OLD SIDE BACK TO LIVE:', 'all eight jobs read back as pond' if not bad else f'NOT RESTORED: {bad}'); return bad
if sys.argv[1] == 'restore': sys.exit(1 if restore() else 0)
if sys.argv[1] == 'run':
    before = {x: cont_of(OLD, x) for x in ORDER}; json.dump({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'old_storage_container_before': before}, open(T / 'old-before.json', 'w'), indent=1); say('old before:', before)
    if any(v != 'pond' for v in before.values()): sys.exit('STOP: an old job is not in live mode before the trial')
    if any(cont_of(NEW, x) != 'staging' for x in ORDER): sys.exit('STOP: a new job is not in staging mode')
    res = {}
    try:
        for x in ORDER: az(OLD, 'containerapp', 'job', 'update', '-n', f'amn-{x}-rail', '-g', OLD[1], '--set-env-vars', 'STORAGE_CONTAINER=staging')
        say('old side in staging mode'); res['started_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for x in ORDER:
            ex = {}
            for nm, side in (('old', OLD), ('new', NEW)):
                r = az(side, 'containerapp', 'job', 'start', '-n', f'{side[3]}-{x}-rail', '-g', side[1]); ex[nm] = r.get('name') or r['id'].split('/')[-1]
            st = {}; t0 = time.time()
            while len(st) < 2 and time.time() - t0 < 9000:
                time.sleep(20)
                for nm, side in (('old', OLD), ('new', NEW)):
                    if nm in st: continue
                    s = az(side, 'containerapp', 'job', 'execution', 'show', '-n', f'{side[3]}-{x}-rail', '-g', side[1], '--job-execution-name', ex[nm], check=False); s = ((s or {}).get('properties') or {}).get('status')
                    if s and s not in ('Running', 'Processing', 'Unknown'): st[nm] = s
            res[x] = {'executions': ex, 'status': st, 'seconds': int(time.time() - t0)}; say(x, ex, st, res[x]['seconds'], 's')
    finally:
        res['not_restored'] = restore(); res['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat(); json.dump(res, open(T / 'trial-run.json', 'w'), indent=1)
if sys.argv[1] == 'snap':
    from azure.storage.blob import BlobServiceClient
    PSQL = os.path.join('C:' + chr(92) + 'Program Files', 'PostgreSQL', '16', 'bin', 'psql.exe')
    for nm, side, sa, kv, sec, host in (('old', OLD, 'stgamnfrc', 'kv-amn-frc', 'pg-amn-frc-admin', 'pg-amn-frc.postgres.database.azure.com'), ('new', NEW, 'allooloostgiwfrc', 'allooloo-iw-kv-frc', 'pg-admin', 'allooloo-iw-pg-frc.postgres.database.azure.com')):
        k = subprocess.run([*AZ, 'storage', 'account', 'keys', 'list', '-n', sa, '-g', side[1], *side[2], '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, env=side[0]).stdout.strip()
        c = BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=k).get_container_client('staging'); n = 0; idx = []
        for b in c.list_blobs():
            p = T / nm / 'staging' / b.name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(c.download_blob(b.name).readall()); n += 1; idx.append({'name': b.name, 'size': b.size, 'modified': b.last_modified.isoformat()})
        json.dump(idx, open(T / nm / 'staging-index.json', 'w'), indent=1)
        pw = subprocess.run([*AZ, 'keyvault', 'secret', 'show', '--vault-name', kv, '-n', sec, *side[2], '--query', 'value', '-o', 'tsv'], capture_output=True, text=True, env=side[0]).stdout.strip()
        (T / nm / 'db').mkdir(parents=True, exist_ok=True); tabs = {}; PE = dict(os.environ, PGPASSWORD=pw, PGSSLMODE='require', PGCONNECT_TIMEOUT='30'); del pw
        def psql(q): return subprocess.run([PSQL, '-h', host, '-U', 'amnadmin', '-d', 'amn', '-At', '-c', q], capture_output=True, env=PE).stdout.decode('utf-8', 'replace')
        for t in [x for x in psql("select table_name from information_schema.tables where table_schema = 'ops_staging' order by 1").splitlines() if x.strip()]:
            out = psql(f'copy (select row_to_json(x) from ops_staging."{t}" x) to stdout'); rows = [l.replace(chr(92) * 2, chr(92)) for l in out.splitlines() if l.strip()]; tabs[t] = len(rows)
            open(T / nm / 'db' / f'{t}.jsonl', 'w', encoding='utf-8').write(''.join(r + chr(10) for r in rows))
        del PE
        say(nm, 'staging blobs', n, 'ops_staging tables', tabs)
