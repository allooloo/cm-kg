r"""eco_ops.py — ECO-OPS-01 (CEO, 2026-10-28): the nightly rebuild of the SM-ECO-10060 set (apex + 49 member pages on .org/.com/.ai = 148 hosts, the
SITE-03A + MANIFEST-03/04 generator) and the REF-01 check, as one Ops Agent in the Allooloo Azure ops set (job cmkg-eco-ops, 03:00 UTC), the hub pattern:
read → rebuild → diff → (grep blocks) → roll on difference → one line to the ops log → digest row → ark/standby when armed. Never typed values.
  1. read  list_nodes · acm-68000.org/signals.json · the FR record (site03a.py does the reads at build) — the roster of record is the apex.
  2. rebuild  site03a.py apply on the image's copy of the snapshots of record (the folder the Pages projects are built from).
  3. diff  every file against the last build (build timestamps and sitemap lastmod normalised out); hosts/paths that differ are the change.
  4. grep  the eight banned words (ruling (b): the duty lines of record are exempt); a non-zero count BLOCKS the roll and is logged.
  5. roll  on difference: sign the 148 cards (sign_ops.py; the GSC signing credential by reference) → pages_app.py gp-sm parts 0-2 --upload
           (the Pages token by reference) → verify_site03a.py live. A credential not placed holds the roll and names the hand.
  6. REF-01  the member lines on the 49 country ECO pages against the registry order (fetched live); a mismatch is a hand item for the ECO Worker.
  7. GH-01  registry.json (the generator writes it) is committed to github.com/allooloo/sm-eco-10060 when it differs (GITHUB_TOKEN by reference; held if absent).
  8. record  ops/eco-ops/<night>/run.json (+ grep/verify/registry files) beside never over; one line ops/eco-ops/<night>/LINE.txt and the rolled log
           ops/eco-ops/LOG.md; digest row digest/rows/<night>/eco-ops.json; ark: put-only to s3://<ARK_BUCKET>/eco-ops/<night>/ when ARK_ENABLED=1.
Env: SITE03A_SNAP SITE03A_LANE SITE03A_REGISTRY CULL_ROOT PROTOCOLS_DIR OPS_ACCOUNT OPS_CONTAINER [CLOUDFLARE_PAGES_TOKEN GSC_SIGN_* GITHUB_TOKEN ARK_*]
Laptop dry run: DRY_DIR=<dir> writes the records there, rolls nothing. Usage: python -X utf8 eco_ops.py"""
import os, sys, re, json, time, hashlib, shutil, datetime, subprocess, urllib.request, collections
HERE = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
SNAP = os.environ["SITE03A_SNAP"]; LANE = os.environ["SITE03A_LANE"]; REGF = os.environ["SITE03A_REGISTRY"]; CULL = os.environ["CULL_ROOT"]; PROT = os.environ["PROTOCOLS_DIR"]
DRY = os.environ.get("DRY_DIR"); T0 = datetime.datetime.now(datetime.timezone.utc); NIGHT = os.environ.get("NIGHT") or T0.date().isoformat()
EXEC = os.environ.get("CONTAINER_APP_JOB_EXECUTION_NAME", os.environ.get("HOSTNAME", "laptop")); IMAGE_TAG = os.environ.get("IMAGE_TAG", "?")
# VAULT-DROP-01 (2026-10-28): PROVE=1 is set only on a manual start (never on the schedule). It signs and rolls with no difference and commits
# registry.json even when the repo already matches, so every credential path is proven once. The nightly never carries it.
PROVE = os.environ.get("PROVE") == "1"
REG = json.load(open(REGF, encoding="utf-8")); CCS = [m["cc"].lower() for arr in REG["jurisdictional_nodes"]["regions"].values() for m in arr]
HOSTS = ["sm-eco-10060.org"] + [f"{cc}-eco-10060.{t}" for cc in CCS for t in ("org", "com", "ai")]
LOG = []
def log(*a):
    s = f"{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')} " + " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)
def sh(args, env=None, cwd=None):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, **(env or {})}, cwd=cwd); return p.returncode, (p.stdout + p.stderr)
NORM = [(re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"), "T"), (re.compile(r"<lastmod>[^<]*</lastmod>"), "<lastmod/>"), (re.compile(r'"updated": "\d{4}-\d{2}-\d{2}"'), '"updated"')]
def norm(b, name=""):
    try: s = b.decode("utf-8")
    except Exception: return hashlib.sha256(b).hexdigest()
    if name.endswith("agent-card.json"):   # the generator writes the card unsigned; the roll signs it — compare the card, not the signature
        try: d = json.loads(s); d.pop("signatures", None); s = json.dumps(d, sort_keys=True, ensure_ascii=False)
        except Exception: pass
    for rx, r in NORM: s = rx.sub(r, s)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
def snapshot_hashes():
    out = {}
    for h in HOSTS:
        for root, _, fs in os.walk(os.path.join(SNAP, h)):
            for f in fs:
                p = os.path.join(root, f); out[os.path.relpath(p, SNAP).replace("\\", "/")] = norm(open(p, "rb").read(), f)
    return out
# ---- the ops store
ops = None
if not DRY and os.environ.get("OPS_ACCOUNT"):
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient, ContentSettings
    ops = BlobServiceClient(f"https://{os.environ['OPS_ACCOUNT']}.blob.core.windows.net", credential=DefaultAzureCredential()).get_container_client(os.environ.get("OPS_CONTAINER", "ops"))
def put_beside(name, data, ct="application/json"):
    if isinstance(data, str): data = data.encode("utf-8")
    if DRY or ops is None:
        p = os.path.join(DRY or LANE, "ops", name); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "wb").write(data); return name
    n, i = name, 1
    while ops.get_blob_client(n).exists(): i += 1; n = re.sub(r"(\.[a-z]+)$", f"-{i}\\1", name)
    ops.upload_blob(n, data, content_settings=ContentSettings(content_type=ct)); return n
def put_over(name, data, ct="text/markdown"):
    if isinstance(data, str): data = data.encode("utf-8")
    if DRY or ops is None: return put_beside(name, data, ct)
    ops.upload_blob(name, data, overwrite=True, content_settings=ContentSettings(content_type=ct)); return name
def get_text(name):
    try:
        if DRY or ops is None: return open(os.path.join(DRY or LANE, "ops", name), encoding="utf-8").read()
        return ops.get_blob_client(name).download_blob().readall().decode("utf-8")
    except Exception: return None
row = {"agent": "eco-ops", "night": NIGHT, "verdict": "PASS", "hosts_changed": 0, "paths_changed": 0, "flags": [], "hand_items": [], "rolled": False, "execution": EXEC, "image": IMAGE_TAG}
hands = row["hand_items"]; flags = row["flags"]
try:
    log(f"ECO-OPS-01 night {NIGHT} image {IMAGE_TAG} execution {EXEC}")
    before = snapshot_hashes(); prev_build = get_text("eco-ops/last-build.json"); prev = json.loads(prev_build) if prev_build else before
    # 2. rebuild from the live reads
    rc, out = sh([PY, "-X", "utf8", os.path.join(PROT, "site03a.py"), "apply"], cwd=PROT); log("site03a apply rc", rc, out.strip().splitlines()[-1][:200] if out.strip() else "")
    if rc: raise RuntimeError("site03a.py apply failed: " + out[-400:])
    after = snapshot_hashes(); changed = sorted(p for p in set(after) | set(prev) if after.get(p) != prev.get(p)); hosts_changed = sorted({p.split("/")[0] for p in changed})
    row["hosts_changed"] = len(hosts_changed); row["paths_changed"] = len(changed); row["changed_sample"] = changed[:40]
    log("diff vs last build:", len(hosts_changed), "hosts,", len(changed), "paths", changed[:5])
    # 4. the banned grep blocks
    rc, out = sh([PY, "-X", "utf8", os.path.join(LANE, "grep_banned.py")]); g = json.load(open(os.path.join(LANE, "grep-banned.json"), encoding="utf-8")); banned = sum(g["banned"].values())
    log("banned grep:", g["banned"] or 0)
    if banned: row["verdict"] = "FAIL"; flags.append(f"banned words {g['banned']} — roll blocked"); hands.append("rule the wording (grep-banned.json names the files)")
    # 6. REF-01: the member lines live against the registry order
    want = {cc: i + 1 for i, cc in enumerate(CCS)}; bad = []
    def member_live(cc):
        for attempt in range(3):
            try:
                b = urllib.request.urlopen(urllib.request.Request(f"https://{cc}-eco.ai/", headers={"User-Agent": "Allooloo eco-ops (REF-01 check)"}), timeout=30).read().decode("utf-8", "replace")
                m = re.search(r"Member (\d+) of 49 under SM-ECO-10060", b); return cc, int(m.group(1)) if m else None
            except Exception: time.sleep(3 * (attempt + 1))
        return cc, "unreachable"
    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(8) as ex:
        for cc, n in ex.map(member_live, CCS):
            if n != want[cc]: bad.append(f"{cc}-eco.ai: {n} (registry {want[cc]})")
    row["ref01_mismatch"] = bad
    if bad: flags.append(f"REF-01 lines off on {len(bad)} ECO pages"); hands.append("re-run CM-KG\\ECO\\patch_ref01.py and redeploy eco-pages (" + "; ".join(bad[:5]) + ")")
    log("REF-01 check: mismatches", len(bad))
    # 5. roll on difference
    if PROVE: log("PROVE=1: proof run (manual start); sign + roll + commit regardless of difference"); row["prove"] = True
    if (changed or PROVE) and not banned:
        held = []
        if not os.environ.get("CLOUDFLARE_PAGES_TOKEN"): held.append("cloudflare-pages-token")
        if not (os.environ.get("GSC_SIGN_TENANT") and os.environ.get("GSC_SIGN_CLIENT") and os.environ.get("GSC_SIGN_SECRET")): held.append("gsc-sign-tenant/client/secret")
        if DRY: held.append("DRY_DIR")
        if held:
            row["roll_held"] = held; flags.append("change found, roll held: " + ", ".join(held)); hands.append("place in allooloo-cmkg-kv-apex: " + ", ".join(h for h in held if h != "DRY_DIR"))
            log("roll held:", held)
        else:
            rc, out = sh([PY, "-X", "utf8", os.path.join(HERE, "sign_ops.py"), SNAP, REGF, os.path.join(LANE, "signed-cards.json")]); log("sign rc", rc, out[-200:])
            if rc: raise RuntimeError("signing failed: " + out[-400:])
            try: sc = json.load(open(os.path.join(LANE, "signed-cards.json"), encoding="utf-8")); row["signed"] = {"kid": sc["kid"], "count": sc["count"], "verified_against": "https://dpuone.ai/.well-known/jwks.json"}
            except Exception as e: row["signed"] = {"error": str(e)[:200]}
            row["pages_deploys"] = []
            ok = True
            # VAULT-DROP-01 guard: assemble every part first (no upload) and roll only if each part's host set equals the custom domains
            # attached to that Pages project. A Pages deploy replaces the whole project, so a different cut would drop hosts.
            acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "dd2832b36f171b815f84c8487aada36b"); HC = {"Authorization": "Bearer " + os.environ["CLOUDFLARE_PAGES_TOKEN"]}
            guard = {}; nparts = None; p = 0
            while nparts is None or p < nparts:
                rc, out = sh([PY, "-X", "utf8", os.path.join(CULL, "pages_app.py"), "gp-sm", "--part", str(p)], cwd=CULL)
                proj = f"cull-gp-sm-{p + 1}"; lg = json.load(open(os.path.join(CULL, "roll", f"app-{proj}.json"), encoding="utf-8")) if rc == 0 else {}
                nparts = lg.get("parts", 0) if nparts is None else nparts
                dom = []; pg = 1
                while True:   # the domains list pages at 20
                    dd = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acct}/pages/projects/{proj}/domains?page={pg}", headers=HC), timeout=60)); dom += dd.get("result") or []
                    if pg >= (dd.get("result_info") or {}).get("total_pages", 1): break
                    pg += 1
                want = {d["name"] for d in dom if not d["name"].startswith("www.")}; have = set(lg.get("hosts", []))
                guard[proj] = {"assembled": len(have), "attached": len(want), "missing": sorted(want - have)[:10], "extra": sorted(have - want)[:10]}
                if rc or not have or want - have: ok = False
                p += 1
            row["roll_guard"] = guard; log("roll guard", json.dumps(guard)[:400])
            if not ok or nparts != 3:
                ok = False; flags.append("roll guard: part host sets differ from the attached Pages domains; nothing uploaded"); hands.append("read run.json roll_guard")
            for part in ([str(i) for i in range(nparts)] if ok else []):
                rc, out = sh([PY, "-X", "utf8", os.path.join(CULL, "pages_app.py"), "gp-sm", "--part", part, "--upload"], cwd=CULL); last = (out.strip().splitlines() or [""])[-1]; log("roll part", part, rc, last[:160]); row["pages_deploys"].append({"project": f"cull-gp-sm-{int(part) + 1}", "rc": rc, "upload_ok": "UPLOAD OK" in out, "last": last[:200]})
                if rc or "UPLOAD OK" not in out: ok = False
            rc, out = sh([PY, "-X", "utf8", os.path.join(LANE, "verify_site03a.py")]); log("verify", rc, out.strip()[-300:]); row["verify"] = out.strip().splitlines()[-8:]
            row["rolled"] = ok and rc == 0 and "not200: []" in out
            if not row["rolled"]: row["verdict"] = "FAIL"; flags.append("roll or verify failed"); hands.append("read run.json: roll/verify output")
            else: log("rolled", len(hosts_changed), "hosts")
    elif not changed: log("no change"); row["note"] = "no change"
    # 7. GH-01 (VAULT-DROP-01 fix): the repo itself is the last-committed copy. The ops copy is written only once the repo holds it,
    # so a commit held for want of a token stays pending instead of being forgotten.
    # 7. GH-01: registry.json on difference
    regp = os.path.join(LANE, "registry.json"); reg_new = open(regp, encoding="utf-8").read() if os.path.exists(regp) else None
    if reg_new:
        import base64
        if not os.environ.get("GITHUB_TOKEN"):
            reg_prev = get_text("eco-ops/registry.json")
            if reg_prev is not None and json.loads(reg_prev).get("registry") == json.loads(reg_new).get("registry"): row["registry"] = "unchanged"
            else: row["registry"] = "changed, commit held: github-token not placed"; flags.append("registry.json changed; GitHub commit held"); hands.append("place github-token in allooloo-cmkg-kv-apex (repo scope, allooloo/sm-eco-10060)")
        else:
            api = "https://api.github.com/repos/allooloo/sm-eco-10060/contents/registry.json"; H = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Accept": "application/vnd.github+json", "User-Agent": "Allooloo eco-ops"}
            cur = json.load(urllib.request.urlopen(urllib.request.Request(api, headers=H), timeout=30)); sha = cur.get("sha")
            repo_reg = json.loads(base64.b64decode(cur.get("content", "")).decode("utf-8")).get("registry") if cur.get("content") else None
            same = repo_reg == json.loads(reg_new).get("registry")
            if same and not PROVE: row["registry"] = "unchanged (matches the repo)"; put_over("eco-ops/registry.json", reg_new, "application/json")
            else:
                msg = f"registry.json: roster read {NIGHT} (ECO-OPS-01 nightly)" if not same else f"registry.json: roster read {NIGHT} (ECO-OPS-01 proof run, VAULT-DROP-01; registry unchanged)"
                body = {"message": msg, "content": base64.b64encode(reg_new.encode("utf-8")).decode(), **({"sha": sha} if sha else {})}
                r = urllib.request.urlopen(urllib.request.Request(api, data=json.dumps(body).encode(), headers=H, method="PUT"), timeout=60); res = json.load(r)
                row["registry"] = f"committed ({r.status}) {res.get('commit', {}).get('sha', '?')[:7]}"; row["commit"] = {"sha": res.get("commit", {}).get("sha"), "url": res.get("commit", {}).get("html_url"), "message": msg}
                put_over("eco-ops/registry.json", reg_new, "application/json")
    # 8. record
    if row["rolled"] or not prev_build: put_over("eco-ops/last-build.json", json.dumps(after), "application/json")
    elif changed: row["note"] = (row.get("note", "") + " last-build.json kept (change not rolled)").strip()
    line = f"{NIGHT} · eco-ops · {row['verdict']} · hosts changed {row['hosts_changed']} · paths {row['paths_changed']} · {'rolled' if row['rolled'] else ('no change' if not (changed or PROVE) else ('held: ' + ', '.join(row['roll_held']) if row.get('roll_held') else ('blocked: banned words' if banned else 'roll failed')))} · banned {banned} · REF-01 mismatches {len(bad)} · registry {row.get('registry', '—')}"
    row["line"] = line; log(line)
except Exception as e:
    import traceback; row["verdict"] = "FAIL"; row["error"] = repr(e)[:400]; flags.append("FAIL: " + repr(e)[:160]); hands.append("read run.json"); line = f"{NIGHT} · eco-ops · FAIL · {repr(e)[:160]}"; row["line"] = line; log(line, traceback.format_exc()[-600:])
row["written_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(); row["log"] = LOG[-60:]
n1 = put_beside(f"eco-ops/{NIGHT}/run.json", json.dumps(row, ensure_ascii=False, indent=1)); n2 = put_beside(f"eco-ops/{NIGHT}/LINE.txt", row["line"] + "\n", "text/plain")
for f in ("grep-banned.json", "verify-live.json", "registry.json", "site03a-apply.json"):
    p = os.path.join(LANE, f)
    if os.path.exists(p): put_beside(f"eco-ops/{NIGHT}/{f}", open(p, "rb").read())
prev_log = get_text("eco-ops/LOG.md") or "# ECO-OPS-01 — the nightly rebuild, one line per night (newest on top)\n"
put_over("eco-ops/LOG.md", prev_log.split("\n", 1)[0] + "\n" + row["line"] + "\n" + prev_log.split("\n", 1)[1] if "\n" in prev_log else prev_log + row["line"] + "\n")
put_beside(f"digest/rows/{NIGHT}/eco-ops.json", json.dumps({k: row[k] for k in ("agent", "night", "verdict", "hosts_changed", "paths_changed", "flags", "hand_items", "rolled", "execution", "image", "line")}, ensure_ascii=False))
if os.environ.get("ARK_ENABLED") == "1":
    try:
        import boto3; s3 = boto3.client("s3", region_name=os.environ.get("ARK_REGION", "us-east-1")); bucket = os.environ.get("ARK_BUCKET", "allooloo-ark-eco"); key = f"eco-ops/{NIGHT}/run.json"
        try: s3.head_object(Bucket=bucket, Key=key); log("ark: already arked", key)
        except Exception: s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(row, ensure_ascii=False).encode("utf-8")); log("ark put", key)
    except Exception as e: log("ark failed (flag):", repr(e)[:160])
else: log("ark/standby: ARK_ENABLED=0 (the bucket and the ark writer are the CEO's hand; the record is in allooloocmkgapex/ops)")
log("written", n1, n2, "LOG.md, digest row"); sys.exit(0 if row["verdict"] == "PASS" else 1)
