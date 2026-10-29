"""Ireland events (Width 1): issuer filings from the Euronext Dublin Official Authorised Mechanism (OAM, authorised by the Central Bank of
Ireland under the Transparency Regulations 2007) and the Euronext Dublin RIS announcement feed, both served by Euronext Direct
(direct.euronext.com, the successor of ise.ie announcements). Public JSON, no key:
  POST https://direct.euronext.com/api/PublicAnnouncements/OAMs  {"startDate","endDate","page","firstLetter","companyName"}  (OAM filings, categorised)
  POST https://direct.euronext.com/api/PublicAnnouncements/RIS   {same body}                                              (RIS announcements, uncategorised)
  document: https://direct.euronext.com/api/PublicAnnouncements/OAMDocument/<name>?id=<id>  (RISDocument/... for RIS)
companyName is a substring filter on the filer name. ISINs are resolved to the issuer's legal name through its LEI (GLEIF, api.gleif.org),
falling back to the FIRDS full name in the latest samples/roster-*.json.

fetch(isin_or_issuer, since, include_ris=True) -> [{"date", "type", "title", "url", "source"}]
  "type": the OAM regulatory category as filed (regulatoryCategoryDescription); RIS items carry type "RIS announcement" (the feed has no category).
Run: python events.py  -> samples/events-<date>.json for Ryanair, Kerry Group, Kingspan.
"""
import datetime as dt, glob, json, os, re, sys, time
import requests

BASE = 'https://direct.euronext.com/api/PublicAnnouncements/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
HERE = os.path.dirname(os.path.abspath(__file__))
SUFFIX = r'\b(public limited company|plc|p l c|dac|designated activity company|limited|ltd|holdings?|group|the|ordinary shares?.*|units.*)\b'


def _post(ep, body, tries=4):
    for i in range(tries):
        try:
            r = requests.post(BASE + ep, json=body, headers=UA, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            r.raise_for_status(); return r.json()
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _norm(s):
    s = re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower())
    s = re.sub(SUFFIX, ' ', s)
    return ' '.join(s.split())


def _roster_row(isin):
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    for r in (json.load(open(files[-1], encoding='utf-8'))['rows'] if files else []):
        if r['isin'] == isin:
            return r
    return None


def legal_name(isin):
    row = _roster_row(isin)
    if not row:
        return None
    if row.get('lei'):
        try:
            j = requests.get('https://api.gleif.org/api/v1/lei-records/' + row['lei'], headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()
            return j['data']['attributes']['entity']['legalName']['name']
        except Exception:
            pass
    return row['name']


def _pages(ep, term, a, b):
    page, out = 0, []
    while True:
        j = _post(ep, {'startDate': a + 'T00:00:00.000Z', 'endDate': b + 'T23:59:59.000Z', 'page': page, 'firstLetter': '', 'companyName': term})
        out += j.get('records') or []
        page += 1
        if page >= int(j.get('numberOfPages') or 0):
            return out


def fetch(isin_or_issuer, since=None, include_ris=True):
    q = (isin_or_issuer or '').strip()
    name = legal_name(q) if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', q) else q
    if not name:
        return []
    key = _norm(name)
    term = key.split()[0] if key else name       # substring search on the first core word, then exact match on the normalised name
    a = since or (dt.date.today() - dt.timedelta(days=365)).isoformat()
    b = dt.datetime.now(dt.timezone.utc).date().isoformat()
    out = []
    for r in _pages('OAMs', term, a, b):
        if _norm(r.get('companyName')) != key:
            continue
        docs = r.get('documents') or []
        out.append({'date': r.get('publishTime') or r.get('filingDate'), 'type': r.get('regulatoryCategoryDescription') or r.get('regulatoryCategory'),
                    'title': (r.get('headline') or '').strip(), 'url': (BASE + 'OAMDocument/' + docs[0]['name'] + '?id=' + docs[0]['id']) if docs else None,
                    'source': 'Euronext Dublin OAM', 'filer': r.get('companyName'), 'filing_date': r.get('filingDate'),
                    'documents': [BASE + 'OAMDocument/' + d['name'] + '?id=' + d['id'] for d in docs]})
    if include_ris:
        for r in _pages('RIS', term, a, b):
            if _norm(r.get('companyName')) != key:
                continue
            docs = r.get('documents') or []
            out.append({'date': r.get('releaseDate'), 'type': 'RIS announcement', 'title': (r.get('headLine') or '').strip(),
                        'url': (BASE + 'RISDocument/' + docs[0]['name'] + '?id=' + docs[0]['id']) if docs else None,
                        'source': 'Euronext Dublin RIS feed', 'filer': r.get('companyName'),
                        'documents': [BASE + 'RISDocument/' + d['name'] + '?id=' + d['id'] for d in docs]})
    out.sort(key=lambda e: e['date'] or '', reverse=True)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    since = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=365)).isoformat()
    tests = ['IE00BYTBXV33', 'IE0004906560', 'IE0004927939']   # Ryanair Holdings, Kerry Group, Kingspan Group
    res = {}
    for t in tests:
        ev = fetch(t, since)
        n = legal_name(t)
        res[t] = {'issuer_name': n, 'count': len(ev), 'count_oam': sum(1 for e in ev if e['source'].endswith('OAM')), 'events': ev}
        print(t, n, len(ev), 'oam', res[t]['count_oam'], (ev[0]['date'], ev[0]['type'], ev[0]['title']) if ev else '')
    out = {'source_url': BASE + 'OAMs (+ RIS)', 'read_by': 'eu-sources/ie/events.py', 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
           'since': since, 'issuers': res}
    p = os.path.join(HERE, 'samples', 'events-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', p)
