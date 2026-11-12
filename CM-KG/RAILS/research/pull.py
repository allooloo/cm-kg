r"""pull.py — USR-01 (2026-11-11): one node's door store read into a dated, immutable pond drop for the research roll-up.
Reads only what the node already holds (account allooloocmkg<cc>pond, container pond): door/index.json (keys), door/facts.json, door/events-by-type.json,
backfill/facts.json, the backfill/replay/<year>/ blob names (which sealed years hold the issuer), every door/records/<EX>/<code>.json and
door/events/<EX>/<code>.json. Nothing is written to the store. The drop: CM-KG\POND\<cc>-cm-kg\research\<date>[-n]\
  records.jsonl   one record per line, as stored
  events.jsonl    one line per issuer: the event lines reduced to (date, event_type, category, title, url, source, reference)
  node.json       facts, lifecycle index, backfill facts, sealed years per issuer key, counts
Usage: python -X utf8 pull.py <cc> [<cc> ...]     exit 1 on any failed node"""
import sys, os, json, datetime, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'isin-dis')); import store
POND = r'C:\ALLOOLOO\CM-KG\POND'; TODAY = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
def drop_dir(cc):
    base = os.path.join(POND, f'{cc}-cm-kg', 'research'); os.makedirs(base, exist_ok=True); d = os.path.join(base, TODAY); n = 1
    while os.path.exists(d): n += 1; d = os.path.join(base, f'{TODAY}-{n}')
    os.makedirs(d); return d
def opt(c, n):
    try: return store.bj(c, n)
    except Exception as e:
        if 'BlobNotFound' in repr(e) or 'does not exist' in repr(e): return None
        raise
def pull(cc):
    c = store.cont(cc); idx = store.bj(c, 'door/index.json'); keys = idx['keys']
    node = {'node': f'{cc}-cm-kg', 'pulled_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'facts': opt(c, 'door/facts.json'), 'lifecycle': opt(c, 'door/events-by-type.json'), 'backfill': opt(c, 'backfill/facts.json')}
    sealed = {}
    for b in c.list_blobs(name_starts_with='backfill/replay/'):
        p = b.name.split('/')
        if len(p) == 5 and p[4].endswith('.json'): sealed.setdefault(f'{cc}-cm-kg/{p[3]}/{p[4][:-5]}', []).append(p[2])
    node['sealed_years'] = {k: sorted(v) for k, v in sealed.items()}
    def rd(k):
        _, ex, code = k.split('/', 2); rec = opt(c, f'door/records/{ex}/{code}.json'); ev = opt(c, f'door/events/{ex}/{code}.json') if rec else None
        return k, rec, [{x: e.get(x) for x in ('date', 'event_type', 'category', 'title', 'url', 'source', 'reference') if e.get(x) not in (None, '')} for e in (ev or [])]
    d = drop_dir(cc); miss = 0; nev = 0
    with cf.ThreadPoolExecutor(32) as ex, open(os.path.join(d, 'records.jsonl'), 'w', encoding='utf-8') as fr, open(os.path.join(d, 'events.jsonl'), 'w', encoding='utf-8') as fe:
        for k, rec, ev in ex.map(rd, keys):
            if rec is None: miss += 1; continue
            fr.write(json.dumps(rec, ensure_ascii=False, separators=(',', ':')) + '\n'); fe.write(json.dumps({'cmr': k, 'events': ev}, ensure_ascii=False, separators=(',', ':')) + '\n'); nev += len(ev)
    node['counts'] = {'keys': len(keys), 'records_read': len(keys) - miss, 'records_missing': miss, 'event_lines': nev}
    json.dump(node, open(os.path.join(d, 'node.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(cc, d, node['counts'], flush=True)
bad = 0
for cc in sys.argv[1:]:
    try: pull(cc)
    except Exception as e: bad += 1; print(cc, 'FAILED', repr(e)[:300], flush=True)
sys.exit(1 if bad else 0)
