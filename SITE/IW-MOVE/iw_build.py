r"""iw_build.py — IW-MOVE-01 step 1 (images), built in the Allooloo registry, each FROM a running image BY DIGEST plus this order's files only.
  door    iw-door:iwmove01 = the door image as it runs on the old side (sha256:9f305377…) + the patched server.py, ledger.py, x402.py, iw.py, pages.py,
          jwks.json and the new x402-old-keys.json. The build checks each replaced file against the copy read out of the image, so nothing else moves.
  fleet   cmkg-sweep:iwmove01-<base12> = the research fleet image + psycopg (the one package Issuerwire's Ops Agents need that it lacks) + the three
          Ops Agents builds as they run today, patched the same way, each under /job/iw/<build>/ops (iw01 · nightly02 · fix) so each job runs the build it
          runs on the old side; and RAILS/research/coverage.py with the Grok second read struck (RESLATE-01, CEO 2026-11-12).
Usage: python -X utf8 -I iw_build.py door|fleet"""
import hashlib, json, os, pathlib, shutil, subprocess, sys
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
H = pathlib.Path(__file__).parent; md5 = lambda p: hashlib.md5(pathlib.Path(p).read_bytes()).hexdigest(); what = sys.argv[1]
def az(*a, raw=True):
    r = subprocess.run([*AZ, *a, '-o', 'tsv'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: sys.exit(f'STOP az {" ".join(a[:4])}: {(r.stdout + r.stderr)[-700:]}')
    return r.stdout.strip()
def build(ctx, tag):
    az('acr', 'build', '-r', 'allooloocmkg', '-t', tag, '--no-logs', str(ctx)); d = az('acr', 'repository', 'show', '-n', 'allooloocmkg', '--image', tag, '--query', 'digest'); print(tag, d); return d
if what == 'door':
    C = H / 'ctx-door'; shutil.rmtree(C, ignore_errors=True); C.mkdir(); files = ['server.py', 'ledger.py', 'x402.py', 'iw.py', 'pages.py', 'jwks.json']
    for f in files + ['x402-old-keys.json']: shutil.copy2(H / 'patched' / 'door' / f, C / f)
    L = ['FROM allooloocmkg.azurecr.io/iw-door@sha256:9f305377a993d7b37e638ab8289f269660f6933de44a72218d6483e5f8531c5d',
         'RUN ' + ' && '.join(f'echo "{md5(H / "extracted" / "door" / "app" / f)}  /app/{f}" | md5sum -c -' for f in files) + ' && test ! -e /app/x402-old-keys.json',
         'COPY ' + ' '.join(files + ['x402-old-keys.json']) + ' /app/', 'RUN python -m py_compile /app/server.py /app/ledger.py /app/x402.py /app/iw.py /app/pages.py && python -c "import json; json.load(open(\'/app/jwks.json\')); json.load(open(\'/app/x402-old-keys.json\'))"']
    (C / 'Dockerfile').write_text('\n'.join(L) + '\n', encoding='utf-8', newline='\n'); d = build(C, 'iw-door:iwmove01'); json.dump({'image': f'allooloocmkg.azurecr.io/iw-door@{d}'}, open(H / 'door-image.json', 'w'))
if what == 'fleet':
    base = json.load(open(H.parent / 'USR-01' / 'reslate-image.json'))['image']; C = H / 'ctx-fleet'; shutil.rmtree(C, ignore_errors=True); C.mkdir()
    for v in ('ops-iw01', 'ops-nightly02', 'ops-fix'):
        (C / 'iw' / v[4:] / 'ops').mkdir(parents=True)
        for f in ('amnlib.py', 'ledger.py', 'job_amn.py', 'ark_amn.py', 'verify_amn.py'): shutil.copy2(H / 'patched' / v / f, C / 'iw' / v[4:] / 'ops' / f)
    shutil.copy2(r'C:\ALLOOLOO\CM-KG\RAILS\research\coverage.py', C / 'coverage.py')
    L = [f'FROM {base}', 'RUN test ! -e /job/iw && pip install --no-cache-dir "psycopg[binary]==3.2.10"', 'COPY iw/ /job/iw/', 'COPY coverage.py /job/ALLOOLOO/CM-KG/RAILS/research/coverage.py',
         'RUN python3 -m py_compile /job/iw/iw01/ops/job_amn.py /job/iw/nightly02/ops/job_amn.py /job/iw/fix/ops/job_amn.py /job/ALLOOLOO/CM-KG/RAILS/research/coverage.py && python3 -c "import psycopg, cryptography, boto3, azure.storage.blob"']
    (C / 'Dockerfile').write_text('\n'.join(L) + '\n', encoding='utf-8', newline='\n'); tag = 'cmkg-sweep:iwmove01-' + base.split('sha256:')[1][:12]; d = build(C, tag); json.dump({'image': f'allooloocmkg.azurecr.io/cmkg-sweep@{d}', 'tag': tag, 'base': base}, open(H / 'fleet-image.json', 'w'))
