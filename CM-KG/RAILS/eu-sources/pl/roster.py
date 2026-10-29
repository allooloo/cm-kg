"""Poland Width 0 roster - listed equity issuers of GPW Warsaw: Main Market (XWAR, EU regulated market) and NewConnect (XNCO, MTF).

Source of record: ESMA FIRDS full equity files (FULINS_E_<date>_NNofMM.zip, weekly, firds.esma.europa.eu), found through the
registers.esma.europa.eu Solr file index when that answers, otherwise by probing the weekly file names (index host 502 on 2026-10-24).
Scope: CFI ES* (shares), no termination date, MIC XWAR or XNCO; one row per ISIN (XWAR wins). Foreign dual listings on XWAR are kept.
Cross-check: GPW's own company list (see crosscheck()).

fetch() -> {"source_url", "read_by", "read_at", "count", "rows": [{"isin","name","mic","lei","ticker","cfi"}]}
Usage: python roster.py   writes samples/roster-<date>.json
"""
import os, sys, io, re, json, time, zipfile, datetime
import xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get('FIRDS_CACHE', os.path.join(HERE, 'cache'))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
MARKET = 'pl'
MICS = {'XWAR': 'GPW Main Market', 'XNCO': 'NewConnect (GPW MTF)'}
PRIMARY_MIC_ORDER = ['XWAR', 'XNCO']
HOME_PREFIX = 'PL'


def keep(rec, all_lines=False):
    return True


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
            'scope': 'XWAR + XNCO', 'rows': rows}


GPW_LIST = 'https://www.gpw.pl/list-of-companies'
GPW_AJAX = 'https://www.gpw.pl/ajaxindex.php'


def gpw_company_list():
    """GPW's own company list (gpw.pl list-of-companies, action GPWCompanySearch), Main Market + NewConnect.
    The page form is read and re-posted with its own default (all-checked) filters, Catalyst left out; paged by offset.
    Prices/changes in the response are discarded. Note: gpw.pl resets curl/schannel connections; Python requests is answered."""
    s = requests.Session(); s.headers.update({**UA, 'Accept-Language': 'en-US,en;q=0.9', 'X-Requested-With': 'XMLHttpRequest', 'Referer': GPW_LIST})
    def call(fn, *a, **kw):
        for i in range(4):
            try:
                return fn(*a, timeout=120, **kw)
            except requests.RequestException:
                time.sleep(5 * (i + 1))
        raise RuntimeError('gpw.pl did not answer')
    page = call(s.get, GPW_LIST).text
    i = page.find("id='search-form'"); form = page[i:page.find('</form>', i)]
    base = []
    for m in re.finditer(r'<input[^>]*>', form):
        tag = m.group(0); n = re.search(r'name=["\']([^"\']+)["\']', tag)
        if not n or n.group(1) in ('source[CAT]', 'offset', 'limit'):
            continue
        ty = (re.search(r'type=["\']([^"\']+)', tag) or [None, 'text'])[1]; v = re.search(r'value=["\']([^"\']*)', tag); v = v.group(1) if v else ''
        if ty == 'checkbox':
            if 'checked' in tag:
                base.append((n.group(1), v or 'on'))
        else:
            base.append((n.group(1), v))
    rows, off, lim = {}, 0, 200
    while True:
        t = call(s.post, GPW_AJAX, data=base + [('offset', str(off)), ('limit', str(lim))]).text
        got = re.findall(r'company-factsheet\?isin=([A-Z0-9]{12})">\s*<strong class="name">\s*(.*?)\s*<span class="grey">\(([^)]*)\)</span>.*?<small class="grey">([^<|]*)', t, re.S)
        for isin, name, tick, mkt in got:
            rows[isin] = {'isin': isin, 'name': re.sub(r'\s+', ' ', name).strip(), 'ticker': tick.strip(), 'market': mkt.strip()}
        if len(got) < lim:
            break
        off += lim
    return list(rows.values())


def crosscheck(result):
    from collections import Counter
    ex = gpw_company_list()
    exi = {r['isin']: r for r in ex}
    ros = {r['isin'] for r in result['rows']}
    for r in result['rows']:
        if r['isin'] in exi:
            r['ticker'] = exi[r['isin']]['ticker']
    return {'source_url': GPW_LIST + ' (POST ' + GPW_AJAX + ' action=GPWCompanySearch, Main Market + NewConnect)',
            'exchange_count': len(ex), 'exchange_by_market': dict(Counter(r['market'] for r in ex)),
            'matched_isins': len(ros & set(exi)), 'in_firds_not_on_gpw_list': len(ros - set(exi)), 'on_gpw_list_not_in_firds': len(set(exi) - ros),
            'missing_sample': {'in_firds_not_on_gpw_list': sorted(ros - set(exi))[:40],
                               'on_gpw_list_not_in_firds': [exi[i] for i in sorted(set(exi) - ros)][:40]}}


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
