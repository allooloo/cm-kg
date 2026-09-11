"""GLEIF legal-name candidate lookup, one /fuzzycompletions call per roster row (GLEIF allows ~60 requests/minute).
Writes raw/lei_match.jsonl (or raw/lei_match2.jsonl with --reverse, so two copies can run from both ends of the roster).
Which candidate, if any, becomes the LEI cell is decided in assemble.py (name-exact only; looser matches go to Gaps)."""
import requests, json, time, re, sys, os
h = {'Accept': 'application/vnd.api+json'}
rows = json.load(open('raw/roster.json'))
REV = '--reverse' in sys.argv
OUT = 'raw/lei_match2.jsonl' if REV else 'raw/lei_match.jsonl'
LEGAL = {'incorporated': 'inc', 'inc': 'inc', 'corporation': 'corp', 'corp': 'corp', 'limited': 'ltd', 'ltd': 'ltd', 'company': 'co', 'co': 'co', 'ltee': 'ltee', 'ltée': 'ltee', 'plc': 'plc', 'trust': 'trust', 'fund': 'fund', 'lp': 'lp', 'llc': 'llc'}
def norm(s):
    s = s.lower().replace('&', ' and ').replace('ée', 'ee').replace('é', 'e')
    s = re.sub(r"[^a-z0-9 ]", ' ', s); toks = [LEGAL.get(t, t) for t in s.split()]
    if toks and toks[0] == 'the': toks = toks[1:]
    return ' '.join(toks)
out = {}
for fn in ('raw/lei_match.jsonl', 'raw/lei_match2.jsonl'):
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            d = json.loads(line); out[d['key']] = d
f = open(OUT, 'a', encoding='utf-8'); n = 0
for r in (reversed(rows) if REV else rows):
    key = r['exchange'] + '|' + r['symbol']
    if key in out: continue
    name = r['name']; cands = []
    for attempt in range(5):
        try:
            x = requests.get('https://api.gleif.org/api/v1/fuzzycompletions', params={'field': 'entity.legalName', 'q': name[:100]}, headers=h, timeout=60)
            if x.status_code == 429: time.sleep(15); continue
            cands = x.json().get('data', []); break
        except Exception:
            time.sleep(5)
    nn = norm(name); matches = []
    for c in cands:
        v = c['attributes']['value']; lei = (c.get('relationships') or {}).get('lei-records', {}).get('data', {}).get('id')
        if lei and norm(v) == nn: matches.append((lei, v))
    d = {'key': key, 'name': name, 'cands': [(c['attributes']['value'], (c.get('relationships') or {}).get('lei-records', {}).get('data', {}).get('id')) for c in cands[:10]], 'matches': matches}
    out[key] = d; f.write(json.dumps(d, ensure_ascii=False) + '\n'); f.flush(); n += 1
    if n % 100 == 0: print(n, len(out), flush=True)
    time.sleep(0.25)
print('DONE', len(out), flush=True)
