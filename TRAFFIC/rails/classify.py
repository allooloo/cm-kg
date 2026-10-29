"""LENS-01 — join the account's zone list to roster v1.1 and the Aug 25 inventory; estate, family, lens for every zone. Nothing on the wire."""
import json, re, sys
from collections import Counter, defaultdict
SP = r'C:\Users\matth\AppData\Local\Temp\claude\C--bpc-agent\4fc1172b-aaae-4859-9f0f-29f4a875d910\scratchpad'
DATE = '2026-10-28'
A = json.load(open(f'{SP}/zones_all.json', encoding='utf-8'))
R = json.load(open(f'{SP}/roster_v11.json', encoding='utf-8'))
INV = json.load(open(f'{SP}/inventory_0825.json', encoding='utf-8'))['ZONES']
DM = json.load(open(f'{SP}/domains_master.json', encoding='utf-8'))['Build']
NEWK = [k for k in R if k.startswith('NEW')][0]
roster = {}
for r in R['ZONES'][1:]:
    roster[r[0].strip()] = {'family': r[1], 'include': str(r[4]).strip(), 'sheet': 'ZONES', 'role_1019': r[5], 'wire_1019': r[6]}
for r in R[NEWK][1:]:
    n = r[0].strip()
    if n in roster: roster[n].update({'family': r[1], 'sheet': 'ZONES+NEW (listed twice)'})
    else: roster[n] = {'family': r[1], 'include': str(r[4]).strip(), 'sheet': NEWK, 'role_1019': r[5], 'wire_1019': ''}
inv = {r[0].strip(): {'family': r[8], 'wire_intent': r[9]} for r in INV[1:] if r[0]}
dm = {str(r[0]).strip().lower(): {'group': r[1], 'role': r[2], 'status': r[6]} for r in DM[1:] if r[0] and r[1]}

ESTATE_PAGES = {l.split()[1]: l.split()[0] for l in open(f'{SP}/zones.txt', encoding='utf-8') if l.strip()}   # zones whose custom domains are on the Allooloo estate-pages Worker (account read 2026-10-27)
SHELF = {'data-now.ai', 'data-now.com', 'data-now.io', 'data-now.org', 'data-vintage.ai', 'data-vintage.com', 'data-vintage.io', 'data-vintage.org', 'data-ark.ai', 'data-ark.io',
         'data-score.ai', 'data-timeline.ai', 'data-events.ai', 'data-replay.ai', 'data-bench.ai', 'data-review.ai', 'data-cleanroom.ai', 'data-cleanroom.io', 'data-cleanroom.org',
         'data-live.ai', 'hunter-agent.ai', 'hedge-agent.ai', 'ark-agent.ai'}   # plan §5, the 23 Oct 25–27 buys
OFFICE = re.compile(r'^(agent-kg|familyofficeknowledgegraph|fokg|fo-kg|agent-padel|gsc-padel)\.')
EXCL = re.compile(r'^(agentic-zen|agenticzen)\.')
KYP_PRODUCTS = {'agentic-ask', 'agentic-issuers', 'agentic-coverage', 'agentic-esg', 'agentic-disclosure', 'agentic-registries'}
PROOF_PRODUCTS = {'agentic-radar', 'agentic-x402'}

def base(n): return n.split('.')[0]
def gsc_pattern_family(n):
    b = base(n)
    rules = [
        (r'(^|-)10060($|-)|^standard10060|^eco10060|10060', 'eco-10060'), (r'esg-cpg|esgcpg', 'esg-cpg'), (r'aio-cpg', 'aio-cpg'), (r'amp-cpg', 'amp-cpg'),
        (r'^cpg-(\d{3}|68000|[a-z]{2})$|^cpgknowledgegraph|^cpg-', 'cpg-doors'), (r'^acm-?', 'acm-standards'), (r'^gsc-marketplace', 'marketplace'), (r'^gsc-fleet', 'fleet'),
        (r'message|^cpghumanintheloop|^x-gsi$', 'ia-family'), (r'^cpgagentprotocols', 'protocols'), (r'^agent-(acp|mpp|ucp|x402)$', 'a2a-gateways'), (r'vector', 'vector'), (r'^agentmarketnews', 'amn (Issuerwire predecessor; §6 names it in no group)'), (r'^a2a-?|^rco-?a2a|^mcp-?peptide|peptide|^glp1', 'a2a-hubs'),
        (r'bev|^gtin-bev', 'agent-bev'), (r'gtin|^x402-?fetch|^fetch-gtin', 'gtinfetch'), (r'^rco', 'rco'), (r'^dpu|^dpp|passport|pass$|paspoort|passaport|pasaporte|produktpass', 'dpu-passport'),
        (r'signal|^ghost', 'ghost-signal'), (r'^x-[a-z0-9]+$', 'x-signal'), (r'^aio|orderab|^ai-order', 'aio'), (r'^tfx|^tfxpl|^tfxbr|^tfxdl', 'tfx'), (r'^gsc-', 'corp'),
        (r'^elyssah|^isitagentready|^greencore|^treefree|^ecoverificado|^internet-?of|^jtretail|^couchemdd|^british-label|^carrierfleet|^electronic-?compliance|regulatory-?compliance', 'singles'),
    ]
    for rx, fam in rules:
        if re.search(rx, b): return fam
    return 'heritage'

rows = []
for z in A['zones']:
    n = z['name']; b = base(n); rec = {'zone': n, 'zone_id': z['id'], 'status': z['status'], 'plan': z['plan'], 'created_on': z['created_on'][:10]}
    ro = roster.get(n); iv = inv.get(n); d = dm.get(n)
    rec['roster_v11'] = ro['sheet'] if ro else ''; rec['roster_family'] = ro['family'] if ro else ''
    rec['inventory_0825_family'] = iv['family'] if iv else ''; rec['domains_master_group'] = d['group'] if d else ''
    if ro and ro['include'] == 'Y':
        est, fam, src, flag = 'allooloo', ro['family'], 'roster v1.1', ''
    elif n in SHELF:
        est, fam, src, flag = 'allooloo', 'shelf', f'plan §5 (NEW-{DATE})', f'NEW-{DATE}'
    elif re.match(r'^(issuerwire|issuer-wire)\.', n):
        est, fam, src, flag = 'allooloo', 'issuerwire', f'plan §6 (NEW-{DATE})', f'NEW-{DATE}'
    elif re.match(r'^(data-|hunter-agent|hedge-agent|ark-agent)', n):
        est, fam, src, flag = 'allooloo', 'shelf', f'pattern data-*/agent (NEW-{DATE}; Domains Master: {d["group"] if d else "not listed"})', f'NEW-{DATE} · unrostered (pattern)'
    elif re.match(r'^[a-z]{2}-issuer\.ai$', n):
        est, fam, src, flag = 'allooloo', 'issuer page', 'pattern <cc>-issuer.ai (plan §5 issuer page; not on roster v1.1)', 'unrostered (pattern) · roster gap'
    elif re.match(r'^[a-z]{2}-eco\.ai$', n) and d and 'ECO' in str(d['group']):
        est, fam, src, flag = 'allooloo', 'eco page', f'pattern <cc>-eco.ai + Domains Master ({d["status"]})', 'unrostered (pattern) · roster gap'
    elif re.match(r'^agentic-x402\.', n):
        est, fam, src, flag = 'allooloo', 'product page' if n.endswith('.ai') else 'product twin', 'pattern agentic-x402 (plan §5/§6 Proof; Domains Master Product — Agentic x402; not on roster v1.1)', 'unrostered (pattern) · roster gap'
    elif n in ESTATE_PAGES and not OFFICE.match(n):
        est, fam, src, flag = 'allooloo', 'product page' if n.endswith('.ai') else 'product twin', 'served by the Allooloo estate-pages Worker (custom domain); not on roster v1.1', 'unrostered (pattern) · roster gap'
    elif OFFICE.match(n):
        est, fam, src, flag = 'office', 'office', 'pattern (C:\\MATTHEWKEDDY root)', 'unrostered (pattern)'
    elif EXCL.match(n):
        est, fam, src, flag = 'exclude', 'agentic-zen', 'plan §5/§6 (the other estate)', 'unrostered (pattern)'
    elif iv and iv['family']:
        est, fam, src, flag = 'gsc', iv['family'], 'inventory 2026-08-25', ''
    elif iv:
        est, fam, src, flag = 'gsc', gsc_pattern_family(n), 'inventory 2026-08-25 (family blank) + pattern', 'inventory family blank (pattern)'
    else:
        est, fam, src, flag = 'gsc', gsc_pattern_family(n), 'pattern (NG-9 §S3 grouping + post-Aug-25 families)', 'unrostered (pattern)'
    # lens (Allooloo only)
    lens = ''
    if est == 'allooloo':
        if re.match(r'^(allooloo|cm-kg|capitalmarketsknowledgegraph)\.', n): lens = 'Company'
        elif re.match(r'^(getissuer|get-issuer)\.', n): lens = 'KYP'
        elif fam == 'issuerwire': lens = 'Issuerwire'
        elif fam == 'shelf': lens = 'Shelf'
        elif fam.startswith('eco '): lens = 'ECO'
        elif fam.startswith(('node ', 'governance', 'product / standard', 'issuer ')): lens = 'KYP'
        elif fam in ('product page', 'product twin'):
            lens = 'KYP' if b in KYP_PRODUCTS else 'Proof' if b in PROOF_PRODUCTS else 'Excluded' if b.startswith('agentic-zen') else f'unassigned ({b}: §6 names no group)'
        elif fam == 'apex / company': lens = 'Company'
        else: lens = 'unassigned'
    elif est == 'exclude': lens = 'Excluded'
    else: lens = f'— ({est})'
    rec.update({'estate': est, 'family': fam, 'lens': lens, 'source': src, 'flag': flag, 'include': 'N' if est == 'exclude' else 'Y'})
    rows.append(rec)

json.dump(rows, open(f'{SP}/zones_classified.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
names = {r['zone'] for r in rows}
print('zones', len(rows)); print('estate', Counter(r['estate'] for r in rows)); print('lens', Counter(r['lens'] for r in rows))
print('allooloo families', Counter(r['family'] for r in rows if r['estate'] == 'allooloo'))
print('gsc families', Counter(r['family'] for r in rows if r['estate'] == 'gsc'))
print('flags', Counter(r['flag'] for r in rows))
print('unrostered by pattern (gsc)', Counter(r['family'] for r in rows if r['estate'] == 'gsc' and r['flag']))
print('office', sorted(r['zone'] for r in rows if r['estate'] == 'office')); print('exclude', sorted(r['zone'] for r in rows if r['estate'] == 'exclude'))
print('roster rows not in account', [(n, v['include']) for n, v in roster.items() if n not in names])
print('inventory 0825 rows not in account', [n for n in inv if n not in names])
print('apex / company members', sorted(r['zone'] for r in rows if r['roster_family'] == 'apex / company'))
print('product / standard members', sorted(r['zone'] for r in rows if r['roster_family'] == 'product / standard'))
print('product page members', sorted(r['zone'] for r in rows if r['roster_family'] == 'product page'))
print('unassigned', sorted(r['zone'] for r in rows if r['lens'].startswith('unassigned')))
print('allooloo NEW', sorted((r['zone'], r['family'], r['domains_master_group']) for r in rows if r['estate'] == 'allooloo' and r['flag']))
print('gsc pattern sample', sorted(Counter((r['family'], base(r['zone']).split('-')[0]) for r in rows if r['estate'] == 'gsc' and r['flag']).items())[:80])
print('estate-pages served but not roster', sorted(n for n in ESTATE_PAGES if n not in roster))
print('heritage-by-pattern names', sorted(r['zone'] for r in rows if r['estate'] == 'gsc' and r['flag'] and r['family'] == 'heritage'))
