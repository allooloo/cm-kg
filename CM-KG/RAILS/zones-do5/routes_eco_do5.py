r"""routes_eco_do5.py — ECO-02 (DAY ORDER 5, 2026-10-24): the six xx-eco zones of the day (eu lu ky bm je tw -eco.ai) bound to the Worker eco-pages with zone routes
<zone>/* and www.<zone>/* (the ECO-01 binding pattern), each apex and www given a proxied AAAA 100:: placeholder (house practice). Prior state to
routes-backup-eco-do5\<zone>.json first. Usage: python -X utf8 -I routes_eco_do5.py dry|apply"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import cf, zones
HERE = os.path.dirname(os.path.abspath(__file__)); BK = os.path.join(HERE, 'routes-backup-eco-do5'); os.makedirs(BK, exist_ok=True); MODE = sys.argv[1]
for z in [f'{c}-eco.ai' for c in 'eu lu ky bm je tw'.split()]:
    Z = zones(z)[0]['id']; routes = cf('GET', f'/zones/{Z}/workers/routes').get('result') or []; dns = cf('GET', f'/zones/{Z}/dns_records?per_page=100').get('result') or []
    bp = os.path.join(BK, z + '.json')
    if not os.path.exists(bp): json.dump({'zone': z, 'read': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'routes': routes, 'dns': dns}, open(bp, 'w'), indent=1)
    acts = []
    for pat in (f'{z}/*', f'www.{z}/*'):
        if any(r['pattern'] == pat for r in routes): acts.append(('route present', pat)); continue
        acts.append(('route add', pat, cf('POST', f'/zones/{Z}/workers/routes', {'pattern': pat, 'script': 'eco-pages'}).get('success') if MODE == 'apply' else None))
    for nm in (z, 'www.' + z):
        if any(d['name'] == nm and d.get('proxied') for d in dns): continue
        acts.append(('AAAA 100::', nm, cf('POST', f'/zones/{Z}/dns_records', {'type': 'AAAA', 'name': nm, 'content': '100::', 'proxied': True, 'ttl': 1, 'comment': 'ECO-02 2026-10-24 placeholder (Worker route)'}).get('success') if MODE == 'apply' else None))
    print(z, acts)
