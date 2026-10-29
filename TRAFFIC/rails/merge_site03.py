"""SITE-03 — merge roster v1.2 (rulings + §5 roles), the wire read and the Cloudflare state into the plan of writes.
Wire-read roles for the families §5 does not spell out (acm-*, sm-eco-10060.*, agentmarketnews, issuerwire): serve where the zone answers 200 on its own host,
else 301 to where it lands today. DORMANT STOCK (v2.2 §8): a GSC zone that lands on gsc-em.com or has no address, and is not a twin of a GSC zone that serves,
is re-pointed 301 → https://allooloo.io/ and tagged estate:allooloo-forward, lens Forwards.
Usage: python -X utf8 -I merge_site03.py <zones_v12.json> <wire.json> <api_state.json> <plan.json>"""
import json, sys, re
from collections import Counter, defaultdict
Z = json.load(open(sys.argv[1], encoding='utf-8')); W = {w['zone']: w for w in json.load(open(sys.argv[2], encoding='utf-8'))['zones']}; S = {s['zone']: s for s in json.load(open(sys.argv[3], encoding='utf-8'))['zones']}
base = lambda n: n.split('.')[0]
def wire_role(n):
    w = W.get(n) or {}
    if w.get('status') == 200 and (w.get('final_host') or '').replace('www.', '') == n: return ('serve', '', 'wire: serves on its own host')
    if w.get('status') == 200 and w.get('final_host'): return ('301', 'https://' + w['final_host'].replace('www.', ''), f"wire: lands on {w['final_host']} today")
    return ('serve', '', f"wire: {w.get('status')} — left as today (no 301 written)")
serving_gsc = {base(z['zone']) for z in Z if z['estate'] == 'gsc' and (W.get(z['zone']) or {}).get('status') == 200 and ((W.get(z['zone']) or {}).get('final_host') or '').replace('www.', '') == z['zone']}
plan = []; dormant = []
for z in Z:
    p = dict(z); n = z['zone']; w = W.get(n) or {}; s = S.get(n) or {}
    p.update(wire_status=w.get('status'), wire_final=w.get('final', ''), apex_addressed=s.get('apex_addressed', False), www_addressed=s.get('www_addressed', False), apex_proxied=s.get('apex_proxied', False), prior_rules=s.get('redirect_rules') or [], ai_bots_protection=s.get('ai_bots_protection'), dnssec=s.get('dnssec'), dns=s.get('dns', []), tags_cf=s.get('tags'))
    if z['estate'] == 'allooloo':
        if p['role'] is None: p['role'], p['target'], p['role_source'] = wire_role(n)
        if n == 'gb-issuer.ai': p['role'], p['target'], p['role_source'] = '301', 'https://uk-issuer.ai', 'ORDER-034: gb-issuer.ai forwards to uk-issuer.ai (UK, never GB)'
        if base(n) in ('sm-eco', 'xx-eco'): p['role'], p['target'], p['role_source'] = '301', 'https://allooloo.ai/markets', 'ECO-01: the index forwards (sm-eco.*, xx-eco.*) land on allooloo.ai/markets'
        if p['role'] == 'exclude': p['role'], p['target'] = 'exclude', ''
        p['tag_txt'] = f"estate:allooloo lens:{p['lens']} family:{p['family']} role:{p['role']} site-03:2026-10-28"
    elif z['estate'] == 'gsc':
        landing = (w.get('final_host') or '').replace('www.', ''); kind = 'lands on gsc-em.com' if landing == 'gsc-em.com' else ('no address' if w.get('status') == 'no address' else None)
        if kind and base(n) not in serving_gsc:
            p.update(estate='allooloo-forward', lens='Forwards', role='301', target='https://allooloo.io/', role_source=f'DORMANT STOCK (v2.2 §8): {kind}; not a twin of a serving GSC zone', include='Y', tag_txt='estate:allooloo-forward lens:Forwards site-03:2026-10-28', dormant_kind=kind)
            dormant.append(p)
    plan.append(p)
json.dump(plan, open(sys.argv[4], 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
A = [p for p in plan if p['estate'] in ('allooloo', 'allooloo-forward')]
print('plan zones', len(plan), 'allooloo', sum(1 for p in A if p['estate'] == 'allooloo'), 'allooloo-forward (dormant stock)', len(dormant), Counter(d['dormant_kind'] for d in dormant))
print('roles', Counter(p['role'] for p in A)); print('role sources', Counter(p['role_source'].split(':')[0].split(' —')[0] for p in A).most_common(12))
print('301 zones needing an apex address', sum(1 for p in A if p['role'] == '301' and not p['apex_addressed']), '; needing www', sum(1 for p in A if p['role'] == '301' and not p['www_addressed']))
print('301 zones with prior redirect rules', sum(1 for p in A if p['role'] == '301' and p['prior_rules']), '; serve zones carrying a redirect rule (not touched)', [(p['zone'], [r['target'] for r in p['prior_rules']]) for p in A if p['role'] == 'serve' and p['prior_rules']][:10])
print('ai_bots', Counter(str(p['ai_bots_protection']) for p in A)); print('dnssec', Counter(str(p['dnssec']) for p in A))
print('serve zones not answering 200 on their own host:', [(p['zone'], p['wire_status'], p['wire_final'][:50]) for p in A if p['role'] == 'serve' and not (p['wire_status'] == 200 and (p['wire_final'] or '').replace('https://', '').replace('www.', '').startswith(p['zone']))][:40])
print('301 zones whose wire already lands on the target:', sum(1 for p in A if p['role'] == '301' and p['target'] and p['wire_final'].replace('www.', '').startswith(p['target'].split('#')[0].rstrip('/'))), 'of', sum(1 for p in A if p['role'] == '301'))
print('dormant by family', Counter(d['family'] for d in dormant).most_common(20))
