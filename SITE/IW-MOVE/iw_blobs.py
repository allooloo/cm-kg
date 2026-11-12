r"""iw_blobs.py — IW-MOVE-01 step 2: Issuerwire's blobs, storage to storage (stgamnfrc in the other directory -> allooloostgiwfrc in the Allooloo
subscription), on a one-time token made from the sign-in already granted: a read+list SAS on the source, valid six hours, made in-process from the source
key (read through the sign-in), never printed and never written to disk. Server-side copy (the bytes never pass through this machine). Then the count and
the byte total of every container on both sides; a difference is printed and exits 1. A re-run copies only what is missing or changed (the final sync).
Usage: python -X utf8 -I iw_blobs.py copy|count"""
import json, os, subprocess, sys, time, datetime
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
OLD = dict(os.environ, AZURE_CONFIG_DIR=r'C:\A2AAMN\.azure'); NEW = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure')
SSUB = '9e406344-81a4-4624-98de-a9c642a75d69'; SSA, SRG = 'stgamnfrc', 'rg-amn-frc'; DSA, DRG = 'allooloostgiwfrc', 'allooloo-iw-francecentral'
CONT = ['audit-log', 'ledger', 'pond', 'record', 'staging', 'statements', 'x402-receipts']; mode = sys.argv[1]
def az(env, *a):
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
    if r.returncode: print('STOP: az', ' '.join(a[:4])); sys.exit(1)
    return json.loads(r.stdout) if r.stdout.strip() else None
skey = az(OLD, 'storage', 'account', 'keys', 'list', '-n', SSA, '-g', SRG, '--subscription', SSUB)[0]['value']; dkey = az(NEW, 'storage', 'account', 'keys', 'list', '-n', DSA, '-g', DRG)[0]['value']
from azure.storage.blob import BlobServiceClient, generate_account_sas, ResourceTypes, AccountSasPermissions
src = BlobServiceClient(f'https://{SSA}.blob.core.windows.net', credential=skey); dst = BlobServiceClient(f'https://{DSA}.blob.core.windows.net', credential=dkey)
def listing(svc, c): return {b.name: (b.size, b.etag, (b.content_settings.content_md5.hex() if b.content_settings and b.content_settings.content_md5 else None)) for b in svc.get_container_client(c).list_blobs()}
if mode == 'copy':
    sas = generate_account_sas(SSA, account_key=skey, resource_types=ResourceTypes(container=True, object=True), permission=AccountSasPermissions(read=True, list=True), expiry=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=6))
    started = 0
    for c in CONT:
        S = listing(src, c); D = listing(dst, c); cc = dst.get_container_client(c); todo = [n for n, v in S.items() if n not in D or D[n][0] != v[0] or (v[2] and D[n][2] != v[2])]
        for n in todo:
            cc.get_blob_client(n).start_copy_from_url(f'https://{SSA}.blob.core.windows.net/{c}/' + __import__('urllib.parse').parse.quote(n) + '?' + sas); started += 1
        print(c, 'source', len(S), 'to copy', len(todo), flush=True)
    del sas
    for i in range(120):   # server-side copies of small blobs finish in seconds; wait for the last pending one
        pend = sum(1 for c in CONT for b in dst.get_container_client(c).list_blobs(include=['copy']) if b.copy and b.copy.status == 'pending')
        if not pend: break
        time.sleep(10)
    print('copies started', started, 'pending now', pend, flush=True)
out = {'at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'containers': {}}; bad = 0
for c in CONT:
    S = listing(src, c); D = listing(dst, c); sb = sum(v[0] for v in S.values()); db = sum(v[0] for v in D.values()); miss = [n for n in S if n not in D]; diff = [n for n in S if n in D and D[n][0] != S[n][0]]; extra = [n for n in D if n not in S]
    out['containers'][c] = {'old': {'blobs': len(S), 'bytes': sb}, 'new': {'blobs': len(D), 'bytes': db}, 'missing_on_new': len(miss), 'size_differs': len(diff), 'only_on_new': len(extra), 'match': len(S) == len(D) and sb == db and not miss and not diff}
    bad += 0 if out['containers'][c]['match'] else 1; print(c, json.dumps(out['containers'][c]), flush=True)
out['old_total'] = {'blobs': sum(v['old']['blobs'] for v in out['containers'].values()), 'bytes': sum(v['old']['bytes'] for v in out['containers'].values())}; out['new_total'] = {'blobs': sum(v['new']['blobs'] for v in out['containers'].values()), 'bytes': sum(v['new']['bytes'] for v in out['containers'].values())}; out['MATCH'] = bad == 0
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"blobs-{mode}-{out['at'].replace(':', '')}.json"), 'w'), indent=1); print('TOTAL old', out['old_total'], 'new', out['new_total'], 'MATCH' if bad == 0 else 'DIFFERENT'); sys.exit(1 if bad else 0)
