"""Step 2 — one roster row per share line on Euronext Amsterdam (XAMS) and Euronext Growth Amsterdam (TNLA) from the FIRDS equity files: CFI ES… (shares)
without a termination date. Corporate scope = shares whose full name is not a fund / ETF / certificate. The issuer LEI comes with the FIRDS record.
Writes raw/roster.json."""
import json, re
from collections import Counter
f = json.load(open('raw/firds_equities.json', encoding='utf-8'))
SRC = f['src']; MICS = f['mics']
FUNDY = re.compile(r'\b(FUND|ETF|SICAV|FCP|TRUST|CERTIFICAAT|CERTIFICATE|TRACKER|INDEX|BELEGGINGSFONDS)\b', re.I)
rows = []; seen = set()
for x in f['rows']:
    if not (x.get('cfi') or '').startswith('ES') or x.get('termination'): continue
    k = (x['isin'], x['mic'])
    if k in seen: continue
    seen.add(k)
    name = (x.get('full_name') or '').strip()
    rows.append(dict(exchange=MICS[x['mic']], mic=x['mic'], symbol=x['isin'], name=name, name_short=(x.get('short_name') or '').strip(), security_type='Corporate' if not FUNDY.search(name) else 'Fund / certificate (by name)', cfi=x.get('cfi') or '', isin=x['isin'], lei=x.get('lei') or '',
                     currency=x.get('currency') or '', listing_date=x.get('first_trade') or x.get('admission') or '', admission_date=x.get('admission') or '', roster_src=SRC, firds_file=x.get('file', ''), status='Admitted to trading (FIRDS)'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['exchange'] for r in rows), Counter(r['security_type'] for r in rows)); print('NL ISIN', sum(1 for r in rows if r['isin'].startswith('NL')), 'with LEI', sum(1 for r in rows if r['lei']), 'with listing date', sum(1 for r in rows if r['listing_date']))
