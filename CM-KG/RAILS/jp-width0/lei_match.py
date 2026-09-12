"""Step 3 — LEI through GLEIF for every roster line. Route a) the register key: GLEIF records for Japanese companies are registered at RA000412 (the
legal affairs bureau corporate registry) with registeredAs = the 12-digit company registration number (会社法人等番号) written XXXX-XX-XXXXXX; the
EDINET corporate number (法人番号, 13 digits) is that number with a leading check digit, so the key is derived exactly, no name matching:
  GET /api/v1/lei-records?filter[entity.registeredAs]=XXXX-XX-XXXXXX  → 'GLEIF registeredAs = EDINET corporate number (RA000412)'
Route b) when the roster line has no corporate number (no EDINET filer joined, or a foreign issuer): fuzzycompletions on the English name; a candidate
becomes the LEI only when one of its names (legal or other) equals the JPX / EDINET English name after normalisation ('GLEIF name-exact'); looser
matches stay in Gaps. Writes raw/lei_match.jsonl keyed by symbol. Resumable."""
import requests, json, time, re, os, threading
from concurrent.futures import ThreadPoolExecutor
h = {'Accept': 'application/vnd.api+json'}
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def norm(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '')).split())
def norm_loose(s):
    s = norm(s); return ' '.join(w for w in s.split() if w not in {'CO', 'LTD', 'INC', 'CORP', 'CORPORATION', 'COMPANY', 'LIMITED', 'KK', 'KABUSHIKI', 'KAISHA', 'HOLDINGS', 'HOLDING', 'GROUP', 'THE'})
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
    return {'lei': x['id'], 'name': e['legalName']['name'], 'jur': e.get('jurisdiction') or '', 'status': e.get('status'), 'reg_status': ra.get('status'), 'other_names': [(n.get('name'), n.get('type'), n.get('language')) for n in (e.get('otherNames') or [])], 'registeredAs': e.get('registeredAs') or '', 'registeredAt': (e.get('registeredAt') or {}).get('id') or ''}
def reg_key(cn):
    cn = re.sub(r'\D', '', cn or '')
    return f'{cn[1:5]}-{cn[5:7]}-{cn[7:]}' if len(cn) == 13 else ''
def work(r):
    key = r['exchange'] + '|' + r['symbol']; cn = r.get('corporate_number') or ''; rk = reg_key(cn)
    if rk:
        x = get('https://api.gleif.org/api/v1/lei-records', params={'filter[entity.registeredAs]': rk, 'page[size]': 10})
        cands = [rec_of(d) for d in (x.json().get('data') or [])] if x is not None and x.status_code == 200 else []
        jp = [c for c in cands if c['registeredAt'] == 'RA000412' or c['jur'] == 'JP']
        if len(jp) == 1: return {'key': key, 'lei': jp[0]['lei'], 'match': 'GLEIF registeredAs = EDINET corporate number (RA000412)', 'route': 'registeredAs', 'registeredAs': rk, 'rec': jp[0]}
        if len(jp) > 1:
            act = [c for c in jp if c['status'] == 'ACTIVE' and c['reg_status'] in ('ISSUED', 'PENDING_TRANSFER', 'PENDING_ARCHIVAL')]
            if len(act) == 1: return {'key': key, 'lei': act[0]['lei'], 'match': 'GLEIF registeredAs = EDINET corporate number (one active record among duplicates)', 'route': 'registeredAs', 'registeredAs': rk, 'rec': act[0]}
            return {'key': key, 'lei': '', 'gap': 'several GLEIF records carry this company registration number: ' + ', '.join(c['lei'] for c in jp[:5]), 'route': 'registeredAs', 'registeredAs': rk}
        gap0 = f'no GLEIF record registered as {rk} (RA000412)'
    else: gap0 = 'no corporate number on the roster line (no EDINET filer joined)' if not r.get('foreign') else 'foreign issuer: no Japanese corporate number'
    names = [n for n in (r.get('name'), r.get('name_en_edinet')) if n]
    y = get('https://api.gleif.org/api/v1/fuzzycompletions', params={'field': 'fulltext', 'q': names[0][:100]})
    ids = list(dict.fromkeys(c['relationships']['lei-records']['data']['id'] for c in (y.json().get('data') or []) if c.get('relationships', {}).get('lei-records')))[:15] if y is not None and y.status_code == 200 else []
    if not ids: return {'key': key, 'lei': '', 'gap': gap0 + '; no GLEIF fuzzy candidate for the English name', 'route': 'fuzzycompletions'}
    z = get('https://api.gleif.org/api/v1/lei-records', params={'filter[lei]': ','.join(ids), 'page[size]': 20})
    cands = [rec_of(d) for d in (z.json().get('data') or [])] if z is not None and z.status_code == 200 else []
    want = {norm(n) for n in names}; wantl = {norm_loose(n) for n in names}
    exact = [c for c in cands if norm(c['name']) in want or any(norm(n[0]) in want for n in c['other_names'])]
    if not exact: exact = [c for c in cands if norm_loose(c['name']) in wantl or any(norm_loose(n[0]) in wantl for n in c['other_names'])]
    if not r.get('foreign'): exact = [c for c in exact if c['jur'] == 'JP']
    if len(exact) == 1: return {'key': key, 'lei': exact[0]['lei'], 'match': 'GLEIF name-exact (English name against the legal or other names' + ('' if r.get('foreign') else ', jurisdiction JP') + ')', 'route': 'fuzzycompletions', 'rec': exact[0]}
    if len(exact) > 1: return {'key': key, 'lei': '', 'gap': 'several GLEIF records match the English name exactly: ' + ', '.join(c['lei'] for c in exact[:5]), 'route': 'fuzzycompletions'}
    return {'key': key, 'lei': '', 'gap': gap0 + f'; no exact English-name match among {len(cands)} fuzzy candidates', 'route': 'fuzzycompletions', 'cand_names': [c['name'] for c in cands[:5]]}
fn = 'raw/lei_match.jsonl'; done = set()
if os.path.exists(fn):
    for line in open(fn, encoding='utf-8'):
        try: done.add(json.loads(line)['key'])
        except Exception: pass
todo = [r for r in rows if r['exchange'] + '|' + r['symbol'] not in done]; print('lei_match todo', len(todo), 'done', len(done), flush=True)
out = open(fn, 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
def run(r):
    try: d = work(r)
    except Exception as e: d = {'key': r['exchange'] + '|' + r['symbol'], 'lei': '', 'gap': 'error ' + repr(e)[:120]}
    with lock:
        out.write(json.dumps(d, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
        if cnt[0] % 250 == 0: print('lei_match', cnt[0], '/', len(todo), flush=True)
with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '3'))) as ex: list(ex.map(run, todo))
allm = [json.loads(l) for l in open(fn, encoding='utf-8')]
from collections import Counter
print('lei_match DONE', 'matched', sum(1 for d in allm if d.get('lei')), 'of', len(allm), Counter(d.get('route') for d in allm if d.get('lei')), flush=True)
