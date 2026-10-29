r"""build_eco.py — ECO-01 (CEO day order 2, 2026-10-23): the 49 Electronic Compliance Object pages, one per <cc>-eco.ai, served by the Worker eco-pages.
Reads the hunt of record (CM-KG\REFERENCE\ECO\hunt-<date>\<cc>.json, every field sourced or "not found" with the pages checked), the example ISIN per live
market (resolved on that market's own node, examples.json) and writes:
  data\eco-<date>.json            the 49 records as built (immutable per date; a re-run the same day is -2, -3)
  worker\data.js                  the module the Worker imports (records + digest + signature, the twelve live markets, examples, JWKS)
Each record carries sha256 over its canonical JSON (sorted keys, compact, UTF-8). It is signed Ed25519 (kid allooloo-eco-2026-10) when the key file
AGENT KEYS\eco-signing-jwk.txt exists (read in-process, never printed); without it the record says signature: null and why.
Live numbers (issuers, as_of, door) are NOT built in: the Worker reads them from the apex list_nodes at render.
Usage: python -X utf8 -I build_eco.py <hunt-date>"""
import sys, os, json, hashlib, base64, glob, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); HUNTS = [os.path.join(HERE, "..", "REFERENCE", "ECO", "hunt-" + d) for d in sys.argv[1].split(",")]   # ECO-02 (DAY ORDER 5): "2026-10-23,2026-10-24" — a later hunt overlays an earlier one per market
KEYF = r"C:\ALLOOLOO\AGENT KEYS\eco-signing-jwk.txt"; KID = "allooloo-eco-2026-10"
# ENUM-01 (DAY ORDER 6, 2026-10-25): a market is LIVE on its ECO page when the roster of record says so (list_nodes, else nodes.json) — no list of its own
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import roster   # ENUM-01 (DAY ORDER 6): the roster of record
LIVE = roster.codes()
_LIVE_TYPED_BEFORE_ENUM01 = ["ca", "uk", "us", "de", "fr", "nl", "ch", "au", "sg", "jp", "kr", "hk"]
# NODE-EU (DAY ORDER 4, 2026-10-24): a European node is LIVE on its ECO page from the day its door is live (RAILS\eu-node\live.json)
# (DAY ORDER 4 read the European half from RAILS\eu-node\live.json here; ENUM-01 reads the whole roster above)
REGION = {"Europe": "uk fr de nl ch be pt at ie cz dk se fi no gr es it pl lu je", "Americas": "us ca mx br ar cl co cr do ec gt pa pe uy ky bm", "Asia-Pacific": "au jp kr sg hk in id my ph th vn tw", "Middle East and Africa": "ae sa il tr ma za"}
REG = {c: r for r, cs in REGION.items() for c in cs.split()}
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
signer = None
KEYTXT = os.environ.get("ECO_SIGNING_JWK") or (open(KEYF, encoding="utf-8").read() if os.path.exists(KEYF) else None)   # the job reads it from its vault secret
if KEYTXT:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    jwk = json.loads(KEYTXT); d = base64.urlsafe_b64decode(jwk["d"] + "=" * (-len(jwk["d"]) % 4))
    signer = Ed25519PrivateKey.from_private_bytes(d); JWKS = {"keys": [{"kty": "OKP", "crv": "Ed25519", "kid": KID, "x": jwk["x"], "use": "sig", "alg": "EdDSA"}]}
else:
    JWKS = {"keys": [], "note": "signing key not placed yet (AGENT KEYS\\eco-signing-jwk.txt); records carry their sha256 digest"}
ex = json.load(open(os.path.join(HERE, "examples.json"), encoding="utf-8"))
recs = {}
files = {}
for H in HUNTS:
    for f in sorted(glob.glob(os.path.join(H, "*.json"))): files[os.path.basename(f)] = f
REGIME = None
for f in sorted(files.values()):
    h = json.load(open(f, encoding="utf-8")); cc = h["market"]
    if cc == "eu":   # ECO-02: the EU regime object (ESMA, MiFID II product governance, Prospectus Regulation, MAR, ESEF, the market rows) — its own record, signed the same way
        REGIME = {"schema": "allooloo-eco/1.0", "object": "Electronic Compliance Object — EU regime", "market": "eu", "country": h["country"], "host": "eu-eco.ai", "hunted": h.get("hunted"), "fields": h["fields"], "markets": h.get("markets") or [],
                  "pages_checked": h.get("pages_checked", []), "notes": h.get("notes"), "sourced": sum(1 for v in h["fields"].values() if v.get("state") == "sourced"), "not_found": sorted(k for k, v in h["fields"].items() if v.get("state") != "sourced")}
        continue
    rec = {"schema": "allooloo-eco/1.0", "object": "Electronic Compliance Object", "market": cc, "country": h["country"], "region": REG.get(cc),
           "host": cc + "-eco.ai", "hunted": h.get("hunted"), "fields": h["fields"], "pages_checked": h.get("pages_checked", []), "notes": h.get("notes"),
           "sourced": sum(1 for v in h["fields"].values() if v.get("state") == "sourced"), "not_found": sorted(k for k, v in h["fields"].items() if v.get("state") != "sourced"),
           "node": {"live": cc in LIVE, "node": cc + "-cm-kg" if cc in LIVE else None, "example": ex.get(cc)}}
    body = canon(rec); dig = hashlib.sha256(body).hexdigest()
    if signer:
        ph = b64u(canon({"alg": "EdDSA", "kid": KID})); pl = b64u(body); sig = b64u(signer.sign((ph + "." + pl).encode("ascii")))
        signature = {"alg": "EdDSA", "kid": KID, "protected": ph, "signature": sig, "jwks": "https://%s-eco.ai/.well-known/jwks.json" % cc, "over": "base64url(protected) + '.' + base64url(canonical JSON of record)"}
    else:
        signature = None
    recs[cc] = {"record": rec, "sha256": dig, "signature": signature, "signature_note": None if signer else "not signed: the signing key (kid %s) is not placed; the sha256 of the canonical record is published instead" % KID}
assert len(recs) >= 49, len(recs)   # ECO-02: 49 + lu ky bm je tw
# NODE-EU (2026-10-24): a live European node without an ECO record in the hunt set (Luxembourg) has no page to flip: named, not fatal
if set(LIVE) - set(recs): print("live node(s) with no ECO record (no page to flip):", sorted(set(LIVE) - set(recs))); LIVE = [c for c in LIVE if c in recs]
def signed(rec):
    body = canon(rec); dig = hashlib.sha256(body).hexdigest()
    if not signer: return {"record": rec, "sha256": dig, "signature": None}
    ph = b64u(canon({"alg": "EdDSA", "kid": KID})); sig = b64u(signer.sign((ph + "." + b64u(body)).encode("ascii")))
    return {"record": rec, "sha256": dig, "signature": {"alg": "EdDSA", "kid": KID, "protected": ph, "signature": sig, "jwks": "https://eu-eco.ai/.well-known/jwks.json", "over": "base64url(protected) + '.' + base64url(canonical JSON of record)"}}
REG_OUT = signed(REGIME) if REGIME else None
day = datetime.date.today().isoformat(); out = os.path.join(HERE, "data", "eco-%s.json" % day); n = 1
while os.path.exists(out): n += 1; out = os.path.join(HERE, "data", "eco-%s-%d.json" % (day, n))
built = {"built": day, "hunt": sys.argv[1], "signed": bool(signer), "kid": KID if signer else None, "markets": recs, "regime": REG_OUT}
json.dump(built, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
js = "// generated by build_eco.py — do not edit by hand; source: %s\nexport const BUILT = %s;\nexport const LIVE = %s;\nexport const JWKS = %s;\nexport const MARKETS = %s;\nexport const REGIME = %s;\n" % (
    os.path.basename(out), json.dumps({"built": day, "hunt": sys.argv[1], "file": os.path.basename(out), "signed": bool(signer)}), json.dumps(LIVE), json.dumps(JWKS), json.dumps(recs, ensure_ascii=False), json.dumps(REG_OUT, ensure_ascii=False))
open(os.path.join(HERE, "worker", "data.js"), "w", encoding="utf-8", newline="\n").write(js)
print("built", out, "markets", len(recs), "signed", bool(signer), "sourced", sum(r["record"]["sourced"] for r in recs.values()), "not found", sum(len(r["record"]["not_found"]) for r in recs.values()))
