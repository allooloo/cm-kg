"""Pass 3 — Confirm, then Mistral (review only). Per field (auditor, share registrar):
  the annual report's own Corporate Information page (pass 2.1) and a lab read (Perplexity, else Grok) name the same firm  → confirmed (two sources)
  only the annual report names it → sourced (from the filing); only a lab names it (with its cited page) → filled
  the annual report and a lab name different firms → conflict: both kept, the filing's value stands as the value, the lab's as the conflict note.
Mistral (mistral-small-latest) reads each conflict as review only: it writes a review flag beside the line, never a field.
Writes raw/confirm.jsonl (one line per roster line: the field values, states, sources, read-bys) and raw/mistral_review.jsonl."""
from fc_common import *
AR = {d['key']: d for d in jload('raw/annual_reports.jsonl')}; AR.update({d['key']: d for d in jload('raw/annual_reports2.jsonl') if d.get('annual_report')}); PX = {d['key']: d for d in jload('raw/perplexity_fill.jsonl')}; GK = {d['key']: d for d in jload('raw/grok_fill.jsonl')}
PL = 'read by Perplexity (agent · low)'; GL = 'read by Grok (grok-4.6, web search)'
def decide(r):
    k = key_of(r); a = AR.get(k, {}); p = PX.get(k, {}); g = GK.get(k, {}); out = {'key': k}
    if a.get('annual_report'): out['annual_report'] = {'value': a['annual_report'], 'source': a['annual_report'], 'read_by': f"HKEXnews title search (Width 1), annual report of {a.get('annual_report_date')}", 'state': 'sourced'}
    for f in ('auditor', 'registrar'):
        fv = a.get(f); lab = (p.get(f), p.get(f'{f}_source'), PL) if p.get(f) else ((g.get(f), g.get(f'{f}_source'), GL) if g.get(f) else (None, None, None))
        ar_src = a.get('annual_report'); ar_rb = f"annual report {a.get('annual_report_date')} (HKEXnews), Corporate Information, read by Tavily page extraction"
        if fv and lab[0] and same_firm(fv, lab[0]): out[f] = {'value': fv, 'source': ar_src, 'read_by': ar_rb, 'state': 'confirmed', 'second_source': lab[1], 'second_read_by': lab[2]}
        elif fv and lab[0]: out[f] = {'value': fv, 'source': ar_src, 'read_by': ar_rb, 'state': 'conflict', 'conflict': {'value': lab[0], 'source': lab[1], 'read_by': lab[2]}}
        elif fv: out[f] = {'value': fv, 'source': ar_src, 'read_by': ar_rb, 'state': 'sourced'}
        elif lab[0]: out[f] = {'value': lab[0], 'source': lab[1], 'read_by': lab[2], 'state': 'filled'}
    if p.get('hq_city'): out['hq_city'] = {'value': p['hq_city'], 'source': p.get('hq_city_source'), 'read_by': PL, 'state': 'filled'}
    return out
if __name__ == '__main__':
    rows = all_rows(); res = [decide(r) for r in rows]
    with open('raw/confirm.jsonl', 'w', encoding='utf-8') as f:
        for d in res: f.write(json.dumps(d, ensure_ascii=False) + '\n')
    conflicts = [(d['key'], fld, d[fld]) for d in res for fld in ('auditor', 'registrar') if d.get(fld, {}).get('state') == 'conflict']
    print('confirm:', {s: sum(1 for d in res for fld in ('auditor', 'registrar') if d.get(fld, {}).get('state') == s) for s in ('confirmed', 'sourced', 'filled', 'conflict')}, 'conflicts to review', len(conflicts), flush=True)
    done = {d.get('key') for d in jload('raw/mistral_review.jsonl')}; out = open('raw/mistral_review.jsonl', 'a', encoding='utf-8')
    for k, fld, d in conflicts:
        kk = f'{k}|{fld}'
        if kk in done: continue
        m = mistral(f"Review only. Two sources name the {fld} of a Hong Kong-listed issuer ({k}). Filing (annual report Corporate Information page): '{d['value']}'. Lab read: '{d['conflict']['value']}' (page {d['conflict']['source']}). "
                    "Do they name the same firm (a rename, a merged practice, a spelling)? Reply JSON only: {\"same_firm\": true|false, \"note\": \"<one line>\"}.")
        j = jparse(m.get('text')) or {}
        out.write(json.dumps({'key': kk, 'review': j, 'usage': m.get('usage'), 'model': m.get('model'), 'error': m.get('error')}, ensure_ascii=False) + '\n'); out.flush()
    print('mistral review written', flush=True)
