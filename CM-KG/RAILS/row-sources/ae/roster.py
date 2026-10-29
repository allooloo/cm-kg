"""UAE Width 0 roster - listed equity shares of the Dubai Financial Market (XDFM) and Nasdaq Dubai (DIFX), from DFM's own site.
Abu Dhabi Securities Exchange (XADS) is NOT read: every ADX data path (apigateway.adx.ae) answers 401 without an ADX gateway key (see README).

Source of record (keyless, official, DFM / Borse Dubai group):
  list    POST https://api2.dfm.ae/web/widgets/v1/data  body Command=FreshSecuritiesLists&Language=en&lang=en&securitytype=equities
          (the call behind https://www.dfm.ae/the-exchange/market-information/listed-securities/equities). Gives symbol, full name,
          exchange (DFM / Nasdaq Dubai), listing date, Active flag, sector. One list for both venues.
  ISIN    POST https://api2.dfm.ae/web/widgets/v1/data  body Command=companyprofile&lang=en&symbol=<SYMBOL>
          (the call behind the company profile page https://www.dfm.ae/the-exchange/market-information/company/<SYMBOL>/...).
          Field "ISIN" as DFM publishes it. Price fields in the same answer are discarded.
  MIC     ISO 10383 list, https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv (read live; XDFM = DUBAI FINANCIAL
          MARKET, DIFX = NASDAQ DUBAI, XADS = ABU DHABI SECURITIES EXCHANGE).
  LEI     GLEIF API exact ISIN map: https://api.gleif.org/api/v1/lei-records?filter[isin]=<ISIN>. DFM carries no LEI.
Scope: SecurityType Equity, Active true. Rights-issue lines (IsLinked) are inactive on the day of the run and drop out by the Active rule.
No CFI is published by DFM: cfi stays blank.

fetch() -> {"source_url","read_by","read_at","count","rows":[{"isin","name","mic","lei","ticker","cfi"}]}
Usage: python roster.py [--no-lei]   writes samples/roster-<date>.json
"""
import os, sys, csv, io, json, time, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'application/json', 'Accept-Language': 'en-US,en;q=0.9', 'Origin': 'https://www.dfm.ae', 'Referer': 'https://www.dfm.ae/'}
WIDGETS = 'https://api2.dfm.ae/web/widgets/v1/data'
LIST_PAGE = 'https://www.dfm.ae/the-exchange/market-information/listed-securities/equities'
PROFILE_PAGE = 'https://www.dfm.ae/the-exchange/market-information/company/{sym}/trading'
ISO_MIC = 'https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv'
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
EXCHANGE_MIC = {'DFM': 'XDFM', 'Nasdaq Dubai': 'DIFX'}
GAP = 0.6   # seconds between calls (<= 2 requests / second)


def _post(body, tries=4):
    for i in range(tries):
        try:
            r = requests.post(WIDGETS, data=body, headers={**UA, 'Content-Type': 'application/x-www-form-urlencoded'}, timeout=90)
            if r.status_code == 200:
                d = r.json()
                return json.loads(d) if isinstance(d, str) else d
        except (requests.RequestException, ValueError):
            pass
        time.sleep(4 * (i + 1))
    raise RuntimeError(f'api2.dfm.ae did not answer: {body}')


def iso_mics(codes):
    """Read the ISO 10383 MIC list live; return {MIC: (name, status)} for the codes asked."""
    r = requests.get(ISO_MIC, headers={'User-Agent': UA['User-Agent']}, timeout=120)
    r.raise_for_status()
    out = {}
    for x in csv.DictReader(io.StringIO(r.content.decode('utf-8-sig', errors='replace'))):
        if x.get('MIC') in codes:
            out[x['MIC']] = (x.get('MARKET NAME-INSTITUTION DESCRIPTION'), x.get('STATUS'))
    return out


def gleif_lei(isin):
    try:
        r = requests.get(GLEIF, params={'filter[isin]': isin}, headers={'Accept': 'application/vnd.api+json'}, timeout=60)
        if r.status_code == 200:
            d = r.json().get('data') or []
            if len(d) == 1:
                return d[0]['id']
    except (requests.RequestException, ValueError):
        pass
    return ''


def securities_list():
    return _post('Command=FreshSecuritiesLists&Language=en&lang=en&securitytype=equities')


def company_profile(sym):
    return _post(f'Command=companyprofile&lang=en&symbol={requests.utils.quote(sym)}') or {}


def fetch(with_lei=True):
    lst = securities_list(); time.sleep(GAP)
    mics = iso_mics(set(EXCHANGE_MIC.values()) | {'XADS'})
    rows, no_isin, profile_errors = [], [], []
    for x in lst:
        if x.get('SecurityType') != 'Equity' or not x.get('Active'):
            continue
        sym = x['SecuritySymbol']; mic = EXCHANGE_MIC.get(x.get('Exchange'))
        try:
            p = company_profile(sym)
        except RuntimeError:
            p = {}; profile_errors.append(sym)
        time.sleep(GAP)
        isin = (p.get('ISIN') or '').strip() or None
        if not isin:
            no_isin.append(sym)
        lei = ''
        if isin and with_lei:
            lei = gleif_lei(isin); time.sleep(GAP)
        rows.append({'isin': isin, 'name': (p.get('FullName') or x.get('FullName') or '').strip(), 'mic': mic, 'lei': lei or '', 'ticker': sym, 'cfi': '',
                     'exchange': x.get('Exchange'), 'listing_date': x.get('ListingDate'), 'sector': x.get('Sector') or '',
                     'instrument_type': p.get('InstrumentType') or '', 'isin_page': PROFILE_PAGE.format(sym=sym)})
    rows.sort(key=lambda r: (r['mic'] or '', r['name']))
    return {'source_url': LIST_PAGE, 'endpoint': WIDGETS + ' (POST Command=FreshSecuritiesLists securitytype=equities; Command=companyprofile per symbol)',
            'read_by': 'DFM own listed-securities list (equities, Active) + DFM company profile ISIN; MIC from ISO 10383 (read live); LEI by GLEIF exact ISIN map',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'count': len(rows), 'count_with_isin': sum(1 for r in rows if r['isin']), 'count_isin_null': len(no_isin), 'isin_null_tickers': no_isin,
            'count_by_mic': {m: sum(1 for r in rows if r['mic'] == m) for m in EXCHANGE_MIC.values()},
            'count_with_lei': sum(1 for r in rows if r['lei']), 'lei_source': 'GLEIF API filter[isin] exact match (DFM carries no LEI)' if with_lei else 'not read (--no-lei)',
            'list_total': len(lst), 'list_inactive_or_other': len(lst) - len(rows), 'profile_errors': profile_errors,
            'iso10383': {'source_url': ISO_MIC, 'mics': {k: {'name': v[0], 'status': v[1]} for k, v in mics.items()}},
            'not_read': {'XADS': 'Abu Dhabi Securities Exchange: apigateway.adx.ae answers 401 Unauthorized without the adx-Gateway-APIKey header '
                                 '(lookups/1.1/data/listed-companies). Needs a key issued by ADX; not read.'},
            'scope': 'XDFM + DIFX equities, Active', 'rows': rows}


if __name__ == '__main__':
    res = fetch(with_lei='--no-lei' not in sys.argv)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], res['count_by_mic'], 'isin', res['count_with_isin'], 'null', res['count_isin_null'], 'lei', res['count_with_lei'], '->', out)
