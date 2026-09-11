"""Step 1 — pull the UK rosters and the registry bulk files into raw/.
Sources (all public, no login):
  LSE price explorer ....... POST https://api.londonstockexchange.com/api/v1/components/refresh (component priceexplorersearch;
                             markets=MAINMARKET|AIM, categories=EQUITY, showonlylse=true) — the same JSON the public price-explorer page renders.
                             Price fields in that feed (bid/mid/last/change/market cap/52-week) are DROPPED at write time; nothing priced is kept.
  LSE sector sweep ......... same endpoint with sectors=<ICB code> for each of the 45 sectors the explorer offers → ISIN → FTSE ICB sector
  Aquis ..................... aquis.eu refuses plain HTTP clients (Vercel checkpoint, HTTP 429). Roster read in a browser session from the page's
                             own Next.js data (/_next/data/<build>/companies.json?segment=… and /companies/<symbol>.json) and saved to raw/aquis.json
                             by the session. Documented in README; this script does not fetch it.
  GLEIF ISIN-to-LEI file ... https://mapping.gleif.org/api/v2/isin-lei/latest (daily zip)
  Companies House bulk ..... https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-<yyyy-mm-01>.zip (monthly, ~490 MB, free product)
"""
import requests, json, os, re, sys, time
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json',
      'Content-Type': 'application/json', 'Origin': 'https://www.londonstockexchange.com', 'Referer': 'https://www.londonstockexchange.com/'}
os.makedirs('raw', exist_ok=True)
LSE_PAGE = 'https://api.londonstockexchange.com/api/v1/pages'
LSE_REFRESH = 'https://api.londonstockexchange.com/api/v1/components/refresh'
PATH = 'live-markets/market-data-dashboard/price-explorer'
DROP = {'fiftyTwoWeeksMin', 'fiftyTwoWeeksMax', 'midPrice', 'marketcapitalization', 'netchangesign', 'netchange', 'percentualchange', 'lastprice', 'idnews', 'datenews', 'productroundel'}

def page_component():
    j = requests.get(LSE_PAGE, params={'path': PATH, 'parameters': 'markets=MAINMARKET'}, headers=UA, timeout=60).json()
    c = next(c for c in j['components'] if c['type'] == 'price-explorer')
    return c['id']

def refresh(cid, params):
    body = {'path': PATH, 'parameters': params, 'components': [{'componentId': cid, 'parameters': params}]}
    for attempt in range(6):
        try:
            r = requests.post(LSE_REFRESH, params={'parameters': params, 'path': PATH, 'components': 'priceexplorersearch'}, json=body, headers=UA, timeout=90)
            if r.status_code in (429,) or r.status_code >= 500: time.sleep(5 * (attempt + 1)); continue
            r.raise_for_status()
            j = r.json()[0]['content']
            return {x['name']: x['value'] for x in j}
        except Exception as e:
            print('retry', e, flush=True); time.sleep(3 * (attempt + 1))
    raise SystemExit('LSE refresh failed: ' + params)

def strip(x): return {k: v for k, v in x.items() if k not in DROP}

if __name__ == '__main__':
    cid = page_component(); print('price-explorer component', cid, flush=True)
    out = {'fetched': time.strftime('%Y-%m-%d'), 'component': cid, 'markets': {}, 'fields': None, 'sectors': {}}
    first = refresh(cid, 'markets=MAINMARKET&categories=EQUITY&showonlylse=true&page=0&size=200')
    out['fields'] = first['priceexplorerfields']
    sectors = first['priceexplorerfields']['sectors']
    for mkt in ('MAINMARKET', 'AIM'):
        rows = []; page = 0
        while True:
            s = refresh(cid, f'markets={mkt}&categories=EQUITY&showonlylse=true&page={page}&size=200')['priceexplorersearch']
            rows += [strip(x) for x in s['content']]
            if s['last'] or page > 40: break
            page += 1; time.sleep(0.5)
        out['markets'][mkt] = {'total': s['totalElements'], 'rows': rows}
        print(mkt, 'equity instruments', len(rows), 'of', s['totalElements'], flush=True)
        # sector sweep: ISIN -> ICB sector, per market
        secmap = {}
        for sec in sectors:
            page = 0
            while True:
                s = refresh(cid, f"markets={mkt}&categories=EQUITY&sectors={sec['key']}&showonlylse=true&page={page}&size=200")['priceexplorersearch']
                for x in s['content']: secmap[x['tidm']] = (sec['key'], sec['value'])
                if s['last'] or page > 10: break
                page += 1; time.sleep(0.3)
            time.sleep(0.3)
        out['sectors'][mkt] = secmap
        print(mkt, 'sector-tagged instruments', len(secmap), flush=True)
    json.dump(out, open('raw/lse_explorer.json', 'w'), indent=0)
    if '--no-gleif' not in sys.argv and not os.path.exists('raw/isin-lei-latest.zip'):
        meta = requests.get('https://mapping.gleif.org/api/v2/isin-lei/latest', headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()['data']['attributes']
        r = requests.get(meta['downloadLink'], timeout=600); open('raw/isin-lei-latest.zip', 'wb').write(r.content); open('raw/isin-lei-latest.txt', 'w').write(meta['fileName'])
        print('GLEIF mapping file', meta['fileName'], flush=True)
    if '--no-ch' not in sys.argv and not any(f.startswith('BasicCompanyDataAsOneFile') for f in os.listdir('raw')):
        idx = requests.get('https://download.companieshouse.gov.uk/en_output.html', headers={'User-Agent': UA['User-Agent']}, timeout=60).text
        fn = re.search(r'BasicCompanyDataAsOneFile-[0-9-]+\.zip', idx).group(0)
        with requests.get('https://download.companieshouse.gov.uk/' + fn, headers={'User-Agent': UA['User-Agent']}, timeout=1800, stream=True) as r:
            with open('raw/' + fn, 'wb') as f:
                for chunk in r.iter_content(1 << 20): f.write(chunk)
        print('Companies House bulk', fn, flush=True)
    print('FETCH DONE', flush=True)
