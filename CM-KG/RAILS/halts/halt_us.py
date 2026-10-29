"""halt_us - United States trading halts, read from Nasdaq Trader's official trade-halt RSS.

The Nasdaq Trader "Current Trading Halts" feed lists halts and pauses in all US-listed
securities (Nasdaq, NYSE, NYSE American, NYSE Arca, Cboe BZX and other listing markets),
as published by Nasdaq as the UTP SIP processor. Fallback: NYSE's own current-halts JSON.
Stdlib + requests only. No retries beyond 2 attempts per list.
"""
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai (CM-KG halts reader)"
SOURCE_URL = "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"
LIST_PAGE = "https://www.nasdaqtrader.com/trader.aspx?id=TradeHalts"
FALLBACK_URL = "https://www.nyse.com/api/trade-halts/current"
FALLBACK_PAGE = "https://www.nyse.com/trade-halt-current"
NS = {"ndaq": "http://www.nasdaqtrader.com/"}
HERE = os.path.dirname(os.path.abspath(__file__))


def _get(url, timeout=30):
    last = None
    for attempt in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
            if attempt == 0:
                time.sleep(2)
    raise last


def _txt(el, tag):
    v = el.findtext(tag, default="", namespaces=NS)
    v = (v or "").strip()
    return v or None


def _from_nasdaq():
    r = _get(SOURCE_URL)
    root = ET.fromstring(r.content)
    out = []
    for it in root.iter("item"):
        resumed = _txt(it, "ndaq:ResumptionTradeTime")
        if resumed:  # halt already lifted (trading resumed) - not current
            continue
        date, tm = _txt(it, "ndaq:HaltDate"), _txt(it, "ndaq:HaltTime")
        out.append({
            "ticker": _txt(it, "ndaq:IssueSymbol"),
            "isin": None,  # feed does not carry ISIN
            "exchange": _txt(it, "ndaq:Market"),
            "name": _txt(it, "ndaq:IssueName"),
            "since": " ".join(x for x in (date, tm) if x) + " ET" if date else None,
            "reason": _txt(it, "ndaq:ReasonCode"),
            "page": LIST_PAGE,
        })
    return SOURCE_URL, "Nasdaq Trader trade-halts RSS", out


def _from_nyse():
    r = _get(FALLBACK_URL)
    d = r.json()
    out = []
    for h in (d.get("results") or {}).get("tradeHalts") or []:
        if h.get("formatedResumptionTime"):
            continue
        date, tm = h.get("formatedHaltDate"), h.get("formatedHaltTime")
        out.append({
            "ticker": h.get("symbol") or None,
            "isin": None,
            "exchange": h.get("sourceExchange") or None,
            "name": h.get("issuerName") or None,
            "since": " ".join(x for x in (date, tm) if x) + " ET" if date else None,
            "reason": h.get("reason") or None,
            "page": FALLBACK_PAGE,
        })
    return FALLBACK_URL, "NYSE current trade halts API (fallback)", out


def fetch():
    read_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    note = None
    try:
        src, label, rows = _from_nasdaq()
    except Exception as e:  # primary failed: use NYSE's own list
        note = f"Nasdaq Trader feed failed ({type(e).__name__}); NYSE fallback used"
        try:
            src, label, rows = _from_nyse()
        except Exception as e2:
            return {"market": "us", "source_url": SOURCE_URL, "read_by": "unavailable",
                    "read_at": read_at, "count": 0, "halted": [],
                    "note": f"unavailable: Nasdaq ({type(e).__name__}) and NYSE ({type(e2).__name__}) both failed"}
    res = {"market": "us", "source_url": src, "read_by": label, "read_at": read_at,
           "count": len(rows), "halted": rows}
    if note:
        res["note"] = note
    return res


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
