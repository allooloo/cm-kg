r"""DOORS-04 (2026-10-26) — read only: the ISINs still on more than one record (dup-isins-after-*.json of DOORS-03), every record behind them read from its door,
with the ISIN field as served (value, source_url, read_by, state) and the identifiers that can settle it (LEI, CIK, CUSIP, corporate number, register ids).
Writes groups-<UTC stamp>.json beside. Usage: python -X utf8 -I read_groups.py"""
import json, glob, os, datetime, urllib.request, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(sorted(glob.glob(r'C:\ALLOOLOO\CM-KG\RAILS\doors-03\dup-isins-after-*.json'))[-1]))
DOOR = {n['node']: n['door'].rstrip('/') for n in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))}
UA = {'User-Agent': 'Allooloo eco-pages DOORS-04 read'}
def rec(k):
    node, ex, code = k.split('/', 2)
    return json.load(urllib.request.urlopen(urllib.request.Request(f'{DOOR[node]}/record/{ex}/{code}', headers=UA), timeout=40))
keys = sorted({k for r in A.values() if r for ks in r['dups'].values() for k in ks})
with cf.ThreadPoolExecutor(12) as ex: R = dict(zip(keys, ex.map(rec, keys)))
out = {}
for cc, r in sorted(A.items()):
    for isin, ks in sorted((r or {}).get('dups', {}).items()):
        out[f'{cc}:{isin}'] = {k: {'name': (R[k]['identity'].get('name') or {}).get('value'), 'isin': R[k]['identity'].get('isin'),
                                  'other_ids': {f: (R[k]['identity'].get(f) or {}).get('value') for f in R[k]['identity'] if f in ('lei', 'cik', 'cusip', 'corporate_number', 'figi', 'sedar_profile', 'security_type', 'exchange', 'tier')}} for k in ks}
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ')
json.dump(out, open(os.path.join(HERE, f'groups-{stamp}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for g, recs in out.items():
    print('==', g)
    for k, x in recs.items(): print('  ', k.split('/', 1)[1], '|', x['name'], '| src:', (x['isin'] or {}).get('source_url', '')[:90], '| by:', (x['isin'] or {}).get('read_by', '')[:70], '| state:', (x['isin'] or {}).get('state'), '|', {a: b for a, b in x['other_ids'].items() if b and a in ('cik', 'cusip', 'corporate_number', 'figi')})
