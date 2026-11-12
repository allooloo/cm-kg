import json, sys, urllib.request
T = open(r'C:\ALLOOLOO\AGENT KEYS\rco-d1-read-token.txt', encoding='utf-8').read().strip().splitlines()[0]
q = sys.argv[1]
r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4/accounts/dd2832b36f171b815f84c8487aada36b/d1/database/111a8a79-4a2b-47e5-81a3-c7b7ab4dd4c6/query', data=json.dumps({'sql': q}).encode(), headers={'Authorization': 'Bearer ' + T, 'content-type': 'application/json'}), timeout=60).read())
print(json.dumps(r['result'][0]['results'])[:900], r['result'][0]['meta'].get('rows_read'))
