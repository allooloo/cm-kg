"""Jersey Width 1 events - TISE market news per issuer (the exchange's own announcement store).

Store: TISE Market News (https://tisegroup.com/market/news), data from POST https://tisegroup.com/api/news; per issuer the
security page uses POST https://tisegroup.com/api/companynews
  {"PageIndex","PageSize","IssuerSearch": <issuer mnemonic>, "SubfundSearch": <sub-fund mnemonic or null>, "IncludeNavs": false}
(issuer mnemonic, not text search). Each item: Id, PublishedAt (UTC), Headline {Text, Category, Code, FsaCode}, Text, Files.
Item page: https://tisegroup.com/market/news/<Id>.  NAV publications are excluded (IncludeNavs false) - they are prices.
The JFSC runs no per-issuer disclosure store for TISE issuers; TISE's news service is the official one.

Fields: type = Headline.Code (the store's own code, e.g. AOL-CISX, SUS, BOA, IR); type_en = Headline.Category (the store's
own English category for the code, e.g. "TISE Announcements", "Financial Statements, Dividends & Corporate Actions");
title = Headline.Text as published. The store is English.

fetch(isin_or_issuer, since) -> [{"date","type","type_en","title","url","source"}]
  isin_or_issuer: an ISIN or TISE security mnemonic (resolved through the roster), or an issuer mnemonic.
Usage: python events.py [ISIN|mnemonic ...]  writes samples/events-<date>.json
"""
import os, sys, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tisehttp

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = 'TISE market news (tisegroup.com /api/companynews)'
_ROSTER = [None]


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
    """-> (issuer_mnemonic, subfund_mnemonic or None)"""
    q = str(q).strip()
    for key in ('isin', 'ticker'):
        for r in _roster():
            if (r.get(key) or '').upper() == q.upper():
                return r['issuer_mnemonic'], r.get('subfund_mnemonic')
    for r in _roster():
        if (r.get('issuer_mnemonic') or '').upper() == q.upper() or (r.get('name') or '').casefold() == q.casefold():
            return r['issuer_mnemonic'], None
    return q.upper(), None   # treat as an issuer mnemonic


def fetch(isin_or_issuer, since, issuer_level=True):
    """issuer_level: True reads the whole issuer's news (umbrella and sub-funds); False narrows to the security's sub-fund."""
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    iss, sub = resolve(isin_or_issuer)
    out, p = [], 1
    while True:
        j = tisehttp.call('/api/companynews', {'PageIndex': p, 'PageSize': 100, 'IssuerSearch': None if (sub and not issuer_level) else iss,
                                               'SubfundSearch': sub if (sub and not issuer_level) else None, 'IncludeNavs': False}) or {}
        items = j.get('News') or []
        stop = False
        for n in items:
            d = datetime.datetime.fromisoformat(n['PublishedAt'])
            if d.astimezone(datetime.timezone.utc).date() < since:
                stop = True; break
            h = n.get('Headline') or {}
            out.append({'date': d.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'type': h.get('Code'), 'type_en': h.get('Category'),
                        'title': h.get('Text'), 'url': f'https://tisegroup.com/market/news/{n["Id"]}', 'source': SOURCE,
                        'issuer': (n.get('Issuer') or {}).get('Name'), 'subfund': (n.get('SubFund') or {}).get('Name') if n.get('SubFund') else None,
                        'files': [f.get('Url') or f.get('Name') for f in (n.get('Files') or []) if isinstance(f, dict)] or None})
        pg = j.get('Pagination') or {}
        if stop or not items or p >= (pg.get('TotalPages') or 0):
            break
        p += 1
    return out


if __name__ == '__main__':
    tests = sys.argv[1:] or ['JE00B4ZV0618', 'JE00BN6MDQ78', 'JE00BTGQPZ41']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': 'https://tisegroup.com/market/news', 'endpoint': 'POST https://tisegroup.com/api/companynews (IssuerSearch=<issuer mnemonic>, IncludeNavs=false)',
           'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': since.isoformat(), 'key_required': False, 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        iss, sub = resolve(q)
        name = next((r['name'] for r in _roster() if r.get('isin') == q or r.get('ticker') == q), q)
        res['issuers'][q] = {'issuer': name, 'issuer_mnemonic': iss, 'count': len(ev),
                             'by_type': {k: sum(1 for e in ev if e['type'] == k) for k in sorted({e['type'] or '' for e in ev})}, 'events': ev}
        print(q, name, iss, len(ev), res['issuers'][q]['by_type'], flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
