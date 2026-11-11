"""MAIL-01: Cloudflare Email Routing log for agent-bev.ai, last 2 hours — events to ops@agent-bev.ai (status, action, SPF/DKIM/DMARC). Read only."""
import json, sys, urllib.request, datetime as dt
def tok(p): t = open(p, encoding="utf-8", errors="ignore").read(); return max(t.replace("=", " ").split(), key=len)
Q = """query($z:String!,$a:Time!,$b:Time!){viewer{zones(filter:{zoneTag:$z}){emailRoutingAdaptive(limit:50,filter:{datetime_geq:$a,datetime_lt:$b},orderBy:[datetime_DESC]){datetime to from status action errorDetail spf dkim dmarc}}}}"""
now = dt.datetime.now(dt.timezone.utc)
v = {"z": "b3aa1d60601731bb4a8082e081f5fdf6", "a": (now - dt.timedelta(hours=2)).isoformat().replace("+00:00", "Z"), "b": now.isoformat().replace("+00:00", "Z")}
for p in [r"C:\ALLOOLOO\AGENT KEYS\cloudflare-analytics.txt", r"C:\ALLOOLOO\AGENT KEYS\cloudflare.txt"]:
    r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=json.dumps({"query": Q, "variables": v}).encode(), headers={"Authorization": "Bearer " + tok(p), "Content-Type": "application/json"}), timeout=60))
    if not r.get("errors"): break
ev = [x for x in r["data"]["viewer"]["zones"][0]["emailRoutingAdaptive"] if (x.get("to") or "").lower() == "ops@agent-bev.ai"]
print("events to ops@agent-bev.ai (2 h):", len(ev))
for x in ev: print(" ", x["datetime"], "status", x["status"], "action", x["action"], "from", x["from"], "spf", x["spf"], "dkim", x["dkim"], "dmarc", x["dmarc"], x.get("errorDetail") or "")
sys.exit(0 if any(x["status"] == "delivered" for x in ev) else 1)
