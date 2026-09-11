"""Pass 2.1 — 'Also known as', sourced only. Four sources, each cited:
   (1) Companies House previous company names (REST API profile: previous_company_names; bulk-file previous names when the API row is absent)   read-by: Companies House REST API (previous names)
   (2) GLEIF other entity names on the issuer's LEI record (Width 0 lei_records)                                                                 read-by: GLEIF LEI record (other entity names)
   (3) the name the issuer's own regulatory-news page displays (Investegate company page <h1>/<title>)                                            read-by: investegate.co.uk company page (display name)
   (4) the exchange profile display name (LSE issuer profile 'issuername' / Aquis company record name) when it differs from the roster legal name  read-by: LSE issuer profile (display name) / aquis.eu company page data (name)
Never a guess. An alias equal to the legal name after normalisation is not an alias. Writes raw/aliases.jsonl and raw/aliases.json (key -> [alias,...]) for the Width 1 assembler."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
chapi = {d['key']: d for d in jload(W0 + r'\ch_api.jsonl')}
chm = {d['key']: d for d in jload(W0 + r'\ch_match.jsonl')}
lei = {d['key']: d for d in jload(W0 + r'\lei_records.jsonl')}
prof = {d['issuercode']: d for d in jload(W0 + r'\lse_issuer.jsonl')}
roster = {r['exchange'] + '|' + r['symbol']: r for r in json.load(open(W0 + r'\roster.json', encoding='utf-8'))}
inv = {d['key']: d for d in jload(W1 + r'\investegate.jsonl')}
def same(a, b): return norm(a).replace(' ', '') == norm(b).replace(' ', '')
def clean(s): return re.sub(r'\s+', ' ', html.unescape(s or '')).strip(' -–|')
def investegate_name(url):
    x = get(url, tries=2, timeout=40)
    if x is None or x.status_code != 200: return ''
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', x.text, re.S)
    t = clean(re.sub(r'<[^>]+>', '', h1.group(1))) if h1 else ''
    t = re.sub(r'(?i)\s*(regulatory news|rns announcements|announcements|news).*$', '', t).strip()
    t = re.sub(r'\s*\([A-Z0-9.\-]{1,8}\)\s*$', '', t).strip()  # the page shows "<display name> (<TIDM>)"; the TIDM is not part of the name
    if not t:
        tt = re.search(r'<title>(.*?)</title>', x.text, re.S)
        t = clean(tt.group(1)).split('|')[0].strip() if tt else ''
        t = re.sub(r'(?i)\s*(regulatory news|rns announcements).*$', '', t).strip()
    return t
def fetch(r):
    k = key(r); out = []
    a = chapi.get(k, {}); p = a.get('profile') or {}
    if a.get('number'):
        for pn in p.get('previous_names') or []:
            if pn and not same(pn, r['name']): out.append({'alias': clean(pn).title() if pn.isupper() else clean(pn), 'source': f"https://find-and-update.company-information.service.gov.uk/company/{a['number']}", 'read_by': 'Companies House REST API (previous names)', 'kind': 'PREVIOUS_NAME'})
    elif (chm.get(k) or {}).get('profile'):
        c = chm[k]
        for pn in c['profile'].get('previous_names') or []:
            nm = pn.get('name') if isinstance(pn, dict) else pn
            if nm and not same(nm, r['name']): out.append({'alias': clean(nm).title(), 'source': c.get('profile_src', ''), 'read_by': 'Companies House bulk data product (previous names)', 'kind': 'PREVIOUS_NAME'})
    g = lei.get(r.get('lei') or '')
    if g:
        for o in g.get('other_names') or []:
            if o and not same(o, r['name']): out.append({'alias': clean(o), 'source': g['src'], 'read_by': 'GLEIF LEI record (other entity names)', 'kind': 'OTHER_NAME'})
    i = inv.get(k, {})
    if i.get('page'):
        nm = investegate_name(i['page'])
        if nm and len(nm) >= 3 and not same(nm, r['name']): out.append({'alias': nm, 'source': i['page'], 'read_by': 'investegate.co.uk company page (display name)', 'kind': 'NEWS_PAGE_NAME'})
    ro = roster.get(k, {})
    dn = ro.get('name_display') or ''
    if dn and not same(dn, r['name']): out.append({'alias': clean(dn), 'source': ro.get('profile_src', ''), 'read_by': 'LSE issuer profile (display name)' if r['exchange'] != 'Aquis Stock Exchange' else 'aquis.eu company page data (name)', 'kind': 'EXCHANGE_PROFILE'})
    seen = {}
    for x in out:
        kk = norm(x['alias']).replace(' ', '')
        if kk and kk not in seen and len(x['alias']) >= 3 and not same(x['alias'], r['name']): seen[kk] = x
    return {'aliases': list(seen.values()), 'n': len(seen)}
if __name__ == '__main__':
    resume('aliases', fetch, issuers, threads=int(E.get('THREADS', '5')))
    al = {}
    for d in jload('raw/aliases.jsonl'):
        if d.get('aliases'): al[d['key']] = [a['alias'] for a in d['aliases']]
    json.dump(al, open(W1 + r'\aliases.json', 'w', encoding='utf-8'), ensure_ascii=False); json.dump(al, open('raw/aliases.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('issuers with aliases', len(al), 'aliases', sum(len(v) for v in al.values()))
