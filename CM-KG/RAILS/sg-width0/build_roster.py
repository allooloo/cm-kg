"""Step 3 — one roster row per SGX-listed stock from the raw feeds: the securities list (name, stock code, market MAINBOARD / CATALIST, currency, listing date)
joined to the market metadata by stock code (ISIN, issuer name, FISN, asset class). Stocks only (type 'stocks'); REITs, business trusts, ETFs, ADRs and
bonds are carried as rows with their type so Width 1-F can pick them up, but sit outside corporate scope. Writes raw/roster.json."""
import json, re, os
from collections import Counter
sec = json.load(open('raw/sgx_securities.json', encoding='utf-8'))['rows']
mm = {x['stockCode']: x for x in json.load(open('raw/sgx_marketmetadata.json', encoding='utf-8'))['rows'] if x.get('stockCode')}
scr = {x['stockCode']: x for x in json.load(open('raw/sgx_screener.json', encoding='utf-8'))['rows'] if x.get('stockCode')} if os.path.exists('raw/sgx_screener.json') else {}
SCR_SRC = 'https://investors.sgx.com/stock-screener (feed api.sgx.com/stockscreener/v2.0, identity fields only)'
SRC = 'https://www.sgx.com/securities/stock-screener (feed api.sgx.com/securities/v1.1)'; MM_SRC = 'https://api.sgx.com/marketmetadata/v2 (SGX market metadata)'
FUNDY = re.compile(r'\b(REIT|TRUST|ETF|FUND|BOND|NOTES?|WARRANT|DLC)\b', re.I)
rows = []
for x in sec:
    if x.get('type') not in ('stocks', 'reits', 'adrs'): continue
    code = x.get('nc') or ''; m = mm.get(code, {})
    stype = 'Corporate' if x.get('type') == 'stocks' and not FUNDY.search(x.get('n') or '') else ({'reits': 'REIT / business trust', 'adrs': 'Depositary receipts'}.get(x.get('type'), 'Fund (by name)'))
    d = x.get('ptd') or ''
    corp = stype == 'Corporate'
    # trusts and depositary receipts: the market-metadata issuer name is the manager / depositary (a Pte. Ltd.), not the listed trust — carried as 'manager'
    rows.append(dict(exchange='SGX', symbol=code, name=((m.get('issuerName') if corp else '') or x.get('issuer-name') or x.get('n') or '').strip(), manager=('' if corp else (m.get('issuerName') or '').strip()), name_display=x.get('n') or '', security_type=stype, sgx_type=x.get('type'), market=x.get('m') or '', currency=x.get('cur') or m.get('tradingCurrency') or '',
        listing_date=(f'{d[:4]}-{d[4:6]}-{d[6:]}' if re.fullmatch(r'\d{8}', d) else ''), isin=m.get('isinCode') or '', fisn=m.get('fisn') or '', ibm_code=m.get('ibmCode') or x.get('id'), chinese_name=m.get('chineseName') or '', sip=x.get('sip') or m.get('sip') or '',
        sector=(scr.get(code) or {}).get('sector') or '', screener_name=(scr.get(code) or {}).get('companyName') or '', sector_src=SCR_SRC if (scr.get(code) or {}).get('sector') else '',
        roster_src=SRC, mm_src=MM_SRC if m else '', status='Listed'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['security_type'] for r in rows), Counter(r['market'] for r in rows)); print('with ISIN', sum(1 for r in rows if r['isin']), 'with listing date', sum(1 for r in rows if r['listing_date']), 'with sector', sum(1 for r in rows if r['sector']))
