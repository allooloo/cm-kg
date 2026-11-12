import sys, json
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\isin-dis'); import store
cc = sys.argv[1]; c = store.cont(cc)
for n in ('door/facts.json', 'backfill/facts.json', 'door/halts.json', 'door/events-by-type.json', 'door/index.json'):
    try:
        j = store.bj(c, n)
        if n.endswith('index.json'): print(n, list(j.keys()), len(j.get('keys', [])), j['keys'][:3])
        elif n.endswith('by-type.json'): print(n, {k: (v if k != 'types' else {t: len(x) for t, x in v.items()}) for k, v in j.items()}, json.dumps(next((x[0] for x in j['types'].values() if x), None))[:400])
        else: print(n, json.dumps(j)[:1500])
    except Exception as e: print(n, 'ERR', repr(e)[:120])
k = store.bj(c, 'door/index.json')['keys'][0].split('/')
r = store.bj(c, f'door/records/{k[1]}/{k[2]}.json'); print({x: (v if x != 'identity' else list(v.keys())) for x, v in r.items()})
e = store.bj(c, f'door/events/{k[1]}/{k[2]}.json'); print(len(e), json.dumps(e[:2])[:1200])
print([b.name for b in c.list_blobs(name_starts_with='backfill/replay/')][:5])
