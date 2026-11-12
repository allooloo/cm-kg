r"""iw_images.py — IW-MOVE-01 step 1 (images): Issuerwire's images as they run today, imported registry to registry (gscemregistry in the other directory ->
allooloocmkg in the Allooloo subscription) by digest or tag, on a short-lived registry token made from the sign-in already granted (az acr login
--expose-token; in-process, never printed). Then the source files of each image are read out of the imported copy (an ACR run that tars /app and /job to
the run log, base64) into extracted\<image>\ so the key change is made against the code as deployed. Usage: python -X utf8 -I iw_images.py import|extract"""
import base64, io, json, os, subprocess, sys, tarfile, re
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
OLD = dict(os.environ, AZURE_CONFIG_DIR=r'C:\A2AAMN\.azure'); NEW = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = {'door': 'a2a-amn@sha256:9f305377a993d7b37e638ab8289f269660f6933de44a72218d6483e5f8531c5d', 'ops-iw01': 'amn-ops-rails:iw01-10262245', 'ops-fix': 'amn-ops-rails:fix-20261103', 'ops-nightly02': 'amn-ops-rails:nightly02-11011600'}
TARGET = {'door': 'iw-door:from-old-9f305377', 'ops-iw01': 'iw-ops-rails:iw01-10262245', 'ops-fix': 'iw-ops-rails:fix-20261103', 'ops-nightly02': 'iw-ops-rails:nightly02-11011600'}
def run(env, *a, hide=None):
    r = subprocess.run([*AZ, *a], capture_output=True, text=True, env=env, encoding='utf-8', errors='replace'); out, err = r.stdout or '', r.stderr or ''
    if hide: out, err = out.replace(hide, '***'), err.replace(hide, '***')
    return r.returncode, out, err
if sys.argv[1] == 'import':
    rc, out, err = run(OLD, 'acr', 'login', '-n', 'gscemregistry', '--subscription', '9e406344-81a4-4624-98de-a9c642a75d69', '--expose-token', '-o', 'json'); tok = json.loads(out)['accessToken']
    for k, src in IMAGES.items():
        rc, out, err = run(NEW, 'acr', 'import', '-n', 'allooloocmkg', '--source', 'gscemregistry.azurecr.io/' + src, '--image', TARGET[k], '--username', '00000000-0000-0000-0000-000000000000', '--password', tok, hide=tok)
        print(k, src, '->', TARGET[k], 'exit', rc, '' if rc == 0 else ('already present' if 'already exists' in err else err[-200:]), flush=True)
    del tok
    for k in IMAGES:
        rc, out, err = run(NEW, 'acr', 'repository', 'show', '-n', 'allooloocmkg', '--image', TARGET[k], '--query', 'digest', '-o', 'tsv'); print(TARGET[k], out.strip())
if sys.argv[1] == 'extract':
    for k in sys.argv[2:] or IMAGES:
        # the markers are assembled by the shell (BEG + IN), so the command line echoed into the run log never contains them
        cmd = f'allooloocmkg.azurecr.io/{TARGET[k]} sh -c "echo @@BEGIN@@; tar czf - --exclude=__pycache__ --exclude=node_modules --exclude=site-packages /app /job 2>/dev/null | base64 -w 0; echo; echo @@FINISH@@"'   # no dollar sign: the registry's run templating consumes them
        rc, out, err = run(NEW, 'acr', 'run', '-r', 'allooloocmkg', '--cmd', cmd, '/dev/null'); open(os.path.join(HERE, f'extract-{k}.raw.log'), 'w', encoding='utf-8').write(out[-3000:] + '\n=====\n' + err[-2000:])
        m = re.search(r'@@BEGIN@@\s*(.*?)\s*@@FINISH@@', out, re.S)
        if not m: print(k, 'NOT EXTRACTED', rc, (out + err)[-400:]); continue
        b = re.sub(r'[^A-Za-z0-9+/=]', '', m.group(1)); d = os.path.join(HERE, 'extracted', k); os.makedirs(d, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(base64.b64decode(b)), mode='r:gz') as t: names = t.getnames(); t.extractall(d)
        print(k, 'extracted', len(names), 'files', [n for n in names if n.endswith(('.py', '.json'))][:12], flush=True)
