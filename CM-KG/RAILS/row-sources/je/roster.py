"""Jersey Width 0 roster - TISE-listed equity of Jersey issuers (The International Stock Exchange, MIC XCIE; Jersey regulator JFSC).

Source of record: TISE's own securities list, https://tisegroup.com/market/securities, which loads its data from
POST https://tisegroup.com/api/Securities  {"PageIndex","PageSize","Search","Country","Security","Subtype","Currency"}
(the page's own filter: Domicile = Country, Security Type = Subtype), and each security's record
GET https://tisegroup.com/api/securities/<mnemonic> (Isin, AllIsins, IssuerDetail.Address.Country, SubFund ...).
The security types list is GET https://tisegroup.com/umbraco/surface/ProxyApi/securityTypes.

Jersey vs Guernsey: TISE is one exchange for both islands (operator in Guernsey, ISO MIC XCIE country GG). The site tells
issuers apart by Domicile: the list filter Country=JEY (Jersey) vs GGY (Guernsey), which is the issuer's registered address
country in its TISE record (IssuerDetail.Address.Country.Code). This reader asks for Country=JEY and keeps a row only when
the record's own address country is also JEY. The ISIN prefix is NOT used (Jersey funds here carry GB ISINs).

Scope: TISE "Equity" security types. The pure share types (Trading Company, Specialist Company, SPAC) hold only 15 Jersey
lines (2026-10-24), so - as the contract allows for a tiny equity list - Closed-Ended and Open-Ended Investment Vehicles
(also typed "Equity" by TISE) are included, each row tagged with its TISE subtype.
ISIN: from the security record's Isin / AllIsins (IsinCode) only; none -> null.  LEI: not on TISE records; GLEIF
(api.gleif.org/api/v1/lei-records?filter[isin]=) by exact ISIN mapping only.  MIC XCIE checked live on the ISO 10383 list.
CFI: not published -> null.  Prices / trading data / latest-issue price fields are discarded.

fetch() -> {"source_url","read_by","read_at","count","rows":[{"isin","name","mic","lei","ticker","cfi", ...}]}
Usage: python roster.py   writes samples/roster-<date>.json (and cache/roster-latest.json for events.py / halt.py)
"""
import os, re, sys, csv, io, json, time, datetime
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tisehttp

HERE = os.path.dirname(os.path.abspath(__file__))
MARKET = 'je'
MIC = 'XCIE'
COUNTRY = 'JEY'
PAGE = 'https://tisegroup.com/market/securities'
API = '/api/Securities'
SHARE_TYPES = ['TradingCompany', 'SpecialistCompany', 'SpecialPurposeAcquisitionCompany']
FUND_TYPES = ['ClosedEndedInvestmentVehicle', 'OpenEndedInvestmentVehicle']
ISO_MIC_CSV = 'https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv'
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
UA = {'User-Agent': tisehttp.UA['User-Agent']}


def iso_mic(mic):
    try:
        r = requests.get(ISO_MIC_CSV, headers=UA, timeout=120)
        for row in csv.DictReader(io.StringIO(r.content.decode('utf-8-sig', errors='replace'))):
            if row.get('MIC') == mic:
                return {k: row[k] for k in ('MIC', 'OPERATING MIC', 'MARKET NAME-INSTITUTION DESCRIPTION', 'LEI', 'ACRONYM', 'ISO COUNTRY CODE (ISO 3166)', 'CITY', 'WEBSITE', 'STATUS', 'LAST UPDATE DATE', 'COMMENTS') if k in row}
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


def security_types():
    return tisehttp.call('/umbraco/surface/ProxyApi/securityTypes') or []


def list_securities(subtype, country=COUNTRY):
    out, p = [], 1
    while True:
        j = tisehttp.call(API, {'PageIndex': p, 'PageSize': 100, 'Search': '', 'Country': country, 'Security': None, 'Subtype': subtype, 'Currency': 'SHOWALL'}) or {}
        out += j.get('Securities') or []
        if p >= (j.get('TotalPages') or 0):
            break
        p += 1
    return out


def fetch(with_lei=True):
    types = {t['Value']: t for t in security_types()}
    eq = [t for t in SHARE_TYPES + FUND_TYPES if types.get(t, {}).get('Type') == 'Equity']
    rows, dropped = [], []
    for st in eq:
        for s in list_securities(st):
            d = tisehttp.call('/api/securities/' + s['Mnemonic']) or {}
            addr = ((d.get('IssuerDetail') or {}).get('Address') or {}).get('Country') or {}
            if addr.get('Code') != COUNTRY:
                dropped.append({'mnemonic': s['Mnemonic'], 'issuer': (s.get('Issuer') or {}).get('Name'), 'address_country': addr.get('Code')}); continue
            isins = [x['Code'] for x in (d.get('AllIsins') or []) if x.get('Type') == 'IsinCode' and ISIN_RE.match(x.get('Code') or '')]
            isin = d.get('Isin') if ISIN_RE.match(d.get('Isin') or '') else (isins[0] if len(isins) == 1 else None)
            iss = d.get('Issuer') or s.get('Issuer') or {}
            rows.append({'isin': isin, 'name': iss.get('Name'), 'mic': MIC, 'lei': None, 'ticker': s['Mnemonic'], 'cfi': None,
                         'instrument': d.get('Name') or s.get('Name'), 'subfund': (d.get('SubFund') or {}).get('Name') if d.get('SubFund') else None,
                         'subtype': s.get('Subtype'), 'subtype_display': s.get('SubtypeDisplay'), 'kind': 'share' if st in SHARE_TYPES else 'investment_vehicle',
                         'issuer_mnemonic': iss.get('Mnemonic'), 'subfund_mnemonic': (d.get('SubFund') or {}).get('Mnemonic') if d.get('SubFund') else None,
                         'currency': s.get('CurrencyIsoCode'), 'listed_at': (s.get('ListedAt') or '')[:10] or None, 'domicile': addr.get('Name'),
                         'all_isins': isins if len(isins) > 1 else None, 'page': f'https://tisegroup.com/market/securities/{s["Mnemonic"]}',
                         'isin_source': f'https://tisegroup.com/api/securities/{s["Mnemonic"]}' if isin else None})
    if with_lei:
        for r in rows:
            if r['isin']:
                lei, legal = gleif_by_isin(r['isin'])
                if lei:
                    r['lei'], r['lei_source'], r['lei_legal_name'] = lei, f'{GLEIF}?filter[isin]={r["isin"]}', legal
    return {'source_url': PAGE, 'endpoint': 'POST https://tisegroup.com/api/Securities (Country=JEY, Subtype=<equity type>) + GET https://tisegroup.com/api/securities/<mnemonic>',
            'read_by': 'TISE securities list, Domicile Jersey (Country=JEY), TISE Equity types ' + ', '.join(eq) + '; ISIN from the security record (Isin / AllIsins); '
                       'kept only when IssuerDetail.Address.Country = JEY; LEI from GLEIF lei-records?filter[isin]= (exact ISIN mapping)',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'count': len(rows), 'count_by_subtype': {t: sum(1 for r in rows if r['subtype'] == t) for t in eq},
            'count_shares': sum(1 for r in rows if r['kind'] == 'share'), 'count_investment_vehicles': sum(1 for r in rows if r['kind'] == 'investment_vehicle'),
            'count_with_isin': sum(1 for r in rows if r['isin']), 'count_without_isin': sum(1 for r in rows if not r['isin']),
            'count_with_lei': sum(1 for r in rows if r['lei']), 'dropped_address_not_jersey': dropped,
            'mic': MIC, 'mic_source': ISO_MIC_CSV, 'mic_iso_row': iso_mic(MIC),
            'scope': 'TISE-listed Equity-type securities of Jersey-domiciled issuers (shares + investment vehicles, because the share list is tiny)', 'rows': rows}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True); os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(res, open(os.path.join(HERE, 'cache', 'roster-latest.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('count', res['count'], res['count_by_subtype'], 'with ISIN', res['count_with_isin'], 'LEI', res['count_with_lei'], 'dropped', len(res['dropped_address_not_jersey']), 'MIC row', bool(res['mic_iso_row']), '->', out)
