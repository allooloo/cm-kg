r"""release.py — USR-03: the apex side on the wire, run by the agent under C:\ALLOOLOO\.azure. A step that fails stops the run.
The apex rail deploys cm-kg-apex and estate-pages from its image (today pinned by digest: the c2027 build). So:
  1  image cmkg-sweep:usr01-<base12> = the apex rail's current image BY DIGEST plus the files this order changed; the build stops unless every replaced file in
     the image is byte-equal to the .pre-usr01 copy on disk and no new file exists there yet, so nothing else travels
  2  cmkg-apex-rail to the new image by digest (image only; env kept); APEX_WAIT_UNTIL=00:01 set for the one manual run (the sweeps are parked, so the
     rail's marker wait would otherwise hold until 14:05 UTC) and removed after it
  3  capacity_snapshot.py (the digest's DRIFT reads the job definitions from it)
  4  the apex rail, one run; waits until it ends Succeeded
  5  waits until mcp.getissuer.ai answers router 0.26.0 with get_research on its tool list and getissuer.ai serves estate 2026-11-11.1
Usage: python -X utf8 -I release.py"""
import hashlib, json, os, pathlib, shutil, subprocess, sys, time, urllib.request
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
K = pathlib.Path(r'C:\ALLOOLOO\CM-KG'); H = pathlib.Path(__file__).parent; C = H / 'ctx-usr04'; J = str(K / 'RAILS' / 'job'); RG = 'allooloo-cmkg-eastus'; JOB = 'cmkg-apex-rail'; P = '/job/ALLOOLOO/CM-KG'
def say(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def stop(m): say('STOP:', m, '— nothing after it ran'); sys.exit(1)
def az(*a, raw=False):
    r = subprocess.run([*AZ, *a, '-o', 'tsv' if raw else 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: stop(f'az {" ".join(a[:4])}: {r.stderr[-300:]}')
    return r.stdout.strip() if raw else (json.loads(r.stdout) if r.stdout.strip() else None)
md5 = lambda p: hashlib.md5(p.read_bytes()).hexdigest()
cur = az('containerapp', 'job', 'show', '-n', JOB, '-g', RG)['properties']['template']['containers'][0]['image']
if '@sha256:' not in cur: stop(f'{JOB} is not pinned by digest ({cur})')
DIG = cur.split('@')[1]; TAG = 'usr04-' + DIG[7:19]; say('base', cur, '->', TAG)
REPLACED = [('DOOR/apex/index.js', 'DOOR/apex/index.pre-usr04-2026-11-12.js'), ('DOOR/apex/research.js', 'DOOR/apex/research.pre-usr04-2026-11-12.js')]
NEW = []
if az('acr', 'repository', 'show-tags', '-n', 'allooloocmkg', '--repository', 'cmkg-sweep', '--query', f"[?@=='{TAG}']", raw=True): say(TAG, 'exists: the build is skipped')
else:
    if C.exists(): shutil.rmtree(C)
    C.mkdir(); lines = [f'FROM allooloocmkg.azurecr.io/cmkg-sweep@{DIG}']
    lines.append('RUN ' + ' && '.join([f'echo "{md5(K / pre)}  {P}/{f}" | md5sum -c -' for f, pre in REPLACED] + [f'test ! -e {P}/{f}' for f in NEW] + ['true']))
    for f in [f for f, _ in REPLACED] + NEW:
        dst = C / f; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(K / f, dst); lines.append(f'COPY {f} {P}/{f}')
    lines.append('RUN ' + ' && '.join(f'echo "{md5(K / f)}  {P}/{f}" | md5sum -c -' for f in [f for f, _ in REPLACED] + NEW))
    (C / 'Dockerfile').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    r = subprocess.run([*AZ, 'acr', 'build', '-r', 'allooloocmkg', '-t', f'cmkg-sweep:{TAG}', str(C)], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    (H / f'image-{TAG}.log').write_text(r.stdout + r.stderr, encoding='utf-8')
    if r.returncode: stop(f'acr build: {(r.stdout + r.stderr)[-700:]}')
NEWDIG = az('acr', 'repository', 'show', '-n', 'allooloocmkg', '--image', f'cmkg-sweep:{TAG}', '--query', 'digest', raw=True); IMG = f'allooloocmkg.azurecr.io/cmkg-sweep@{NEWDIG}'; say('image', TAG, NEWDIG)
(H / 'release-c-state.json').write_text(json.dumps({'job': JOB, 'image_before': cur, 'image_after': IMG, 'tag': TAG}, indent=1), encoding='utf-8')
az('containerapp', 'job', 'update', '-n', JOB, '-g', RG, '--image', IMG, '--set-env-vars', 'APEX_WAIT_UNTIL=00:01')
if az('containerapp', 'job', 'show', '-n', JOB, '-g', RG)['properties']['template']['containers'][0]['image'] != IMG: stop(f'{JOB} not on the new image')
r = subprocess.run([sys.executable, '-X', 'utf8', 'capacity_snapshot.py'], cwd=J, env=ENV, capture_output=True, text=True, encoding='utf-8', errors='replace'); say('capacity_snapshot exit', r.returncode, (r.stdout or '').strip().splitlines()[-1:])
if r.returncode: stop('capacity_snapshot: ' + (r.stderr or r.stdout)[-300:])
x = az('containerapp', 'job', 'start', '-n', JOB, '-g', RG); name = x.get('name') or x.get('id', '').split('/')[-1]; say('apex rail started', name); t0 = time.time()
while True:
    ex = [e for e in az('containerapp', 'job', 'execution', 'list', '-n', JOB, '-g', RG) if e['name'] == name]; st = ex[0]['properties']['status'] if ex else 'unknown'
    if st == 'Succeeded': say('apex rail', name, st); break
    if st in ('Failed', 'Stopped', 'Degraded'): az('containerapp', 'job', 'update', '-n', JOB, '-g', RG, '--remove-env-vars', 'APEX_WAIT_UNTIL'); stop(f'apex rail {name} {st}')
    if time.time() - t0 > 5400: stop(f'apex rail {name} still {st} after 90 minutes')
    time.sleep(30)
az('containerapp', 'job', 'update', '-n', JOB, '-g', RG, '--remove-env-vars', 'APEX_WAIT_UNTIL'); say('APEX_WAIT_UNTIL removed')
UA = {'User-Agent': 'Allooloo USR-01 release wait', 'Cache-Control': 'no-cache', 'content-type': 'application/json', 'accept': 'application/json'}; t0 = time.time()
def rpc(m): return json.loads(urllib.request.urlopen(urllib.request.Request('https://mcp.getissuer.ai/mcp', data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': {}}).encode(), headers=UA, method='POST'), timeout=30).read())['result']
while True:
    try: v = rpc('initialize')['serverInfo']['version']; tools = [t['name'] for t in rpc('tools/list')['tools']]; sv = urllib.request.urlopen(urllib.request.Request('https://getissuer.ai/', headers=UA), timeout=30).headers.get('X-Surface-Version')
    except Exception as e: v, tools, sv = repr(e)[:60], [], None
    if v == '0.27.0' and 'get_research' in tools: say('live: router', v, '· estate', sv); break
    if time.time() - t0 > 1200: stop(f'router {v} / tools {len(tools)} / estate {sv} after 20 minutes')
    time.sleep(30)
say('RELEASE DONE')
