"""CSE exchange bulletins: one fetch of the exchange's bulletins feed, filtered to the corporate issuers and the window.
   https://website-data-api-v2.thecse.com/api/bulletins?locale=en   (every bulletin since 2003; symbol(s), title, date, slug)
   bulletin page: https://thecse.com/bulletin/<slug>/
Read-by: 'thecse.com bulletins API'."""
import json, re
from common import *
def main():
    x = get('https://website-data-api-v2.thecse.com/api/bulletins?locale=en', timeout=180, headers={'Accept': 'application/json', 'Origin': 'https://thecse.com', 'Referer': 'https://thecse.com/'})
    if x is None or x.status_code != 200: print('feed http', x.status_code if x else None); return
    d = x.json(); rows = d.get('list', d if isinstance(d, list) else [])
    open('raw/cse_bulletins_feed.json', 'w', encoding='utf-8').write(json.dumps(d))
    iss = [r for r in load_issuers() if r['exchange'] == 'CSE']
    by_sym = {}
    for r in iss:
        by_sym.setdefault(r['ticker'], r); by_sym.setdefault(r['root'], r)
    out = open('raw/cse_bulletins.jsonl', 'w', encoding='utf-8'); n = 0; per = {}
    for b in rows:
        date = to_iso(b.get('date') or '')
        if not in_window(date): continue
        syms = b.get('symbols') or ([b['symbol']] if b.get('symbol') else [])
        hit = None
        for s in syms:
            hit = by_sym.get(s) or by_sym.get(str(s).split('.')[0])
            if hit: break
        if not hit: continue
        title = b.get('title') or ''; kind = re.sub(r'^\d{4}-\d{4}\s*-\s*', '', title).split(' - ')[0]
        et = 'halt_resume' if re.search(r'halt|resum|cease trade', kind, re.I) else ('corporate_action' if re.search(r'consolidat|dividend|distribution|split|name|symbol|delist|new listing|graduat|rights|warrant|record date|cusip|reinstat|transfer|reverse', kind, re.I) else 'exchange_bulletin')
        e = event(hit, et, date, title, 'CSE bulletin', f"https://thecse.com/bulletin/{b.get('slug')}/", 'thecse.com bulletins API', detail=kind)
        e['key'] = key(hit); out.write(json.dumps(e, ensure_ascii=False) + '\n'); n += 1; per[e['key']] = per.get(e['key'], 0) + 1
    print('cse bulletins in window for corporates:', n, 'issuers with bulletins:', len(per), 'of', len(iss), flush=True)
    print('cse_bulletins DONE', flush=True)
if __name__ == '__main__': main()
