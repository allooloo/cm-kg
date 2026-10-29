"""Saudi Arabia Width 1 events - issuer announcements on the Saudi Exchange (the store of record for Main Market and Nomu issuers;
the exchange publishes English and Arabic editions).

Not readable from this network: www.saudiexchange.sa answered 403 Akamai "Access Denied" on every path on 2026-10-24 (see _probe.py).
fetch() probes the exchange each call; when blocked it returns [] and records why in LAST_STATUS, rather than reading a copy elsewhere.
CMA (cma.gov.sa) is reachable but carries CMA's own announcements (decisions, approvals), not issuer filings, so it is not used here.

fetch(isin_or_issuer, since) -> [{"date","type","type_en","title","url","source"}]
Usage: python events.py [ISIN|symbol ...]   writes samples/events-<date>.json (default: Saudi Aramco, Al Rajhi Bank, SABIC by name)
"""
import os, sys, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _probe import probe, SAUDI_EXCHANGE  # noqa: E402

SOURCE = 'Saudi Exchange issuer announcements (www.saudiexchange.sa)'
LAST_STATUS = {}


def fetch(isin_or_issuer, since):
    p = probe(SAUDI_EXCHANGE)
    LAST_STATUS.clear(); LAST_STATUS.update(p)
    if p['blocked']:
        return []
    # Reachable: the announcements endpoint must first be captured from a browser session the exchange admits; not seen from here.
    return []


if __name__ == '__main__':
    # Queried by issuer name: no symbol or ISIN could be read from an official source here, so none is written.
    tests = sys.argv[1:] or ['Saudi Arabian Oil Company', 'Al Rajhi Bank', 'Saudi Basic Industries Corporation']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': SAUDI_EXCHANGE, 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'since': since.isoformat(), 'key_required': None, 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        res['issuers'][q] = {'count': len(ev), 'events': ev, 'status': dict(LAST_STATUS)}
        print(q, len(ev), LAST_STATUS.get('reason'), flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
