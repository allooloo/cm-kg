r"""iw_verify_old.py — IW-MOVE-01 step 5 test: what was signed before the move still verifies against the NEW keyring.
Reads from the Allooloo-side copy (allooloostgiwfrc): every x402 settlement receipt (x402-receipts/) and the ledger events of the newest days (ledger/).
Each is verified with Ed25519 against the public key the NEW keyring publishes for the kid the object names:
  receipts  -> the list the new door serves at /x402/jwks.json = the runtime key + x402-old-keys.json (here: the old entries of that file)
  events    -> patched\door\jwks.json (/.well-known/jwks.json)
A tampered copy of the first receipt must FAIL. Writes verify-old.json. Usage: python -X utf8 -I iw_verify_old.py"""
import base64, json, os, pathlib, subprocess, sys
from azure.storage.blob import BlobServiceClient
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
H = pathlib.Path(__file__).parent; ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
k = subprocess.run([*AZ, 'storage', 'account', 'keys', 'list', '-n', 'allooloostgiwfrc', '-g', 'allooloo-iw-francecentral', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, env=ENV).stdout.strip()
svc = BlobServiceClient('https://allooloostgiwfrc.blob.core.windows.net', credential=k); ub = lambda s: base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))
ring = {x['kid']: x for x in json.load(open(H / 'patched' / 'door' / 'jwks.json', encoding='utf-8'))['keys']}; xold = {x['kid']: x for x in json.load(open(H / 'patched' / 'door' / 'x402-old-keys.json', encoding='utf-8'))['keys']}
def ok(pub_x, msg, sig):
    try: Ed25519PublicKey.from_public_bytes(ub(pub_x)).verify(ub(sig), msg); return True
    except Exception: return False
def sd(v): return [sd(i) for i in v] if isinstance(v, list) else ({q: sd(v[q]) for q in sorted(v)} if isinstance(v, dict) else v)
out = {'receipts': {'read': 0, 'verified': 0, 'kids': {}, 'issuers': {}, 'failed': []}, 'events': {'read': 0, 'verified': 0, 'kids': {}, 'days': [], 'failed': []}}
c = svc.get_container_client('x402-receipts'); first = None
for b in c.list_blobs():
    if not b.name.endswith('.json'): continue
    r = json.loads(c.download_blob(b.name).readall()); R = out['receipts']; R['read'] += 1
    sig = r.get('signature') or r.get('sig') or {}; body = {q: v for q, v in r.items() if q not in ('signature', 'sig')}; kid = sig.get('kid'); R['kids'][kid] = R['kids'].get(kid, 0) + 1; R['issuers'][str(body.get('issuer'))] = R['issuers'].get(str(body.get('issuer')), 0) + 1
    key = xold.get(kid) or ring.get(kid); canon = json.dumps(sd(body), separators=(',', ':'), ensure_ascii=False).encode('utf-8'); good = bool(key) and ok(key['x'], canon, sig.get('value', ''))
    if good:
        R['verified'] += 1
        if first is None: first = (b.name, key['x'], body, sig)
    else: R['failed'].append(b.name)
if first:
    t = dict(first[2]); t['issuer'] = 'tampered'; out['receipts']['tamper_test'] = {'receipt': first[0], 'tampered_copy_verifies': ok(first[1], json.dumps(sd(t), separators=(',', ':'), ensure_ascii=False).encode('utf-8'), first[3].get('value', ''))}
    out['receipts']['sample'] = {'receipt': first[0], 'kid': first[3].get('kid'), 'issuer': first[2].get('issuer'), 'fields': sorted(first[2])}
L = svc.get_container_client('ledger'); days = sorted(b.name for b in L.list_blobs() if b.name.endswith('.jsonl'))
for d in days[-5:]:
    out['events']['days'].append(d)
    for line in L.download_blob(d).readall().decode('utf-8').splitlines():
        if not line.strip(): continue
        e = json.loads(line); E = out['events']; E['read'] += 1; kid = (e.get('sig') or {}).get('kid'); E['kids'][kid] = E['kids'].get(kid, 0) + 1
        sig = (e.get('sig') or {}).get('sig'); canon = json.dumps({q: v for q, v in e.items() if q != 'sig'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str).encode('utf-8')
        if kid in ring and sig and ok(ring[kid]['x'], canon, sig): E['verified'] += 1
        elif len(E['failed']) < 5: E['failed'].append({'day': d, 'keys': sorted(e)[:14], 'kid': kid})
out['receipts']['failed'] = out['receipts']['failed'][:5]; out['keyring_kids'] = list(ring); out['x402_old_kids'] = list(xold)
json.dump(out, open(H / 'verify-old.json', 'w'), indent=1); print(json.dumps(out, indent=1)[:2600])
