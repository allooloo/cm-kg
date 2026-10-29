"""Texas Stock Exchange (TXSE) roster: TXSE-listed securities + traded-only symbols.

Sources, all TXSE's own:
  1. https://www.txse.com/api/all-listings-products  JSON behind www.txse.com/all-listings
     ("All corporate securities and ETPs listed on TXSE").
  2. https://www.txse.com/listings-calendar  the page's embedded rows carry listingCategory /
     listingKind (Transfer, New Listing, Dual Listing, Conversion) per symbol.
  3. https://download.web.txse.com/public_symbols.txt  daily symbol file (linked from
     www.txse.com/symbols): SymbolRoot|SymbolSuffix|SymbolID|StreamID|LotSize|IsTest|ETF|TXSEListed.
TXSE publishes no ISIN or CUSIP on any of these, so isin/cusip stay null.
"""
import datetime as dt
import json
import os
import re

import requests

LISTINGS = "https://www.txse.com/api/all-listings-products"
CALENDAR = "https://www.txse.com/listings-calendar"
SYMBOLS = "https://download.web.txse.com/public_symbols.txt"
H = {"User-Agent": "Mozilla/5.0 (Allooloo Technologies Corp. developers@allooloo.ai)"}


def _get(u):
    r = requests.get(u, headers=H, timeout=60)
    r.raise_for_status()
    return r


def _key(root, suffix):
    return f"{root} {suffix}".strip() if suffix else root


def _calendar():
    t = _get(CALENDAR).text.replace('\\"', '"')
    out = {}
    for m in re.finditer(r'\{"_key":"[^"]*","_type":"listing",[^{}]*\}', t):
        try:
            o = json.loads(m.group(0).encode().decode("unicode_escape", "ignore"))
        except ValueError:
            continue
        if o.get("symbol"):
            out[o["symbol"].replace(".", " ")] = o
    return out


def fetch():
    lst = _get(LISTINGS).json()
    cal = _calendar()
    sym_lines = _get(SYMBOLS).text.splitlines()
    hdr = sym_lines[0].split("|")
    syms = [dict(zip(hdr, l.split("|"))) for l in sym_lines[1:] if l.strip()]
    flag = {_key(s["SymbolRoot"], s["SymbolSuffix"]): s for s in syms}

    rows, listed = [], set()
    for x in lst["listings"]:
        k = _key(x["symbol"], x.get("suffix"))
        listed.add(k)
        c = cal.get(k) or {}
        kind = " ".join(v for v in (c.get("listingCategory"), c.get("listingKind")) if v) or x.get("type")
        sf = flag.get(k, {})
        rows.append({"ticker": k, "name": x.get("securityName") or x.get("issuer"),
                     "issuer": x.get("issuer"), "security_type": x.get("securityType"),
                     "isin": None, "cusip": None,
                     "listing_type": f"TXSE listing ({kind})",
                     "symbol_file_TXSEListed": sf.get("TXSEListed"),
                     "first_trade_date": c.get("expectedDate")})
    for s in syms:
        k = _key(s["SymbolRoot"], s["SymbolSuffix"])
        if k in listed or s["IsTest"] == "Y":
            continue
        rows.append({"ticker": k, "name": None, "issuer": None,
                     "security_type": "etf" if s["ETF"] == "Y" else None,
                     "isin": None, "cusip": None,
                     "listing_type": "listed on TXSE (symbol file only)" if s["TXSEListed"] == "Y"
                     else "traded-only (symbol file TXSEListed=N)",
                     "symbol_file_TXSEListed": s["TXSEListed"], "first_trade_date": None})
    return {"source_url": [LISTINGS, CALENDAR, SYMBOLS],
            "read_by": "Allooloo Technologies Corp. txse_roster.py",
            "read_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "listings_as_of": lst.get("asOf"),
            "count": len(rows), "count_txse_listed": len(listed), "rows": rows}


if __name__ == "__main__":
    out = fetch()
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"txse-{dt.date.today().isoformat()}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(out["count"], "rows;", out["count_txse_listed"], "TXSE-listed ->", p)
    for r in out["rows"][:3]:
        print(r)
