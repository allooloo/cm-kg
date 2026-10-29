"""India Width 1 events - corporate announcements filed by listed companies under SEBI LODR, as published by the exchanges.

Primary store: NSE corporate announcements (https://www.nseindia.com/companies-listing/corporate-filings-announcements), whose page
loads https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=<SYMBOL>&from_date=DD-MM-YYYY&to_date=DD-MM-YYYY.
The API needs the Akamai session cookies that a plain GET of https://www.nseindia.com/ sets (on 2026-10-24 that GET itself answered
403 but set the cookies, and the API then answered 200). One call returns the whole window (no paging; 12 months worked).
Fields kept: an_dt (IST), desc (the store's own subject category, English), attchmntText (subject text as filed), attchmntFile (the
filing PDF on nsearchives.nseindia.com), seq_id, sm_isin, sm_name. NSE is an English store: type_en = desc as published.

Fallback store: BSE corporate announcements (https://www.bseindia.com/corporates/ann.html), whose page loads
https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?pageno=N&strCat=-1&strPrevDate=YYYYMMDD&strScrip=<BSE code>
&strSearch=P&strToDate=YYYYMMDD&strType=C&subcategory=-1 (50 per page, Table1.ROWCNT = total). Needs the browser's Referer/Origin/
Sec-Fetch-* headers (a bare request gets Akamai 403). Fields: NEWS_DT, CATEGORYNAME (+ SUBCATNAME), NEWSSUB (subject as filed),
HEADLINE, ATTACHMENTNAME -> https://www.bseindia.com/xml-data/corpfiling/AttachLive|AttachHis/<file> (AttachHis when PDFFLAG=1).
BSE is an English store: type_en = CATEGORYNAME as published.

Input: ISIN (resolved to the NSE symbol / BSE code through the exchanges' own lists, see roster.py), an NSE symbol, or a BSE
numeric code. source='auto' uses NSE when the ISIN has an NSE symbol, else BSE.

fetch(isin_or_issuer, since, source='auto') -> [{"date","type","type_en","title","url","source", ...}]
Usage: python events.py [ISIN ...]   (default: three large issuers) writes samples/events-<date>.json
"""
import os, re, sys, json, time, datetime, threading
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roster  # noqa: E402  (same folder: the exchange lists used to resolve ISIN -> symbol / code)

UA = roster.UA
NSE_HOME = 'https://www.nseindia.com/'
NSE_PAGE = 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'
NSE_API = 'https://www.nseindia.com/api/corporate-announcements'
BSE_PAGE = 'https://www.bseindia.com/corporates/ann.html'
BSE_API = 'https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w'
SRC_NSE = 'NSE corporate announcements (nseindia.com api/corporate-announcements)'
SRC_BSE = 'BSE corporate announcements (api.bseindia.com AnnSubCategoryGetData)'
_lock = threading.Lock(); _last = [0.0]; _maps = {}; _nse = {}


def _pace(gap=0.6):
    with _lock:
        w = _last[0] + gap - time.time()
        if w > 0:
            time.sleep(w)
        _last[0] = time.time()


def _maps_load():
    if not _maps:
        nse = roster.nse_list(roster.NSE_EQ) + roster.nse_list(roster.NSE_SME)
        _maps['nse'] = {r['isin']: r['symbol'] for r in nse if r['isin']}
        _maps['nse_sym'] = {r['symbol'] for r in nse}
        try:
            bse = roster.bse_list('Active')
        except Exception:
            bse = []
        _maps['bse'] = {r['isin']: r['code'] for r in bse if r['isin']}
    return _maps


def _nse_session():
    if 's' not in _nse:
        s = requests.Session(); s.headers.update({'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9',
                                                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
        _pace(); s.get(NSE_HOME, timeout=60)          # sets the Akamai cookies (the page itself may answer 403)
        _nse['s'] = s
    return _nse['s']


def nse_events(symbol, since, until):
    s = _nse_session(); out = []
    for i in range(4):
        _pace(0.8)
        r = s.get(NSE_API, params={'index': 'equities', 'symbol': symbol, 'from_date': since.strftime('%d-%m-%Y'), 'to_date': until.strftime('%d-%m-%Y')},
                  headers={'Accept': 'application/json, text/plain, */*', 'Referer': NSE_PAGE}, timeout=90)
        if r.status_code == 200 and r.headers.get('content-type', '').startswith('application/json'):
            break
        _nse.pop('s', None); time.sleep(4 * (i + 1)); s = _nse_session()
    else:
        raise RuntimeError(f'NSE announcements did not answer for {symbol} ({r.status_code})')
    for d in r.json():
        try:
            dt = datetime.datetime.strptime(d['an_dt'], '%d-%b-%Y %H:%M:%S')
        except (KeyError, ValueError):
            continue
        if dt.date() < since:
            continue
        url = d.get('attchmntFile') or None
        out.append({'date': dt.strftime('%Y-%m-%dT%H:%M:%S') + '+05:30', 'type': d.get('desc'), 'type_en': d.get('desc'),
                    'title': (d.get('attchmntText') or '').strip(), 'url': url if url and url.startswith('http') else None,
                    'source': SRC_NSE, 'seq_id': d.get('seq_id'), 'isin': d.get('sm_isin'), 'issuer': d.get('sm_name'), 'symbol': d.get('symbol')})
    out.sort(key=lambda e: e['date'], reverse=True)
    return out


def bse_events(code, since, until):
    s = requests.Session(); s.headers.update(roster.BSE_HEADERS); out, page, total = [], 1, None
    while True:
        for i in range(4):
            _pace(0.8)
            try:
                r = s.get(BSE_API, params={'pageno': page, 'strCat': -1, 'strPrevDate': since.strftime('%Y%m%d'), 'strScrip': code, 'strSearch': 'P',
                                           'strToDate': until.strftime('%Y%m%d'), 'strType': 'C', 'subcategory': -1}, timeout=90)
                if r.status_code == 200 and r.headers.get('content-type', '').startswith('application/json'):
                    break
            except requests.RequestException:
                pass
            time.sleep(4 * (i + 1))
        else:
            raise RuntimeError(f'BSE announcements did not answer for {code}')
        js = r.json(); tab = js.get('Table') or []
        if total is None:
            total = (js.get('Table1') or [{}])[0].get('ROWCNT') or 0
        for d in tab:
            dt = (d.get('NEWS_DT') or d.get('DT_TM') or '')[:19]
            att = (d.get('ATTACHMENTNAME') or '').strip()
            url = (f"https://www.bseindia.com/xml-data/corpfiling/{'AttachHis' if d.get('PDFFLAG') == 1 else 'AttachLive'}/{att}" if att else None)
            out.append({'date': dt + '+05:30' if dt else None, 'type': d.get('CATEGORYNAME'), 'type_en': d.get('CATEGORYNAME'), 'subtype': d.get('SUBCATNAME'),
                        'title': (d.get('NEWSSUB') or '').strip(), 'headline': (d.get('HEADLINE') or '').strip(), 'url': url, 'source': SRC_BSE,
                        'news_id': d.get('NEWSID'), 'bse_code': d.get('SCRIP_CD'), 'issuer': d.get('SLONGNAME')})
        if not tab or len(out) >= total:
            break
        page += 1
    out.sort(key=lambda e: e['date'] or '', reverse=True)
    return out


def resolve(q):
    q = q.strip().upper()
    if re.fullmatch(r'\d{6}', q):
        return None, q
    if len(q) == 12 and q.startswith('IN'):
        m = _maps_load()
        return m['nse'].get(q), m['bse'].get(q)
    return q, None


def fetch(isin_or_issuer, since, source='auto'):
    """since: 'YYYY-MM-DD' or date. Returns newest first."""
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    until = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).date()
    sym, code = resolve(isin_or_issuer)
    if source in ('auto', 'nse') and sym:
        return nse_events(sym, since, until)
    if source in ('auto', 'bse') and code:
        return bse_events(code, since, until)
    return []


if __name__ == '__main__':
    tests = sys.argv[1:] or ['INE002A01018', 'INE040A01034', 'INE467B01029']   # Reliance Industries, HDFC Bank, TCS
    today = datetime.datetime.now(datetime.timezone.utc).date(); since = today - datetime.timedelta(days=365)
    res = {'source_url': NSE_PAGE, 'endpoint': NSE_API + '?index=equities&symbol=<SYMBOL>&from_date&to_date (cookie from GET ' + NSE_HOME + ')',
           'fallback_endpoint': BSE_API + ' (strScrip=<BSE code>)', 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'since': since.isoformat(), 'key_required': False, 'issuers': {}}
    for q in tests:
        sym, code = resolve(q)
        ev = fetch(q, since)
        bse = bse_events(code, since, today) if code else []
        res['issuers'][q] = {'nse_symbol': sym, 'bse_code': code, 'count': len(ev), 'source_used': ev[0]['source'] if ev else None,
                             'by_type': {k: sum(1 for e in ev if e['type'] == k) for k in sorted({e['type'] or '' for e in ev})},
                             'bse_crosscheck_count': len(bse), 'events': ev}
        print(q, sym, code, 'nse', len(ev), 'bse', len(bse), flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
