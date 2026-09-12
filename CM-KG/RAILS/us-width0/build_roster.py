"""Step 2 — one roster row per exchange-listed EDGAR filer from company_tickers_exchange.json joined to the submissions header. Scope: exchange in
NYSE / Nasdaq / CBOE (OTC and blank-exchange filers are counted, not carried). One row per (exchange, ticker); a filer with several tickers on one
exchange keeps every line (share classes). Corporate scope = entity type 'operating' with an SIC code outside the fund / trust pockets (6221 commodity
pools, 6798 REITs stay corporate; 6770 blank checks are carried as 'SPAC (by SIC)'). Writes raw/roster.json."""
import json, re
from collections import Counter
ct = json.load(open('raw/company_tickers_exchange.json', encoding='utf-8')); SRC = ct['src']
subs = {}
for line in open('raw/submissions.jsonl', encoding='utf-8'):
    d = json.loads(line); subs[d['cik']] = d
EXCH = {'NYSE': 'NYSE', 'Nasdaq': 'Nasdaq', 'CBOE': 'Cboe'}
FUND_SIC = {'6722', '6726'}  # management investment offices; unit investment trusts and closed-end funds
rows = []; seen = set(); skipped = Counter()
for r in ct['rows']:
    ex = r.get('exchange') or ''
    if ex not in EXCH: skipped[ex or 'blank'] += 1; continue
    k = (EXCH[ex], r['ticker'])
    if k in seen: continue
    seen.add(k); s = subs.get(r['cik']) or {}
    sic = str(s.get('sic') or ''); et = (s.get('entity_type') or '').lower(); name = (s.get('name') or r['name'] or '').strip()
    if sic in FUND_SIC or re.search(r'\b(ETF|EXCHANGE TRADED FUND|TRUST SERIES|INDEX FUND)\b', name.upper()): st = 'Fund / trust (by SIC or name)'
    elif sic == '6770': st = 'SPAC (by SIC 6770)'
    elif et and et != 'operating': st = f'Non-operating entity type ({et})'
    else: st = 'Corporate'
    b = s.get('business') or {}; la = s.get('latest_annual') or {}
    rows.append(dict(exchange=EXCH[ex], symbol=r['ticker'], cik=r['cik'], name=name, name_edgar_list=r['name'], security_type=st, sic=sic, sic_desc=s.get('sic_desc') or '', state_inc=s.get('state_inc') or '', state_inc_desc=s.get('state_inc_desc') or '',
                     fye=s.get('fye') or '', category=s.get('category') or '', entity_type=s.get('entity_type') or '', ein=s.get('ein') or '', former_names=s.get('former_names') or [], tickers=s.get('tickers') or [], exchanges=s.get('exchanges') or [],
                     business_street=b.get('street') or '', business_city=b.get('city') or '', business_state=b.get('state') or '', business_state_desc=b.get('state_desc') or '', business_zip=b.get('zip') or '', website=s.get('website') or '', ir_website=s.get('ir_website') or '',
                     latest_annual_form=la.get('form') or '', latest_annual_date=la.get('date') or '', latest_annual_accession=la.get('accession') or '', latest_annual_doc=la.get('doc') or '', filings_12m=len(s.get('recent_12m') or []),
                     roster_src=SRC, submissions_src=s.get('src') or '', submissions_error=s.get('error'), status='Listed (EDGAR company_tickers_exchange)'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['exchange'] for r in rows), Counter(r['security_type'] for r in rows).most_common(6)); print('skipped by exchange', dict(skipped)); print('with submissions', sum(1 for r in rows if r['submissions_src'] and not r['submissions_error']), 'with latest annual', sum(1 for r in rows if r['latest_annual_accession']), 'with SIC', sum(1 for r in rows if r['sic']), 'with state of incorporation', sum(1 for r in rows if r['state_inc']))
