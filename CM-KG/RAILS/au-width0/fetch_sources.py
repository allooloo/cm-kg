"""Step 1 — pull the Australian rosters and registry files into raw/. All public, no login.
  ASX directory ........... https://asx.api.markitdigital.com/asx-research/1.0/companies/directory/file (the CSV the public ASX listed-companies page serves:
                            code, company name, GICS industry group, listing date, market cap — market cap dropped) + https://www.asx.com.au/asx/research/ASXListedCompanies.csv
  ASX per company ......... asx.api.markitdigital.com/asx-research/1.0/companies/<code>/header (listing date, sector, industry group, security type, status),
                            /key-statistics (ISIN; price and dividend fields dropped), /about (website, contact address, share-registry address, secretaries, indices)
                            — the same JSON the public asx.com.au company pages render; access token as published in the page.
  NSX official list ....... https://www.nsx.com.au/ftp/rss/nsx_rss_officiallist.xml (code, name, ISIN, industry, nominated adviser, listed date, summary link)
  TMX Australia (formerly Cboe Australia) .. tmxaustralia.com/listings/companies renders by script: read in a browser session (see README), saved to raw/tmxau.json
  ASIC company register ... data.gov.au "Company Dataset — Current" (weekly zip; ACN, ABN, type, class, status, registration date, state, previous names) → raw/asic_company.zip
  GLEIF ISIN-to-LEI file .. https://mapping.gleif.org/api/v2/isin-lei/latest
"""
import requests, json, os, re, sys, time, csv, io, threading, html
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
TOKEN = '83ff96335c2d45a094df02a206a39ff4'  # public access token embedded in asx.com.au pages (not a secret)
MK = 'https://asx.api.markitdigital.com/asx-research/1.0/companies/'
os.makedirs('raw', exist_ok=True)
DROP_HDR = {'priceAsk', 'priceBid', 'priceChange', 'priceChangePercent', 'priceLast', 'volume', 'marketCap'}
KEEP_KS = {'isin', 'shareDescription', 'numOfShares', 'foreignExempt'}
def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=60, **kw)
            if r.status_code in (429, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
if __name__ == '__main__':
    r = get(MK + f'directory/file?access_token={TOKEN}'); open('raw/asx_directory.csv', 'wb').write(r.content)
    rows = list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
    for x in rows: x.pop('Market Cap', None)
    json.dump(rows, open('raw/asx_directory.json', 'w', encoding='utf-8'), ensure_ascii=False); print('ASX directory rows', len(rows), flush=True)
    r = get('https://www.asx.com.au/asx/research/ASXListedCompanies.csv'); open('raw/ASXListedCompanies.csv', 'wb').write(r.content); print('ASX listed companies csv', len(r.content), 'bytes', flush=True)
    r = requests.get('https://www.nsx.com.au/ftp/rss/nsx_rss_officiallist.xml', headers={'User-Agent': UA['User-Agent']}, timeout=60); open('raw/nsx_officiallist.xml', 'wb').write(r.content)
    items = []
    for it in re.findall(r'<item>(.*?)</item>', r.text, re.S):
        d = html.unescape(re.search(r'<description>(.*?)</description>', it, re.S).group(1)); fields = dict(re.findall(r'([A-Za-z ]+?):\s*(.*?)\s*(?:<BR>|<br>)', d))
        t = html.unescape(re.search(r'<title>(.*?)</title>', it, re.S).group(1)); link = re.search(r'<link>(.*?)</link>', it).group(1)
        items.append({'title': t, 'link': link, **{k.strip().lower().replace(' ', '_'): v.strip() for k, v in fields.items()}})
    json.dump(items, open('raw/nsx_list.json', 'w', encoding='utf-8'), ensure_ascii=False); print('NSX official list items', len(items), flush=True)
    if not os.path.exists('raw/asic_company.zip'):
        meta = get('https://data.gov.au/data/api/3/action/package_show?id=asic-companies').json()['result']
        res = next(x for x in meta['resources'] if x['format'].upper() == 'ZIP')
        with requests.get(res['url'], headers=UA, timeout=1800, stream=True) as z:
            with open('raw/asic_company.zip', 'wb') as f:
                for chunk in z.iter_content(1 << 20): f.write(chunk)
        open('raw/asic_company.txt', 'w').write(res['url'] + '\n' + res.get('last_modified', '')); print('ASIC company dataset', res['url'].split('/')[-1], flush=True)
    if '--no-gleif' not in sys.argv and not os.path.exists('raw/isin-lei-latest.zip'):
        meta = requests.get('https://mapping.gleif.org/api/v2/isin-lei/latest', headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()['data']['attributes']
        rr = requests.get(meta['downloadLink'], timeout=600); open('raw/isin-lei-latest.zip', 'wb').write(rr.content); open('raw/isin-lei-latest.txt', 'w').write(meta['fileName']); print('GLEIF mapping file', meta['fileName'], flush=True)
    # per-company reference records
    codes = [x['ASX code'] for x in rows]
    done = set()
    if os.path.exists('raw/asx_company.jsonl'):
        for line in open('raw/asx_company.jsonl', encoding='utf-8'):
            try: done.add(json.loads(line)['code'])
            except Exception: pass
    todo = [c for c in codes if c not in done]; print('ASX company records todo', len(todo), 'done', len(done), flush=True)
    out = open('raw/asx_company.jsonl', 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
    def work(c):
        rec = {'code': c, 'src': f'https://www.asx.com.au/markets/company/{c}'}
        for part in ('header', 'key-statistics', 'about'):
            r = get(MK + f'{c.lower()}/{part}?access_token={TOKEN}')
            if r is None or r.status_code != 200: rec[part.replace('-', '_')] = None; rec[part + '_http'] = r.status_code if r is not None else 'none'; continue
            d = (r.json() or {}).get('data') or {}
            if part == 'header': rec['header'] = {k: v for k, v in d.items() if k not in DROP_HDR}
            elif part == 'key-statistics': rec['key_statistics'] = {k: v for k, v in d.items() if k in KEEP_KS}
            else: rec['about'] = {k: d.get(k) for k in ('displayName', 'issueType', 'addressContact', 'addressShareRegistry', 'websiteUrl', 'secretaries', 'indices', 'foreignExempt') if k in d}
        with lock:
            out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 100 == 0: print('asx company', cnt[0], '/', len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '4'))) as ex: list(ex.map(work, todo))
    print('FETCH DONE', flush=True)
