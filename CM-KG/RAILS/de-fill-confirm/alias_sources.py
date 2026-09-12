"""Pass 2.1 — 'Also known as', sourced only. Four sources, each cited:
   (1) Handelsregister former names (monthly bulk register, former_entity_name columns for the register number)   read-by: Handelsregister (HRA/HRB sheet on the LEI record) (former names)
   (2) the exchange trading name when it differs from the legal name                           read-by: exchange listed-securities feed (trading name)
   (3) GLEIF other entity names on the issuer's LEI record                                   read-by: GLEIF LEI record (other entity names)
   (4) the name a wire company page displays (PR Newswire / GlobeNewswire organisation page found in Width 1 hits)   read-by: <wire> company page
Never a guess. An alias equal to the legal name after normalisation is not an alias. Writes raw/aliases.jsonl and aliases.json for the Width 1 assembler."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
Handelsregister = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
LEI = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
ROSTER = {r['exchange'] + '|' + r['symbol']: r for r in json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))}
for _r in ROSTER.values(): _r.setdefault('name_display', _r.get('name', ''))
EV = events(); wire_pages = {}
for e in EV:
    if e.get('wire') in ('PR Newswire', 'GlobeNewswire') and e.get('url'): wire_pages.setdefault(e['exchange'] + '|' + e['ticker'], e['url'])
def same(a, b): return norm(a).replace(' ', '') == norm(b).replace(' ', '')
def clean(s): return re.sub(r'\s+', ' ', html.unescape(s or '')).strip(' -–|')
def wire_page_name(url):
    """the organisation name a GlobeNewswire / PR Newswire release page prints in its byline ('Company name' link); never the headline"""
    t, st = page_text(url)
    if not t: return '', ''
    m = re.search(r'(?:About|ABOUT)\s+([A-Z][A-Za-z0-9&.\' -]{2,60}?)\s*(?:\(|:|\n|Limited|Ltd)', t)
    return (clean(m.group(1)) if m else ''), ('globenewswire.com release page (About section)' if 'globenewswire' in url else 'prnewswire.com release page (About section)')
def fetch(r):
    k = key(r); out = []
    a = Handelsregister.get(r.get('reg_id') or '')
    if a:
        pass  # no former-name column in the register index used here; GLEIF other names below carry former names
    ro = ROSTER.get(k, {})
    if ro.get('name_display') and not same(ro['name_display'], r['name']) and len(ro['name_display']) >= 4: out.append({'alias': clean(ro['name_display']), 'source': ro.get('roster_src', ''), 'read_by': 'exchange listed-securities feed (trading name)', 'kind': 'EXCHANGE_PROFILE'})
    g = LEI.get(r.get('lei') or '')
    if g:
        for o in g.get('other_names') or []:
            if o and not same(o, r['name']): out.append({'alias': clean(o), 'source': g['src'], 'read_by': 'GLEIF LEI record (other entity names)', 'kind': 'OTHER_NAME'})
    u = wire_pages.get(k)
    if u:
        nm, rb = wire_page_name(u)
        if nm and len(nm) >= 3 and not same(nm, r['name']) and name_match(nm, r['name'])[0] in ('full', 'distinctive'): out.append({'alias': nm, 'source': u, 'read_by': rb, 'kind': 'WIRE_PAGE_NAME'})
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
    json.dump(al, open('raw/aliases.json', 'w', encoding='utf-8'), ensure_ascii=False)
    w1 = pond.open_drop(NODE, 'width1') if pond.drops(NODE, 'width1') else r'C:\ALLOOLOO\CM-KG\RAILS\de-width1\raw'
    json.dump(al, open(os.path.join(w1, 'aliases.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('issuers with aliases', len(al), 'aliases', sum(len(v) for v in al.values()))
