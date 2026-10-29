"""India Width 0 roster - listed equity shares on the NSE main board (XNSE) and the BSE main board (XBOM).
SME platforms (NSE Emerge, BSE SME = BSME) are optional: fetch(include_sme=True) or `python roster.py --sme`.

Sources of record (official, keyless):
- NSE "Securities available for trading" equity list: https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv
  (SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE). NSE Emerge (SME):
  https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv. The nsearchives host needs no cookie.
- BSE "List of Scrips" (https://www.bseindia.com/corporates/List_Scrips.html), whose page loads
  https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active
  (SCRIP_CD, Scrip_Name, Status, GROUP, FACE_VALUE, ISIN_NUMBER, scrip_id, Issuer_Name, Mktcap). The API answers 403 (Akamai
  "Access Denied") to a bare request; it answers when the request carries the headers a browser sends from the page
  (Referer/Origin www.bseindia.com, Sec-Fetch-*). Mktcap is discarded (no prices). INF* ISINs (mutual fund / ETF units) are left out.
  BSE groups M, MT, MS are the BSE SME platform (MIC BSME), all other groups the main board (XBOM).
- MIC: ISO 10383 (https://www.iso20022.org/market-identifier-codes, CSV ISO10383_MIC.csv): XNSE = NATIONAL STOCK EXCHANGE OF INDIA,
  XBOM = BSE LTD, BSME = BSE SME (segment of XBOM). NSE Emerge has no MIC of its own in ISO 10383, so SME rows from NSE carry XNSE.
- LEI: neither exchange list carries an LEI. LEIs come only from GLEIF's ISIN->LEI map (api.gleif.org, filter[isin], exact match),
  chunks with a hit are split down to single-ISIN queries, so each LEI is the exact GLEIF map of that ISIN.
- CFI: not published by NSE or BSE; left null.

Dual listings: one row per ISIN. NSE wins (mic XNSE, ticker = NSE symbol); bse_code / bse_id are kept on the row.
BSE-only ISINs get mic XBOM (or BSME) and ticker = BSE scrip_id.

fetch() -> {"source_url","read_by","read_at","count","rows":[{"isin","name","mic","lei","ticker","cfi", ...}]}
Usage: python roster.py [--sme] [--no-lei]   writes samples/roster-<date>.json
"""
import os, sys, io, csv, json, time, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
MARKET = 'in'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
NSE_EQ = 'https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv'
NSE_SME = 'https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv'
BSE_PAGE = 'https://www.bseindia.com/corporates/List_Scrips.html'
BSE_API = 'https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w'
BSE_HEADERS = {'User-Agent': UA, 'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'en-US,en;q=0.9',
               'Referer': 'https://www.bseindia.com/', 'Origin': 'https://www.bseindia.com',
               'Sec-Fetch-Site': 'same-site', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty'}
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
ISO_MIC = 'https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv'
BSE_SME_GROUPS = {'M', 'MT', 'MS'}
MICS = {'XNSE': 'NSE main board', 'XBOM': 'BSE main board', 'BSME': 'BSE SME'}


def _get(url, headers=None, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=headers or {'User-Agent': UA}, timeout=120, **kw)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(5 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(4 * (i + 1))
    return None


def _clean_isin(v):
    v = (v or '').strip().upper()
    return v if len(v) == 12 and v[:2].isalpha() else None


def nse_list(url=NSE_EQ):
    r = _get(url)
    if r is None or r.status_code != 200:
        raise RuntimeError(f'NSE list did not answer: {url} ({None if r is None else r.status_code})')
    rows = []
    for d in csv.DictReader(io.StringIO(r.content.decode('utf-8-sig', 'replace'))):
        d = {k.strip().upper().replace('_', ' '): (v or '').strip() for k, v in d.items() if k}
        rows.append({'symbol': d.get('SYMBOL'), 'name': d.get('NAME OF COMPANY'), 'series': d.get('SERIES'),
                     'isin': _clean_isin(d.get('ISIN NUMBER')), 'listed': d.get('DATE OF LISTING')})
    return rows


def bse_list(status='Active'):
    time.sleep(0.6)
    r = _get(BSE_API, headers=BSE_HEADERS, params={'Group': '', 'Scripcode': '', 'industry': '', 'segment': 'Equity', 'status': status})
    if r is None or r.status_code != 200 or not r.headers.get('content-type', '').startswith('application/json'):
        raise RuntimeError(f'BSE ListofScripData did not answer ({None if r is None else r.status_code})')
    out = []
    for d in r.json():
        out.append({'code': d.get('SCRIP_CD'), 'id': (d.get('scrip_id') or '').strip(), 'name': (d.get('Issuer_Name') or d.get('Scrip_Name') or '').strip(),
                    'scrip_name': (d.get('Scrip_Name') or '').strip(), 'group': (d.get('GROUP') or '').strip(), 'status': d.get('Status'),
                    'segment': d.get('Segment'), 'isin': _clean_isin(d.get('ISIN_NUMBER')), 'raw_isin': d.get('ISIN_NUMBER')})
    return out


def gleif_map(isins, log=None):
    """Exact ISIN -> LEI from GLEIF api.gleif.org: filter[isin] with up to 100 ISINs per call; a chunk with hits is split in halves
    until each hit is a single-ISIN query, so every LEI is tied to the exact ISIN GLEIF maps it to. <= 1 call/second."""
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

    def probe(chunk, data=None):
        data = q(chunk) if data is None else data
        if not data:
            return
        if len(chunk) == 1:
            rec = data[0]
            hits[chunk[0]] = {'lei': rec['id'], 'lei_name': rec['attributes']['entity']['legalName']['name']}
            return
        h = len(chunk) // 2
        probe(chunk[:h]); probe(chunk[h:])

    for k in range(0, len(isins), 100):
        probe(isins[k:k + 100])
        if log and (k // 100) % 10 == 0:
            log(f'gleif {min(k + 100, len(isins))}/{len(isins)} hits {len(hits)} calls {calls[0]}')
    return hits, calls[0]


def last_roster():
    """the last sourced roster drop in the pond (POND/in-cm-kg/width0/<date>/roster.json) — the job's pond sync brings it into the image's tree"""
    d = os.path.join(HERE, '..', '..', '..', 'POND', 'in-cm-kg', 'width0')
    for drop in sorted(os.listdir(d), reverse=True) if os.path.isdir(d) else []:
        f = os.path.join(d, drop, 'roster.json')
        if os.path.exists(f):
            r = json.load(open(f, encoding='utf-8'))
            if r.get('rows'): return r, drop
    return None, None


def fetch(include_sme=False, with_lei=True, log=None):
    read_at = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        nse = nse_list(NSE_EQ); sme = nse_list(NSE_SME) if include_sme else []
        bse = bse_list('Active')
    except Exception as e:
        # DAY ORDER 5 (2026-10-25): the exchanges' lists sit behind Akamai and refuse cloud egress (BSE ListofScripData answered 403 to the Azure job).
        # The roster is then the last sourced roster drop, as read (its rows, read_at and sources unchanged) — never a guess; the refusal is named.
        prev, drop = last_roster()
        if not prev: raise
        prev = dict(prev); prev['fallback'] = {'reason': repr(e)[:200], 'drop': drop, 'at': read_at, 'rule': 'last sourced roster drop reused as read; the refusal named'}
        prev['read_by'] = (prev.get('read_by') or '') + f' — reused from pond drop {drop} (the exchange refused this read: {repr(e)[:80]})'
        if log: log(f'roster: exchange list refused ({e!r}); reusing the last sourced roster drop {drop} ({len(prev["rows"])} rows)')
        return prev
    rows, by_isin, noisin = [], {}, 0
    for n, mic, board in [(x, 'XNSE', 'NSE main board') for x in nse] + [(x, 'XNSE', 'NSE Emerge (SME)') for x in sme]:
        row = {'isin': n['isin'], 'name': n['name'], 'mic': mic, 'lei': None, 'ticker': n['symbol'], 'cfi': None,
               'board': board, 'nse_series': n['series'], 'bse_code': None, 'bse_id': None, 'listed_on': ['XNSE']}
        if n['isin'] and n['isin'] in by_isin:
            continue
        rows.append(row)
        if n['isin']:
            by_isin[n['isin']] = row
    bse_dropped = {'INF (fund units)': 0, 'SME (not requested)': 0}
    for b in bse:
        if (b['raw_isin'] or '').upper().startswith('INF'):
            bse_dropped['INF (fund units)'] += 1; continue
        sme_b = b['group'] in BSE_SME_GROUPS
        if sme_b and not include_sme:
            bse_dropped['SME (not requested)'] += 1; continue
        mic = 'BSME' if sme_b else 'XBOM'
        if b['isin'] and b['isin'] in by_isin:
            r = by_isin[b['isin']]; r['bse_code'] = b['code']; r['bse_id'] = b['id']; r['listed_on'].append(mic)
            continue
        row = {'isin': b['isin'], 'name': b['name'], 'mic': mic, 'lei': None, 'ticker': b['id'], 'cfi': None,
               'board': 'BSE SME' if sme_b else 'BSE main board', 'nse_series': None, 'bse_code': b['code'], 'bse_id': b['id'], 'listed_on': [mic],
               'bse_group': b['group']}
        rows.append(row)
        if b['isin']:
            by_isin[b['isin']] = row
    gl_calls = 0
    if with_lei:
        hits, gl_calls = gleif_map(list(by_isin), log=log)
        for i, h in hits.items():
            by_isin[i]['lei'] = h['lei']; by_isin[i]['lei_source'] = 'GLEIF ISIN map (api.gleif.org lei-records filter[isin]=<ISIN>, exact single-ISIN match)'
    rows.sort(key=lambda r: (['XNSE', 'XBOM', 'BSME'].index(r['mic']), r['name'] or ''))
    count_by_mic = {m: sum(1 for r in rows if r['mic'] == m) for m in MICS}
    return {'source_url': NSE_EQ, 'sources': {'nse_main': NSE_EQ, 'nse_sme': NSE_SME if include_sme else None, 'bse': BSE_API + '?segment=Equity&status=Active (page ' + BSE_PAGE + ')',
                                              'lei': GLEIF + '?filter[isin]=...' if with_lei else None, 'mic': ISO_MIC},
            'read_by': 'NSE EQUITY_L.csv' + (' + SME_EQUITY_L.csv' if include_sme else '') + ' + BSE ListofScripData (Equity, Active, INF* dropped); one row per ISIN, NSE wins; '
                       'LEI = GLEIF exact ISIN map only; CFI not published (null)',
            'read_at': read_at, 'count': len(rows), 'count_by_mic': count_by_mic,
            'count_isin_null': sum(1 for r in rows if not r['isin']), 'count_dual_nse_bse': sum(1 for r in rows if len(r['listed_on']) > 1),
            'count_lei': sum(1 for r in rows if r['lei']), 'gleif_calls': gl_calls,
            'source_counts': {'nse_main': len(nse), 'nse_sme': len(sme), 'bse_active_equity': len(bse), 'bse_dropped': bse_dropped},
            'scope': 'NSE + BSE main boards' + (' + SME platforms' if include_sme else ''), 'rows': rows}


if __name__ == '__main__':
    res = fetch(include_sme='--sme' in sys.argv, with_lei='--no-lei' not in sys.argv, log=lambda m: print(m, flush=True))
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], res['count_by_mic'], 'isin null', res['count_isin_null'], 'dual', res['count_dual_nse_bse'], 'LEI', res['count_lei'], '->', out)
