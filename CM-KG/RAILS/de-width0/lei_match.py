"""Step 5b — GLEIF legal-name candidates (fuzzycompletions) for roster entities whose ISIN is not in the mapping file.
Same rule as Canada and the United Kingdom: a candidate becomes the LEI only when the GLEIF legal name equals the roster name after case / space /
punctuation normalisation ('GLEIF name-exact'); looser matches stay in Gaps. Writes raw/lei_match.jsonl."""
import requests, json, time, re, os
h = {'Accept': 'application/vnd.api+json'}
hits = json.load(open('raw/isin_lei_hits.json')) if os.path.exists('raw/isin_lei_hits.json') else {}
names = {}
for r in json.load(open('raw/roster.json', encoding='utf-8')):
    if r.get('isin') not in hits: names.setdefault(r['name'], r['exchange'] + '|' + r['symbol'])
def name_key(s):
    s = s.lower().replace('&', ' and ')
    return ' '.join(re.sub(r"[^a-z0-9 ]", ' ', s).split())
out = {}
if os.path.exists('raw/lei_match.jsonl'):
    for line in open('raw/lei_match.jsonl', encoding='utf-8'):
        d = json.loads(line); out[d['name']] = d
f = open('raw/lei_match.jsonl', 'a', encoding='utf-8'); n = 0
print('names to look up', len(names), 'done', len(out), flush=True)
for name, key in names.items():
    if name in out: continue
    cands = []
    for attempt in range(5):
        try:
            x = requests.get('https://api.gleif.org/api/v1/fuzzycompletions', params={'field': 'entity.legalName', 'q': name[:100]}, headers=h, timeout=60)
            if x.status_code == 429: time.sleep(15); continue
            cands = x.json().get('data', []); break
        except Exception:
            time.sleep(5)
    matches = []
    for c in cands:
        v = c['attributes']['value']; lei = (c.get('relationships') or {}).get('lei-records', {}).get('data', {}).get('id')
        if lei and name_key(v) == name_key(name): matches.append((lei, v))
    d = {'key': key, 'name': name, 'cands': [(c['attributes']['value'], (c.get('relationships') or {}).get('lei-records', {}).get('data', {}).get('id')) for c in cands[:10]], 'matches': matches}
    out[name] = d; f.write(json.dumps(d, ensure_ascii=False) + '\n'); f.flush(); n += 1
    if n % 50 == 0: print(n, flush=True)
    time.sleep(1.0)
print('DONE', len(out), 'name-exact', sum(1 for d in out.values() if d['matches']), flush=True)
