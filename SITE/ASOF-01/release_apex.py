r"""release_apex.py — ASOF-01: the apex side of the 0.35.56 release, run by the agent under C:\ALLOOLOO\.azure. A step that fails stops the run.
  1  cmkg-apex-rail to 0.35.56 (provision_jobs.py upgrade 0.35.56 apex: image and IMAGE_TAG only)
  2  cmkg-apex-digest and cmkg-apex-week to 0.35.56 (image and IMAGE_TAG; FLEET_TAG already 0.35.56 from fleet_move)
  3  capacity_snapshot.py (the digest's DRIFT reads the job definitions from it)
  4  the apex rail, one run (deploys cm-kg-apex and estate-pages from the image); waits until it ends Succeeded
  5  waits (up to 20 minutes) until mcp.getasof.ai/mcp... is not yet routed: reads the router version on mcp.getissuer.ai (0.24.0) and getissuer.ai's surface (2026-11-05.1)
Usage: python -X utf8 -I release_apex.py"""
import os, sys, json, time, subprocess, urllib.request
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
J = r'C:\ALLOOLOO\CM-KG\RAILS\job'; RG = 'allooloo-cmkg-eastus'; TAG = '0.35.56'; IMG = f'allooloocmkg.azurecr.io/cmkg-sweep:{TAG}'
def say(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def stop(m): say('STOP:', m, '— nothing after it ran'); sys.exit(1)
def az(*a):
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: stop(f'az {" ".join(a[:4])}: {r.stderr[-300:]}')
    return json.loads(r.stdout) if r.stdout.strip() else None
def py(script, *a):
    r = subprocess.run([sys.executable, '-X', 'utf8', script, *a], cwd=J, env=ENV, capture_output=True, text=True, encoding='utf-8', errors='replace')
    say(os.path.basename(script), 'exit', r.returncode, (r.stdout or '').strip().splitlines()[-2:]);
    if r.returncode: stop(f'{script} {a}: {(r.stderr or r.stdout)[-300:]}')
py('provision_jobs.py', 'upgrade', TAG, 'apex')
for j in ('cmkg-apex-digest', 'cmkg-apex-week'):
    az('containerapp', 'job', 'update', '-n', j, '-g', RG, '--image', IMG, '--set-env-vars', f'IMAGE_TAG={TAG}')
    c = az('containerapp', 'job', 'show', '-n', j, '-g', RG)['properties']['template']['containers'][0]; e = {x['name']: x.get('value') for x in c.get('env', [])}
    say(j, c['image'].split(':')[-1], 'IMAGE_TAG', e.get('IMAGE_TAG'), 'FLEET_TAG', e.get('FLEET_TAG'))
    if not c['image'].endswith(TAG): stop(f'{j} not on {TAG}')
py('capacity_snapshot.py')
x = az('containerapp', 'job', 'start', '-n', 'cmkg-apex-rail', '-g', RG); name = x.get('name') or x.get('id', '').split('/')[-1]; say('apex rail started', name)
t0 = time.time()
while True:
    ex = [e for e in az('containerapp', 'job', 'execution', 'list', '-n', 'cmkg-apex-rail', '-g', RG) if e['name'] == name]
    st = ex[0]['properties']['status'] if ex else 'unknown'
    if st == 'Succeeded': say('apex rail', name, st); break
    if st in ('Failed', 'Stopped', 'Degraded'): stop(f'apex rail {name} {st}')
    if time.time() - t0 > 3600: stop(f'apex rail {name} still {st} after 60 minutes')
    time.sleep(30)
UA = {'User-Agent': 'Allooloo ASOF-01 release wait', 'Cache-Control': 'no-cache', 'content-type': 'application/json'}
t0 = time.time()
while True:
    try:
        v = json.loads(urllib.request.urlopen(urllib.request.Request('https://mcp.getissuer.ai/mcp', data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}}).encode(), headers=UA, method='POST'), timeout=30).read())['result']['serverInfo']['version']
        sv = urllib.request.urlopen(urllib.request.Request('https://getissuer.ai/', headers=UA), timeout=30).headers.get('X-Surface-Version')
    except Exception as e: v, sv = repr(e)[:60], None
    if v == '0.24.0' and sv == '2026-11-05.1': say('live: router', v, '· estate', sv); break
    if time.time() - t0 > 1200: stop(f'router {v} / estate {sv} after 20 minutes')
    time.sleep(30)
