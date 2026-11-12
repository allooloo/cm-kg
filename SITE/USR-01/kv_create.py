import json, urllib.request, urllib.error
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]; A = 'dd2832b36f171b815f84c8487aada36b'
def api(p, m='GET', b=None):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, method=m, data=json.dumps(b).encode() if b else None, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'}), timeout=30).read())
    except urllib.error.HTTPError as e: return {'success': False, 'code': e.code, 'body': e.read()[:300].decode()}
ns = [n for n in api(f'/accounts/{A}/storage/kv/namespaces?per_page=100')['result'] if n['title'] == 'allooloo-research']
if not ns: r = api(f'/accounts/{A}/storage/kv/namespaces', 'POST', {'title': 'allooloo-research'}); print(r.get('success'), r.get('result') or r)
else: print('exists', ns[0])
