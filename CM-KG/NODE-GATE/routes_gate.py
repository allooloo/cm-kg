r"""routes_gate.py — RCO-A-01 (2026-10-24): route mcp.<cc>-cm-kg.ai/* to the Worker cmkg-node-gate on the node zones named (nl first: the proving node).
Prior routes of each zone are backed up first (routes-backup\<zone>.json, first copy kept); an existing route on that pattern is re-pointed, its prior script
kept in the backup. Rollback = remove the route (the request then reaches the node's Container App exactly as before). Nothing else on the zone changes.
Usage: python -X utf8 -I routes_gate.py dry|apply <cc> [<cc> ...] | all"""
import sys, os, io, json, time, urllib.request, urllib.error
MODE = sys.argv[1]; SEL = sys.argv[2:]
ALL = ["ca", "uk", "us", "de", "fr", "nl", "ch", "au", "sg", "jp", "kr", "hk"]
if SEL == ["all"]: SEL = ALL
HERE = os.path.dirname(os.path.abspath(__file__)); BK = os.path.join(HERE, "routes-backup"); os.makedirs(BK, exist_ok=True)
TOK = io.open(r"C:\ALLOOLOO\AGENT KEYS\cloudflare.txt", encoding="utf-8").read().strip().splitlines()[0]; SCRIPT = "cmkg-node-gate"
def api(p, m="GET", b=None):
    for a in range(5):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4" + p, method=m, headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}, data=json.dumps(b).encode() if b is not None else None), timeout=60).read())
        except urllib.error.HTTPError as e:
            r = json.loads(e.read() or b"{}")
            if e.code == 429: time.sleep(5 * (a + 1)); continue
            return r
        except Exception: time.sleep(3)
    return {"success": False, "errors": ["retries"]}
log = {}
for cc in SEL:
    z = "%s-cm-kg.ai" % cc; Z = api("/zones?name=" + z)["result"][0]["id"]; pat = "mcp.%s/*" % z
    routes = api(f"/zones/{Z}/workers/routes").get("result", [])
    bp = os.path.join(BK, z + ".json")
    if not os.path.exists(bp): json.dump({"zone": z, "zone_id": Z, "read": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "routes": routes}, open(bp, "w", encoding="utf-8"), indent=1)
    ex = [r for r in routes if r["pattern"] == pat]; act = ("repoint", ex[0].get("script")) if ex else ("add",)
    res = None
    if MODE == "apply":
        res = api(f"/zones/{Z}/workers/routes/{ex[0]['id']}", "PUT", {"pattern": pat, "script": SCRIPT}) if ex else api(f"/zones/{Z}/workers/routes", "POST", {"pattern": pat, "script": SCRIPT})
        res = [res.get("success"), (res.get("errors") or [None])[0]]
    log[z] = {"pattern": pat, "action": act, "result": res, "other_routes": [r["pattern"] for r in routes if r["pattern"] != pat]}
    print(z, log[z])
json.dump(log, open(os.path.join(HERE, "routes-%s-%s.json" % (MODE, "_".join(SEL))), "w", encoding="utf-8"), indent=1)
