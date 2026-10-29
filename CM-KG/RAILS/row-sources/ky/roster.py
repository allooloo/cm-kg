"""Cayman Islands Width 0 roster - Cayman Islands Stock Exchange (CSX, MIC XCAY; regulator CIMA).

Source of record: the CSX's own lists, https://www.csx.ky/companies/equities.asp (Equity) and
https://www.csx.ky/companies/investment-funds.asp (Investment Funds), and each instrument's own page
(equity.asp?SecId=<id> / investment-fund.asp?SecId=<id>), which carries Ticker / CSX Ticker and, where the CSX
publishes it, ISIN.

Scope: the CSX Equity list holds only 2 lines (2026-10-24), so - as the contract allows for a tiny equity list - the
Investment Funds list (listed fund share classes) is included too, each row tagged kind = equity | investment_fund.
Debt, specialist debt, ILS / cat bonds and retail debt are left out.
ISIN: read only from the instrument page's "ISIN" field. CSX fund pages carry no ISIN field, so fund rows keep
isin = null (the harvester drops them) - the count is reported.  The CSX is also the Cayman numbering agency, but it
publishes no public ISIN look-up (isin/isin-cusip.asp is a service page only).
LEI: not on CSX pages; filled only from GLEIF (api.gleif.org/api/v1/lei-records?filter[isin]=<ISIN>) by exact ISIN
mapping, one LEI back or blank.
MIC: XCAY, checked live against the ISO 10383 list (iso20022.org ISO10383_MIC.csv) on every run.
CFI: not published by CSX -> null.  Prices / NAVs on the pages are discarded.

fetch() -> {"source_url", "read_by", "read_at", "count", "rows": [{"isin","name","mic","lei","ticker","cfi", ...}]}
Usage: python roster.py   writes samples/roster-<date>.json (and cache/roster-latest.json for events.py / halt.py)
"""
import os, re, sys, csv, io, json, time, html, datetime
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csxhttp

HERE = os.path.dirname(os.path.abspath(__file__))
MARKET = 'ky'
MIC = 'XCAY'
LISTS = {'equity': 'https://www.csx.ky/companies/equities.asp', 'investment_fund': 'https://www.csx.ky/companies/investment-funds.asp'}
ISO_MIC_CSV = 'https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv'
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}


def _clean(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def iso_mic(mic):
    """Read the ISO 10383 MIC row live (iso20022.org). Returns the row dict or None."""
    try:
        r = requests.get(ISO_MIC_CSV, headers=UA, timeout=120)
        for row in csv.DictReader(io.StringIO(r.content.decode('utf-8-sig', errors='replace'))):
            if row.get('MIC') == mic:
                return {k: row[k] for k in ('MIC', 'OPERATING MIC', 'MARKET NAME-INSTITUTION DESCRIPTION', 'ISO COUNTRY CODE (ISO 3166)', 'CITY', 'WEBSITE', 'STATUS', 'LAST UPDATE DATE') if k in row}
    except requests.RequestException:
        pass
    return None


def gleif_by_isin(isin):
    """Exact ISIN -> LEI mapping from GLEIF. One LEI back or None (none / ambiguous stays blank)."""
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


def list_lines(kind):
    """One CSX list page -> [{'issuer','sec_id','description','page'}]. Value / NAV / closing columns are discarded."""
    url = LISTS[kind]
    t = csxhttp.text(url)
    out = []
    for panel in re.split(r'<div class="panel panel-issuer">', t)[1:]:
        m = re.search(r'<h4 class="panel-title">\s*<a[^>]*>(.*?)</a>', panel, re.S)
        issuer = _clean(m.group(1)) if m else ''
        for href, sec, desc in re.findall(r"<a href='((?:equity|investment-fund)\.asp\?SecId=([^'&]+))'[^>]*>(.*?)</a>", panel, re.S):
            out.append({'issuer': issuer, 'sec_id': sec, 'description': _clean(desc), 'page': 'https://www.csx.ky/companies/' + href, 'kind': kind})
    return out


def instrument_fields(page):
    """<tr><th>Label</th><td>Value</td></tr> pairs of the instrument page's details table."""
    t = csxhttp.text(page)
    i = t.find('id="content"'); t = t[i:] if i >= 0 else t
    stop = t.find('Related Announcements'); body = t[:stop] if stop > 0 else t
    f = {}
    for k, v in re.findall(r'<tr>\s*<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>\s*</tr>', body, re.S):
        k = _clean(k)
        if k and k not in f:
            f[k] = _clean(v)
    return f


def fetch(with_lei=True):
    lines = list_lines('equity') + list_lines('investment_fund')
    rows = []
    for ln in lines:
        f = instrument_fields(ln['page'])
        isin = (f.get('ISIN') or '').strip().upper()
        isin = isin if ISIN_RE.match(isin) else None
        ticker = f.get('Ticker') or f.get('CSX Ticker') or None
        rows.append({'isin': isin, 'name': ln['issuer'], 'mic': MIC, 'lei': None, 'ticker': ticker, 'cfi': None,
                     'instrument': ln['description'], 'kind': ln['kind'], 'sec_id': ln['sec_id'], 'page': ln['page'],
                     'currency': f.get('Currency'), 'listing_type': f.get('Listing Type'),
                     'country_of_incorporation': f.get('Country of incorporation'), 'isin_source': ln['page'] if isin else None})
    lei_note = 'GLEIF api.gleif.org lei-records?filter[isin]= (exact ISIN mapping; not on CSX pages)'
    if with_lei:
        for r in rows:
            if r['isin']:
                lei, legal = gleif_by_isin(r['isin'])
                if lei:
                    r['lei'], r['lei_source'], r['lei_legal_name'] = lei, f'{GLEIF}?filter[isin]={r["isin"]}', legal
    mic_row = iso_mic(MIC)
    by_kind = {k: sum(1 for r in rows if r['kind'] == k) for k in LISTS}
    res = {'source_url': LISTS['equity'], 'lists': LISTS,
           'read_by': 'CSX Equity + Investment Funds lists and each instrument page (equity.asp / investment-fund.asp ?SecId=); ISIN from the instrument page ISIN field only; '
                      'LEI from ' + lei_note,
           'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'count': len(rows), 'count_by_kind': by_kind, 'count_with_isin': sum(1 for r in rows if r['isin']),
           'count_without_isin': sum(1 for r in rows if not r['isin']), 'count_with_lei': sum(1 for r in rows if r['lei']),
           'distinct_issuers': len({r['name'] for r in rows}),
           'mic': MIC, 'mic_source': ISO_MIC_CSV, 'mic_iso_row': mic_row,
           'scope': 'CSX Equity list (2 lines) + Investment Funds list (fund share classes), because the equity list is tiny', 'rows': rows}
    return res


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True); os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(res, open(os.path.join(HERE, 'cache', 'roster-latest.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('count', res['count'], res['count_by_kind'], 'with ISIN', res['count_with_isin'], 'LEI', res['count_with_lei'], 'MIC row', bool(res['mic_iso_row']), '->', out)
