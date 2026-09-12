"""Step 4 — GLEIF LEI records for every matched LEI, 100 per call, plus the ISINs GLEIF maps to each LEI (GET /api/v1/lei-records/<lei>/isins — the only
keyless ISIN source for United States issuers; EDGAR carries none). Kept: legal name, other names, jurisdiction, legal and headquarters addresses,
entity status, registration status, legal form, registeredAs / registeredAt, ISIN list. Writes raw/lei_records.jsonl keyed by LEI. Resumable."""
import requests, json, time, os, threading
from concurrent.futures import ThreadPoolExecutor
h = {'Accept': 'application/vnd.api+json'}
leis = []
for line in open('raw/lei_match.jsonl', encoding='utf-8'):
    d = json.loads(line)
    if d.get('lei') and d['lei'] not in leis: leis.append(d['lei'])
have = set()
if os.path.exists('raw/lei_records.jsonl'):
    for line in open('raw/lei_records.jsonl', encoding='utf-8'):
        try: have.add(json.loads(line)['key'])
        except Exception: pass
todo = [l for l in leis if l not in have]; print('leis', len(leis), 'todo', len(todo), flush=True)
_gate = threading.Lock(); _last = [0.0]
def get(url, params=None, tries=6):
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
def isins_of(lei):
    r = get(f'https://api.gleif.org/api/v1/lei-records/{lei}/isins')
    if r is None or r.status_code != 200: return None
    return sorted({d['attributes']['isin'] for d in (r.json().get('data') or []) if d.get('attributes', {}).get('isin')})
out = open('raw/lei_records.jsonl', 'a', encoding='utf-8'); lock = threading.Lock()
def batch(bl):
    r = get('https://api.gleif.org/api/v1/lei-records', params={'filter[lei]': ','.join(bl), 'page[size]': 100})
    if r is None or r.status_code != 200: print('batch failed', r.status_code if r is not None else None, flush=True); return
    for x in r.json().get('data', []):
        e = x['attributes']['entity']; ra = x['attributes'].get('registration') or {}; la = e.get('legalAddress') or {}; ha = e.get('headquartersAddress') or {}
        rec = {'key': x['id'], 'lei': x['id'], 'name': e['legalName']['name'], 'other_names': [n.get('name') for n in (e.get('otherNames') or [])], 'jur': e.get('jurisdiction') or '', 'status': e.get('status'), 'reg_status': ra.get('status'), 'legalForm': (e.get('legalForm') or {}).get('id') or '',
               'registeredAs': e.get('registeredAs') or '', 'registeredAt': (e.get('registeredAt') or {}).get('id') or '', 'legal_lines': la.get('addressLines') or [], 'legal_city': la.get('city') or '', 'legal_region': la.get('region') or '', 'legal_postal': la.get('postalCode') or '', 'legal_country': la.get('country') or '',
               'hq_city': ha.get('city') or '', 'hq_region': ha.get('region') or '', 'hq_country': ha.get('country') or '', 'src': f"https://api.gleif.org/api/v1/lei-records/{x['id']}", 'isins': isins_of(x['id']), 'isins_src': f"https://api.gleif.org/api/v1/lei-records/{x['id']}/isins"}
        with lock: out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush()
chunks = [todo[i:i + 100] for i in range(0, len(todo), 100)]
with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '3'))) as ex: list(ex.map(batch, chunks))
n = sum(1 for _ in open('raw/lei_records.jsonl', encoding='utf-8')); print('lei_records DONE', n, flush=True)
