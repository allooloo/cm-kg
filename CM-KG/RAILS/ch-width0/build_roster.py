"""Step 2 — one roster row per share line: every SIX Swiss Exchange equity line (SecTypeCode SS registered / RS bearer? / BS / PC participation certificate)
plus BX Swiss share lines with a Swiss ISIN that SIX does not carry (BX-listed). Corporate scope = SS/RS/BS share lines whose name is not a fund / ETF / certificate;
PC lines are carried as 'Participation certificate'. Writes raw/roster.json."""
import json, re
from collections import Counter
six = json.load(open('raw/six_eq.json', encoding='utf-8'))
SRC = six['src']; rows = []; seen_isin = set()
FUNDY = re.compile(r'\b(FUND|ETF|SICAV|TRUST|CERTIFICATE|CERT|INDEX|TRACKER)\b', re.I)
TYPE = {'SS': 'Registered share', 'RS': 'Registered share', 'BS': 'Bearer share', 'PC': 'Participation certificate'}
for x in six['rows']:
    isin = str(x.get('ISIN') or ''); d = str(x.get('FirstTradingDate') or '')
    stype = 'Corporate' if x.get('SecTypeCode') in ('SS', 'RS', 'BS') and not FUNDY.search(x.get('ShortName') or '') else (TYPE.get(x.get('SecTypeCode'), x.get('SecTypeCode')) if x.get('SecTypeCode') == 'PC' else 'Fund / certificate (by name)')
    rows.append(dict(exchange='SIX', symbol=x.get('ValorSymbol') or '', valor=str(x.get('ValorNumber') or ''), name=(x.get('ShortName') or '').strip(), security_type=stype, share_type=TYPE.get(x.get('SecTypeCode'), x.get('SecTypeCode') or ''), isin=isin,
                     currency=x.get('TradingBaseCurrency') or x.get('Currency') or '', listing_date=(f'{d[:4]}-{d[4:6]}-{d[6:]}' if re.fullmatch(r'\d{8}', d) else ''), sector=x.get('ICBIndustry') or '', number_in_issue=x.get('NumberInIssue') or '', roster_src=SRC, status='Listed'))
    seen_isin.add(isin)
bx = json.load(open('raw/bx_instruments.json', encoding='utf-8'))
n_bx = 0
for x in bx['rows']:
    if not x['isin'].startswith('CH') or x['isin'] in seen_isin: continue
    if not re.search(r'(?i)share|aktie|action', x.get('label') or ''): continue
    seen_isin.add(x['isin']); n_bx += 1
    rows.append(dict(exchange='BX Swiss', symbol=x.get('code') or '', valor='', name=x.get('name') or '', security_type='Corporate' if not FUNDY.search(x.get('name') or '') else 'Fund / certificate (by name)', share_type=x.get('label') or '', isin=x['isin'], currency='', listing_date='', sector='', number_in_issue='', roster_src=bx['src'], bx_url=x.get('url', ''), status='Listed'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), 'BX added', n_bx, Counter(r['exchange'] for r in rows), Counter(r['security_type'] for r in rows)); print('CH ISIN', sum(1 for r in rows if r['isin'].startswith('CH')), 'with sector', sum(1 for r in rows if r['sector']), 'with listing date', sum(1 for r in rows if r['listing_date']))
