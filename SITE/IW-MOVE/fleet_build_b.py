r"""fleet_build_b.py — the fleet image with the one weekly job as it now stands: the page-store publish step run from the research folder (RESLATE-01) and
Issuerwire's cycle (IW-MOVE-01 step 8). FROM the fleet image by digest + job_reslate.py only; the build checks the file it replaces against the .pre copy.
Then the 34 market rails and the one job move to it by digest (a running execution keeps its image). Usage: python -X utf8 -I fleet_build_b.py"""
import hashlib, json, os, pathlib, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
H = pathlib.Path(__file__).parent; J = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\job'); md5 = lambda p: hashlib.md5(pathlib.Path(p).read_bytes()).hexdigest(); BASE = json.load(open(H / 'fleet-image.json'))['image']
def az(*a, js=False):
    r = subprocess.run([*AZ, *a, '-o', 'json' if js else 'tsv'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: sys.exit(f'STOP az {" ".join(a[:4])}: {(r.stdout + r.stderr)[-700:]}')
    return json.loads(r.stdout) if js else r.stdout.strip()
out = H / 'fleet-image-b.json'
if not out.exists():
    C = H / 'ctx-fleet-b'; shutil.rmtree(C, ignore_errors=True); C.mkdir(); shutil.copy2(J / 'job_reslate.py', C / 'job_reslate.py'); P = '/job/ALLOOLOO/CM-KG/RAILS/job/job_reslate.py'
    (C / 'Dockerfile').write_text('\n'.join([f'FROM {BASE}', f'RUN echo "{md5(J / "job_reslate.pre-kvpublish-2026-11-12.py")}  {P}" | md5sum -c -', f'COPY job_reslate.py {P}',
        f'RUN echo "{md5(J / "job_reslate.py")}  {P}" | md5sum -c - && python3 -m py_compile {P}']) + '\n', encoding='utf-8', newline='\n')
    tag = 'cmkg-sweep:iwmove01b-' + BASE.split('sha256:')[1][:12]; az('acr', 'build', '-r', 'allooloocmkg', '-t', tag, '--no-logs', str(C)); d = az('acr', 'repository', 'show', '-n', 'allooloocmkg', '--image', tag, '--query', 'digest')
    json.dump({'image': f'allooloocmkg.azurecr.io/cmkg-sweep@{d}', 'tag': tag, 'base': BASE}, open(out, 'w')); print(tag, d)
IMG = json.load(open(out))['image']; todo = [j for j in az('containerapp', 'job', 'list', js=True) if re.fullmatch(r'cmkg-([a-z]{2}|apex)-rail', j['name'])]
def move(j):
    cur = j['properties']['template']['containers'][0]['image']
    if cur == IMG: return j['name'], 'already'
    if cur != BASE: return j['name'], 'SKIPPED ' + cur[-16:]
    o = az('containerapp', 'job', 'update', '-n', j['name'], '-g', j['resourceGroup'], '--image', IMG, js=True); return j['name'], 'moved' if o['properties']['template']['containers'][0]['image'] == IMG else 'FAILED'
with ThreadPoolExecutor(6) as ex: res = list(ex.map(move, todo))
print(len(res), 'jobs;', sum(r[1] == 'moved' for r in res), 'moved;', sum(r[1] == 'already' for r in res), 'already; not moved:', [r for r in res if r[1] not in ('moved', 'already')])
