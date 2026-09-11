"""Step 2 — index the ASIC company register (data.gov.au Company Dataset, weekly, tab-delimited, ~3 M rows) down to public companies (Type APUB)
and to any row whose name equals an exchange-list name. Rows are grouped by ACN: the current name row (Current Name Indicator Y) plus previous
names. Writes raw/asic_pub.jsonl: ACN, ABN, current name, type, class, sub-class, status, registration date, state of registration, previous names.
Source URL per row: https://connectonline.asic.gov.au/RegistrySearch/faces/landing/panelSearch.jspx?searchText=<ACN> (the public ASIC Connect search; unverified by fetch)."""
import zipfile, io, csv, json, re, time, os
from collections import defaultdict
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '')
    s = re.sub(r'\bLIMITED\b', 'LTD', s); s = re.sub(r'\bPROPRIETARY\b', 'PTY', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
want = set()
for x in json.load(open('raw/asx_directory.json', encoding='utf-8')): want.add(name_key(x['Company name']))
if os.path.exists('raw/nsx_list.json'):
    for x in json.load(open('raw/nsx_list.json', encoding='utf-8')): want.add(name_key(re.sub(r'^\[\w+\]\s*', '', x['title'])))
z = zipfile.ZipFile('raw/asic_company.zip'); name = z.namelist()[0]
f = io.TextIOWrapper(z.open(name), encoding='utf-8', errors='replace'); rd = csv.reader(f, delimiter='\t')
hdr = [h.strip().lstrip('﻿') for h in next(rd)]; ix = {h: i for i, h in enumerate(hdr)}
by = defaultdict(lambda: {'previous_names': []}); n = 0; t = time.time()
for row in rd:
    n += 1
    if len(row) < len(hdr): continue
    typ = row[ix['Type']]; nm = row[ix['Company Name']]
    if typ != 'APUB' and name_key(nm) not in want: continue
    acn = row[ix['ACN']]; rec = by[acn]
    cur = row[ix['Current Name Indicator']] == 'Y' or not row[ix['Current Name']]
    if cur or 'name' not in rec:
        rec.update({'acn': acn, 'abn': row[ix['ABN']], 'name': nm if cur else row[ix['Current Name']], 'type': typ, 'class': row[ix['Class']], 'sub_class': row[ix['Sub Class']], 'status': row[ix['Status']], 'registered': row[ix['Date of Registration']], 'deregistered': row[ix['Date of Deregistration']],
                    'state': row[ix['Previous State of Registration']] or '', 'state_reg_no': row[ix['State Registration number']]})
    if not cur: rec['previous_names'].append({'name': nm, 'until': row[ix['Current Name Start Date']]})
    if n % 500000 == 0: print(n, 'scanned', len(by), 'kept', round(time.time() - t), 's', flush=True)
out = open('raw/asic_pub.jsonl', 'w', encoding='utf-8')
for acn, rec in by.items():
    if 'name' in rec: rec['src'] = f'https://connectonline.asic.gov.au/RegistrySearch/faces/landing/panelSearch.jspx?searchText={acn}'; out.write(json.dumps(rec, ensure_ascii=False) + '\n')
json.dump({'file': name, 'rows_scanned': n, 'companies_kept': len(by), 'built': time.strftime('%Y-%m-%d')}, open('raw/asic_index_meta.json', 'w'))
print('DONE scanned', n, 'kept', len(by), flush=True)
