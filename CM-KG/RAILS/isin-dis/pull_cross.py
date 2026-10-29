r"""ISIN disambiguation (2026-10-27) — read only: the record files behind every cross-node ISIN (cross-excl-eurex.json beside), identity only,
to read what each node's own source says about the line (secondary, foreign, primary venue). Writes cross-records.json beside."""
import json, os, re, concurrent.futures as cf, store
HERE = os.path.dirname(os.path.abspath(__file__))
cross = json.load(open(os.path.join(HERE, 'cross-excl-eurex.json'), encoding='utf-8'))
want = {}
for i, w in cross.items():
    for cc, ks in w.items(): want.setdefault(cc, set()).update(ks)
slug = lambda t: re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
def node(cc):
    c = store.cont(cc); out = {}
    def one(k):
        try: r = store.bj(c, f"door/records/{k.split('/')[1]}/{slug(k.split('/', 2)[2])}.json")
        except Exception as e: return k, {'error': repr(e)[:120]}
        idn = r.get('identity') or {}
        return k, {'cmr': r.get('cmr'), 'parent': r.get('parent'), 'listings': [l['cmr'] for l in r.get('listings') or []],
                   'id': {f: (x.get('value') if isinstance(x, dict) else x) for f, x in idn.items() if not isinstance(x, (list,)) and f not in ('trading_hours', 'tes_profiles', 'expirations', 'contracts')}}
    with cf.ThreadPoolExecutor(16) as ex: out.update(dict(ex.map(one, sorted(want[cc]))))
    return cc, out
recs = {}
with cf.ThreadPoolExecutor(8) as ex:
    for cc, o in ex.map(node, sorted(want)): recs.update(o); print(cc, len(o), flush=True)
json.dump(recs, open(os.path.join(HERE, 'cross-records.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
