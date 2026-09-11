"""Step 3 — per-instrument reference record from the LSE instrument endpoint (the same call the public stock page makes):
  GET https://api.londonstockexchange.com/api/gw/lse/instruments/alldata/<TIDM>
Kept: ISIN, SEDOL, market, segment code, MiFIR type, country of the instrument, issuer code/name, instrument type, funds type, currency,
listing admission date, ICB sector/subsector codes. Price, volume, turnover, 52-week, news and market-cap fields are dropped at write time.
Writes raw/lse_alldata.jsonl keyed by TIDM; re-runs skip TIDMs already written.
"""
import requests, json, os, time, threading
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json', 'Origin': 'https://www.londonstockexchange.com', 'Referer': 'https://www.londonstockexchange.com/'}
KEEP = ['description', 'name', 'tidm', 'isin', 'sedol', 'category', 'mifir', 'country', 'csm', 'market', 'segment', 'fundsType', 'mifid', 'currency', 'suspend', 'issuercode', 'issuername', 'shortname', 'instrumenttype', 'tradingstatus', 'listingadmissiondate', 'sectorcode', 'subsectorcode', 'islse', 'fourwaykey', 'underlying']
ex = json.load(open('raw/lse_explorer.json'))
tidms = []
for mkt, blk in ex['markets'].items():
    for x in blk['rows']:
        if x['tidm'] not in tidms: tidms.append(x['tidm'])
done = set()
if os.path.exists('raw/lse_alldata.jsonl'):
    for line in open('raw/lse_alldata.jsonl', encoding='utf-8'):
        try: done.add(json.loads(line)['tidm'])
        except Exception: pass
todo = [t for t in tidms if t not in done]
print('instruments', len(tidms), 'todo', len(todo), flush=True)
out = open('raw/lse_alldata.jsonl', 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
def work(t):
    rec = None
    for attempt in range(5):
        try:
            r = requests.get('https://api.londonstockexchange.com/api/gw/lse/instruments/alldata/' + t, headers=UA, timeout=60)
            if r.status_code == 429 or r.status_code >= 500: time.sleep(4 * (attempt + 1)); continue
            if r.status_code == 200:
                j = r.json(); rec = {k: j.get(k) for k in KEEP}; rec['tidm'] = t
            else: rec = {'tidm': t, 'error': r.status_code}
            break
        except Exception as e:
            time.sleep(3)
    if rec is None: rec = {'tidm': t, 'error': 'exhausted'}
    rec['src'] = 'https://api.londonstockexchange.com/api/gw/lse/instruments/alldata/' + t
    with lock:
        out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
        if cnt[0] % 100 == 0: print(cnt[0], '/', len(todo), flush=True)
with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '4'))) as exr:
    list(exr.map(work, todo))
print('DONE', flush=True)
