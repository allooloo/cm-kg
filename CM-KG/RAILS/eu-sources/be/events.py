"""Belgium events (Width 1): issuer filings from FSMA STORI (www.fsma.be/en/stori), the Belgian Officially Appointed Mechanism for the
central storage of regulated information, run by the national regulator. The STORI page is a Vue app over a public JSON API, no key:
  POST https://webapi.fsma.be/api/v1/en/stori/result   {"startRowIndex","pageSize","sortDirection","isinCode"|"companyName"|"companyId",
                                                         "publicationStart","publicationEnd"}
  GET  https://webapi.fsma.be/api/v1/en/stori/companies/abbreviated-name   (issuer list)
  GET  https://webapi.fsma.be/api/v1/en/stori/document-type                (STORI categories)
  GET  https://webapi.fsma.be/api/v1/en/stori/download?fileDataId=<id>     (the filed document)
Search is by full ISIN (isinCode) or by issuer name (companyName, partial / historical names allowed).

fetch(isin_or_issuer, since) -> [{"date", "type", "title", "url", "source", ...}]
  "type" = STORI reportingTopicName (as the store categorises); "title" = the filed documentTitle, else the English (or first) main document title.
Run: python events.py  -> samples/events-<date>.json for AB InBev, KBC, UCB.
"""
import datetime as dt, json, os, re, sys, time
import requests

API = 'https://webapi.fsma.be/api/v1/en/stori/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'application/json', 'Origin': 'https://www.fsma.be', 'Referer': 'https://www.fsma.be/en/stori'}
HERE = os.path.dirname(os.path.abspath(__file__))


def _post(body, tries=4):
    for i in range(tries):
        try:
            r = requests.post(API + 'result', json=body, headers=UA, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            r.raise_for_status(); return r.json()
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _title(item):
    if (item.get('documentTitle') or '').strip():
        return item['documentTitle'].strip()
    docs = item.get('mainDocuments') or []
    en = [d for d in docs if d.get('language') == 'en'] or docs
    return (en[0].get('title') or en[0].get('originalFileName')) if en else ''


def fetch(isin_or_issuer, since=None):
    q = (isin_or_issuer or '').strip()
    a = since or (dt.date.today() - dt.timedelta(days=365)).isoformat()
    body = {'startRowIndex': 0, 'pageSize': 100, 'sortDirection': 'Descending', 'publicationStart': a,
            'publicationEnd': dt.datetime.now(dt.timezone.utc).date().isoformat()}
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', q):
        body['isinCode'] = q
    else:
        body['companyName'] = q
    items, total = [], None
    while total is None or len(items) < total:
        j = _post(body)
        total = int(j.get('resultCount') or 0)
        page = j.get('storiResultItems') or []
        if not page:
            break
        items += page
        body['startRowIndex'] += len(page)
    out = []
    for it in items:
        docs = it.get('mainDocuments') or []
        en = [d for d in docs if d.get('language') == 'en'] or docs
        out.append({'date': it.get('datePublication'), 'type': it.get('reportingTopicName'), 'title': _title(it),
                    'url': (API + 'download?fileDataId=' + en[0]['fileDataId']) if en else None, 'source': 'FSMA STORI (OAM)',
                    'issuer': it.get('companyName'), 'lei': it.get('lei'), 'company_number': it.get('companyNumber'), 'received': it.get('dateReceived'),
                    'languages': sorted({d.get('language') for d in docs if d.get('language')}),
                    'documents': [{'language': d.get('language'), 'title': d.get('title'), 'url': API + 'download?fileDataId=' + d['fileDataId']} for d in docs],
                    'attachments': len(it.get('attachments') or [])})
    out.sort(key=lambda e: e['date'] or '', reverse=True)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    since = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=365)).isoformat()
    tests = ['BE0974293251', 'BE0003565737', 'BE0003739530']   # AB InBev, KBC Group, UCB
    res = {}
    for t in tests:
        ev = fetch(t, since)
        res[t] = {'issuer_name': ev[0]['issuer'] if ev else None, 'count': len(ev), 'events': ev}
        print(t, res[t]['issuer_name'], len(ev), (ev[0]['date'], ev[0]['type'], ev[0]['title']) if ev else '')
    out = {'source_url': API + 'result', 'read_by': 'eu-sources/be/events.py', 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
           'since': since, 'issuers': res}
    p = os.path.join(HERE, 'samples', 'events-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', p)
