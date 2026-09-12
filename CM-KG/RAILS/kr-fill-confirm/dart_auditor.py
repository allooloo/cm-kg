"""Pass 2.1 — the auditor from DART's structured endpoint 회계감사인의 명칭 및 감사의견 (accnutAdtorNmNdAdtOpinion.json, keyed with AGENT KEYS\\dart.txt)
for the latest annual report (reprt_code 11011) of the last two business years: audit firm (adtor), audit opinion, period end (stlm_dt),
emphasis-of-matter / going-concern text (emphs_matter, adt_reprt_spcmnt_matter) and the receipt number of the report. Sourced from the regulator's
own API, not a lab read. Read-by: 'DART API 회계감사인의 명칭 및 감사의견 (annual report, business year <y>)'. Source URL = the DART viewer page of the
receipt. Writes raw/dart_auditor.jsonl. Resumable."""
from fc_common import *
DK = os.environ['DART_API_KEY']
issuers = load_issuers()
VIEW = 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo='
_gate = threading.Lock(); _last = [0.0]
def call(cc, year):
    with _gate:
        w = 0.25 - (time.time() - _last[0])
        if w > 0: time.sleep(w)
        _last[0] = time.time()
    for i in range(4):
        try:
            r = requests.get('https://opendart.fss.or.kr/api/accnutAdtorNmNdAdtOpinion.json', params={'crtfc_key': DK, 'corp_code': cc, 'bsns_year': str(year), 'reprt_code': '11011'}, headers=UA, timeout=60)
            if r.status_code != 200: time.sleep(3 * (i + 1)); continue
            return r.json()
        except Exception: time.sleep(3 * (i + 1))
    return {'status': 'error'}
def fetch(r):
    cc = r.get('reg_id') or ''
    if not cc: return {'gap': 'no DART corp code'}
    for year in (TODAY.year, TODAY.year - 1):
        j = call(cc, year)
        if j.get('status') == '000' and j.get('list'):
            rows = [x for x in j['list'] if x.get('adtor')]
            if not rows: continue
            cur = next((x for x in rows if '당기' in (x.get('bsns_year') or '')), rows[0])
            gc = ''
            em = (cur.get('emphs_matter') or '').strip(); sp = (cur.get('adt_reprt_spcmnt_matter') or '').strip()
            if '계속기업' in em or '계속기업' in sp: gc = 'material uncertainty stated (계속기업 관련 중요한 불확실성)'
            elif em and em not in ('-', '해당사항 없음', '해당사항없음'): gc = 'emphasis of matter stated: ' + em[:120]
            return {'auditor': cur['adtor'].strip(), 'opinion': (cur.get('adt_opinion') or '').strip(), 'period_end': to_iso(cur.get('stlm_dt') or ''), 'business_year': year, 'bsns_year_label': (cur.get('bsns_year') or '').replace('\n', ' '), 'emphasis': em[:300], 'special': sp[:300], 'going_concern': gc, 'rcept_no': cur.get('rcept_no', ''),
                    'source_url': VIEW + (cur.get('rcept_no') or ''), 'read_by': f'DART API 회계감사인의 명칭 및 감사의견 (annual report 11011, business year {year})', 'status': j.get('status')}
        if j.get('status') not in ('000', '013'): return {'error': f"DART status {j.get('status')} {j.get('message')}"}
    return {'gap': 'no auditor row on the DART annual-report endpoint for the last two business years'}
if __name__ == '__main__':
    targets = [r for r in issuers if r.get('reg_id')]
    print('issuers with a DART corp code:', len(targets), flush=True)
    resume('dart_auditor', fetch, targets, threads=int(E.get('THREADS', '3')))
    rows = jload('raw/dart_auditor.jsonl'); print('auditor rows', sum(1 for d in rows if d.get('auditor')), 'of', len(rows), 'going concern', sum(1 for d in rows if d.get('going_concern')), flush=True)
