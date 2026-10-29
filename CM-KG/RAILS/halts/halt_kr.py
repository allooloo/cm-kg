"""KRX trading-halt reader (KOSPI, KOSDAQ, KONEX) from KRX KIND.

Source: KIND 매매거래정지종목 (trading-halt issues),
https://kind.krx.co.kr/investwarn/tradinghaltissue.do?method=searchTradingHaltIssueMain .
The on-screen list (forward=tradinghaltissue_sub) omits the 6-digit code, so
this reader posts the page's own "download" form (forward=tradinghaltissue_down),
which returns the same list as an Excel-HTML table with 종목코드. One POST per
market segment (유가증권=1 KOSPI, 코스닥=2 KOSDAQ, 코넥스=6 KONEX) so each row
carries its venue from the source. KIND rejects the POST without a Referer.
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
PAGE_URL = "https://kind.krx.co.kr/investwarn/tradinghaltissue.do?method=searchTradingHaltIssueMain"
POST_URL = "https://kind.krx.co.kr/investwarn/tradinghaltissue.do"
SEGMENTS = [("1", "KOSPI"), ("2", "KOSDAQ"), ("6", "KONEX")]
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

ROW = re.compile(r"<tr>\s*<td[^>]*>\s*(\d+)\s*</td>\s*<td[^>]*>(.*?)</td>\s*"
                 r"<td[^>]*>\s*(.*?)\s*</td>\s*<td[^>]*>(.*?)</td>\s*</tr>", re.S)


def _post(market_type):
    form = {"method": "searchTradingHaltIssueSub", "currentPageSize": "3000", "pageIndex": "1",
            "searchMode": "", "searchCodeType": "", "searchCorpName": "",
            "forward": "tradinghaltissue_down", "paxreq": "", "outsvcno": "",
            "marketType": market_type, "repIsuSrtCd": ""}
    last = None
    for _ in range(2):
        try:
            r = requests.post(POST_URL, data=form, timeout=60,
                              headers={"User-Agent": UA, "Referer": PAGE_URL})
            r.raise_for_status()
            text = r.content.decode("euc-kr", "replace")
            if "종목코드" not in text:
                raise requests.RequestException("KIND returned an error page")
            return text
        except requests.RequestException as e:
            last = e
    raise last


def _clean(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def fetch():
    read_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"market": "kr", "source_url": PAGE_URL,
           "read_by": "KRX KIND 매매거래정지종목 (trading-halt issues, Excel download form)",
           "read_at": read_at, "count": 0, "halted": []}
    notes = []
    for mtype, venue in SEGMENTS:
        try:
            text = _post(mtype)
        except Exception as e:
            notes.append(f"{venue} unavailable: {type(e).__name__}")
            continue
        for _, name, code, reason in ROW.findall(text):
            code = _clean(code)
            out["halted"].append({
                "ticker": code if re.fullmatch(r"[0-9A-Z]{6}", code) else None,
                "isin": None,  # KIND list carries no ISIN
                "exchange": venue,
                "name": _clean(name),
                "since": None,  # list carries no halt start date
                "reason": _clean(reason) or None,
                "page": PAGE_URL,
            })
    out["count"] = len(out["halted"])
    if notes:
        out["note"] = "; ".join(notes)
    return out


def main():
    res = fetch()
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"kr-{datetime.now(timezone.utc):%Y-%m-%d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
