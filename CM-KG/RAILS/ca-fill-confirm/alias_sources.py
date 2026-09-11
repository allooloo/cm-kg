"""Pass 2.1 — 'Also known as', sourced only. Three sources, each cited:
   (1) GLEIF other entity names on the issuer's LEI record (raw/gleif_names.jsonl)            read-by: GLEIF LEI record (other entity names)
   (2) the name the issuer's own wire company page displays (Cision / PR Newswire <h1>, Newsfile page path)  read-by: <wire> company page
   (3) the exchange profile name (TMX directory name / instrument names, CSE company page title)          read-by: exchange list / exchange site
Never a guess. An alias equal to the legal name (after normalisation) is not an alias."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
gleif = {d['lei']: d for d in jload('raw/gleif_names.jsonl')}
wp = {d['key']: d for d in jload(W1 + r'\wire_pages.jsonl')}
cse = {d['key']: d for d in jload('raw/width0/enr_cse.jsonl') if 'error' not in d}
roster = {r['exchange'] + '|' + r['symbol']: r for r in json.load(open('raw/width0/roster.json', encoding='utf-8'))}
def same(a, b): return norm(a).replace(' ', '') == norm(b).replace(' ', '')
def clean(s): return re.sub(r'\s+', ' ', html.unescape(s or '')).strip(' -–|')
def wire_page_name(url):
    if 'newsfilecorp.com/company/' in url:
        m = re.search(r'/company/\d+/([^/?]+)', url); return (clean(m.group(1).replace('-', ' ')) if m else ''), 'newsfilecorp.com company page (page path)'
    x = get(url, tries=2, timeout=40)
    name = cision_page_name(x.text) if x is not None and x.status_code == 200 else ''
    return name, ('newswire.ca company page' if 'newswire.ca' in url else 'prnewswire.com company page')
def fetch(r):
    k = key(r); out = []
    g = gleif.get(r.get('lei') or '')
    if g:
        for o in g['other']:
            if o['name'] and not same(o['name'], r['name']): out.append({'alias': clean(o['name']), 'source': f"https://api.gleif.org/api/v1/lei-records/{r['lei']}", 'read_by': 'GLEIF LEI record (other entity names)', 'kind': o.get('type') or ''})
    p = wp.get(k, {})
    if p.get('page'):
        nm, rb = wire_page_name(p['page'])
        if nm and not same(nm, r['name']): out.append({'alias': nm, 'source': p['page'], 'read_by': rb, 'kind': 'WIRE_COMPANY_PAGE'})
    ro = roster.get(k, {})
    if ro.get('name') and not same(ro['name'], r['name']): out.append({'alias': clean(ro['name']), 'source': ro.get('roster_src', ''), 'read_by': 'exchange list (directory name)', 'kind': 'EXCHANGE_PROFILE'})
    c = cse.get(k, {})
    if c.get('page') and c.get('title') and not same(c['title'], r['name']): out.append({'alias': clean(c['title']), 'source': c['page'], 'read_by': 'thecse.com company page (title)', 'kind': 'EXCHANGE_PROFILE'})
    # dedupe by normalised alias
    seen = {};
    for a in out:
        kk = norm(a['alias']).replace(' ', '')
        if kk and kk not in seen and len(a['alias']) >= 3: seen[kk] = a
    return {'aliases': list(seen.values()), 'n': len(seen)}
if __name__ == '__main__':
    resume('aliases', fetch, issuers, threads=int(E.get('THREADS', '5')))
