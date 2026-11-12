r"""reslate_image.py — RESLATE-01: the fleet image with the Data Research chain and the one job in it. Built FROM the apex job's current image BY DIGEST (the
guarded line: the Tavily guard and everything else in it stay as they are) plus this order's files only. The build stops unless every replaced file in the
image is byte-equal to its .pre copy on disk, and every new file is absent there. Prints the tag and digest; writes reslate-image.json. Nothing is moved.
Usage: python -X utf8 -I reslate_image.py"""
import hashlib, json, os, pathlib, shutil, subprocess, sys, time
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
K = pathlib.Path(r'C:\ALLOOLOO\CM-KG'); H = pathlib.Path(__file__).parent; C = H / 'ctx-reslate'; P = '/job/ALLOOLOO/CM-KG'
def az(*a, raw=False):
    r = subprocess.run([*AZ, *a, '-o', 'tsv' if raw else 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: sys.exit(f'STOP az {" ".join(a[:4])}: {r.stderr[-300:]}')
    return r.stdout.strip() if raw else (json.loads(r.stdout) if r.stdout.strip() else None)
md5 = lambda p: hashlib.md5(p.read_bytes()).hexdigest()
cur = az('containerapp', 'job', 'show', '-n', 'cmkg-apex-rail', '-g', 'allooloo-cmkg-eastus')['properties']['template']['containers'][0]['image']; DIG = cur.split('@')[1]; TAG = 'reslate01b-' + DIG[7:19]
REPLACED = [('RAILS/job/job_node.py', 'RAILS/job/job_node.py.pre-reslate01-2026-11-12')] + [(f'ESTATE/worker/{n}.js', f'ESTATE/worker/{n}.pre-reslate01-2026-11-12.js') for n in ('site', 'about-copy', 'asof', 'doors027', 'zones02', 'nodes', 'nav02', 'tm-copy', 'radar')]
NEW = ['RAILS/job/job_reslate.py', 'NODE-GATE/worker/stampclass.js', 'NODE-GATE/worker/classes.js', 'RESEARCH/venues.json'] + [f'RAILS/research/{n}' for n in ('pull.py', 'rollup.py', 'orderability.mjs', 'coverage.py', 'write.py', 'publish.py', 'exchange.py', 'chain.py', 'publish_stores.py', 'density.py')]
FORCE = ['ESTATE/worker/research.js']   # this order line's own file, already in the image from USR-03: taken as it stands on disk
if az('acr', 'repository', 'show-tags', '-n', 'allooloocmkg', '--repository', 'cmkg-sweep', '--query', f"[?@=='{TAG}']", raw=True): sys.exit(f'STOP {TAG} exists: an image tag is never overwritten')
if C.exists(): shutil.rmtree(C)
C.mkdir(); L = [f'FROM allooloocmkg.azurecr.io/cmkg-sweep@{DIG}']
L.append('RUN ' + ' && '.join([f'echo "{md5(K / pre)}  {P}/{f}" | md5sum -c -' for f, pre in REPLACED] + [f'test ! -e {P}/{f}' for f in NEW] + ['test -e /opt/tavily_guard/tavily_guard.py']))
for f in [f for f, _ in REPLACED] + NEW + FORCE:
    d = C / f; d.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(K / f, d); L.append(f'COPY {f} {P}/{f}')
L.append('RUN ' + ' && '.join(f'echo "{md5(K / f)}  {P}/{f}" | md5sum -c -' for f in [f for f, _ in REPLACED] + NEW + FORCE) + f' && mkdir -p {P}/RESEARCH/pages {P}/RESEARCH/numbers {P}/RESEARCH/orderability {P}/RESEARCH/exchanges {P}/RESEARCH/published && node --check {P}/RAILS/research/orderability.mjs && python3 -m py_compile {P}/RAILS/job/job_reslate.py {P}/RAILS/job/job_node.py {P}/RAILS/research/chain.py')
(C / 'Dockerfile').write_text('\n'.join(L) + '\n', encoding='utf-8', newline='\n')
r = subprocess.run([*AZ, 'acr', 'build', '-r', 'allooloocmkg', '-t', f'cmkg-sweep:{TAG}', str(C)], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace'); (H / f'image-{TAG}.log').write_text(r.stdout + r.stderr, encoding='utf-8')
if r.returncode: sys.exit('STOP acr build: ' + (r.stdout + r.stderr)[-900:])
nd = az('acr', 'repository', 'show', '-n', 'allooloocmkg', '--image', f'cmkg-sweep:{TAG}', '--query', 'digest', raw=True)
json.dump({'base': cur, 'tag': TAG, 'digest': nd, 'image': f'allooloocmkg.azurecr.io/cmkg-sweep@{nd}', 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, open(H / 'reslate-image.json', 'w'), indent=1); print('image', TAG, nd)
