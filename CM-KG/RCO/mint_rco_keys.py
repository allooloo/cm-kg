r"""mint_rco_keys.py — RCO-A-01 (DAY ORDER 3, 2026-10-24). Two keys, written to files by name, values never printed:
  1. the Allooloo receipt-signing key: Ed25519, kid allooloo-rco-2026-10 -> C:\ALLOOLOO\AGENT KEYS\rco-signing-jwk.txt (private OKP JWK); the public JWK is
     written beside the rail (rco-signing.pub.jwk.json) for the keyring at https://mcp.getissuer.ai/.well-known/jwks.json;
  2. the write key the office issues to Allooloo for write_receipt -> C:\ALLOOLOO\AGENT KEYS\rco-write-key.txt; the door holds only its sha256
     (written to door-keys.json beside the rail: no secret in the door's configuration).
Refuses to overwrite either key file (Rule One). Usage: python -X utf8 -I mint_rco_keys.py"""
import os, json, base64, hashlib, secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
K = r"C:\ALLOOLOO\AGENT KEYS"; HERE = os.path.dirname(os.path.abspath(__file__)); KID = "allooloo-rco-2026-10"
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
sk_path, wk_path = os.path.join(K, "rco-signing-jwk.txt"), os.path.join(K, "rco-write-key.txt")
for p in (sk_path, wk_path):
    if os.path.exists(p): raise SystemExit("exists, not overwritten: " + p)
sk = Ed25519PrivateKey.generate()
d = sk.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
x = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
pub = {"kty": "OKP", "crv": "Ed25519", "x": b64u(x), "kid": KID, "alg": "EdDSA", "use": "sig"}
open(sk_path, "w", encoding="utf-8", newline="\n").write(json.dumps({**pub, "d": b64u(d)}) + "\n")
open(os.path.join(HERE, "rco-signing.pub.jwk.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(pub, indent=1) + "\n")
wk = "rcow_" + b64u(secrets.token_bytes(32))
open(wk_path, "w", encoding="utf-8", newline="\n").write(wk + "\n")
h = hashlib.sha256(wk.encode()).hexdigest()
door = {h: {"door": "allooloo", "holder": "Allooloo Technologies Corp.", "issued_by": "Agentic KG Holdings (the office)", "issued": "2026-10-24",
            "keyring": "https://mcp.getissuer.ai/.well-known/jwks.json", "kids": [KID],
            "door_hosts": ["mcp.getissuer.ai", "mcp.capitalmarketsknowledgegraph.ai", "*-cm-kg.ai", "*-eco.ai", "acm-*.ai"]}}
open(os.path.join(HERE, "door-keys.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(door) + "\n")
print("minted", KID, "and the write key; files written by name; write-key sha256 prefix", h[:12])
