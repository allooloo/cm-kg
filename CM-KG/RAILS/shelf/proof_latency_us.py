r"""SHELF-01 proof (Score, us) — ten latencies checked against the EDGAR filing pages. For each issuer: the first results filing (10-K / 10-Q / 20-F /
40-F) with a stated period end in its sealed Replay year (backfill/replay/<year>/<EX>/<code>.json, rows as sealed); the filing's own EDGAR index page
(…/<accession>-index.htm, declared user agent, SEC fair access) is read for its "Filing Date" and "Period of Report"; the latency Score uses (row date −
period end) must equal the page's (filing date − period of report). The issuer's served score (door/score/<EX>/<code>.json) is shown beside.
Usage: python -X utf8 -I proof_latency_us.py [year] [EX:CODE ...]"""
import os, sys, json, re, time, datetime, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'isin-dis'), os.path.join(HERE, '..', 'door')]
import store, store_index
from score import pe_of, is_result
UA = {'User-Agent': 'Allooloo Technologies Corp. developers@allooloo.ai'}
a = sys.argv[1:]; year = int(a[0]) if a and a[0].isdigit() else 2024
want = [x for x in a if ':' in x] or ['NASDAQ:AAPL', 'NASDAQ:MSFT', 'NYSE:JPM', 'NYSE:KO', 'NYSE:JNJ', 'NASDAQ:WMT', 'NYSE:PFE', 'NASDAQ:NVDA', 'NYSE:BA', 'NYSE:T']
c = store.cont('us'); out = []
def page(url):
    time.sleep(0.25); return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8', 'replace')
for w in want:
    ex, code = w.split(':'); row = {'issuer': w}
    try: rp = json.loads(c.download_blob(f'backfill/replay/{year}/{ex}/{store_index.slug(code)}.json').readall())
    except Exception as e: row['error'] = f'no replay file ({type(e).__name__})'; out.append(row); print(json.dumps(row)); continue
    f = next((r for r in rp['rows'] if is_result(r) and pe_of(r) and (r.get('category') or '').split('/')[0] in ('10-K', '10-Q', '20-F', '40-F')), None)
    if not f: row['error'] = 'no results filing with a period end in the sealed year'; out.append(row); print(json.dumps(row)); continue
    acc = f['reference']; cik = int(f.get('cik') or re.search(r'/data/(\d+)/', f['url']).group(1))
    idx = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{acc}-index.htm"; h = page(idx)
    fd = re.search(r'Filing Date</div>\s*<div class="info">(\d{4}-\d{2}-\d{2})', h); pr = re.search(r'Period of Report</div>\s*<div class="info">(\d{4}-\d{2}-\d{2})', h)
    d = lambda s: datetime.date.fromisoformat(s[:10])
    row.update({'form': f['category'], 'accession': acc, 'page': idx, 'row_date': f['date'], 'row_period_end': pe_of(f), 'row_latency_days': (d(f['date']) - d(pe_of(f))).days,
                'page_filing_date': fd and fd.group(1), 'page_period_of_report': pr and pr.group(1)})
    row['page_latency_days'] = (d(row['page_filing_date']) - d(row['page_period_of_report'])).days if fd and pr else None
    row['match'] = row['page_latency_days'] == row['row_latency_days'] and row['page_filing_date'] == f['date'][:10] and row['page_period_of_report'] == pe_of(f)
    try:
        sc = json.loads(c.download_blob(f'door/score/{ex}/{store_index.slug(code)}.json').readall())
        s = sc.get('score') or sc; row['served_latency_median'] = s.get('latency_days_median'); row['served_latency_n'] = s.get('latency_filings_with_period_end')
    except Exception as e: row['served'] = f'no score file ({type(e).__name__})'
    out.append(row); print(json.dumps(row))
n = sum(1 for r in out if r.get('match')); print(json.dumps({'checked': len(out), 'match': n, 'PASS': n == len(out) == 10}))
json.dump(out, open(os.path.join(HERE, f'proof-latency-us-{datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%MZ")}.json'), 'w'), indent=1)
