"""Ireland halts: the official current trading-suspension list for Euronext Dublin (XMSM, operating MIC XDUB) and Euronext Growth Dublin (XESM).

Source: Euronext "Suspended instruments" (live.euronext.com/en/resources/market-events/suspended/current), whose table is fed by
  GET https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current   (JSON, all Euronext venues, public, no key)
Columns as published: halted at, MIC, issuer, LEI, ISIN, name, code, group, type (Stock / Bond / W&C), reason, resumption.
Suspensions directed by the Central Bank of Ireland are executed by Euronext Dublin and appear in this list. Bond and warrant lines are kept, typed.

fetch() -> {"source_url", "count", "count_equity", "halted": [{"isin", "ticker", "name", "since", "reason", ...}]}
"""
import datetime as dt, json, os, re, sys, time
import requests

MARKET = 'ie'
MICS = {'XMSM', 'XESM', 'XDUB'}
EURONEXT = 'https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current'
PAGE = 'https://live.euronext.com/en/resources/market-events/suspended/current'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
HERE = os.path.dirname(os.path.abspath(__file__))


def _clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(s or ''))).strip()


def _get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers={**UA, **kw.pop('headers', {})}, timeout=180, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            r.raise_for_status(); return r
        except requests.RequestException:
            if i == 3:
                raise
            time.sleep(4 * (i + 1))


def euronext_halted(mics):
    data = _get(EURONEXT, headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}).json()['data']
    out = []
    for row in data:
        if len(row) < 10 or _clean(row[1]) not in mics:
            continue
        m = re.search(r"data-order='([^']+)'", str(row[0]))
        res = re.search(r"data-order='([^']+)'", str(row[10])) if len(row) > 10 else None
        out.append({'isin': _clean(row[4]), 'ticker': _clean(row[6]) or None, 'name': _clean(row[5]), 'issuer': _clean(row[2]), 'lei': _clean(row[3]) or None,
                    'mic': _clean(row[1]), 'since': m.group(1) if m else _clean(row[0]), 'reason': _clean(row[9]), 'group': _clean(row[7]),
                    'instrument_type': _clean(row[8]), 'resumption': (res.group(1) if res else _clean(row[10]) if len(row) > 10 else '') or None,
                    'resumption_reason': _clean(row[11]) if len(row) > 11 else None, 'source': 'Euronext suspended instruments (current)'})
    return out


def fetch():
    halted = euronext_halted(MICS)
    eq = [h for h in halted if h['instrument_type'].lower() in ('stock', 'stocks', 'equity', 'equities', 'share', 'shares')]
    return {'source_url': EURONEXT + ' (page: ' + PAGE + ')', 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'mics': sorted(MICS), 'count': len(halted), 'count_equity': len(eq),
            'by_type': {t: sum(1 for h in halted if h['instrument_type'] == t) for t in sorted({h['instrument_type'] for h in halted})},
            'halted': halted}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out = fetch()
    p = os.path.join(HERE, 'samples', 'halts-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', out['count'], 'equity', out['count_equity'], out['by_type'], '->', p)
    for h in out['halted']:
        print(' ', h['mic'], h['isin'], h['ticker'], h['name'], h['since'], h['reason'], h['instrument_type'])

# DAY ORDER 4: the read-by label of record (the node's halt flag names its source, not a file)
_fetch_src = fetch
def fetch():
    h = _fetch_src(); h["read_by"] = "Euronext live - Suspended instruments (current), Dublin MICs (XMSM, XESM)"; return h
