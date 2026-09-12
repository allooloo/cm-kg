"""Pass 3 — Confirm. Every filled or sourced identity field gets a second, independent source where one exists:
  ISIN            second = the GLEIF mapping file (ISIN -> the issuer's LEI) or a second quote page (Tavily) carrying the ISIN with the issuer name
  LEI             second = the register number on the LEI record (registeredAs at Handelsregister) equals the register row, else the mapping file vs name-exact
  register number / ABN       second = the GLEIF record's registeredAs equals the register number (when the register number came from the name route), or Claude's ruling agrees (when from the LEI route)
  Share registry  second = the ChatGPT annual-report read, a Gemini read, or a second page on a different domain (Tavily)
  Auditor         second = a second page on a different domain naming the same firm (the annual report read is the first source)
  Newswire        second = the dominant channel in the Width 1 event set (an independent 12-month observation)
  State           second = GLEIF legal-address region vs the Handelsregister state of registration / the GLEIF address
  Alias           second = two alias sources naming the same alias
Agree -> confirmed (both cited). Disagree -> conflict (Claude adjudicates in conflict_adjudicate.py). One source only -> sourced/filled.
Writes raw/confirm_fields.jsonl (one row per issuer with per-field state, second source, read-by)."""
import re
from fc_common import *
from collections import Counter
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Symbol']: r for r in all_rows()}
isin_lei = pond.read_json_latest(NODE, 'width0', 'isin_lei_hits.json') or {}; lei_rec = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
Handelsregister = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
claude_lei = {d['key']: d for d in jload('raw/claude_lei.jsonl')}; claude_acn = {d['key']: d for d in jload('raw/claude_acn.jsonl')}
gem = {d['key']: d for d in jload('raw/gemini_agm.jsonl')}
rep = {}
for d in jload('raw/chatgpt_reports.jsonl'):
    if d.get('key') and not d.get('error'): rep.setdefault(d['key'], []).append(d)
def report_read(k):
    ds = sorted(rep.get(k, []), key=lambda d: (d.get('kind') != 'annual_report', d.get('date') or ''), reverse=False)
    ar = [d for d in ds if d.get('kind') == 'annual_report'] or ds
    if not ar: return {}
    d = ar[0]
    return {'auditor': d.get('auditor') or '', 'registry': d.get('registry') or '', 'period_end': d.get('period_end') or '', 'going_concern': d.get('going_concern') or '', 'evidence': d.get('evidence') or '', 'document_url': d.get('document_url') or '', 'date': d.get('date') or '', 'kind': d.get('kind')}
ALIASES = all_aliases()
EV = events(); wire_by = {}
for e in EV:
    if e.get('wire') and 'Handelsregister' not in e.get('read_by', '') and 'Perplexity' not in e.get('read_by', ''): wire_by.setdefault(e['exchange'] + '|' + e['ticker'], Counter())[e['wire'].split(' (')[0]] += 1
_src = open(r'C:\ALLOOLOO\CM-KG\RAILS\de-width0\enrich.py', encoding='utf-8').read()
REG_LIST = eval(re.search(r'^REG_LIST = (\[.*?\])\s*$', _src, re.M | re.S).group(1))
AUD_FIRMS = [('KPMG', r'\bKPMG\b'), ('Deloitte', r'\bDeloitte\b'), ('PricewaterhouseCoopers', r'PricewaterhouseCoopers|\bPwC\b'), ('Ernst & Young', r'Ernst\s*&\s*Young|\bEY\b'), ('BDO', r'\bBDO\b'), ('Baker Tilly', r'Baker Tilly'), ('Rödl & Partner', r'R[öo]dl'), ('Grant Thornton', r'Grant Thornton'), ('Forvis Mazars', r'Mazars'), ('RSM', r'\bRSM\b'), ('Nexia', r'\bNexia\b'), ('Crowe', r'\bCrowe\b'), ('Ebner Stolz', r'Ebner Stolz'), ('Warth & Klein', r'Warth'), ('PKF', r'\bPKF\b'), ('Dr. Kleeberg', r'Kleeberg'), ('Baker Tilly', r'Baker Tilly'), ('Moore', r'\bMoore\b'), ('ETL', r'\bETL\b'), ('Kreston', r'Kreston')]
def firm_key(s):
    for canon, pat in AUD_FIRMS:
        if re.search(pat, s or ''): return canon.lower()
    return norm(s).split()[0] if s and norm(s).split() else ''
def reg_key(s):
    for label, pat in REG_LIST:
        if re.search(pat, s or ''): return label.lower().split()[0]
    return norm(s).split()[0] if s and norm(s).split() else ''
def dom(u): return '.'.join(re.sub(r'^https?://', '', u).split('/')[0].split('.')[-2:]) if u else ''
def second_read(r, kind):
    q = f"{r['name']} share registry" if kind == 'reg' else f"{r['name']} auditor independent audit report"
    j = tavily({'query': q, 'max_results': 6, 'include_raw_content': True}); found = []
    for x in j.get('results', []):
        txt = (x.get('raw_content') or '') + '\n' + (x.get('content') or '')
        if name_match(txt[:5000], r['name'])[0] not in ('full', 'distinctive'): continue
        if kind == 'reg':
            for m in re.finditer(r'(?i)\bshare regist(?:ry|rar)\b|\bregistry\b', txt):
                win = txt[max(0, m.start() - 300):m.end() + 300]
                for label, pat in REG_LIST:
                    if re.search(pat, win): found.append((label, x['url'])); break
        else:
            for m in re.finditer(r"[Aa]uditors?\s+(?:of\s+the\s+(?:Company|Group)\s+)?(?:is|are|were|was|:|,)?\s*([A-Z][\w&.'’\- ]{2,60}?)(?:\s+(?:Pty|Ltd|Limited|Partners|LLP|Chartered)|[.,])", txt):
                found.append((m.group(1).strip(), x['url']))
    return found
def confirm_issuer(r):
    k = key(r); row = rows.get(k, {}); out = {'fields': {}}; rec = lei_rec.get(row.get('LEI') or '', {}); rr = report_read(k)
    v = row.get('ISIN') or ''
    if v:
        m = isin_lei.get(v, '').split('|')[0]
        if m and lei_rec.get(m) and (row.get('LEI State') or '') != 'conflict': out['fields']['ISIN'] = {'state': 'confirmed', 'second': ['https://mapping.gleif.org/api/v2/isin-lei/latest'], 'read_by2': "GLEIF ISIN-to-LEI mapping file carries this ISIN against the issuer's LEI"}
        else:
            j = tavily({'query': f"{r['name']} {r['ticker']} ISIN", 'max_results': 5, 'include_raw_content': True})
            hits = [x['url'] for x in j.get('results', []) if v in ((x.get('raw_content') or '') + (x.get('content') or '')) and dom(x['url']) != 'asx.com.au' and name_match((x.get('raw_content') or '')[:5000] + x['title'], r['name'])[0] in ('full', 'distinctive')]
            out['fields']['ISIN'] = {'state': 'confirmed', 'second': hits[:1], 'read_by2': 'Tavily second read (quote page carrying the ISIN with the issuer name)'} if hits else {'state': 'sourced', 'second': [], 'read_by2': ''}
    v = row.get('LEI') or ''; cl = claude_lei.get(k, {})
    if (row.get('LEI State') or '') == 'conflict':
        if cl.get('ruling'): out['fields']['LEI'] = {'state': 'filled', 'value': cl['ruling'], 'second': [cl.get('source', '')], 'read_by2': 'adjudicated by Claude: ' + (cl.get('reason') or '')[:120]}
        else: out['fields']['LEI'] = {'state': 'conflict', 'second': [f"mapping-file LEI {cl.get('mapped_lei', '')} is {cl.get('mapped_lei_is', 'unclear')}"], 'read_by2': 'adjudicated by Claude: unsettled — ' + (cl.get('reason') or '')[:120]}
    elif v:
        acn = row.get('Register number (HR)') or ''; ras = re.sub(r'[^A-Z0-9]', '', (rec.get('registeredAs') or '').upper())
        if rec.get('registeredAt') == ('RA000304', 'RA000259', 'RA000217', 'RA000242') and acn and ras == acn and 'name-exact' in (row.get('Register read by') or '') + (row.get('LEI read by') or ''): out['fields']['LEI'] = {'state': 'confirmed', 'second': [Handelsregister.get(acn, {}).get('src', '')], 'read_by2': 'register number on the LEI record equals the name-exact register row'}
        elif isin_lei.get(row.get('ISIN') or '', '').split('|')[0] == v and 'name-exact' in (row.get('LEI read by') or ''): out['fields']['LEI'] = {'state': 'confirmed', 'second': ['https://mapping.gleif.org/api/v2/isin-lei/latest'], 'read_by2': 'GLEIF ISIN-to-LEI mapping file agrees with the name-exact match'}
        else: out['fields']['LEI'] = {'state': 'sourced', 'second': [], 'read_by2': 'no second independent LEI source for this row'}
    v = row.get('Register number (HR)') or ''; ca = claude_acn.get(k, {})
    if v:
        ras = re.sub(r'[^A-Z0-9]', '', (rec.get('registeredAs') or '').upper())
        if 'LEI record' in (row.get('Register read by') or ''):
            out['fields']['Register number (HR)'] = {'state': 'confirmed', 'second': [ca.get('source', '')], 'read_by2': 'Handelsregister (HRA/HRB sheet on the LEI record) candidates adjudicated by Claude return the same register number'} if (ca.get('ruling') or '') == v else {'state': 'sourced', 'second': [], 'read_by2': ''}
        elif ras == v: out['fields']['Register number (HR)'] = {'state': 'confirmed', 'second': [rec.get('src', '')], 'read_by2': 'GLEIF LEI record registeredAs equals the name-matched register number'}
        else: out['fields']['Register number (HR)'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    elif ca.get('ruling'): out['fields']['Register number (HR)'] = {'state': 'filled', 'value': ca['ruling'], 'second': [ca.get('source', '')], 'read_by2': 'adjudicated by Claude: ' + (ca.get('reason') or '')[:120]}
    # registry
    v = row.get('Share registrar') or ''; g = gem.get(k, {}); reads = []
    if rr.get('registry'): reads.append((rr['registry'], rr['document_url'], 'read by ChatGPT (batch) — annual report'))
    if g.get('registrar'): reads.append((g['registrar'], g.get('registrar_url', ''), 'read by Gemini (announcement set)'))
    if v:
        agree = [(u, rb) for lab, u, rb in reads if reg_key(lab) == reg_key(v)]; dis2 = [lab for lab, u, rb in reads if reg_key(lab) != reg_key(v)]
        if not agree and not dis2:
            first_dom = dom(row.get('Share registrar source') or ''); found = [(lab, u) for lab, u in second_read(r, 'reg') if dom(u) != first_dom]
            agree = [(u, 'Tavily second read (different domain) + regex') for lab, u in found if reg_key(lab) == reg_key(v)]; disagree = Counter(lab for lab, u in found if reg_key(lab) != reg_key(v))
        else: disagree = Counter()
        if agree: out['fields']['Share registrar'] = {'state': 'confirmed', 'second': [agree[0][0]], 'read_by2': agree[0][1]}
        elif dis2: out['fields']['Share registrar'] = {'state': 'conflict', 'second': dis2[:2], 'read_by2': 'a lab read names a different registry'}
        elif disagree and disagree.most_common(1)[0][1] >= 2: out['fields']['Share registrar'] = {'state': 'conflict', 'second': [f'{lab} ({n} pages)' for lab, n in disagree.most_common(2)], 'read_by2': 'Tavily second read names a different registry'}
        else: out['fields']['Share registrar'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    elif reads: out['fields']['Share registrar'] = {'state': 'filled', 'value': reads[0][0], 'second': [reads[0][1]], 'read_by2': reads[0][2]}
    # auditor (first source = the annual report read)
    if rr.get('auditor'):
        first_dom = dom(rr.get('document_url') or ''); found = [(lab, u) for lab, u in second_read(r, 'aud') if dom(u) != first_dom]
        agree = [u for lab, u in found if firm_key(lab) == firm_key(rr['auditor'])]; disagree = Counter(lab for lab, u in found if firm_key(lab) != firm_key(rr['auditor']) and firm_key(lab))
        if agree: out['fields']['Auditor'] = {'state': 'confirmed', 'value': rr['auditor'], 'second': agree[:1], 'read_by2': 'Tavily second read (different domain) + regex'}
        elif disagree and disagree.most_common(1)[0][1] >= 2: out['fields']['Auditor'] = {'state': 'conflict', 'value': rr['auditor'], 'second': [f'{lab} ({n} pages)' for lab, n in disagree.most_common(2)], 'read_by2': 'Tavily second read names a different firm'}
        else: out['fields']['Auditor'] = {'state': 'filled', 'value': rr['auditor'], 'second': [], 'read_by2': ''}
    # newswire
    v = (row.get('Newswire of habit') or '').split(' (')[0]; c = wire_by.get(k)
    if v and c:
        top, n = c.most_common(1)[0]
        if (top == 'EQS News' and v.startswith('EQS News')) or norm(top).split()[0] == norm(v).split()[0]: out['fields']['Newswire of habit'] = {'state': 'confirmed', 'second': [f'Width 1 events: {n} of {sum(c.values())} announcements via {top}'], 'read_by2': 'Width 1 12-month event set (independent observation)'}
        else: out['fields']['Newswire of habit'] = {'state': 'conflict', 'second': [f'Width 1 events: {top} {n} of {sum(c.values())}'], 'read_by2': 'Width 1 12-month event set disagrees'}
    elif v: out['fields']['Newswire of habit'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    # state
    v = row.get('State') or ''
    if v:
        g_reg = (rec.get('legal_region') or ''); a = Handelsregister.get(row.get('Register number (HR)') or '', {})
        alt = (g_reg[3:] if g_reg.startswith('AU-') else '') if 'Handelsregister' in (row.get('State read by') or '') or 'contact' in (row.get('State read by') or '') else (a.get('state') or '')
        if alt:
            ok = alt.upper() in v.upper()
            out['fields']['State'] = {'state': 'confirmed' if ok else 'conflict', 'second': [rec.get('src', '') if g_reg else a.get('src', '')], 'read_by2': ('GLEIF legal-address region agrees' if ok else f'second registry says {alt}') if g_reg or a else ''}
        else: out['fields']['State'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    al = ALIASES.get(k, [])
    if al:
        cnt = Counter(norm(a['alias']).replace(' ', '') for a in al); multi = [a for a in al if cnt[norm(a['alias']).replace(' ', '')] >= 2]
        out['fields']['Also known as'] = {'state': 'confirmed' if multi else 'sourced', 'second': [multi[0]['source']] if multi else [], 'read_by2': 'two alias sources agree' if multi else ''}
    out['report'] = rr
    return out
if __name__ == '__main__':
    resume('confirm_fields', confirm_issuer, issuers, threads=int(E.get('THREADS', '6')))
