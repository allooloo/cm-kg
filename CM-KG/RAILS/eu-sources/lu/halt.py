"""Luxembourg halts - securities currently suspended from trading on the Luxembourg Stock Exchange (Bourse de Luxembourg + Euro MTF).

Source of record: LuxSE "Latest suspensions" (www.luxse.com market news / trading-data pages), read through the public GraphQL
endpoint the site itself calls (https://graphqlaz.luxse.com/v1/graphql, query securitiesLatestSuspension; no key). Pages are 0-based.
The list covers every instrument class (bonds, certificates, warrants, shares, GDRs, funds); each row carries LuxSE's instrument type
(ACT = shares / GDR / GDS, OBL = bonds, CER = certificates, WAR = warrants, ...) so equity halts can be split out (equity_count).
suspensionReason is LuxSE's code as published (e.g. ARET, which the site sorts after all other reasons; it marks the routine
suspension of an instrument ahead of its maturity / redemption). CSSF suspension decisions (Art. 46 Law of 30 May 2018) are press
releases on cssf.lu, not a list; they are not read here.

fetch() -> {"source_url", "count", "halted": [{"isin","ticker","name","since","reason", ...}]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, json, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
GQL = 'https://graphqlaz.luxse.com/v1/graphql'
HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
       'Content-Type': 'application/json', 'Origin': 'https://www.luxse.com', 'Referer': 'https://www.luxse.com/'}
Q = """query($pageNumber: Float!, $pageSize: Float!) { securitiesLatestSuspension(pageNumber: $pageNumber, pageSize: $pageSize) {
 id instrumentName isin instrumentType instrumentSubtype tradingCode currency status suspensionDate suspensionReason postponed } }"""


def fetch(page_size=100):
    rows, page, seen = [], 0, set()
    while page < 200:
        r = requests.post(GQL, headers=HDR, json={'query': Q, 'variables': {'pageNumber': page, 'pageSize': page_size}}, timeout=90)
        r.raise_for_status()
        j = r.json()
        if j.get('errors'):
            raise RuntimeError(j['errors'][0].get('message'))
        d = j['data']['securitiesLatestSuspension'] or []
        new = [x for x in d if x['id'] not in seen]
        seen.update(x['id'] for x in new)
        rows += new
        if len(d) < page_size or not new:
            break
        page += 1
    halted = [{'isin': x.get('isin') or '', 'ticker': x.get('tradingCode') or '', 'name': (x.get('instrumentName') or '').strip(),
               'since': (x.get('suspensionDate') or '')[:10], 'reason': x.get('suspensionReason') or '',
               'instrument_type': x.get('instrumentType') or '', 'instrument_subtype': x.get('instrumentSubtype') or '',
               'page': f"https://www.luxse.com/security/{x.get('isin')}/{x.get('id')}" if x.get('isin') else 'https://www.luxse.com',
               'status': x.get('status') or '', 'currency': x.get('currency') or '', 'luxse_id': x.get('id')} for x in rows]
    by_type, by_reason = {}, {}
    for h in halted:
        by_type[h['instrument_type']] = by_type.get(h['instrument_type'], 0) + 1
        by_reason[h['reason']] = by_reason.get(h['reason'], 0) + 1
    return {'source_url': 'https://www.luxse.com (Latest suspensions; GraphQL ' + GQL + ' securitiesLatestSuspension)',
            'read_by': 'LuxSE official Latest suspensions list (all instrument classes, Bourse de Luxembourg XLUX + Euro MTF EMTF), '
                       'through the public GraphQL endpoint luxse.com calls; equity = instrumentType ACT',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'count': len(halted), 'equity_count': by_type.get('ACT', 0), 'by_instrument_type': by_type, 'by_reason': by_reason, 'halted': halted}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    fn = os.path.join(HERE, 'samples', f"halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json")
    json.dump(res, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], 'equity', res['equity_count'], res['by_instrument_type'], res['by_reason'], '->', fn)
