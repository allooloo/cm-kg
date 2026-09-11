"""Step 2 — index the Companies House free bulk product (BasicCompanyDataAsOneFile) down to the rows a listed-issuer sweep can use.
Keeps every company whose category is a public company (PLC, incl. Scottish / Northern Irish PLCs and overseas-registered public companies)
or whose name ends in PLC / P.L.C. / PUBLIC LIMITED COMPANY, any status. Writes raw/ch_plc.jsonl: number, name, status, category, country of origin,
registered office (lines, town, county, country, postcode), incorporation date, SIC codes (up to four), accounts category, previous names.
Source URL per row: https://find-and-update.company-information.service.gov.uk/company/<number> (the public profile the bulk row describes).
"""
import zipfile, io, csv, json, os, re, time
fn = next(f for f in os.listdir('raw') if f.startswith('BasicCompanyDataAsOneFile'))
z = zipfile.ZipFile('raw/' + fn); name = z.namelist()[0]
f = io.TextIOWrapper(z.open(name), encoding='utf-8', errors='replace'); rd = csv.reader(f)
hdr = [h.strip() for h in next(rd)]; ix = {h: i for i, h in enumerate(hdr)}
PLC_NAME = re.compile(r'\b(?:PLC|P\.L\.C\.?|PUBLIC LIMITED COMPANY|CCC|CWMNI CYFYNGEDIG CYHOEDDUS)\s*$', re.I)
out = open('raw/ch_plc.jsonl', 'w', encoding='utf-8'); n = kept = 0; t = time.time(); cats = {}
for row in rd:
    n += 1
    if len(row) < len(hdr): continue
    cat = row[ix['CompanyCategory']]
    if not ('Public' in cat or 'PLC' in cat.upper() or PLC_NAME.search(row[ix['CompanyName']])): continue
    cats[cat] = cats.get(cat, 0) + 1
    prev = []
    for k in range(1, 11):
        pn = ix.get(f'PreviousName_{k}.CompanyName'); pd = ix.get(f'PreviousName_{k}.CONDATE')
        if pn is not None and row[pn]: prev.append({'name': row[pn], 'until': row[pd] if pd is not None else ''})
    rec = {'number': row[ix['CompanyNumber']], 'name': row[ix['CompanyName']], 'status': row[ix['CompanyStatus']], 'category': cat, 'origin': row[ix['CountryOfOrigin']],
           'office': {'care_of': row[ix['RegAddress.CareOf']], 'line1': row[ix['RegAddress.AddressLine1']], 'line2': row[ix['RegAddress.AddressLine2']], 'town': row[ix['RegAddress.PostTown']], 'county': row[ix['RegAddress.County']], 'country': row[ix['RegAddress.Country']], 'postcode': row[ix['RegAddress.PostCode']]},
           'incorporated': row[ix['IncorporationDate']], 'dissolved': row[ix['DissolutionDate']], 'sic': [row[ix[f'SICCode.SicText_{k}']] for k in range(1, 5) if row[ix[f'SICCode.SicText_{k}']]],
           'accounts_category': row[ix['Accounts.AccountCategory']], 'accounts_last': row[ix['Accounts.LastMadeUpDate']], 'previous_names': prev}
    out.write(json.dumps(rec, ensure_ascii=False) + '\n'); kept += 1
    if n % 500000 == 0: print(n, 'scanned', kept, 'kept', round(time.time() - t), 's', flush=True)
out.close()
json.dump({'file': fn, 'rows_scanned': n, 'rows_kept': kept, 'categories': cats, 'built': time.strftime('%Y-%m-%d')}, open('raw/ch_index_meta.json', 'w'), indent=1)
print('DONE scanned', n, 'kept', kept, cats, flush=True)
