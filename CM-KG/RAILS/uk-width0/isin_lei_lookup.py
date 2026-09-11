"""Step 5 — LEI by exact ISIN from the GLEIF ISIN-to-LEI mapping file (daily zip fetched in step 1) for every LSE and Aquis instrument ISIN.
Writes raw/isin_lei_hits.json {ISIN: LEI or LEI|LEI}. GB-, JE-, GG-, IM-, IE- and other prefixed ISINs are all looked up; the label on the sheet is
'GLEIF ISIN-to-LEI mapping file (exact ISIN match)'."""
import zipfile, csv, io, json, os
want = set()
ex = json.load(open('raw/lse_explorer.json'))
for mkt, blk in ex['markets'].items():
    for x in blk['rows']:
        if x.get('isin'): want.add(x['isin'])
if os.path.exists('raw/aquis.json'):
    for r in json.load(open('raw/aquis.json', encoding='utf-8'))['rows']:
        if r.get('isin'): want.add(r['isin'])
print('ISINs to look up', len(want), 'GB-prefixed', sum(1 for s in want if s.startswith('GB')), flush=True)
z = zipfile.ZipFile('raw/isin-lei-latest.zip'); n = z.namelist()[0]
f = io.TextIOWrapper(z.open(n), encoding='utf-8'); rd = csv.reader(f); next(rd)
hits = {}; total = 0; gb = 0
for lei, isin in rd:
    total += 1
    if isin.startswith('GB'): gb += 1
    if isin in want:
        if isin in hits and hits[isin] != lei: hits[isin] = hits[isin] + '|' + lei
        else: hits[isin] = lei
json.dump(hits, open('raw/isin_lei_hits.json', 'w'), indent=0)
json.dump({'mapping_rows': total, 'gb_rows_in_file': gb, 'wanted': len(want), 'hits': len(hits), 'file': open('raw/isin-lei-latest.txt').read().strip()}, open('raw/isin_lei_meta.json', 'w'))
print('mapping rows', total, 'GB rows in file', gb, 'hits', len(hits), 'of', len(want), 'multi-LEI ISINs', sum(1 for v in hits.values() if '|' in v), flush=True)
