"""Step 7 — one roster row per issuer per market from the raw feeds:
  LSE Main Market and AIM: price-explorer equity instruments (raw/lse_explorer.json) grouped by issuer code, joined to the per-instrument
  reference record (raw/lse_alldata.jsonl: ISIN, SEDOL, segment, MiFIR type, funds type, admission date, ICB codes) and the issuer profile
  (raw/lse_issuer.jsonl: address, country of incorporation, web address, ICB names, listing category). Sector name from the explorer sector sweep.
  Aquis: raw/aquis.json (company records read from the exchange's own page data).
Writes raw/roster.json. No price field exists in any input at this point."""
import json, os, re
from collections import Counter, defaultdict
def load(fn, k):
    d = {}
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try:
                x = json.loads(line); d[x[k]] = x
            except Exception: pass
    return d
ex = json.load(open('raw/lse_explorer.json'))
ALL = load('raw/lse_alldata.jsonl', 'tidm'); ISS = load('raw/lse_issuer.jsonl', 'issuercode')
EXPL_SRC = 'https://www.londonstockexchange.com/live-markets/market-data-dashboard/price-explorer (price-explorer feed api.londonstockexchange.com/api/v1/components/refresh, markets=%s, categories=EQUITY, showonlylse=true)'
MKT = {'MAINMARKET': 'LSE Main Market', 'AIM': 'AIM'}
rows = []
for mkt, blk in ex['markets'].items():
    by = defaultdict(list)
    for x in blk['rows']: by[x['issuercode']].append(x)
    secmap = ex['sectors'].get(mkt, {})
    for code, insts in by.items():
        insts.sort(key=lambda x: (x['tidm'] != (ISS.get(code, {}).get('ref') or {}).get('defaultinstrumentcode'), x['tidm']))
        p = insts[0]; a = ALL.get(p['tidm'], {}); prof = ISS.get(code, {}); ref = prof.get('ref') or {}
        sec = secmap.get(p['tidm']) or next((secmap[i['tidm']] for i in insts if i['tidm'] in secmap), None)
        ftype = a.get('fundsType') or ''; mifir = a.get('mifir') or ''; lc = ref.get('listingcategory') or ''
        if mifir == 'DPRS': stype = 'Depositary receipts'
        elif ftype and ftype != 'NONE': stype = 'Fund (' + ftype + ')'
        elif re.search(r'\b(?:INVESTMENT TRUST|INV TRUST|INVESTMENT COMPANY|VCT|FUND)\b', p['issuername'], re.I) or 'Closed-ended' in lc or 'closed ended' in lc.lower(): stype = 'Closed-ended investment company'
        else: stype = 'Corporate'
        rows.append(dict(exchange=MKT[mkt], market_code=mkt, symbol=p['tidm'], issuercode=code, name=p['issuername'], name_display=prof.get('displayname') or '',
            instruments='; '.join(f"{i['tidm']} ({i.get('name') or i.get('description') or ''})" for i in insts),
            security_type=stype, listing_category=lc, segment=a.get('segment') or '', mifir=mifir, funds_type=ftype, isin=p.get('isin') or a.get('isin') or '',
            sedol=a.get('sedol') or '', instrument_country=a.get('country') or '', currency=a.get('currency') or p.get('currency') or '',
            admission_date=a.get('listingadmissiondate') or ref.get('starttradabledate') or '', trading_status=a.get('tradingstatus') or '', suspend=a.get('suspend') or '',
            sector=(ref.get('icbsector') or (sec[1] if sec else '')), sector_code=(ref.get('icbsectorcode') or a.get('sectorcode') or (sec[0] if sec else '')),
            subsector=ref.get('icbsubsector') or '', subsector_code=ref.get('icbsubsectorcode') or a.get('subsectorcode') or '', industry=ref.get('icbindustry') or '', supersector=ref.get('icbsupersector') or '',
            sector_src=(prof.get('src') if ref.get('icbsector') else (EXPL_SRC % mkt if sec else '')), sector_rb=('LSE issuer profile (exchange site)' if ref.get('icbsector') else ('LSE price-explorer sector filter (exchange list)' if sec else '')),
            address=ref.get('address') or '', country_inc=ref.get('countryofincorporation') or '', website=ref.get('webaddress') or '', index_roundel=(prof.get('roundels') or {}).get('indexroundel') or '',
            profile_src=prof.get('src') or '', profile_err=prof.get('error') or '', alldata_src=a.get('src') or '', alldata_err=a.get('error') or '',
            roster_src=EXPL_SRC % mkt, status='Listed'))
aq = json.load(open('raw/aquis.json', encoding='utf-8')) if os.path.exists('raw/aquis.json') else {'rows': []}
for r in aq['rows']:
    if r.get('_error'): continue
    it = r.get('instrument_type') or ''
    stype = 'Corporate' if it in ('Ordinary Shares', 'B Ordinary Shares') else it
    rows.append(dict(exchange='Aquis Stock Exchange', market_code='AQSE', symbol=r['symbol'], issuercode='', name=r['name'], name_display=r['name'], instruments=f"{r['symbol']} ({it})",
        security_type=stype, listing_category=r.get('market_type') or '', segment=r.get('listing_type_name') or '', mifir='', funds_type='', isin=r.get('isin') or '', sedol='',
        instrument_country='', currency=r.get('currency') or '', admission_date=r.get('admission_date') or '', trading_status=r.get('status') or '', suspend='',
        sector=r.get('sector') or '', sector_code=str(r.get('sector_id') or ''), subsector='', subsector_code='', industry='', supersector='',
        sector_src=r['_url'] if r.get('sector') else '', sector_rb='aquis.eu company page data (exchange site)' if r.get('sector') else '',
        address=', '.join(v for v in [r.get('registered_address1'), r.get('registered_address2'), r.get('registered_town'), r.get('registered_county'), r.get('registered_post_code'), r.get('registered_country')] if v) ,
        country_inc='', website=r.get('website_url') or '', index_roundel='', profile_src=r['_url'], profile_err='', alldata_src='', alldata_err='',
        aq_registrar=(r.get('registrar') or '').strip(), aq_registrar_town=r.get('registrar_town') or '', aq_adviser=r.get('corporate_adviser') or '', aq_reg_town=r.get('registered_town') or '', aq_reg_country=r.get('registered_country') or '',
        roster_src=aq.get('source', 'https://www.aquis.eu/companies'), status=r.get('status') or ''))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows)); print(Counter(r['exchange'] for r in rows)); print(Counter((r['exchange'], r['security_type']) for r in rows).most_common(20))
print('segments', Counter((r['exchange'], r['segment']) for r in rows).most_common(15)); print('listing categories', Counter(r['listing_category'] for r in rows).most_common(12))
print('profile errors', sum(1 for r in rows if r['profile_err']), 'alldata errors', sum(1 for r in rows if r['alldata_err']), 'no ISIN', sum(1 for r in rows if not r['isin']), 'no sector', sum(1 for r in rows if not r['sector']))
