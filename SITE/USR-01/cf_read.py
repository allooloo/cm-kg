import json, urllib.request, urllib.error
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]; A = 'dd2832b36f171b815f84c8487aada36b'
def api(p):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, headers={'Authorization': 'Bearer ' + TOK}), timeout=30).read())
    except urllib.error.HTTPError as e: return {'success': False, 'code': e.code, 'body': e.read()[:200].decode()}
r = api(f'/accounts/{A}/storage/kv/namespaces?per_page=100'); print('kv', r.get('success'), [(n['title'], n['id'][:6]) for n in r.get('result') or []] if r.get('success') else r)
r = api(f'/accounts/{A}/r2/buckets'); print('r2', r.get('success'), [b['name'] for b in (r.get('result') or {}).get('buckets', [])] if r.get('success') else r)
r = api(f'/accounts/{A}/workers/scripts'); print('workers', len(r.get('result') or []), [s['id'] for s in r.get('result') or [] if 'page' in s['id'] or 'apex' in s['id'] or 'gate' in s['id']])
r = api(f'/accounts/{A}/workers/subscriptions'); print('subs', json.dumps(r)[:300])
