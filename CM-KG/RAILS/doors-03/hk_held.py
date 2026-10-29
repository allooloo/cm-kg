r"""IW-01 — read only: hk's held index (door-held/<date>/) against the index on the wire (door/), names and sizes; the flag line."""
import sys, json, os, subprocess
from azure.storage.blob import BlobServiceClient
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'
key = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-g', 'allooloo-cmkg-eastasia', '-n', 'allooloocmkghkpond', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=True).stdout.strip()
c = BlobServiceClient('https://allooloocmkghkpond.blob.core.windows.net', credential=key).get_container_client('pond')
for pre in ('door-held/', 'door/'):
    bl = list(c.list_blobs(name_starts_with=pre)); print(pre, len(bl))
    for b in sorted(bl, key=lambda b: b.name)[:40]: print('  ', b.name, b.size, b.last_modified.isoformat()[:19])
for b in c.list_blobs(name_starts_with='sweeps/2026-10-27/hk/'): print(b.name, b.size)
for b in c.list_blobs(name_starts_with='flags/'): print(b.name, b.size, b.last_modified.isoformat()[:19])
