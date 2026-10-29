"""Euronext Amsterdam halted / suspended instruments reader.

Venues: Euronext Amsterdam (MIC XAMS), Euronext Growth Amsterdam (ALXA),
Euronext Amsterdam non-regulated segment (TNLA).

Source: the JSON endpoint that live.euronext.com's own "Suspended instruments"
page (/en/resources/market-events/suspended/current) calls to fill its table:
/en/ajax/haltedInstrument/getAjax/current. It lists every instrument currently
halted on all Euronext cash venues; this reader keeps the Amsterdam MICs only.
Columns, as the page labels them: Halted, mic, Issuer, LEI, Isin, Name, Code,
Grp, Type, Reason, Resumption, Resumption Reason.
Python 3.12, stdlib + requests.
"""
import html
import json
import os
import re
from datetime import datetime, timezone

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai"
MARKET = "nl"
MICS = {"XAMS": "Euronext Amsterdam", "ALXA": "Euronext Growth Amsterdam", "TNLA": "Euronext Amsterdam non-regulated (TNLA)"}
SOURCE_URL = "https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current"
LIST_PAGE = "https://live.euronext.com/en/resources/market-events/suspended/current"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def _get(url):
    last = None
    for _ in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Accept": "application/json",
                                           "Referer": LIST_PAGE}, timeout=90)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
    raise last


def _txt(cell):
    s = re.sub(r"<[^>]+>", " ", cell or "")
    s = " ".join(html.unescape(s).split())
    return None if s in ("", "-") else s


def _since(cell):
    # cell carries data-order='YYYY-MM-DDTHH:MM:SS' (UTC; the page shows the CET/CEST time)
    m = re.search(r"data-order='([^']+)'", cell or "")
    return (m.group(1) + "Z") if m else _txt(cell)


def fetch():
    read_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"market": MARKET, "source_url": SOURCE_URL,
           "read_by": "Euronext live - Suspended instruments (current), Amsterdam MICs",
           "read_at": read_at, "count": 0, "halted": []}
    try:
        rows = _get(SOURCE_URL).json()["data"]
    except Exception as e:  # unreachable or reshaped: report, never invent
        out["note"] = f"unavailable: {type(e).__name__}"
        return out
    by_type = {}
    for r in rows:
        if len(r) < 11:
            continue
        mic = _txt(r[1])
        if mic not in MICS:
            continue
        typ = _txt(r[8])
        by_type[typ] = by_type.get(typ, 0) + 1
        out["halted"].append({
            "ticker": _txt(r[6]),
            "isin": _txt(r[4]),
            "exchange": mic,
            "name": _txt(r[5]),
            "issuer": _txt(r[2]),
            "type": typ,
            "since": _since(r[0]),
            "reason": _txt(r[9]),
            "resumption": _txt(r[10]),
            "page": LIST_PAGE,
        })
    out["count"] = len(out["halted"])
    out["count_by_type"] = by_type
    out["note"] = ("All instrument types as listed (Stock, Bond, W&C = warrants/certificates, ...). "
                   "Filter on 'type' for equities. 'reason' is Euronext's text, e.g. 'Action by MO' "
                   "(market operator).")
    return out


if __name__ == "__main__":
    res = fetch()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    os.makedirs(OUT_DIR, exist_ok=True)
    day = res["read_at"][:10]
    with open(os.path.join(OUT_DIR, f"{MARKET}-{day}.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
