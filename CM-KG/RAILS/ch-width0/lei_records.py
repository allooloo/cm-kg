"""Step 6 — GLEIF LEI records for every LEI found (ISIN mapping hits + name-exact matches), 100 per call:
  GET https://api.gleif.org/api/v1/lei-records?filter[lei]=A,B,C
Kept: legal name, other entity names, legal jurisdiction, legal address (city/region/country), headquarters address, entity status,
registration status, legal form, registeredAs (the UEN when registeredAt is RA000254 = Zefix), registeredAt.
Writes raw/lei_records.jsonl keyed by LEI."""
import requests, json, time, os
h = {'Accept': 'application/vnd.api+json'}
leis = []
if os.path.exists('raw/isin_lei_hits.json'):
    for v in json.load(open('raw/isin_lei_hits.json')).values():
        for lei in v.split('|'):
            if lei not in leis: leis.append(lei)
for fn in ('raw/lei_match.jsonl',):
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            d = json.loads(line)
            for lei, v in d.get('matches', []):
                if lei not in leis: leis.append(lei)
have = set()
if os.path.exists('raw/lei_records.jsonl'):
    for line in open('raw/lei_records.jsonl', encoding='utf-8'):
        try: have.add(json.loads(line)['key'])
        except Exception: pass
todo = [l for l in leis if l not in have]
print('leis', len(leis), 'todo', len(todo), flush=True)
out = open('raw/lei_records.jsonl', 'a', encoding='utf-8')
for i in range(0, len(todo), 100):
    batch = todo[i:i + 100]
    for attempt in range(6):
        try:
            r = requests.get('https://api.gleif.org/api/v1/lei-records', params={'filter[lei]': ','.join(batch), 'page[size]': 200}, headers=h, timeout=120)
            if r.status_code == 429: time.sleep(15); continue
            r.raise_for_status(); break
        except Exception as e:
            print('retry', e, flush=True); time.sleep(5)
    for d in r.json().get('data', []):
        a = d['attributes']; e = a['entity']
        rec = {'key': a['lei'], 'name': e['legalName']['name'], 'other_names': [x.get('name') for x in (e.get('otherNames') or [])], 'jur': e.get('jurisdiction'),
               'legal_city': e['legalAddress'].get('city'), 'legal_region': e['legalAddress'].get('region'), 'legal_country': e['legalAddress'].get('country'),
               'legal_lines': e['legalAddress'].get('addressLines'), 'legal_postal': e['legalAddress'].get('postalCode'),
               'hq_city': e['headquartersAddress'].get('city'), 'hq_region': e['headquartersAddress'].get('region'), 'hq_country': e['headquartersAddress'].get('country'),
               'status': e.get('status'), 'reg_status': a['registration'].get('status'), 'legalForm': (e.get('legalForm') or {}).get('id'),
               'registeredAs': e.get('registeredAs'), 'registeredAt': (e.get('registeredAt') or {}).get('id'), 'src': 'https://api.gleif.org/api/v1/lei-records/' + a['lei']}
        out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    out.flush(); time.sleep(1.2)
    if (i // 100) % 5 == 0: print(i + len(batch), '/', len(todo), flush=True)
print('DONE', flush=True)
