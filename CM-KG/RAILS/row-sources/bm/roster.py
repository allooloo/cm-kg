"""Bermuda Width 0 roster - Bermuda Stock Exchange (BSX, MIC XBDA; regulator BMA).

Source of record: BSX "Listed Securities" (https://www.bsx.com/listed-securities, a Drupal/Solr view, server-rendered,
paged ?page=N from 0), filtered by the page's own Security Type select (CoListingType) and Status (CoStatus=All = listed
+ suspended).  Equity types read: 1 Domestic Main Board, 2 Domestic Small Cap Board, 3 International Company,
8 Mezzanine Market.  Funds (5), ILS (4), debt (6, 9), CLO (10) and derivative warrants (7) are left out.
Each line's company page (https://www.bsx.com/company/<id>) carries Ticker, ISIN, CUSIP, Status, Domicile, Listing Date,
Currency, Investors.  ISIN is read only from that page's ISIN field (BSX also runs Bermuda's numbering service).
LEI: not on BSX pages; filled only from GLEIF (api.gleif.org/api/v1/lei-records?filter[isin]=<ISIN>), exact ISIN mapping.
MIC: XBDA, checked live against the ISO 10383 list (iso20022.org ISO10383_MIC.csv) on every run.
CFI: not published by BSX -> null.  The trading-history / dividend tables (prices) are discarded.

fetch() -> {"source_url", "read_by", "read_at", "count", "rows": [{"isin","name","mic","lei","ticker","cfi", ...}]}
Usage: python roster.py   writes samples/roster-<date>.json (and cache/roster-latest.json for events.py / halt.py)
"""
import os, re, sys, csv, io, json, time, html, datetime
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bsxhttp

HERE = os.path.dirname(os.path.abspath(__file__))
MARKET = 'bm'
MIC = 'XBDA'
LIST = 'https://www.bsx.com/listed-securities'
EQUITY_TYPES = {'1': 'Domestic Main Board', '2': 'Domestic Small Cap Board', '3': 'International Company', '8': 'Mezzanine Market'}
ISO_MIC_CSV = 'https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv'
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
UA = {'User-Agent': bsxhttp.UA['User-Agent']}


def _clean(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def iso_mic(mic):
    try:
        r = requests.get(ISO_MIC_CSV, headers=UA, timeout=120)
        for row in csv.DictReader(io.StringIO(r.content.decode('utf-8-sig', errors='replace'))):
            if row.get('MIC') == mic:
                return {k: row[k] for k in ('MIC', 'OPERATING MIC', 'MARKET NAME-INSTITUTION DESCRIPTION', 'ACRONYM', 'ISO COUNTRY CODE (ISO 3166)', 'CITY', 'WEBSITE', 'STATUS', 'LAST UPDATE DATE') if k in row}
    except requests.RequestException:
        pass
    return None


def gleif_by_isin(isin):
    for i in range(3):
        try:
            r = requests.get(GLEIF, params={'filter[isin]': isin}, headers={**UA, 'Accept': 'application/vnd.api+json'}, timeout=60)
            if r.status_code == 200:
                data = r.json().get('data') or []
                ids = sorted({d['id'] for d in data})
                time.sleep(0.6)
                return (ids[0], data[0]['attributes']['entity']['legalName']['name']) if len(ids) == 1 else (None, None)
        except requests.RequestException:
            pass
        time.sleep(3 * (i + 1))
    return None, None


ROW = re.compile(r'<a href="(/company/(\d+))" hreflang="und">(.*?)</a>\s*</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>', re.S)


def list_lines(co_type, status='All'):
    """All pages of the Listed Securities view for one Security Type -> [{'company_id','name','currency','type','page'}]."""
    out, page = [], 0
    while True:
        t = bsxhttp.text(LIST, params={'CoListingType': co_type, 'CoStatus': status, 'page': page})
        got = ROW.findall(t)
        for href, cid, name, cur, ty in got:
            out.append({'company_id': cid, 'name': _clean(name), 'currency': _clean(cur), 'type': _clean(ty), 'page': bsxhttp.BASE + href})
        last = [int(x) for x in re.findall(r'[?;&]page=(\d+)', t)]   # the view's pager links
        if not got or page >= (max(last) if last else 0):
            break
        page += 1
    return out


def company_fields(page):
    """Field label -> value from the company page ('field__label' / 'field__item' pairs)."""
    t = bsxhttp.text(page)
    f = {}
    for lab, val in re.findall(r'<div class="field__label">([^<]*)</div>\s*<div class="field__item">(.*?)</div>', t, re.S):
        lab = _clean(lab)
        if lab and lab not in f:
            f[lab] = _clean(val)
    return f, t


def fetch(with_lei=True):
    lines, seen = [], set()
    for ty in EQUITY_TYPES:
        for ln in list_lines(ty):
            if ln['company_id'] not in seen:
                seen.add(ln['company_id']); lines.append(ln)
    rows = []
    for ln in lines:
        f, _ = company_fields(ln['page'])
        isin = (f.get('ISIN') or '').strip().upper()
        isin = isin if ISIN_RE.match(isin) else None
        rows.append({'isin': isin, 'name': ln['name'], 'mic': MIC, 'lei': None, 'ticker': f.get('Ticker') or None, 'cfi': None,
                     'company_id': ln['company_id'], 'page': ln['page'], 'listing_type': ln['type'], 'currency': ln['currency'] or f.get('Currency'),
                     'cusip': f.get('CUSIP') or None, 'status': f.get('Status'), 'domicile': f.get('Domicile'), 'listed_since': f.get('Listing Date'),
                     'investors': f.get('Investors'), 'isin_source': ln['page'] if isin else None})
    if with_lei:
        for r in rows:
            if r['isin']:
                lei, legal = gleif_by_isin(r['isin'])
                if lei:
                    r['lei'], r['lei_source'], r['lei_legal_name'] = lei, f'{GLEIF}?filter[isin]={r["isin"]}', legal
    return {'source_url': LIST, 'read_by': 'BSX Listed Securities view (CoListingType in 1,2,3,8; CoStatus=All) + each company page (ISIN / Ticker / CUSIP / Status); '
                                           'LEI from GLEIF api.gleif.org lei-records?filter[isin]= (exact ISIN mapping; not on BSX pages)',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'count': len(rows), 'count_by_type': {v: sum(1 for r in rows if r['listing_type'] == v) for v in EQUITY_TYPES.values()},
            'count_by_status': {s: sum(1 for r in rows if r['status'] == s) for s in sorted({r['status'] or '' for r in rows})},
            'count_with_isin': sum(1 for r in rows if r['isin']), 'count_without_isin': sum(1 for r in rows if not r['isin']),
            'count_with_lei': sum(1 for r in rows if r['lei']), 'mic': MIC, 'mic_source': ISO_MIC_CSV, 'mic_iso_row': iso_mic(MIC),
            'scope': 'BSX equity boards: Domestic Main Board, Domestic Small Cap Board, International Company, Mezzanine Market (listed + suspended)', 'rows': rows}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True); os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(res, open(os.path.join(HERE, 'cache', 'roster-latest.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('count', res['count'], res['count_by_type'], res['count_by_status'], 'with ISIN', res['count_with_isin'], 'LEI', res['count_with_lei'], 'MIC row', bool(res['mic_iso_row']), '->', out)
