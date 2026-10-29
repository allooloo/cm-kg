r"""survey_zones.py — PROTOCOLS-A-01 (2026-10-24): every Allooloo zone of record (Allooloo_Domains_Master.xlsx, Build sheet, 310 rows) read live:
/llms.txt (redirects followed: a forward-only twin is answered by its canonical), /.well-known/agent-card.json (does it name the resolver
mcp.getissuer.ai?), /.well-known/mcp.json or /mcp.json (does it carry the x402 payment door?). Writes zones-<tag>.json. Usage: python -X utf8 -I survey_zones.py <tag>"""
import sys, os, json, openpyxl, urllib.request, urllib.error, concurrent.futures as cf
TAG = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
wb = openpyxl.load_workbook(r"C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.xlsx", read_only=True, data_only=True)
rows = list(wb["Build"].iter_rows(values_only=True))[1:]
zones = sorted({str(r[0]).strip().lower() for r in rows if r and r[0] and "." in str(r[0])})
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8 PROTOCOLS-A-01 survey"}), timeout=25) as r: return r.status, r.read(200000), r.geturl()
    except urllib.error.HTTPError as e: return e.code, b"", u
    except Exception as e: return 0, b"", u
def one(z):
    out = {"zone": z}
    st, b, fin = get(f"https://{z}/llms.txt"); out["llms"] = [st, fin if fin != f"https://{z}/llms.txt" else None]
    st, b, fin = get(f"https://{z}/.well-known/agent-card.json"); out["card"] = [st, b"mcp.getissuer.ai" in b or b"capitalmarketsknowledgegraph.ai/mcp" in b, fin if fin != f"https://{z}/.well-known/agent-card.json" else None]
    m = None
    for p in ("/.well-known/mcp.json", "/mcp.json"):
        st, b, fin = get(f"https://{z}{p}")
        if st == 200: m = [p, st, b'"x402"' in b or b"x402" in b, fin if fin != f"https://{z}{p}" else None]; break
    out["mcp"] = m or [None, st, False, None]
    return out
with cf.ThreadPoolExecutor(24) as ex: res = list(ex.map(one, zones))
json.dump(res, open(os.path.join(HERE, f"zones-{TAG}.json"), "w", encoding="utf-8"), indent=1)
n = len(res); llms = sum(1 for r in res if r["llms"][0] == 200); card = sum(1 for r in res if r["card"][0] == 200 and r["card"][1]); mcp = sum(1 for r in res if r["mcp"][1] == 200 and r["mcp"][2])
print(f"zones {n} · llms.txt 200 {llms} · card naming the resolver {card} · mcp.json with x402 {mcp}")
