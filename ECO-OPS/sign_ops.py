"""sign_ops.py — ECO-OPS-01: sign the 148 SM-ECO-10060 agent cards from inside the nightly job. Same discipline as site03a_sign.py (ES256 JWS over the canonical
card without `signatures`, Key Vault kv-gsc-signing-fr key gsc-cards-2026, kid gsc-cards-2026-08, every signature verified against the live keyring at dpuone.ai
before it is written; the private key never leaves the vault), but the vault token comes from a service principal of the GSC tenant whose credentials the job
reads by reference (GSC_SIGN_TENANT / GSC_SIGN_CLIENT / GSC_SIGN_SECRET). Without them the job raises SigningNotPlaced and the roll is held.
Usage: python -X utf8 sign_ops.py <snapshots dir> <registry estate.json> <out signed-cards.json>"""
import os, sys, json, base64, hashlib, pathlib, urllib.request, time
import httpx
from cryptography.hazmat.primitives.asymmetric import ec; from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature; from cryptography.hazmat.primitives import hashes
class SigningNotPlaced(Exception): pass
SNAP = pathlib.Path(sys.argv[1]); REG = json.load(open(sys.argv[2], encoding="utf-8")); OUT = sys.argv[3]; KID = "gsc-cards-2026-08"
CCS = [m["cc"].lower() for arr in REG["jurisdictional_nodes"]["regions"].values() for m in arr]
HOSTS = ["sm-eco-10060.org"] + [f"{cc}-eco-10060.{t}" for cc in CCS for t in ("org", "com", "ai")]; assert len(HOSTS) == 148
t_id, c_id, c_sec = os.environ.get("GSC_SIGN_TENANT"), os.environ.get("GSC_SIGN_CLIENT"), os.environ.get("GSC_SIGN_SECRET")
if not (t_id and c_id and c_sec): raise SigningNotPlaced("GSC_SIGN_TENANT / GSC_SIGN_CLIENT / GSC_SIGN_SECRET not placed (allooloo-cmkg-kv-apex: gsc-sign-tenant, gsc-sign-client, gsc-sign-secret)")
from azure.identity import ClientSecretCredential
tok = ClientSecretCredential(t_id, c_id, c_sec).get_token("https://vault.azure.net/.default").token
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("="); unb = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
jw = json.loads(urllib.request.urlopen(urllib.request.Request("https://dpuone.ai/.well-known/jwks.json", headers={"User-Agent": "curl/8"}), timeout=30).read()); k = next(x for x in jw["keys"] if x["kid"] == KID)
pub = ec.EllipticCurvePublicNumbers(int.from_bytes(unb(k["x"]), "big"), int.from_bytes(unb(k["y"]), "big"), ec.SECP256R1()).public_key()
PH = b64u(json.dumps({"alg": "ES256", "kid": KID}, separators=(",", ":")).encode())
client = httpx.Client(timeout=60, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"}); URL = "https://kv-gsc-signing-fr.vault.azure.net/keys/gsc-cards-2026/sign?api-version=7.4"
done = []
for h in HOSTS:
    card = SNAP / h / ".well-known" / "agent-card.json"; rec = json.loads(card.read_text(encoding="utf-8")); rec.pop("signatures", None)
    payload = b64u(json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")); digest = hashlib.sha256((PH + "." + payload).encode("ascii")).digest()
    for attempt in range(4):
        r = client.post(URL, json={"alg": "ES256", "value": b64u(digest)})
        if r.status_code == 200: break
        time.sleep(2 * (attempt + 1))
    assert r.status_code == 200, (h, r.status_code, r.text[:200]); raw = unb(r.json()["value"]); assert len(raw) == 64
    pub.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")), (PH + "." + payload).encode("ascii"), ec.ECDSA(hashes.SHA256()))
    rec["signatures"] = [{"protected": PH, "signature": b64u(raw)}]; card.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"); done.append(h)
    mp = SNAP / (h + ".manifest.json"); man = json.loads(mp.read_text(encoding="utf-8")); body = card.read_bytes()
    v = man["paths"]["/.well-known/agent-card.json"]; v["sha256"] = hashlib.sha256(body).hexdigest(); v["bytes"] = len(body); mp.write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
json.dump({"kid": KID, "signed": done, "count": len(done)}, open(OUT, "w", encoding="utf-8"), indent=1); print("signed + verified:", len(done))
