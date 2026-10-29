"""halt_de - Germany (Xetra / Boerse Frankfurt) trading suspensions, read from
Deutsche Boerse's own "MiFID II Trading Suspensions" publication.

Frankfurter Wertpapierboerse (FWB) publishes every MiFID II Art. 32 action
(suspension / lifting of a suspension / removal) for XETR and XFRA at
https://www.cashmarket.deutsche-boerse.com/cash-en/Stay-Informed/current-regulatory-topics/mifid-ii-releases
The list is server-rendered HTML (50 events per page, newest first); each event has a
detail page carrying venue, reason, effective-from and an "Ongoing" flag.

Method: read PAGES list pages (one request each). An ISIN is "currently suspended" when
its most recent event in that window is a suspension. Each open one's detail page is read
(capped) and kept only if the source still says Ongoing: true. Suspensions older than the
window are not seen (see README). Stdlib + requests only; max 2 attempts per request.
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
HOST = "https://www.cashmarket.deutsche-boerse.com"
SOURCE_URL = HOST + "/cash-en/Stay-Informed/current-regulatory-topics/mifid-ii-releases/4086638!suspension-list"
PAGES = 4          # 4 x 50 = 200 most recent events (roughly 3-5 trading days)
DETAIL_CAP = 60
HERE = os.path.dirname(os.path.abspath(__file__))


def _get(url, timeout=40):
    last = None
    for attempt in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            r.raise_for_status()
            try:
                r.content.decode("utf-8")
                r.encoding = "utf-8"
            except UnicodeDecodeError:
                r.encoding = "cp1252"
            return r
        except requests.RequestException as e:
            last = e
            if attempt == 0:
                time.sleep(2)
    raise last


def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


ITEM_RE = re.compile(
    r'<a class="teasable-search-result-link[^"]*" href="([^"]*suspension-view\?[^"]+)">.*?'
    r'search-result-tagline">([^<]*)</h2>.*?'
    r'<h1 class="search-result-description">([^<]*)</h1>.*?'
    r'mifid-desc[^"]*">([^<]*)</p>', re.S)


def _page(n):
    url = f"{SOURCE_URL}?hitsPerPage=50" + (f"&pageNum={n}" if n else "")
    t = _get(url).text
    out = []
    for href, action, name, ident in ITEM_RE.findall(t):
        href = html.unescape(href)
        ts = re.search(r"ts=(\d+)", href)
        out.append({"url": HOST + href, "action": action.strip().lower(), "name": html.unescape(name).strip(),
                    "isin": ident.strip() or None, "ts": int(ts.group(1)) if ts else 0})
    return out


def _field(body, label, nxt):
    m = re.search(re.escape(label) + r":\s*(.*?)\s*(?:" + nxt + r"):", body)
    v = m.group(1).strip() if m else ""
    return v or None


def _detail(url):
    body = _clean(_get(url).text)
    i = body.find("Date and time of the communication")
    body = body[i:i + 3000] if i >= 0 else body
    return {
        "action": _field(body, "Action type", "Reasons for the action"),
        "reason": _field(body, "Reasons for the action", "Effective from"),
        "from": _field(body, "Effective from", "Effective to"),
        "ongoing": (_field(body, "Ongoing", "Trading venue\\(s\\)") or "").lower() == "true",
        "venues": _field(body, "Trading venue(s)", "Issuer name"),
        "issuer": _field(body, "Issuer name", "Issuer"),
        "full_name": _field(body, "Instrument full name", "Sufficiently related derivatives"),
    }


def fetch():
    read_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    base = {"market": "de", "source_url": SOURCE_URL,
            "read_by": "Deutsche Boerse / FWB MiFID II Trading Suspensions (XETR, XFRA)", "read_at": read_at}
    events, notes = [], []
    for n in range(PAGES):
        try:
            if n:
                time.sleep(0.5)
            events += _page(n)
        except Exception as e:
            notes.append(f"list page {n} failed ({type(e).__name__})")
            if n == 0:
                return {**base, "read_by": "unavailable", "count": 0, "halted": [],
                        "note": "unavailable: " + "; ".join(notes)}
    events.sort(key=lambda e: e["ts"], reverse=True)
    latest = {}
    for e in events:  # newest first
        key = e["isin"] or e["name"]
        latest.setdefault(key, e)
    open_ = [e for e in latest.values() if e["action"] == "suspension"]
    open_.sort(key=lambda e: e["ts"], reverse=True)
    halted = []
    for k, e in enumerate(open_):
        d = None
        if k < DETAIL_CAP:
            try:
                time.sleep(0.4)
                d = _detail(e["url"])
            except Exception:
                d = None
        if d and not d["ongoing"]:
            continue  # source says this suspension is no longer ongoing
        since = (d and d["from"]) or (datetime.fromtimestamp(e["ts"] / 1000, timezone.utc)
                                      .replace(microsecond=0).isoformat().replace("+00:00", "Z") + " (communication time)"
                                      if e["ts"] else None)
        halted.append({"ticker": None,  # source carries ISIN, not exchange ticker
                       "isin": e["isin"], "exchange": (d and d["venues"]) or None,
                       "name": e["name"], "since": since, "reason": (d and d["reason"]) or None,
                       "page": e["url"], **({"issuer": d["issuer"]} if d and d["issuer"] else {})})
    first = datetime.fromtimestamp(events[-1]["ts"] / 1000, timezone.utc).isoformat()[:16] if events else None
    last = datetime.fromtimestamp(events[0]["ts"] / 1000, timezone.utc).isoformat()[:16] if events else None
    res = {**base, "count": len(halted), "halted": halted,
           "window": {"events_read": len(events), "utc": f"{first} .. {last}",
                      "detail_checked": min(len(open_), DETAIL_CAP),
                      "note": "suspensions announced before this window are not seen"}}
    if notes:
        res["note"] = "; ".join(notes)
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
