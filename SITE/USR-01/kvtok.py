import json, urllib.request, urllib.error
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-workers-deploy.txt', encoding='utf-8').read().strip().splitlines()[0]
B = 'https://api.cloudflare.com/client/v4/accounts/dd2832b36f171b815f84c8487aada36b/storage/kv/namespaces/7d0e0e4a059e444982b5eb1cc500efc1'
def call(p, m='GET', b=None):
    try: return urllib.request.urlopen(urllib.request.Request(B + p, method=m, data=b, headers={'Authorization': 'Bearer ' + T, 'Content-Type': 'application/json'}), timeout=30).status
    except urllib.error.HTTPError as e: return e.code, e.read()[:120]
print('read meta', call('/values/meta')); print('bulk write probe', call('/bulk', 'PUT', json.dumps([{'key': 'probe:token', 'value': 'workers-deploy token can write'}]).encode()))
