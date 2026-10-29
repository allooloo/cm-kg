r"""BACKFILL-02 (CEO order 2026-10-27) — ca history widened from a free public source: SEC EDGAR, for the ca issuers that are also SEC registrants.
Who: every corporate issuer on the ca list (ca-issuers.xlsx) whose legal name matches an SEC registrant (company_tickers.json) AND whose EDGAR record says
Canada (state of incorporation or business address A0–A9, B0, Z4). A name match EDGAR does not place in Canada is not taken (named in the log).
What: data.sec.gov/submissions — filings.recent and every older page — kept when dated inside the window; event type and title as the live US pipeline types
them (us-job\us_pipeline.py FORM_TYPE / ITEM_TYPE, read from its source). Each row is filed under the issuer's ca listing (exchange, ticker, legal name).
  period_end      on 10-K, 10-Q, 40-F, 20-F (and amendments): EDGAR's 'period of report' as filed (reportDate) — only where the filing states it
  auditor_named   on 10-K, 40-F and 20-F filed from 2021-12-15: the inline XBRL tag dei:AuditorName (with dei:AuditorLocation) read from the filing's own
                  primary document — only where the filing states it; otherwise absent
Declared user agent (developers@allooloo.ai), under the SEC's fair-access rate. Window: WINDOW_DAYS (the backfill adapter opens it back to the epoch).
Writes raw/edgar_history.jsonl ({key, events[]} per issuer). Env CA_EDGAR_ONLY=<ticker,…> limits the run (a proof run)."""
import os, re, json, time, html, datetime, threading
from concurrent.futures import ThreadPoolExecutor
import requests
from common import load_issuers, norm
ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO')
src = open(os.path.join(ROOT, 'CM-KG', 'RAILS', 'us-job', 'us_pipeline.py'), encoding='utf-8').read()
ns = {'re': re}; exec('\n'.join(l for l in src.splitlines() if l.startswith(('FORM_TYPE = ', 'ITEM_TYPE = '))), ns); FORM_TYPE, ITEM_TYPE = ns['FORM_TYPE'], ns['ITEM_TYPE']
UA = {'User-Agent': 'Allooloo Technologies Corp. developers@allooloo.ai', 'Accept-Encoding': 'gzip, deflate'}
RPS = 5; CANADA = {'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'B0', 'Z4'}
PERIOD_FORMS = re.compile(r'^(10-K|10-KT|10-Q|40-F|20-F)(/A)?$'); ANNUAL = re.compile(r'^(10-K|10-KT|40-F|20-F)(/A)?$')
DAYS = int(os.environ.get('WINDOW_DAYS', '400')); UNTIL = datetime.date.today().isoformat(); SINCE = (datetime.date.today() - datetime.timedelta(days=DAYS - 1)).isoformat()
_lock = threading.Lock(); _last = [0.0]
def get(u, as_json=True):
    for i in range(4):
        with _lock:
            w = 1.0 / RPS - (time.time() - _last[0])
            if w > 0: time.sleep(w)
            _last[0] = time.time()
        r = requests.get(u, headers=UA, timeout=90)
        if r.status_code == 429 or r.status_code >= 500: time.sleep(10 * (i + 1)); continue
        r.raise_for_status(); return r.json() if as_json else r.text
    r.raise_for_status()
def key(n): return ' '.join(w for w in norm(n).split() if w not in ('inc', 'corp', 'corporation', 'ltd', 'limited', 'the', 'co', 'company', 'plc', 'ltee', 'incorporated'))
AUD = re.compile(r'name="dei:AuditorName"[^>]*>(.*?)</ix:nonNumeric>', re.S | re.I); LOC = re.compile(r'name="dei:AuditorLocation"[^>]*>(.*?)</ix:nonNumeric>', re.S | re.I)
def text(x): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()
def main():
    sec = get('https://www.sec.gov/files/company_tickers.json'); by = {}
    for s in sec.values(): by.setdefault(key(s['title']), []).append(s)
    only = {x.strip().upper() for x in os.environ.get('CA_EDGAR_ONLY', '').split(',') if x.strip()}
    issuers = [r for r in load_issuers() if key(r['name']) in by and (not only or str(r['ticker']).upper() in only)]
    print('ca issuers name-matched to SEC registrants:', len(issuers), '· window', SINCE, UNTIL, flush=True)
    os.makedirs('raw', exist_ok=True); out = open('raw/edgar_history.jsonl', 'w', encoding='utf-8'); stats = {'taken': 0, 'not_canada': 0, 'error': 0, 'events': 0, 'period_end': 0, 'auditor': 0}
    def one(r):
        cik = by[key(r['name'])][0]['cik_str']
        try:
            s = get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json')
            here = {s.get('stateOfIncorporation'), ((s.get('addresses') or {}).get('business') or {}).get('stateOrCountry')} & CANADA
            if not here: return {'key': f"{r['exchange']}:{r['ticker']}", 'not_canada': True, 'cik': cik, 'sec_name': s.get('name')}
            pages = [s['filings']['recent']]
            for fl in s['filings'].get('files') or []:
                if fl.get('filingTo', '9999') >= SINCE and fl.get('filingFrom', '0000') <= UNTIL: pages.append(get('https://data.sec.gov/submissions/' + fl['name']))
            evs = []
            for pg in pages:
                ks = list(pg.keys()); n = len(pg.get('accessionNumber') or [])
                for i in range(n):
                    fz = {x: (pg[x][i] if i < len(pg[x]) else None) for x in ks}; d = fz.get('filingDate') or ''
                    if not (SINCE <= d <= UNTIL): continue
                    form = fz.get('form') or ''; items = fz.get('items') or ''
                    et = next((t for t, pat in FORM_TYPE if re.match(pat, form)), 'regulatory_filing')
                    if form.startswith('8-K') and items:
                        for it in [x.strip() for x in items.split(',')]:
                            if it in ITEM_TYPE: et = ITEM_TYPE[it]; break
                    acc = fz['accessionNumber'].replace('-', ''); doc = fz.get('primaryDocument'); url = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}' if doc else f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/'
                    e = {'exchange': r['exchange'], 'ticker': r['ticker'], 'isin': r['isin'], 'lei': r['lei'], 'issuer': r['name'], 'cik': str(cik), 'date': d, 'event_type': et,
                         'title': form + (f" — {fz.get('primaryDocDescription')}" if fz.get('primaryDocDescription') else '') + (f' (items {items})' if items else ''),
                         'category': form, 'reference': fz['accessionNumber'], 'language': 'en', 'wire': 'EDGAR', 'source': 'SEC EDGAR filing index', 'url': url,
                         'read_by': 'EDGAR submissions API (filings list per CIK, every page) — ca issuer, SEC registrant placed in Canada by EDGAR', 'state': 'sourced'}
                    if PERIOD_FORMS.match(form) and fz.get('reportDate'):
                        e['period_end'] = fz['reportDate']; e['period_end_source'] = "EDGAR filing index — period of report as filed (reportDate)"
                    if ANNUAL.match(form) and d >= '2021-12-15' and doc:
                        try:
                            h = get(url, as_json=False); m = AUD.search(h); lm = LOC.search(h)
                            if m and text(m.group(1)):
                                e['auditor_named'] = text(m.group(1)); e['auditor_source'] = url + ' (inline XBRL dei:AuditorName)'
                                if lm and text(lm.group(1)): e['auditor_location'] = text(lm.group(1))
                        except Exception as x: e['auditor_read_error'] = repr(x)[:120]
                    evs.append(e)
            return {'key': f"{r['exchange']}:{r['ticker']}", 'cik': cik, 'events': evs}
        except Exception as x: return {'key': f"{r['exchange']}:{r['ticker']}", 'error': repr(x)[:200]}
    with ThreadPoolExecutor(4) as ex:
        for res in ex.map(one, issuers):
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush()
            if res.get('not_canada'): stats['not_canada'] += 1
            elif res.get('error'): stats['error'] += 1
            else:
                stats['taken'] += 1; stats['events'] += len(res['events']); stats['period_end'] += sum(1 for e in res['events'] if e.get('period_end')); stats['auditor'] += sum(1 for e in res['events'] if e.get('auditor_named'))
    out.close(); print('edgar_history', json.dumps(stats), flush=True)
if __name__ == '__main__': main()
