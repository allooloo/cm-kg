r"""Backfill gate fix (2026-10-26): move backfill jobs to a cmkg-sweep tag, and prove the B-3 gate on one market (manual start, wait, read the marker).
  python -X utf8 -I gate_proof.py move <tag> [cc ...|all]     image + IMAGE_TAG on the backfill jobs, read back
  python -X utf8 -I gate_proof.py prove <cc>                  start cmkg-<cc>-backfill now, wait for the execution, print its marker tail
Anchor of each job (image before) appended to gate-proof.json."""
import json, os, sys, time, subprocess, datetime
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'gate-proof.json'); ACR = 'allooloocmkg.azurecr.io'
def az(*a):
    p = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8'); return (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr[-300:]
rep = json.load(open(OUT)) if os.path.exists(OUT) else {}
def save(): json.dump(rep, open(OUT, 'w'), indent=1)
jobs = {j['n'].split('-')[1]: j for j in az('containerapp', 'job', 'list', '--query', "[?ends_with(name,'-backfill')].{n:name,g:resourceGroup,i:properties.template.containers[0].image}")[0]}
cmd = sys.argv[1]
if cmd == 'move':
    tag = sys.argv[2]; img = f'{ACR}/cmkg-sweep:{tag}'; want = sorted(jobs) if sys.argv[3:] in ([], ['all']) else sys.argv[3:]
    for cc in want:
        j = jobs[cc]; rep.setdefault('anchors', {}).setdefault(cc, j['i'])
        if j['i'] != img:
            r, err = az('containerapp', 'job', 'update', '-n', j['n'], '-g', j['g'], '--image', img, '--set-env-vars', f'IMAGE_TAG={tag}', '--query', 'properties.template.containers[0].image')
            print(cc, r or ('UPDATE FAILED ' + err))
        else: print(cc, 'already', img)
    save()
    back = az('containerapp', 'job', 'list', '--query', "[?ends_with(name,'-backfill')].properties.template.containers[0].image")[0]
    print('read back:', {i: back.count(i) for i in set(back)})
elif cmd == 'prove':
    cc = sys.argv[2]; j = jobs[cc]
    ex, err = az('containerapp', 'job', 'start', '-n', j['n'], '-g', j['g'])
    if not ex: sys.exit('START FAILED ' + err)
    name = ex.get('name') or ex['id'].split('/')[-1]; print('started', name, j['i'])
    for _ in range(240):
        st = (az('containerapp', 'job', 'execution', 'show', '-n', j['n'], '-g', j['g'], '--job-execution-name', name, '--query', 'properties.status')[0])
        if st in ('Succeeded', 'Failed', 'Stopped', 'Degraded'): break
        time.sleep(30)
    sys.path.insert(0, HERE); import roster
    from azure.storage.blob import BlobServiceClient
    sa = f'allooloocmkg{cc}pond'; key = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', f'allooloo-cmkg-{roster.region(cc)}', '--query', '[0].value')[0]
    c = BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client('pond')
    mk = [b for b in c.list_blobs(name_starts_with='sweeps-backfill/') if b.name.endswith(('/done.json', '/failed.json'))]
    m = max(mk, key=lambda b: b.last_modified); d = json.loads(c.download_blob(m.name).readall())
    rep.setdefault('proofs', []).append({'market': cc, 'execution': name, 'status': st, 'marker': m.name, 'exit': d.get('exit'), 'image': d.get('image'), 'tail': (d.get('tail') or '')[-1500:], 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}); save()
    print(st, m.name, 'exit', d.get('exit'), d.get('image')); print((d.get('tail') or '')[-1500:])
