"""SITE-03 — roster v1.2: the four LENS-01 rulings (CEO, 2026-10-28) and the role of record per zone (Site Build Plan v2.2 §5).
Input: zones_classified.json (LENS-01). Output: zones_v12.json — estate · family · lens · role · target · rule_source per zone. Read-only.
Usage: python -X utf8 -I rulings_v12.py <zones_classified.json> <zones_v12.json>"""
import json, re, sys
from collections import Counter
Z = json.load(open(sys.argv[1], encoding='utf-8'))
EU13 = ['it', 'es', 'se', 'dk', 'no', 'fi', 'be', 'ie', 'at', 'pl', 'pt', 'gr', 'cz']   # the European nodes served under eu-cm-kg.ai (DAY ORDER 5)
KYP_PRODUCTS = {'agentic-ask': 'ask', 'agentic-issuers': 'issuers', 'agentic-coverage': 'coverage', 'agentic-esg': 'esg', 'agentic-disclosure': 'disclosure', 'agentic-registries': 'registries'}
SERVE_PRODUCTS = {'agentic-radar', 'agentic-x402', 'agentic-trades'}
SHELF_SERVE = {'data-now', 'data-vintage', 'data-ark', 'data-score', 'data-timeline', 'data-events', 'data-replay', 'data-bench', 'data-cleanroom', 'data-review', 'data-record', 'data-eco', 'data-rco'}
ROOMS = {'hunter-agent': 'https://data-now.ai', 'hedge-agent': 'https://data-vintage.ai', 'ark-agent': 'https://data-ark.ai'}
def base(n): return n.split('.')[0]
def tld(n): return n.split('.', 1)[1]
def role_of(z):
    """(role, target, source) per §5; None where the role is read from the wire (acm-*, sm-eco-10060.*, agentmarketnews, issuerwire)."""
    n = z['zone']; b = base(n); t = tld(n); fam = z['family']; m = None
    if n == 'allooloo.io': return ('serve', '', '§5 apex')
    if b == 'allooloo': return ('301', 'https://allooloo.io', '§5 apex')
    if b in ('capitalmarketsknowledgegraph', 'cm-kg'): return ('301', 'https://getissuer.ai', '§5 apex (human page; the MCP apex hostname keeps answering)')
    if n == 'getissuer.ai': return ('serve', '', '§5 apex')
    if b in ('getissuer', 'get-issuer'): return ('301', 'https://getissuer.ai', '§5 apex')
    if n == 'eu-cm-kg.ai': return ('301', 'https://eu-issuer.ai', '§5 node door')
    if (m := re.match(r'^([a-z]{2})-cm-kg\.ai$', n)): return ('serve', '', '§5 node door')
    if (m := re.match(r'^([a-z]{2})-cm-kg\.(com|org|io|net)$', n)): return ('301', f'https://{m.group(1)}-cm-kg.ai', '§5 node twin')
    if fam == 'governance zone':
        d = re.match(r'^agent-?(kyp|prod|mifid|finsa|ddo|regbi)\.', n)
        if d: return ('serve', '', '§5 governance zone') if n == f'agent-{d.group(1)}.ai' else ('301', f'https://agent-{d.group(1)}.ai', '§5 governance twin')
    if b in KYP_PRODUCTS: return ('301', f'https://getissuer.ai/#{KYP_PRODUCTS[b]}', '§5 product page → the KYP section' if t == 'ai' else '§5 product twin')
    if b in SERVE_PRODUCTS: return ('serve', '', '§5 product page') if t == 'ai' else ('301', f'https://{b}.ai', '§5 product twin')
    if b in ('agentic-zen', 'agenticzen'): return ('exclude', '', '§5 — the other estate')
    if n == 'kyp-model.ai': return ('serve', '', '§5 product / standard')
    if b in ('kyp-model', 'kypmodel'): return ('301', 'https://kyp-model.ai', '§5 product / standard twin')
    if b in ('cite-fact', 'cite-dd'): return ('301', 'https://getissuer.ai/#cite-fact', '§5 cite → the KYP section (until they carry their own page)') if t == 'ai' else ('301', f'https://{b}.ai', '§5 cite twin')
    if b == 'cm-record': return ('301', 'https://getissuer.ai/#provenance', '§5 cm-record → the KYP provenance section')
    if (m := re.match(r'^([a-z]{2})-eco\.ai$', n)): return ('serve', '', '§5 eco page')
    if (m := re.match(r'^([a-z]{2})-eco\.(com|org|io|net)$', n)): return ('301', f'https://{m.group(1)}-eco.ai', '§5 eco twin')
    if (m := re.match(r'^([a-z]{2})-issuer\.ai$', n)): return ('serve', '', '§5 issuer page')
    if (m := re.match(r'^([a-z]{2})-issuer\.(com|org|io|net)$', n)): return ('301', f'https://{m.group(1)}-issuer.ai', '§5 issuer twin')
    if b in SHELF_SERVE: return ('serve', '', '§5 shelf') if t == 'ai' else ('301', f'https://{b}.ai', '§5 shelf twin')
    if n == 'data-live.ai': return ('301', 'https://data-now.ai', '§5 shelf')
    if b in ROOMS: return ('301', ROOMS[b], '§5 shelf room → its shelf page') if t == 'ai' else ('301', f'https://{b}.ai', '§5 shelf twin')
    if b == 'agent-swap': return ('serve' if t == 'ai' else '301', '' if t == 'ai' else 'https://agent-swap.ai', 'hold — CEO to name the lens; role as today')
    return (None, None, 'read from the wire')
out = []
for z in Z:
    z = dict(z); n = z['zone']; b = base(n); note = ''
    # ---- the four rulings
    if b == 'agentic-trades': z['lens'] = 'Shelf'; note = 'ruling 3: agentic-trades → Shelf'
    elif b == 'agentmarketnews': z.update(estate='allooloo', family='issuerwire', lens='Issuerwire', include='Y'); note = 'ruling 3: agentmarketnews → allooloo / Issuerwire'
    elif re.match(r'^[a-z]{2}-eco-10060\.(org|com|ai)$', n) or b == 'sm-eco-10060': z.update(estate='allooloo', family='sm-eco-10060', lens='ECO', include='Y'); note = 'ruling 4: sm-eco-10060.* → allooloo / ECO'
    elif re.match(r'^acm-?', b) and z['estate'] == 'gsc': z.update(estate='allooloo', family='acm-standards', lens='Proof', include='Y'); note = 'ruling 4: acm-* → allooloo / Proof'
    elif b == 'agent-swap': z['lens'] = 'hold (CEO to name)'; note = 'ruling 2: agent-swap → hold'
    elif z['lens'].startswith('unassigned'): z['lens'] = 'unassigned'; note = 'no ruling'
    if z['estate'] == 'allooloo':
        r, tg, src = role_of(z); z.update(role=r, target=tg or '', role_source=src)
    else: z.update(role='', target='', role_source='')
    z['ruling'] = note; out.append(z)
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
A = [z for z in out if z['estate'] == 'allooloo']
print('allooloo zones', len(A), 'estate', Counter(z['estate'] for z in out))
print('lens', Counter(z['lens'] for z in A)); print('roles', Counter(z['role'] for z in A)); print('from the wire', [z['zone'] for z in A if z['role'] is None][:60], '…', sum(1 for z in A if z['role'] is None))
