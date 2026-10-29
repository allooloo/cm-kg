"""Norway events (Width 1): issuer filings from Oslo Bors NewsWeb (newsweb.oslobors.no), the Norwegian Officially Appointed Mechanism
operated by Euronext Oslo Bors. Server-readable JSON API, public, no key:
  POST https://api3.oslo.oslobors.no/v1/newsreader/list?issuer=<SIGN>&fromDate=YYYY-MM-DD&toDate=YYYY-MM-DD   (messages)
  POST https://api3.oslo.oslobors.no/v1/newsreader/issuers                                                    (issuer sign / name list)
  POST https://api3.oslo.oslobors.no/v1/newsreader/categories                                                 (NewsWeb categories)
Message page (as filed): https://newsweb.oslobors.no/message/<messageId>

fetch(isin_or_issuer, since) -> [{"date", "type", "title", "url", "source", ...}]
  isin_or_issuer: an ISIN (resolved to the NewsWeb issuer sign via the latest samples/roster-*.json ticker, then by name),
                  a NewsWeb issuer sign (EQNR), or an issuer name.
  since: 'YYYY-MM-DD' (default 365 days back).
"type" is the NewsWeb category as the store categorises it (English label; Norwegian label in type_no).
Run: python events.py  -> samples/events-<date>.json for Equinor, DNB, Telenor.
"""
import datetime as dt, glob, json, os, re, sys, time
import requests

API = 'https://api3.oslo.oslobors.no/v1/newsreader/'
SOURCE = 'Oslo Bors NewsWeb (OAM)'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
HERE = os.path.dirname(os.path.abspath(__file__))
_issuers = None


def _post(path, params=None, tries=4):
    for i in range(tries):
        try:
            r = requests.post(API + path, params=params or {}, headers=UA, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            r.raise_for_status()
            return r.json()['data']
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _norm(s):
    s = (s or '').lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9æøå ]', ' ', s)
    s = re.sub(r'\b(asa|as|ltd|limited|plc|inc|corp|corporation|sa|se|ab|publ|nv|bv|group|holding|holdings|the)\b', ' ', s)
    return ' '.join(s.split())


def issuers():
    global _issuers
    if _issuers is None:
        _issuers = _post('issuers')['issuers']
    return _issuers


def _latest_roster():
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    return json.load(open(files[-1], encoding='utf-8')) if files else None


def resolve(isin_or_issuer):
    """-> (issuer sign, issuer name) on NewsWeb, or (None, None)."""
    q = (isin_or_issuer or '').strip()
    signs = {i['issuerSign']: i for i in issuers() if i.get('issuerSign')}
    names = []
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', q):
        ro = _latest_roster()
        for r in (ro or {}).get('rows', []):
            if r['isin'] == q:
                if r.get('ticker') and r['ticker'] in signs:
                    return r['ticker'], signs[r['ticker']]['name']
                names.append(r['name'])
        if not names:
            return None, None
    elif q.upper() in signs:
        return q.upper(), signs[q.upper()]['name']
    else:
        names.append(q)
    for n in names:
        hits = [i for i in issuers() if i.get('issuerSign') and _norm(i.get('name')) == _norm(n)]
        hits.sort(key=lambda i: -int(i.get('isActive') or 0))
        if hits:
            return hits[0]['issuerSign'], hits[0]['name']
    return None, None


def fetch(isin_or_issuer, since=None):
    sign, name = resolve(isin_or_issuer)
    if not sign:
        return []
    start = dt.date.fromisoformat(since) if since else dt.date.today() - dt.timedelta(days=365)
    end = dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)
    out, seen = [], set()
    a = start
    while a < end:                      # 92-day windows keep each list response small
        b = min(a + dt.timedelta(days=92), end)
        for m in _post('list', {'issuer': sign, 'fromDate': a.isoformat(), 'toDate': b.isoformat()})['messages']:
            if m['messageId'] in seen:
                continue
            seen.add(m['messageId'])
            cats = m.get('category') or [{}]
            out.append({'date': m['publishedTime'], 'type': '; '.join(c.get('category_en', '') for c in cats),
                        'type_no': '; '.join(c.get('category_no', '') for c in cats), 'title': m['title'],
                        'url': 'https://newsweb.oslobors.no/message/' + str(m['messageId']), 'source': SOURCE,
                        'issuer_sign': m.get('issuerSign'), 'issuer_name': m.get('issuerName'), 'markets': m.get('markets'),
                        'attachments': m.get('numbAttachments'), 'correction_for': m.get('correctionForMessageId') or None})
        a = b
    out.sort(key=lambda e: e['date'], reverse=True)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    since = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=365)).isoformat()
    tests = ['NO0010096985', 'NO0010161896', 'NO0010063308']   # Equinor, DNB Bank, Telenor (by ISIN)
    res = {}
    for t in tests:
        ev = fetch(t, since)
        sign, name = resolve(t)
        res[t] = {'issuer_sign': sign, 'issuer_name': name, 'count': len(ev), 'events': ev}
        print(t, sign, name, len(ev), (ev[0]['date'], ev[0]['type'], ev[0]['title']) if ev else '')
    out = {'source_url': API + 'list', 'read_by': 'eu-sources/no/events.py', 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
           'since': since, 'issuers': res}
    p = os.path.join(HERE, 'samples', 'events-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', p)
