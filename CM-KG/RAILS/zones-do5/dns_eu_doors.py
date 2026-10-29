r"""dns_eu_doors.py — DAY ORDER 5 ZONES-01 (2026-10-24): the zone records for the European doors under the EU regime zone, and the Luxembourg door on its own zone.
  <cc>.eu-cm-kg.ai   CNAME → the node's Container Apps FQDN (proxied, orange)   + TXT asuid.<cc>.eu-cm-kg.ai = the app's customDomainVerificationId
  mcp.lu-cm-kg.ai / agent.lu-cm-kg.ai  the same for Luxembourg's own zone (lu is also <lu>.eu-cm-kg.ai, the alias)
Records only (no Worker routes, no bindings). An existing record of the same name and type is updated in place; nothing deleted.
Input: doors-2026-10-24.json beside (cc → {app, rg, env, fqdn, asuid}) from az. Usage: python -X utf8 -I dns_eu_doors.py dry|apply"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import cf, zones
HERE = os.path.dirname(os.path.abspath(__file__)); MODE = sys.argv[1]
D = json.load(open(os.path.join(HERE, 'doors-2026-10-24.json')))
want = []
for cc, d in D.items():
    want += [('eu-cm-kg.ai', f'{cc}.eu-cm-kg.ai', 'CNAME', d['fqdn'], True), ('eu-cm-kg.ai', f'asuid.{cc}.eu-cm-kg.ai', 'TXT', d['asuid'], False)]
lu = D['lu']
for h in ('mcp', 'agent'):
    want += [('lu-cm-kg.ai', f'{h}.lu-cm-kg.ai', 'CNAME', lu['fqdn'], True), ('lu-cm-kg.ai', f'asuid.{h}.lu-cm-kg.ai', 'TXT', lu['asuid'], False)]
zid = {}; log = []
for zn, name, typ, content, prox in want:
    if zn not in zid: zid[zn] = zones(zn)[0]['id']
    Z = zid[zn]; ex = cf('GET', f'/zones/{Z}/dns_records?name={name}&type={typ}').get('result') or []
    body = {'type': typ, 'name': name, 'content': content if typ != 'TXT' else '"%s"' % content, 'ttl': 1, 'proxied': prox, 'comment': 'DAY ORDER 5 ZONES-01 2026-10-24'}
    act = 'same' if ex and ex[0]['content'].strip('"') == content and ex[0].get('proxied', False) == prox else ('update' if ex else 'add')
    res = None
    if MODE == 'apply' and act != 'same':
        r = cf('PUT', f"/zones/{Z}/dns_records/{ex[0]['id']}", body) if ex else cf('POST', f'/zones/{Z}/dns_records', body)
        res = r.get('success'), (r.get('errors') or [None])[0]
    log.append([name, typ, act, res]); print(name, typ, act, res if res else '')
json.dump(log, open(os.path.join(HERE, f'dns-eu-doors-{MODE}-2026-10-24.json'), 'w'), indent=1)
