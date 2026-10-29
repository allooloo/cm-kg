"""SEC Fails-to-Deliver data as an official source of SYMBOL -> CUSIP pairs.

Source: https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data
Files cnsfailsYYYYMM{a,b}.zip, pipe-delimited:
SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY|(DESCRIPTION)|PRICE
Only securities with a fail-to-deliver balance in the window appear, so this is partial coverage.
"""
import datetime as dt
import io
import json
import os
import re
import zipfile

import requests

INDEX = "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data"
TICKERS = "https://www.sec.gov/files/company_tickers_exchange.json"
H = {"User-Agent": "Allooloo Technologies Corp. developers@allooloo.ai", "Accept-Encoding": "gzip, deflate"}
N_FILES = 12


def _get(u):
    r = requests.get(u, headers=H, timeout=120)
    r.raise_for_status()
    return r


def file_urls(n=N_FILES):
    html = _get(INDEX).text
    hrefs = dict.fromkeys(re.findall(r'href="([^"]*cnsfails(\d{6}[ab])\.zip)"', html))
    items = sorted(((k[1], k[0]) for k in hrefs), reverse=True)[:n]
    return [(tag, u if u.startswith("http") else "https://www.sec.gov" + u) for tag, u in items]


def fetch(n=N_FILES):
    files = file_urls(n)
    seen = {}  # symbol -> {cusip -> {description, last_seen, files}}
    for tag, url in files:
        z = zipfile.ZipFile(io.BytesIO(_get(url).content))
        for member in z.namelist():
            text = z.read(member).decode("latin-1")
            for line in text.splitlines()[1:]:
                p = line.split("|")
                if len(p) < 6:
                    continue
                date, cusip, sym, desc = p[0].strip(), p[1].strip().upper(), p[2].strip().upper(), p[4].strip()
                if not (sym and re.fullmatch(r"[0-9A-Z]{9}", cusip) and re.fullmatch(r"\d{8}", date)):
                    continue
                d = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                e = seen.setdefault(sym, {}).setdefault(cusip, {"description": desc, "last_seen": d, "files": set()})
                if d >= e["last_seen"]:
                    e["last_seen"], e["description"] = d, desc or e["description"]
                e["files"].add(tag)
    clean, conflicts = {}, {}
    for sym, by in sorted(seen.items()):
        if len(by) == 1:
            (c, e), = by.items()
            clean[sym] = {"cusip": c, "description": e["description"], "last_seen": e["last_seen"],
                          "files_seen": len(e["files"])}
        else:
            conflicts[sym] = {c: {"description": e["description"], "last_seen": e["last_seen"],
                                  "files_seen": len(e["files"])} for c, e in by.items()}
    return {"source_url": INDEX, "files": [u for _, u in files], "read_by": "Allooloo Technologies Corp. sec_ftd.py",
            "read_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "count": len(clean), "count_conflicts": len(conflicts), "symbols": clean, "conflicts": conflicts}


def coverage(symbols):
    t = _get(TICKERS).json()
    i = t["fields"].index("ticker")
    ex = t["fields"].index("exchange")
    tick = {r[i].upper() for r in t["data"] if r[i] and r[ex]}
    norm = lambda s: s.replace("-", ".").replace("/", ".")
    have = set(symbols) | {norm(s) for s in symbols} | {s.replace(".", "") for s in symbols}
    hit = {s for s in tick if s in have or norm(s) in have or s.replace("-", "") in have}
    return {"tickers_url": TICKERS, "exchange_listed_tickers": len(tick), "covered": len(hit),
            "pct": round(100 * len(hit) / max(len(tick), 1), 1)}


if __name__ == "__main__":
    out = fetch()
    out["coverage"] = coverage(out["symbols"])
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"us-ftd-{dt.date.today().isoformat()}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("files:", len(out["files"]), out["files"][0].rsplit("/", 1)[1], "..", out["files"][-1].rsplit("/", 1)[1])
    print("distinct symbols, one CUSIP:", out["count"], "| conflicts:", out["count_conflicts"])
    print("coverage of company_tickers_exchange.json:", out["coverage"])
    for s in ("AAPL", "MSFT", "TSLA"):
        print(s, out["symbols"].get(s))
