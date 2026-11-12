import sys, json, collections
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\isin-dis'); import store
out = {}
for cc in ('ch', 'kr'):
    c = store.cont(cc); keys = set(store.bj(c, 'door/index.json')['keys']); names = [b.name for b in c.list_blobs(name_starts_with='door/records/') if b.name.endswith('.json')]
    allk = {f"{cc}-cm-kg/{n.split('/')[2]}/{n.split('/', 3)[3][:-5]}" for n in names}; miss = sorted(allk - keys); rows = []
    for k in miss:
        _, ex, code = k.split('/', 2); r = store.bj(c, f'door/records/{ex}/{code}.json'); i = r.get('identity', {}); v = lambda f: (i.get(f) or {}).get('value')
        rows.append({'cmr': k, 'name': v('name'), 'exchange': v('exchange'), 'security_type': v('security_type'), 'isin': v('isin'), 'kind': r.get('kind'), 'parent': r.get('parent'), 'folded_into': r.get('folded_into') or r.get('folded') or r.get('listing_of'), 'as_of': r.get('as_of'), 'status': v('status'), 'top_keys': sorted(k2 for k2 in r if k2 not in ('identity', 'aliases', 'gaps'))})
    out[cc] = rows; print(cc, 'record blobs', len(allk), 'keys', len(keys), 'not in keys', len(miss), 'facts', store.bj(c, 'door/facts.json')['nodes'][f'{cc}-cm-kg'])
    print(collections.Counter((r['exchange'], r['security_type'], r['kind'], bool(r['parent']), r['as_of']) for r in rows).most_common(12)); print(json.dumps(rows[:2], ensure_ascii=False)[:900])
json.dump(out, open(r'C:\ALLOOLOO\SITE\USR-01\trace246.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
