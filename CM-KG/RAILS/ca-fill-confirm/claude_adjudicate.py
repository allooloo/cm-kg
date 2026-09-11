"""Pass 2.2 — Claude adjudicates the Width 0 pockets: conflicting ISINs and unrecognised / conflicting auditor strings.
Claude reads the cited sources (page text fetched now, or the stored evidence when the page will not answer) and rules,
or leaves the field blank with a one-line reason. Label: 'adjudicated by Claude'."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
isin = {d['key']: d for d in jload('raw/width0/enr_isin.jsonl')}
corp = {d['key']: d for d in jload('raw/width0/enr_corp.jsonl')}
from collections import Counter
_src = open(r'C:\ALLOOLOO\CM-KG\RAILS\ca-width0\assemble.py', encoding='utf-8').read()
KNOWN_AUD = eval(re.search(r'^KNOWN_AUD = (\[.*?\])\s*$', _src, re.M).group(1))  # the recognised-firm list of record (Width 0)
KNOWN_SET = set(c for c, _ in KNOWN_AUD)
def canon_aud(name):
    for canon, pat in KNOWN_AUD:
        if re.search(pat, name, re.I): return canon
    return name
def is_known_aud(name): return name in KNOWN_SET
def repick_aud(c):
    cands = c.get('aud_cands') or {}
    if not cands: return c.get('aud', ''), c.get('aud_gap', 'none found')
    merged = Counter()
    for k, v in cands.items(): merged[canon_aud(k)] += v
    (b, s) = merged.most_common(1)[0]
    if len(merged) > 1 and merged.most_common(2)[1][1] == s: return '', 'conflict: ' + '; '.join(f'{k}({v})' for k, v in merged.most_common(3))
    return b, ''
SYS = ("You are the reader of record for a capital-markets identity registry. You answer only from the evidence given. "
       "You never guess. If the evidence does not settle the question, you say so. Reply with strict JSON only.")
def excerpt(url, needle, span=500):
    t, st = page_text(url)
    if not t: return f'[{url} did not answer: http {st}]'
    i = t.find(needle) if needle else -1
    return (t[max(0, i - span):i + span] if i >= 0 else t[:2 * span])
def rule_isin(r):
    d = isin.get(key(r), {}); cands = d.get('cands') or {}
    ev = []
    for c in list(cands)[:4]:
        for u in (d.get('urls') or {}).get(c, [])[:1] if isinstance(d.get('urls'), dict) else []:
            ev.append(f'--- {c} on {u}\n{excerpt(u, c)}')
    if not ev:  # urls not stored for conflicts; refetch from a search of the candidate pages
        j = tavily({'query': f"{r['name']} {r['root']} ISIN", 'max_results': 4, 'include_raw_content': True, 'include_domains': ['marketscreener.com', 'investing.com', 'stockanalysis.com', 'tradingview.com', 'morningstar.ca']})
        for x in j.get('results', []):
            txt = (x.get('raw_content') or '') + ' ' + (x.get('content') or '')
            for c in cands:
                i = txt.find(c)
                if i >= 0: ev.append(f'--- {c} on {x["url"]}\n{txt[max(0, i - 400):i + 400]}')
    prompt = (f"Issuer: {r['name']} — listed on {r['exchange']} as {r['ticker']}. Candidate ISINs found on quote pages: {list(cands)}.\n"
              f"Question: which ISIN identifies THIS issuer's listed common shares on {r['exchange']}? A US-prefixed ISIN may belong to a US-domiciled issuer, an ADR, or a different security; "
              f"a CA ISIN may belong to a Canadian-domiciled issuer. Rule ONLY if the evidence names the issuer with that ISIN for the listed shares.\n\nEVIDENCE:\n" + '\n'.join(ev)[:12000] +
              '\n\nReply JSON: {"isin": "<ISIN or empty>", "confidence": "high|medium|low", "reason": "<one line>", "source": "<URL that settles it or empty>"}')
    res = claude(prompt, SYS)
    j = jparse(res.get('text', '')) or {}
    return {'field': 'ISIN', 'ruling': j.get('isin', ''), 'confidence': j.get('confidence', ''), 'reason': j.get('reason', ''), 'source': j.get('source', ''), 'usage': res.get('usage'), 'cands': cands, 'error': res.get('error')}
def rule_auditor(r):
    c = corp.get(key(r), {}); cands = c.get('aud_cands') or {}
    ev = f"Evidence snippet from {c.get('aud_src')}: {c.get('aud_ev')}\n"
    if c.get('aud_src'): ev += '\nPage excerpt:\n' + excerpt(c['aud_src'], 'uditor', 700)
    prompt = (f"Issuer: {r['name']} ({r['exchange']}: {r['ticker']}). Strings read as a possible auditor: {list(cands)}.\n"
              f"Question: which audit firm is named as THIS issuer's auditor in the evidence? Give the firm's proper name (e.g. 'KPMG LLP', 'Davidson & Company LLP'). "
              f"If the evidence names no audit firm for this issuer, leave it empty.\n\nEVIDENCE:\n{ev[:9000]}\n\n"
              'Reply JSON: {"auditor": "<firm or empty>", "confidence": "high|medium|low", "reason": "<one line>"}')
    res = claude(prompt, SYS)
    j = jparse(res.get('text', '')) or {}
    return {'field': 'Auditor', 'ruling': j.get('auditor', ''), 'confidence': j.get('confidence', ''), 'reason': j.get('reason', ''), 'source': c.get('aud_src', ''), 'usage': res.get('usage'), 'cands': cands, 'error': res.get('error')}
if __name__ == '__main__':
    isin_items = [byk[k] for k, d in isin.items() if 'conflict' in d.get('gap', '') and k in byk]
    aud_items = []
    for k, c in corp.items():
        if k not in byk: continue
        v, g = repick_aud(c)
        if (v and not is_known_aud(v)) or 'conflict' in (g or ''): aud_items.append(byk[k])
    print('ISIN conflicts', len(isin_items), '| auditor unrecognised/conflict', len(aud_items), flush=True)
    resume('claude_isin', rule_isin, isin_items, threads=3)
    resume('claude_auditor', rule_auditor, aud_items, threads=3)
