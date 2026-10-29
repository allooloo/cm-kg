"""Switzerland trading suspensions reader: SIX Swiss Exchange + BX Swiss.

SIX Swiss Exchange: neither SIX nor SIX Exchange Regulation publishes a
"currently suspended" list. What they publish is the Official Notices feed
(www.ser-ag.com / www.six-group.com "Official notices"), whose search calls
/sheldon/official_notices/v2/find.json. SIX posts a "Suspension: <name> /
<symbol> / <ISIN>" notice when it suspends a security and a matching
"Resumption: ..." notice when trading restarts; fund sponsors post
"Suspendierung des Handels ..." / "Auflösung der Suspendierung ..." and
"Sistierung des Handels ...". This reader takes the manual + delisting notices
of the last LOOKBACK_DAYS in ONE request, keeps suspension notices, and drops
every ISIN that a later resumption or delisting notice names. Notice details
(/v2/details/<id>.json) are read only where the list row lacks the ISINs.

BX Swiss: www.bxswiss.com/suspensions answers JSON
{"PagedInstruments":{"Suspensions":[...],"EmptyText":...}} - the live list
behind the site's "Suspensions" page. Outside trading hours it is empty with
EmptyText "The market is closed.".
Python 3.12, stdlib + requests.
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai"
MARKET = "ch"
LOOKBACK_DAYS = 400
SER = "https://www.ser-ag.com"
FIND = SER + "/sheldon/official_notices/v2/find.json"
DETAIL = SER + "/sheldon/official_notices/v2/details/{}.json"
NOTICES_PAGE = SER + "/en/resources/notifications-market-participants/official-notices.html"
BX_URL = "https://www.bxswiss.com/suspensions"
BX_PAGE = "https://www.bxswiss.com/suspensions"
MAX_DETAILS = 40
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

ISIN_RE = re.compile(r"\b([A-Z]{2}[A-Z0-9]{9}[0-9])\b")
SUSP_RE = re.compile(r"^\s*Suspension\s*:|Suspendierung des Handels|Sistierung des Handels", re.I)
RESUME_RE = re.compile(r"^\s*Resumption\b|Auflösung der Suspendierung|Wiederaufnahme des Handels|"
                       r"Entsistierung", re.I)
END_RE = re.compile(r"Dekotierung|Delisting|Streichung|Einstellung des Handels", re.I)
NOT_HALT_RE = re.compile(r"Auflösung der Suspendierung|second trading line", re.I)


def _get(url, params=None, accept="application/json"):
    last = None
    for _ in range(2):
        try:
            r = requests.get(url, params=params, timeout=90,
                             headers={"User-Agent": UA, "Accept": accept})
            r.raise_for_status()
            r.encoding = "utf-8"
            return r
        except requests.RequestException as e:
            last = e
    raise last


def _isins(s):
    return ISIN_RE.findall(s or "")


def _detail(nid, budget):
    if budget[0] <= 0:
        return None
    budget[0] -= 1
    try:
        return _get(DETAIL.format(nid)).json()["itemList"][0]
    except Exception:
        return None


def _rows_from_text(text):
    """ISIN -> (name, symbol) from the pipe tables in a notice text."""
    out, sym_col = {}, None
    for line in (text or "").splitlines():
        cells = [c.strip() for c in line.split("|")]
        isin = next((c for c in cells if ISIN_RE.fullmatch(c or "")), None)
        if not isin:
            if "ISIN" in cells:  # header row: find the Symbol column if the table has one
                sym_col = next((k for k, c in enumerate(cells) if c.lower() == "symbol"), None)
            continue
        name = cells[0] or None
        sym = cells[sym_col] or None if sym_col is not None and sym_col < len(cells) else None
        out[isin] = (name, sym)
    return out


def _since(n):
    d, t = str(n.get("date") or ""), str(n.get("publishTime") or "").zfill(6)
    if len(d) != 8:
        return None
    return f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:{t[4:]} (Swiss local time)"


def _six(out):
    today = datetime.now(timezone.utc).date()
    params = {"firstDate": (today - timedelta(days=LOOKBACK_DAYS)).strftime("%Y%m%d"),
              "lastDate": today.strftime("%Y%m%d"), "pageNumber": 0, "pageSize": 20000,
              "sortAttribute": "date", "sortDirection": "asc",
              "showAutomatic": "false", "showManual": "true", "showExDividend": "false",
              "showProvisional": "false", "showFirstListing": "false", "showDelisting": "true"}
    items = _get(FIND, params=params).json()["itemList"]
    items.sort(key=lambda n: (n.get("date") or 0, n.get("publishTime") or 0))
    budget = [MAX_DETAILS]
    open_ = {}  # isin -> item dict
    pending_no_isin = []
    for n in items:
        title = n.get("title") or ""
        isins = _isins(n.get("isin")) or _isins(title)
        is_resume = bool(RESUME_RE.search(title))
        if is_resume or (END_RE.search(title) and not SUSP_RE.search(title)):
            if not isins and open_ and is_resume:  # delisting notices: list-row ISINs only
                det = _detail(n["noticeId"], budget)
                isins = _isins(det.get("text")) if det else []
            for i in isins:
                open_.pop(i, None)
            continue
        if not SUSP_RE.search(title) or NOT_HALT_RE.search(title):
            continue
        rows = {}
        parts = [p.strip() for p in title.split(":", 1)[-1].split("/")]
        if len(parts) == 3 and ISIN_RE.fullmatch(parts[2]):
            rows[parts[2]] = (parts[0] or None, parts[1] or None)
        if not isins or not rows:
            det = _detail(n["noticeId"], budget)
            if det:
                rows.update({k: v for k, v in _rows_from_text(det.get("text")).items() if k not in rows})
                isins = isins or list(rows) or _isins(det.get("text"))
        if not isins:
            pending_no_isin.append(n)
            continue
        for i in isins:
            name, sym = rows.get(i, (None, None))
            open_[i] = {"ticker": sym, "isin": i, "exchange": "XSWX",
                        "name": name or n.get("contact"), "since": _since(n), "reason": title,
                        "notice_id": n["noticeId"], "page": DETAIL.format(n["noticeId"])}
    for n in pending_no_isin:  # suspension notice with no ISIN anywhere we could read
        out["halted"].append({"ticker": None, "isin": None, "exchange": "XSWX",
                              "name": n.get("contact"), "since": _since(n), "reason": n.get("title"),
                              "notice_id": n["noticeId"], "page": DETAIL.format(n["noticeId"])})
    out["halted"].extend(open_.values())
    out["six_notices_read"] = len(items)
    out["six_detail_reads"] = MAX_DETAILS - budget[0]


def _pick(d, *keys):
    low = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = low.get(k.lower())
        if v not in (None, "", "-"):
            return v if isinstance(v, str) else str(v)
    return None


def _bx(out):
    data = _get(BX_URL, accept="application/json, text/javascript, */*").json()
    pi = data.get("PagedInstruments") or {}
    rows = pi.get("Suspensions") or []
    out["bx_empty_text"] = pi.get("EmptyText") if not rows else None
    for r in rows:
        if not isinstance(r, dict):
            continue
        out["halted"].append({
            "ticker": _pick(r, "Symbol", "Ticker", "ValorSymbol"),
            "isin": _pick(r, "Isin", "ISIN"),
            "exchange": "XBRN",
            "name": _pick(r, "Name", "InstrumentName", "ShortName", "Description"),
            "since": _pick(r, "Since", "SuspendedSince", "Time", "Date", "Timestamp", "DateTime"),
            "reason": _pick(r, "Reason", "Remark", "Status", "Type"),
            "page": BX_PAGE,
            "raw": r,
        })


def fetch():
    read_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"market": MARKET, "source_url": FIND + " ; " + BX_URL,
           "read_by": "SIX Official Notices (suspension/resumption pairing) + BX Swiss live suspensions",
           "read_at": read_at, "count": 0, "halted": []}
    notes = []
    try:
        _six(out)
    except Exception as e:
        notes.append(f"SIX notices unavailable: {type(e).__name__}")
    try:
        _bx(out)
    except Exception as e:
        notes.append(f"BX Swiss unavailable: {type(e).__name__}")
    out["count"] = len(out["halted"])
    notes.append(f"SIX: suspensions announced by notice in the last {LOOKBACK_DAYS} days with no later "
                 "resumption/delisting notice for the same ISIN; regulatory suspensions announced only "
                 "by SER media release are not covered. BX Swiss: live list, empty when market closed.")
    out["note"] = " | ".join(notes)
    return out


if __name__ == "__main__":
    res = fetch()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{MARKET}-{res['read_at'][:10]}.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
