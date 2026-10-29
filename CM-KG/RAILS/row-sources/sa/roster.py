"""Saudi Arabia Width 0 roster - listed equity shares of the Saudi Exchange: Main Market and Nomu Parallel Market.

MIC: ISO 10383 has one operating MIC for the Saudi Exchange, XSAU ("SAUDI STOCK EXCHANGE"), and no separate segment MIC for Nomu
(ISO list read live: https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv). Both markets map to XSAU.

Sources of record for ISIN + listing: the Saudi Exchange (www.saudiexchange.sa, issuer lists and company profiles) and the depository /
numbering agency Edaa (www.edaa.sa). On 2026-10-24 both hosts answered 403 Akamai "Access Denied" to every path from this network
(Python and a real browser alike). This reader therefore returns no rows; it says so in "blocked" instead of filling from elsewhere.
No other official source carries the list with ISINs: CMA (cma.gov.sa) publishes prospectuses and decisions, not a roster; the GLEIF
ISIN map returned nothing for Saudi ISINs tried. Rows stay empty rather than computed or taken from an aggregator.

fetch() -> {"source_url","read_by","read_at","count","rows":[{"isin","name","mic","lei","ticker","cfi"}], "blocked": [...]}
Usage: python roster.py   writes samples/roster-<date>.json
"""
import os, sys, csv, io, json, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _probe import probe, SAUDI_EXCHANGE, EDAA, UA  # noqa: E402

ISO_MIC = 'https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv'


def iso_mic(code='XSAU'):
    r = requests.get(ISO_MIC, headers={'User-Agent': UA['User-Agent']}, timeout=120)
    r.raise_for_status()
    rows = [x for x in csv.DictReader(io.StringIO(r.content.decode('utf-8-sig', errors='replace'))) if x.get('ISO COUNTRY CODE (ISO 3166)') == 'SA']
    return [{'mic': x['MIC'], 'operating_mic': x['OPERATING MIC'], 'type': x['OPRT/SGMT'], 'name': x['MARKET NAME-INSTITUTION DESCRIPTION'], 'status': x['STATUS']} for x in rows]


def fetch():
    checks = [probe(SAUDI_EXCHANGE), probe(EDAA)]
    rows = []
    if not checks[0]['blocked']:
        # The exchange answered: the issuer-list endpoint still has to be captured from a browser session on a network the exchange
        # lets in (it could not be seen from here). Until then no rows are produced.
        pass
    return {'source_url': SAUDI_EXCHANGE, 'read_by': 'Saudi Exchange issuer list + Edaa ISIN (not read: blocked from this network)',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'count': len(rows), 'count_with_isin': 0, 'count_isin_null': 0, 'rows': rows,
            'blocked': [c for c in checks if c['blocked']], 'probes': checks,
            'iso10383': {'source_url': ISO_MIC, 'sa_mics': iso_mic()},
            'scope': 'XSAU: Main Market + Nomu Parallel Market (one MIC)',
            'hitl': 'A human on a network the Saudi Exchange admits (which networks are admitted is not known from here; the deny is at '
                    'Akamai, network level) to capture the issuer-list and company-profile requests; or a Saudi Exchange market-data licence '
                    '(Saudi Exchange / Tadawul Group market data services). No registration attempted.'}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], 'blocked', [(b['url'], b['status'], b.get('reference')) for b in res['blocked']], '->', out)
