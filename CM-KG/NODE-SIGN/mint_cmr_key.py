r"""mint_cmr_key.py — NODE-SIGN-01 (DAY ORDER 4, 2026-10-24): the node-record signing key, Ed25519, kid allooloo-cmr-2026-10.
Private OKP JWK -> C:\ALLOOLOO\AGENT KEYS\cmr-signing-jwk.txt (never printed); public JWK beside as cmr-signing.pub.jwk.json. Refuses to overwrite."""
import os, json, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
P = r"C:\ALLOOLOO\AGENT KEYS\cmr-signing-jwk.txt"; KID = "allooloo-cmr-2026-10"
if os.path.exists(P): raise SystemExit("exists, not overwritten")
b = lambda x: base64.urlsafe_b64encode(x).decode().rstrip("=")
k = Ed25519PrivateKey.generate(); d = k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()); x = k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
pub = {"kty": "OKP", "crv": "Ed25519", "x": b(x), "kid": KID, "alg": "EdDSA", "use": "sig"}
open(P, "w", newline="\n").write(json.dumps({**pub, "d": b(d)}) + "\n"); open("cmr-signing.pub.jwk.json", "w", newline="\n").write(json.dumps(pub) + "\n"); print("minted", KID)
