"""Bermuda Width 1 events - issuer filings as released by the BSX (the exchange's own store).

Store: the "Financial & Other Information" table on each BSX company page (https://www.bsx.com/company/<id>), one row
per filing: date posted (YYYY-MM-DD), title as released, document link (content.bsx.com/CompanyDocuments/<id>/...).
The same filings feed the BSX "News & Announcements" list (https://www.bsx.com/news, topic "Regulatory News"); the
company page is the per-issuer view, so no keyword search is used.  The BMA runs no public per-issuer disclosure store.
Category: the table carries no category code; every row is of the table's own heading "Financial & Other Information".
The store is English, so type_en = type.

fetch(isin_or_issuer, since) -> [{"date","type","type_en","title","url","source"}]
  isin_or_issuer: an ISIN or ticker (resolved through the roster), a BSX company id, or the issuer name exactly as listed.
Usage: python events.py [ISIN ...]  writes samples/events-<date>.json
"""
import os, re, sys, json, html, datetime
from urllib.parse import quote, urljoin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bsxhttp

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = 'BSX company page "Financial & Other Information" (bsx.com/company/<id>)'
TYPE = 'Financial & Other Information'
_ROSTER = [None]
ROW = re.compile(r'<td headers="view-dateposted-table-column"[^>]*>\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*</td>\s*<td headers="view-title-table-column"[^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>', re.S)


def _clean(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def _roster():
    if _ROSTER[0] is None:
        p = os.path.join(HERE, 'cache', 'roster-latest.json')
        if os.path.exists(p):
            _ROSTER[0] = json.load(open(p, encoding='utf-8'))['rows']
        else:
            import roster
            _ROSTER[0] = roster.fetch(with_lei=False)['rows']
    return _ROSTER[0]


def resolve(q):
    q = str(q).strip()
    if q.isdigit():
        return f'{bsxhttp.BASE}/company/{q}'
    for key in ('isin', 'ticker'):
        for r in _roster():
            if (r.get(key) or '').upper() == q.upper():
                return r['page']
    for r in _roster():
        if r['name'].casefold() == q.casefold():
            return r['page']
    return None


def fetch(isin_or_issuer, since):
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    page = resolve(isin_or_issuer)
    if not page:
        return []
    t = bsxhttp.text(page)
    i = t.find('Financial &amp; Other Information')
    out, seen = [], set()
    for d, href, title in ROW.findall(t[i:] if i >= 0 else t):
        dt = datetime.date.fromisoformat(d)
        if dt < since:
            continue
        url = quote(urljoin(bsxhttp.BASE + '/', html.unescape(href)), safe=':/?&=%#')
        if url in seen:
            continue
        seen.add(url)
        out.append({'date': d, 'type': TYPE, 'type_en': TYPE, 'title': _clean(title), 'url': url, 'source': SOURCE, 'company_page': page})
    out.sort(key=lambda e: e['date'], reverse=True)
    return out


if __name__ == '__main__':
    tests = sys.argv[1:] or ['BMG0772R2087', 'BMG507361001', 'BMG948001026']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': 'https://www.bsx.com/listed-securities', 'endpoint': 'https://www.bsx.com/company/<id> (Financial & Other Information table)',
           'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': since.isoformat(), 'key_required': False, 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        name = next((r['name'] for r in _roster() if r.get('isin') == q), q)
        res['issuers'][q] = {'issuer': name, 'company_page': resolve(q), 'count': len(ev), 'by_type': {TYPE: len(ev)} if ev else {}, 'events': ev}
        print(q, name, len(ev), flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
