"""Step 2 — one roster row per Xetra-traded share (Instrument Type CS) whose product group is a German group (DAX, MDAX, SDAX, TecDAX, DEUTSCHLAND) or whose
ISIN is German: the Deutsche Börse listed-companies universe as the exchange publishes it by machine. Foreign shares on Xetra (NORDAMERIKA, GROSSBRITANNIEN, …)
are not German issuers and are left out. Segment = the Xetra product group (index membership or 'DEUTSCHLAND'); the Regulated Market / Scale split is not
in the file (HITL: Börse Frankfurt API). Writes raw/roster.json."""
import json, re
from collections import Counter
x = json.load(open('raw/xetra_instruments.json', encoding='utf-8')); SRC = x['src']
GERMAN = {'DAX', 'MDAX', 'SDAX', 'TECDAX', 'DEUTSCHLAND'}
FUNDY = re.compile(r'\b(FUND|ETF|SICAV|TRUST|CERT|INDEX|ZERTIFIKAT)\b', re.I)
rows = []; seen = set()
for r in x['rows']:
    if r.get('Instrument Type') != 'CS' or r.get('Instrument Status') not in ('Active', ''): continue
    grp = (r.get('Product Assignment Group Description') or '').upper(); isin = r.get('ISIN', '')
    if grp not in GERMAN and not isin.startswith('DE'): continue
    if isin in seen: continue
    seen.add(isin)
    rows.append(dict(exchange='Xetra', symbol=r.get('Mnemonic') or '', wkn=r.get('WKN') or '', name=(r.get('Instrument') or '').strip(), security_type='Corporate' if not FUNDY.search(r.get('Instrument') or '') else 'Fund / certificate (by name)', isin=isin,
                     segment=r.get('Product Assignment Group Description') or '', product_group=r.get('Product Assignment Group') or '', designated_sponsor=(r.get('Designated Sponsor') or '').strip('#'), currency=r.get('Trading Currency') or r.get('Currency') or '', roster_src=SRC, file_date=x.get('file_date', ''), status='Active'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['segment'] for r in rows).most_common(8), Counter(r['security_type'] for r in rows)); print('DE ISIN', sum(1 for r in rows if r['isin'].startswith('DE')), 'non-DE ISIN in German groups', sum(1 for r in rows if not r['isin'].startswith('DE')))
