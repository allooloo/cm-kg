"""EDINET statutory filings per issuer over the window through the EDINET API v2 (AGENT KEYS\\edinet.txt): one documents.json call per calendar day
(type=2 = the full list with metadata) written to raw/edinet_daily/<date>.json — 365 calls for the year, then the per-issuer trail is cut locally
for the roster's EDINET codes (and the codes of subsidiaries filing about them stay out). Event types from docTypeCode: 120 有価証券報告書 and
140 四半期報告書 / 160 半期報告書 → results; 180 臨時報告書 → ad_hoc; 350 / 360 大量保有報告書 (and 変更) → major_holder; 030 / 040 / 050 有価証券届出書
→ prospectus; 220 自己株券買付状況報告書 → corporate_news (buy-back); 130 / 150 / 170 / 370 訂正 → regulatory_filing (amendment); 240 公開買付届出書
→ takeover; 090 / 100 ... → regulatory_filing. Titles are the docDescription in Japanese as filed (no machine translation). URL = the EDINET
viewer page for the document. Read-by: 'EDINET API v2 documents list (statutory filings per EDINET code)'. Register rows are the issuer's own
record: exempt from the name rule. Language 'ja'."""
import os, json, datetime, time
from common import *
EK = os.environ['EDINET_API_KEY']
API = 'https://api.edinet-fsa.go.jp/api/v2/documents.json'
VIEW = 'https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?'
TYPE = {'120': 'results', '130': 'regulatory_filing', '140': 'results', '150': 'regulatory_filing', '160': 'results', '170': 'regulatory_filing', '180': 'ad_hoc', '190': 'regulatory_filing', '220': 'corporate_news', '230': 'corporate_news', '240': 'takeover', '250': 'takeover', '260': 'takeover', '270': 'takeover', '350': 'major_holder', '360': 'major_holder', '370': 'major_holder', '030': 'prospectus', '040': 'prospectus', '050': 'prospectus', '060': 'prospectus', '070': 'prospectus', '080': 'prospectus', '090': 'prospectus', '100': 'prospectus', '110': 'regulatory_filing', '200': 'regulatory_filing', '210': 'regulatory_filing'}
LABEL = {'120': '有価証券報告書 (annual securities report)', '140': '四半期報告書 (quarterly report)', '160': '半期報告書 (half-year report)', '180': '臨時報告書 (extraordinary report)', '350': '大量保有報告書 (large shareholding report)', '360': '変更報告書 (change report, large shareholding)', '030': '有価証券届出書 (securities registration statement)', '220': '自己株券買付状況報告書 (share buy-back status report)', '240': '公開買付届出書 (tender offer registration)', '130': '訂正有価証券報告書 (amended annual report)', '150': '訂正四半期報告書 (amended quarterly report)', '170': '訂正半期報告書 (amended half-year report)', '370': '訂正報告書 (amended large shareholding report)'}
os.makedirs('raw/edinet_daily', exist_ok=True)
def day(d):
    fn = f'raw/edinet_daily/{d.isoformat()}.json'
    if os.path.exists(fn): return json.load(open(fn, encoding='utf-8'))
    for i in range(5):
        try:
            r = requests.get(API, params={'date': d.isoformat(), 'type': 2, 'Subscription-Key': EK}, headers=UA, timeout=120)
            if r.status_code == 200:
                j = r.json(); json.dump(j, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return j
            if r.status_code in (429, 500, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return {'metadata': {'status': str(r.status_code)}, 'results': []}
        except Exception: time.sleep(3 * (i + 1))
    return {'metadata': {'status': 'error'}, 'results': []}
def sweep():
    d = SINCE; n = 0; docs = 0
    while d <= TODAY:
        j = day(d); n += 1; docs += len(j.get('results') or [])
        if n % 30 == 0: print('edinet days', n, 'documents', docs, flush=True)
        d += datetime.timedelta(days=1)
    print('edinet sweep DONE days', n, 'documents', docs, flush=True)
issuers = load_issuers(); by_code = {}
for r in issuers:
    if r.get('reg_id'): by_code.setdefault(r['reg_id'], []).append(r)
def cut():
    per = {key(r): [] for r in issuers}; seen = set()
    for fn in sorted(os.listdir('raw/edinet_daily')):
        j = json.load(open(os.path.join('raw/edinet_daily', fn), encoding='utf-8'))
        for it in j.get('results') or []:
            ec = it.get('edinetCode') or ''; rs = by_code.get(ec)
            if not rs or it.get('docID') in seen: continue
            seen.add(it['docID']); tc = str(it.get('docTypeCode') or ''); dt = (it.get('submitDateTime') or '')[:10]
            if not in_window(dt): continue
            et = TYPE.get(tc, 'regulatory_filing'); title = (it.get('docDescription') or LABEL.get(tc) or f'EDINET document {tc}')
            for r in rs:
                per[key(r)].append(event(r, et, dt, title, 'EDINET (統合開示システム) — statutory filing', VIEW + it['docID'], 'EDINET API v2 documents list (statutory filings per EDINET code)', wire='EDINET', detail=f"docTypeCode {tc} {LABEL.get(tc, '')}; formCode {it.get('formCode')}; filer {it.get('filerName')}; period {it.get('periodStart')}..{it.get('periodEnd')}; secCode {it.get('secCode')}; ordinance {it.get('ordinanceCode')}", category=LABEL.get(tc, tc), reference=it['docID'], language='ja'))
    with open('raw/edinet_events.jsonl', 'w', encoding='utf-8') as f:
        for r in issuers:
            evs = per[key(r)]
            f.write(json.dumps({'key': key(r), 'events': evs, 'n': len(evs), **({} if r.get('reg_id') else {'gap': 'no EDINET code on the roster line (no filer joined at Width 0)'})}, ensure_ascii=False) + '\n')
    print('edinet events', sum(len(v) for v in per.values()), 'issuers with events', sum(1 for v in per.values() if v), '/', len(issuers), flush=True)
if __name__ == '__main__':
    sweep(); cut()
