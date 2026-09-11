"""Pass 3 — Confirm. Every filled or sourced identity field gets a second, independent source where one exists:
  ISIN            second = the GLEIF mapping file (ISIN -> an LEI whose legal name is the issuer) or a second quote page (Tavily) carrying the ISIN with the issuer name
  LEI             second = Companies House number on the LEI record equals the issuer's Companies House number (registry cross-check), else the mapping file vs name-exact
  CH number       second = the GLEIF record's registeredAs equals the number (when the number came from the name route) or the API name search returns the same number (when it came from the LEI route)
  Registrar       second = a second page on a different domain naming the same registrar (Tavily, different phrasing), the Aquis record, a Gemini RNS read, or the ChatGPT accounts read
  Auditor         second = the ChatGPT accounts read (independent of the page-text regex), or a second page on a different domain
  Newswire        second = the dominant wire in the issuer's Width 1 event set (an independent 12-month observation)
  Jurisdiction    second = GLEIF legal jurisdiction vs the Companies House jurisdiction field / number prefix (both must exist)
  Alias           second = two alias sources naming the same alias
Agree -> confirmed (both cited). Disagree -> conflict (Claude adjudicates from the two sources in rebuild). One source only -> sourced/filled.
Writes raw/confirm_fields.jsonl (one row per issuer with per-field state, second source, read-by)."""
import re
from fc_common import *
from collections import Counter
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['Ticker (TIDM)']: r for r in all_rows()}
isin_lei = json.load(open(W0 + r'\isin_lei_hits.json')); lei_rec = {d['key']: d for d in jload(W0 + r'\lei_records.jsonl')}
chapi = {d['key']: d for d in jload(W0 + r'\ch_api.jsonl')}
claude_lei = {d['key']: d for d in jload('raw/claude_lei.jsonl')}; claude_ch = {d['key']: d for d in jload('raw/claude_ch.jsonl')}; claude_aud = {d['key']: d for d in jload('raw/claude_auditor.jsonl')}
gem = {d['key']: d for d in jload('raw/gemini_agm.jsonl')}
parts = json.load(open('raw/openai_accounts_parts.json')) if os.path.exists('raw/openai_accounts_parts.json') else {}
acc = {}
for d in jload('raw/chatgpt_accounts.jsonl'):
    num = d['custom_id'].rsplit('_', 2)[0]; acc.setdefault(num, []).append(d)
def accounts_read(k):
    """merged ChatGPT accounts read for an issuer key: first non-empty auditor across parts; disagreement noted"""
    num = next((n for n, m in parts.items() if m.get('key') == k), None)
    if not num or num not in acc: return {}
    auds = [d.get('auditor') for d in acc[num] if d.get('auditor')]; regs = [d.get('registrar') for d in acc[num] if d.get('registrar')]
    pe = [d.get('period_end') for d in acc[num] if d.get('period_end')]; gc = [d.get('going_concern') for d in acc[num] if d.get('going_concern') == 'material_uncertainty']
    return {'number': num, 'auditor': auds[0] if auds else '', 'auditor_all': auds, 'registrar': regs[0] if regs else '', 'period_end': pe[0] if pe else '', 'going_concern': 'material_uncertainty' if gc else ('none_stated' if acc[num] else ''), 'evidence': next((d.get('evidence') for d in acc[num] if d.get('auditor')), ''), 'document_url': parts[num].get('document_url', ''), 'filing_date': parts[num].get('filing_date', '')}
ALIASES = all_aliases()
EV = events(); wire_by = {}
for e in EV:
    if e.get('wire') and 'Companies House' not in e.get('read_by', ''): wire_by.setdefault(e['exchange'] + '|' + e['ticker'], Counter())[e['wire'].split(' (')[0]] += 1
_src = open(r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0\enrich.py', encoding='utf-8').read()
REG_LIST = eval(re.search(r'^REG_LIST = (\[.*?\])\s*$', _src, re.M | re.S).group(1))
_src2 = open(r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0\assemble.py', encoding='utf-8').read()
KNOWN_AUD = eval(re.search(r'^KNOWN_AUD = (\[.*?\])\s*$', _src2, re.M | re.S).group(1))
def canon_aud(name):
    for canon, pat in KNOWN_AUD:
        if re.search(pat, name or ''): return canon
    return name or ''
def canon_reg(name):
    for label, pat in REG_LIST:
        if re.search(pat, name or ''): return label
    return name or ''
def firm_key(s): return norm(canon_aud(s)).split()[0] if s and norm(canon_aud(s)).split() else ''
def reg_key(s): return norm(canon_reg(s)).split()[0] if s and norm(canon_reg(s)).split() else ''
def dom(u): return '.'.join(re.sub(r'^https?://', '', u).split('/')[0].split('.')[-2:]) if u else ''
def second_read(r, kind):
    q = f"{r['name']} share registrar" if kind == 'reg' else f"{r['name']} independent auditor statutory auditor"
    j = tavily({'query': q, 'max_results': 6, 'include_raw_content': True}); found = []
    for x in j.get('results', []):
        txt = (x.get('raw_content') or '') + '\n' + (x.get('content') or '')
        if name_match(txt[:5000], r['name'])[0] not in ('full', 'distinctive'): continue
        if kind == 'reg':
            for m in re.finditer(r'(?i)\bregistrars?\b', txt):
                win = txt[max(0, m.start() - 300):m.end() + 300]
                for label, pat in REG_LIST:
                    if re.search(pat, win): found.append((label, x['url'])); break
        else:
            for m in re.finditer(r"[Aa]uditors?\s+(?:of\s+the\s+(?:Company|Group)\s+)?(?:is|are|were|was|:|,)?\s*([A-Z][\w&.'’\- ]{2,60}?\s(?:LLP|Limited|Ltd\.?|Inc\.?))", txt):
                found.append((canon_aud(m.group(1).strip()), x['url']))
    return found
def confirm_issuer(r):
    k = key(r); row = rows.get(k, {}); out = {'fields': {}}; rec = lei_rec.get(row.get('LEI') or '', {})
    # ISIN
    v = row.get('ISIN') or ''
    if v:
        m = isin_lei.get(v, '').split('|')[0]; mrec = lei_rec.get(m, {})
        if m and mrec and (row.get('LEI State') or '') != 'conflict': out['fields']['ISIN'] = {'state': 'confirmed', 'second': ['https://mapping.gleif.org/api/v2/isin-lei/latest'], 'read_by2': 'GLEIF ISIN-to-LEI mapping file carries this ISIN against the issuer\'s LEI'}
        else:
            j = tavily({'query': f"{r['name']} {r['ticker']} ISIN", 'max_results': 5, 'include_raw_content': True})
            hits = [x['url'] for x in j.get('results', []) if v in ((x.get('raw_content') or '') + (x.get('content') or '')) and dom(x['url']) not in ('londonstockexchange.com',) and name_match((x.get('raw_content') or '')[:5000] + x['title'], r['name'])[0] in ('full', 'distinctive')]
            out['fields']['ISIN'] = {'state': 'confirmed', 'second': hits[:1], 'read_by2': 'Tavily second read (quote page carrying the ISIN with the issuer name)'} if hits else {'state': 'sourced', 'second': [], 'read_by2': ''}
    # LEI
    v = row.get('LEI') or ''; cl = claude_lei.get(k, {})
    if (row.get('LEI State') or '') == 'conflict':
        if cl.get('ruling'): out['fields']['LEI'] = {'state': 'filled', 'value': cl['ruling'], 'second': [cl.get('source', '')], 'read_by2': 'adjudicated by Claude: ' + (cl.get('reason') or '')[:120]}
        else: out['fields']['LEI'] = {'state': 'conflict', 'second': [f"mapping-file LEI {cl.get('mapped_lei', '')} is {cl.get('mapped_lei_is', 'unclear')}"], 'read_by2': 'adjudicated by Claude: unsettled — ' + (cl.get('reason') or '')[:120]}
    elif v:
        chn = row.get('Companies House number') or ''
        if rec.get('registeredAt') == 'RA000585' and chn and rec.get('registeredAs', '').strip().upper().zfill(8) == chn.zfill(8) and 'name-exact' in (row.get('Companies House read by') or '') + (row.get('LEI read by') or ''):
            out['fields']['LEI'] = {'state': 'confirmed', 'second': [row.get('Companies House profile link', '')], 'read_by2': 'Companies House number on the LEI record equals the name-exact Companies House match'}
        elif isin_lei.get(row.get('ISIN') or '', '').split('|')[0] == v and 'name-exact' in (row.get('LEI read by') or ''): out['fields']['LEI'] = {'state': 'confirmed', 'second': ['https://mapping.gleif.org/api/v2/isin-lei/latest'], 'read_by2': 'GLEIF ISIN-to-LEI mapping file agrees with the name-exact match'}
        elif 'mapping file' in (row.get('LEI read by') or '') and rec.get('registeredAt') == 'RA000585' and chn and rec.get('registeredAs', '').strip().upper().zfill(8) == chn.zfill(8) and 'REST API company search' in (row.get('Companies House read by') or ''):
            out['fields']['LEI'] = {'state': 'confirmed', 'second': [row.get('Companies House profile link', '')], 'read_by2': 'Companies House API name search returned the number the LEI record carries'}
        else: out['fields']['LEI'] = {'state': 'sourced', 'second': [], 'read_by2': 'no second independent LEI source for this row'}
    # Companies House number
    v = row.get('Companies House number') or ''; cc = claude_ch.get(k, {})
    if v:
        rb = row.get('Companies House read by') or ''
        if 'LEI record' in rb:
            a = chapi.get(k, {}); found = [it.get('company_number') for it in (a.get('candidates') or [])] if a else []
            out['fields']['Companies House number'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
            if (cc.get('ruling') or '') == v: out['fields']['Companies House number'] = {'state': 'confirmed', 'second': [cc.get('source', '')], 'read_by2': 'Companies House API name search, adjudicated by Claude, returns the same number'}
        elif rec.get('registeredAs', '').strip().upper().zfill(8) == v.zfill(8): out['fields']['Companies House number'] = {'state': 'confirmed', 'second': [rec.get('src', '')], 'read_by2': 'GLEIF LEI record registeredAs equals the name-matched number'}
        else: out['fields']['Companies House number'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    elif cc.get('ruling'): out['fields']['Companies House number'] = {'state': 'filled', 'value': cc['ruling'], 'second': [cc.get('source', '')], 'read_by2': 'adjudicated by Claude: ' + (cc.get('reason') or '')[:120]}
    # Registrar
    v = row.get('Registrar') or ''; g = gem.get(k, {}); ar = accounts_read(k)
    reads = []
    if g.get('registrar'): reads.append((canon_reg(g['registrar']), g.get('registrar_url', ''), 'read by Gemini (RNS set)'))
    if ar.get('registrar'): reads.append((canon_reg(ar['registrar']), ar.get('document_url', ''), 'read by ChatGPT (batch) — accounts'))
    if v:
        first_dom = dom(row.get('Registrar source') or '')
        agree = [(u, rb) for lab, u, rb in reads if reg_key(lab) == reg_key(v)]
        if not agree:
            found = [(lab, u) for lab, u in second_read(r, 'reg') if dom(u) != first_dom]
            agree = [(u, 'Tavily second read (different domain) + regex') for lab, u in found if reg_key(lab) == reg_key(v)]
            disagree = Counter(lab for lab, u in found if reg_key(lab) != reg_key(v))
        else: disagree = Counter()
        dis2 = [lab for lab, u, rb in reads if reg_key(lab) != reg_key(v)]
        if agree: out['fields']['Registrar'] = {'state': 'confirmed', 'second': [agree[0][0]], 'read_by2': agree[0][1]}
        elif dis2: out['fields']['Registrar'] = {'state': 'conflict', 'second': dis2[:2], 'read_by2': 'a lab read names a different registrar'}
        elif disagree and disagree.most_common(1)[0][1] >= 2: out['fields']['Registrar'] = {'state': 'conflict', 'second': [f'{lab} ({n} pages)' for lab, n in disagree.most_common(2)], 'read_by2': 'Tavily second read names a different registrar'}
        else: out['fields']['Registrar'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    elif reads: out['fields']['Registrar'] = {'state': 'filled', 'value': reads[0][0], 'second': [reads[0][1]], 'read_by2': reads[0][2]}
    # Auditor
    v = row.get('Auditor') or ''; ca = claude_aud.get(k, {})
    if not v and ca.get('ruling'): v = ca['ruling']; out['fields']['Auditor'] = {'state': 'filled', 'value': v, 'second': [ca.get('source', '')], 'read_by2': 'adjudicated by Claude'}
    if v:
        if ar.get('auditor'):
            if firm_key(ar['auditor']) == firm_key(v): out['fields']['Auditor'] = {**out['fields'].get('Auditor', {}), 'state': 'confirmed', 'second': [ar['document_url']], 'read_by2': 'read by ChatGPT (batch) — accounts filing agrees'}
            else: out['fields']['Auditor'] = {**out['fields'].get('Auditor', {}), 'state': 'conflict', 'second': [f"{ar['auditor']} ({ar['document_url']})"], 'read_by2': 'read by ChatGPT (batch) — accounts filing names a different firm'}
        else:
            first_dom = dom(row.get('Auditor source') or '')
            found = [(lab, u) for lab, u in second_read(r, 'aud') if dom(u) != first_dom]
            agree = [u for lab, u in found if firm_key(lab) == firm_key(v)]; disagree = Counter(lab for lab, u in found if firm_key(lab) != firm_key(v))
            if agree: out['fields']['Auditor'] = {**out['fields'].get('Auditor', {}), 'state': 'confirmed', 'second': agree[:1], 'read_by2': 'Tavily second read (different domain) + regex'}
            elif disagree and disagree.most_common(1)[0][1] >= 2: out['fields']['Auditor'] = {**out['fields'].get('Auditor', {}), 'state': 'conflict', 'second': [f'{lab} ({n} pages)' for lab, n in disagree.most_common(2)], 'read_by2': 'Tavily second read names a different firm'}
            elif 'Auditor' not in out['fields']: out['fields']['Auditor'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    elif ar.get('auditor'): out['fields']['Auditor'] = {'state': 'filled', 'value': canon_aud(ar['auditor']) if canon_aud(ar['auditor']) in set(c for c, _ in KNOWN_AUD) else ar['auditor'], 'second': [ar['document_url']], 'read_by2': 'read by ChatGPT (batch) — accounts filing', 'evidence': ar.get('evidence', '')}
    # Newswire
    v = (row.get('Newswire of habit') or '').split(' (')[0]
    c = wire_by.get(k)
    if v and c:
        top, n = c.most_common(1)[0]
        if norm(top).split()[0] == norm(v).split()[0]: out['fields']['Newswire of habit'] = {'state': 'confirmed', 'second': [f'Width 1 events: {n} of {sum(c.values())} announcements via {top}'], 'read_by2': 'Width 1 12-month event set (independent observation)'}
        else: out['fields']['Newswire of habit'] = {'state': 'conflict', 'second': [f'Width 1 events: {top} {n} of {sum(c.values())}'], 'read_by2': 'Width 1 12-month event set disagrees'}
    elif v: out['fields']['Newswire of habit'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    elif c:
        top, n = c.most_common(1)[0]
        if n >= 2 and n / sum(c.values()) >= 0.5: out['fields']['Newswire of habit'] = {'state': 'filled', 'value': top, 'second': [f'Width 1 events: {n} of {sum(c.values())}'], 'read_by2': 'Width 1 12-month event set (majority wire)'}
    # Jurisdiction
    v = row.get('Incorporation jurisdiction') or ''
    if v:
        g_j = rec.get('jur') or ''
        if g_j and 'Companies House' in (row.get('Jurisdiction read by') or ''):
            ok = (g_j.startswith('GB') and re.search(r'England|Scotland|Northern Ireland|United Kingdom|Wales', v)) or (g_j[:2] in v)
            out['fields']['Incorporation jurisdiction'] = {'state': 'confirmed' if ok else 'conflict', 'second': [rec.get('src', '')], 'read_by2': ('GLEIF legal jurisdiction agrees' if ok else f'GLEIF legal jurisdiction {g_j} disagrees')}
        else: out['fields']['Incorporation jurisdiction'] = {'state': 'sourced', 'second': [], 'read_by2': ''}
    # Alias
    al = ALIASES.get(k, [])
    if al:
        cnt = Counter(norm(a['alias']).replace(' ', '') for a in al); multi = [a for a in al if cnt[norm(a['alias']).replace(' ', '')] >= 2]
        out['fields']['Also known as'] = {'state': 'confirmed' if multi else 'sourced', 'second': [multi[0]['source']] if multi else [], 'read_by2': 'two alias sources agree' if multi else ''}
    out['accounts'] = ar
    return out
if __name__ == '__main__':
    resume('confirm_fields', confirm_issuer, issuers, threads=int(E.get('THREADS', '6')))
