"""Cayman Islands Width 1 events - CSX announcements per issuer (the exchange's own announcement store).

Store: CSX "Announcements" (https://www.csx.ky/companies/announcements.asp, data at /_data/Announcements.asp?SearchText=&Year=),
each announcement at https://www.csx.ky/companies/announcement.asp?Id=<id>.  Per issuer, the reader uses the list the CSX
itself links to the instrument: the "Related Announcements" tables on the instrument page (equity.asp / investment-fund.asp
?SecId=<id>), grouped by year, each row = release date + title as filed + announcement link.  No text search, no fuzzy match.
CIMA (the regulator) runs no public per-issuer disclosure store for CSX issuers; the CSX page is the official store.

Category: the CSX store has no category code.  type is read from the title's own form, exactly:
  "CSX Notice"           - exchange notices, titles starting "CSX " (CSX ADMITS / SUSPENDS / REINSTATES / CANCELS ...)
  "Company Announcement" - titles carrying "COMPANY ANNOUNCEMENT" (issuer filings released by the CSX)
  "Announcement"         - anything else
The store is English, so type_en = type.

fetch(isin_or_issuer, since) -> [{"date","type","type_en","title","url","source"}]
  isin_or_issuer: an ISIN (resolved through the roster's instrument pages), a CSX SecId, or the issuer name exactly as on the CSX list.
Usage: python events.py [ISIN|SecId ...]  writes samples/events-<date>.json
"""
import os, re, sys, json, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csxhttp

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = 'CSX announcements (csx.ky instrument page "Related Announcements")'
STORE = 'https://www.csx.ky/companies/announcements.asp'
_ROSTER = [None]


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
    """-> instrument page URL (first matching line), or None."""
    q = str(q).strip()
    rows = _roster()
    for key in ('isin', 'sec_id'):
        for r in rows:
            if (r.get(key) or '').upper() == q.upper():
                return r['page']
    for r in rows:
        if r['name'].casefold() == q.casefold():
            return r['page']
    return None


def classify(title):
    t = title.strip()
    if t.upper().startswith('CSX '):
        return 'CSX Notice'
    if 'COMPANY ANNOUNCEMENT' in t.upper():
        return 'Company Announcement'
    return 'Announcement'


def fetch(isin_or_issuer, since):
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    page = resolve(isin_or_issuer)
    if not page:
        return []
    t = csxhttp.text(page)
    i = t.find('Related Announcements')
    if i < 0:
        return []
    out, seen = [], set()
    for d, href, title in re.findall(r'<TR><TD[^>]*>([^<]+)</TD><TD><a[^>]*href=([^ >]+)>(.*?)</a>', t[i:], re.S | re.I):
        try:
            dt = datetime.datetime.strptime(d.strip(), '%d %b %Y').date()
        except ValueError:
            continue
        if dt < since:
            continue
        url = 'https://www.csx.ky' + href.strip('\'"') if href.startswith('/') else href.strip('\'"')
        if url in seen:
            continue
        seen.add(url)
        title = _clean(title); ty = classify(title)
        out.append({'date': dt.isoformat(), 'type': ty, 'type_en': ty, 'title': title, 'url': url, 'source': SOURCE, 'instrument_page': page})
    out.sort(key=lambda e: e['date'], reverse=True)
    return out


if __name__ == '__main__':
    tests = sys.argv[1:] or ['NL0010833307', 'KYG2957T1168', 'KYG0068P1063']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': STORE, 'endpoint': 'instrument page Related Announcements (https://www.csx.ky/companies/{equity|investment-fund}.asp?SecId=<id>)',
           'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': since.isoformat(), 'key_required': False, 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        name = next((r['name'] for r in _roster() if r.get('isin') == q or r.get('sec_id') == q), q)
        res['issuers'][q] = {'issuer': name, 'instrument_page': resolve(q), 'count': len(ev),
                             'by_type': {k: sum(1 for e in ev if e['type'] == k) for k in sorted({e['type'] for e in ev})}, 'events': ev}
        print(q, name, len(ev), res['issuers'][q]['by_type'], flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
