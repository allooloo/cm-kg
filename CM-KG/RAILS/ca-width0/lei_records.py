import requests, json, time, os
h = {'Accept': 'application/vnd.api+json'}
leis = []
for fn in ('raw/lei_match.jsonl', 'raw/lei_match2.jsonl'):
    if not os.path.exists(fn): continue
    for line in open(fn, encoding='utf-8'):
        d = json.loads(line)
        for lei, v in d.get('matches', []):
            if lei not in leis: leis.append(lei)
if os.path.exists('raw/isin_lei_hits.json'):
    for v in json.load(open('raw/isin_lei_hits.json')).values():
        for lei in v.split('|'):
            if lei not in leis: leis.append(lei)
have = {}
if os.path.exists('raw/lei_records.jsonl'):
    for line in open('raw/lei_records.jsonl', encoding='utf-8'):
        x = json.loads(line); have[x['key']] = x
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
        rec = {'key': a['lei'], 'name': e['legalName']['name'], 'jur': e.get('jurisdiction'), 'legal_country': e['legalAddress'].get('country'), 'hq_city': e['headquartersAddress'].get('city'), 'hq_region': e['headquartersAddress'].get('region'), 'hq_country': e['headquartersAddress'].get('country'), 'status': e.get('status'), 'reg_status': a['registration'].get('status'), 'legalForm': (e.get('legalForm') or {}).get('id'), 'registeredAs': e.get('registeredAs'), 'registeredAt': (e.get('registeredAt') or {}).get('id')}
        out.write(json.dumps(rec, ensure_ascii=False) + '\n')
    out.flush(); time.sleep(1.2)
print('DONE', flush=True)
