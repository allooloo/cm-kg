import json, urllib.request
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]
def api(p): return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, headers={'Authorization': 'Bearer ' + TOK}), timeout=30).read())
for z in ['data-equityresearch.ai', 'data-equityresearch.com', 'data-equityresearch.org', 'data-equityresearch.io', 'dataequityresearch.ai', 'dataequityresearch.com', 'dataequityresearch.org', 'dataequityresearch.io']:
    Z = api('/zones?name=' + z)['result'][0]['id']
    try: r = api(f'/zones/{Z}/ssl/certificate_packs?status=all'); print(z, [(c.get('type'), c.get('status')) for c in r.get('result', [])])
    except Exception as e: print(z, 'not read', repr(e)[:80])
