"""MAIL-01 item 7 sweep: every host the account serves through a Worker (custom domains + zone routes) or a Pages project (custom domains), read on
/, /.well-known/security.txt, /llms.txt, /facts.json, /.well-known/agent-card.json, /contact, /about — any still printing allooloo@hey.com is listed.
Read only. Token read in-process. Writes sweep_hey.json."""
import json, re, sys, urllib.request, urllib.error, concurrent.futures as cf, pathlib
sys.path.insert(0, r"C:\AGENTBEV\OPS\BEV-LIB-02-2026-11-10"); from cf import api, ACCOUNT
HERE = pathlib.Path(__file__).parent
hosts = set()
for d in api("GET", f"/accounts/{ACCOUNT}/workers/domains?per_page=1000").get("result") or []: hosts.add(d["hostname"])
page = 1
while True:
    j = api("GET", f"/zones?per_page=50&page={page}&account.id={ACCOUNT}")
    for z in j.get("result") or []:
        for r in api("GET", f"/zones/{z['id']}/workers/routes").get("result") or []:
            h = r["pattern"].split("/")[0].lstrip("*.")
            if h and "*" not in h: hosts.add(h)
    if page >= (j.get("result_info") or {}).get("total_pages", 1): break
    page += 1
for p in api("GET", f"/accounts/{ACCOUNT}/pages/projects?per_page=50").get("result") or []:
    for d in p.get("domains") or []: hosts.add(d)
hosts = sorted(h for h in hosts if not h.startswith("www."))
PATHS = ["/", "/.well-known/security.txt", "/llms.txt", "/facts.json", "/.well-known/agent-card.json", "/contact", "/about"]
def one(h):
    hits = []
    for p in PATHS:
        try:
            with urllib.request.urlopen(urllib.request.Request(f"https://{h}{p}", headers={"User-Agent": "mail-01-sweep/1.0"}), timeout=20) as r:
                if r.status == 200 and b"allooloo@hey.com" in r.read(): hits.append(p)
        except Exception: pass
    return h, hits
with cf.ThreadPoolExecutor(24) as ex: R = list(ex.map(one, hosts))
left = {h: p for h, p in R if p}
json.dump({"hosts": len(hosts), "printing": left}, open(HERE / "sweep_hey.json", "w", encoding="utf-8"), indent=1)
print("hosts swept:", len(hosts), "· still printing allooloo@hey.com:", len(left))
for h, p in sorted(left.items()): print(" ", h, p)
