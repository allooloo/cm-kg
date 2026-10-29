r"""routes_allooloo_ai.py — X402-A-01 + PROTOCOLS-A-01 (2026-10-24): allooloo.ai serves /x402*, /.well-known/* and /llms.txt from eco-pages (beside
/markets*). The apex 308 rule to allooloo.io gains the exemptions (prior expression kept in routes-backup\allooloo.ai.<date>.json, first copy kept);
routes allooloo.ai/x402*, allooloo.ai/.well-known/*, allooloo.ai/llms.txt -> eco-pages. Every other path still 308s to allooloo.io. Usage: python -X utf8 -I routes_allooloo_ai.py dry|apply"""
import sys, os, io, json, time, urllib.request, urllib.error
MODE = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); BK = os.path.join(HERE, "routes-backup")
TOK = io.open(r"C:\ALLOOLOO\AGENT KEYS\cloudflare.txt", encoding="utf-8").read().strip().splitlines()[0]
def api(p, m="GET", b=None):
    req = urllib.request.Request("https://api.cloudflare.com/client/v4" + p, method=m, headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}, data=json.dumps(b).encode() if b is not None else None)
    try: return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e: return json.loads(e.read() or b"{}")
Z = api("/zones?name=allooloo.ai")["result"][0]["id"]
ep = api(f"/zones/{Z}/rulesets/phases/http_request_dynamic_redirect/entrypoint")["result"]; routes = api(f"/zones/{Z}/workers/routes")["result"]
bp = os.path.join(BK, "allooloo.ai.2026-10-24.json")
if not os.path.exists(bp): json.dump({"read": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ruleset": ep, "routes": routes}, open(bp, "w", encoding="utf-8"), indent=1)
EX = ['/x402', '/.well-known', '/llms.txt']; acts = []
for r in ep["rules"]:
    if not r.get("enabled", True) or "allooloo.io" not in json.dumps(r.get("action_parameters")): continue
    e = r["expression"]
    for x in EX:
        if f'"{x}"' not in e: e = '(%s) and not starts_with(http.request.uri.path, "%s")' % (e, x)
    if e != r["expression"]:
        body = {k: r[k] for k in ("action", "action_parameters", "description", "enabled") if k in r}; body["expression"] = e
        acts.append(("amend_rule", r["id"], e))
        if MODE == "apply": acts[-1] += (api(f"/zones/{Z}/rulesets/{ep['id']}/rules/{r['id']}", "PATCH", body).get("success"),)
have = {x["pattern"] for x in routes}
for p in ("allooloo.ai/x402*", "allooloo.ai/.well-known/*", "allooloo.ai/llms.txt"):
    if p not in have:
        acts.append(("add_route", p))
        if MODE == "apply": acts[-1] += (api(f"/zones/{Z}/workers/routes", "POST", {"pattern": p, "script": "eco-pages"}).get("success"),)
if MODE == "apply": acts.append(("purge", api(f"/zones/{Z}/purge_cache", "POST", {"purge_everything": True}).get("success")))
json.dump(acts, open(os.path.join(HERE, "routes-allooloo-ai-%s.json" % MODE), "w", encoding="utf-8"), indent=1); print(json.dumps(acts, indent=1)[:1500])
