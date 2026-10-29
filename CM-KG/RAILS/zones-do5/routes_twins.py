r"""routes_twins.py — TWINS-01 (DAY ORDER 5, 2026-10-24): every Allooloo twin zone that exists today renders its family page (no 301), one Worker per family:
  eco-twins  — <cc>-eco.io / .org / .com (the xx-eco family twins; sm and xx render the index allooloo.ai/markets)
  acm-twins  — acm-<code>.org / .com
  rco-twins  — rco-10060.ai / .com (the family page of record is the standard, rco-10060.org)
Per zone: prior routes, dynamic-redirect rules and apex/www records to routes-backup-twins\<zone>.json (first copy kept); enabled redirect rules DISABLED (never
deleted; restore = enabled true from the backup); routes <zone>/* and www.<zone>/* → the family Worker (an existing route on that exact pattern is re-pointed,
its prior script kept in the backup; more specific routes such as <zone>/01/* are left as they are); a zone whose apex or www has no proxied record gets a proxied
AAAA 100:: placeholder (house practice). Usage: python -X utf8 -I routes_twins.py dry|apply eco|acm|rco|<zone> ..."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import cf, zones
HERE = os.path.dirname(os.path.abspath(__file__)); BK = os.path.join(HERE, 'routes-backup-twins'); os.makedirs(BK, exist_ok=True)
MODE = sys.argv[1]; SEL = sys.argv[2:]
INV = json.load(open(os.path.join(HERE, 'twins-inventory-2026-10-24.json')))
FAM = {'eco': [z for z in INV['eco'] if z.split('.')[-1] in ('io', 'org', 'com')], 'acm': [z for z in INV['acm'] if z.split('.')[-1] in ('org', 'com')], 'rco': ['rco-10060.ai', 'rco-10060.com']}
fam_of = lambda z: next(f for f, zs in FAM.items() if z in zs)
targets = []
for s in SEL: targets += FAM[s] if s in FAM else [s]
log = {}
for z in targets:
    script = fam_of(z) + '-twins'; Z = zones(z)[0]['id']
    routes = cf('GET', f'/zones/{Z}/workers/routes').get('result') or []
    rs = cf('GET', f'/zones/{Z}/rulesets/phases/http_request_dynamic_redirect/entrypoint'); rules = (rs.get('result') or {}).get('rules') or []
    dns = [d for d in (cf('GET', f'/zones/{Z}/dns_records?per_page=100').get('result') or []) if d['name'] in (z, 'www.' + z)]
    bp = os.path.join(BK, z + '.json')
    if not os.path.exists(bp): json.dump({'zone': z, 'zone_id': Z, 'read': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'routes': routes, 'redirect_ruleset': rs.get('result'), 'dns': dns}, open(bp, 'w', encoding='utf-8'), indent=1)
    acts = []
    for pat in (f'{z}/*', f'www.{z}/*'):
        ex = [r for r in routes if r['pattern'] == pat]
        acts.append(('repoint' if ex else 'add', pat, ex[0].get('script') if ex else None))
        if MODE == 'apply':
            r = cf('PUT', f"/zones/{Z}/workers/routes/{ex[0]['id']}", {'pattern': pat, 'script': script}) if ex else cf('POST', f'/zones/{Z}/workers/routes', {'pattern': pat, 'script': script})
            acts[-1] += (r.get('success'),)
    en = [r for r in rules if r.get('enabled', True)]
    if en:
        acts.append(('disable redirect rules', len(en)))
        if MODE == 'apply':
            for r in en:
                body = {k: r[k] for k in ('action', 'expression', 'description', 'action_parameters') if k in r}; body['enabled'] = False
                cf('PATCH', f"/zones/{Z}/rulesets/{rs['result']['id']}/rules/{r['id']}", body)
    for nm in (z, 'www.' + z):
        if not any(d['name'] == nm and d.get('proxied') for d in dns):
            acts.append(('placeholder AAAA 100::', nm))
            if MODE == 'apply': cf('POST', f'/zones/{Z}/dns_records', {'type': 'AAAA', 'name': nm, 'content': '100::', 'proxied': True, 'ttl': 1, 'comment': 'TWINS-01 2026-10-24 placeholder (Worker route)'})
    if MODE == 'apply': cf('POST', f'/zones/{Z}/purge_cache', {'purge_everything': True})
    log[z] = acts; print(z, script, acts)
json.dump(log, open(os.path.join(HERE, f'routes-twins-{MODE}-{"_".join(SEL)[:40]}-2026-10-24.json'), 'w'), indent=1)
print(len(targets), 'zones')
