"""Step 4 (local, shared by the jp / kr / us / hk rails) — GLEIF records for every matched LEI from the golden copy extract plus the ISIN list per LEI
from the GLEIF ISIN-to-LEI mapping zip (inverted locally): no API call, no rate limit. Run from a rail folder: python ..\\gleif-golden\\lei_records_local.py <JUR>
Reads raw/lei_match.jsonl (field lei), the extract POND\\estate\\gleif-golden\\<date>\\lei-<JUR>.jsonl (and lei-<other>.jsonl for LEIs registered
elsewhere), and the mapping zip from any pond drop that holds isin-lei-latest.zip (hk-width0 today). Writes raw/lei_records.jsonl keyed by LEI in
the same shape as the API route (src = the GLEIF record URL, read-by = the golden copy label, isins + isins_src)."""
import json, os, sys, glob, zipfile, csv, io
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS'); import pond
JUR = sys.argv[1] if len(sys.argv) > 1 else 'JP'
leis = []
for line in open('raw/lei_match.jsonl', encoding='utf-8'):
    d = json.loads(line)
    if d.get('lei') and d['lei'] not in leis: leis.append(d['lei'])
want = set(leis); print('LEIs', len(want), flush=True)
recs = {}
files = sorted(glob.glob(os.path.join(os.path.dirname(pond.latest('estate', 'gleif-golden', f'lei-{JUR}.jsonl')), 'lei-*.jsonl')))
files.sort(key=lambda f: 0 if f.endswith(f'lei-{JUR}.jsonl') else 1)
for f in files:
    for line in open(f, encoding='utf-8'):
        d = json.loads(line)
        if d['lei'] in want and d['lei'] not in recs: recs[d['lei']] = d
    if len(recs) == len(want): break
print('records from the golden copy', len(recs), 'missing', len(want) - len(recs), flush=True)
zp = None
for node in ('hk-cm-kg', 'ch-cm-kg', 'de-cm-kg', 'nl-cm-kg', 'fr-cm-kg', 'sg-cm-kg', 'au-cm-kg'):
    zp = pond.latest(node, 'width0', 'isin-lei-latest.zip')
    if zp: break
isins = {l: [] for l in want}
if zp:
    z = zipfile.ZipFile(zp); n = z.namelist()[0]
    rd = csv.reader(io.TextIOWrapper(z.open(n), encoding='utf-8', newline='')); hdr = next(rd); li = hdr.index('LEI'); ii = hdr.index('ISIN'); k = 0
    for row in rd:
        if row[li] in isins: isins[row[li]].append(row[ii]); k += 1
    print('ISINs mapped', k, 'from', os.path.basename(zp), 'LEIs with ISINs', sum(1 for v in isins.values() if v), flush=True)
else: print('no ISIN mapping zip in any pond drop; isins left None', flush=True)
with open('raw/lei_records.jsonl', 'w', encoding='utf-8') as out:
    for l in leis:
        r = recs.get(l)
        if not r: continue
        rec = {'key': l, 'lei': l, 'name': r['name'], 'name_lang': r.get('name_lang', ''), 'other_names': [o['name'] for o in r.get('other_names', [])], 'other_names_full': r.get('other_names', []), 'jur': r['jur'], 'status': r['status'], 'reg_status': r['reg_status'], 'legalForm': r.get('legalForm', ''), 'registeredAs': r.get('registeredAs', ''), 'registeredAt': r.get('registeredAt', ''),
               'legal_lines': r.get('legal_lines', []), 'legal_city': r.get('legal_city', ''), 'legal_region': r.get('legal_region', ''), 'legal_postal': r.get('legal_postal', ''), 'legal_country': r.get('legal_country', ''), 'hq_city': r.get('hq_city', ''), 'hq_region': r.get('hq_region', ''), 'hq_country': r.get('hq_country', ''),
               'src': r['src'], 'read_by': r.get('read_by', ''), 'isins': sorted(set(isins.get(l) or [])) if zp else None, 'isins_src': f'https://mapping.gleif.org/api/v2/isin-lei/latest ({os.path.basename(zp)}, ISINs mapped to the LEI)' if zp else ''}
        out.write(json.dumps(rec, ensure_ascii=False) + '\n')
print('lei_records (local) DONE', sum(1 for _ in open('raw/lei_records.jsonl', encoding='utf-8')), flush=True)
