"""Pass 3 — Claude adjudicates the conflicts Pass 3 raised (first source vs second source) for share registry, auditor, ISIN, LEI, SIREN, state and
newswire of habit. Claude sees both values with their sources and rules for one, or leaves the field as a conflict with a one-line reason.
Label: 'adjudicated by Claude'. Writes raw/conflict_rulings.jsonl (key#field)."""
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Symbol']: r for r in all_rows()}
conf = {d['key']: d for d in jload('raw/confirm_fields.jsonl')}
COL = {'Share registrar': ('Share registrar', 'Share registry source', 'Share registry read by'), 'Auditor': ('Auditor', 'Annual report (EQS News)', 'Annual report read by'), 'ISIN': ('ISIN', 'ISIN source', 'ISIN read by'), 'LEI': ('LEI', 'LEI source', 'LEI read by'), 'SIREN': ('SIREN', 'Register source', 'Register read by'), 'State': ('State', 'State source', 'State read by'), 'Newswire of habit': ('Newswire of habit', 'Newswire releases seen', 'Newswire read by')}
SYS = 'You adjudicate between two sourced readings of one fact about a listed company. Rule only when one reading is clearly the fact for this issuer; otherwise say so. Never guess. JSON only.'
items = []
for k, d in conf.items():
    for f, v in d.get('fields', {}).items():
        if v.get('state') == 'conflict' and f in COL and k in byk: items.append({'key': k, 'field': f, 'first': v.get('value') or '', 'second': v.get('second', []), 'read_by2': v.get('read_by2', '')})
def rule(it):
    r = byk[it['key']]; row = rows.get(it['key'], {}); col, src, rb = COL[it['field']]
    first = it['first'] or row.get(col) or ''; fsrc = row.get(src) or ''
    note = {'Newswire of habit': "Note: reading B is the channel carrying the majority of this issuer's announcements over 12 months; EQS News is every exchange issuer's primary channel.\n",
            'Auditor': "Note: reading A comes from the independent auditor's report in the latest annual report lodged on EQS News (the most authoritative source); reading B is page text.\n"}.get(it['field'], '')
    prompt = (f"Issuer: {r['name']} ({r['exchange']}: {r['ticker']}). Field: {it['field']}.\nReading A: \"{first}\" — source: {str(fsrc)[:300]} — read by: {row.get(rb) or ''}\n"
              f"Reading B: \"{'; '.join(str(x) for x in it['second'])}\" — read by: {it['read_by2']}\n" + note + "Reply JSON: {\"ruling\": \"<the value that stands, or empty if it cannot be settled>\", \"basis\": \"A|B|neither\", \"reason\": \"one line\"}")
    res = claude(prompt, SYS, max_tokens=300); j = jparse(res.get('text', '')) or {}
    return {'field': it['field'], 'ruling': j.get('ruling', ''), 'basis': j.get('basis', ''), 'reason': j.get('reason', ''), 'first': first, 'second': it['second'], 'usage': res.get('usage'), 'error': res.get('error')}
if __name__ == '__main__':
    print('conflicts to adjudicate', len(items), flush=True)
    resume('conflict_rulings', rule, items, threads=6, keyf=lambda it: it['key'] + '#' + it['field'])
