"""IT halts: the official current trading-suspension list for Euronext Milan (MTAA; operating MIC XMIL) and Euronext Growth Milan (EXGM).

Source: Euronext "Suspended instruments" (live.euronext.com/en/resources/market-events/suspended/current), whose table is fed by
  GET https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current   (JSON, all Euronext venues incl. Borsa Italiana, public, no key)
filtered to MTAA / EXGM / XMIL (the shares venues; Borsa's SeDeX / EuroTLX / MOT / XMLI structured-product and bond lines are left out,
their count is kept in other_milan_venues). Columns as published: halted at, MIC, issuer, LEI, ISIN, name, code, group, type, reason, resumption.
Seen 2026-10-24: 7,538 suspended lines estate-wide, none on MTAA / EXGM shares (XMLI 1 stock line, the rest warrants/certificates/bonds).
Suspension decisions are also published one by one as Borsa Italiana / Euronext "Avvisi" (connect.euronext.com/en/listview/notices,
notice numbers MIL_<date>_<n>_<segment>); that page is HTML without a usable paging API and is not read here.

fetch() -> {"source_url", "read_by", "read_at", "count", "halted": [{"isin", "ticker", "name", "since", "reason", "page"}], ...}
"""
import collections, datetime as dt, glob, json, os, re, sys, time
import requests

MICS = {'MTAA', 'EXGM', 'XMIL'}
MILAN_OTHER = {'XMLI', 'SEDX', 'ETLX', 'MOTX', 'XMOT', 'EMTF', 'MIVX', 'BGEM'}
EURONEXT = 'https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current'
PAGE = 'https://live.euronext.com/en/resources/market-events/suspended/current'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
HERE = os.path.dirname(os.path.abspath(__file__))


def _clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(s or ''))).strip()


def _req(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers={**UA, 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}, timeout=180, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            r.raise_for_status(); return r
        except requests.RequestException:
            if i == 3:
                raise
            time.sleep(4 * (i + 1))


def _roster():
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    return {r['isin']: r for r in json.load(open(files[-1], encoding='utf-8'))['rows']} if files else {}


def fetch():
    data = _req(EURONEXT).json()['data']
    roster = _roster()
    halted, other = [], collections.Counter()
    for row in data:
        if len(row) < 10:
            continue
        mic = _clean(row[1])
        if mic in MILAN_OTHER:
            other[(mic, _clean(row[8]))] += 1
        if mic not in MICS:
            continue
        m = re.search(r"data-order='([^']+)'", str(row[0]))
        res = re.search(r"data-order='([^']+)'", str(row[10])) if len(row) > 10 else None
        isin = _clean(row[4])
        halted.append({'isin': isin, 'ticker': _clean(row[6]) or (roster.get(isin) or {}).get('ticker'), 'name': _clean(row[5]), 'issuer': _clean(row[2]),
                       'lei': _clean(row[3]) or None, 'mic': mic, 'since': m.group(1) if m else _clean(row[0]), 'reason': _clean(row[9]),
                       'instrument_type': _clean(row[8]), 'resumption': (res.group(1) if res else (_clean(row[10]) if len(row) > 10 else '')) or None,
                       'page': PAGE, 'in_roster': isin in roster, 'source': 'Euronext suspended instruments (current)'})
    return {'source_url': EURONEXT + ' (page: ' + PAGE + ')', 'read_by': 'eu-sources/it/halt.py',
            'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'mics': sorted(MICS),
            'lines_read': len(data), 'count': len(halted), 'count_equity': sum(1 for h in halted if h['instrument_type'].lower().startswith('stock')),
            'halted': halted, 'other_milan_venues': {'%s %s' % k: v for k, v in sorted(other.items())}}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out = fetch()
    p = os.path.join(HERE, 'samples', 'halts-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('lines', out['lines_read'], 'halted', out['count'], 'equity', out['count_equity'], 'other milan', out['other_milan_venues'], '->', p)
    for h in out['halted']:
        print(' ', h['mic'], h['isin'], h['ticker'], h['name'], h['since'], h['reason'], h['instrument_type'])


# DAY ORDER 4: the read-by label of record (the node's halt flag names its source, not a file)
_fetch_src = fetch
def fetch():
    h = _fetch_src(); h['read_by'] = 'Euronext live — Suspended instruments (current), Euronext Milan MICs (MTAA, EXGM)'; return h
