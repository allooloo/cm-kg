r"""fleet_build_c.py — FIX-01: the fleet image with (a) the Tavily meter shared out in the one job (job_reslate.py) and (b) the digest reading the fleet
tag from the capacity snapshot (job_digest.py). FROM the fleet image by digest + those two files only; the build checks each file it replaces against
its .pre copy. Then the 34 market rails and the one job move to it by digest (a running execution keeps its image).
Usage: python -X utf8 -I fleet_build_c.py"""
import hashlib, json, os, pathlib, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
H = pathlib.Path(__file__).parent; J = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\job'); md5 = lambda p: hashlib.md5(pathlib.Path(p).read_bytes()).hexdigest(); BASE = json.load(open(H / 'fleet-image-b.json'))['image']
FILES = {'job_reslate.py': 'job_reslate.pre-fix01-2026-11-12.py', 'job_digest.py': 'job_digest.pre-fix01drift-2026-11-12.py'}; P = '/job/ALLOOLOO/CM-KG/RAILS/job/'
def az(*a, js=False):
    r = subprocess.run([*AZ, *a, '-o', 'json' if js else 'tsv'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: sys.exit(f'STOP az {" ".join(a[:4])}: {(r.stdout + r.stderr)[-900:]}')
    return json.loads(r.stdout) if js else r.stdout.strip()
out = H / 'fleet-image-c.json'
if not out.exists():
    C = H / 'ctx-fleet-c'; shutil.rmtree(C, ignore_errors=True); C.mkdir()
    for f in FILES: shutil.copy2(J / f, C / f)
    L = [f'FROM {BASE}', 'RUN ' + ' && '.join(f'echo "{md5(J / pre)}  {P}{f}" | md5sum -c -' for f, pre in FILES.items()), f'COPY {" ".join(FILES)} {P}',
         'RUN ' + ' && '.join(f'echo "{md5(J / f)}  {P}{f}" | md5sum -c -' for f in FILES) + f' && python3 -m py_compile {P}job_reslate.py {P}job_digest.py']
    (C / 'Dockerfile').write_text(chr(10).join(L) + chr(10), encoding='utf-8', newline=chr(10))
    tag = 'cmkg-sweep:fix01-' + BASE.split('sha256:')[1][:12]; az('acr', 'build', '-r', 'allooloocmkg', '-t', tag, '--no-logs', str(C)); d = az('acr', 'repository', 'show', '-n', 'allooloocmkg', '--image', tag, '--query', 'digest')
    json.dump({'image': f'allooloocmkg.azurecr.io/cmkg-sweep@{d}', 'tag': tag, 'base': BASE}, open(out, 'w')); print(tag, d)
IMG = json.load(open(out))['image']; todo = [j for j in az('containerapp', 'job', 'list', js=True) if re.fullmatch(r'cmkg-([a-z]{2}|apex)-rail', j['name'])]
def move(j):
    cur = j['properties']['template']['containers'][0]['image']
    if cur == IMG: return j['name'], 'already'
    if cur != BASE: return j['name'], 'SKIPPED ' + cur[-16:]
    o = az('containerapp', 'job', 'update', '-n', j['name'], '-g', j['resourceGroup'], '--image', IMG, js=True); return j['name'], 'moved' if o['properties']['template']['containers'][0]['image'] == IMG else 'FAILED'
with ThreadPoolExecutor(6) as ex: res = list(ex.map(move, todo))
print(len(res), 'jobs;', sum(r[1] == 'moved' for r in res), 'moved;', sum(r[1] == 'already' for r in res), 'already; not moved:', [r for r in res if r[1] not in ('moved', 'already')])
