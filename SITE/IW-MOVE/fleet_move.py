r"""fleet_move.py — the 34 market rails and the one job onto the fleet image that carries the coverage rail with the Grok second read struck (RESLATE-01,
CEO 2026-11-12) and Issuerwire's Ops Agents (IW-MOVE-01). Image by digest only; nothing else on a job changes. A running execution keeps the image it
started on. Usage: python -X utf8 -I fleet_move.py"""
import json, os, subprocess, sys, pathlib, re
from concurrent.futures import ThreadPoolExecutor
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
H = pathlib.Path(__file__).parent; F = json.load(open(H / 'fleet-image.json')); IMG, BASE = F['image'], F['base']
def az(*a):
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    return r.returncode, (json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None), r.stderr[-300:]
rc, jobs, err = az('containerapp', 'job', 'list')
if rc: sys.exit('STOP list ' + err)
todo = [j for j in jobs if re.fullmatch(r'cmkg-([a-z]{2}|apex)-rail', j['name'])]
json.dump([{'name': j['name'], 'rg': j['resourceGroup'], 'image': j['properties']['template']['containers'][0]['image']} for j in todo], open(H / 'fleet-before-move.json', 'w'), indent=1)
def move(j):
    cur = j['properties']['template']['containers'][0]['image']
    if cur == IMG: return j['name'], 'already'
    if cur != BASE: return j['name'], 'SKIPPED: not on the base image ' + cur[-20:]
    rc, o, err = az('containerapp', 'job', 'update', '-n', j['name'], '-g', j['resourceGroup'], '--image', IMG)
    return j['name'], 'moved' if rc == 0 and o['properties']['template']['containers'][0]['image'] == IMG else 'FAILED ' + err
with ThreadPoolExecutor(6) as ex: res = list(ex.map(move, todo))
bad = [r for r in res if r[1] not in ('moved', 'already')]
print(len(res), 'jobs;', sum(r[1] == 'moved' for r in res), 'moved;', sum(r[1] == 'already' for r in res), 'already;', 'not moved:', bad)
