"""Pass 3 — Confirm. Every filled or sourced field on the issuer record gets a second, independent source where one exists.
  ISIN         second source = a second quote-page domain carrying the same ISIN for this issuer (Width 0 candidate URLs), else a fresh Tavily read
  LEI          second source = the GLEIF ISIN-to-LEI mapping file agreeing with the name-exact match (the only independent LEI source that answers)
  Transfer agent / Auditor   second source = a second page, on a different domain from the first source, that names the same agent/firm
               (Tavily query with different phrasing; CSE page counts as one source, the regex read as the other)
  Newswire     second source = the dominant wire in the issuer's Width 1 events (an independent 12-month observation)
  Jurisdiction second source = GLEIF record vs the statute phrase read from filings (both must exist)
  Alias        second source = two alias sources naming the same alias
Agree -> confirmed (both sources cited). Disagree -> conflict (Claude adjudicates from the two sources). One source only -> sourced/filled.
Writes raw/confirm_fields.jsonl (one row per issuer with per-field state, second source, read-by)."""
import re
from fc_common import *
from collections import Counter
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Ticker']: r for r in all_rows()}
isin0 = {d['key']: d for d in jload('raw/width0/enr_isin.jsonl')}
corp0 = {d['key']: d for d in jload('raw/width0/enr_corp.jsonl')}
cse0 = {d['key']: d for d in jload('raw/width0/enr_cse.jsonl') if 'error' not in d}
isin_lei = json.load(open('raw/width0/isin_lei_hits.json'))
claude_isin = {d['key']: d for d in jload('raw/claude_isin.jsonl')}
claude_aud = {d['key']: d for d in jload('raw/claude_auditor.jsonl')}
aliases = {d['key']: d.get('aliases', []) for d in jload('raw/aliases.jsonl')}
for k_, a_ in perplexity_aliases().items(): aliases.setdefault(k_, []).append(a_)
for k_, a_ in website_aliases().items(): aliases.setdefault(k_, []).append(a_)
EV = events(); wire_by = {}
for e in EV:
    if e.get('wire'): wire_by.setdefault(e['exchange'] + '|' + e['ticker'], Counter())[e['wire']] += 1
TA_LIST = eval(re.search(r'^TA_LIST = (\[.*?\])\s*$', open(r'C:\ALLOOLOO\CM-KG\RAILS\ca-width0\enrich.py', encoding='utf-8').read(), re.M).group(1))
_src = open(r'C:\ALLOOLOO\CM-KG\RAILS\ca-width0\assemble.py', encoding='utf-8').read()
KNOWN_AUD = eval(re.search(r'^KNOWN_AUD = (\[.*?\])\s*$', _src, re.M).group(1))
def canon_aud(name):
    for canon, pat in KNOWN_AUD:
        if re.search(pat, name, re.I): return canon
    return name
def dom(u): return '.'.join(re.sub(r'^https?://', '', u).split('/')[0].split('.')[-2:]) if u else ''
def second_read(r, kind):
    """a second page (different domain from the first source) naming a transfer agent / auditor for this issuer"""
    q = f"{r['name']} registrar and transfer agent" if kind == 'ta' else f"{r['name']} auditors chartered professional accountants"
    j = tavily({'query': q, 'max_results': 6, 'include_raw_content': True})
    found = []
    for x in j.get('results', []):
        txt = (x.get('raw_content') or '') + '\n' + (x.get('content') or '')
        if name_match(txt[:5000], r['name'])[0] not in ('full', 'distinctive'): continue
        if kind == 'ta':
            for m in re.finditer(r'(?i)transfer agent', txt):
                win = txt[max(0, m.start() - 300):m.end() + 300]
                for label, pat in TA_LIST:
                    if re.search(pat, win): found.append((label, x['url'])); break
        else:
            for m in re.finditer(r"[Aa]uditors?\s+(?:of\s+the\s+(?:Company|Corporation|Trust|Fund)\s+)?(?:is|are|were|was|:|,)?\s*([A-Z][\w&.'’\- ]{2,60}?\s(?:LLP|Inc\.|Ltd\.|S\.E\.N\.C\.R\.L\.|Professional Corporation|CPA))", txt):
                c = canon_aud(m.group(1).strip()); found.append((c, x['url']))
    return found
def confirm_issuer(r):
    k = key(r); row = rows.get(k, {}); out = {'fields': {}}
    # ISIN
    v = row.get('ISIN') or ''; d = isin0.get(k, {})
    if v:
        urls = (d.get('urls') or {}).get(v, []) if isinstance(d.get('urls'), dict) else []
        doms = set(dom(u) for u in urls) | ({dom(row.get('ISIN source') or '')} - {''})
        if len(doms) >= 2: out['fields']['ISIN'] = {'state': 'confirmed', 'second': [u for u in urls if dom(u) != dom(row.get('ISIN source') or '')][:1] or list(doms)[:1], 'read_by2': 'second quote-page domain carrying the same ISIN'}
        else:
            j = tavily({'query': f"{r['name']} {r['root']} ISIN", 'max_results': 5, 'include_raw_content': True})
            hits = [x['url'] for x in j.get('results', []) if v in ((x.get('raw_content') or '') + (x.get('content') or '')) and dom(x['url']) != dom(row.get('ISIN source') or '') and name_match((x.get('raw_content') or '')[:5000] + x['title'], r['name'])[0] in ('full', 'distinctive')]
            others = set()
            for x in j.get('results', []):
                for s in re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}\d\b', (x.get('raw_content') or '')):
                    if s != v and name_match((x.get('raw_content') or '')[:5000], r['name'])[0] == 'full' and s.startswith('CA'): others.add(s)
            if hits: out['fields']['ISIN'] = {'state': 'confirmed', 'second': hits[:1], 'read_by2': 'Tavily second read (different domain)'}
            elif others: out['fields']['ISIN'] = {'state': 'conflict', 'second': sorted(others)[:2], 'read_by2': 'Tavily second read found a different CA ISIN'}
            else: out['fields']['ISIN'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    elif claude_isin.get(k, {}).get('ruling'):
        out['fields']['ISIN'] = {'state': 'filled', 'value': claude_isin[k]['ruling'], 'second': [claude_isin[k].get('source', '')], 'read_by2': 'adjudicated by Claude'}
    # LEI
    v = row.get('LEI') or ''
    if v:
        if isin_lei.get(row.get('ISIN') or '', '').split('|')[0] == v and 'name-exact' in (row.get('LEI read by') or ''): out['fields']['LEI'] = {'state': 'confirmed', 'second': ['https://mapping.gleif.org/api/v2/isin-lei/latest'], 'read_by2': 'GLEIF ISIN-to-LEI mapping file agrees with the name-exact match'}
        elif row.get('ISIN') and isin_lei.get(row['ISIN'], '') and isin_lei[row['ISIN']].split('|')[0] != v: out['fields']['LEI'] = {'state': 'conflict', 'second': [isin_lei[row['ISIN']]], 'read_by2': 'GLEIF ISIN-to-LEI mapping file names a different LEI'}
        else: out['fields']['LEI'] = {'state': 'sourced', 'second': [], 'read_by2': 'no second independent LEI source answers (CA ISINs absent from the GLEIF mapping file)'}
    # Transfer agent / auditor
    for fld, kind, col, srccol in [('Transfer agent', 'ta', 'Transfer agent', 'Transfer agent source'), ('Auditor', 'aud', 'Auditor', 'Auditor source')]:
        v = row.get(col) or ''
        if not v and fld == 'Auditor' and claude_aud.get(k, {}).get('ruling'):
            out['fields'][fld] = {'state': 'filled', 'value': claude_aud[k]['ruling'], 'second': [claude_aud[k].get('source', '')], 'read_by2': 'adjudicated by Claude'}; v = claude_aud[k]['ruling']
        if not v: continue
        first_dom = dom(row.get(srccol) or '')
        found = [(lab, u) for lab, u in second_read(r, kind) if dom(u) != first_dom]
        agree = [u for lab, u in found if norm(lab).split()[0] == norm(v).split()[0]]
        disagree = Counter(lab for lab, u in found if norm(lab).split()[0] != norm(v).split()[0])
        if agree: out['fields'][fld] = {**out['fields'].get(fld, {}), 'state': 'confirmed', 'second': agree[:1], 'read_by2': 'Tavily second read (different domain) + regex'}
        elif disagree and disagree.most_common(1)[0][1] >= 2: out['fields'][fld] = {**out['fields'].get(fld, {}), 'state': 'conflict', 'second': [f'{lab} ({n} pages)' for lab, n in disagree.most_common(2)], 'read_by2': 'Tavily second read names a different ' + ('agent' if kind == 'ta' else 'firm')}
        elif fld not in out['fields']: out['fields'][fld] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    # Newswire
    v = (row.get('Newswire of habit') or '').split(' (')[0]
    if v:
        c = wire_by.get(k)
        if c:
            top, n = c.most_common(1)[0]
            if norm(top).split()[0] == norm(v).split()[0]: out['fields']['Newswire of habit'] = {'state': 'confirmed', 'second': [f'Width 1 events: {n} of {sum(c.values())} releases on {top}'], 'read_by2': 'Width 1 12-month event set (independent observation)'}
            else: out['fields']['Newswire of habit'] = {'state': 'conflict', 'second': [f'Width 1 events: {top} {n} of {sum(c.values())}'], 'read_by2': 'Width 1 12-month event set disagrees'}
        else: out['fields']['Newswire of habit'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    # Jurisdiction
    v = row.get('Incorporation jurisdiction') or ''
    if v:
        c = corp0.get(k, {}); g = 'GLEIF' in (row.get('Jurisdiction read by') or '')
        alt = c.get('jur') if g else ''
        def jkey(s): return re.sub(r'\(.*?\)', '', s).lower().replace('québec', 'quebec').strip()
        if g and alt:
            if jkey(alt) in jkey(v) or jkey(v) in jkey(alt) or ('canada' in jkey(v) and 'cbca' in jkey(alt)): out['fields']['Incorporation jurisdiction'] = {'state': 'confirmed', 'second': [c.get('jur_src', '')], 'read_by2': 'statute phrase in filings (Tavily regex) agrees with GLEIF'}
            else: out['fields']['Incorporation jurisdiction'] = {'state': 'conflict', 'second': [f"{alt} ({c.get('jur_src', '')})"], 'read_by2': 'statute phrase in filings disagrees with GLEIF'}
        else: out['fields']['Incorporation jurisdiction'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    # Alias
    al = aliases.get(k, [])
    if al:
        c = Counter(norm(a['alias']).replace(' ', '') for a in al)
        multi = [a for a in al if c[norm(a['alias']).replace(' ', '')] >= 2]
        out['fields']['Also known as'] = {'state': 'confirmed' if multi else 'sourced', 'second': [multi[0]['source']] if multi else [], 'read_by2': 'two alias sources agree' if multi else ''}
    return out
if __name__ == '__main__':
    resume('confirm_fields', confirm_issuer, issuers, threads=int(E.get('THREADS', '8')))
