import json, urllib.request, os, sys
TOK = open(r"C:\ALLOOLOO\AGENT KEYS\cloudflare.txt").read().strip()
def cf(method, path, body=None, raw=False):
    req = urllib.request.Request("https://api.cloudflare.com/client/v4" + path, method=method,
        data=None if body is None else (body if raw else json.dumps(body).encode()),
        headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except Exception: return {"success": False, "status": e.code}
def zones(name=None):
    out, page = [], 1
    while True:
        q = f"/zones?per_page=50&page={page}" + (f"&name={name}" if name else "")
        r = cf("GET", q); out += r.get("result", [])
        if page >= r.get("result_info", {}).get("total_pages", 1): return out
        page += 1
