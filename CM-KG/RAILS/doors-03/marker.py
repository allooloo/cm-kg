r"""DOORS-03 — the newest sweep marker of a node (sweeps/<night>/<cc>/done.json or failed.json in its store), the fields that say green.
Usage: python -X utf8 -I marker.py <cc>"""
import sys, json, os, subprocess
from azure.storage.blob import BlobServiceClient
cc = sys.argv[1]; node = f'{cc}-cm-kg'; os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'
st = [x for x in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8')) if x['node'] == node][0]['region']['store']; sa = f'allooloocmkg{cc}pond'
key = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{st}', '-n', sa, '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=True).stdout.strip()
c = BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client('pond')
bl = sorted((b for b in c.list_blobs(name_starts_with='sweeps/') if b.name.endswith(f'/{cc}/done.json') or b.name.endswith(f'/{cc}/failed.json')), key=lambda b: b.last_modified)
b = bl[-1]; m = json.loads(c.download_blob(b.name).readall())
print(b.name, b.last_modified.isoformat())
print({k: m.get(k) for k in ('image', 'execution', 'market_date', 'records', 'events', 'records_delta', 'events_delta', 'held', 'gate', 'fold', 'enrich', 'error') if k in m})
tail = m.get('tail') or m.get('log_tail') or ''
print([l for l in str(tail).splitlines() if 'fold' in l or 'gate' in l][-6:])
