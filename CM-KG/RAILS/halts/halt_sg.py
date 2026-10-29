"""SGX trading halts / suspensions reader (SGX Mainboard + Catalist).

Source: the securities prices API that www.sgx.com/securities/securities-prices
calls (api.sgx.com/securities/v1.1). Each counter carries a remarks indicator
field "i"; sgx.com's own locale file (www.sgx.com/locales/en.json,
sgx-securities-service.remarks.*) maps SUSP = Suspended, H = Trading Halt,
CIRH = Halt due to Circuit Breaker. Those three are read as halted.
Python 3.12, stdlib + requests.
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai"
SOURCE_URL = "https://api.sgx.com/securities/v1.1/"
LIST_PAGE = "https://www.sgx.com/securities/securities-prices"
HALT_CODES = {"SUSP": "Suspended", "H": "Trading Halt", "CIRH": "Halt due to Circuit Breaker"}
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def _get(url):
    last = None
    for _ in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Accept": "application/json",
                                           "Referer": "https://www.sgx.com/"}, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
    raise last


def fetch():
    read_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"market": "sg", "source_url": SOURCE_URL,
           "read_by": "SGX securities prices API (remarks indicator SUSP/H/CIRH)",
           "read_at": read_at, "count": 0, "halted": []}
    try:
        data = _get(SOURCE_URL).json()
        prices = data["data"]["prices"]
    except Exception as e:  # source unreachable or reshaped: report, never invent
        out["note"] = f"unavailable: {type(e).__name__}"
        return out
    seen = set()
    for p in prices:
        code = (p.get("i") or "").strip()
        if code not in HALT_CODES:
            continue
        nc = (p.get("nc") or "").strip() or None
        key = (nc, code)
        if key in seen:  # the API lists some counters twice (e.g. under 'stocks' and 'others')
            continue
        seen.add(key)
        board = p.get("m")
        out["halted"].append({
            "ticker": nc,
            "isin": None,  # not carried by this API
            "exchange": f"SGX {board}" if board else None,
            "name": p.get("n"),
            "since": None,  # API carries no halt/suspension start date
            "reason": f"{code} ({HALT_CODES[code]})",
            "page": LIST_PAGE,
        })
    out["count"] = len(out["halted"])
    stamps = sorted({p.get("trading_time") for p in prices if p.get("trading_time")})
    if stamps:
        out["source_as_of"] = stamps[-1]
    return out


def main():
    res = fetch()
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"sg-{datetime.now(timezone.utc):%Y-%m-%d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
