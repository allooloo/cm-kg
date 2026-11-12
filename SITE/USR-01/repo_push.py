r"""repo_push.py — USR-03: commit and push the code of the surfaces this order touched to allooloo/cm-kg (public, code only — CEO 2026-10-18), the way
CHAIN-CLOSE's chainclose_commit.py does: the files are taken whole as they stand on the laptop tree (so earlier uncommitted work in the same files rides along),
.pre-* anchors left untracked, the ops rule (ops_split.is_ops) applied, every staged file key-shape scanned first (public_scan.py's patterns; a hit stops).
Folders: CM-KG/NODE-GATE/worker · CM-KG/DOOR/apex (js) · CM-KG/ESTATE/worker · CM-KG/DOOR/getasof · CM-KG/DOOR/getdoors · SITE/DOORS-01 (code). Usage: python -I -X utf8 repo_push.py plan|commit"""
import os, re, sys, subprocess
MODE = sys.argv[1]; ROOT = r'C:\ALLOOLOO'
src = open(os.path.join(ROOT, r'CM-KG\RAILS\job\ops_split.py'), encoding='utf-8').read(); ns = {}; exec(src.split('def ls():')[0], ns); is_ops = ns['is_ops']
ps = open(os.path.join(ROOT, r'CM-KG\RAILS\job\public_scan.py'), encoding='utf-8').read(); PAT = eval(ps[ps.index('PAT = ') + 6: ps.index('}\n', ps.index('PAT = ')) + 1])
CODE = ('.py', '.js', '.mjs', '.toml', '.json'); DIRS = ['CM-KG/DOOR/apex', 'CM-KG/ESTATE/worker', 'CM-KG/DOOR/getresearch', 'CM-KG/RAILS/research', 'CM-KG/RAILS/job/job_node.py', 'CM-KG/RAILS/job/job_reslate.py', 'CM-KG/DOOR/server.json', 'SITE/USR-01']
MSG = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commit-msg.txt'), encoding='utf-8').read()
def git(*a, check=True):
    r = subprocess.run(['git', '-c', 'core.quotepath=false', *a], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode: raise SystemExit(f'git {a[:3]}: {(r.stderr or r.stdout)[-400:]}')
    return r.stdout
st = [l for l in git('status', '--porcelain', '--untracked-files=all', '--', *DIRS).splitlines() if l.strip()]
take = []
for l in st:
    p = l[3:].strip().strip('"')
    if '.pre' in os.path.basename(p) or '/backup/' in p or '/__pycache__/' in p or '/static/' in p or '/ctx-' in p: continue
    if p.startswith('SITE/USR-01/') and not p.endswith(('.py', '.mjs')): continue
    if not p.endswith(CODE) or is_ops(p): continue
    take.append(p)
hits = []
for p in take:
    t = open(os.path.join(ROOT, p), encoding='utf-8', errors='replace').read()
    for k, rx in PAT.items():
        if re.search(rx, t): hits.append((p, k))
print(len(take), 'files ·', 'scan hits:', hits or 'none'); [print(' ', p) for p in take]
if hits: raise SystemExit('STOP: a key-shaped string in a staged file')
if MODE == 'commit':
    git('add', '--', *take); git('commit', '-m', MSG); print(git('log', '-1', '--format=%h %s')); r = subprocess.run(['git', 'push', 'origin', 'HEAD'], cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, GH_CONFIG_DIR=r'C:\ALLOOLOO\.gh'))
    print('push exit', r.returncode, (r.stderr or r.stdout)[-300:])
    if r.returncode: sys.exit(1)
