"""halt_uk - United Kingdom suspended securities, read from the FCA's Official List.

The FCA (UK Listing Authority) publishes the Official List at
https://marketsecurities.fca.org.uk/officiallist with a Status column (Live / Suspended)
for every listed security, its trading venue (LSE, Aquis, Cboe, ...), market status
(RM / MTF) and ISIN. The page is a Salesforce Visualforce form: the full list is reached
letter by letter (0-9, A..Z) and page by page via the page's own AJAX POST. This reader
walks it sequentially (one request per letter page) and keeps rows with Status = Suspended.

Not covered: AIM and Aquis Growth Market (not on the Official List) - see README.
Stdlib + requests only; max 2 attempts per request.
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
HOST = "https://marketsecurities.fca.org.uk"
SOURCE_URL = HOST + "/officiallist"
F = "mainPage:SiteTemplatePage:theform"
LETTERS = ["0-9"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
PAUSE = 0.5
HERE = os.path.dirname(os.path.abspath(__file__))
COLS = {"j_id79": "name", "j_id82": "country", "j_id85": "description", "j_id88": "category",
        "j_id91": "market_status", "j_id94": "venue", "j_id100": "isin", "j_id103": "status"}


def _req(s, method, url, **kw):
    last = None
    for attempt in range(2):
        try:
            r = s.request(method, url, timeout=90, **kw)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except requests.RequestException as e:
            last = e
            if attempt == 0:
                time.sleep(3)
    raise last


def _hidden(t):
    d = {}
    for name in ("com.salesforce.visualforce.ViewState", "com.salesforce.visualforce.ViewStateVersion",
                 "com.salesforce.visualforce.ViewStateMAC", "com.salesforce.visualforce.ViewStateCSRF"):
        m = re.search(r'name="%s" value="([^"]*)"' % re.escape(name), t)
        if m:
            d[name] = m.group(1)
    return d


def _rows(t):
    rows = {}
    for idx, col, val in re.findall(r'tableData:(\d+):(j_id\d+)"[^>]*>(?:<span[^>]*>)?([^<]*)', t):
        if col in COLS:
            rows.setdefault(int(idx), {})[COLS[col]] = html.unescape(val).strip()
    return [rows[k] for k in sorted(rows)]


def _pages(t):
    return sorted({int(p) for p in re.findall(r"RecordToShowForSelectedPage\('(\d+)'\)", t)}) or [1]


def fetch():
    read_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    base = {"market": "uk", "source_url": SOURCE_URL, "read_by": "FCA Official List (marketsecurities.fca.org.uk)",
            "read_at": read_at}
    s = requests.Session()
    s.headers["User-Agent"] = UA
    try:
        t = _req(s, "GET", SOURCE_URL)
        action = HOST + re.search(r'action="(/[^"]*)"', t[t.find('id="%s"' % F):]).group(1)
    except Exception as e:
        return {**base, "read_by": "unavailable", "count": 0, "halted": [],
                "note": f"unavailable: FCA Official List did not answer ({type(e).__name__})"}
    state = _hidden(t)
    all_rows, failed, requests_made = 0, [], 1
    suspended = []
    common = {"AJAXREQUEST": "_viewRoot", F: F, F + ":j_id53:j_id54:searchName": ""}
    for letter in LETTERS:
        try:
            time.sleep(PAUSE)
            t = _req(s, "POST", action, data={**common, **state, "searchtext": letter, F + ":j_id27": F + ":j_id27"})
            requests_made += 1
            state = _hidden(t) or state
            batch = _rows(t)
            for p in _pages(t)[1:]:
                time.sleep(PAUSE)
                t = _req(s, "POST", action, data={**common, **state, "selectedPage": str(p), F + ":j_id29": F + ":j_id29"})
                requests_made += 1
                state = _hidden(t) or state
                batch += _rows(t)
        except Exception as e:
            failed.append(f"{letter} ({type(e).__name__})")
            continue
        all_rows += len(batch)
        suspended += [r for r in batch if r.get("status", "").lower() == "suspended"]
    halted = [{"ticker": None,  # Official List carries no exchange ticker
               "isin": r.get("isin") or None, "exchange": r.get("venue") or None,
               "name": r.get("name") or None, "since": None,  # not published on the list
               "reason": None,  # not published on the list
               "page": SOURCE_URL,
               "security": r.get("description") or None, "category": r.get("category") or None,
               "market_status": r.get("market_status") or None} for r in suspended]
    res = {**base, "count": len(halted), "halted": halted,
           "coverage": {"rows_read": all_rows, "requests": requests_made, "letters_failed": failed,
                        "scope": "Official List securities (Main Market and other UK venues); AIM / Aquis Growth Market not included"}}
    if failed:
        res["note"] = "partial: some letters failed - " + ", ".join(failed)
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
