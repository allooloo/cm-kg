"""Pass 3 — Claude adjudicates the conflicts Pass 3 raised (first source vs second source) for transfer agent, auditor, ISIN,
jurisdiction and newswire of habit. Claude sees both values with their sources and rules for one, or leaves the field as a
conflict with a one-line reason. Label: 'adjudicated by Claude'. Writes raw/conflict_rulings.jsonl."""
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Ticker']: r for r in all_rows()}
conf = {d['key']: d for d in jload('raw/confirm_fields.jsonl')}
COL = {'Transfer agent': ('Transfer agent', 'Transfer agent source'), 'Auditor': ('Auditor', 'Auditor source'), 'ISIN': ('ISIN', 'ISIN source'), 'Incorporation jurisdiction': ('Incorporation jurisdiction', 'Jurisdiction source'), 'Newswire of habit': ('Newswire of habit', 'Newswire releases seen')}
SYS = 'You adjudicate between two sourced readings of one fact about a listed company. Rule only when one reading is clearly the fact for this issuer; otherwise say so. Never guess. JSON only.'
items = []
for k, d in conf.items():
    for f, v in d.get('fields', {}).items():
        if v.get('state') == 'conflict' and f in COL: items.append({'key': k, 'field': f, 'second': v.get('second', []), 'read_by2': v.get('read_by2', '')})
def rule(it):
    r = byk[it['key']]; row = rows.get(it['key'], {}); col, src = COL[it['field']]
    first = row.get(col) or ''; fsrc = row.get(src) or ''
    prompt = (f"Issuer: {r['name']} ({r['exchange']}: {r['ticker']}). Field: {it['field']}.\n"
              f"Reading A: \"{first}\" — source: {fsrc[:300]} — read by: {row.get(it['field'] + ' read by') or row.get('Newswire read by') or ''}\n"
              f"Reading B: \"{'; '.join(str(x) for x in it['second'])}\" — read by: {it['read_by2']}\n"
              + ("Note: for 'Newswire of habit', reading B is the wire carrying the majority of this issuer's releases over the last 12 months; reading A came from three releases.\n" if it['field'] == 'Newswire of habit' else '')
              + "Reply JSON: {\"ruling\": \"<the value that stands, or empty if it cannot be settled>\", \"basis\": \"A|B|neither\", \"reason\": \"one line\"}")
    res = claude(prompt, SYS, max_tokens=300)
    j = jparse(res.get('text', '')) or {}
    return {'field': it['field'], 'ruling': j.get('ruling', ''), 'basis': j.get('basis', ''), 'reason': j.get('reason', ''), 'first': first, 'second': it['second'], 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    print('conflicts to adjudicate', len(items), flush=True)
    resume('conflict_rulings', rule, items, threads=6, keyf=lambda it: it['key'] + '#' + it['field'])
