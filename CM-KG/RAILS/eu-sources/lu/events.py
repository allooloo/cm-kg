"""Luxembourg Width 1 events - regulated information filed with the LuxSE OAM (Officially Appointed Mechanism, Transparency Law).

Source of record: the OAM search on www.luxse.com ("OAM search", https://www.luxse.com/issuer-services-overview/oam), read through the
public GraphQL endpoint the site itself calls (https://graphqlaz.luxse.com/v1/graphql; no key, no login):
  oamSubmissionsSearch(issuerName | isin, publicationStartDate, publicationEndDate, pageSize, pageNumber[1-based]) -> submissions
  oamSubmissionDetail(submissionId) -> documents (fileName, url token, category, obsolete)
A document's download link is https://dl.luxse.com/dl?v=<url token> (served as application/pdf).

Per issuer: pass an ISIN or an issuer name. The OAM ISIN filter only matches securities known to the OAM record of the issuer; when an
ISIN gives no hit, the issuer's FIRDS full name (from samples/roster-*.json or the FIRDS cache) is used as issuerName (legal-form suffix
stripped). Per day: fetch(None, since=date, until=date) returns every OAM filing of that window.

fetch(isin_or_issuer, since, until=None, documents=True) -> [{"date","type","title","url","source", ...}]
  date  = OAM publication date (UTC, YYYY-MM-DD); type = OAM submission type label as categorised by the OAM;
  title = the filed document's name (falls back to the type when a submission carries no document); url = the document download link.
Usage: python events.py            -> 3 test issuers, 12 months, writes samples/events-<date>.json
       python events.py <ISIN|name> [since YYYY-MM-DD]
"""
import os, re, sys, json, glob, zipfile, datetime
import xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
GQL = 'https://graphqlaz.luxse.com/v1/graphql'
DL = 'https://dl.luxse.com/dl?v='
SOURCE = 'LuxSE OAM (www.luxse.com OAM search; graphqlaz.luxse.com oamSubmissionsSearch)'
HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
       'Content-Type': 'application/json', 'Origin': 'https://www.luxse.com', 'Referer': 'https://www.luxse.com/'}
Q_SEARCH = """query($issuerName: String, $isin: String, $publicationStartDate: Date, $publicationEndDate: Date, $pageSize: Int, $pageNumber: Int) {
 oamSubmissionsSearch(issuerName: $issuerName, isin: $isin, publicationStartDate: $publicationStartDate, publicationEndDate: $publicationEndDate,
  pageSize: $pageSize, pageNumber: $pageNumber) { totalHits submissions { submissionId submissionTypeLabel actionsList publicationDate
  referenceYear referenceStartDate referenceEndDate issuerName } } }"""
Q_DETAIL = """query($submissionId: Float!) { oamSubmissionDetail(submissionId: $submissionId) {
 documents { fileName url size publicationDate category obsolete } } }"""
ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
LEGAL = re.compile(r'[\s,]+(S\.?A\.?|S\.?A\.?R\.?L\.?|SE|AG|N\.?V\.?|PLC|LTD|LIMITED|SCA|S\.?C\.?A\.?|INC\.?|CORP\.?|GMBH)\.?$', re.I)
session = requests.Session()


def _post(query, variables):
    r = session.post(GQL, headers=HDR, json={'query': query, 'variables': variables}, timeout=90)
    r.raise_for_status()
    j = r.json()
    if j.get('errors'):
        raise RuntimeError(j['errors'][0].get('message', 'GraphQL error'))
    return j['data']


def search(issuer_name=None, isin=None, since=None, until=None, page_size=100):
    out, page = [], 1
    while True:
        v = {'pageSize': page_size, 'pageNumber': page}
        if issuer_name: v['issuerName'] = issuer_name
        if isin: v['isin'] = isin
        if since: v['publicationStartDate'] = since
        if until: v['publicationEndDate'] = until
        d = _post(Q_SEARCH, v)['oamSubmissionsSearch']
        out += d['submissions']
        if not d['submissions'] or len(out) >= d['totalHits']:
            return d['totalHits'], out
        page += 1


def documents(submission_id):
    return _post(Q_DETAIL, {'submissionId': float(submission_id)})['oamSubmissionDetail'].get('documents') or []


def firds_name(isin):
    """Issuer full name for an ISIN from the local FIRDS roster sample or the FIRDS cache (no network)."""
    for f in sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')), reverse=True):
        for r in json.load(open(f, encoding='utf-8'))['rows']:
            if r['isin'] == isin:
                return r['name']
    cache = os.environ.get('FIRDS_CACHE', os.path.join(HERE, '..', 'at', 'cache'))
    for fn in sorted(glob.glob(os.path.join(cache, 'FULINS_E_*.zip'))):
        z = zipfile.ZipFile(fn)
        for _, el in ET.iterparse(z.open(z.namelist()[0]), events=('end',)):
            if el.tag.endswith('}FinInstrmGnlAttrbts'):
                ns = el.tag.split('}')[0] + '}'
                if el.findtext(ns + 'Id') == isin:
                    return (el.findtext(ns + 'FullNm') or '').strip()
                el.clear()
            elif el.tag.endswith('}RefData'):
                el.clear()
    return None


def fetch(isin_or_issuer, since, until=None, docs=True):
    since = since or (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
    resolved = None
    if isin_or_issuer is None:
        total, subs = search(since=since, until=until)
    elif ISIN_RE.match(isin_or_issuer.upper()):
        total, subs = search(isin=isin_or_issuer.upper(), since=since, until=until)
        if total == 0:
            name = firds_name(isin_or_issuer.upper())
            if name:
                resolved = LEGAL.sub('', name).strip()
                total, subs = search(issuer_name=resolved, since=since, until=until)
    else:
        total, subs = search(issuer_name=isin_or_issuer, since=since, until=until)
    rows = []
    # the server's end-date bound is not strictly inclusive (a 2026-10-22..22 query returned 2026-10-23 items); bound it client-side
    subs = [s for s in subs if (s.get('publicationDate') or '')[:10] >= since and (not until or (s.get('publicationDate') or '')[:10] <= until)]
    for s in subs:
        ds = [d for d in (documents(s['submissionId']) if docs else []) if not d.get('obsolete')]
        first = ds[0] if ds else None
        rows.append({'date': (s.get('publicationDate') or '')[:10], 'type': s.get('submissionTypeLabel') or '',
                     'title': (first or {}).get('fileName') or s.get('submissionTypeLabel') or '',
                     'url': DL + first['url'] if first and first.get('url') else 'https://www.luxse.com/issuer-services-overview/oam',
                     'source': SOURCE, 'issuer': s.get('issuerName') or '', 'submission_id': s['submissionId'],
                     'documents': [{'name': d.get('fileName'), 'url': DL + d['url'], 'category': d.get('category')} for d in ds if d.get('url')],
                     'reference_period': [(s.get('referenceStartDate') or '')[:10], (s.get('referenceEndDate') or '')[:10]],
                     **({'resolved_issuer_name': resolved} if resolved else {})})
    return rows


if __name__ == '__main__':
    since = (datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=365)).isoformat()
    if len(sys.argv) > 1:
        rows = fetch(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else since)
        print(json.dumps(rows[:5], ensure_ascii=False, indent=1)); print('events', len(rows))
        sys.exit(0)
    tests = [('LU1598757687', 'ArcelorMittal'), ('LU0088087324', 'SES'), ('LU1673108939', 'Aroundtown')]
    out = {'source': SOURCE, 'endpoint': GQL, 'since': since, 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'issuers': {}}
    for isin, label in tests:
        rows = fetch(isin, since)
        by_type = {}
        for r in rows:
            by_type[r['type']] = by_type.get(r['type'], 0) + 1
        out['issuers'][isin] = {'label': label, 'count': len(rows), 'by_type': by_type, 'events': rows}
        print(isin, label, len(rows), by_type)
    day = (datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)).isoformat()
    day_rows = fetch(None, day, day, docs=False)
    out['per_day_check'] = {'date': day, 'count': len(day_rows)}
    print('per-day', day, len(day_rows))
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    fn = os.path.join(HERE, 'samples', f"events-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json")
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', fn)
