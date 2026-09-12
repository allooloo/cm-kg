"""Pass 2.7 — Mistral (mistral-small-latest) as REVIEW ONLY (ORDER-017 re-cut: Gemini reads Japanese as primary; Mistral review only; machine-translated
English never a source). Mistral never writes a field. It re-reads, in Japanese, the same text windows Gemini read and CONFIRMS or DISPUTES each value
Gemini took (auditor, registrar, period end, going concern); anything Mistral finds that Gemini did not take is a FLAG for the Review tab, never a
record value. It also reviews the pages Perplexity located (issuer named, page kind). Label: 'review by Mistral (ja)'. Writes raw/mistral_reads.jsonl."""
from fc_common import *
from collections import Counter
LANG = 'ja'; LABEL = f'review by Mistral ({LANG})'
issuers = load_issuers(); byk = {key(r): r for r in issuers}
docs = {d['key']: d for d in jload('raw/edinet_docs.jsonl') if d.get('docID')}
targets = []
for g in jload('raw/gemini_reads.jsonl'):
    if g.get('docID') and (g.get('auditor') or g.get('registrar') or g.get('period_end')): targets.append({'kind': 'gemini_doc', 'url': g['document_url'], 'key': g['key'], 'gemini': g})
for d in jload('raw/perplexity_pages.jsonl'):
    if d.get('verified') and d.get('url'): targets.append({'kind': 'perplexity_page', 'url': d['url'], 'key': d['key']})
def fetch(t):
    r = byk.get(t['key']) or {}; nm = r.get('name_native') or r.get('name', '')
    if t['kind'] == 'gemini_doc':
        d = docs.get(t['key']) or {}; g = t['gemini']
        txt = '\n'.join(['【監査法人 / 会計監査人】'] + d.get('auditor_windows', []) + ['【株主名簿管理人】'] + d.get('registrar_windows', []) + ['【事業年度】'] + d.get('period_windows', []) + ['【継続企業の前提】'] + d.get('going_concern_windows', []))
        q = (f"発行体: {nm}（証券コード {r.get('ticker')}）。別のエンジンが有価証券報告書の本文断片から次の値を読み取りました: 会計監査人=\"{g.get('auditor')}\", 株主名簿管理人=\"{g.get('registrar')}\", 事業年度末日=\"{g.get('period_end')}\", 継続企業の前提=\"{g.get('going_concern')}\"。"
             "以下の同じ断片を日本語のまま読み、各値が断片の記載と一致するか確認してください。翻訳はしないでください。JSONのみで回答: "
             '{"auditor_ok": true|false, "registrar_ok": true|false, "period_end_ok": true|false, "going_concern_ok": true|false, "verdict": "confirm|dispute", "reason": "one line in English", '
             '"flags": [{"field": "auditor|registrar|period_end|going_concern|other", "value": "断片にあるがエンジンが取らなかった値（原文）", "evidence": "原文の一文"}]}\n\n' + txt[:12000])
        res = mistral(q); j = jparse(res.get('text', '')) or {}
        return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'issuer': nm, 'verdict': j.get('verdict') or ('confirm' if all(j.get(k, True) for k in ('auditor_ok', 'registrar_ok', 'period_end_ok', 'going_concern_ok')) else 'dispute'), 'reason': j.get('reason', ''), 'checks': {k: j.get(k) for k in ('auditor_ok', 'registrar_ok', 'period_end_ok', 'going_concern_ok')}, 'flags': [f for f in (j.get('flags') or []) if isinstance(f, dict) and f.get('value')], 'usage': res.get('usage'), 'model': res.get('model'), 'error': res.get('error'), 'read_by': LABEL}
    txt, st = page_text(t['url'])
    if not txt or len(txt) < 200: return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'issuer': nm, 'verdict': 'no_view', 'reason': f'page body not readable ({st})', 'flags': [], 'read_by': LABEL}
    q = (f"発行体: {nm}（証券コード {r.get('ticker')}）。別のエンジンがこのページを発行体自身のIR・お知らせページとして特定しました。ページを日本語のまま読んで答えてください。JSONのみ: "
         '{"issuer_named": true|false, "page_kind": "ir|news|corporate|other", "verdict": "confirm|dispute", "reason": "one line in English", "flags": [{"field": "auditor|registrar|meeting_date|record_date|period_end|other", "value": "", "evidence": "原文"}]}\n\n' + txt[:8000])
    res = mistral(q); j = jparse(res.get('text', '')) or {}
    return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'issuer': nm, 'verdict': j.get('verdict', ''), 'reason': j.get('reason', ''), 'issuer_named': j.get('issuer_named'), 'page_kind': j.get('page_kind'), 'flags': [f for f in (j.get('flags') or []) if isinstance(f, dict) and f.get('value')], 'usage': res.get('usage'), 'model': res.get('model'), 'error': res.get('error'), 'read_by': LABEL}
if __name__ == '__main__':
    print('review targets:', len(targets), Counter(t['kind'] for t in targets), flush=True)
    resume('mistral_reads', fetch, targets, threads=int(E.get('THREADS', '4')), keyf=lambda t: t['kind'] + '|' + t['url'])
    rows = jload('raw/mistral_reads.jsonl'); c = Counter(d.get('verdict') for d in rows)
    json.dump({'n_targets': len(targets), 'reviewed': len(rows), 'confirmed': c.get('confirm', 0), 'disputed': c.get('dispute', 0), 'no_view': c.get('no_view', 0), 'flags': sum(len(d.get('flags') or []) for d in rows), 'role': 'review only; never writes a field; flags go to the Review tab'}, open('raw/mistral_count.json', 'w'))
    print('mistral review', dict(c), 'flags', sum(len(d.get('flags') or []) for d in rows), flush=True)
