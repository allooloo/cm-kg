"""KRX short code -> ISIN (standard code) for every listed stock on KOSPI, KOSDAQ, KONEX.

Source: KRX Data Marketplace (data.krx.co.kr) stock finder, bld dbms/comm/finder/finder_stkisu,
the same list the site's issue-search popup uses. It answers without login.
(MDCSTAT01901 "전종목 기본정보" and the CSV OTP download answer "LOGOUT" without a member session.)
Every ISIN is read from KRX's full_code field; none is constructed.
"""
import datetime as dt
import json
import os
import sys

import requests

URL = "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
FORM = {"bld": "dbms/comm/finder/finder_stkisu", "locale": "ko_KR", "mktsel": "ALL",
        "searchText": "", "typeNo": "0"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Allooloo Technologies Corp. developers@allooloo.ai)",
           "Referer": "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020201"}
MARKETS = {"STK": "KOSPI", "KSQ": "KOSDAQ", "KNX": "KONEX"}


def fetch():
    r = requests.post(URL, data=FORM, headers=HEADERS, timeout=60)
    r.raise_for_status()
    if r.text.strip() == "LOGOUT":
        raise RuntimeError("KRX answered LOGOUT (member session required)")
    rows = []
    for x in r.json()["block1"]:
        seg = x.get("marketEngName") or ""
        rows.append({
            "code": x["short_code"],
            "isin": x["full_code"],
            "name_ko": x["codeName"],
            "name_en": None,  # finder gives Korean names only
            "market": MARKETS.get(x["marketCode"], seg),
            "segment": seg,  # e.g. "KOSDAQ GLOBAL"
            "class": None,  # share class not given by this endpoint
        })
    rows.sort(key=lambda r: r["code"])
    return {"source_url": URL + "  [POST bld=" + FORM["bld"] + ", mktsel=ALL]",
            "read_by": "Allooloo Technologies Corp. kr_isin.py",
            "read_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "count": len(rows), "rows": rows}


if __name__ == "__main__":
    out = fetch()
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"kr-{dt.date.today().isoformat()}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    sys.stdout.reconfigure(encoding="utf-8")
    print(out["count"], "rows ->", p)
    by = {r["code"]: r for r in out["rows"]}
    for c in ("005930", "000660", "035720"):
        print(by.get(c))
