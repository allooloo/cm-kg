r"""eu_backfill.py — BACKFILL-01 adapter 'eu-node-events' (DAY ORDER 7, 2026-10-25): the European and ROW nodes' own events readers pointed backward.
The roster is the node's latest roster drop in the pond (width0/<date>/roster.json, what the live node serves — read, never re-harvested here); each issuer's
events come from the market's own reader (RAILS\eu-sources|row-sources\<cc>\events.py fetch(isin, since)), the same code the nightly runs, with `since`
opened back to the backfill window. Row fields as eu_node.py writes them (the live row). Paced: one worker per pace rps of the policy line.
Usage: python -X utf8 eu_backfill.py <cc> <since> <out.jsonl>"""
import os, sys, json, glob, importlib.util, time, hashlib
from concurrent.futures import ThreadPoolExecutor
ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO'); RAILS = os.path.join(ROOT, 'CM-KG', 'RAILS'); POND = os.path.join(ROOT, 'CM-KG', 'POND')
CC, SINCE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; NODE = f'{CC}-cm-kg'
POL = json.load(open(os.environ.get('BACKFILL_POLICY') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'policy.json'), encoding='utf-8'))['markets'][CC]
VENUES = json.load(open(os.path.join(RAILS, 'eu-node', 'venues.json'), encoding='utf-8'))[CC]
def mod(name):
    p = os.path.join(RAILS, 'eu-sources', CC, name + '.py')
    if not os.path.exists(p): p = os.path.join(RAILS, 'row-sources', CC, name + '.py')
    s = importlib.util.spec_from_file_location(f'{CC}_{name}', p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
drops = sorted(glob.glob(os.path.join(POND, NODE, 'width0', '*', 'roster.json')))
if not drops: raise SystemExit(f'no roster drop for {NODE} in the pond (width0/<date>/roster.json): the node must have run once')
ro = json.load(open(drops[-1], encoding='utf-8')); roster = ro['rows']
print(NODE, 'roster drop', os.path.basename(os.path.dirname(drops[-1])), len(roster), 'issuers · since', SINCE, flush=True)
ev = mod('events'); rps = max(1, int((POL.get('pace') or {}).get('rps') or 1))
done = set()
if os.path.exists(OUT + '.part'):
    for l in open(OUT + '.part', encoding='utf-8'):
        try: done.add(json.loads(l)['key'])
        except Exception: pass
out = open(OUT + '.part', 'a', encoding='utf-8')   # resumable: the cursor is the issuers already read
def one(r):
    t0 = time.time()
    try: res = ev.fetch(r['isin'], SINCE) or []
    except Exception as e: res = e
    time.sleep(max(0, 1.0 - (time.time() - t0)))   # each worker at most one call a second; workers = the policy's rps
    return r, res
todo = [r for r in roster if r['isin'] not in done]; errs = 0
with ThreadPoolExecutor(rps) as ex:
    for r, res in ex.map(one, todo):
        if isinstance(res, Exception): errs += 1; out.write(json.dumps({'key': r['isin'], 'error': repr(res)[:200]}) + '\n'); continue
        evs = [{'exchange': VENUES.get(r.get('mic'), r.get('mic')), 'ticker': r['isin'], 'isin': r['isin'], 'issuer': r.get('name'), 'date': str(e['date'])[:10], 'event_type': e.get('type') or 'regulatory_filing',
                'title': e.get('title'), 'url': e['url'], 'source': e.get('source'), 'read_by': e.get('source') or 'the regulated-information store', 'state': 'sourced', 'category': e.get('type')} for e in res if e.get('date') and e.get('url')]
        out.write(json.dumps({'key': r['isin'], 'events': evs}, ensure_ascii=False) + '\n'); out.flush()
out.close(); os.replace(OUT + '.part', OUT)
print(NODE, 'read errors', errs, '->', OUT, flush=True)
