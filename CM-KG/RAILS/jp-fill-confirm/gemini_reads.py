"""Pass 2.2 — Gemini (gemini-flash-latest) reads the Japanese text windows cut from each issuer's 有価証券報告書 (edinet_docs.py) as the PRIMARY reader
(ORDER-017 re-cut: Gemini reads Japanese; machine-translated English is never a source). Fields: auditor (会計監査人 — the audit firm as written, e.g.
"EY新日本有限責任監査法人"), shareholder-register administrator (株主名簿管理人, e.g. "三井住友信託銀行株式会社"), fiscal period end (事業年度 … 至 YYYY年MM月DD日)
and going-concern language (継続企業の前提に関する重要事象 stated or not). Values are copied from the Japanese text verbatim with the evidence quoted;
nothing is translated. Label: 'read by Gemini (ja) — EDINET 有価証券報告書 text windows'. Writes raw/gemini_reads.jsonl."""
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
LABEL = 'read by Gemini (ja) — EDINET 有価証券報告書 text windows'
docs = {d['key']: d for d in jload('raw/edinet_docs.jsonl') if d.get('docID')}
def fetch(r):
    d = docs.get(key(r))
    if not d: return {'gap': 'no securities report windows for this issuer'}
    txt = '\n'.join(['【監査法人 / 会計監査人】'] + d.get('auditor_windows', []) + ['【株主名簿管理人】'] + d.get('registrar_windows', []) + ['【事業年度】'] + d.get('period_windows', []) + ['【継続企業の前提】'] + d.get('going_concern_windows', []))
    prompt = (f"以下は、{r.get('name_native') or r['name']}（証券コード {r['ticker']}）の有価証券報告書から切り出した日本語の本文断片です。断片に書かれていることだけを根拠に、次をJSONで答えてください。翻訳はしないでください。値は原文のまま書き写してください。\n"
              '{"auditor": "会計監査人（監査法人名。原文どおり。不明なら空）", "auditor_evidence": "根拠の一文（原文）", "registrar": "株主名簿管理人（原文どおり。不明なら空）", "registrar_evidence": "根拠の一文（原文）", '
              '"period_end": "事業年度の末日 YYYY-MM-DD（不明なら空）", "going_concern": "stated|not_stated|unclear（継続企業の前提に関する重要事象等の記載の有無）", "going_concern_evidence": "根拠（原文、30字以内）"}\n\n' + txt[:12000])
    res = gemini(prompt); j = jparse(res.get('text', '')) or {}
    return {'auditor': (j.get('auditor') or '').strip(), 'auditor_evidence': (j.get('auditor_evidence') or '')[:300], 'registrar': (j.get('registrar') or '').strip(), 'registrar_evidence': (j.get('registrar_evidence') or '')[:300], 'period_end': to_iso(j.get('period_end') or '') or (j.get('period_end') or ''), 'going_concern': j.get('going_concern') or '', 'going_concern_evidence': (j.get('going_concern_evidence') or '')[:200],
            'document_url': d['document_url'], 'docID': d['docID'], 'doc_date': d.get('doc_date'), 'usage': res.get('usage'), 'model': res.get('model'), 'error': res.get('error'), 'read_by': LABEL}
if __name__ == '__main__':
    targets = [r for r in issuers if key(r) in docs]
    print('issuers with report windows:', len(targets), flush=True)
    resume('gemini_reads', fetch, targets, threads=int(E.get('THREADS', '6')))
    rows = jload('raw/gemini_reads.jsonl'); print('gemini reads', len(rows), 'auditor', sum(1 for d in rows if d.get('auditor')), 'registrar', sum(1 for d in rows if d.get('registrar')), 'period end', sum(1 for d in rows if d.get('period_end')), 'going concern stated', sum(1 for d in rows if d.get('going_concern') == 'stated'), flush=True)
