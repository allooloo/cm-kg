"""HKEX suspended / halted securities reader (Main Board + GEM).

Source: HKEX Daily Quotations (end-of-day, plain text in <pre>), where each
security whose trading is suspended or halted is printed with
"TRADING SUSPENDED" / "TRADING HALTED" in place of prices:
  index : https://www.hkex.com.hk/eng/stat/smstat/dayquot/qtn.asp  (finds latest date)
  Main  : https://www.hkex.com.hk/eng/stat/smstat/dayquot/dYYMMDDe.htm
  GEM   : https://www.hkex.com.hk/eng/stat/smstat/dayquot/gem/e_GYYMMDD.htm
The Main Board file is ~28 MB; it is streamed and the read stops at the end of
the QUOTATIONS section. Covers every listed security in the quotations,
including structured products (CBBCs / warrants), not only shares.
Python 3.12, stdlib + requests.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from html import unescape

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai"
BASE = "https://www.hkex.com.hk/eng/stat/smstat/dayquot/"
INDEX_URL = BASE + "qtn.asp"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
LINE = re.compile(r"^ *(\d{1,5})(.*?)\s+([A-Z]{3}) TRADING (SUSPENDED|HALTED)\s*$")
DATE = re.compile(r"DATE:\s*(\d{1,2} [A-Z]{3} \d{4})")


def _get(url, stream=False):
    last = None
    for _ in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=120, stream=stream)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
    raise last


def _read_quotations(url):
    """Stream a daily-quotation file; return (sheet date, [(code, name, status)])."""
    r = _get(url, stream=True)
    rows, sheet_date, in_quot = [], None, False
    try:
        for raw in r.iter_lines(decode_unicode=False):
            line = unescape(raw.decode("iso-8859-1", "replace"))
            if sheet_date is None:
                m = DATE.search(line)
                if m:
                    sheet_date = m.group(1)
            if 'name = "quotations"' in line:
                in_quot = True
                continue
            if 'name = "sales_all"' in line:
                break
            if in_quot:
                m = LINE.match(line)
                if m:
                    rows.append((m.group(1), m.group(2).strip(), m.group(4)))
    finally:
        r.close()
    return sheet_date, rows


def fetch():
    read_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"market": "hk", "source_url": INDEX_URL,
           "read_by": "HKEX Daily Quotations (Main Board + GEM), TRADING SUSPENDED/HALTED rows",
           "read_at": read_at, "count": 0, "halted": []}
    try:
        idx = _get(INDEX_URL).text
        days = sorted(set(re.findall(r"d(\d{6})e\.htm", idx)))
        if not days:
            raise ValueError("no daily quotation links on index")
        ymd = days[-1]
    except Exception as e:
        out["note"] = f"unavailable: {type(e).__name__}: {e}"
        return out
    lists = [("SEHK Main Board", f"{BASE}d{ymd}e.htm"),
             ("SEHK GEM", f"{BASE}gem/e_G{ymd}.htm")]
    out["source_url"] = lists[0][1]
    out["source_urls"] = [u for _, u in lists]
    notes = []
    for venue, url in lists:
        try:
            sheet_date, rows = _read_quotations(url)
        except Exception as e:
            notes.append(f"{venue} unavailable: {type(e).__name__}")
            continue
        for code, name, status in rows:
            out["halted"].append({
                "ticker": code.zfill(5),
                "isin": None,  # daily quotations carry no ISIN
                "exchange": venue,
                "name": name,
                "since": None,  # the sheet shows status on its date, not the start date
                "reason": f"TRADING {status} (as at {sheet_date})" if sheet_date else f"TRADING {status}",
                "page": url,
            })
    out["count"] = len(out["halted"])
    out["sheet_date"] = ymd
    if notes:
        out["note"] = "; ".join(notes)
    return out


def main():
    res = fetch()
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"hk-{datetime.now(timezone.utc):%Y-%m-%d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
