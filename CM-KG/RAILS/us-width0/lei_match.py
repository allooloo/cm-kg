"""Step 3 — LEI by legal name through GLEIF (EDGAR carries no LEI or ISIN). Two routes, each recorded with its label:
  a) GET /api/v1/lei-records?filter[entity.legalName]=<name as filed>            'GLEIF name-exact' when one record's legal name equals the EDGAR name
     after case / space / punctuation normalisation and its legal jurisdiction is US-<state of incorporation> (or US when the state is blank)
  b) GET /api/v1/fuzzycompletions?field=fulltext&q=<name>                         candidates; the same name-exact + jurisdiction rule decides
Looser matches stay in Gaps (never a fuzzy fill). Foreign private issuers (state of incorporation outside the United States) are matched on name with
the jurisdiction of the LEI record kept as read. Writes raw/lei_match.jsonl keyed by cik. Resumable."""
import requests, json, time, re, os, threading
from concurrent.futures import ThreadPoolExecutor
h = {'Accept': 'application/vnd.api+json'}
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def norm(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '').replace("'", '').replace('-', ' ').replace('/', ' ')
    s = re.sub(r'\b(INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|PLC|LLC|LP|L P|HOLDINGS|HOLDING|GROUP|THE|NV|N V|SA|S A|AG|SE|PLC)\b', ' ', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
def norm_strict(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper().replace('&', ' AND ')).split())
US_STATES = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR VI GU'.split())
_gate = threading.Lock(); _last = [0.0]
def get(url, params=None, tries=5):
    for i in range(tries):
        with _gate:
            w = 0.2 - (time.time() - _last[0])
            if w > 0: time.sleep(w)
            _last[0] = time.time()
        try:
            r = requests.get(url, params=params, headers=h, timeout=60)
            if r.status_code == 429 or r.status_code >= 500: time.sleep(5 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
def rec_of(x):
    e = x['attributes']['entity']; ra = x['attributes'].get('registration') or {}
    return {'lei': x['id'], 'name': e['legalName']['name'], 'jur': e.get('jurisdiction') or '', 'status': e.get('status'), 'reg_status': ra.get('status'), 'other_names': [n.get('name') for n in (e.get('otherNames') or [])], 'registeredAs': e.get('registeredAs') or '', 'registeredAt': (e.get('registeredAt') or {}).get('id') or ''}
def decide(r, cands, route):
    want = norm_strict(r['name']); wantn = norm(r['name']); st = (r.get('state_inc') or '').upper(); us = st in US_STATES
    exact = [c for c in cands if norm_strict(c['name']) == want or norm_strict(c['name']) == norm_strict(r['name_edgar_list'])]
    if not exact: exact = [c for c in cands if norm(c['name']) == wantn and wantn]
    if not exact:
        for c in cands:
            if any(norm_strict(n) == want for n in c['other_names']): exact.append(c)
    if us: jur_ok = [c for c in exact if c['jur'] == f'US-{st}' or c['jur'] == 'US']
    else: jur_ok = exact
    if len(jur_ok) == 1: return {'lei': jur_ok[0]['lei'], 'match': 'GLEIF name-exact' + (' (jurisdiction US-' + st + ')' if us else ' (foreign incorporation, jurisdiction as read)'), 'route': route, 'rec': jur_ok[0]}
    if len(jur_ok) > 1:
        active = [c for c in jur_ok if c['status'] == 'ACTIVE' and c['reg_status'] in ('ISSUED', 'PENDING_TRANSFER', 'PENDING_ARCHIVAL')]
        if len(active) == 1: return {'lei': active[0]['lei'], 'match': 'GLEIF name-exact (one active record among duplicates)', 'route': route, 'rec': active[0]}
        return {'lei': '', 'gap': 'several GLEIF records share the exact name and jurisdiction: ' + ', '.join(c['lei'] for c in jur_ok[:5]), 'route': route, 'cands': [c['lei'] for c in jur_ok[:5]]}
    if exact and us: return {'lei': '', 'gap': f"name-exact record(s) but jurisdiction {', '.join(sorted({c['jur'] for c in exact}))} is not US-{st}", 'route': route, 'cands': [c['lei'] for c in exact[:5]]}
    return None
def work(r):
    x = get('https://api.gleif.org/api/v1/lei-records', params={'filter[entity.legalName]': r['name'], 'page[size]': 20})
    cands = [rec_of(d) for d in (x.json().get('data') or [])] if x is not None and x.status_code == 200 else []
    d = decide(r, cands, 'legalName filter') if cands else None
    if d is None:
        y = get('https://api.gleif.org/api/v1/fuzzycompletions', params={'field': 'fulltext', 'q': r['name'][:100]})
        ids = [c['relationships']['lei-records']['data']['id'] for c in (y.json().get('data') or []) if c.get('relationships', {}).get('lei-records')] if y is not None and y.status_code == 200 else []
        ids = list(dict.fromkeys(ids))[:15]
        if ids:
            z = get('https://api.gleif.org/api/v1/lei-records', params={'filter[lei]': ','.join(ids), 'page[size]': 20})
            c2 = [rec_of(d2) for d2 in (z.json().get('data') or [])] if z is not None and z.status_code == 200 else []
            d = decide(r, c2, 'fuzzycompletions') if c2 else None
            if d is None: d = {'lei': '', 'gap': 'no GLEIF record with the exact legal name (' + str(len(c2)) + ' fuzzy candidates, none exact)', 'route': 'fuzzycompletions', 'cands': [c['lei'] for c in c2[:5]], 'cand_names': [c['name'] for c in c2[:5]]}
        else: d = {'lei': '', 'gap': 'no GLEIF candidate for this name', 'route': 'fuzzycompletions'}
    d['cik'] = r['cik']; d['key'] = r['exchange'] + '|' + r['symbol']; return d
fn = 'raw/lei_match.jsonl'; done = set()
if os.path.exists(fn):
    for line in open(fn, encoding='utf-8'):
        try: done.add(json.loads(line)['cik'])
        except Exception: pass
todo = {}
for r in rows:
    if r['cik'] not in done and r['cik'] not in todo: todo[r['cik']] = r
todo = list(todo.values()); print('lei_match todo', len(todo), 'done', len(done), flush=True)
out = open(fn, 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
def run(r):
    try: d = work(r)
    except Exception as e: d = {'cik': r['cik'], 'key': r['exchange'] + '|' + r['symbol'], 'lei': '', 'gap': 'error ' + repr(e)[:120]}
    with lock:
        out.write(json.dumps(d, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
        if cnt[0] % 250 == 0: print('lei_match', cnt[0], '/', len(todo), flush=True)
with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '3'))) as ex: list(ex.map(run, todo))
allm = [json.loads(l) for l in open(fn, encoding='utf-8')]
print('lei_match DONE', 'matched', sum(1 for d in allm if d.get('lei')), 'of', len(allm), flush=True)
