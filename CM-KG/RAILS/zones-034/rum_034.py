"""ORDER-034 — zero scripts on the page: Cloudflare Web Analytics (RUM) auto-injects beacon.min.js into HTML on zones where it is on. This rail lists the RUM sites
of the fifteen ORDER-034 zones and sets auto_install off on each (the site and its data stay; nothing deleted). Prior site records exported beside first. Tokens by file name."""
import json, os, urllib.request, urllib.error, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); KEYS = r'C:\ALLOOLOO\AGENT KEYS'; ACCOUNT = 'dd2832b36f171b815f84c8487aada36b'
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
ZONES = [f'{c}-issuer.ai' for c in 'ca uk us de fr nl ch au sg jp kr hk gb'.split()] + ['kyp-model.org', 'issuerwire.org']
def cf(t, m, p, b=None):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + p, data=json.dumps(b).encode() if b is not None else None, method=m, headers={'Authorization': 'Bearer ' + open(os.path.join(KEYS, t), encoding='utf-8').read().strip(), 'content-type': 'application/json'})
    try: return json.load(urllib.request.urlopen(r, timeout=60))
    except urllib.error.HTTPError as e: return json.load(e)
tok = None
for t in ('cloudflare-d1.txt', 'cloudflare.txt', 'cloudflare-zt.txt'):
    r = cf(t, 'GET', f'/accounts/{ACCOUNT}/rum/site_info/list?per_page=1000')
    if r.get('success'): tok = t; sites = r['result']; break
    print(t, 'rum list refused', [e.get('code') for e in r.get('errors', [])])
if not tok: raise SystemExit('no token reads RUM sites — the CEO\'s click: Web Analytics → each zone → auto-install off')
mine = [s for s in sites if (s.get('ruleset') or {}).get('zone_name') in ZONES or s.get('host') in ZONES]
with open(os.path.join(HERE, f'pre-{STAMP}-rum-sites.json'), 'x', encoding='utf-8') as f: json.dump(mine, f, indent=1)
print(len(sites), 'RUM sites on the account;', len(mine), 'on ORDER-034 zones')
for s in mine:
    name = (s.get('ruleset') or {}).get('zone_name') or s.get('host')
    if not s.get('auto_install'): print(name, 'auto_install already off'); continue
    r = cf(tok, 'PUT', f"/accounts/{ACCOUNT}/rum/site_info/{s['site_tag']}", {'auto_install': False, 'host': s.get('host'), 'zone_tag': (s.get('ruleset') or {}).get('zone_tag')})
    print(name, 'auto_install off' if r.get('success') else [(e.get('code'), e.get('message')) for e in r.get('errors', [])])
