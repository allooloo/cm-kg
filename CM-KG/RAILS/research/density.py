r"""density.py — USR-04 item 6: the density readout, one CSV, numbers only (no page is changed).
Per issuer: market, exchange, cmr, name, size measure and band, houses named, open-research rows, coverage state.
  size band   by market cap where the record has it; no node's record carries a market cap today, so the band is by filings count in the trailing twelve
              months: 0 · 1-9 · 10-49 · 50-199 · 200+   (the size_basis column says which)
Then one line per market (row type "market"): issuers, read, house rate (issuers with one house or more / issuers read), note rate (issuers with one
open-research row or more / issuers read), median houses and median notes among the issuers that have any, and over all issuers read.
Usage: python -X utf8 density.py <out.csv>"""
import sys, os, csv, json, glob, statistics
P = r'C:\ALLOOLOO\CM-KG\RESEARCH\pages'; out = sys.argv[1]
band = lambda n: '0' if n == 0 else '1-9' if n < 10 else '10-49' if n < 50 else '50-199' if n < 200 else '200+'
med = lambda v: (statistics.median(v) if v else '')
rows = []; mk = []
for f in sorted(glob.glob(os.path.join(P, '*.jsonl'))):
    if '.pre-' in f: continue
    cc = os.path.basename(f)[:-6]; H = []; N = []; read = 0; n = 0
    for l in open(f, encoding='utf-8'):
        p = json.loads(l); x = p['numbers']; i = x['identity']; cv = x['coverage']; fil = x['disclosure']['filings']; cap = (i.get('market_cap') or {}).get('value') if isinstance(i.get('market_cap'), dict) else None
        h = len(cv.get('houses', [])); o = len(x['open_research'].get('rows', [])); n += 1
        if cv['state'] != 'not_read': read += 1; H.append(h); N.append(o)
        rows.append(['issuer', cc.upper(), p['cmr'].split('/')[1], p['cmr'], (i['name'].get('value') or ''), fil, cap if cap is not None else '', 'market cap' if cap is not None else 'filings count, trailing twelve months', band(fil), h, o, cv['state'], x['open_research']['state']])
    hp = [v for v in H if v]; npos = [v for v in N if v]
    mk.append(['market', cc.upper(), '', '', '', n, read, round(len(hp) / read, 4) if read else '', round(len(npos) / read, 4) if read else '', med(hp), med(npos), med(H), med(N), sum(H), sum(N)])
with open(out, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh); w.writerow(['row', 'market', 'exchange', 'cmr', 'issuer', 'filings_ttm', 'market_cap', 'size_basis', 'size_band', 'houses_named', 'open_research_rows', 'coverage_state', 'open_research_state']); w.writerows(rows)
    w.writerow([]); w.writerow(['row', 'market', '', '', '', 'issuers', 'issuers_read', 'house_rate', 'note_rate', 'median_houses_where_any', 'median_notes_where_any', 'median_houses_all_read', 'median_notes_all_read', 'houses_total', 'notes_total']); w.writerows(mk)
print('issuers', len(rows), 'markets', len(mk), '->', out)
for m in mk: print(m[1], m[5], m[6], m[7], m[8], m[9], m[10])
