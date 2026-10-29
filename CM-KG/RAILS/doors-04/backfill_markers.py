r"""LIST-02 step 4 — read only: the first-run markers of the backfill jobs (night 2026-10-26, 14:30 UTC) in every roster store: sweeps-backfill/<night>/<cc>/
done.json or failed.json, plus the year drop it names (backfill/<year>/ manifest and its signature) and the ark line in the job's tail. No fix, report only.
Usage: python -X utf8 -I backfill_markers.py [--peek cc]"""
import json, os, sys, re, subprocess, concurrent.futures as cf
from azure.storage.blob import BlobServiceClient
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'
nodes = json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))
def cont(n):
    cc = n['node'].split('-')[0]; st = n['region']['store']; sa = f'allooloocmkg{cc}pond'
    key = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{st}', '-n', sa, '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=True).stdout.strip()
    return cc, BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client('pond')
if '--peek' in sys.argv:
    cc = sys.argv[sys.argv.index('--peek') + 1]; _, c = cont([n for n in nodes if n['node'].startswith(cc + '-')][0])
    for b in c.list_blobs(name_starts_with='sweeps-backfill/'): print(b.name, b.size, b.last_modified)
    for b in c.list_blobs(name_starts_with='backfill/'):
        if b.name.count('/') <= 3: print(b.name, b.size, b.last_modified)
    sys.exit()
def one(n):
    cc, c = cont(n); out = {'node': n['node'], 'market': n['country']}
    ms = sorted([b for b in c.list_blobs(name_starts_with='sweeps-backfill/') if b.name.endswith(('/done.json', '/failed.json'))], key=lambda b: b.last_modified)
    if not ms: out['marker'] = None; return out
    b = ms[-1]; m = json.loads(c.download_blob(b.name).readall()); out.update({'marker': b.name, 'at': b.last_modified.isoformat(), 'exit': m.get('exit'), 'image': m.get('image'), 'execution': m.get('execution')})
    t = m.get('tail') or ''
    out['year'] = (re.findall(r'\byear[ =:]+(\d{4})', t) or [None])[-1]
    out['rows'] = (re.findall(r'(\d[\d,]*) rows', t) or [None])[-1]; out['events'] = (re.findall(r'(\d[\d,]*) events', t) or [None])[-1]
    out['signed'] = bool(re.search(r'signed|signature|kid allooloo-cmr', t, re.I)); out['manifest'] = (re.findall(r'(backfill/\d{4}[^\s\'"]*manifest[^\s\'"]*)', t) or [None])[-1]
    out['ark'] = (re.findall(r'(s3://[^\s\'"]+)', t) or [None])[-1] or ('ark: ' + (re.findall(r'ark[^\n]{0,80}', t, re.I) or ['none named'])[-1])
    out['fail_reason'] = None if m.get('exit') == 0 else (re.findall(r'(?:Error|FAIL|refus|Traceback)[^\n]{0,200}', t) or [t[-200:]])[-1]
    out['tail_end'] = t[-400:]
    return out
with cf.ThreadPoolExecutor(8) as ex: R = list(ex.map(one, nodes))
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backfill-first-run.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for r in sorted(R, key=lambda x: x['node']): print(r['node'], r.get('marker'), r.get('exit'), r.get('year'), r.get('rows'), r.get('events'), r.get('signed'), r.get('ark'), (r.get('fail_reason') or '')[:120])
