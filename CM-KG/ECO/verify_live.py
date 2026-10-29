import json, re, urllib.request, urllib.error, concurrent.futures as cf
class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
op = urllib.request.build_opener(NR)
def get(u):
    try: r = op.open(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 ECO-01 verify", "Accept": "*/*", "Cache-Control": "no-cache"}), timeout=30); return r.status, r.headers.get("location"), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: return e.code, e.headers.get("location"), e.read().decode("utf-8", "replace")
    except Exception as e: return 0, None, str(e)
zones = [z[0] for z in json.load(open(r"C:\ALLOOLOO\START_ME_UP\ECO-01\eco_zones.json")) if re.match(r"^[a-z]{2}-eco\.(ai|io|org|com|net)$", z[0])]
def build_no(p): m = re.match(r"eco-(\d{4}-\d{2}-\d{2})(?:-(\d+))?\.json$", p.replace("\\", "/").split("/")[-1]); return (m.group(1), int(m.group(2) or 1)) if m else ("", 0)   # DOORS-02: date, then same-day number
D = json.load(open(max(__import__("glob").glob("data/eco-*.json"), key=build_no), encoding="utf-8"))["markets"]
EX = json.load(open("examples.json", encoding="utf-8"))
PATHS = ["/", "/eco.json", "/signals.json", "/nodes.json", "/health.json", "/llms.txt", "/sitemap.xml", "/.well-known/agent-card.json", "/.well-known/mcp.json", "/.well-known/acm-68000.json", "/.well-known/security.txt"]
def check(z):
    cc, tld = z.split("-eco.")
    bad = []
    if cc not in D:
        st, loc, _ = get("https://%s/" % z)
        if not (st == 301 and loc == "https://allooloo.ai/markets"): bad.append(("/", st, loc))
        return z, "index-301", bad
    if tld != "ai":
        for host in (z, "www." + z):
            st, loc, _ = get("https://%s/eco.json?x=1" % host)
            if not (st == 301 and loc == "https://%s-eco.ai/eco.json?x=1" % cc): bad.append((host, st, loc))
        st, loc, _ = get("https://%s/01/03017620422003" % z)
        if st != 301: bad.append(("/01/", st, loc))
        return z, "twin-301", bad
    for p in PATHS:
        st, loc, b = get("https://%s%s" % (z, p))
        if st != 200: bad.append((p, st, loc))
        elif p == "/" and "Electronic Compliance Object · " + D[cc]["record"]["country"] not in b: bad.append((p, "title"))
        elif p == "/" and cc in EX and "NODE LIVE" not in b: bad.append((p, "not live"))
    st, loc, _ = get("https://www.%s/" % z)
    if st != 200: bad.append(("www", st, loc))
    if cc in EX and not cc.startswith("_"):
        e = EX[cc]; st, loc, b = get("https://%s/%s/%s" % (z, "isin" if e["isin_on_node"] else "ticker", e["isin"] if e["isin_on_node"] else e["ticker"]))
        sig = (json.loads(b).get("signal") if st == 200 else None)
        if sig not in ("ACM-200", "ACM-451"): bad.append(("lookup", st, sig))
    return z, "page", bad
res = list(cf.ThreadPoolExecutor(12).map(check, sorted(zones)))
extra = {}
for u, want in [("https://allooloo.ai/markets", 200), ("https://allooloo.ai/markets.json", 200), ("https://allooloo.ai/", 308), ("https://allooloo.ai/about", 308)]:
    st, loc, b = get(u); extra[u] = [st, loc, st == want]
st, _, b = get("https://allooloo.ai/markets.json"); mj = json.loads(b) if st == 200 else {}
json.dump({"zones": res, "allooloo": extra, "markets_json": {k: mj.get(k) for k in ("markets", "live_nodes")}}, open("verify-live-2026-10-24.json", "w"), indent=0)
import collections
print("zones", len(res), collections.Counter(k for _, k, _ in res), "bad", [(z, b) for z, _, b in res if b][:10])
print(extra); print("markets.json", mj.get("markets"), "live", mj.get("live_nodes"))
