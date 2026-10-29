import json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'door')]
import store, store_index, concurrent.futures as cf
cc = sys.argv[1]; c = store.cont(cc)
names = [b.name for b in c.list_blobs(name_starts_with='door/records/') if b.name.endswith('.json')]
with cf.ThreadPoolExecutor(32) as ex: recs = dict(ex.map(lambda n: (n, json.loads(c.download_blob(n).readall())), names))
new = store_index.build((n.split('/')[2], n.split('/')[3][:-5], r) for n, r in recs.items()); cur = store.bj(c, 'door/index.json')
for kind in ('lei', 'name', 'alias', 'ticker', 'cmr'):
    A, B = cur.get(kind) or {}, new.get(kind) or {}; kinds = {'dup-only': 0, 'set': 0}; ex = []
    for i in set(A) | set(B):
        if A.get(i) == B.get(i): continue
        if set(A.get(i) or []) == set(B.get(i) or []): kinds['dup-only'] += 1
        else:
            kinds['set'] += 1
            if len(ex) < 4: ex.append((i, A.get(i), B.get(i)))
    print(kind, kinds, ex)
