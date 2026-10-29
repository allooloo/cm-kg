r"""ISIN disambiguation (2026-10-27) — store access for the rails beside: cont(cc) gives the node's pond container (account key via az, read in-process).
SHELF-01 (2026-10-27): on a job the node's own key comes from its environment (STORAGE_ACCOUNT / STORAGE_KEY) when the account matches; elsewhere the
signed-in az reads it (the CLI2 python on the laptop, `az` on a job)."""
import json, os, subprocess
os.environ.setdefault('AZURE_CONFIG_DIR', r'C:\ALLOOLOO\.azure' if os.name == 'nt' else '/tmp/.azure')
_ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO' if os.name == 'nt' else '/job/ALLOOLOO')
NODES = {n['node'].split('-')[0]: n for n in json.load(open(os.path.join(_ROOT, 'CM-KG', 'DOOR', 'apex', 'static', 'nodes.json'), encoding='utf-8'))}
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli'] if os.name == 'nt' else ['az']
def key(cc):
    sa = f'allooloocmkg{cc}pond'
    if os.environ.get('STORAGE_ACCOUNT') == sa and os.environ.get('STORAGE_KEY'): return os.environ['STORAGE_KEY']
    st = NODES[cc]['region']['store']
    return subprocess.run([*AZ, 'storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{st}', '-n', sa, '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True).stdout.strip()
def cont(cc):
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient(f'https://allooloocmkg{cc}pond.blob.core.windows.net', credential=key(cc)).get_container_client('pond')
def bj(c, n): return json.loads(c.download_blob(n).readall())
