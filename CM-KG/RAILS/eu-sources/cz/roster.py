"""CZ Width 0 roster: listed equity issuers of the Prague Stock Exchange (Burza cenných papírů Praha, PSE).

Primary  : ESMA FIRDS full equity files (FULINS_E_<date>_<n>of<m>.zip), CFI ES* (shares), filtered to
           MIC XPRA (PSE regulated market: Prime + Standard) and MIC XPRM (PSE MTF: Free Market + START).
           Of XPRM only the START segment is kept (Czech growth issuers); Free Market rows are foreign
           secondary lines (Erste on XPRA is primary-listed in Vienna but is kept: it is on the regulated market).
           Index of files: registers.esma.europa.eu Solr core esma_registers_firds_files; when that index is down
           (502 on 2026-10-24) the reader probes the file host firds.esma.europa.eu directly.
Cross-chk: PSE market pages (server-rendered HTML, each row = PSE short name + ISIN):
           https://www.pse.cz/en/market-data/shares/{prime|standard|start}-market
           'ticker' = the PSE short name shown in the row (e.g. ČEZ, COLTCZ, KB); Bloomberg/Reuters codes sit on the detail page.
Public, no login, no key.  Run:  python roster.py   -> samples/roster-<date>.json
"""
import datetime as dt, html, io, json, os, re, sys, time, zipfile
import xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
TODAY = lambda: dt.datetime.now(dt.timezone.utc).date()
READ_BY = 'Allooloo CM-KG eu-sources/cz roster.py 0.1.0'
MICS = {'XPRA': 'Prague Stock Exchange regulated market (Prime, Standard)', 'XPRM': 'Prague Stock Exchange MTF (START kept; Free Market dropped)'}
SEGMENTS = {'prime': 'XPRA', 'standard': 'XPRA', 'start': 'XPRM'}
FIRDS_INDEX = 'https://registers.esma.europa.eu/solr/esma_registers_firds_files/select'
FIRDS_FILES = 'https://firds.esma.europa.eu/firds/'
PSE_URL = 'https://www.pse.cz/en/market-data/shares/{seg}-market'


def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=300, **kw)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    return None


def firds_equity_files():
    """Latest FULINS equity file set -> (publication_date, [urls], how_found)."""
    r = get(FIRDS_INDEX, tries=2, params={'q': '*', 'fq': 'file_type:FULINS', 'wt': 'json', 'rows': 60, 'sort': 'publication_date desc'})
    if r is not None and r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
        docs = r.json()['response']['docs']
        latest = docs[0]['publication_date']
        return latest[:10], [d['download_link'] for d in docs if d['publication_date'] == latest and '_E_' in d['file_name']], 'esma_registers_firds_files index'
    # index down: probe the file host for the most recent weekly set (published on Saturdays)
    today = TODAY()
    for back in range(0, 22):
        d = (today - dt.timedelta(days=back)).strftime('%Y%m%d')
        for m in range(1, 6):
            first = f'{FIRDS_FILES}FULINS_E_{d}_01of{m:02d}.zip'
            h = requests.head(first, headers=UA, timeout=60)
            if h.status_code == 200:
                return f'{d[:4]}-{d[4:6]}-{d[6:]}', [f'{FIRDS_FILES}FULINS_E_{d}_{k:02d}of{m:02d}.zip' for k in range(1, m + 1)], 'file host probe (index unavailable)'
    raise RuntimeError('no FIRDS FULINS_E file set found in the last 21 days')


def firds_rows(mics):
    pub, urls, how = firds_equity_files()
    rows, today = [], TODAY().isoformat()
    for u in urls:
        r = get(u)
        if r is None or r.status_code != 200:
            raise RuntimeError(f'FIRDS file download failed: {u}')
        z = zipfile.ZipFile(io.BytesIO(r.content))
        for _, el in ET.iterparse(z.open(z.namelist()[0]), events=('end',)):
            if not el.tag.endswith('}RefData'):
                continue
            ns = el.tag.split('}')[0] + '}'
            g, tv = el.find(ns + 'FinInstrmGnlAttrbts'), el.find(ns + 'TradgVnRltdAttrbts')
            mic = tv.findtext(ns + 'Id') if tv is not None else ''
            cfi = g.findtext(ns + 'ClssfctnTp') or ''
            term = (tv.findtext(ns + 'TermntnDt') or '')[:10]
            if mic in mics and cfi.startswith('ES') and not (term and term < today):
                rows.append({'isin': g.findtext(ns + 'Id'), 'name': g.findtext(ns + 'FullNm'), 'short_name': g.findtext(ns + 'ShrtNm'),
                             'cfi': cfi, 'currency': g.findtext(ns + 'NtnlCcy'), 'mic': mic, 'lei': el.findtext(ns + 'Issr'),
                             'admission': (tv.findtext(ns + 'AdmssnApprvlDtByIssr') or '')[:10], 'first_trade': (tv.findtext(ns + 'FrstTradDt') or '')[:10]})
            el.clear()
    return pub, urls, how, rows


def pse_segment(seg):
    """{isin: short_name} from a PSE market page."""
    url = PSE_URL.format(seg=seg)
    r = get(url, tries=3)
    if r is None or r.status_code != 200:
        return url, {}
    out = {}
    for m in re.finditer(r'data-title="([^"]*)".{0,400}?<div class="isin">\s*([A-Z]{2}[A-Z0-9]{9}[0-9])\s*</div>', r.text, re.S):
        out[m.group(2)] = html.unescape(m.group(1)).strip()
    return url, out


def fetch():
    pub, urls, how, frows = firds_rows(set(MICS))
    pse = {seg: pse_segment(seg) for seg in SEGMENTS}
    seg_of = {i: seg for seg, (_, m) in pse.items() for i in m}
    sym_of = {i: s for _, (_, m) in pse.items() for i, s in m.items()}
    seen, rows, dropped = set(), [], []
    for r in sorted(frows, key=lambda x: (x['mic'], x['name'] or '')):
        if (r['isin'], r['mic']) in seen:
            continue
        seen.add((r['isin'], r['mic']))
        seg = seg_of.get(r['isin'])
        if r['mic'] == 'XPRM' and seg != 'start':
            dropped.append(r['isin']); continue
        rows.append({'isin': r['isin'], 'name': r['name'], 'mic': r['mic'], 'lei': r['lei'], 'ticker': sym_of.get(r['isin']),
                     'segment': seg, 'cfi': r['cfi'], 'currency': r['currency'], 'on_exchange_list': seg is not None})
    have = {r['isin'] for r in rows}
    exchange_only = [{'isin': i, 'ticker': s, 'segment': seg} for seg, (_, m) in pse.items() for i, s in m.items() if i not in have]
    return {
        'source_url': FIRDS_FILES + ' (ESMA FIRDS FULINS equity files, publication ' + pub + ')',
        'source_files': urls, 'firds_found_via': how,
        'cross_check_urls': {seg: u for seg, (u, _) in pse.items()},
        'read_by': READ_BY, 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'mics': MICS, 'count': len(rows),
        'count_by_mic': {m: sum(1 for r in rows if r['mic'] == m) for m in MICS},
        'count_by_segment': {s: sum(1 for r in rows if r['segment'] == s) for s in SEGMENTS},
        'distinct_lei': len({r['lei'] for r in rows if r['lei']}),
        'cross_check': {'firds_rows_on_exchange_list': sum(r['on_exchange_list'] for r in rows),
                        'firds_only': [r['isin'] for r in rows if not r['on_exchange_list']],
                        'exchange_only': exchange_only, 'xprm_not_start_dropped': len(dropped)},
        'rows': rows,
    }


if __name__ == '__main__':
    out = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', f'roster-{TODAY().isoformat()}.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', out['count'], out['count_by_mic'], out['count_by_segment'], 'distinct LEI', out['distinct_lei'],
          'on exchange list', out['cross_check']['firds_rows_on_exchange_list'],
          'firds-only', out['cross_check']['firds_only'], 'exchange-only', out['cross_check']['exchange_only'], '->', p)
