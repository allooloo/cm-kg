r"""routes_acm.py — ACM-SIGNALS-01 (DAY ORDER 3, 2026-10-24): bind the Worker acm-signals to acm-000/200/300/403/404/451/500 .ai/.org/.com (21 zones; .io untouched).
Per zone, the ECO-01 rail unchanged: (1) the prior state — redirect entrypoint rules, Worker routes, apex/www DNS — goes to routes-backup\<zone>.json (first copy kept);
(2) every enabled redirect rule is DISABLED, never deleted (restore = enabled true from the backup); (3) routes <zone>/* and www.<zone>/* -> acm-signals;
(4) a proxied AAAA 100:: placeholder where the apex has no proxied record; then purge. Usage: python -X utf8 -I routes_acm.py dry|apply"""
import sys, os, io, json, time, urllib.request, urllib.error
MODE = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__)); BK = os.path.join(HERE, "routes-backup"); os.makedirs(BK, exist_ok=True)
TOK = io.open(r"C:\ALLOOLOO\AGENT KEYS\cloudflare.txt", encoding="utf-8").read().strip().splitlines()[0]; SCRIPT = "acm-signals"
def api(p, m="GET", b=None):
    for a in range(5):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4" + p, method=m, headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}, data=json.dumps(b).encode() if b is not None else None), timeout=60).read())
        except urllib.error.HTTPError as e:
            r = json.loads(e.read() or b"{}")
            if e.code == 429: time.sleep(5 * (a + 1)); continue
            return r
        except Exception: time.sleep(3)
    return {"success": False, "errors": ["retries"]}
targets = ["acm-%s.%s" % (c, t) for c in ("000", "200", "300", "403", "404", "451", "500") for t in ("ai", "org", "com")]
log = {}
for z in targets:
    zr = api("/zones?name=" + z).get("result") or []
    if not zr: log[z] = {"error": "zone not on the account"}; print(z, "NOT FOUND"); continue
    Z = zr[0]["id"]; rec = {"zone": z, "actions": [], "results": []}
    ep = api(f"/zones/{Z}/rulesets/phases/http_request_dynamic_redirect/entrypoint"); rules = (ep.get("result") or {}).get("rules", []); rsid = (ep.get("result") or {}).get("id")
    routes = api(f"/zones/{Z}/workers/routes").get("result", []); dns = [d for d in api(f"/zones/{Z}/dns_records?per_page=100").get("result", []) if d["name"] in (z, "www." + z)]
    bp = os.path.join(BK, z + ".json")
    if not os.path.exists(bp): json.dump({"zone": z, "zone_id": Z, "read": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ruleset_id": rsid, "redirect_rules": rules, "routes": routes, "dns": dns}, open(bp, "w", encoding="utf-8"), indent=1)
    def do(action, call):
        rec["actions"].append(action)
        if MODE == "apply": r = call(); rec["results"].append([action[0], bool(r.get("success")), (r.get("errors") or [None])[0]])
    for r in rules:
        if not r.get("enabled", True): continue
        body = {k: r[k] for k in ("action", "action_parameters", "expression", "description", "enabled") if k in r}; body["enabled"] = False
        do(("disable_rule", r["id"], r["expression"][:80]), lambda b=body, i=r["id"]: api(f"/zones/{Z}/rulesets/{rsid}/rules/{i}", "PATCH", b))
    have = {r["pattern"] for r in routes}
    for r in routes:
        if r.get("script") != SCRIPT: do(("repoint_route", r["pattern"], r.get("script")), lambda r=r: api(f"/zones/{Z}/workers/routes/{r['id']}", "PUT", {"pattern": r["pattern"], "script": SCRIPT}))
    for p in (z + "/*", "www." + z + "/*"):
        if p not in have: do(("add_route", p), lambda p=p: api(f"/zones/{Z}/workers/routes", "POST", {"pattern": p, "script": SCRIPT}))
    if not any(d["name"] == z and d.get("proxied") for d in dns):
        do(("add_placeholder_AAAA", z), lambda: api(f"/zones/{Z}/dns_records", "POST", {"type": "AAAA", "name": z, "content": "100::", "proxied": True, "comment": "ACM-SIGNALS-01 2026-10-24: placeholder so the acm-signals route fires"}))
    if MODE == "apply" and rec["results"]: rec["purge"] = api(f"/zones/{Z}/purge_cache", "POST", {"purge_everything": True}).get("success")
    log[z] = rec
    if MODE == "dry" or any(not x[1] for x in rec["results"]): print(z, rec["actions"], rec["results"] if MODE == "apply" else "")
json.dump(log, open(os.path.join(HERE, "routes-%s.json" % MODE), "w", encoding="utf-8"), indent=1)
fails = {z: [x for x in v.get("results", []) if not x[1]] for z, v in log.items() if any(not x[1] for x in v.get("results", []))}
print(MODE, "zones", len(log), "actions", sum(len(v.get("actions", [])) for v in log.values()), "fails", len(fails), json.dumps(fails)[:600])
