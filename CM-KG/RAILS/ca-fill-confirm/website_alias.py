"""Alias channel 4 (standing change, 2026-09-10): the issuer's own website <title>, the site taken from the exchange profile's
website field — TMX Money company record (TSX / TSXV) or the CSE company page (CSE). Sourced or blank: generic titles
('Home', 'Welcome', the bare domain) and titles equal to the legal name yield no alias. Targets: the issuers with zero events
(all corporates when TARGETS=all). Label: 'issuer website <title> (site from exchange profile)'."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
cse = {d['key']: d for d in jload('raw/width0/enr_cse.jsonl') if 'error' not in d}
TMX_UA = {'User-Agent': UA['User-Agent'], 'Content-Type': 'application/json', 'Accept': 'application/json', 'Origin': 'https://money.tmx.com', 'Referer': 'https://money.tmx.com/', 'locale': 'en'}
GENERIC = re.compile(r'^(home|homepage|welcome|index|untitled|default)\b|^\s*$|^(www\.)?[a-z0-9-]+\.(com|ca|net|org|io|ai)\s*$', re.I)
def profile_site(r):
    if r['exchange'] == 'CSE':
        w = cse.get(key(r), {}).get('website') or ''; return w, cse.get(key(r), {}).get('page', '')
    if r['exchange'] in ('TSX', 'TSXV'):
        q = {'query': 'query($symbol:String,$locale:String){ getQuoteBySymbol(symbol:$symbol, locale:$locale){ symbol website } }', 'variables': {'symbol': r['root'], 'locale': 'en'}}
        try:
            j = requests.post('https://app-money.tmx.com/graphql', json=q, headers=TMX_UA, timeout=60).json()
            w = ((j.get('data') or {}).get('getQuoteBySymbol') or {}).get('website') or ''
            return w, f"https://money.tmx.com/en/quote/{r['root']}"
        except Exception: return '', ''
    return '', ''
def clean_title(t, site, legal=''):
    """the name segment of a <title>: split on separators, drop generic segments, ticker suffixes ('CSE: AWR', 'TSX: DBM') and slogans.
    A segment is a name only when it shares a token with the legal name, or is a short brand (one or two words, no comma)."""
    t = re.sub(r'\s+', ' ', html.unescape(t)).strip()
    parts = re.split(r'\s+[|\-–—:·]\s+|\s*·\s*', t)
    parts = [p.strip() for p in parts if p.strip() and not GENERIC.match(p) and not re.match(r'^(TSX|TSXV|CSE|NEO|Cboe|OTC|OTCQB|OTCQX|NYSE|NASDAQ)\b', p, re.I)]
    legal_toks = set(w for w in norm(legal).split() if w not in STOP and len(w) >= 4)
    cands = []
    for p in parts:
        toks = set(norm(p).split())
        shares = bool(toks & legal_toks)
        short_brand = len(p.split()) <= 2 and ',' not in p and not re.search(r'\b(bank|banking|investing|home|welcome|official|site|website)\b', p, re.I)
        if (shares or short_brand) and len(p.split()) <= 8: cands.append(p)
    return max(cands, key=len) if cands else ''
def fetch(r):
    site, src = profile_site(r)
    if not site: return {'website': '', 'alias': '', 'gap': 'exchange profile carries no website'}
    if not site.startswith('http'): site = 'https://' + site
    x = get(site, tries=2, timeout=30)
    if x is None or x.status_code != 200: return {'website': site, 'alias': '', 'gap': f'site http {x.status_code if x else "none"}', 'profile': src}
    body = x.content.decode('utf-8', errors='ignore') if 'charset' not in (x.headers.get('content-type') or '').lower() or 'utf-8' in (x.headers.get('content-type') or '').lower() else x.text
    m = re.search(r'<title[^>]*>(.*?)</title>', body, re.S | re.I)
    if not m: return {'website': site, 'alias': '', 'gap': 'no <title>', 'profile': src}
    name = clean_title(m.group(1), site, r['name'])
    if not name or norm(name).replace(' ', '') == norm(r['name']).replace(' ', ''): return {'website': site, 'alias': '', 'title': m.group(1)[:120], 'gap': 'title generic or equals the legal name', 'profile': src}
    return {'website': site, 'alias': name, 'title': m.group(1)[:120], 'profile': src, 'read_by': 'issuer website <title> (site from exchange profile)'}
if __name__ == '__main__':
    if E.get('TARGETS', 'zero') == 'all': targets = issuers
    else:
        have = set(e['exchange'] + '|' + e['ticker'] for e in events()); targets = [r for r in issuers if key(r) not in have]
    print('website alias targets', len(targets), flush=True)
    resume('website_aliases', fetch, targets, threads=int(E.get('THREADS', '6')))
