r"""refresh_eco.py — the eco-refresh agent (ECO-01 RUN; weekly, Sunday 05:00 UTC, Allooloo tenant).
1. Re-read: every source page cited by a sourced field of the 49 records (latest data\eco-*.json) is fetched again; its visible text is hashed.
2. Flag: a field whose source page changed (hash differs from the last drop), stopped answering, or moved is flagged CHANGED / GONE — the field value is
   never rewritten by this agent; a flagged field goes to the hunter for a re-read (sourced or blank).
3. Re-sign: build_eco.py runs again (new dated build; signed when the key is placed) and the Worker eco-pages is redeployed with it.
4. Record: an immutable drop CM-KG\POND\eco\refresh\<date>\ (hashes.json, flags.json, DIGEST-ROW.json); never overwritten (same day -> -2, -3).
5. Digest row: agent · verdict · pages read · fields flagged · markets touched · spend — the same row shape as the ops digest.
6. Ark: the drop goes put-only to s3://allooloo-ark-eco/eco/refresh/<drop>/ (Object Lock) when ARK_ENABLED=1.
Usage: python -X utf8 -I refresh_eco.py [--no-deploy]"""
import os, sys, re, json, glob, hashlib, datetime, subprocess, urllib.request, urllib.error, html
HERE = os.path.dirname(os.path.abspath(__file__)); POND = os.path.join(HERE, "..", "POND", "eco", "refresh")
UA = "Allooloo eco-refresh (ECO-01; developers@allooloo.ai)"
# DOORS-02 (2026-10-26): the latest build by date then same-day number (eco-<date>.json is 1, -2, -3 …); a plain string sort put -9 after -24
def build_no(p): m = re.match(r"eco-(\d{4}-\d{2}-\d{2})(?:-(\d+))?\.json$", os.path.basename(p)); return (m.group(1), int(m.group(2) or 1)) if m else ("", 0)
latest = max(glob.glob(os.path.join(HERE, "data", "eco-*.json")), key=build_no); B = json.load(open(latest, encoding="utf-8"))
def text_of(body):
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", body); t = re.sub(r"(?s)<[^>]+>", " ", t); t = html.unescape(t)
    t = re.sub(r"\d{1,2}:\d{2}(:\d{2})?", " ", t)                                     # clocks on a page are not a change of rule
    return re.sub(r"\s+", " ", t).strip()
def read(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf,*/*"}), timeout=40)
        body = r.read(); ct = r.headers.get("content-type", "")
        h = hashlib.sha256(body if "pdf" in ct else text_of(body.decode("utf-8", "replace")).encode("utf-8")).hexdigest()
        return {"status": r.status, "final": r.geturl(), "sha256": h, "bytes": len(body)}
    except urllib.error.HTTPError as e: return {"status": e.code, "final": url, "sha256": None}
    except Exception as e: return {"status": 0, "final": url, "sha256": None, "error": str(e)[:120]}
urls = {}
for cc, R in B["markets"].items():
    for k, f in R["record"]["fields"].items():
        if f.get("state") != "sourced": continue
        for u in re.split(r"\s;\s|\s\|\s", str(f.get("source") or "")):
            if u.startswith("http"): urls.setdefault(u.split(" ")[0], []).append((cc, k))
BLOB = None
if os.environ.get("OPS_ACCOUNT"):                                                     # in the Azure job: the pond drop lives in the ops store (managed identity)
    from azure.identity import DefaultAzureCredential; from azure.storage.blob import ContainerClient
    BLOB = ContainerClient("https://%s.blob.core.windows.net" % os.environ["OPS_ACCOUNT"], os.environ.get("OPS_CONTAINER", "ops"), credential=DefaultAzureCredential())
    names = sorted(b.name for b in BLOB.list_blobs(name_starts_with="eco/refresh/") if b.name.endswith("/hashes.json"))
    if names:
        p = os.path.join(POND, names[-1].split("/")[2]); os.makedirs(p, exist_ok=True)
        if not os.path.exists(os.path.join(p, "hashes.json")): open(os.path.join(p, "hashes.json"), "wb").write(BLOB.download_blob(names[-1]).readall())
prev = sorted(glob.glob(os.path.join(POND, "*", "hashes.json")))
P = json.load(open(prev[-1], encoding="utf-8")) if prev else {}
now = {u: read(u) for u in sorted(urls)}
flags = []
for u, r in now.items():
    p = P.get(u)
    if r["sha256"] is None: kind = "GONE"
    elif p and p.get("sha256") and p["sha256"] != r["sha256"]: kind = "CHANGED"
    elif r["final"].rstrip("/") != u.rstrip("/") and not (p and p.get("final") == r["final"]): kind = "MOVED"
    else: continue
    for cc, k in urls[u]: flags.append({"market": cc, "field": k, "source": u, "flag": kind, "status": r["status"], "first_read": not p})
day = datetime.date.today().isoformat(); d = os.path.join(POND, day); n = 1
while os.path.exists(d): n += 1; d = os.path.join(POND, "%s-%d" % (day, n))
os.makedirs(d)
json.dump(now, open(os.path.join(d, "hashes.json"), "w", encoding="utf-8"), indent=1)
json.dump(flags, open(os.path.join(d, "flags.json"), "w", encoding="utf-8"), indent=1)
b = subprocess.run([sys.executable, "-X", "utf8", "-I", os.path.join(HERE, "build_eco.py"), B["hunt"]], capture_output=True, text=True)
dep = None; dep_tail = None
if "--no-deploy" not in sys.argv and b.returncode == 0:
    r = subprocess.run("wrangler deploy", shell=True, cwd=HERE, capture_output=True, text=True); dep = r.returncode
    dep_tail = (r.stdout + r.stderr).strip().splitlines()[-6:]                      # kept in the row: a failed deploy reads on the digest, not in a lost log
# MARKET-SPECS-01 (DAY ORDER 5, 2026-10-24): the market specification set regenerated from the live record after the re-sign, into this drop (arked and blobbed with it)
sp = subprocess.run([sys.executable, "-X", "utf8", "-I", os.path.join(HERE, "build_specs.py"), d], capture_output=True, text=True); specs_line = ((sp.stdout or sp.stderr).strip().splitlines() or [""])[-1][:200]
row = {"agent": "eco-refresh", "night": day, "specs": specs_line, "specs_rc": sp.returncode, "verdict": "PASS" if b.returncode == 0 and dep in (None, 0) else "FAIL", "pages_read": len(now),
       "pages_failed": sum(1 for r in now.values() if r["sha256"] is None), "fields_flagged": len(flags), "markets_touched": sorted({f["market"] for f in flags}),
       "first_run": not prev, "build": (b.stdout.strip().splitlines() or [""])[-1][:200], "deploy_rc": dep, "deploy_tail": dep_tail if dep else None, "lab_spend": "$0 (no engine; direct reads)", "ark": None}
if os.environ.get("ARK_ENABLED") == "1": row["ark"] = {"bucket": os.environ.get("ARK_BUCKET", "allooloo-ark-eco"), "prefix": "eco/refresh/%s/" % os.path.basename(d), "objects": 3}
json.dump(row, open(os.path.join(d, "DIGEST-ROW.json"), "w", encoding="utf-8"), indent=1)
if os.environ.get("ARK_ENABLED") == "1":
    import boto3
    s3 = boto3.client("s3", region_name=os.environ.get("ARK_REGION", "us-east-1")); bucket = os.environ.get("ARK_BUCKET", "allooloo-ark-eco"); put = 0
    for f in os.listdir(d):
        key = "eco/refresh/%s/%s" % (os.path.basename(d), f)   # house layout: each bucket under its own prefix (ark-writer may write eco/* only)
        try: s3.head_object(Bucket=bucket, Key=key); continue                      # put-only: an object already arked is never written again
        except Exception: pass
        s3.upload_file(os.path.join(d, f), bucket, key); put += 1
    print("ark put", put, "of", len(os.listdir(d)))
if BLOB:                                                                              # immutable: a blob already there is never overwritten
    for f in os.listdir(d):
        BLOB.upload_blob("eco/refresh/%s/%s" % (os.path.basename(d), f), open(os.path.join(d, f), "rb"), overwrite=False)
    n = 1; name = "digest/rows/%s/eco-refresh.json" % day
    while BLOB.get_blob_client(name).exists(): n += 1; name = "digest/rows/%s/eco-refresh-%d.json" % (day, n)   # same-day re-run: beside, never over
    BLOB.upload_blob(name, json.dumps(row).encode(), overwrite=False)
print(json.dumps(row))
