r"""bind_pages_do5.py — DAY ORDER 5 ZONES-01 / ISSUER-PAGES-01 (2026-10-24): the page hosts of the day bound to the Worker estate-pages as Workers custom domains
(Cloudflare makes the proxied record and the edge certificate). Hosts: <cc>-issuer.ai + www and <cc>-cm-kg.ai + www for lu ky bm je in tw sa ae br mx;
eu-issuer.ai + www; eu-cm-kg.ai (apex only — <cc>.eu-cm-kg.ai are the doors, on the node gate); <cc>.eu-issuer.ai for the fourteen European nodes.
A host already bound is left as it is. The eco hosts are bound by the ECO rail (eco-pages, zone routes). Usage: python -X utf8 -I bind_pages_do5.py dry|apply"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import cf, zones
ACCT = 'dd2832b36f171b815f84c8487aada36b'; MODE = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
OWN = 'lu ky bm je in tw sa ae br mx'.split(); EU14 = 'it es se dk no fi be ie at pl pt lu gr cz'.split()
H = []
for cc in OWN: H += [(f'{cc}-issuer.ai', f'{cc}-issuer.ai'), (f'www.{cc}-issuer.ai', f'{cc}-issuer.ai'), (f'{cc}-cm-kg.ai', f'{cc}-cm-kg.ai'), (f'www.{cc}-cm-kg.ai', f'{cc}-cm-kg.ai')]
H += [('eu-issuer.ai', 'eu-issuer.ai'), ('www.eu-issuer.ai', 'eu-issuer.ai'), ('eu-cm-kg.ai', 'eu-cm-kg.ai')] + [(f'{cc}.eu-issuer.ai', 'eu-issuer.ai') for cc in EU14]
have = {d['hostname']: d['service'] for d in cf('GET', f'/accounts/{ACCT}/workers/domains?per_page=1000').get('result', [])}
zid = {}; log = []
for host, zn in H:
    if host in have: log.append([host, 'bound', have[host]]); print(host, 'bound', have[host]); continue
    if zn not in zid: zid[zn] = zones(zn)[0]['id']
    res = None
    if MODE == 'apply':
        r = cf('PUT', f'/accounts/{ACCT}/workers/domains', {'hostname': host, 'service': 'estate-pages', 'zone_id': zid[zn], 'environment': 'production'})
        res = [r.get('success'), (r.get('errors') or [None])[0]]
    log.append([host, 'add', res]); print(host, 'add', res)
json.dump(log, open(os.path.join(HERE, f'bind-pages-{MODE}-2026-10-24.json'), 'w'), indent=1)
print(len(H), 'hosts')
