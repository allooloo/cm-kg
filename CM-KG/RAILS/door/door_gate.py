r"""Forward-only door gate — CEO standing line 2, 2026-10-17 (applies from the 2026-10-23 sweep): a door never goes backward without a reason.
The pond is append-only. If the build would serve fewer records or events than the door serves now, the rail does not publish it: the last good
index stays on the wire, the new index/facts/nodes are written BESIDE it (store prefix door-held/<market date>/), and one flag file is written for the
sweepREVIEW machine half to read and explain (delisting · twelve-month window roll · Confirm dropping duplicates — one line each, with the count).
The node's as-of does not advance until it is resolved. No polling, no retry loop: one flag, one read.

  python door_gate.py <cc> <region> <market date>            before the store reload: compares CM-KG\DOOR\data (just built) with the store's door/facts.json.
                                                              exit 0 = publish; exit 3 = HOLD (sweep_node.ps1 then uploads pond drops only, DOOR_HOLD=1).
  python door_gate.py us eastus <market date> --after-job     the United States job publishes from inside its container; this compares the job's door/facts.json
                                                              with its previous blob version and, on a drop, copies the new files beside and restores the previous
                                                              versions of door/index.json, door/facts.json and door/nodes.json (blob versioning). exit 0 / 3 as above.
Tenant guard as provision_region.py. Storage keys in memory only."""
import json, os, sys, subprocess, datetime, tempfile
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
cc, region, mdate = sys.argv[1], sys.argv[2], sys.argv[3]; after_job = '--after-job' in sys.argv
node = f'{cc}-cm-kg'; rg = f'allooloo-cmkg-{region}'; sa = f'allooloocmkg{cc}pond'
CONT = os.environ.get('STORAGE_CONTAINER', 'pond')   # ORDER-031 (2026-10-17): 'pond' on the wire, 'staging' for a dry run; default unchanged
FLAGS = r'C:\ALLOOLOO\CM-KG\SWEEPS'
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
    if p.returncode != 0: raise SystemExit(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-300:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az('account', 'show')
if not acct or acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
k = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', rg, '--query', '[0].value', '-o', 'tsv', raw=True)
tmp = tempfile.mkdtemp(prefix=f'gate-{cc}-')
def get(name, version=None):
    p = os.path.join(tmp, name.replace('/', '_') + ('.v' + ''.join(ch for ch in version if ch.isalnum()) if version else ''))
    args = ['storage', 'blob', 'download', '--account-name', sa, '--account-key', k, '-c', CONT, '-n', name, '-f', p, '--no-progress', '-o', 'none'] + (['--version-id', version] if version else [])
    az(*args, raw=True); return p
def put(name, path): az('storage', 'blob', 'upload', '--account-name', sa, '--account-key', k, '-c', CONT, '-n', name, '-f', path, '--overwrite', 'true', '--content-type', 'application/json', '--no-progress', '-o', 'none', raw=True)
def counts(facts_path): f = json.load(open(facts_path, encoding='utf-8')); n = (f.get('nodes') or {}).get(node) or {}; return int(n.get('records') or 0), int(n.get('events') or 0), n.get('as_of')
if after_job:
    vs = az('storage', 'blob', 'list', '--account-name', sa, '--account-key', k, '-c', CONT, '--prefix', 'door/facts.json', '--include', 'v', '--query', "[?name=='door/facts.json'].{v:versionId,cur:isCurrentVersion}") or []
    vs = sorted([x for x in vs if x.get('v')], key=lambda x: x['v'])
    prev = [x for x in vs if not x.get('cur')]
    if not prev: print(f'{node} gate: no previous facts version; publish'); sys.exit(0)
    new = counts(get('door/facts.json')); old = counts(get('door/facts.json', prev[-1]['v']))
else:
    new = counts(r'C:\ALLOOLOO\CM-KG\DOOR\data\facts.json'); old = counts(get('door/facts.json'))
dr, de = new[0] - old[0], new[1] - old[1]
if dr >= 0 and de >= 0:
    print(f'{node} gate: forward (records {old[0]} -> {new[0]}, events {old[1]} -> {new[1]}); publish'); sys.exit(0)
# HOLD — the new index goes beside the old; the door keeps its last good data
held = f'door-held/{mdate}'
if after_job:
    for fn in ('index.json', 'facts.json', 'nodes.json'):
        put(f'{held}/{fn}', get(f'door/{fn}'))
        fv = sorted([x for x in (az('storage', 'blob', 'list', '--account-name', sa, '--account-key', k, '-c', CONT, '--prefix', f'door/{fn}', '--include', 'v', '--query', f"[?name=='door/{fn}'].{{v:versionId,cur:isCurrentVersion}}") or []) if x.get('v') and not x.get('cur')], key=lambda x: x['v'])
        if fv: put(f'door/{fn}', get(f'door/{fn}', fv[-1]['v']))
    note = 'the job had published; index, facts and nodes restored to their previous versions (record blobs the job rewrote stay as written)'
else:
    note = 'nothing published to door/; the store reload runs with DOOR_HOLD=<market date>: pond drops upload as usual, index/facts/nodes are written beside'
line = f"HELD {node} · market date {mdate} · records {old[0]} -> {new[0]} ({dr:+d}) · events {old[1]} -> {new[1]} ({de:+d}) · new index beside at {sa}/pond/{held}/ · {note} · as-of stays {old[2]} until the machine half explains the drop (delisting / window roll / Confirm duplicates) and publishes"
open(os.path.join(FLAGS, f'HELD-{node}-{mdate}.txt'), 'a', encoding='utf-8').write(line + '\n'); print(line); sys.exit(3)
