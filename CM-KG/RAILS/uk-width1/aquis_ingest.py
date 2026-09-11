"""Ingest Aquis announcements read in a browser session (the exchange page's own Next.js data) into raw/aquis_announcements.json.
Usage: python aquis_ingest.py <file with the browser tool result (JSON array of {type,text} or raw text)>
Each row: [announcement id, symbol, ISIN, issuer name, headline, date]. Announcement URL = https://www.aquis.eu/stock-exchange/announcements/<id>."""
import json, os, re, sys
fn = sys.argv[1]
raw = open(fn, encoding='utf-8').read()
try:
    arr = json.loads(raw); txt = '\n'.join(x.get('text', '') for x in arr if isinstance(x, dict))
except Exception:
    txt = raw
m = re.search(r'\{\s*"build"', txt)
if not m: raise SystemExit('no browser result object found in ' + fn)
i = m.start(); dec = json.JSONDecoder(); d, _ = dec.raw_decode(txt[i:])
acc = {'rows': [], 'meta': {}, 'source': 'https://www.aquis.eu/stock-exchange/announcements (Next.js page data /_next/data/<build>/stock-exchange/announcements.json?year=&month=&page=, read in a browser session)'}
if os.path.exists('raw/aquis_announcements.json'): acc = json.load(open('raw/aquis_announcements.json', encoding='utf-8'))
have = set(r[0] for r in acc['rows'])
new = [r for r in d['rows'] if r[0] not in have]; acc['rows'] += new; acc['meta'].update(d.get('meta', {})); acc['build'] = d.get('build')
json.dump(acc, open('raw/aquis_announcements.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('added', len(new), 'total', len(acc['rows']), d.get('meta'))
