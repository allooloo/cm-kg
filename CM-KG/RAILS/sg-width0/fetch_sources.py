"""Step 1 — pull the Singapore rosters and registry files into raw/ (a junction to the open pond drop POND\\sg-cm-kg\\width0\\<date>\\). All public, no login.
  SGX securities list ..... https://api.sgx.com/securities/v1.1  (every SGX security the public screener renders: name, stock code, type, market MAINBOARD / CATALIST,
                            trading currency, listing date 'ptd'; price fields dropped at write time)
  SGX market metadata ..... https://api.sgx.com/marketmetadata/v2 (18,733 instruments: stock code, ISIN, issuer name, FISN, currency, asset class)
  SGX stock screener ...... https://api.sgx.com/stockscreener/v2.0/all?params=... (identity fields only: company name, stock code, sector; the screener's
                            financial columns are never requested)
  ACRA register ........... data.gov.sg collection 2 "ACRA Information on Corporate Entities" (27 monthly CSVs by first letter: UEN, entity name, entity type,
                            company type, status, incorporation date, registered address, SSIC, former names, audit firms) via the v2 API poll-download
  GLEIF ISIN-to-LEI file .. https://mapping.gleif.org/api/v2/isin-lei/latest
SGX company profiles and SGXNet announcements (api.sgx.com/companies, /announcements) answer 403 / 401 to plain clients — recorded as HITL."""
import requests, json, os, re, sys, time
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json', 'Origin': 'https://www.sgx.com', 'Referer': 'https://www.sgx.com/'}
os.makedirs('raw', exist_ok=True); os.makedirs('raw/acra', exist_ok=True)
DROP_PRICE = {'b', 'bv', 'c', 'h', 'l', 'o', 'p', 'p_', 'pv', 's', 'sv', 'v', 'v_', 'vl', 'lt', 'iiv', 'iopv', 'change_vs_pc', 'change_vs_pc_percentage', 'dp', 'dpc', 'bond_accrued_interest', 'bond_clean_price', 'bond_dirty_price', 'bond_date', 'r', 'ed', 'ej', 'ex', 'clo', 'cr', 'du'}
def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=120, **kw)
            if r.status_code in (429, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
if __name__ == '__main__':
    r = get('https://api.sgx.com/securities/v1.1'); j = r.json()
    secs = [{k: v for k, v in x.items() if k not in DROP_PRICE} for x in j['data']['prices']]
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'total': j['meta'].get('totalItems'), 'rows': secs}, open('raw/sgx_securities.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('SGX securities', len(secs), 'stocks', sum(1 for x in secs if x.get('type') == 'stocks'), flush=True)
    r = get('https://api.sgx.com/marketmetadata/v2'); j = r.json()
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'rows': j['data']}, open('raw/sgx_marketmetadata.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('SGX market metadata', len(j['data']), 'with ISIN', sum(1 for x in j['data'] if x.get('isinCode')), flush=True)
    r = get('https://api.sgx.com/stockscreener/v2.0/all', params={'params': 'exchange,exchangeCountryCode,companyName,stockCode,sector,priceCurrCode'}); j = r.json()
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'rows': j['data']}, open('raw/sgx_screener.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('SGX stock screener', len(j['data']), 'with sector', sum(1 for x in j['data'] if x.get('sector')), flush=True)
    meta = get('https://api-production.data.gov.sg/v2/public/api/collections/2/metadata').json()['data']['collectionMetadata']
    ids = meta.get('childDatasets') or []; got = 0
    for ds in ids:
        fn = f'raw/acra/{ds}.csv'
        if os.path.exists(fn) and os.path.getsize(fn) > 1000: got += 1; continue
        m = get(f'https://api-production.data.gov.sg/v2/public/api/datasets/{ds}/metadata').json()['data']
        p = get(f'https://api-open.data.gov.sg/v1/public/api/datasets/{ds}/poll-download').json()
        u = (p.get('data') or {}).get('url')
        if not u: print('no download url for', ds, m.get('name')); continue
        with requests.get(u, timeout=1800, stream=True) as z:
            with open(fn, 'wb') as f:
                for chunk in z.iter_content(1 << 20): f.write(chunk)
        open(f'raw/acra/{ds}.meta.json', 'w', encoding='utf-8').write(json.dumps({'name': m.get('name'), 'lastUpdatedAt': m.get('lastUpdatedAt'), 'size': m.get('datasetSize')}))
        got += 1; print('ACRA', m.get('name'), os.path.getsize(fn), 'bytes', flush=True)
    print('ACRA datasets', got, 'of', len(ids), flush=True)
    if '--no-gleif' not in sys.argv and not os.path.exists('raw/isin-lei-latest.zip'):
        meta = requests.get('https://mapping.gleif.org/api/v2/isin-lei/latest', headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()['data']['attributes']
        rr = requests.get(meta['downloadLink'], timeout=600); open('raw/isin-lei-latest.zip', 'wb').write(rr.content); open('raw/isin-lei-latest.txt', 'w').write(meta['fileName']); print('GLEIF mapping file', meta['fileName'], flush=True)
    print('FETCH DONE', flush=True)
