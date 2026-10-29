"""Australia trading halts / suspensions reader: ASX + NSX.

ASX: ASX publishes no machine-readable "currently halted" list. It does tag
every company announcement with a type, and halts/suspensions are themselves
announcements ("Trading Halt", "Suspension from Official Quotation", "Trading
Halt Lifted", "Reinstatement to Official Quotation"). The market announcements
feed behind www.asx.com.au (ASX research API, asx.api.markitdigital.com/
asx-research/1.0/markets/announcements, operated for ASX by Markit Digital)
is read in ONE request of the latest ASX_ITEMS announcements (about 3-4 weeks),
and per symbol the latest status-type announcement decides:
  Trading Halt -> halted;  Suspension from Official Quotation -> suspended;
  Trading Halt Lifted / Reinstatement to Official Quotation -> cleared.
A trading halt can last at most two trading days (ASX Operating Rule 16.4.2,
Listing Rule 17.1), so a halt whose announcement is older than that with no
later status announcement is dropped and counted in "asx_stale_halts_dropped".

NSX: www.nsx.com.au/marketdata/delisted-suspended/ is the exchange's own HTML
list of currently suspended securities (Code, Security Name, Suspended Date).
Python 3.12, stdlib + requests.
"""
import html
import json
import os
import re
from datetime import date, datetime, timedelta, timezone

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai"
MARKET = "au"
ASX_ITEMS = 10000
ASX_URL = "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements"
ASX_CO_PAGE = "https://www.asx.com.au/markets/trade-our-cash-market/announcements.{}"
NSX_URL = "https://www.nsx.com.au/marketdata/delisted-suspended/"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

HALT, SUSP = "Trading Halt", "Suspension from Official Quotation"
CLEAR = {"Trading Halt Lifted", "Reinstatement to Official Quotation"}


def _get(url, params=None, accept="application/json"):
    last = None
    for _ in range(2):
        try:
            r = requests.get(url, params=params, timeout=120,
                             headers={"User-Agent": UA, "Accept": accept,
                                      "Referer": "https://www.asx.com.au/"})
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
    raise last


def _trading_days_back(d, n):
    """Date n weekdays before d (ASX public holidays not modelled: errs toward keeping)."""
    while n > 0:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def _asx(out):
    items = _get(ASX_URL, params={"itemsPerPage": ASX_ITEMS, "page": 0}).json()["data"]["items"]
    items.sort(key=lambda a: a.get("date") or "")
    state = {}
    for a in items:
        types = set(a.get("announcementTypes") or [])
        sym = a.get("symbol")
        if not sym:
            continue
        if types & CLEAR:
            state.pop(sym, None)
        if SUSP in types:
            state[sym] = (SUSP, a)
        elif HALT in types:
            state[sym] = (HALT, a)
    # halt cut-off: announcements dated (Sydney) on/after 2 trading days before today
    syd_today = (datetime.now(timezone.utc) + timedelta(hours=10)).date()
    cutoff = _trading_days_back(syd_today, 2)
    stale = 0
    for sym, (kind, a) in sorted(state.items()):
        ts = a.get("date")
        if kind == HALT and ts:
            local = (datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=10)).date()
            if local < cutoff:
                stale += 1
                continue
        info = next((c for c in a.get("companyInfo") or [] if c.get("symbol") == sym), {})
        # a headline such as "CBAPJ - Hybrid Security Suspension" names the affected line
        # (issuer code + suffix); then that code is the ticker, as printed by ASX.
        m = re.search(r"\b(" + re.escape(sym) + r"[A-Z0-9]{1,3})\b", a.get("headline") or "")
        ticker = m.group(1) if m else sym
        out["halted"].append({
            "ticker": ticker, "issuer_symbol": sym,
            "isin": info.get("isin") if ticker == sym else None, "exchange": "XASX",
            "name": info.get("displayName"), "since": ts, "reason": kind,
            "headline": a.get("headline"), "document_key": a.get("documentKey"),
            "page": ASX_CO_PAGE.format(sym.lower()),
        })
    out["asx_announcements_read"] = len(items)
    out["asx_window_from"] = items[0].get("date") if items else None
    out["asx_stale_halts_dropped"] = stale


def _nsx(out):
    h = _get(NSX_URL, accept="text/html").text
    m = re.search(r'<table id="myTable"[^>]*>(.*?)</table>', h, re.S)
    if not m:
        raise ValueError("NSX suspended table not found")
    for tr in re.findall(r"<tr>(.*?)</tr>", m.group(1), re.S):
        tds = re.findall(r"<td>(.*?)</td>", tr, re.S)
        if len(tds) < 3:
            continue
        code = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", tds[0])).split()) or None
        name = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", tds[1])).split()) or None
        since = " ".join(re.sub(r"<span[^>]*>.*?</span>", "", tds[2], flags=re.S).split()) or None
        href = re.search(r'href="([^"]+)"', tds[1])
        out["halted"].append({
            "ticker": code, "isin": None, "exchange": "XNEC", "name": name, "since": since,
            "reason": "Suspended (NSX suspended listings)",
            "page": ("https://www.nsx.com.au" + href.group(1)) if href else NSX_URL,
        })


def fetch():
    read_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"market": MARKET, "source_url": ASX_URL + " ; " + NSX_URL,
           "read_by": "ASX announcements feed (halt/suspension announcement types) + NSX suspended listings",
           "read_at": read_at, "count": 0, "halted": []}
    notes = []
    try:
        _asx(out)
    except Exception as e:
        notes.append(f"ASX unavailable: {type(e).__name__}")
    try:
        _nsx(out)
    except Exception as e:
        notes.append(f"NSX unavailable: {type(e).__name__}")
    out["count"] = len(out["halted"])
    notes.append("ASX: derived from halt/suspension announcements in the window read; suspensions "
                 "that began before asx_window_from are not seen. NSX: exchange list as published.")
    out["note"] = " | ".join(notes)
    return out


if __name__ == "__main__":
    res = fetch()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{MARKET}-{res['read_at'][:10]}.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
