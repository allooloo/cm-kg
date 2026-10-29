"""halt_ca - Canada trading halts, read from CIRO's own Halts/Resumptions bulletins.

CIRO (Canadian Investment Regulatory Organization) imposes regulatory halts on all
Canadian marketplaces (TSX, TSXV, CSE, Cboe Canada). Its page
https://www.ciro.ca/newsroom/halts-and-resumptions embeds its bulletin newsroom
https://iiroc.mediaroom.com/ (Cision-hosted, CIRO's own channel). ciro.ca itself sits
behind a Cloudflare challenge; the mediaroom answers plain HTTP.

Method: one request for the 100 most recent bulletins (Trading Halt / Trade Resumption),
newest first. A symbol is "currently halted" when its most recent bulletin in that window
is a Trading Halt. Then each open halt's bulletin page is read (capped) for company,
venue, reason and halt time. Halts older than the window are not seen (see README).
Stdlib + requests only. No retries beyond 2 attempts per request.
"""
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai (CM-KG halts reader)"
SOURCE_URL = "https://iiroc.mediaroom.com/index.php?s=2429&l=100"
CIRO_PAGE = "https://www.ciro.ca/newsroom/halts-and-resumptions"
DETAIL_CAP = 40
HERE = os.path.dirname(os.path.abspath(__file__))
VENUES = {"tsx": "TSX", "tsx-venture": "TSXV", "tsxv": "TSXV", "cse": "CSE",
          "tsx venture": "TSXV", "cboe canada": "CBOE CA", "cboe ca": "CBOE CA",
          "cboe ca exchange": "CBOE CA", "neo": "CBOE CA", "neo exchange": "CBOE CA", "aequitas neo": "CBOE CA"}


def _get(url, timeout=30):
    last = None
    for attempt in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            r.raise_for_status()
            if not r.encoding or r.encoding.lower() == "iso-8859-1":
                r.encoding = r.apparent_encoding or "utf-8"
            return r
        except requests.RequestException as e:
            last = e
            if attempt == 0:
                time.sleep(2)
    raise last


def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _list():
    t = _get(SOURCE_URL).text
    items = re.findall(
        r'<div class="wd_date">([^<]+)</div>\s*<div class="wd_title"><a href="([^"]+)">([^<]+)</a>', t)
    out = []
    for date, link, title in items:
        m = re.search(r"(Trading Halt|Trade Resumption)\s*-\s*(\S+)\s*$", html.unescape(title))
        if m:
            out.append({"date": date.strip(), "url": link, "kind": m.group(1), "symbol": m.group(2)})
    return out


def _detail(url):
    t = _get(url).text
    i = t.find("/CNW/")
    body = _clean(t[i:i + 6000] if i >= 0 else t)
    body = body.split("CIRO can make a decision")[0]
    rows = []
    venue_re = (r"(TSX-Venture|TSX Venture|TSXV|TSX|CSE|Cboe CA Exchange|Cboe CA|Cboe Canada|NEO Exchange|"
                r"Aequitas NEO|NEO|[A-Za-z\-]+)")
    for m in re.finditer(r"Company:\s*(.+?)\s+" + venue_re + r"\s+Symbol\s*:\s*(\S+)", body, re.I):
        rows.append({"name": m.group(1).strip(), "venue_label": m.group(2).strip(), "symbol": m.group(3)})
    reason = re.search(r"Reason:\s*(.+?)\s+(?:Halt Time|All Issues|$)", body)
    htime = re.search(r"Halt Time \(ET\):\s*([0-9:]+\s*(?:AM|PM)?)", body)
    return rows, (reason.group(1).strip() if reason else None), (htime.group(1).strip() if htime else None)


def fetch():
    read_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    base = {"market": "ca", "source_url": SOURCE_URL,
            "read_by": "CIRO Halts/Resumptions bulletins (iiroc.mediaroom.com)", "read_at": read_at}
    try:
        items = _list()
    except Exception as e:
        return {**base, "read_by": "unavailable", "count": 0, "halted": [],
                "note": f"unavailable: CIRO bulletin list failed ({type(e).__name__})"}
    seen, open_halts = set(), []
    for it in items:  # newest first: first bulletin per symbol is its latest state
        if it["symbol"] in seen:
            continue
        seen.add(it["symbol"])
        if it["kind"] == "Trading Halt":
            open_halts.append(it)
    halted = []
    for n, it in enumerate(open_halts):
        name = exch = reason = htime = None
        if n < DETAIL_CAP:
            try:
                time.sleep(0.5)
                rows, reason, htime = _detail(it["url"])
                hit = next((r for r in rows if r["symbol"].upper() == it["symbol"].upper()), rows[0] if rows else None)
                if hit:
                    name = hit["name"]
                    exch = VENUES.get(hit["venue_label"].lower(), hit["venue_label"])
            except Exception:
                pass
        since = it["date"] + (f" {htime} ET" if htime else "")
        halted.append({"ticker": it["symbol"], "isin": None, "exchange": exch, "name": name,
                       "since": since, "reason": reason, "page": it["url"]})
    window = f"{items[-1]['date']} .. {items[0]['date']}" if items else None
    return {**base, "count": len(halted), "halted": halted,
            "window": {"bulletins_read": len(items), "dates": window,
                       "note": "halts whose bulletin is older than this window are not seen"},
            "ciro_page": CIRO_PAGE}


def _save(res):
    d = os.path.join(HERE, "samples")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{res['market']}-{res['read_at'][:10]}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    return p


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    res = fetch()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print("saved:", _save(res), file=sys.stderr)
