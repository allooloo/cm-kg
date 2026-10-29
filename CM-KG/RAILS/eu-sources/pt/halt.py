"""Portugal halts - current trading halts / suspensions on Euronext Lisbon (XLIS), Euronext Growth Lisbon (ALXL) and Euronext Access
Lisbon (ENXL).

Source: Euronext's official "Suspended instruments - Cash - Current" list (https://live.euronext.com/en/resources/market-events/suspended/current),
read through the JSON the page itself loads: GET https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current
(all Euronext venues, mostly warrants and certificates; one row = [halted since, MIC, issuer, LEI, ISIN, name, code, trading group,
type, reason, resumption, resumption reason]). Filtered here to the Lisbon MICs. No key.
CMVM orders suspensions (CVM art. 213/214) but publishes no current-suspension list on cmvm.pt (checked 2026-10-24); its orders
reach this list through Euronext Lisbon, which executes them. Limit: on 2026-10-24 neither the current list (7,538 rows) nor the
"past" list (8,230 rows) carried any Lisbon MIC, so Lisbon coverage of this feed is unproven; as a second signal halt.py scans the
CMVM SDI all-issuer feed for the last 30 days for filings whose title or type mentions a suspension (cmvm_sdi_mentions).

fetch() -> {"source_url", "count", "halted": [{"isin", "ticker", "name", "since", "reason"}]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, re, json, html, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
URL = 'https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current'
PAGE = 'https://live.euronext.com/en/resources/market-events/suspended/current'
LISBON = {'XLIS', 'ALXL', 'ENXL'}
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}


def _txt(c):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', str(c or '')))).strip()


def fetch():
    r = requests.get(URL, headers=UA, timeout=120)
    r.raise_for_status()
    data = r.json()['data']
    halted = []
    for row in data:
        if len(row) < 10 or _txt(row[1]) not in LISBON:
            continue
        m = re.search(r"data-order='([^']+)'", str(row[0]))
        halted.append({'isin': _txt(row[4]), 'ticker': _txt(row[6]), 'name': _txt(row[5]), 'since': m.group(1) if m else _txt(row[0]),
                       'reason': _txt(row[9]), 'page': PAGE, 'mic': _txt(row[1]), 'issuer': _txt(row[2]), 'lei': _txt(row[3]), 'instrument_type': _txt(row[8]),
                       'resumption': _txt(row[10]) if len(row) > 10 else '', 'resumption_reason': _txt(row[11]) if len(row) > 11 else ''})
    mentions = []
    try:
        import events
        cm = events.CMVM(); today = datetime.date.today()
        for x in cm.filings(0, (today - datetime.timedelta(days=30)).isoformat(), today.isoformat()):
            if re.search(r'(?i)suspens|halt', (x.get('Desc') or '') + ' ' + (x.get('Tipo') or '')):
                mentions.append({'date': x['Date'], 'type': x['Tipo'], 'title': x['Desc'], 'sdi': f"{x['Table']}{x['Id']}"})
    except Exception as e:
        mentions = [{'error': f'{type(e).__name__}: {e}'}]
    return {'source_url': URL, 'read_by': 'Euronext official current halted-instruments list (all venues), filtered to MICs XLIS / ENXL / ALXL; '
            'CMVM SDI suspension mentions over 30 days attached as a cross-check', 'page': PAGE, 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'scope': sorted(LISBON), 'euronext_rows_all_venues': len(data), 'count': len(halted), 'halted': halted,
            'cmvm_sdi_mentions_30d': mentions}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    fn = os.path.join(HERE, 'samples', f"halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json")
    json.dump(res, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Lisbon halted', res['count'], 'of', res['euronext_rows_all_venues'], 'Euronext rows; CMVM SDI suspension mentions 30d', len(res['cmvm_sdi_mentions_30d']), '->', fn)
