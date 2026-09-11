"""Step 2 — index the ACRA register (27 monthly CSVs from data.gov.sg) down to the rows a listed-issuer sweep can use: every public company limited by
shares, every foreign company branch, and every row whose entity name (current or former) equals an SGX issuer name. Writes raw/acra_pub.jsonl:
UEN, entity name, entity type, company type, status, incorporation date, registered address, primary SSIC, former names, audit firms (names + UENs).
Source URL per row: https://www.bizfile.gov.sg/ (the public BizFile search; per-UEN pages sit behind the search UI — unverified by fetch)."""
import csv, json, os, re, time, glob
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '')
    s = re.sub(r'\bLIMITED\b', 'LTD', s); s = re.sub(r'\bPRIVATE\b', 'PTE', s); s = re.sub(r'\bCORPORATION\b', 'CORP', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
want = set()
mm = json.load(open('raw/sgx_marketmetadata.json', encoding='utf-8'))['rows']
for x in mm:
    if x.get('issuerName'): want.add(name_key(x['issuerName']))
for x in json.load(open('raw/sgx_securities.json', encoding='utf-8'))['rows']:
    if x.get('n'): want.add(name_key(x['n']))
    if x.get('issuer-name'): want.add(name_key(x['issuer-name']))
out = open('raw/acra_pub.jsonl', 'w', encoding='utf-8'); n = kept = 0; t = time.time(); types = {}
for fn in sorted(glob.glob('raw/acra/*.csv')):
    rd = csv.reader(open(fn, encoding='utf-8', errors='replace')); hdr = [h.strip() for h in next(rd)]; ix = {h: i for i, h in enumerate(hdr)}
    for row in rd:
        n += 1
        if len(row) < len(hdr): continue
        et = row[ix['entity_type_description']]; ct = row[ix['company_type_description']]; nm = row[ix['entity_name']]
        formers = [row[ix[f'former_entity_name{k}']] for k in range(1, 16) if ix.get(f'former_entity_name{k}') is not None and row[ix[f'former_entity_name{k}']] not in ('', 'na')]
        keep = ('PUBLIC' in ct.upper()) or (et == 'Foreign Company Branch') or (name_key(nm) in want) or any(name_key(f) in want for f in formers)
        if not keep: continue
        types[ct] = types.get(ct, 0) + 1
        addr = ', '.join(v for v in [row[ix['block']], row[ix['street_name']], (('#' + row[ix['level_no']] + '-' + row[ix['unit_no']]) if row[ix['level_no']] not in ('', 'na') else ''), row[ix['building_name']], ('Singapore ' + row[ix['postal_code']]) if row[ix['postal_code']] not in ('', 'na') else '', row[ix['other_address_line1']], row[ix['other_address_line2']]] if v and v != 'na')
        auditors = [{'name': row[ix[f'name_of_audit_firm{k}']], 'uen': row[ix[f'uen_of_audit_firm{k}']]} for k in range(1, 6) if ix.get(f'name_of_audit_firm{k}') is not None and row[ix[f'name_of_audit_firm{k}']] not in ('', 'na')]
        rec = {'uen': row[ix['uen']], 'name': nm, 'entity_type': et, 'company_type': ct, 'status': row[ix['entity_status_description']], 'incorporated': row[ix['registration_incorporation_date']], 'address': addr, 'address_type': row[ix['address_type']],
               'ssic': row[ix['primary_ssic_code']] + ' ' + row[ix['primary_ssic_description']] if row[ix['primary_ssic_code']] not in ('', 'na') else '', 'former_names': formers, 'auditors': auditors, 'annual_return_date': row[ix['annual_return_date']],
               'src': 'https://www.bizfile.gov.sg/', 'file': os.path.basename(fn)}
        out.write(json.dumps(rec, ensure_ascii=False) + '\n'); kept += 1
    print(os.path.basename(fn), 'scanned', n, 'kept', kept, round(time.time() - t), 's', flush=True)
out.close()
json.dump({'rows_scanned': n, 'rows_kept': kept, 'company_types': types, 'built': time.strftime('%Y-%m-%d')}, open('raw/acra_index_meta.json', 'w'), indent=1)
print('DONE scanned', n, 'kept', kept, types, flush=True)
