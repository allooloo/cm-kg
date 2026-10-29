r"""DOORS-03 step b/c planning — read only: every record behind an ISIN that resolves to more than one record (dup-isins-before-*.json), read from its
door (GET /record/<venue>/<code>), and each group classed:
  derivative     a Eurex product whose underlying_cmr is the other record           -> fold (listing line, type derivative)
  dual-counter   an HKEX RMB counter (8xxxx, name ending -R) of a HKD counter        -> fold (listing line, type dual-counter)
  same issuer    same LEI, or the same legal name once case and punctuation are set aside -> fold (listing line, type listing)
  different      none of the above                                                    -> leave both; hand item
Writes classes-<UTC stamp>.json beside. Usage: python -X utf8 -I classify_dups.py"""
import json, glob, os, re, datetime, urllib.request, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(sorted(glob.glob(os.path.join(HERE, 'dup-isins-before-*.json')))[-1]))
DOOR = {n['node']: n['door'].rstrip('/') for n in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))}
UA = {'User-Agent': 'Allooloo eco-pages DOORS-03 classify'}   # an Allooloo internal read (gate INTERNAL rule): never metered, never offered
def rec(key):
    node, ex, code = key.split('/', 2)
    try: return json.load(urllib.request.urlopen(urllib.request.Request(f"{DOOR[node]}/record/{ex}/{code}", headers=UA), timeout=40))
    except Exception as e: return {'error': str(e)[:80]}
v = lambda r, f: ((r.get('identity') or {}).get(f) or {}).get('value')
def nk(s): s = re.sub(r'[^a-z0-9]+', ' ', str(s or '').lower().replace('&', ' and ')); return re.sub(r'\b(inc|corp|corporation|co|ltd|limited|plc|sa|se|ag|nv|the|holdings?|group|class|cl|a|b|shs|o n|inh|-r)\b', ' ', s).split()
keys = sorted({k for r in D.values() if r for ks in r['dups'].values() for k in ks})
with cf.ThreadPoolExecutor(16) as ex: R = dict(zip(keys, ex.map(rec, keys)))
out = {}; tally = {}
for cc, r in sorted(D.items()):
    if not r or not r['dups']: continue
    for isin, ks in sorted(r['dups'].items()):
        recs = {k: R[k] for k in ks}; cls = None; primary = None; lines = {}
        eu = [k for k in ks if k.split('/')[1] == 'EUREX']; non = [k for k in ks if k not in eu]
        if eu and len(non) == 1 and all(v(recs[k], 'underlying_cmr') == non[0] for k in eu): cls, primary = 'derivative', non[0]; lines = {k: 'derivative' for k in eu}
        elif cc == 'hk' and len(ks) == 2:
            a, b = sorted(ks, key=lambda k: k.split('/')[2]); ca_, cb = a.split('/')[2], b.split('/')[2]
            if cb.startswith('8') and str(v(recs[b], 'name') or '').upper().endswith('-R'): cls, primary = 'dual-counter', a; lines = {b: 'dual-counter'}
        if not cls:
            leis = {v(recs[k], 'lei') for k in ks}; names = {' '.join(nk(v(recs[k], 'name'))) for k in ks}
            if (len(leis) == 1 and None not in leis and '' not in leis) or len(names) == 1: cls = 'same issuer'
            else: cls = 'different'
        out[f'{cc}:{isin}'] = {'node': f'{cc}-cm-kg', 'isin': isin, 'class': cls, 'primary': primary, 'lines': lines,
                               'records': {k: {'name': v(recs[k], 'name'), 'lei': v(recs[k], 'lei'), 'security_type': v(recs[k], 'security_type'), 'exchange': v(recs[k], 'exchange'), 'events': recs[k].get('event_count'), 'error': recs[k].get('error')} for k in ks}}
        tally.setdefault(cc, {}).setdefault(cls, 0); tally[cc][cls] += 1
for cc, t in tally.items(): print(cc, t)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ')
json.dump(out, open(os.path.join(HERE, f'classes-{stamp}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for k, o in out.items():
    if o['class'] in ('different', 'same issuer'): print(o['class'][:4], k, ' | '.join(f"{kk.split('/',1)[1]}={x['name']} lei={x['lei']}" for kk, x in o['records'].items())[:260])
