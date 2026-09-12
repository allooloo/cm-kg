"""Step 1 — pull the United States roster and issuer headers into raw/ (a junction to the open pond drop POND\\us-cm-kg\\width0\\<date>\\). EDGAR is keyless
and public; every request carries the declared User-Agent EDGAR asks for and stays under 8 requests a second.
  company_tickers_exchange.json ... every EDGAR filer with a ticker: CIK, name, ticker, exchange (Nasdaq, NYSE, CBOE, OTC or blank)
  submissions/CIK##########.json .. the issuer header: name as filed, SIC code and description, state of incorporation, fiscal year end, filer category,
                                    business and mailing addresses, former names, EIN, tickers and exchanges, and the recent filings list (form, date,
                                    accession, primary document). Kept compact: header + the last 12 months of filings + the latest annual report
                                    (10-K / 20-F / 40-F / 10-KT) so the Width 1 rail reads from the drop, not from EDGAR again.
No ISIN, LEI, auditor, registrar or newswire comes from EDGAR at this step; LEI and ISIN follow through GLEIF (lei_match.py, lei_records.py)."""
import requests, json, os, sys, time, threading, datetime
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'Allooloo Technologies Corp. allooloo@users.noreply.github.com', 'Accept-Encoding': 'gzip, deflate', 'Accept': 'application/json'}
os.makedirs('raw', exist_ok=True)
TODAY = datetime.date.today(); SINCE = (TODAY - datetime.timedelta(days=366)).isoformat()
_gate = threading.Lock(); _last = [0.0]
def get(url, tries=4, **kw):
    for i in range(tries):
        with _gate:
            wait = 0.13 - (time.time() - _last[0])
            if wait > 0: time.sleep(wait)
            _last[0] = time.time()
        try:
            r = requests.get(url, headers=UA, timeout=60, **kw)
            if r.status_code in (429, 403, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
def roster():
    src = 'https://www.sec.gov/files/company_tickers_exchange.json'
    j = get(src).json(); f = j['fields']; rows = [dict(zip(f, d)) for d in j['data']]
    json.dump({'src': src, 'fetched': TODAY.isoformat(), 'rows': rows}, open('raw/company_tickers_exchange.json', 'w', encoding='utf-8'), ensure_ascii=False)
    from collections import Counter
    print('company_tickers_exchange rows', len(rows), Counter((r.get('exchange') or 'blank') for r in rows).most_common(8), flush=True)
    return rows
ANNUAL = ('10-K', '10-K405', '10-KT', '20-F', '40-F', '10-K/A')
def submission(cik):
    url = f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json'; r = get(url)
    if r is None or r.status_code != 200: return {'cik': cik, 'error': None if r is None else r.status_code, 'src': url}
    j = r.json(); rec = j.get('filings', {}).get('recent', {}); n = len(rec.get('form', []))
    recent = []; latest_annual = None
    for i in range(n):
        f = {'form': rec['form'][i], 'date': rec['filingDate'][i], 'accession': rec['accessionNumber'][i], 'doc': rec.get('primaryDocument', [''] * n)[i], 'desc': rec.get('primaryDocDescription', [''] * n)[i], 'items': rec.get('items', [''] * n)[i], 'report_date': rec.get('reportDate', [''] * n)[i]}
        if f['date'] >= SINCE: recent.append(f)
        if latest_annual is None and f['form'] in ANNUAL and f['form'] != '10-K/A': latest_annual = f
    b = (j.get('addresses') or {}).get('business') or {}; m = (j.get('addresses') or {}).get('mailing') or {}
    return {'cik': cik, 'src': url, 'name': j.get('name'), 'sic': j.get('sic'), 'sic_desc': j.get('sicDescription'), 'state_inc': j.get('stateOfIncorporation'), 'state_inc_desc': j.get('stateOfIncorporationDescription'),
            'fye': j.get('fiscalYearEnd'), 'category': j.get('category'), 'ein': j.get('ein'), 'entity_type': j.get('entityType'), 'tickers': j.get('tickers') or [], 'exchanges': j.get('exchanges') or [], 'former_names': [x.get('name') for x in (j.get('formerNames') or [])],
            'business': {'street': ', '.join(v for v in (b.get('street1'), b.get('street2')) if v), 'city': b.get('city'), 'state': b.get('stateOrCountry'), 'state_desc': b.get('stateOrCountryDescription'), 'zip': b.get('zipCode')},
            'mailing': {'city': m.get('city'), 'state': m.get('stateOrCountry')}, 'website': j.get('website') or '', 'ir_website': j.get('investorWebsite') or '', 'filings_total': n, 'recent_12m': recent, 'latest_annual': latest_annual, 'fetched': TODAY.isoformat()}
def submissions(rows):
    fn = 'raw/submissions.jsonl'; done = set()
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try: done.add(json.loads(line)['cik'])
            except Exception: pass
    todo = sorted({r['cik'] for r in rows if (r.get('exchange') or '') not in ('', 'OTC')} - done)
    print('submissions todo', len(todo), 'done', len(done), flush=True)
    out = open(fn, 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
    def work(cik):
        d = submission(cik)
        with lock:
            out.write(json.dumps(d, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 250 == 0: print('submissions', cnt[0], '/', len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '4'))) as ex: list(ex.map(work, todo))
    print('submissions DONE', flush=True)
if __name__ == '__main__':
    rows = roster() if not os.path.exists('raw/company_tickers_exchange.json') or 'roster' in sys.argv else json.load(open('raw/company_tickers_exchange.json', encoding='utf-8'))['rows']
    if 'roster' not in sys.argv or 'submissions' in sys.argv: submissions(rows)
