r"""ORDER-031 — the laptop side of the repo write. The apex job lands sweepREVIEW-<date>.md, NODE-SURFACES.md, SPEND.md, numbers-log.json and the
apex index/nodes in the shared store (allooloocmkgapex/sweeps/<market date>/...); this pulls them into the repo, new beside old:
  START_ME_UP\sweepREVIEW-<date>.md (written only if absent), NODE-SURFACES.md NUMBERS LOG block = union of lines (never a line removed),
  CM-KG\SPEND\SPEND.md = union of lines, numbers-log.json mirrored, apex static index/nodes refreshed (.pre-<date> copies beside).
Usage: python pull_sweep.py <market date>     (AZURE_CONFIG_DIR = C:\ALLOOLOO\.azure; tenant guard as the rails)"""
import os, sys, json, re, subprocess, shutil, datetime
ROOT = r'C:\ALLOOLOO'; TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
mdate = sys.argv[1]; datetime.date.fromisoformat(mdate); stamp = datetime.date.today().strftime('%Y%m%d')
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=(os.name == 'nt'))
    if p.returncode != 0: raise SystemExit(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-300:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az('account', 'show')
if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
from azure.storage.blob import BlobServiceClient
key = az('storage', 'account', 'keys', 'list', '-n', 'allooloocmkgapex', '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True)
c = BlobServiceClient('https://allooloocmkgapex.blob.core.windows.net', credential=key).get_container_client('sweeps')
def get(n):
    try: return c.get_blob_client(f'{mdate}/{n}').download_blob().readall().decode('utf-8')
    except Exception: return None
def pre(p):
    if os.path.exists(p): shutil.copy2(p, p + f'.pre-pull-{stamp}')
rep = get(f'sweepREVIEW-{mdate}.md')
if rep is None: raise SystemExit(f'no sweepREVIEW-{mdate}.md in the apex store yet (the apex job has not closed {mdate})')
rp = os.path.join(ROOT, 'START_ME_UP', f'sweepREVIEW-{mdate}.md')
if os.path.exists(rp): print('report already in the repo, left as is:', rp)
else: open(rp, 'w', encoding='utf-8').write(rep); print('report written', rp)
def union_block(path, remote, rx):
    local = open(path, encoding='utf-8').read(); ml = re.search(rx, local); mr = re.search(rx, remote)
    if not (ml and mr): print('block not found, skipped:', path); return
    have = [l for l in ml.group(2).splitlines() if l.strip()]; new = [l for l in mr.group(2).splitlines() if l.strip() and l not in have]
    if not new: print('no new lines:', path); return
    pre(path); open(path, 'w', encoding='utf-8').write(local[:ml.start(2)] + '\n'.join(have + new) + '\n' + local[ml.start(3):]); print(f'{len(new)} lines added:', path)
ns = get('NODE-SURFACES.md')
if ns: union_block(os.path.join(ROOT, 'START_ME_UP', 'NODE-SURFACES.md'), ns, r'(## 9 NUMBERS LOG[\s\S]*?```\n)([\s\S]*?)(```)')
sp = get('SPEND.md')
if sp: union_block(os.path.join(ROOT, 'CM-KG', 'SPEND', 'SPEND.md'), sp, r'(```\n)([\s\S]*?)(```)')
for n, dst in (('numbers-log.json', os.path.join(ROOT, 'CM-KG', 'ESTATE', 'public', 'numbers-log.json')), ('apex-index.json', os.path.join(ROOT, 'CM-KG', 'DOOR', 'apex', 'static', 'index.json')), ('apex-nodes.json', os.path.join(ROOT, 'CM-KG', 'DOOR', 'apex', 'static', 'nodes.json'))):
    b = get(n)
    if b is not None: pre(dst); open(dst, 'w', encoding='utf-8').write(b); print('mirrored', dst)
d = get('apex-done.json'); print(json.loads(d)['close_line'] if d else 'no apex-done.json')
