"""Taiwan Width 0 roster - listed equity shares on TWSE (MIC XTAI, incl. the Taiwan Innovation Board) and TPEx (MIC ROCO, OTC / 上櫃).

Source of record: TWSE's ISIN code lists (TWSE is Taiwan's national numbering agency for ISIN / CFI):
  https://isin.twse.com.tw/isin/C_public.jsp?strMode=2  本國上市證券國際證券辨識號碼一覽表 (TWSE listed)
  https://isin.twse.com.tw/isin/C_public.jsp?strMode=4  本國上櫃證券國際證券辨識號碼一覽表 (TPEx listed)
  English twins: https://isin.twse.com.tw/isin/e_C_public.jsp?strMode=2 / 4. Encoding MS950 (cp950).
  Columns: 有價證券代號及名稱 (code + short name), 國際證券辨識號碼(ISIN Code), 上市日, 市場別, 產業別, CFICode, 備註.
  Section rows split the table (股票, 創新板, 特別股, ETF, 權證, TDR, ...). Kept: sections 股票 and 創新板 with CFI ES* (shares);
  preferred shares (特別股, EP*/EF*), TDRs (ED*), ETFs, ETNs, warrants and REITs are left out. Emerging board (興櫃, strMode=5) is not read.
Names: full Chinese legal name from the exchanges' company basic data (TWSE OpenAPI https://openapi.twse.com.tw/v1/opendata/t187ap03_L
  上市公司基本資料, field 公司名稱; TPEx OpenAPI https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O 上櫃股票基本資料, field CompanyName),
  falling back to the ISIN-list short name. name_short (Chinese) and name_en_short (English list) are kept as published.
MIC: ISO 10383 (https://www.iso20022.org/market-identifier-codes, ISO10383_MIC.csv): XTAI = TAIWAN STOCK EXCHANGE, ROCO = TAIPEI EXCHANGE.
LEI: the lists carry none. LEI only from GLEIF's ISIN->LEI map (api.gleif.org lei-records filter[isin], exact single-ISIN match).
Ticker: the TWSE/TPEx security code (e.g. 2330). One row per ISIN (an ISIN is on one market only).

fetch() -> {"source_url","read_by","read_at","count","rows":[{"isin","name","mic","lei","ticker","cfi", ...}]}
Also writes cache/isin_map.json (code -> ISIN, all sections) for events.py / halt.py.
Usage: python roster.py [--no-lei]   writes samples/roster-<date>.json
"""
import os, re, sys, json, time, html, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
MARKET = 'tw'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
ISIN_URL = 'https://isin.twse.com.tw/isin/{e}C_public.jsp?strMode={m}'
LISTS = {'XTAI': 2, 'ROCO': 4}
SHARE_SECTIONS = {'股票', '創新板'}
TWSE_BASIC = 'https://openapi.twse.com.tw/v1/opendata/t187ap03_L'
TPEX_BASIC = 'https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O'
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
ISO_MIC = 'https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv'
MICS = {'XTAI': 'Taiwan Stock Exchange', 'ROCO': 'Taipei Exchange (TPEx)'}
CACHE = os.path.join(HERE, 'cache')


def _get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers={'User-Agent': UA}, timeout=180, **kw)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 502, 503, 504):
                time.sleep(5 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(5 * (i + 1))
    raise RuntimeError(f'no answer: {url}')


def isin_list(mode, english=False):
    """All rows of one ISIN list: [{'section','code','short','isin','listed','market','industry','cfi','note'}]."""
    url = ISIN_URL.format(e='e_' if english else '', m=mode)
    t = _get(url).content.decode('cp950', 'replace')
    out, sec = [], None
    upd = re.search(r'(?:最近更新日期|Last Update)[^0-9]*([0-9/]+)', t)
    for tr in re.findall(r'<tr>(.*?)</tr>', t, re.S):
        cells = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if len(cells) == 1:
            sec = cells[0].strip(); continue
        if len(cells) < 6 or not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}[0-9]', cells[1]):
            continue
        code, _, short = cells[0].partition('　')
        out.append({'section': sec, 'code': code.strip(), 'short': re.sub(r'\s+', ' ', short).strip(), 'isin': cells[1], 'listed': cells[2].replace('/', '-'),
                    'market': cells[3], 'industry': cells[4], 'cfi': cells[5], 'note': cells[6] if len(cells) > 6 else ''})
    return url, (upd.group(1) if upd else None), out


def basic_names():
    names = {}
    try:
        for d in _get(TWSE_BASIC).json():
            names[d.get('公司代號', '').strip()] = (d.get('公司名稱') or '').strip()
    except Exception:
        pass
    time.sleep(0.6)
    try:
        for d in _get(TPEX_BASIC).json():
            names[d.get('SecuritiesCompanyCode', '').strip()] = (d.get('CompanyName') or '').strip()
    except Exception:
        pass
    return names


def gleif_map(isins, log=None):
    """Exact ISIN -> LEI from GLEIF: filter[isin] with up to 100 ISINs per call; a chunk with hits is split in halves until each
    hit is a single-ISIN query. <= 1 call/second."""
    isins = sorted(set(i for i in isins if i)); hits = {}; s = requests.Session(); s.headers.update({'Accept': 'application/vnd.api+json', 'User-Agent': UA})
    calls = [0]

    def q(chunk):
        for i in range(5):
            try:
                r = s.get(GLEIF, params={'filter[isin]': ','.join(chunk), 'page[size]': 200}, timeout=90); calls[0] += 1; time.sleep(1.05)
                if r.status_code == 429:
                    time.sleep(30); continue
                if r.status_code == 200:
                    return r.json().get('data', [])
            except requests.RequestException:
                time.sleep(5)
        raise RuntimeError('GLEIF did not answer')

    def probe(chunk):
        data = q(chunk)
        if not data:
            return
        if len(chunk) == 1:
            hits[chunk[0]] = {'lei': data[0]['id'], 'lei_name': data[0]['attributes']['entity']['legalName']['name']}
            return
        h = len(chunk) // 2
        probe(chunk[:h]); probe(chunk[h:])

    for k in range(0, len(isins), 100):
        probe(isins[k:k + 100])
        if log and (k // 100) % 5 == 0:
            log(f'gleif {min(k + 100, len(isins))}/{len(isins)} hits {len(hits)} calls {calls[0]}')
    return hits, calls[0]


def fetch(with_lei=True, log=None):
    read_at = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rows, urls, updated, code_map, sections = [], {}, {}, {}, {}
    for mic, mode in LISTS.items():
        url, upd, zh = isin_list(mode); time.sleep(1)
        _, _, en = isin_list(mode, english=True); time.sleep(1)
        en_by = {r['isin']: r for r in en}
        urls[mic] = url; updated[mic] = upd
        for r in zh:
            code_map[r['code']] = {'isin': r['isin'], 'mic': mic, 'section': r['section'], 'short': r['short'], 'cfi': r['cfi']}
            sections.setdefault(mic, {}).setdefault(r['section'], 0); sections[mic][r['section']] += 1
            if r['section'] in SHARE_SECTIONS and r['cfi'].startswith('ES'):
                e = en_by.get(r['isin'], {})
                rows.append({'isin': r['isin'], 'name': None, 'mic': mic, 'lei': None, 'ticker': r['code'], 'cfi': r['cfi'],
                             'name_short': r['short'], 'name_en_short': e.get('short') or None, 'board': r['market'], 'section': r['section'],
                             'industry': r['industry'], 'industry_en': e.get('industry') or None, 'listed': r['listed']})
    names = basic_names()
    for r in rows:
        full = names.get(r['ticker'])
        r['name'] = full or r['name_short']; r['name_source'] = 'company basic data (t187ap03)' if full else 'ISIN list short name'
    gl_calls = 0
    if with_lei:
        hits, gl_calls = gleif_map([r['isin'] for r in rows], log=log)
        for r in rows:
            if r['isin'] in hits:
                r['lei'] = hits[r['isin']]['lei']; r['lei_source'] = 'GLEIF ISIN map (api.gleif.org lei-records filter[isin]=<ISIN>, exact single-ISIN match)'
    os.makedirs(CACHE, exist_ok=True)
    json.dump({'read_at': read_at, 'map': code_map}, open(os.path.join(CACHE, 'isin_map.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    rows.sort(key=lambda r: (r['mic'] != 'XTAI', r['ticker']))
    return {'source_url': urls['XTAI'], 'sources': {'isin_lists': urls, 'isin_lists_en': {m: ISIN_URL.format(e='e_', m=n) for m, n in LISTS.items()},
                                                   'names': [TWSE_BASIC, TPEX_BASIC], 'lei': GLEIF + '?filter[isin]=...' if with_lei else None, 'mic': ISO_MIC},
            'read_by': 'TWSE ISIN lists (isin.twse.com.tw C_public.jsp strMode=2 TWSE / 4 TPEx), sections 股票 + 創新板, CFI ES*; full names from TWSE/TPEx '
                       'company basic data; LEI = GLEIF exact ISIN map only', 'read_at': read_at, 'lists_updated': updated,
            'count': len(rows), 'count_by_mic': {m: sum(1 for r in rows if r['mic'] == m) for m in MICS},
            'count_isin_null': sum(1 for r in rows if not r['isin']), 'count_lei': sum(1 for r in rows if r['lei']),
            'count_full_name': sum(1 for r in rows if r['name_source'].startswith('company')), 'gleif_calls': gl_calls,
            'sections_on_lists': sections, 'scope': 'TWSE (XTAI, incl. 創新板) + TPEx (ROCO) shares', 'rows': rows}


if __name__ == '__main__':
    res = fetch(with_lei='--no-lei' not in sys.argv, log=lambda m: print(m, flush=True))
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], res['count_by_mic'], 'isin null', res['count_isin_null'], 'LEI', res['count_lei'], 'full names', res['count_full_name'], '->', out)
