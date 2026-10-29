r"""DOORS-04 ruling (CEO 2026-10-26): the manager-published CUSIPs are accepted for the 13 held Canadian ETF records. Adds them to ca-reads.json with the
manager document as source and the ruling in read_by. .pre copy kept. Usage: python -X utf8 -I add_manager_reads.py"""
import json, os, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'ca-reads.json')
shutil.copy2(P, P + '.pre-ruling-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
R = json.load(open(P, encoding='utf-8')); RB = 'manager-published CUSIP as printed on the manager document (accepted as source by CEO ruling 2026-10-26; no filed register document prints it) · ISIN = CA + CUSIP + check digit (ISO 6166)'
M = {'ETSX': ('30052P108', 'https://evolveetfs.com/product/etsx/', 'Evolve product page, Fund Details'),
     'ESPX': ('30052U206', 'https://evolveetfs.com/product/espx/', 'Evolve product page, Fund Details (Hedged ETF units)'),
     'HISA': ('42970H100', 'https://evolveetfs.com/product/hisa/', 'Evolve product page, visible Fund Details (also Evolve fact sheet 2020-03-17); an older hidden block shows 42969L104'),
     'HISA.L': ('42970H209', 'https://evolveetfs.com/product/hisa-l/', 'Evolve product page, Fund Details'),
     'USCL': ('379940109', 'https://assets.globalx.ca/product_sheet%2Fen%2Fuscl.pdf', 'Global X product sheet, as at 2026-10-23'),
     'BNKL': ('37962T104', 'https://assets.globalx.ca/product_sheet%2Fen%2Fbnkl.pdf', 'Global X product sheet, as at 2026-10-22'),
     'GRCC': ('379942105', 'https://assets.globalx.ca/product_sheet%2Fen%2Fgrcc.pdf', 'Global X product sheet, as at 2026-10-23'),
     'RNCL': ('37965X102', 'https://assets.globalx.ca/product_sheet%2Fen%2Frncl.pdf', 'Global X product sheet, as at 2026-10-23'),
     'RSCL': ('379954100', 'https://assets.globalx.ca/product_sheet%2Fen%2Frscl.pdf', 'Global X product sheet, as at 2026-10-22'),
     'REIT': ('379952104', 'https://assets.globalx.ca/product_sheet%2Fen%2Freit.pdf', 'Global X product sheet, as at 2026-10-23'),
     'HCRE': ('37963L100', 'https://assets.globalx.ca/product_sheet%2Fen%2Fhcre.pdf', 'Global X product sheet, as at 2026-10-22'),
     'HBNK': ('379946106', 'https://assets.globalx.ca/product_sheet%2Fen%2Fhbnk.pdf', 'Global X product sheet, as at 2026-10-23'),
     'HEB': ('40704N104', 'https://hamiltonetfs.com/etf/heb', 'Hamilton ETFs product page, Fund Details')}
for t, (c, url, d) in M.items(): R[t] = {'cusip': c, 'document': url, 'date': d, 'read_by': RB, 'read_at': '2026-10-26T16:00:00Z'}
json.dump(R, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('reads', len(R))
