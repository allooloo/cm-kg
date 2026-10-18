r"""ORDER-031 — assemble the image build context from the laptop tree as it stands (copy, never move; the tree itself is untouched).
Takes only what the jobs run: CM-KG\RAILS (no raw\ junctions, logs, node_modules, caches), AZURE\provision_region.py, CM-KG\DOOR\apex (+static),
CM-KG\DOOR\static, CM-KG\ESTATE (worker + public + wrangler.toml), START_ME_UP\NODE-SURFACES.md, CM-KG\SPEND\SPEND.md, CM-KG\ISSUERS\*.xlsx
(fallback inputs; the job prefers the pond's latest assembled copy), ROOT-CONFIG.json, and the current door facts/nodes as the seed the loader
keeps the other nodes from. Never: AGENT KEYS, .azure, .gh, POND, DISCLOSURE, SWEEPS logs, COMPANY RECORDS.
Usage: python build_context.py <out-dir>   -> <out-dir>\Dockerfile, <out-dir>\shim\, <out-dir>\ALLOOLOO\..."""
import os, sys, shutil, fnmatch
ROOT = r'C:\ALLOOLOO'; HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]; dst = os.path.join(out, 'ALLOOLOO')
if os.path.exists(out): shutil.rmtree(out)
os.makedirs(dst)
SKIP_DIRS = {'raw', 'logs', 'node_modules', '__pycache__', '.wrangler', '.tools', 'certs'}
def ignore(d, names):
    out = set(n for n in names if n in SKIP_DIRS or n.endswith('.pyc') or n.endswith('.log') or '.pre' in n)
    return out
def take(rel, **kw):
    s = os.path.join(ROOT, rel); t = os.path.join(dst, rel)
    if os.path.isdir(s): shutil.copytree(s, t, ignore=ignore, symlinks=False, **kw)
    else: os.makedirs(os.path.dirname(t), exist_ok=True); shutil.copy2(s, t)
take(r'CM-KG\RAILS')
# the raw\ junctions are skipped by name; the job's pond_open creates them fresh
for d in ('AZURE',): os.makedirs(os.path.join(dst, d), exist_ok=True)
take(r'AZURE\provision_region.py'); take(r'AZURE\az_guard.py') if os.path.exists(os.path.join(ROOT, r'AZURE\az_guard.py')) else None
take(r'CM-KG\DOOR\apex'); take(r'CM-KG\DOOR\static'); take(r'CM-KG\ESTATE')
for extra in (r'CM-KG\DOOR\server.json',):
    if os.path.exists(os.path.join(ROOT, extra)): take(extra)
take(r'START_ME_UP\NODE-SURFACES.md'); take(r'CM-KG\SPEND\SPEND.md'); take('ROOT-CONFIG.json')
os.makedirs(os.path.join(dst, r'CM-KG\ISSUERS'), exist_ok=True)
for f in os.listdir(os.path.join(ROOT, r'CM-KG\ISSUERS')):
    if f.endswith('.xlsx') and '.pre' not in f: shutil.copy2(os.path.join(ROOT, r'CM-KG\ISSUERS', f), os.path.join(dst, r'CM-KG\ISSUERS', f))
os.makedirs(os.path.join(dst, r'CM-KG\DOOR\data'), exist_ok=True); os.makedirs(os.path.join(dst, r'CM-KG\DISCLOSURE\events'), exist_ok=True); os.makedirs(os.path.join(dst, r'CM-KG\POND'), exist_ok=True); os.makedirs(os.path.join(dst, r'CM-KG\SWEEPS'), exist_ok=True)
for f in ('facts.json', 'nodes.json'): shutil.copy2(os.path.join(ROOT, r'CM-KG\DOOR\data', f), os.path.join(dst, r'CM-KG\RAILS\job', 'seed-' + f))
shutil.copy2(os.path.join(HERE, 'Dockerfile'), os.path.join(out, 'Dockerfile')); shutil.copytree(os.path.join(HERE, 'shim'), os.path.join(out, 'shim'))
n = sum(len(fs) for _, _, fs in os.walk(out)); sz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(out) for f in fs)
print('context', out, n, 'files', round(sz / 1e6, 1), 'MB')
