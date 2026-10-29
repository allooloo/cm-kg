"""Austria Width 0 roster - listed equity issuers of Wiener Boerse (operating MIC XWBO).

Source of record: ESMA FIRDS full equity files (FULINS_E_<date>_NNofMM.zip, weekly, published on firds.esma.europa.eu),
found through the registers.esma.europa.eu Solr file index when that answers, otherwise by probing the weekly file names
(the index host returned 502 on 2026-10-24). FIRDS reports Wiener Boerse by segment MIC, not by XWBO:
  WBAH = Amtlicher Handel (Official Market, EU regulated market: prime market + standard market)
  WBDM = Vienna MTF (direct market plus / direct market / global market; global market = foreign shares traded, not listed)
Scope: CFI ES* (shares), no termination date. Default = WBAH all + WBDM with an AT ISIN (the global market, about 1,700
foreign lines, is left out; pass --all to keep it). One row per ISIN (WBAH wins over WBDM).
Cross-check: Wiener Boerse's own listed-companies page (see crosscheck()).

fetch() -> {"source_url", "read_by", "read_at", "count", "rows": [{"isin","name","mic","lei","ticker","cfi"}]}
Tickers: Wiener Boerse instrument pages ("Symbol").
Usage: python roster.py [--all]   writes samples/roster-<date>.json
"""
import os, sys, io, re, json, time, zipfile, datetime
import xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get('FIRDS_CACHE', os.path.join(HERE, 'cache'))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
MARKET = 'at'
MICS = {'WBAH': 'Wiener Boerse Official Market (Amtlicher Handel)', 'WBDM': 'Wiener Boerse Vienna MTF'}
PRIMARY_MIC_ORDER = ['WBAH', 'WBDM']
HOME_PREFIX = 'AT'


def keep(rec, all_lines=False):
    """Market-specific scope rule applied to one FIRDS share record."""
    if rec['mic'] == 'WBAH':
        return True
    return all_lines or rec['isin'].startswith(HOME_PREFIX)


# ---------------------------------------------------------------- FIRDS (shared logic, same in at/pl/pt/lu)
def _get(url, tries=3, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=600, **kw)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    return None


def firds_equity_files():
    """Latest FULINS_E file set -> (publication_date 'YYYY-MM-DD', [download urls], how_found)."""
    r = _get('https://registers.esma.europa.eu/solr/esma_registers_firds_files/select',
             params={'q': '*', 'fq': 'file_type:FULINS', 'wt': 'json', 'start': 0, 'rows': 60, 'sort': 'publication_date desc'}, tries=2)
    if r is not None and r.status_code == 200 and r.headers.get('content-type', '').startswith(('application/json', 'text/plain')):
        docs = r.json()['response']['docs']; latest = docs[0]['publication_date']
        links = [d['download_link'] for d in docs if d['publication_date'] == latest and '_E_' in d['file_name']]
        if links:
            return latest[:10], links, 'registers.esma.europa.eu Solr file index (esma_registers_firds_files)'
    # Fallback: the index did not answer; probe the weekly file names on firds.esma.europa.eu (FULINS is published on Saturdays).
    today = datetime.date.today()
    for back in range(0, 42):
        d = today - datetime.timedelta(days=back)
        if d.weekday() != 5:
            continue
        ds = d.strftime('%Y%m%d')
        for parts in range(1, 6):
            first = f'https://firds.esma.europa.eu/firds/FULINS_E_{ds}_01of{parts:02d}.zip'
            try:
                h = requests.get(first, headers={**UA, 'Range': 'bytes=0-10'}, timeout=60)
            except requests.RequestException:
                h = None
            if h is not None and h.status_code in (200, 206):
                return d.isoformat(), [f'https://firds.esma.europa.eu/firds/FULINS_E_{ds}_{i:02d}of{parts:02d}.zip' for i in range(1, parts + 1)], \
                    'firds.esma.europa.eu weekly file name probe (Solr index unavailable)'
    raise RuntimeError('No FIRDS FULINS_E file set found (index down and no file in the last 6 weeks)')


def firds_share_records(mics):
    pub, links, how = firds_equity_files()
    os.makedirs(CACHE, exist_ok=True)
    out, scanned = [], 0
    for url in links:
        fn = os.path.join(CACHE, url.rsplit('/', 1)[-1])
        if not os.path.exists(fn):
            r = _get(url)
            if r is None or r.status_code != 200:
                raise RuntimeError(f'FIRDS download failed: {url} ({None if r is None else r.status_code})')
            open(fn, 'wb').write(r.content)
        z = zipfile.ZipFile(fn)
        for _, el in ET.iterparse(z.open(z.namelist()[0]), events=('end',)):
            if not el.tag.endswith('}RefData'):
                continue
            scanned += 1
            ns = el.tag.split('}')[0] + '}'
            g = el.find(ns + 'FinInstrmGnlAttrbts'); tv = el.find(ns + 'TradgVnRltdAttrbts')
            mic = tv.findtext(ns + 'Id') if tv is not None else ''
            if mic in mics:
                cfi = g.findtext(ns + 'ClssfctnTp') or ''
                if cfi.startswith('ES') and not (tv.findtext(ns + 'TermntnDt') or ''):
                    out.append({'isin': g.findtext(ns + 'Id'), 'name': (g.findtext(ns + 'FullNm') or '').strip(),
                                'short_name': (g.findtext(ns + 'ShrtNm') or '').strip(), 'cfi': cfi, 'mic': mic,
                                'lei': el.findtext(ns + 'Issr') or '', 'currency': g.findtext(ns + 'NtnlCcy') or '',
                                'first_trade': (tv.findtext(ns + 'FrstTradDt') or '')[:10]})
            el.clear()
    return pub, links, how, scanned, out


def fetch(all_lines=False):
    pub, links, how, scanned, recs = firds_share_records(set(MICS))
    best = {}
    for r in recs:
        if not keep(r, all_lines):
            continue
        cur = best.get(r['isin'])
        if cur is None or PRIMARY_MIC_ORDER.index(r['mic']) < PRIMARY_MIC_ORDER.index(cur['mic']):
            best[r['isin']] = r
    rows = [{'isin': r['isin'], 'name': r['name'], 'mic': r['mic'], 'lei': r['lei'], 'ticker': '', 'cfi': r['cfi']} for r in sorted(best.values(), key=lambda x: (x['mic'], x['name']))]
    by_mic = {m: sum(1 for r in rows if r['mic'] == m) for m in MICS}
    return {'source_url': links[0].rsplit('/', 1)[0] + '/', 'files': links, 'read_by': f'ESMA FIRDS full equity files {pub} ({how}); CFI ES*, MIC in {sorted(MICS)}, no termination date',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'firds_publication_date': pub,
            'records_scanned': scanned, 'count': len(rows), 'count_by_mic': by_mic, 'distinct_lei': len({r['lei'] for r in rows if r['lei']}),
            'scope': 'WBAH all + WBDM AT-ISIN' if not all_lines else 'WBAH + WBDM all lines', 'rows': rows}


WB = 'https://www.wienerborse.at'
WB_LIST = WB + '/en/listing/shares/companies-list/'
WB_ROW = re.compile(r'<tr data-key="\d+">\s*<td>([A-Z]{2}[A-Z0-9]{9}[0-9])</td>.*?data-pjax="0">(.*?)</a>.*?</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>', re.S)
WB_SYM = re.compile(r'Symbol:\s*(?:<[^>]+>\s*)*([A-Z0-9]{2,8})\b')


def wb_companies():
    """Wiener Boerse's own listed-companies page (ISIN, issuer, country, market, segment, security type)."""
    r = _get(WB_LIST); r.raise_for_status()
    return [{'isin': i, 'name': re.sub(r'<[^>]+>', '', n).strip(), 'country': c, 'market': m, 'segment': g, 'type': t}
            for i, n, c, m, g, t in WB_ROW.findall(r.text)]


def wb_symbol(s, isin):
    """Ticker ('Symbol') from the instrument page Wiener Boerse serves for /en/?ISIN=<isin>."""
    try:
        r = s.get(f'{WB}/en/?ISIN={isin}', timeout=60)
        m = WB_SYM.search(r.text)
        return (m.group(1) if m else ''), r.url
    except requests.RequestException:
        return '', ''


def crosscheck(result):
    """Compare with Wiener Boerse's companies list and fill tickers from each instrument page (one GET per row)."""
    try:
        wb = wb_companies()
    except Exception as e:  # noqa: BLE001 - keep the roster
        return {'source': WB_LIST, 'error': f'{type(e).__name__}: {e}'}
    wbi = {x['isin']: x for x in wb}
    s = requests.Session(); s.headers.update(UA)
    for r in result['rows']:
        r['ticker'], _ = wb_symbol(s, r['isin'])
        time.sleep(0.2)
    firds = {r['isin'] for r in result['rows']}
    seg = {}
    for x in wb:
        k = f"{x['market']} / {x['segment']}"; seg[k] = seg.get(k, 0) + 1
    return {'source': WB_LIST, 'ticker_source': WB + '/en/?ISIN=<isin> (instrument page, "Symbol")', 'exchange_count': len(wb),
            'exchange_by_market_segment': dict(sorted(seg.items())), 'matched': len(firds & set(wbi)),
            'firds_not_on_wb_list': sorted(firds - set(wbi)),
            'wb_at_isin_not_in_rows': sorted(i for i in wbi if i.startswith('AT') and i not in firds),
            'tickers_filled': sum(1 for r in result['rows'] if r['ticker'])}


if __name__ == '__main__':
    res = fetch(all_lines='--all' in sys.argv)
    cc = crosscheck(res)
    if cc is not None:
        res['crosscheck'] = cc
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], res['count_by_mic'], 'LEIs', res['distinct_lei'], 'scanned', res['records_scanned'], '->', out)
    if cc is not None:
        print('crosscheck', {k: v for k, v in cc.items() if k != 'missing_sample'})
