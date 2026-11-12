r"""iw_keys.py — IW-MOVE-01 steps 4 and 5: the Allooloo side's secrets, in its own vault (allooloo-iw-kv-frc). No secret value is printed, logged or written
to disk here; only public key material is printed.
  mint     two NEW Ed25519 signing keys are made in this process and written straight into the new vault: iw-sign-key (rows, ledger, statements, door)
           and iw-x402-key (x402 settlement receipts). Only their public x values are printed, for the keyring. A key already in the vault is kept.
  carry    the secrets that are not Issuerwire's to re-create — the payment facilitator's credentials and the two receiving addresses, the second-cloud
           (ark) access pair, the Companies House key — pass from the old vault to the new one inside this process, vault to vault, never in the clear.
           The old signing keys and the old database password do NOT move.
  storage  the new storage account's key into the new vault (storage-key), for the door and the jobs.
Usage: python -X utf8 -I iw_keys.py mint|carry|storage"""
import base64, json, os, subprocess, sys
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
OLD = dict(os.environ, AZURE_CONFIG_DIR=r'C:\A2AAMN\.azure'); NEW = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); KV = 'allooloo-iw-kv-frc'
def show(env, kv, name, extra=()):
    r = subprocess.run([*AZ, 'keyvault', 'secret', 'show', '--vault-name', kv, '-n', name, *extra, '--query', 'value', '-o', 'tsv'], capture_output=True, text=True, env=env); return r.stdout.rstrip('\n') if r.returncode == 0 and r.stdout.strip() else None
def put(name, value):
    r = subprocess.run([*AZ, 'keyvault', 'secret', 'set', '--vault-name', KV, '-n', name, '--value', value, '--query', 'name', '-o', 'tsv'], capture_output=True, text=True, env=NEW)
    if r.returncode: sys.exit(f'STOP: {name} not written to the new vault')
b64u = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=').decode()
if sys.argv[1] == 'mint':
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    out = {}
    for name in ('iw-sign-key', 'iw-x402-key'):
        pem = show(NEW, KV, name)
        if pem: k = serialization.load_pem_private_key(pem.replace('\\n', '\n').encode(), password=None); state = 'already in the vault (kept)'
        else:
            k = Ed25519PrivateKey.generate(); pem = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode().strip().replace('\n', '\\n'); put(name, pem); state = 'minted'
        out[name] = b64u(k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)); del pem, k; print(name, state, 'public x', out[name])
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new-public-keys.json'), 'w'), indent=1)
elif sys.argv[1] == 'carry':
    for name in ('x402-facilitator-auth', 'x402-facilitator-key-id', 'x402-pay-to', 'x402-pay-to-ousd', 'ark-aws-key-id', 'ark-aws-secret', 'companieshouse-key'):
        v = show(OLD, 'kv-amn-frc', name, ('--subscription', '9e406344-81a4-4624-98de-a9c642a75d69'))
        if v is None: print(name, 'not read from the old vault — not carried'); continue
        put(name, v); del v; print(name, 'carried vault to vault')
elif sys.argv[1] == 'storage':
    r = subprocess.run([*AZ, 'storage', 'account', 'keys', 'list', '-n', 'allooloostgiwfrc', '-g', 'allooloo-iw-francecentral', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, env=NEW); put('storage-key', r.stdout.strip()); print('storage-key placed')
