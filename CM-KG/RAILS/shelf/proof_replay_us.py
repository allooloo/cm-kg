r"""SHELF-01 proof (Replay, us) — get_record(as_of) through the market door and through the apex router must answer the sealed lines of the
market-year to that date, as sealed (same lines, each row's own signature intact), from the year's manifest; a date in an unsealed year answers "not sealed".
Usage: python -X utf8 -I proof_replay_us.py [EX:CODE] [YYYY-MM-DD]"""
import os, sys, json, datetime, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'isin-dis'), os.path.join(HERE, '..', 'door')]
import store, store_index
a = sys.argv[1:]; who = next((x for x in a if ':' in x), 'NASDAQ:AAPL'); asof = next((x for x in a if x[:2] == '20' and '-' in x), '2023-06-30')
ex, code = who.split(':'); y = int(asof[:4]); c = store.cont('us')
APEX = 'https://mcp.getissuer.ai/mcp'; DOOR = (store.NODES['us'].get('door') or '').rstrip('/'); DOOR = DOOR if DOOR.endswith('/mcp') else DOOR + '/mcp'
def call(u, args):
    r = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'get_record', 'arguments': args}}).encode(),
                               headers={'content-type': 'application/json', 'accept': 'application/json, text/event-stream', 'user-agent': 'Allooloo SHELF-01 proof'}), timeout=120)
    t = r.read().decode(); res = json.loads(t[t.index('{'):])['result']
    sc = res.get('structuredContent')
    return sc if sc is not None else json.loads(res['content'][0]['text'])
rp = json.loads(c.download_blob(f'backfill/replay/{y}/{ex}/{store_index.slug(code)}.json').readall())
man = json.loads(c.download_blob(f'backfill/replay/{y}/_manifest.json').readall())
want = [r for r in rp['rows'] if r['date'][:10] <= asof]
out = {'issuer': who, 'as_of': asof, 'manifest': {'name': rp['manifest']['name'], 'root': man['hash_tree_root'], 'rows': man['rows']}, 'sealed_lines_to_date': len(want)}
key = lambda r: (r.get('date'), r.get('url'), r.get('event_type'), (r.get('signature') or {}).get('signature'))
for name, u in (('door', DOOR), ('apex', APEX)):
    try:
        d = call(u, {'identifier': who, 'as_of': asof}); s = json.dumps(d)
        lines = d.get('events_as_of') or d.get('lines') or d.get('rows') or d.get('events') or (d.get('replay') or {}).get('lines') or []
        got = sorted(map(key, lines), key=str); exp = sorted(map(key, want), key=str)
        out[name] = {'lines': len(lines), 'same_lines_and_signatures': got == exp, 'manifest_root_cited': man['hash_tree_root'] in s, 'keys': sorted(d)[:20]}
    except Exception as e: out[name] = {'error': f'{type(e).__name__}: {str(e)[:200]}'}
for name, u in (('door_unsealed', DOOR), ('apex_unsealed', APEX)):
    try: d = call(u, {'identifier': who, 'as_of': '2027-03-31'}); s = json.dumps(d); out[name] = {'not_sealed': 'not sealed' in s.lower(), 'said': s[:240]}
    except Exception as e: out[name] = {'error': f'{type(e).__name__}: {str(e)[:200]}'}
out['PASS'] = all(out.get(k, {}).get('same_lines_and_signatures') and out[k].get('manifest_root_cited') for k in ('door', 'apex')) and all(out.get(k, {}).get('not_sealed') for k in ('door_unsealed', 'apex_unsealed'))
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(HERE, f'proof-replay-us-{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")}.json'), 'w'), indent=1)
