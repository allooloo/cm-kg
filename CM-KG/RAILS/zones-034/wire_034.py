"""ORDER-034 — read the wire after the roll: every zone's root, /llms.txt, /facts.json, agent card, /mcp (302), gb-issuer.ai (301), the CMR headers as read,
page size (< 50 KB), script count (0), the colours in /issuer.css (2), first-use acronyms (none unspelled), and shared text between every pair of node pages
(8-word shingles over the smaller page, < 40%). Writes zones-034\\wire-<stamp>.json. Read-only."""
import json, os, re, sys, itertools, datetime, urllib.request, urllib.error, html as H
HERE = os.path.dirname(os.path.abspath(__file__)); STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
NODES = 'ca uk us de fr nl ch au sg jp kr hk'.split(); ZONES = [f'{c}-issuer.ai' for c in NODES] + ['kyp-model.org', 'issuerwire.org']
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
OP = urllib.request.build_opener(NoRedir)
def get(url, accept='text/html'):
    try: r = OP.open(urllib.request.Request(url, headers={'User-Agent': 'Allooloo ORDER-034 wire read', 'Accept': accept}), timeout=40); return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e: return e.code, dict(e.headers), e.read()
    except Exception as e: return 0, {}, repr(e).encode()
def visible(b):
    s = b.decode('utf-8', 'replace'); s = re.sub(r'<head>.*?</head>', ' ', s, flags=re.S); s = re.sub(r'<(pre|code)[^>]*>.*?</\1>', ' ', s, flags=re.S); s = re.sub(r'<form.*?</form>', ' ', s, flags=re.S)
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
def shingles(t, n=8): w = t.lower().split(); return {' '.join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}
ACR = re.compile(r'(?<![A-Za-z0-9.\-/_@])([A-Z][A-Za-z]*[A-Z][A-Za-z0-9+]*|[A-Z]{2,}[0-9+]*)(?![A-Za-z0-9])')
ALLOW = {'Allooloo', 'Azure', 'Nasdaq', 'Cboe', 'Xetra', 'Eurex', 'BaFin', 'FinSA', 'MiFID', 'RegCo', 'TDnet', 'EDINET', 'HKEXnews', 'SGXNet', 'II', 'GmbH', 'SE', 'NV', 'SA', 'PLC',
         'GET', 'POST', 'TMX', 'SIX', 'BX', 'EQS', 'CHE', 'TOKYO', 'PRO', 'XXX', 'NETwork', 'GlobeNewswire', 'BusinessWire', 'ActusNews', 'Actusnews', 'RA', 'AG', 'XAMS', 'AEX', 'AMX', 'AScX', 'IR', 'OpenDART', 'iXBRL'}   # company and product names, HTTP verbs, register-code placeholders
# a first use counts as spelled when "(ACR)" follows within 160 characters (multi-word expansions put the words first)
def spelled(vis, m, a):
    if f'({a})' in vis[max(0, m.start() - 1):m.end() + 160]: return True
    p = re.match(r' \(([^()]{3,90})\)', vis[m.end():m.end() + 100])   # "ACR (Words)": the capitals of the words carry the acronym's letters in order
    if p:
        caps = ''.join(w[0] for w in re.findall(r'[A-Za-zÀ-ÿ]+', p.group(1)) if w[0].isupper()); it = iter(caps)
        return all(ch in it for ch in re.sub(r'[^A-Z]', '', a))
    return False
out = {'read_at': STAMP, 'zones': {}, 'pairs': {}}
texts = {}
for z in ZONES:
    st, hd, body = get(f'https://{z}/'); vis = visible(body) if st == 200 else ''; texts[z] = vis
    acr_first = {}
    for m in ACR.finditer(vis):
        a = m.group(1)
        if a not in acr_first: acr_first[a] = spelled(vis, m, a) or vis[max(0, m.start() - 80):m.start()].rstrip().endswith('(') and False
    unspelled = [a for a, ok in acr_first.items() if not ok and a not in ALLOW and not re.fullmatch(r'RA\d{6}', a) and not re.fullmatch(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', a) and a != 'GraphQL']   # GLEIF registration-authority codes, XBRL element names, product names
    doubled = re.findall(r'([A-Z][^()]{3,60}) \(\1 \(', vis) + re.findall(r'\(([A-Z][A-Za-z+]+)\) \([^()]*\(\1\)', vis)
    if doubled: unspelled.append('DOUBLED:' + '|'.join(map(str, doubled))[:120])
    rec = {'root': st, 'bytes': len(body), 'scripts': len(re.findall(rb'<script', body)), 'x_cmr': {k: v for k, v in hd.items() if k.lower().startswith('x-cmr')}, 'server': hd.get('Server') or hd.get('server'),
           'h1': (re.search(rb'<h1>(.*?)</h1>', body) or [None, b''])[1].decode('utf-8', 'replace'), 'acronyms_seen': len(acr_first), 'unspelled_first_use': unspelled}
    s2, h2, b2 = get(f'https://{z}/llms.txt', 'text/plain'); rec['llms'] = (s2, len(b2), b2.decode('utf-8', 'replace').splitlines()[0] if s2 == 200 else '')
    s3, _, b3 = get(f'https://{z}/facts.json', 'application/json'); rec['facts'] = s3
    s4, _, b4 = get(f'https://{z}/.well-known/agent-card.json', 'application/json'); rec['agent_card'] = (s4, (json.loads(b4).get('url') if s4 == 200 else None))
    s5, _, _ = get(f'https://{z}/robots.txt', 'text/plain'); s6, _, _ = get(f'https://{z}/sitemap.xml', 'application/xml'); rec['robots'] = s5; rec['sitemap'] = s6
    s7, _, b7 = get(f'https://{z}/', 'text/markdown'); rec['markdown_twin'] = (s7, len(b7))
    if z.endswith('-issuer.ai'): s8, h8, _ = get(f'https://{z}/mcp'); rec['mcp_get'] = (s8, h8.get('Location') or h8.get('location'))
    sw, hw, _ = get(f'https://www.{z}/'); rec['www'] = (sw, hw.get('Location') or hw.get('location'))
    out['zones'][z] = rec
st, hd, _ = get('https://gb-issuer.ai/some/path?x=1'); out['gb'] = (st, hd.get('Location') or hd.get('location'))
st, hd, css = get('https://uk-issuer.ai/issuer.css', 'text/css'); out['css_colours'] = sorted(set(re.findall(r'#[0-9A-Fa-f]{6}\b', css.decode())))
pages = [z for z in ZONES if z.endswith('-issuer.ai')]
worst = 0
for a, b in itertools.combinations(pages, 2):
    sa, sb = shingles(texts[a]), shingles(texts[b]); small = min(len(sa), len(sb)) or 1; share = round(100 * len(sa & sb) / small, 1); out['pairs'][f'{a}|{b}'] = share; worst = max(worst, share)
out['shared_text_worst_pct'] = worst
p = os.path.join(HERE, f'wire-{STAMP}.json'); json.dump(out, open(p, 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
print(p)
for z, r in out['zones'].items(): print(z, r['root'], r['bytes'], 'scripts', r['scripts'], 'llms', r['llms'][0], 'facts', r['facts'], 'card', r['agent_card'], 'md', r['markdown_twin'][0], 'mcp', r.get('mcp_get'), 'www', r['www'], 'unspelled', r['unspelled_first_use'], 'node', r['x_cmr'].get('X-CMR-Node') or r['x_cmr'].get('x-cmr-node'))
print('gb', out['gb'], 'css', out['css_colours'], 'worst shared', worst)
print(sorted(out['pairs'].items(), key=lambda x: -x[1])[:5])
