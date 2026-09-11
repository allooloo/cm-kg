"""Step 1 — pull the four exchange rosters and the TMX listed-companies workbook into raw/.
Sources (all public, no login):
  TSX / TSXV roster ........ https://www.tsx.com/json/company-directory/search/{tsx|tsxv}/^*
  TMX listed companies ..... https://www.tsx.com/en/resource/571  (monthly xlsx: sector, sub-sector, HQ province, listing date/type)
  CSE roster ............... https://thecse.com/api/webapi/listed-companies/
  Cboe Canada roster ....... https://www-api.cboe.com/ca/equities/listing-directory-data/
  GLEIF ISIN-to-LEI file ... https://mapping.gleif.org/api/v2/isin-lei/latest  (daily zip, ~32 MB)
"""
import requests, json, os, re, sys
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
os.makedirs('raw', exist_ok=True)
def get(url, fn, **kw):
    r = requests.get(url, headers=UA, timeout=180, **kw); r.raise_for_status()
    open(fn, 'wb').write(r.content); print(fn, len(r.content), 'bytes', flush=True); return r
for ex in ('tsx', 'tsxv'):
    r = get(f'https://www.tsx.com/json/company-directory/search/{ex}/%5E*', f'raw/{ex}.json')
    print('  ', ex, 'length', r.json().get('length'))
get('https://www.tsx.com/en/resource/571', 'raw/tmx_571.xlsx')
r = get('https://thecse.com/api/webapi/listed-companies/', 'raw/cse_list.json', params=None)
print('   CSE securities', len(r.json()))
r = get('https://www-api.cboe.com/ca/equities/listing-directory-data/', 'raw/cboe.json')
print('   Cboe securities', len(r.json()['data']))
# CSE Next.js build id (needed by enrich.py cse to read company page data)
h = requests.get('https://thecse.com/listing/listed-companies/', headers={'User-Agent': UA['User-Agent']}, timeout=120).text
m = re.search(r'/_next/static/([A-Za-z0-9_-]+)/_buildManifest\.js', h)
if not m: sys.exit('CSE build id not found — thecse.com layout changed')
open('raw/cse_build_id.txt', 'w').write(m.group(1)); print('   CSE build id', m.group(1))
if '--no-gleif' not in sys.argv:
    meta = requests.get('https://mapping.gleif.org/api/v2/isin-lei/latest', headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()['data']['attributes']
    get(meta['downloadLink'], 'raw/isin-lei-latest.zip'); open('raw/isin-lei-latest.txt', 'w').write(meta['fileName'])
    print('   GLEIF mapping file', meta['fileName'])
print('FETCH DONE')
