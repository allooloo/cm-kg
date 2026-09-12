"""DART filings per issuer over the window (event types from the Korean report name: the list response carries no publication-type field) through the DART list API (AGENT KEYS\\dart.txt): list.json per corp_code with bgn_de / end_de, 100 rows a
page. Event types from the publication type (pblntf_ty) and the report name: A 정기공시 (사업보고서 annual, 반기 / 분기보고서) → results; B 주요사항보고
→ ad_hoc; C 발행공시 (증권신고서 …) → prospectus; D 지분공시 (임원ㆍ주요주주특정증권등소유상황보고서 → directors_dealings; 주식등의대량보유상황보고서 → major_holder);
E 기타공시 → corporate_news; F 외부감사관련 → regulatory_filing (audit); I 거래소공시 (조회공시, 수시공시, 공정공시 — KIND mirrored) → exchange_bulletin, or
results / dividend / agm_egm / halt_suspension when the report name says so; J 공정위공시 → regulatory_filing. Titles are the report name in Korean
as filed (no machine translation). URL = the DART viewer page (dsaf001/main.do?rcpNo=). Read-by: 'DART list API (filings per corp_code)'.
Register rows are the issuer's own record: exempt from the name rule. Language 'ko'."""
import os, json, time
from common import *
DK = os.environ['DART_API_KEY']
API = 'https://opendart.fss.or.kr/api/list.json'; VIEW = 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo='
PT = {'A': 'results', 'B': 'ad_hoc', 'C': 'prospectus', 'D': 'major_holder', 'E': 'corporate_news', 'F': 'regulatory_filing', 'G': 'regulatory_filing', 'H': 'regulatory_filing', 'I': 'exchange_bulletin', 'J': 'regulatory_filing'}
PTL = {'A': '정기공시 (periodic)', 'B': '주요사항보고 (material events)', 'C': '발행공시 (issuance)', 'D': '지분공시 (ownership)', 'E': '기타공시 (other)', 'F': '외부감사관련 (external audit)', 'G': '펀드공시 (funds)', 'H': '자산유동화 (securitisation)', 'I': '거래소공시 (exchange disclosure)', 'J': '공정위공시 (fair trade)'}
RULES = [('halt_suspension', ('매매거래정지', '거래정지', '상장폐지')), ('directors_dealings', ('임원ㆍ주요주주', '임원·주요주주', '임원 주요주주', '특정증권등소유상황')), ('major_holder', ('대량보유', '대량보유상황')), ('takeover', ('공개매수',)), ('agm_egm', ('주주총회', '주총')), ('dividend', ('배당결정', '현금ㆍ현물배당', '현금·현물배당', '배당')),
         ('name_change', ('상호변경', '회사명변경')), ('results', ('사업보고서', '반기보고서', '분기보고서', '영업(잠정)실적', '결산실적', '연결재무제표기준영업', '매출액또는손익구조')), ('prospectus', ('증권신고서', '투자설명서', '일괄신고', '증권발행실적보고서')), ('ad_hoc', ('주요사항보고서',)), ('director_change', ('대표이사변경', '임원변경', '대표이사 변경')),
         ('regulatory_filing', ('감사보고서', '외부감사', '내부회계관리제도', '기업지배구조보고서', '지속가능경영보고서', '자기주식', '주식등의 대량')), ('exchange_bulletin', ('조회공시', '공정공시', '기타 경영사항', '기타경영사항', '풍문', '답변'))]
def etype(pt, nm):
    """type from the Korean report name (the DART list response carries no publication-type field); pt kept for compatibility"""
    n = (nm or '').replace(' ', '')
    for t, keys in RULES:
        if any(k.replace(' ', '') in n for k in keys): return t
    return PT.get(pt or '', 'corporate_news')
_gate = threading.Lock(); _last = [0.0]
def call(params, tries=4):
    for i in range(tries):
        with _gate:
            w = 0.25 - (time.time() - _last[0])
            if w > 0: time.sleep(w)
            _last[0] = time.time()
        try:
            r = requests.get(API, params={'crtfc_key': DK, **params}, headers=UA, timeout=60)
            if r.status_code != 200: time.sleep(3 * (i + 1)); continue
            return r.json()
        except Exception: time.sleep(3 * (i + 1))
    return {'status': 'error'}
def fetch(r):
    cc = r.get('reg_id') or ''
    if not cc: return {'gap': 'no DART corp code on the roster line', 'events': []}
    evs = []; seen = set(); page = 1; total = None; status = ''
    while page <= 30:
        j = call({'corp_code': cc, 'bgn_de': SINCE.strftime('%Y%m%d'), 'end_de': TODAY.strftime('%Y%m%d'), 'page_no': page, 'page_count': 100}); status = j.get('status')
        if status == '013': break  # no data
        if status != '000': return {'error': f"DART status {status} {j.get('message')}", 'events': evs}
        total = j.get('total_count'); rows = j.get('list') or []
        for it in rows:
            rn = it.get('rcept_no') or ''
            if not rn or rn in seen: continue
            seen.add(rn); dt = it.get('rcept_dt') or ''; dt = f'{dt[:4]}-{dt[4:6]}-{dt[6:8]}' if len(dt) == 8 else ''
            if not in_window(dt): continue
            pt = it.get('pblntf_ty') or ''; nm = (it.get('report_nm') or '').strip()
            evs.append(event(r, etype(pt, nm), dt, nm, 'DART (전자공시시스템) — filing', VIEW + rn, 'DART list API (filings per corp_code)', wire='DART', detail=f"pblntf_ty {pt} {PTL.get(pt, '')}; submitter {it.get('flr_nm')}; corp_cls {it.get('corp_cls')}; remarks {it.get('rm')}", category=PTL.get(pt, pt), reference=rn, language='ko'))
        if len(rows) < 100 or page * 100 >= (total or 0): break
        page += 1
    return {'events': evs, 'n': len(evs), 'total_items': total}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('dart_events', fetch, issuers, threads=3)
