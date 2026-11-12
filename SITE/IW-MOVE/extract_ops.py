import base64, io, os, re, subprocess, sys, tarfile
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']; NEW = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); HERE = os.path.dirname(os.path.abspath(__file__))
for k, img in (('ops-fix', 'iw-ops-rails:fix-20261103'), ('ops-iw01', 'iw-ops-rails:iw01-10262245'), ('ops-nightly02', 'iw-ops-rails:nightly02-11011600')):
    y = os.path.join(HERE, f'extract-{k}.yaml')
    open(y, 'w', encoding='utf-8', newline='\n').write("version: v1.1.0\nsteps:\n  - cmd: allooloocmkg.azurecr.io/" + img + " -c 'echo @@BEGIN@@; tar czf - --exclude=__pycache__ --exclude=site-packages /job /app 2>/dev/null | base64 -w 0; echo; echo @@FINISH@@'\n    entryPoint: sh\n    timeout: 600\n")
    r = subprocess.run([*AZ, 'acr', 'run', '-r', 'allooloocmkg', '-f', y, '/dev/null'], capture_output=True, text=True, env=NEW, encoding='utf-8', errors='replace'); out = r.stdout or ''
    m = re.search(r'@@BEGIN@@\s*(.*?)\s*@@FINISH@@', out, re.S)
    if not m: print(k, 'NOT EXTRACTED', r.returncode, (out + (r.stderr or ''))[-300:]); continue
    d = os.path.join(HERE, 'extracted', k); os.makedirs(d, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(re.sub(r'[^A-Za-z0-9+/=]', '', m.group(1)))), mode='r:gz') as t: n = t.getnames(); t.extractall(d)
    print(k, 'extracted', len(n), [x for x in n if x.endswith('.py')][:10], flush=True)
