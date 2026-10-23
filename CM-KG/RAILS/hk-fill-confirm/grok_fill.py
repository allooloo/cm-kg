"""Pass 2.3 — Grok (grok-4.6, web search), second in the reading order of record and the cost driver: only the roster lines where neither the annual report
(pass 2.1) nor Perplexity (pass 2.2) gave a sourced auditor or share registrar. A value is kept only with a cited URL from Grok's own annotations.
Label: 'read by Grok (grok-4.6, web search)'. Raw: raw/grok_fill.jsonl."""
from fc_common import *
AR = {d['key']: d for d in jload('raw/annual_reports.jsonl')}; AR.update({d['key']: d for d in jload('raw/annual_reports2.jsonl') if d.get('annual_report')}); PX = {d['key']: d for d in jload('raw/perplexity_fill.jsonl')}
def missing(r):
    k = key_of(r); a = AR.get(k, {}); p = PX.get(k, {})
    return [f for f in ('auditor', 'registrar') if not (a.get(f) or p.get(f))]
def ask(r):
    need = missing(r); name = r['Name of Securities (HKEX, English)']; code = r['Stock code']
    words = {'auditor': 'its auditor as named in its latest annual report', 'registrar': 'its Hong Kong (branch) share registrar'}
    prompt = (f"Hong Kong-listed issuer {name} (HKEX stock code {code}). From English-language pages only (HKEXnews filings or the company's own site), give "
              + ' and '.join(words[f] for f in need) + ". Reply with JSON only: {" + ', '.join(f'\"{f}\": \"\", \"{f}_source\": \"<URL>\"' for f in need) + "}; empty strings where not found.")
    res = grok(prompt); j = jparse(res.get('text', '')) or {}; cites = set(res.get('citations') or [])
    out = {'need': need, 'model': res.get('model'), 'usage': res.get('usage'), 'error': res.get('error')}
    for f in need:
        v = (j.get(f) or '').strip(); s = (j.get(f'{f}_source') or '').strip()
        if v and not CJK.search(v) and s.startswith('http') and (not cites or s in cites or any(s.rstrip('/') == c.rstrip('/') for c in cites)): out[f] = v; out[f'{f}_source'] = s
        elif v: out[f'{f}_unsourced'] = v
    return out
if __name__ == '__main__':
    rows = [r for r in all_rows() if missing(r)]; print('lines with a field still missing after passes 2.1-2.2:', len(rows), flush=True)
    resume('grok_fill', ask, rows, threads=int(E.get('THREADS', '6')))
