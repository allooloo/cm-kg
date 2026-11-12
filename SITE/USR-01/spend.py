import json, glob, os, urllib.request
t = {}
for f in glob.glob(r'C:\ALLOOLOO\CM-KG\RESEARCH\pages\*.spend.json'):
    for k, v in json.load(open(f)).items(): t[k] = t.get(k, 0) + v
print('writer (claude-haiku-5-5):', t)
c = {}
for f in glob.glob(r'C:\ALLOOLOO\CM-KG\POND\us-cm-kg\research-coverage\*\spend.json'):
    j = json.load(open(f)); print(os.path.basename(os.path.dirname(f)), j)
    for k, v in j.items(): c[k] = c.get(k, 0) + v
print('coverage total (files):', c)
try:
    K = open(r'C:\ALLOOLOO\AGENT KEYS\tavily.txt', encoding='utf-8').read().strip().splitlines()[0]
    r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + K}), timeout=30).read()); print('tavily usage:', json.dumps(r)[:400])
except Exception as e: print('tavily usage not read:', repr(e)[:120])
