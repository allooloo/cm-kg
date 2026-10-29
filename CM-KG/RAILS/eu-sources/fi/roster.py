"""Finland roster (Width 0): listed equity issuers on Nasdaq Helsinki (XHEL) and First North Finland.
First North Finland shares are reported to FIRDS under the SME-growth-market MIC FSME (the FNFI MIC carries only ETNs / trackers).

Source of record: ESMA FIRDS full equity files (FULINS_E_*), filtered to the two MICs and CFI ES* (shares), plus EM* (equity certificates) and ED* (depositary receipts) -- see CFI_PREFIXES. FIRDS gives ISIN, full name,
MIC and issuer LEI. Cross-check and ticker: Nasdaq's own share list (api.nasdaq.com/api/nordic/screener/shares, market=HEL, MAIN_MARKET / FIRST_NORTH).
Public, no key. No prices are kept (the screener carries price columns; they are dropped).

fetch() -> {"source_url", "read_by", "read_at", "count", "rows": [{"isin", "name", "mic", "lei", "ticker"}], ...}
Run: python roster.py   (writes samples/roster-<date>.json). FIRDS zips are cached in $FIRDS_CACHE or ./cache.
"""
import datetime as dt, io, json, os, re, sys, time, zipfile
import xml.etree.ElementTree as ET
import requests

MARKET = 'fi'
MICS = {'XHEL': 'Nasdaq Helsinki (main market)', 'FSME': 'Nasdaq First North Growth Market Finland'}
# Nasdaq screener category per MIC (cross-check list)
NASDAQ_CATEGORY = {'XHEL': 'MAIN_MARKET', 'FSME': 'FIRST_NORTH'}
EXCHANGE_LIST = 'nasdaq'   # cross-check list
# ES = shares (the brief); EM = equity certificates (Finnish savings-bank / cooperative capital certificates); ED = depositary receipts. by_cfi gives the ES-only figure.
CFI_PREFIXES = ('ES', 'EM', 'ED')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
HERE = os.path.dirname(os.path.abspath(__file__))
FIRDS_INDEX = 'https://registers.esma.europa.eu/solr/esma_registers_firds_files/select'
FIRDS_FILES = 'https://firds.esma.europa.eu/firds/'


def _get(url, tries=4, method='GET', **kw):
    for i in range(tries):
        try:
            r = requests.request(method, url, headers={**UA, **kw.pop('headers', {})}, timeout=300, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(4 * (i + 1))
    return None


def firds_equity_files():
    """Latest FULINS_E file set. The FIRDS Solr index first; when it is down (502 seen 2026-10-24), probe the weekly file names directly."""
    r = _get(FIRDS_INDEX, tries=2, params={'q': '*', 'fq': 'file_type:FULINS', 'wt': 'json', 'rows': 60, 'sort': 'publication_date desc'})
    try:
        docs = r.json()['response']['docs']
        latest = docs[0]['publication_date'][:10]
        files = [d['download_link'] for d in docs if d['publication_date'][:10] == latest and '_E_' in d['file_name']]
        if files:
            return latest, files, FIRDS_INDEX
    except Exception:
        pass
    day = dt.datetime.now(dt.timezone.utc).date()
    for back in range(0, 35):
        d = day - dt.timedelta(days=back)
        tag = d.strftime('%Y%m%d')
        for total in range(1, 6):
            h = _get(f'{FIRDS_FILES}FULINS_E_{tag}_01of{total:02d}.zip', tries=1, method='HEAD')
            if h is not None and h.status_code == 200:
                return d.isoformat(), [f'{FIRDS_FILES}FULINS_E_{tag}_{k:02d}of{total:02d}.zip' for k in range(1, total + 1)], FIRDS_FILES + ' (index down; file names probed)'
    raise RuntimeError('no FIRDS FULINS_E file found in the last 35 days')


def firds_rows(mics):
    pub, links, how = firds_equity_files()
    cache = os.environ.get('FIRDS_CACHE') or os.path.join(HERE, 'cache')
    os.makedirs(cache, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    rows = []
    for link in links:
        path = os.path.join(cache, link.rsplit('/', 1)[1])
        if not os.path.exists(path):
            r = _get(link); r.raise_for_status()
            open(path + '.part', 'wb').write(r.content); os.replace(path + '.part', path)
        z = zipfile.ZipFile(path)
        for _, el in ET.iterparse(z.open(z.namelist()[0]), events=('end',)):
            if not el.tag.endswith('}RefData'):
                continue
            ns = el.tag.split('}')[0] + '}'
            g = el.find(ns + 'FinInstrmGnlAttrbts'); tv = el.find(ns + 'TradgVnRltdAttrbts')
            mic = tv.findtext(ns + 'Id') if tv is not None else ''
            cfi = g.findtext(ns + 'ClssfctnTp') or ''
            term = (tv.findtext(ns + 'TermntnDt') or '')[:10] if tv is not None else ''
            if mic in mics and cfi[:2] in CFI_PREFIXES and not (term and term < today):
                rows.append({'isin': g.findtext(ns + 'Id'), 'name': g.findtext(ns + 'FullNm'), 'mic': mic, 'lei': el.findtext(ns + 'Issr'),
                             'cfi': cfi, 'currency': g.findtext(ns + 'NtnlCcy'), 'admission': (tv.findtext(ns + 'AdmssnApprvlDtByIssr') or '')[:10],
                             'first_trade': (tv.findtext(ns + 'FrstTradDt') or '')[:10]})
            el.clear()
    return pub, links, how, rows


def euronext_list(mic):
    """Euronext's own list for one MIC: {isin: (symbol, name)}. Last price / change columns are dropped."""
    out = {}
    start = 0
    while True:
        r = _get(f'https://live.euronext.com/en/pd_es/data/stocks?mics={mic}&display_datapoints=dp_stocks&display_filters=df_stocks', method='POST',
                 headers={'X-Requested-With': 'XMLHttpRequest'}, data={'draw': 1, 'start': start, 'length': 500, 'iDisplayLength': 500, 'iDisplayStart': start})
        if r is None or r.status_code != 200:
            return None
        j = r.json(); data = j.get('aaData') or []
        for row in data:
            if len(row) < 4:
                continue
            name = re.sub(r'<[^>]+>', '', row[1]).strip()
            out[row[2]] = (row[3], name)
        start += 500
        if start >= int(j.get('iTotalRecords') or 0) or not data:
            return out


def nasdaq_list(mic):
    """Nasdaq Nordic screener for Helsinki: {isin: (symbol, name)}; price fields dropped."""
    r = _get('https://api.nasdaq.com/api/nordic/screener/shares', params={'category': NASDAQ_CATEGORY[mic], 'tableonly': 'false', 'market': 'HEL'}, headers={'Accept': 'application/json'})
    if r is None or r.status_code != 200:
        return None
    return {x['isin']: (x['symbol'], x['fullName']) for x in r.json()['data']['instrumentListing']['rows']}


def fetch():
    pub, links, how, rows = firds_rows(set(MICS))
    seen, uniq = set(), []
    for r in rows:
        k = (r['isin'], r['mic'])
        if k not in seen:
            seen.add(k); uniq.append(r)
    cross = {}
    for mic in MICS:
        cross[mic] = nasdaq_list(mic)
    for r in uniq:
        hit = (cross.get(r['mic']) or {}).get(r['isin'])
        r['ticker'] = hit[0] if hit else None
        r['on_exchange_list'] = bool(hit)
    exch_only = []
    for mic, lst in cross.items():
        if lst is None:
            continue
        firds_isins = {r['isin'] for r in uniq if r['mic'] == mic}
        exch_only += [{'isin': i, 'ticker': s, 'name': n, 'mic': mic} for i, (s, n) in lst.items() if i not in firds_isins]
    by_mic = {m: sum(1 for r in uniq if r['mic'] == m) for m in MICS}
    return {
        'source_url': links[0].rsplit('/', 1)[0] + '/ (ESMA FIRDS FULINS_E ' + pub + ': ' + ', '.join(l.rsplit('/', 1)[1] for l in links) + ')',
        'read_by': 'eu-sources/' + MARKET + '/roster.py (FIRDS ' + how + ')',
        'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'count': len(uniq),
        'issuers': len({r['lei'] or r['name'] for r in uniq}),
        'by_mic': by_mic,
        'by_cfi': {c: sum(1 for r in uniq if r['cfi'].startswith(c)) for c in CFI_PREFIXES},
        'mics': MICS,
        'cross_check': {'source_url': 'https://api.nasdaq.com/api/nordic/screener/shares?market=HEL&category=<MAIN_MARKET|FIRST_NORTH>',
                        'exchange_counts': {m: (len(v) if v is not None else None) for m, v in cross.items()},
                        'firds_on_exchange_list': sum(1 for r in uniq if r['on_exchange_list']),
                        'exchange_only': exch_only},
        'rows': uniq,
    }


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', 'roster-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', out['count'], 'by_cfi', out['by_cfi'], 'issuers', out['issuers'], 'by_mic', out['by_mic'], 'cross', out['cross_check']['exchange_counts'],
          'firds_on_list', out['cross_check']['firds_on_exchange_list'], 'exchange_only', len(out['cross_check']['exchange_only']), '->', p)
