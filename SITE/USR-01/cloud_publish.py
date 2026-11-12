r"""cloud_publish.py — RESLATE-01: the page-store publish run FROM THE JOB (cmkg-apex-rail, its image, its identity, its vault reference to the page-store
token), not from this machine. This machine only starts the execution and reads its log.
  seed     once: the publish ledgers and manifests this machine holds (CM-KG\RESEARCH\published, pages\<cc>.manifest.json) go to the apex store
           (ops/research/published, ops/research/manifests) where the job reads them, so the job's first publish writes on change and keeps every market
           in the page store's index. A ledger already in the store is not overwritten.
  run <night> <cc…>   one execution of cmkg-apex-rail whose command is publish_stores.py for those markets; waits and prints the log's last lines.
Usage: python -X utf8 -I cloud_publish.py seed | run <night> <cc…>"""
import json, os, subprocess, sys, time, pathlib
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
JOB, RG, SUB = 'cmkg-apex-rail', 'allooloo-cmkg-eastus', '038b49c0-5a0c-46f7-bd34-41ee6d087b41'; R = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RESEARCH')
def az(*a, js=True):
    r = subprocess.run([*AZ, *a, '-o', 'json' if js else 'tsv'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: sys.exit(f'STOP az {" ".join(a[:4])}: {r.stderr[-500:]}')
    return (json.loads(r.stdout) if r.stdout.strip() else None) if js else r.stdout.strip()
if sys.argv[1] == 'seed':
    from azure.storage.blob import BlobServiceClient
    k = az('storage', 'account', 'keys', 'list', '-g', 'allooloo-cmkg-shared', '-n', 'allooloocmkgapex', '--query', '[0].value', js=False)
    ops = BlobServiceClient('https://allooloocmkgapex.blob.core.windows.net', credential=k).get_container_client('ops'); have = {b.name for b in ops.list_blobs(name_starts_with='research/')}; n = kept = 0
    for f in sorted((R / 'published').glob('*.json')):
        cc = f.stem; m = R / 'pages' / f'{cc}.manifest.json'
        for name, p in ((f'research/published/{cc}.json', f), (f'research/manifests/{cc}.json', m)):
            if name in have: kept += 1; continue
            if p.exists(): ops.upload_blob(name, p.read_bytes(), overwrite=False); n += 1
            else: print('missing on this machine', p)
    print('seeded', n, 'kept', kept)
if sys.argv[1] == 'run':
    night, ccs = sys.argv[2], sys.argv[3:]; img = az('containerapp', 'job', 'show', '-n', JOB, '-g', RG, '--query', 'properties.template.containers[0].image', js=False)
    sh = f'cd /job/ALLOOLOO/CM-KG/RAILS/research && export AZURE_CONFIG_DIR=/tmp/.azure && az login --identity -o none && az account set -s {SUB} && /usr/local/bin/python3 -X utf8 publish_stores.py {night} {" ".join(ccs)}'
    y = pathlib.Path(__file__).parent / 'cloud-publish.yaml'   # a YAML template: the CLI reads '-c' on the command line as its own flag
    y.write_text(json.dumps({'containers': [{'name': JOB, 'image': img, 'command': ['/bin/sh'], 'args': ['-c', sh], 'resources': {'cpu': 1.0, 'memory': '2Gi'},
        'env': [{'name': 'CLOUDFLARE_KV_TOKEN', 'secretRef': 'cloudflare-kv-token'}, {'name': 'APEX_STORAGE_ACCOUNT', 'value': 'allooloocmkgapex'}, {'name': 'OPS_CONTAINER', 'value': 'ops'}]}]}, indent=1), encoding='utf-8')
    x = az('containerapp', 'job', 'start', '-n', JOB, '-g', RG, '--yaml', str(y)); ex = x.get('name') or x['id'].split('/')[-1]; print('execution', ex, flush=True)
    while True:
        time.sleep(45); st = az('containerapp', 'job', 'execution', 'show', '-n', JOB, '-g', RG, '--job-execution-name', ex, '--query', 'properties.status', js=False)
        if st not in ('Running', 'Processing', 'Unknown', ''): break
    print('status', st); time.sleep(20)
    r = subprocess.run([*AZ, 'containerapp', 'job', 'logs', 'show', '-n', JOB, '-g', RG, '--execution', ex, '--container', JOB, '--tail', '60'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    for l in r.stdout.splitlines()[-40:]:
        try: print(json.loads(l).get('Log', '')[:260])
        except Exception: print(l[:260])
