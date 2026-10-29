"""JPX / Tokyo Stock Exchange trading halts reader.

Source: JPX 売買停止情報 (equities trading halts) page,
https://www.jpx.co.jp/markets/equities/suspended/index.html .
The first table on the page lists the halts in force / announced for the
current day; the second table ("過去の売買停止情報") is history and is ignored.
Rows sharing a date/time/reason use rowspan; this reader carries those cells
down to every row they span. Python 3.12, stdlib + requests.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser

import requests

UA = "Allooloo Technologies Corp. developers@allooloo.ai"
SOURCE_URL = "https://www.jpx.co.jp/markets/equities/suspended/index.html"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
HISTORY_MARK = "過去の売買停止情報"


class _Tables(HTMLParser):
    """Collect tables as lists of rows; each cell = (text, rowspan, colspan)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self._t, self._row, self._cell = [], None, None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._t = []
        elif tag == "tr" and self._t is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = {"text": "", "rs": int(a.get("rowspan") or 1),
                          "cs": int(a.get("colspan") or 1), "th": tag == "th"}

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._cell["text"] = re.sub(r"\s+", " ", self._cell["text"]).strip()
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._t.append(self._row)
            self._row = None
        elif tag == "table" and self._t is not None:
            self.tables.append(self._t)
            self._t = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data


def _grid(rows):
    """Expand rowspans for data rows (rows without <th>) into 7-column lists."""
    out, carry = [], {}  # carry: col -> [remaining, text]
    for row in rows:
        if any(c["th"] for c in row):
            continue
        vals, col, new_carry = {}, 0, {}

        def take_carried():
            nonlocal col
            while col in carry:
                vals[col] = carry[col][1]
                if carry[col][0] > 1:
                    new_carry[col] = [carry[col][0] - 1, carry[col][1]]
                col += 1

        for c in row:
            take_carried()
            for _ in range(c["cs"]):
                vals[col] = c["text"]
                if c["rs"] > 1:
                    new_carry[col] = [c["rs"] - 1, c["text"]]
                col += 1
        take_carried()
        for k, v in carry.items():  # carried cells beyond the last real cell
            if k not in vals:
                vals[k] = v[1]
                if v[0] > 1:
                    new_carry[k] = [v[0] - 1, v[1]]
        carry = new_carry
        out.append([vals.get(i) for i in range(7)])
    return out


def _get(url):
    last = None
    for _ in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
    raise last


def fetch():
    read_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"market": "jp", "source_url": SOURCE_URL,
           "read_by": "JPX 売買停止情報 (TSE equities trading halts, current table)",
           "read_at": read_at, "count": 0, "halted": []}
    try:
        html = _get(SOURCE_URL).content.decode("utf-8", "replace")
    except Exception as e:
        out["note"] = f"unavailable: {type(e).__name__}"
        return out
    cut = html.find(HISTORY_MARK)
    current = html[:cut] if cut > 0 else html
    p = _Tables()
    p.feed(current)
    halt_tables = [t for t in p.tables
                   if any("売買停止時間" in c["text"] for r in t for c in r if c["th"])]
    if not halt_tables:
        out["note"] = "no current trading-halt table found on page (layout change or none published)"
        return out
    for name, code, date, start, end, restart, reason in _grid(halt_tables[0]):
        if not name and not code:
            continue
        code = unescape(code or "").strip() or None
        since = " ".join(x for x in (date, start) if x) or None
        rsn = reason or None
        if end or restart:
            rsn = f"{reason or ''} [終了時刻: {end or '-'}; 売買再開時刻: {restart or '-'}]".strip()
        out["halted"].append({
            "ticker": code if code and re.fullmatch(r"[0-9A-Z]{4,5}", code) else None,
            "isin": None,  # page carries no ISIN
            "exchange": "TSE",
            "name": name,
            "since": since,
            "reason": rsn,
            "page": SOURCE_URL,
        })
    out["count"] = len(out["halted"])
    return out


def main():
    res = fetch()
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"jp-{datetime.now(timezone.utc):%Y-%m-%d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
