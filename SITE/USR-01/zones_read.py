import json, urllib.request
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]
def api(p):
    return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, headers={'Authorization': 'Bearer ' + TOK, 'User-Agent': 'Allooloo USR-01 zones'}), timeout=30).read())
for z in ['getresearch.ai', 'getresearch.io', 'get-research.ai', 'get-research.com', 'get-research.org', 'get-research.io']:
    r = api('/zones?name=' + z).get('result') or []
    if not r: print(z, 'NOT IN THE ACCOUNT'); continue
    Z = r[0]['id']; recs = api(f'/zones/{Z}/dns_records?per_page=100').get('result') or []; routes = api(f'/zones/{Z}/workers/routes').get('result') or []
    print(z, r[0]['status'], r[0]['plan']['name'], 'dns', [(x['type'], x['name'], x['content'][:40]) for x in recs], 'routes', [(x['pattern'], x.get('script')) for x in routes])
