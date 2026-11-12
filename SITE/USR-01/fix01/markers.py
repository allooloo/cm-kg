r"""markers.py — FIX-01: last night's run as each market's own store records it (sweeps/<night>/<cc>/done.json | failed.json | skipped.json), all 34 markets,
plus each market's Tavily guard ledger figures and its research step. Read only. Writes fix01\markers-<night>.json. Usage: python -X utf8 markers.py <night>"""
import json, sys, os
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\isin-dis'); sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\job'); import store, roster
night = sys.argv[1]; out = {}
for n in roster.load():
    cc = roster.cc_of(n); m = {}
    try:
        c = store.cont(cc)
        for k in ('done', 'failed', 'skipped'):
            try: m[k] = json.loads(c.download_blob(f'sweeps/{night}/{cc}/{k}.json').readall()); break
            except Exception: pass
        try: m['manifest'] = bool(c.get_blob_client(f'research/out/{night}/manifest.json').exists())
        except Exception: m['manifest'] = None
    except Exception as e: m['error'] = repr(e)[:200]
    out[cc] = m; d = m.get('done') or {}; g = d.get('tavily_guard') or {}; r = d.get('research') or {}; pg = r.get('pages') or {}; cv = r.get('coverage') or {}
    print(cc, 'done' if 'done' in m else 'FAILED' if 'failed' in m else 'skipped' if 'skipped' in m else 'NO MARKER', 'held' if d.get('held') else '', '| tavily', g.get('credits'), g.get('calls'), g.get('denied'), g.get('ceiling') or g.get('run_ceiling'), (g.get('stopped') or '')[:40],
          '| research', r.get('ok'), pg.get('pages'), pg.get('changed'), pg.get('new'), 'manifest' if m.get('manifest') else 'no manifest', '| cov', {k: v for k, v in cv.items() if k != 'tail'} if cv else None, '|', str((m.get('failed') or {}).get('error') or r.get('error') or '')[:120], flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'markers-{night}.json'), 'w'), indent=1)
