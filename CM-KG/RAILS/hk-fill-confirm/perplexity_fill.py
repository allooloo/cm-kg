"""Pass 2.2 — Perplexity (Agent API, preset low), first in the reading order of record. For every roster line: the auditor and the Hong Kong share
registrar as the issuer's own filings state them, and the city of its principal place of business in Hong Kong. A value is kept only when its source
URL is one of the pages Perplexity's search_results returned (the prose is never a source) and the page is an English-language one.
Label: 'read by Perplexity (agent · low)'. Raw: raw/perplexity_fill.jsonl."""
from fc_common import *
LABEL = 'read by Perplexity (agent · low)'
def ask(r):
    name = r['Name of Securities (HKEX, English)']; code = r['Stock code']; board = r['_tab']
    prompt = (f"For the Hong Kong-listed issuer {name} (HKEX stock code {code}, {board}), using its English-language filings on HKEXnews or its own investor-relations site: "
              "1) its auditor as named in the latest annual report, 2) its Hong Kong (branch) share registrar, 3) the city of its principal place of business in Hong Kong. "
              "Use only English-language pages. Reply with JSON only: {\"auditor\": \"\", \"auditor_source\": \"<URL>\", \"registrar\": \"\", \"registrar_source\": \"<URL>\", \"hq_city\": \"\", \"hq_source\": \"<URL>\"}; empty strings where not found.")
    res = perplexity_agent(prompt, preset='low'); j = jparse(res.get('text', '')) or {}
    srcs = {s['url'] for s in res.get('sources', []) if s.get('url')}
    out = {'model': res.get('model'), 'cost': res.get('cost'), 'usage': res.get('usage'), 'error': res.get('error'), 'sources': res.get('sources', [])[:8]}
    for f in ('auditor', 'registrar', 'hq_city'):
        v = (j.get(f) or '').strip(); s = (j.get(f'{f}_source') or j.get('hq_source' if f == 'hq_city' else '') or '').strip()
        if v and not CJK.search(v) and s and (s in srcs or s.rstrip('/') in {x.rstrip('/') for x in srcs}): out[f] = v; out[f'{f}_source'] = s
        elif v: out[f'{f}_unsourced'] = v
    return out
if __name__ == '__main__':
    rows = all_rows(); rows = rows[:int(E['PPLX_MAX'])] if E.get('PPLX_MAX') else rows
    resume('perplexity_fill', ask, rows, threads=int(E.get('THREADS', '8')))
