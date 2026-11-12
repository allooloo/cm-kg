import json, urllib.request
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]
def api(p): return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, headers={'Authorization': 'Bearer ' + TOK}), timeout=30).read())
for z in ['data-equityresearch.ai', 'data-equityresearch.com', 'data-equityresearch.org', 'data-equityresearch.io', 'dataequityresearch.ai', 'dataequityresearch.com', 'dataequityresearch.org', 'dataequityresearch.io']:
    r = api('/zones?name=' + z).get('result') or []
    if not r: print(z, 'NOT IN THE ACCOUNT'); continue
    Z = r[0]['id']; recs = api(f'/zones/{Z}/dns_records?per_page=100').get('result') or []; routes = api(f'/zones/{Z}/workers/routes').get('result') or []
    print(z, r[0]['status'], 'dns', len(recs), 'routes', len(routes))
