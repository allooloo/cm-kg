r"""verify_receipt.py — RCO-A-01 proof, read from the wire only: get_receipt(decision_id) on mcp.rco-a2a.ai; the issuing door's EdDSA signature verified against
the keyring the receipt names (fetched live); the receipt's hash recomputed (RFC 8785 canonical JSON of the receipt without ledger, receipt_url, page and
signature_check) and compared with ledger.hash; the ledger transaction id read. Writes proof-<decision_id>.json beside. Usage: python -X utf8 -I verify_receipt.py <decision_id>"""
import sys, os, json, base64, hashlib, urllib.request
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
D = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
unb = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)); b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
def post(u, b):
    raw = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(b).encode(), headers={"content-type": "application/json", "accept": "application/json, text/event-stream", "user-agent": "curl/8 RCO-A-01 verify"}), timeout=60).read().decode()
    return json.loads(raw[raw.index("{"):])
r = post("https://mcp.rco-a2a.ai/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_receipt", "arguments": {"decision_id": D}}})["result"]
rec = r.get("structuredContent") or json.loads(r["content"][0]["text"])
sig = rec["signature"]; ph, _, s = sig["jws"].split("."); hdr = json.loads(unb(ph))
ring = json.loads(urllib.request.urlopen(urllib.request.Request(sig["keyring"], headers={"user-agent": "curl/8"}), timeout=30).read()); k = next(x for x in ring["keys"] if x["kid"] == hdr["kid"])
signed = {kk: v for kk, v in rec.items() if kk not in ("signature", "signature_check", "ledger", "receipt_url", "page", "writer")}   # writer is the door's label, added after the signature
payload = b64u(json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
try: Ed25519PublicKey.from_public_bytes(unb(k["x"])).verify(unb(s), (ph + "." + payload).encode("ascii")); sig_ok = True
except Exception: sig_ok = False
kept = {kk: v for kk, v in rec.items() if kk not in ("ledger", "receipt_url", "page", "signature_check")}
h = "sha256:" + hashlib.sha256(json.dumps(kept, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
out = {"decision_id": D, "issuing_door": rec.get("issuing_door"), "object": rec.get("object"), "signal": rec.get("signal"), "rule": rec.get("rule"), "records_read": rec.get("records_read"),
       "signature": {"kid": hdr["kid"], "alg": hdr["alg"], "keyring": sig["keyring"], "verified_here": sig_ok, "door_check": rec.get("signature_check")},
       "hash": {"recomputed": h, "ledger_hash": rec["ledger"].get("hash"), "match": h == rec["ledger"].get("hash")},
       "ledger": rec["ledger"], "page": rec.get("page")}
json.dump(out, open(os.path.join(HERE, "proof-%s.json" % D), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({k2: out[k2] for k2 in ("decision_id", "issuing_door", "signal")}), "| signature verified:", sig_ok, "| hash match:", out["hash"]["match"], "| ledger:", rec["ledger"].get("transaction_id") or rec["ledger"].get("status"))
