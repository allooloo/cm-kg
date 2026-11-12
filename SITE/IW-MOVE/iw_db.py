r"""iw_db.py — IW-MOVE-01 step 3: Issuerwire's database, dump and restore. pg-amn-frc (other directory) database amn -> allooloo-iw-pg-frc (Allooloo)
database amn. PostgreSQL 16 tools on this machine. Each side's password is read from ITS OWN vault through its own sign-in, held in the child process
environment only, never printed, never written to disk; the old password is not placed anywhere on the new side (the new side has its own, made in
iw_infra.py). The dump is a custom-format file under this folder's dump\ (public-record rows; kept, never deleted).
  dump      pg_dump -Fc --no-owner --no-privileges, every schema of the database
  restore   the new database amn is created if absent, then pg_restore --no-owner --no-privileges --clean --if-exists (a re-run replaces what is there)
  count     count(*) of every table on both sides; a difference is printed and exits 1
Usage: python -X utf8 -I iw_db.py dump|restore|count"""
import json, os, subprocess, sys, time, datetime
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']; BIN = r'C:\Program Files\PostgreSQL\16\bin'
OLD = dict(os.environ, AZURE_CONFIG_DIR=r'C:\A2AAMN\.azure'); NEW = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'dump'); os.makedirs(D, exist_ok=True)
SIDES = {'old': (OLD, ['--subscription', '9e406344-81a4-4624-98de-a9c642a75d69'], 'kv-amn-frc', 'pg-amn-frc-admin', 'pg-amn-frc.postgres.database.azure.com'), 'new': (NEW, [], 'allooloo-iw-kv-frc', 'pg-admin', 'allooloo-iw-pg-frc.postgres.database.azure.com')}
def pw(side):
    env, sub, kv, name, _ = SIDES[side]; r = subprocess.run([*AZ, 'keyvault', 'secret', 'show', '--vault-name', kv, '-n', name, *sub, '--query', 'value', '-o', 'tsv'], capture_output=True, text=True, env=env)
    if r.returncode or not r.stdout.strip(): print('STOP: the', side, 'vault did not give its database password'); sys.exit(1)
    return r.stdout.strip()
def pg(side, tool, *a, db='amn', stdin=None):
    p = pw(side); r = subprocess.run([os.path.join(BIN, tool + '.exe'), '-h', SIDES[side][4], '-U', 'amnadmin', *a], env=dict(os.environ, PGPASSWORD=p, PGSSLMODE='require', PGDATABASE=db, PGCONNECT_TIMEOUT='30'), capture_output=True, text=True, encoding='utf-8', errors='replace', input=stdin)
    return r.returncode, (r.stdout or ''), (r.stderr or '').replace(p, '***')
Q = "select table_schema||'.'||table_name from information_schema.tables where table_type='BASE TABLE' and table_schema not in ('pg_catalog','information_schema') and table_schema not like 'pg_%' order by 1"
def counts(side):
    rc, out, err = pg(side, 'psql', '-At', '-c', Q)
    if rc: print('STOP:', side, 'tables not read:', err[-300:]); sys.exit(1)
    res = {}
    for t in [x for x in out.splitlines() if x.strip()]:
        s, n = t.split('.', 1); rc, o, e = pg(side, 'psql', '-At', '-c', f'select count(*) from "{s}"."{n}"'); res[t] = int(o.strip()) if rc == 0 and o.strip().isdigit() else f'not read: {e[-80:]}'
    return res
mode = sys.argv[1]; f = os.path.join(D, 'amn.dump')
if mode == 'dump':
    if os.path.exists(f): os.replace(f, os.path.join(D, f"amn.pre-{time.strftime('%Y%m%dT%H%M%S')}.dump"))
    rc, out, err = pg('old', 'pg_dump', '-Fc', '--no-owner', '--no-privileges', '-f', f)
    print('dump exit', rc, 'bytes', os.path.getsize(f) if os.path.exists(f) else 0, err[-300:]); sys.exit(rc)
if mode == 'restore':
    rc, out, err = pg('new', 'psql', '-At', '-c', "select 1 from pg_database where datname='amn'", db='postgres')
    if rc: print('STOP: new server not reached:', err[-300:]); sys.exit(1)
    if not out.strip(): rc, out, err = pg('new', 'psql', '-c', 'create database amn', db='postgres'); print('create database amn exit', rc, err[-200:])
    rc, out, err = pg('new', 'pg_restore', '--no-owner', '--no-privileges', '--clean', '--if-exists', '-d', 'amn', f)
    print('restore exit', rc, err[-600:]); sys.exit(0 if rc in (0,) else rc)
if mode == 'count':
    a = counts('old'); b = counts('new'); keys = sorted(set(a) | set(b)); bad = [k for k in keys if a.get(k) != b.get(k)]
    out = {'at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'tables': {k: {'old': a.get(k), 'new': b.get(k), 'match': a.get(k) == b.get(k)} for k in keys}, 'MATCH': not bad}
    json.dump(out, open(os.path.join(HERE, f"rows-{out['at'].replace(':', '')}.json"), 'w'), indent=1)
    for k in keys: print(k, a.get(k), b.get(k), '' if a.get(k) == b.get(k) else '<-- DIFFERENT')
    print('tables', len(keys), 'rows old', sum(v for v in a.values() if isinstance(v, int)), 'new', sum(v for v in b.values() if isinstance(v, int)), 'MATCH' if not bad else 'DIFFERENT'); sys.exit(1 if bad else 0)
