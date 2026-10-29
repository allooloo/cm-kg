"""Norway halts: the official current trading-suspension list.

Primary: Euronext "Suspended instruments" (live.euronext.com/en/resources/market-events/suspended/current), whose table is fed by
  GET https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current   (JSON, all Euronext venues, public, no key)
filtered to XOSL / XOAS / MERK. Columns as published: halted at, MIC, issuer, LEI, ISIN, name, code, group, type, reason, resumption.
Second source: NewsWeb category 1202 "TRADING HALTS" (SUSPENSJONER) notices published by Oslo Bors over the last 180 days. Seen 2026-10-24:
the Euronext list carried no Oslo share suspension while NewsWeb had open suspensions (NEXT, ASA). An issuer whose latest 1202 notice is a
suspension with no later resumption, and whose share is still in the FIRDS roster (samples/roster-*.json), is added to "halted" with
source "NewsWeb 1202 (derived)"; the rest (mostly since delisted) stay in newsweb_cross_check.open.

fetch() -> {"source_url", "count", "halted": [{"isin", "ticker", "name", "since", "reason", ...}], ...}
"""
import datetime as dt, glob, json, os, re, sys, time
import requests

MICS = {'XOSL', 'XOAS', 'MERK'}
EURONEXT = 'https://live.euronext.com/en/ajax/haltedInstrument/getAjax/current'
PAGE = 'https://live.euronext.com/en/resources/market-events/suspended/current'
NEWSWEB = 'https://api3.oslo.oslobors.no/v1/newsreader/list'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
HERE = os.path.dirname(os.path.abspath(__file__))


def _clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(s or ''))).strip()


def _req(method, url, **kw):
    for i in range(4):
        try:
            r = requests.request(method, url, headers={**UA, **kw.pop('headers', {})}, timeout=180, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            r.raise_for_status(); return r
        except requests.RequestException:
            if i == 3:
                raise
            time.sleep(4 * (i + 1))


def euronext_halted(mics):
    data = _req('GET', EURONEXT, headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}).json()['data']
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


def newsweb_open(days=180):
    end = dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)
    start = end - dt.timedelta(days=days)
    msgs = []
    for cat in (1202, 1203):   # 1202 TRADING HALTS; resumptions are sometimes filed under 1203 MATCHING HALT
        msgs += _req('POST', NEWSWEB, params={'category': cat, 'fromDate': start.isoformat(), 'toDate': end.isoformat()},
                     headers={'Accept': 'application/json'}).json()['data']['messages']
    last = {}
    for m in sorted(msgs, key=lambda x: x['publishedTime']):
        last[m['issuerSign']] = m
    out = []
    for sign, m in last.items():
        t = m['title'].upper()
        if ('SUSPENSION' in t or 'HALT' in t or 'SUSPENSJON' in t or 'HANDELSSTANS' in t) and not ('RESUMPTION' in t or 'GJENOPPTA' in t or 'LIFT' in t):
            out.append({'ticker': sign, 'name': m['issuerName'], 'since': m['publishedTime'], 'title': m['title'],
                        'url': 'https://newsweb.oslobors.no/message/' + str(m['messageId'])})
    return {'source_url': NEWSWEB + '?category=1202 and 1203', 'window_days': days, 'notices': len(msgs), 'open': out}


def _norm(s):
    s = re.sub(r'[^a-z0-9æøå ]', ' ', (s or '').lower())
    s = re.sub(r'\b(asa|as|ltd|limited|plc|inc|corp|corporation|sa|se|ab|publ|nv|group|holding|holdings|the)\b', ' ', s)
    return ' '.join(s.split())


def _roster():
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    return json.load(open(files[-1], encoding='utf-8'))['rows'] if files else []


def fetch():
    halted = euronext_halted(MICS)
    try:
        nw = newsweb_open()
    except Exception as e:
        nw = {'error': repr(e)}
    rows = _roster(); have = {h['isin'] for h in halted}
    for o in nw.get('open', []):
        hits = [r for r in rows if (r.get('ticker') and r['ticker'] == o['ticker']) or _norm(r['name']) == _norm(o['name'])]
        o['in_roster'] = bool(hits)
        for r in hits:
            if r['isin'] not in have:
                have.add(r['isin'])
                halted.append({'isin': r['isin'], 'ticker': o['ticker'], 'name': r['name'], 'issuer': o['name'], 'lei': r.get('lei'), 'mic': r['mic'],
                               'since': o['since'], 'reason': o['title'], 'instrument_type': 'Stock', 'url': o['url'], 'source': 'NewsWeb 1202 (derived)'})
    eq = [h for h in halted if h['instrument_type'].lower() in ('stock', 'stocks', 'equity', 'equities', 'share', 'shares')]
    return {'source_url': EURONEXT + ' (page: ' + PAGE + ')', 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'mics': sorted(MICS), 'count': len(halted), 'count_equity': len(eq),
            'by_type': {t: sum(1 for h in halted if h['instrument_type'] == t) for t in sorted({h['instrument_type'] for h in halted})},
            'halted': halted, 'newsweb_cross_check': nw}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out = fetch()
    p = os.path.join(HERE, 'samples', 'halts-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', out['count'], 'equity', out['count_equity'], out['by_type'], 'newsweb open', len(out['newsweb_cross_check'].get('open', [])), '->', p)
    for h in out['halted']:
        print(' ', h['mic'], h['isin'], h['ticker'], h['name'], h['since'], h['reason'], h['instrument_type'])
    for h in out['newsweb_cross_check'].get('open', []):
        print('  newsweb', h['ticker'], h['name'], h['since'], h['title'])

# DAY ORDER 4: the read-by label of record (the node's halt flag names its source, not a file)
_fetch_src = fetch
def fetch():
    h = _fetch_src(); h["read_by"] = "Euronext live - Suspended instruments (current), Oslo MICs"; return h
