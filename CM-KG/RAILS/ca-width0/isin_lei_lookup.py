import zipfile, csv, io, json
want = set()
for line in open('raw/enr_isin.jsonl', encoding='utf-8'):
    d = json.loads(line)
    if d.get('isin'): want.add(d['isin'])
print('ISINs to look up', len(want), 'CA-prefixed', sum(1 for s in want if s.startswith('CA')), flush=True)
z = zipfile.ZipFile('raw/isin-lei-latest.zip'); n = z.namelist()[0]
f = io.TextIOWrapper(z.open(n), encoding='utf-8'); rd = csv.reader(f); next(rd)
hits = {}
for lei, isin in rd:
    if isin in want:
        if isin in hits and hits[isin] != lei: hits[isin] = hits[isin] + '|' + lei
        else: hits[isin] = lei
json.dump(hits, open('raw/isin_lei_hits.json', 'w'), indent=0)
print('hits', len(hits), 'multi-LEI ISINs', sum(1 for v in hits.values() if '|' in v), flush=True)
