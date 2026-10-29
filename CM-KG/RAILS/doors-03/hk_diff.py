r"""IW-01 — read only: per-record event counts, hk held index (door-held/2026-10-26/index.json) vs the wire (door/index.json); held.txt; the job log lines that matter."""
import json, os, subprocess, collections
from azure.storage.blob import BlobServiceClient
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'
key = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-g', 'allooloo-cmkg-eastasia', '-n', 'allooloocmkghkpond', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=True).stdout.strip()
c = BlobServiceClient('https://allooloocmkghkpond.blob.core.windows.net', credential=key).get_container_client('pond')
g = lambda n: json.loads(c.download_blob(n).readall())
print(c.download_blob('sweeps/2026-10-27/hk/held.txt').readall().decode())
log = c.download_blob('sweeps/2026-10-27/hk/job-cmkg-hk-rail-29883960.log').readall().decode('utf-8', 'replace')
print('\n'.join(l for l in log.splitlines() if any(w in l.lower() for w in ('window', 'events', 'gate', 'fold', 'dedup', 'drop', 'held', 'enrich')))[:3000])
new, old = g('door-held/2026-10-26/index.json'), g('door/index.json')
json.dump({'new': new, 'old': old}, open(os.path.join(os.environ.get('TEMP', '.'), 'hk_idx.json'), 'w'))
def recs(ix):
    r = ix.get('records') or ix.get('issuers') or ix
    if isinstance(r, dict): r = [dict(v, _k=k) if isinstance(v, dict) else {'_k': k, 'v': v} for k, v in r.items()]
    return r
o, n = recs(old), recs(new)
print('top keys old', list(old)[:10] if isinstance(old, dict) else type(old), 'new', list(new)[:10] if isinstance(new, dict) else type(new))
print('records', len(o), len(n)); print('sample', json.dumps(o[0])[:600])
