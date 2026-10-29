r"""edgar_backfill.py — BACKFILL-01 adapter 'edgar' (DAY ORDER 7, 2026-10-25): the United States, SEC EDGAR, pointed backward.
Issuers: the SEC's own exchange ticker list (company_tickers_exchange.json — the list the live US node reads), the exchanges the node carries (NYSE, Nasdaq,
CBOE, TXSE). Filings: data.sec.gov/submissions/CIK##########.json — filings.recent plus every older page in filings.files — kept when dated inside
[since, until]. Event type and title exactly as the live pipeline (us_pipeline.py FORM_TYPE / ITEM_TYPE, read from its source, not copied). Declared user
agent (developers@allooloo.ai), under the SEC's fair-access rate (the policy line's pace). Resumable: the cursor is the CIKs already read.
Output (stream, SHELF-01 2026-10-27): one line per filing {cik, e} — never fanned out per ticker here (a bank's 45 listed notes once made one filer
4.4 GB in memory) — then {key: cik} when the filer is read whole; the filer's listings (exchange, ticker, name) go once to <out>.listings.json. The seal fans
each filing out to every listing line month by month (backfill.py edgar_stream), so the rows are exactly what the live record carries.
Usage: python -X utf8 edgar_backfill.py <since> <until> <out.ndjson>"""
import os, sys, json, re, time, threading, requests
from concurrent.futures import ThreadPoolExecutor
SINCE, UNTIL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO')
src = open(os.path.join(ROOT, 'CM-KG', 'RAILS', 'us-job', 'us_pipeline.py'), encoding='utf-8').read()
ns = {'re': re}; exec('\n'.join(l for l in src.splitlines() if l.startswith(('FORM_TYPE = ', 'ITEM_TYPE = '))), ns); FORM_TYPE, ITEM_TYPE = ns['FORM_TYPE'], ns['ITEM_TYPE']
POL = json.load(open(os.environ.get('BACKFILL_POLICY') or os.path.join(HERE, 'policy.json'), encoding='utf-8'))['markets']['us']
RPS = max(1, int((POL.get('pace') or {}).get('rps') or 5)); UA = {'User-Agent': 'Allooloo Technologies Corp. developers@allooloo.ai', 'Accept-Encoding': 'gzip, deflate'}
EXCH = {'NYSE': 'NYSE', 'Nasdaq': 'NASDAQ', 'CBOE': 'CBOE', 'TXSE': 'TXSE'}
_lock = threading.Lock(); _last = [0.0]
def get(u):
    for i in range(4):
        with _lock:
            w = 1.0 / RPS - (time.time() - _last[0])
            if w > 0: time.sleep(w)
            _last[0] = time.time()
        r = requests.get(u, headers=UA, timeout=60)
        if r.status_code == 429 or r.status_code >= 500: time.sleep(10 * (i + 1)); continue
        r.raise_for_status(); return r.json()
    r.raise_for_status()
lst = get('https://www.sec.gov/files/company_tickers_exchange.json'); f = lst['fields']
rows = [dict(zip(f, x)) for x in lst['data'] if x[f.index('exchange')] in EXCH]
by_cik = {}
for r in rows: by_cik.setdefault(r['cik'], []).append(r)
print('EDGAR issuers', len(by_cik), 'listings', len(rows), 'window', SINCE, UNTIL, flush=True)
json.dump({str(k): [[EXCH[r['exchange']], r['ticker'], r['name']] for r in v] for k, v in by_cik.items()}, open(OUT + '.listings.json', 'w', encoding='utf-8'), ensure_ascii=False)
done = set()
if os.path.exists(OUT + '.part'):
    for l in open(OUT + '.part', encoding='utf-8'):
        try:
            d = json.loads(l)
            if 'key' in d and not d.get('error'): done.add(d['key'])
        except Exception: pass
out = open(OUT + '.part', 'a', encoding='utf-8'); _w = threading.Lock(); tally = {'filers': 0, 'filings': 0, 'errors': 0}
def filings(block):
    k = list(block.keys()); n = len(block.get('accessionNumber') or [])
    for i in range(n): yield {x: (block[x][i] if i < len(block[x]) else None) for x in k}
def one(cik):
    try:
        s = get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json'); pages = [s['filings']['recent']]
        for fl in s['filings'].get('files') or []:
            if fl.get('filingTo', '9999') >= SINCE and fl.get('filingFrom', '0000') <= UNTIL: pages.append(get('https://data.sec.gov/submissions/' + fl['name']))
        del s; lines = []
        for pg in pages:
            for fz in filings(pg):
                d = fz.get('filingDate') or ''
                if not (SINCE <= d <= UNTIL): continue
                form = fz.get('form') or ''; items = fz.get('items') or ''
                et = next((t for t, pat in FORM_TYPE if re.match(pat, form)), 'regulatory_filing')
                if form.startswith('8-K') and items:
                    for it in [x.strip() for x in items.split(',')]:
                        if it in ITEM_TYPE: et = ITEM_TYPE[it]; break
                acc = fz['accessionNumber'].replace('-', ''); doc = fz.get('primaryDocument'); url = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}' if doc else f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/'
                lines.append(json.dumps({'cik': str(cik), 'e': {'cik': str(cik), 'date': d, 'event_type': et, 'title': form + (f" — {fz.get('primaryDocDescription')}" if fz.get('primaryDocDescription') else '') + (f' (items {items})' if items else ''),
                             'category': form, 'reference': fz['accessionNumber'], 'language': 'en', 'wire': 'EDGAR', 'source': 'SEC EDGAR filing index', 'url': url, 'read_by': 'EDGAR submissions API (filings list per CIK, every page)', 'detail': f"report date {fz.get('reportDate') or ''}", 'state': 'sourced'}}, ensure_ascii=False) + '\n')
        del pages
        with _w:
            out.writelines(lines); out.write(json.dumps({'key': str(cik), 'filings': len(lines)}) + '\n'); out.flush(); tally['filers'] += 1; tally['filings'] += len(lines)
            if tally['filers'] % 500 == 0: print('EDGAR filers', tally['filers'], 'filings', tally['filings'], flush=True)
    except Exception as e:
        with _w: out.write(json.dumps({'key': str(cik), 'error': repr(e)[:200]}) + '\n'); out.flush(); tally['errors'] += 1
todo = [c for c in by_cik if str(c) not in done]
if os.environ.get('EDGAR_LIMIT'): todo = todo[:int(os.environ['EDGAR_LIMIT'])]   # smoke test only; the nightly reads every CIK
with ThreadPoolExecutor(min(RPS, 8)) as ex: list(ex.map(one, todo))
out.close(); print('EDGAR read', json.dumps(tally), flush=True)
if tally['errors']: raise SystemExit(f"EDGAR: {tally['errors']} filers not read — the run resumes them (the .part keeps the rest); not sealed")
os.replace(OUT + '.part', OUT); print('EDGAR done', OUT, flush=True)
