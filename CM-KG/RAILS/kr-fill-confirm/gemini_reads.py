"""Pass 2.3 — Gemini (gemini-flash-latest) reads the Korean text windows cut from each issuer's 사업보고서 (dart_docs.py) as the PRIMARY reader
(ORDER-017 re-cut: the regulator's language is the source; machine-translated English is never a source). Fields: transfer agent / register
administrator (명의개서대리인, e.g. "한국예탁결제원", "국민은행 증권대행부", "하나은행"), the auditor line as written (회계감사인, kept beside the DART structured
value), the fiscal period end and going-concern language (계속기업 관련 중요한 불확실성). Values verbatim in Korean with the evidence quoted.
Label: 'read by Gemini (ko) — DART 사업보고서 text windows'. Writes raw/gemini_reads.jsonl."""
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
LABEL = 'read by Gemini (ko) — DART 사업보고서 text windows'
docs = {d['key']: d for d in jload('raw/dart_docs.jsonl') if d.get('docID')}
def fetch(r):
    d = docs.get(key(r))
    if not d: return {'gap': 'no annual-report windows for this issuer'}
    txt = '\n'.join(['【명의개서대리인】'] + d.get('registrar_windows', []) + ['【회계감사인】'] + d.get('auditor_windows', []) + ['【사업연도】'] + d.get('period_windows', []) + ['【계속기업】'] + d.get('going_concern_windows', []))
    prompt = (f"다음은 {r.get('name_native') or r['name']}(종목코드 {r['ticker']})의 사업보고서 본문에서 잘라낸 한국어 단락입니다. 단락에 적힌 내용만을 근거로 아래를 JSON으로 답하십시오. 번역하지 마십시오. 값은 원문 그대로 옮겨 적으십시오.\n"
              '{"registrar": "명의개서대리인 (원문 그대로, 없으면 빈 문자열)", "registrar_evidence": "근거 문장 (원문)", "auditor": "회계감사인 (원문 그대로, 없으면 빈 문자열)", "auditor_evidence": "근거 문장 (원문)", '
              '"period_end": "사업연도 종료일 YYYY-MM-DD (없으면 빈 문자열)", "going_concern": "stated|not_stated|unclear (계속기업 관련 중요한 불확실성 기재 여부)", "going_concern_evidence": "근거 (원문, 30자 이내)"}\n\n' + txt[:12000])
    res = gemini(prompt); j = jparse(res.get('text', '')) or {}
    return {'registrar': (j.get('registrar') or '').strip(), 'registrar_evidence': (j.get('registrar_evidence') or '')[:300], 'auditor': (j.get('auditor') or '').strip(), 'auditor_evidence': (j.get('auditor_evidence') or '')[:300], 'period_end': to_iso(j.get('period_end') or '') or (j.get('period_end') or ''), 'going_concern': j.get('going_concern') or '', 'going_concern_evidence': (j.get('going_concern_evidence') or '')[:200],
            'document_url': d['document_url'], 'docID': d['docID'], 'doc_date': d.get('doc_date'), 'usage': res.get('usage'), 'model': res.get('model'), 'error': res.get('error'), 'read_by': LABEL}
if __name__ == '__main__':
    targets = [r for r in issuers if key(r) in docs]
    print('issuers with report windows:', len(targets), flush=True)
    resume('gemini_reads', fetch, targets, threads=int(E.get('THREADS', '6')))
    rows = jload('raw/gemini_reads.jsonl'); print('gemini reads', len(rows), 'registrar', sum(1 for d in rows if d.get('registrar')), 'auditor', sum(1 for d in rows if d.get('auditor')), 'period end', sum(1 for d in rows if d.get('period_end')), flush=True)
