"""Luxembourg Width 0 roster - equity lines of the Luxembourg Stock Exchange: regulated market (XLUX, Bourse de Luxembourg)
and Euro MTF (EMTF).

Source of record: ESMA FIRDS full equity files (FULINS_E_<date>_NNofMM.zip, weekly, firds.esma.europa.eu), found through the
registers.esma.europa.eu Solr file index when that answers, otherwise by probing the weekly file names (index host 502 on 2026-10-24).
Scope: CFI ES* (shares; LuxSE equity is mostly foreign shares and depositary-receipt-like lines, which carry CFI ED* and are
therefore out), no termination date; one row per ISIN (XLUX wins). Cross-check: LuxSE's own data (see crosscheck()).

fetch() -> {"source_url", "read_by", "read_at", "count", "rows": [{"isin","name","mic","lei","ticker","cfi"}]}
Usage: python roster.py [--with-dr]   writes samples/roster-<date>.json
"""
import os, sys, io, re, json, time, zipfile, datetime
import xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get('FIRDS_CACHE', os.path.join(HERE, 'cache'))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
MARKET = 'lu'
MICS = {'XLUX': 'Luxembourg Stock Exchange regulated market', 'EMTF': 'LuxSE Euro MTF'}
PRIMARY_MIC_ORDER = ['XLUX', 'EMTF']
HOME_PREFIX = 'LU'


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


def firds_share_records(mics, prefixes=('ES',)):
    pub, links, how = firds_equity_files()
    os.makedirs(CACHE, exist_ok=True)
    out, scanned = [], 0
    global CFI_BREAKDOWN
    CFI_BREAKDOWN = {}
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
                live = not (tv.findtext(ns + 'TermntnDt') or '')
                key = f"{mic} {cfi[:2]} {'active' if live else 'terminated'}"
                CFI_BREAKDOWN[key] = CFI_BREAKDOWN.get(key, 0) + 1
                if cfi.startswith(tuple(prefixes)) and not (tv.findtext(ns + 'TermntnDt') or ''):
                    out.append({'isin': g.findtext(ns + 'Id'), 'name': (g.findtext(ns + 'FullNm') or '').strip(),
                                'short_name': (g.findtext(ns + 'ShrtNm') or '').strip(), 'cfi': cfi, 'mic': mic,
                                'lei': el.findtext(ns + 'Issr') or '', 'currency': g.findtext(ns + 'NtnlCcy') or '',
                                'first_trade': (tv.findtext(ns + 'FrstTradDt') or '')[:10]})
            el.clear()
    return pub, links, how, scanned, out


CFI_BREAKDOWN = {}


def fetch(all_lines=False, with_dr=False):
    prefixes = ('ES', 'ED') if with_dr else ('ES',)
    pub, links, how, scanned, recs = firds_share_records(set(MICS), prefixes)
    best = {}
    for r in recs:
        if not keep(r, all_lines):
            continue
        cur = best.get(r['isin'])
        if cur is None or PRIMARY_MIC_ORDER.index(r['mic']) < PRIMARY_MIC_ORDER.index(cur['mic']):
            best[r['isin']] = r
    rows = [{'isin': r['isin'], 'name': r['name'], 'mic': r['mic'], 'lei': r['lei'], 'ticker': '', 'cfi': r['cfi']} for r in sorted(best.values(), key=lambda x: (x['mic'], x['name']))]
    by_mic = {m: sum(1 for r in rows if r['mic'] == m) for m in MICS}
    return {'source_url': links[0].rsplit('/', 1)[0] + '/', 'files': links, 'read_by': f'ESMA FIRDS full equity files {pub} ({how}); CFI {'/'.join(p + '*' for p in prefixes)}, MIC in {sorted(MICS)}, no termination date',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'firds_publication_date': pub,
            'records_scanned': scanned, 'count': len(rows), 'count_by_mic': by_mic, 'distinct_lei': len({r['lei'] for r in rows if r['lei']}),
            'scope': 'XLUX + EMTF' + (' incl. depositary receipts (ED*)' if with_dr else ''),
            'firds_cfi_breakdown': dict(sorted(CFI_BREAKDOWN.items())), 'rows': rows}


LUXSE_GQL = 'https://graphqlaz.luxse.com/v1/graphql'
LUXSE_HDR = {**UA, 'Content-Type': 'application/json', 'Origin': 'https://www.luxse.com', 'Referer': 'https://www.luxse.com/'}
LUXSE_EQ_Q = """query($page: Int){luxseSecuritiesSearch(searchTerm:"",size:200,page:$page,sort:"",excludeRetr:true,
 statuses:["ADMI","NEGO","COTE","RETR"],statusesOperator:"OR",excludeStatuses:["PUBL"],excludeMarketRules:["PUBL"],category:EQUITY)
 {totalHits securities{id isin instrumentName instrumentType instrumentSubtype status marketRule tradingCode}}}"""


def luxse_equities():
    """LuxSE's own equity list: the luxse.com search 'Equities' tab (public GraphQL behind www.luxse.com, no key)."""
    out, page = [], 0
    while True:
        r = requests.post(LUXSE_GQL, headers=LUXSE_HDR, json={'query': LUXSE_EQ_Q, 'variables': {'page': page}}, timeout=90)
        r.raise_for_status()
        d = r.json()['data']['luxseSecuritiesSearch']
        out += d['securities']
        if not d['securities'] or len(out) >= d['totalHits']:
            return d['totalHits'], out
        page += 1


def crosscheck(result):
    """Compare the FIRDS rows with LuxSE's own equity list (all subtypes, both markets)."""
    try:
        total, lx = luxse_equities()
    except Exception as e:  # noqa: BLE001 - record the failure, keep the roster
        return {'source': LUXSE_GQL, 'error': f'{type(e).__name__}: {e}'}
    lx_isins = {s['isin'] for s in lx}
    codes = {s['isin']: (s.get('tradingCode') or '').strip() for s in lx if s.get('tradingCode')}
    for r in result['rows']:  # ticker = LuxSE trading code, from the exchange's own list
        r['ticker'] = codes.get(r['isin'], '')
    firds = {r['isin'] for r in result['rows']}
    sub = {}
    for s in lx:
        k = f"{s.get('marketRule')} {s.get('instrumentSubtype')}"
        sub[k] = sub.get(k, 0) + 1
    return {'source': 'https://www.luxse.com/search (Equities; GraphQL luxseSecuritiesSearch category EQUITY, statuses ADMI/NEGO/COTE)',
            'exchange_count': total, 'exchange_by_market_and_subtype': dict(sorted(sub.items())),
            'matched': len(firds & lx_isins), 'firds_not_on_luxse': sorted(firds - lx_isins),
            'luxse_not_in_firds_rows': len(lx_isins - firds),
            'missing_sample': [{'isin': s['isin'], 'name': s['instrumentName'], 'subtype': s.get('instrumentSubtype'), 'market': s.get('marketRule')}
                               for s in lx if s['isin'] not in firds][:40]}


if __name__ == '__main__':
    res = fetch(all_lines='--all' in sys.argv, with_dr='--with-dr' in sys.argv)
    cc = crosscheck(res)
    if cc is not None:
        res['crosscheck'] = cc
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], res['count_by_mic'], 'LEIs', res['distinct_lei'], 'scanned', res['records_scanned'], '->', out)
    if cc is not None:
        print('crosscheck', {k: v for k, v in cc.items() if k != 'missing_sample'})
