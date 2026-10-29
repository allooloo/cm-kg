r"""SHELF-01 step 6 — the shelf lights itself, market by market, as each market seals: no hand.
Triggered by the order ledger, not the clock: for every market whose ledger entry is complete, any sealed year whose newest manifest has no Replay split
built from it gets one (replay_index.py); the market is scored (score.py) when its score is older than its newest manifest; the newest full sealed year
gets a bench (bench.py) and every sealed year a review (review.py) when the published one is missing or was built from another manifest.
A market named in hold.json never lights (ca: held by the CEO until its vintage passes the memo's proofs). Run nightly by the apex job (it reaches every node store and the apex store); a step that fails is logged and holds nothing but its own market.
Writes shelf/state.json (apex store): per market, what is lit per tool and from which manifest — the pages read it.
Usage: python -X utf8 auto.py [cc ...] [--dry]"""
import os, sys, json, re, subprocess, datetime
if os.environ.get('CONTAINER_APP_JOB_EXECUTION_NAME', '').startswith('cmkg-apex'):   # the apex identity holds Contributor (keys), not blob data roles: read every store by key
    os.environ.pop('IDENTITY_ENDPOINT', None); os.environ.pop('MSI_ENDPOINT', None)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'isin-dis'), os.path.join(HERE, '..', 'backfill')]
import store, backfill as BF
from replay_index import newest_manifest
from bench import apex_cont
PY = sys.executable
def sh(*a):
    p = subprocess.run([PY, '-X', 'utf8', *a], cwd=HERE, capture_output=True, text=True, encoding='utf-8', errors='replace'); return p.returncode, (p.stdout + p.stderr)[-600:]
def door_tools():
    """tools/list on each live market door (public, read-only): which doors answer get_timeline and list_events tonight"""
    import urllib.request
    out = {'get_timeline': [], 'list_events': [], 'read_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    for cc, n in store.NODES.items():
        if not n.get('live'): continue
        d = (n.get('door') or '').rstrip('/'); d = d if d.endswith('/mcp') else d + '/mcp'
        try:
            r = urllib.request.urlopen(urllib.request.Request(d, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}).encode(), headers={'content-type': 'application/json', 'accept': 'application/json, text/event-stream', 'user-agent': 'Allooloo shelf state (SHELF-01)'}), timeout=20)
            t = r.read().decode(); names = [x['name'] for x in json.loads(t[t.index('{'):])['result']['tools']]
            for k in ('get_timeline', 'list_events'):
                if k in names: out[k].append(cc)
        except Exception: pass
    return out
def restart_door(app):
    """restart the door's latest revision so it reads what was just published; a failure is flagged, never fatal"""
    def az(*a):
        p = subprocess.run(['az', *a, '-o', 'tsv'], capture_output=True, text=True, encoding='utf-8', errors='replace', shell=os.name == 'nt')
        if p.returncode != 0: raise RuntimeError((p.stderr or p.stdout)[-200:])
        return p.stdout.strip()
    try:
        rg, rev = az('containerapp', 'list', '--query', f"[?name=='{app}'] | [0].[resourceGroup, properties.latestRevisionName]").split()
        az('containerapp', 'revision', 'restart', '-g', rg, '-n', app, '--revision', rev); return 'restarted ' + rev
    except Exception as e: return 'failed (flagged): ' + repr(e)[:160]
def blob_json(c, n):
    try: return json.loads(c.download_blob(n).readall())
    except Exception: return None
def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; dry = '--dry' in sys.argv
    order = [c for c in BF.POL['order']] if hasattr(BF, 'POL') else []
    want = a or [c for c in order if c in store.NODES]
    shelf = apex_cont('shelf')
    try: shelf.create_container()
    except Exception: pass
    state = blob_json(shelf, 'state.json') or {'markets': {}}; log = []
    H = json.load(open(os.path.join(HERE, 'hold.json'), encoding='utf-8'))
    for cc in want:
        if cc in H['markets']: state['markets'].setdefault(cc, {}).update({'lit': False, 'held': H['markets'][cc]}); print(cc, 'held:', H['markets'][cc]); continue
        led = BF.order_get(cc)
        if not (led and led.get('complete')): state['markets'].setdefault(cc, {})['lit'] = False; continue
        c = store.cont(cc); ys = sorted({int(b.name.split('/')[1]) for b in c.list_blobs(name_starts_with='backfill/') if re.match(r'backfill/\d{4}/manifest', b.name)})
        m = state['markets'].setdefault(cc, {}); m['lit'] = True; m['years'] = ys; m['ledger_updated'] = led.get('updated_utc')
        man = {y: newest_manifest(c, y) for y in ys}; roots = {y: (blob_json(c, man[y]) or {}).get('hash_tree_root') for y in ys}
        todo_replay = [y for y in ys if (blob_json(c, f'backfill/replay/{y}/_manifest.json') or {}).get('hash_tree_root') != roots[y]]
        steps = []
        if todo_replay: steps.append(('replay', ['replay_index.py', cc, *map(str, todo_replay)]))
        elif ys: m.setdefault('tools', {}).setdefault('replay', {'exit': 0, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'note': 'every sealed year split from its current manifest'})   # a split built outside this run (us, laptop 2026-10-28) counts once it matches
        if todo_replay or not c.get_blob_client('door/score/_tables.json').exists(): steps.append(('score', ['score.py', cc]))
        full = [y for y in ys if y < datetime.date.today().year]
        if full:
            yb = H.get('bench_year') if H.get('bench_year') in full else max(full); m['bench_years'] = [yb]; b =blob_json(shelf, f'bench/bench-{cc}-{yb}.json')   # the memo's bench year (2024) where sealed
            if not b or b['manifest']['hash_tree_root'] != roots[yb]: steps.append(('bench', ['bench.py', 'build', cc, str(yb)]))
        for y in ys:
            r = blob_json(shelf, f'review/review-{cc}-{y}.json')
            if not r or r['manifest']['hash_tree_root'] != roots[y]: steps.append(('review', ['review.py', cc, str(y)]))
        for tool, args in steps:
            rc, out = (0, 'dry') if dry else sh(*args)
            log.append({'market': cc, 'tool': tool, 'args': args[1:], 'exit': rc, 'tail': out[-300:]}); print(cc, tool, args[1:], 'exit', rc, flush=True)
            m.setdefault('tools', {})[tool] = {'exit': rc, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        m['manifests'] = {str(y): roots[y] for y in ys}
        if not dry:   # the doors keep what they read until a revision restart (no-expiry cache), as the nightly does after its upload (SHELF-01 2026-10-28)
            ran = {t for t, _ in steps}
            for app in ([f'cmkg-door-{cc}'] if ran & {'replay', 'score'} else []) + (['cmkg-door-bench'] if 'bench' in ran else []) + (['cmkg-door-review'] if 'review' in ran else []):
                m.setdefault('door_restart', {})[app] = restart_door(app)
    state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # the door tools as the market doors answer them tonight (Timeline and Events are served once a door lists them)
    state['door_tools'] = door_tools()
    if not dry: shelf.upload_blob('state.json', json.dumps(state, ensure_ascii=False, indent=1).encode(), overwrite=True)
    # the public summary the seven pages read (no ledger internals): per tool, the markets lit and their years
    pub = {'updated_utc': state['updated_utc'], 'source': 'the order ledger (backfill-order) and the shelf state; a market lights per tool only when its ledger entry is complete and its manifests verify',
           'door_tools': state['door_tools'],   # holds stay in the private state only
           'tools': {t: {k: (v.get('bench_years') if t == 'bench' else None) or v.get('years') for k, v in state['markets'].items() if v.get('lit') and v.get('tools', {}).get(t, {}).get('exit') == 0} for t in ('replay', 'score', 'bench', 'review')}}
    est = os.path.join(os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO' if os.name == 'nt' else '/job/ALLOOLOO'), 'CM-KG', 'ESTATE', 'public', 'shelf')
    if not dry and os.path.isdir(os.path.dirname(est)):
        os.makedirs(est, exist_ok=True); json.dump(pub, open(os.path.join(est, 'state.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: {'lit': v.get('lit'), 'years': v.get('years')} for k, v in state['markets'].items() if v.get('lit')}))
if __name__ == '__main__': main()
