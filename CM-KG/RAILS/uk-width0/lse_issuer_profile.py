"""Step 4 — issuer reference data from the LSE issuer-profile page API (the same call the public company page makes):
  GET https://api.londonstockexchange.com/api/v1/pages?path=issuer-profile&parameters=tidm=<TIDM>&tab=company-page&issuername=<slug>
Kept from component issuerreferencedata: issuer code, name, address, country of incorporation, web address, first tradable date,
ICB industry / supersector / sector / subsector (codes and names), listing category, issued instrument codes; plus the Main Market / AIM
roundel and index roundel from bestRoundels. Market cap is dropped. One call per issuer code (default instrument TIDM). Writes raw/lse_issuer.jsonl.
"""
import requests, json, os, re, time, threading
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json', 'Origin': 'https://www.londonstockexchange.com', 'Referer': 'https://www.londonstockexchange.com/'}
ex = json.load(open('raw/lse_explorer.json'))
issuers = {}
for mkt, blk in ex['markets'].items():
    for x in blk['rows']:
        issuers.setdefault(x['issuercode'], {'issuercode': x['issuercode'], 'issuername': x['issuername'], 'tidm': x['tidm'], 'market': mkt})
done = set()
if os.path.exists('raw/lse_issuer.jsonl'):
    for line in open('raw/lse_issuer.jsonl', encoding='utf-8'):
        try: done.add(json.loads(line)['issuercode'])
        except Exception: pass
todo = [v for k, v in issuers.items() if k not in done]
print('issuers', len(issuers), 'todo', len(todo), flush=True)
def slug(n): return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
out = open('raw/lse_issuer.jsonl', 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
def work(v):
    rec = {'issuercode': v['issuercode'], 'tidm': v['tidm'], 'market': v['market']}
    params = f"tidm={v['tidm']}&tab=company-page&issuername={slug(v['issuername'])}"
    rec['src'] = f"https://www.londonstockexchange.com/stock/{v['tidm']}/{slug(v['issuername'])}/company-page"
    for attempt in range(5):
        try:
            r = requests.get('https://api.londonstockexchange.com/api/v1/pages', params={'path': 'issuer-profile', 'parameters': params}, headers=UA, timeout=60)
            if r.status_code == 429 or r.status_code >= 500: time.sleep(4 * (attempt + 1)); continue
            if r.status_code != 200: rec['error'] = r.status_code; break
            j = r.json(); found = False
            for c in j.get('components') or []:
                for x in c.get('content') or []:
                    if not isinstance(x, dict): continue
                    if x.get('name') == 'issuerreferencedata' and x.get('value'):
                        val = dict(x['value']); val.pop('marketcap', None); rec['ref'] = val; found = True
                    if x.get('name') == 'bestRoundels' and x.get('value'): rec['roundels'] = x['value']
                    if x.get('name') == 'issuername' and x.get('value'): rec['displayname'] = x['value'].get('name')
            if not found: rec['error'] = 'no issuerreferencedata'
            break
        except Exception as e:
            time.sleep(3)
    else: rec['error'] = 'exhausted'
    with lock:
        out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
        if cnt[0] % 100 == 0: print(cnt[0], '/', len(todo), flush=True)
with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '4'))) as exr:
    list(exr.map(work, todo))
print('DONE', flush=True)
