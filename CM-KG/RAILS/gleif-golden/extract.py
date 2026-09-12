"""Extract per-jurisdiction LEI records from the GLEIF golden copy CSV in the pond drop (streamed from the zip, never fully unpacked on disk):
raw/lei-<JUR>.jsonl for JP, KR, US, HK, KY, BM, CN, VG, SG (and any jurisdiction given on the command line). Each record keeps: LEI, legal name
(+ language), other names (name, type, language), legal jurisdiction, entity category, legal form code, entity status, registration status,
registration authority id + entity id (registeredAt / registeredAs), legal address (lines, city, region, country, postal), headquarters address
(city, region, country). Source URL per record = https://api.gleif.org/api/v1/lei-records/<LEI>; read-by label 'GLEIF golden copy <publish date>'.
Also raw/lei-index-<JUR>.json: registeredAs -> [LEI] and normalised-name -> [LEI] for exact local joins (no API rate limit)."""
import csv, io, json, os, re, sys, zipfile
from collections import defaultdict
sys.setrecursionlimit(10000); csv.field_size_limit(10 ** 9)
meta = json.load(open('raw/golden.meta.json')); fn = meta['file']
WANT = set(sys.argv[1:] or ['JP', 'KR', 'US', 'HK', 'KY', 'BM', 'CN', 'VG', 'SG'])
def norm(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper().replace('&', ' AND ')).split())
outs = {j: open(f'raw/lei-{j}.jsonl', 'w', encoding='utf-8') for j in WANT}; idx = {j: {'registeredAs': defaultdict(list), 'name': defaultdict(list)} for j in WANT}; n = 0; kept = 0
z = zipfile.ZipFile(fn); name = [x for x in z.namelist() if x.lower().endswith('.csv')][0]
with z.open(name) as fh:
    rd = csv.reader(io.TextIOWrapper(fh, encoding='utf-8', newline='')); hdr = next(rd); H = {h: i for i, h in enumerate(hdr)}
    def col(row, k): i = H.get(k); return row[i] if i is not None and i < len(row) else ''
    other = [(k, H.get(k + '.xmllang'), H.get(k + '.type')) for k in hdr if re.fullmatch(r'Entity\.OtherEntityNames\.OtherEntityName\.\d+', k)]
    trans = [(k, H.get(k + '.xmllang')) for k in hdr if re.fullmatch(r'Entity\.TransliteratedOtherEntityNames\.TransliteratedOtherEntityName\.\d+', k)]
    jur_i = H['Entity.LegalJurisdiction']; lines_i = [H[k] for k in hdr if re.fullmatch(r'Entity\.LegalAddress\.AdditionalAddressLine\.\d+', k)]
    for row in rd:
        n += 1
        if n % 500000 == 0: print(n, 'rows read,', kept, 'kept', flush=True)
        jur = row[jur_i] if jur_i < len(row) else ''; j2 = jur.split('-')[0]
        if j2 not in WANT: continue
        lei = col(row, 'LEI'); ln = col(row, 'Entity.LegalName')
        rec = {'key': lei, 'lei': lei, 'name': ln, 'name_lang': col(row, 'Entity.LegalName.xmllang'), 'jur': jur, 'category': col(row, 'Entity.EntityCategory'), 'legalForm': col(row, 'Entity.LegalForm.EntityLegalFormCode'), 'status': col(row, 'Entity.EntityStatus'), 'reg_status': col(row, 'Registration.RegistrationStatus'),
               'registeredAt': col(row, 'Entity.RegistrationAuthority.RegistrationAuthorityID'), 'registeredAs': col(row, 'Entity.RegistrationAuthority.RegistrationAuthorityEntityID'),
               'other_names': [{'name': row[H[k]], 'lang': row[li] if li is not None else '', 'type': row[ti] if ti is not None else ''} for k, li, ti in other if H[k] < len(row) and row[H[k]]] + [{'name': row[H[k]], 'lang': row[li] if li is not None else '', 'type': 'TRANSLITERATED'} for k, li in trans if H[k] < len(row) and row[H[k]]],
               'legal_lines': [x for x in [col(row, 'Entity.LegalAddress.FirstAddressLine')] + [row[i] for i in lines_i if i < len(row)] if x], 'legal_city': col(row, 'Entity.LegalAddress.City'), 'legal_region': col(row, 'Entity.LegalAddress.Region'), 'legal_country': col(row, 'Entity.LegalAddress.Country'), 'legal_postal': col(row, 'Entity.LegalAddress.PostalCode'),
               'hq_city': col(row, 'Entity.HeadquartersAddress.City'), 'hq_region': col(row, 'Entity.HeadquartersAddress.Region'), 'hq_country': col(row, 'Entity.HeadquartersAddress.Country'),
               'src': f'https://api.gleif.org/api/v1/lei-records/{lei}', 'read_by': f"GLEIF golden copy {meta['publish_date'][:10]} (LEI-CDF {meta.get('cdf_version')})"}
        outs[j2].write(json.dumps(rec, ensure_ascii=False) + '\n'); kept += 1
        if rec['registeredAs']: idx[j2]['registeredAs'][rec['registeredAs']].append(lei)
        for nm in [ln] + [o['name'] for o in rec['other_names']]:
            k = norm(nm)
            if k: idx[j2]['name'][k].append(lei)
for j in WANT:
    outs[j].close(); json.dump({'registeredAs': idx[j]['registeredAs'], 'name': idx[j]['name']}, open(f'raw/lei-index-{j}.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(j, 'records', sum(1 for _ in open(f'raw/lei-{j}.jsonl', encoding='utf-8')), 'registeredAs keys', len(idx[j]['registeredAs']), 'name keys', len(idx[j]['name']), flush=True)
print('EXTRACT DONE rows', n, 'kept', kept, flush=True)
