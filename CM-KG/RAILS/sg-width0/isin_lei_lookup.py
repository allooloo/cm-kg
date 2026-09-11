"""Step 5 — LEI by exact ISIN from the GLEIF ISIN-to-LEI mapping file (daily zip) for every SGX ISIN on the roster.
Writes raw/isin_lei_hits.json {ISIN: LEI or LEI|LEI}. Label on the sheet: 'GLEIF ISIN-to-LEI mapping file (exact ISIN match)'."""
import zipfile, csv, io, json, os
want = set()
for r in json.load(open('raw/roster.json', encoding='utf-8')):
    if r.get('isin'): want.add(r['isin'])
print('ISINs to look up', len(want), 'SG-prefixed', sum(1 for s in want if s.startswith('SG')), flush=True)
z = zipfile.ZipFile('raw/isin-lei-latest.zip'); n = z.namelist()[0]
f = io.TextIOWrapper(z.open(n), encoding='utf-8'); rd = csv.reader(f); next(rd)
hits = {}; total = 0; au = 0
for lei, isin in rd:
    total += 1
    if isin.startswith('SG'): au += 1
    if isin in want:
        if isin in hits and hits[isin] != lei: hits[isin] = hits[isin] + '|' + lei
        else: hits[isin] = lei
json.dump(hits, open('raw/isin_lei_hits.json', 'w'), indent=0)
json.dump({'mapping_rows': total, 'sg_rows_in_file': au, 'wanted': len(want), 'hits': len(hits), 'file': open('raw/isin-lei-latest.txt').read().strip()}, open('raw/isin_lei_meta.json', 'w'))
print('mapping rows', total, 'SG rows in file', au, 'hits', len(hits), 'of', len(want), 'multi-LEI ISINs', sum(1 for v in hits.values() if '|' in v), flush=True)
