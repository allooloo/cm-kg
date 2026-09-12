"""Pass 2.7 — Mistral (mistral-small-latest) as REVIEW ONLY (ORDER-017 re-cut): it never writes a field. It re-reads, in Korean, the same 사업보고서
text windows Gemini read and CONFIRMS or DISPUTES each value Gemini took (registrar, auditor, period end, going concern); anything Mistral finds that
Gemini did not take is a FLAG for the Review tab, never a record value. It also reviews the pages Perplexity located. Label: 'review by Mistral (ko)'.
Writes raw/mistral_reads.jsonl."""
from fc_common import *
from collections import Counter
LANG = 'ko'; LABEL = f'review by Mistral ({LANG})'
issuers = load_issuers(); byk = {key(r): r for r in issuers}
docs = {d['key']: d for d in jload('raw/dart_docs.jsonl') if d.get('docID')}
targets = []
for g in jload('raw/gemini_reads.jsonl'):
    if g.get('docID') and (g.get('registrar') or g.get('auditor') or g.get('period_end')): targets.append({'kind': 'gemini_doc', 'url': g['document_url'], 'key': g['key'], 'gemini': g})
for d in jload('raw/perplexity_pages.jsonl'):
    if d.get('verified') and d.get('url'): targets.append({'kind': 'perplexity_page', 'url': d['url'], 'key': d['key']})
def fetch(t):
    r = byk.get(t['key']) or {}; nm = r.get('name_native') or r.get('name', '')
    if t['kind'] == 'gemini_doc':
        d = docs.get(t['key']) or {}; g = t['gemini']
        txt = '\n'.join(['【명의개서대리인】'] + d.get('registrar_windows', []) + ['【회계감사인】'] + d.get('auditor_windows', []) + ['【사업연도】'] + d.get('period_windows', []) + ['【계속기업】'] + d.get('going_concern_windows', []))
        q = (f"발행회사: {nm}(종목코드 {r.get('ticker')}). 다른 엔진이 사업보고서 단락에서 다음 값을 읽었습니다: 명의개서대리인=\"{g.get('registrar')}\", 회계감사인=\"{g.get('auditor')}\", 사업연도 종료일=\"{g.get('period_end')}\", 계속기업=\"{g.get('going_concern')}\". "
             "아래 같은 단락을 한국어 그대로 읽고 각 값이 단락의 기재와 일치하는지 확인하십시오. 번역하지 마십시오. JSON으로만 답하십시오: "
             '{"registrar_ok": true|false, "auditor_ok": true|false, "period_end_ok": true|false, "going_concern_ok": true|false, "verdict": "confirm|dispute", "reason": "one line in English", '
             '"flags": [{"field": "registrar|auditor|period_end|going_concern|other", "value": "단락에 있으나 엔진이 취하지 않은 값 (원문)", "evidence": "원문 문장"}]}\n\n' + txt[:12000])
        res = mistral(q); j = jparse(res.get('text', '')) or {}
        return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'issuer': nm, 'verdict': j.get('verdict') or ('confirm' if all(j.get(k, True) for k in ('registrar_ok', 'auditor_ok', 'period_end_ok', 'going_concern_ok')) else 'dispute'), 'reason': j.get('reason', ''), 'checks': {k: j.get(k) for k in ('registrar_ok', 'auditor_ok', 'period_end_ok', 'going_concern_ok')}, 'flags': [f for f in (j.get('flags') or []) if isinstance(f, dict) and f.get('value')], 'usage': res.get('usage'), 'model': res.get('model'), 'error': res.get('error'), 'read_by': LABEL}
    txt, st = page_text(t['url'])
    if not txt or len(txt) < 200: return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'issuer': nm, 'verdict': 'no_view', 'reason': f'page body not readable ({st})', 'flags': [], 'read_by': LABEL}
    q = (f"발행회사: {nm}(종목코드 {r.get('ticker')}). 다른 엔진이 이 페이지를 발행회사 자신의 IR/공지 페이지로 특정했습니다. 페이지를 한국어 그대로 읽고 답하십시오. JSON으로만: "
         '{"issuer_named": true|false, "page_kind": "ir|news|corporate|other", "verdict": "confirm|dispute", "reason": "one line in English", "flags": [{"field": "auditor|registrar|meeting_date|record_date|period_end|other", "value": "", "evidence": "원문"}]}\n\n' + txt[:8000])
    res = mistral(q); j = jparse(res.get('text', '')) or {}
    return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'issuer': nm, 'verdict': j.get('verdict', ''), 'reason': j.get('reason', ''), 'issuer_named': j.get('issuer_named'), 'page_kind': j.get('page_kind'), 'flags': [f for f in (j.get('flags') or []) if isinstance(f, dict) and f.get('value')], 'usage': res.get('usage'), 'model': res.get('model'), 'error': res.get('error'), 'read_by': LABEL}
if __name__ == '__main__':
    print('review targets:', len(targets), Counter(t['kind'] for t in targets), flush=True)
    resume('mistral_reads', fetch, targets, threads=int(E.get('THREADS', '4')), keyf=lambda t: t['kind'] + '|' + t['url'])
    rows = jload('raw/mistral_reads.jsonl'); c = Counter(d.get('verdict') for d in rows)
    json.dump({'n_targets': len(targets), 'reviewed': len(rows), 'confirmed': c.get('confirm', 0), 'disputed': c.get('dispute', 0), 'no_view': c.get('no_view', 0), 'flags': sum(len(d.get('flags') or []) for d in rows), 'role': 'review only; never writes a field; flags go to the Review tab'}, open('raw/mistral_count.json', 'w'))
    print('mistral review', dict(c), 'flags', sum(len(d.get('flags') or []) for d in rows), flush=True)
