"""Austria Width 1 events - regulated information from the OeKB OAM ("OAM Issuer Info", the Officially Appointed Mechanism
under the Transparency Directive, Sec. 123 BoerseG 2018). Public, free, no registration, no key.

Endpoint (the JSON API behind https://issuerinfo.oekb.at/ -> my.oekb.at/kapitalmarkt-services/kms-output/oamn/iic/list):
  GET https://my.oekb.at/issuer-info/rest/public/meldedaten/iic?isins=<ISIN>|emittentId=<id>&uploadFrom=YYYY-MM-DD&startPosition=<n>&offset=<page size>
  GET https://my.oekb.at/issuer-info/rest/public/stammdaten/iic                     (notification type codes -> English / German names)
  GET https://my.oekb.at/issuer-info/rest/public/stammdaten/iic/emittenten?query=<name>   (issuer search -> emittentId)
  Document file: https://my.oekb.at/issuer-info/rest/public/meldedaten/download/<file id>
Per-day reading: fetch_day(date) uses uploadFrom/uploadTo without an issuer filter.

fetch(isin_or_issuer, since) -> [{"date", "type", "title", "url", "source", ...}]
Usage: python events.py [since=YYYY-MM-DD]  -> tests three large issuers, writes samples/events-<date>.json
"""
import re, sys, json, os, time, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://my.oekb.at/issuer-info/rest'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
SOURCE = 'OeKB OAM Issuer Info (issuerinfo.oekb.at)'
ISIN_RX = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
PAGE = 200
_types = None


def _get(path, params=None, tries=4):
    for i in range(tries):
        try:
            r = requests.get(BASE + path, params=params, headers=UA, timeout=90)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def type_names():
    global _types
    if _types is None:
        j = _get('/public/stammdaten/iic')
        _types = {t['code']: (t.get('enName') or t.get('deName') or t['code']) for t in j.get('meldeTypen', [])}
    return _types


def issuers(query):
    return _get('/public/stammdaten/iic/emittenten', {'query': query}) or []


def _page_all(params):
    out, start = [], 0
    while True:
        j = _get('/public/meldedaten/iic', {**params, 'startPosition': start, 'offset': PAGE, 'locale': 'en'})
        docs = j.get('dokumente', [])
        out.extend(docs)
        start += len(docs)
        if not docs or start >= j.get('anzahlTreffer', 0):
            return out


def _row(d):
    tn = type_names()
    ts = datetime.datetime.fromtimestamp(d['uploadzeitpunkt'] / 1000, datetime.timezone.utc)
    files = d.get('dateien') or []
    return {'date': ts.strftime('%Y-%m-%dT%H:%M:%SZ'), 'type': tn.get(d.get('meldetypCode'), d.get('meldetypCode')), 'type_code': d.get('meldetypCode'),
            'title': d.get('titel') or d.get('kurzbeschreibung') or '', 'url': f'{BASE}/public/meldedaten/download/{files[0]["id"]}' if files else '',
            'files': [f'{BASE}/public/meldedaten/download/{f["id"]}' for f in files], 'language': d.get('sprachcode'), 'status': d.get('status'),
            'issuer': (d.get('emittent') or {}).get('name'), 'issuer_lei': (d.get('emittent') or {}).get('lei'), 'isins': [x.split(' ')[0] for x in d.get('isinBezug') or []],
            'oam_id': d['id'], 'source': SOURCE}


def fetch(isin_or_issuer, since=None):
    since = since or (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
    q = isin_or_issuer.strip()
    if ISIN_RX.match(q.upper()):
        # Resolve the ISIN to its OAM issuer, then read every filing of that issuer (filings are not always tagged with the share ISIN).
        j = _get('/public/meldedaten/iic', {'isins': q.upper(), 'startPosition': 0, 'offset': 1})
        eid = ((j.get('dokumente') or [{}])[0].get('emittent') or {}).get('id')
        docs = _page_all({'emittentId': eid, 'uploadFrom': since}) if eid else []
    else:
        hits = issuers(q)
        if not hits:
            return []
        docs = _page_all({'emittentId': hits[0]['id'], 'uploadFrom': since})
    return sorted((_row(d) for d in docs), key=lambda r: r['date'], reverse=True)


def fetch_day(day):
    """Every OAM notification uploaded on one day (all issuers)."""
    nxt = (datetime.date.fromisoformat(day) + datetime.timedelta(days=1)).isoformat()
    return [_row(d) for d in _page_all({'uploadFrom': day, 'uploadTo': nxt}) if _row(d)['date'][:10] == day]


if __name__ == '__main__':
    since = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('since=')), (datetime.date.today() - datetime.timedelta(days=365)).isoformat())
    tests = {'AT0000652011': 'Erste Group Bank AG', 'AT0000743059': 'OMV AG', 'AT0000BAWAG2': 'BAWAG Group AG'}
    out = {'source': SOURCE, 'endpoint': BASE + '/public/meldedaten/iic', 'since': since, 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'issuers': {}}
    for isin, name in tests.items():
        ev = fetch(isin, since)
        from collections import Counter
        out['issuers'][isin] = {'name': name, 'count': len(ev), 'by_type': dict(Counter(e['type'] for e in ev).most_common()), 'events': ev}
        print(isin, name, len(ev), Counter(e['type'] for e in ev).most_common(4))
    day = (datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)).isoformat()
    try:
        d = fetch_day(day); out['day_sample'] = {'day': day, 'count': len(d)}; print('day', day, len(d))
    except Exception as e:  # per-day mode is a convenience; keep the issuer sample
        out['day_sample'] = {'day': day, 'error': str(e)[:200]}
    fn = os.path.join(HERE, 'samples', f'events-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', fn)
