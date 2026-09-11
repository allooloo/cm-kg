import json, openpyxl, re
from collections import Counter, defaultdict
def root(s): return s.split('.')[0]
rows=[]
# ---- TMX xlsx (July 2026) lookup by root ticker
wb=openpyxl.load_workbook('raw/tmx_571.xlsx',read_only=True)
xl={}; months=[]
for ex in ('TSX','TSXV'):
    sheet=next(s for s in wb.sheetnames if s.upper().startswith(ex+' ISSUERS')); months.append(sheet)
    ws=wb[sheet]; rr=list(ws.iter_rows(values_only=True))
    hi=next(i for i,row in enumerate(rr) if row and 'Exchange' in [str(c).strip() for c in row if c])
    hdr=[str(c).replace('\n',' ').strip() if c else None for c in rr[hi]]
    for r in rr[hi+1:]:
        d=dict(zip(hdr,r))
        if d.get('Exchange'): xl[(ex,root(str(d['Root Ticker'])))]=d
XL_SRC='https://www.tsx.com/en/resource/571 (TMX listed-companies workbook, monthly; sheets: '+', '.join(months)+')'
for ex,fn in [('TSX','raw/tsx.json'),('TSXV','raw/tsxv.json')]:
    for x in json.load(open(fn))['results']:
        d=xl.get((ex,root(x['symbol'])),{})
        hqloc=d.get('HQ Location'); hqreg=d.get('HQ Region')
        prov = hqloc if (hqreg=='Canada' and hqloc) else ''
        sector=d.get('Sector') or ''; sub=d.get('Sub Sector') or d.get('Sub-Sector') or ''
        sectype=''
        if ex=='TSX':
            sectype={'ETP':'ETF/ETP','CDR':'CDR','Closed-End Funds':'Closed-end fund'}.get(sector,'Corporate' if sector else '')
            if d.get('SP_Type') in ('Split Shares','Income Trust','Exchange Traded Receipt') and sectype=='Corporate': sectype=d.get('SP_Type')
        else:
            sectype='CPC' if sector=='CPC' else ('Corporate' if sector else '')
        # standing change 2026-09-10: rows the TMX workbook has not classified yet leave corporate scope when the name reads as a fund
        if not sectype and re.search(r'\bETFs?\b|\bFund\b|\bIndex\b|\bPortfolio\b|\bCDR\b|\bTrust Units?\b|\bETP\b', x['name'], re.I): sectype='Fund (by name; not yet in TMX workbook)'
        rows.append(dict(exchange=ex, symbol=x['symbol'], root=root(x['symbol']), name=x['name'],
            instruments='; '.join(i['symbol'] for i in x.get('instruments',[])), security_type=sectype,
            tier='' , tier_src='', sector=sector, sub_sector=sub, hq_prov=prov, hq_region=hqreg or '', hq_country_hint=(hqloc if hqreg and hqreg!='Canada' else ''),
            listing_date=str(d.get('Listing Date') or ''), listing_type=d.get('Listing Type') or '', status='Listed',
            roster_src=f'https://www.tsx.com/json/company-directory/search/{ex.lower()}/^*', enrich_src=(XL_SRC if d else ''),
            sedar_no='', tmx_co_id=d.get('Co_ID') or ''))
# ---- CSE
cse=json.load(open('raw/cse_list.json'))
by=defaultdict(list)
for r in cse:
    if r['status']=='Delisted': continue
    m=re.search(r'/(\d{9})\.json',r.get('sedar_filings') or ''); k=m.group(1) if m else 'NAME:'+r['security_name']
    by[k].append(r)
for k,secs in by.items():
    secs.sort(key=lambda r:(r['security_type']!='Equity',r['symbol']))
    p=secs[0]; sedar=k if not k.startswith('NAME:') else ''
    rows.append(dict(exchange='CSE', symbol=p['symbol'], root=root(p['symbol']), name=p['security_name'],
        instruments='; '.join(f"{s['symbol']} ({s['security_type']})" for s in secs), security_type='Corporate' if p['security_type']=='Equity' else p['security_type'],
        tier=f"CSE Tier {p['tier']}" if p.get('tier') else '', tier_src='https://thecse.com/api/webapi/listed-companies/' if p.get('tier') else '',
        sector=p.get('sector') or '', sub_sector='; '.join(p.get('sector_tags') or []), hq_prov='', hq_region='', hq_country_hint='',
        listing_date=p.get('listing_date') or '', listing_type='', status=p['status'],
        roster_src='https://thecse.com/api/webapi/listed-companies/', enrich_src='', sedar_no=sedar, tmx_co_id=''))
# ---- Cboe Canada
cb=json.load(open('raw/cboe.json'))['data']
TYPE={'etf':'ETF/ETP','dr':'CDR','equity':'Corporate','warrant':'Warrant','debt':'Debt','cef':'Closed-end fund'}
for r in cb:
    rows.append(dict(exchange='Cboe Canada', symbol=r['symbol'], root=root(r['symbol']), name=r['name'], instruments=r['symbol'],
        security_type=TYPE.get(r['security'],r['security'])+(f" ({r['security_sub_type']})" if r.get('security_sub_type') not in (None,'',r['security']) else ''),
        tier='', tier_src='', sector='', sub_sector='', hq_prov='', hq_region='', hq_country_hint='', listing_date='', listing_type='', status='Listed',
        roster_src='https://www-api.cboe.com/ca/equities/listing-directory-data/', enrich_src='', sedar_no='', tmx_co_id=''))
json.dump(rows,open('raw/roster.json','w'),indent=0)
print('rows',len(rows)); print(Counter(r['exchange'] for r in rows)); print(Counter((r['exchange'],r['security_type']) for r in rows).most_common(30))
print('CSE delisted excluded', sum(1 for r in cse if r['status']=='Delisted'), 'CSE issuers w/o sedar no', sum(1 for r in rows if r['exchange']=='CSE' and not r['sedar_no']))
print('TSX/TSXV rows without xlsx enrich', Counter(r['exchange'] for r in rows if r['exchange'] in('TSX','TSXV') and not r['enrich_src']))
