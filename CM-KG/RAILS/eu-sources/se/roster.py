"""SE roster (Width 0) - listed equity issuers on Nasdaq Stockholm (XSTO) and Nasdaq First North Growth Market Sweden (SSME).

Primary source  : ESMA FIRDS full equity files (FULINS_E_*), filtered to trading-venue MICs XSTO + SSME and CFI ES* (shares).
                  Index: https://registers.esma.europa.eu/solr/esma_registers_firds_files/select (falls back to probing the
                  weekly file names on firds.esma.europa.eu when the index answers 5xx).
Cross-check     : Nasdaq Nordic share screener (the exchange's own list), which also gives the ticker.
                  https://api.nasdaq.com/api/nordic/screener/shares?category=MAIN_MARKET|FIRST_NORTH&market=STO
No key. No prices are kept (the screener's price fields are dropped on read).
Run: python roster.py            -> writes samples/roster-<date>.json
     FIRDS_CACHE=<dir> to reuse downloaded FIRDS zips.
"""
import datetime as dt, io, json, os, sys, time, zipfile
import xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
READ_BY = 'allooloo-cm-kg/eu-sources/se roster.py'
MICS = {'XSTO': 'Nasdaq Stockholm', 'SSME': 'Nasdaq First North Growth Market Sweden'}
EXCHANGE = [('MAIN_MARKET', 'XSTO'), ('FIRST_NORTH', 'SSME')]
SCREENER = 'https://api.nasdaq.com/api/nordic/screener/shares'
FIRDS_INDEX = 'https://registers.esma.europa.eu/solr/esma_registers_firds_files/select'
FIRDS_FILES = 'https://firds.esma.europa.eu/firds/'


def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=300, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    return None


def firds_equity_files():
    """Latest FULINS_E file set: [(publication_date, file_name, url)]."""
    r = get(FIRDS_INDEX, params={'q': '*', 'fq': 'file_type:FULINS', 'wt': 'json', 'rows': 60, 'sort': 'publication_date desc'})
    try:
        docs = [d for d in r.json()['response']['docs'] if '_E_' in d['file_name']]
        latest = docs[0]['publication_date'][:10]
        return [(latest, d['file_name'], d['download_link']) for d in docs if d['publication_date'][:10] == latest]
    except Exception:
        pass
    # index down: FULINS are published weekly; probe the last five weeks of file names
    today = dt.date.today()
    for back in range(0, 36):
        d = (today - dt.timedelta(days=back)).strftime('%Y%m%d')
        for n in range(1, 5):
            first = 'FULINS_E_%s_01of%02d.zip' % (d, n)
            h = requests.head(FIRDS_FILES + first, headers=UA, timeout=60)
            if h.status_code == 200:
                names = ['FULINS_E_%s_%02dof%02d.zip' % (d, k, n) for k in range(1, n + 1)]
                return [(d[:4] + '-' + d[4:6] + '-' + d[6:], x, FIRDS_FILES + x) for x in names]
    raise RuntimeError('no FIRDS FULINS_E file found')


def firds_rows(mics):
    files = firds_equity_files()
    cache = os.environ.get('FIRDS_CACHE') or os.path.join(HERE, 'cache')
    os.makedirs(cache, exist_ok=True)
    today = dt.date.today().isoformat(); rows = {}
    for pub, name, url in files:
        path = os.path.join(cache, name)
        if not os.path.exists(path):
            r = get(url)
            if r is None or r.status_code != 200:
                raise RuntimeError('FIRDS download failed ' + url)
            open(path, 'wb').write(r.content)
        z = zipfile.ZipFile(path)
        for _, el in ET.iterparse(z.open(z.namelist()[0]), events=('end',)):
            if not el.tag.endswith('}RefData'):
                continue
            ns = el.tag.split('}')[0] + '}'
            g = el.find(ns + 'FinInstrmGnlAttrbts'); tv = el.find(ns + 'TradgVnRltdAttrbts')
            mic = tv.findtext(ns + 'Id') if tv is not None else ''
            cfi = g.findtext(ns + 'ClssfctnTp') or ''
            term = (tv.findtext(ns + 'TermntnDt') or '')[:10] if tv is not None else ''
            if mic in mics and cfi.startswith('ES') and (not term or term >= today):
                isin = g.findtext(ns + 'Id')
                rows[(isin, mic)] = {'isin': isin, 'name': g.findtext(ns + 'FullNm'), 'mic': mic, 'lei': el.findtext(ns + 'Issr'),
                                     'ticker': None, 'cfi': cfi, 'first_trade': (tv.findtext(ns + 'FrstTradDt') or '')[:10]}
            el.clear()
    return files, list(rows.values())


def exchange_list():
    out = {}
    for cat, mic in EXCHANGE:
        r = get(SCREENER, params={'category': cat, 'tableonly': 'false', 'market': 'STO'})
        for x in ((r.json().get('data') or {}).get('instrumentListing') or {}).get('rows', []) if r is not None else []:
            if x.get('isin'):
                out[(x['isin'], mic)] = {'ticker': x.get('symbol'), 'name': x.get('fullName')}
    return out


def fetch():
    files, rows = firds_rows(set(MICS))
    ex = exchange_list()
    seen = set()
    for r in rows:
        e = ex.get((r['isin'], r['mic']))
        r['on_exchange_list'] = e is not None
        if e:
            r['ticker'] = e['ticker']; seen.add((r['isin'], r['mic']))
    rows.sort(key=lambda r: (r['mic'], r['name'] or ''))
    return {'source_url': files[0][2].rsplit('/', 1)[0] + '/ (ESMA FIRDS FULINS_E ' + files[0][0] + ': ' + ', '.join(f[1] for f in files) + ')',
            'read_by': READ_BY, 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'count': len(rows), 'issuers': len({r['lei'] or r['isin'] for r in rows}),
            'by_mic': {m: sum(1 for r in rows if r['mic'] == m) for m in MICS},
            'cross_check': {'source_url': SCREENER + '?category=MAIN_MARKET|FIRST_NORTH&market=STO', 'exchange_lines': len(ex),
                            'matched': len(seen), 'firds_only': len(rows) - len(seen),
                            'exchange_only': sorted('%s %s %s' % (k[0], k[1], v['name']) for k, v in ex.items() if k not in seen)},
            'rows': rows}


if __name__ == '__main__':
    out = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', 'roster-%s.json' % dt.date.today().isoformat())
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('roster', out['count'], 'lines', out['issuers'], 'issuers', out['by_mic'], 'cross-check', {k: v for k, v in out['cross_check'].items() if k != 'exchange_only'}, '->', p)
