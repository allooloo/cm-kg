"""UAE Width 1 events - issuer disclosures filed on DFM's eFSAH disclosure platform (DFM and Nasdaq Dubai issuers).

Store: eFSAH, the feed behind https://www.dfm.ae/the-exchange/news-disclosures/disclosures and each company's News & Disclosures tab.
  GET https://api2.dfm.ae/efsah/v1/prototype_efsah?announcement_type=Disclosure&symbol=<SYMBOL>&lang=en&take=20&skip=<n>&cms_resources=true
  (newest first; the store serves at most 20 items per call, paged by skip). Keyless.
  Each item: id, publication_date (UAE local time), headline (title as filed), issuer_symbol, announcement_type (the store's category),
  report fields, resources (the filed PDF, served at https://feeds.dfm.ae/documents<r_path>).
  Item page: https://www.dfm.ae/the-exchange/news-disclosures/disclosures/<id>
Editions: DFM keeps an English and an Arabic edition of each filing as separate items (different ids). This reader reads the English
edition (lang=en); pass lang='ar' for the Arabic edition.
type = announcement_type as the store returns it; type_en = the same field from the English edition (the store's English label).
ADX issuers are not covered: ADX's disclosure store (apigateway.adx.ae) needs an ADX gateway key (see README).

fetch(isin_or_issuer, since) -> [{"date","type","type_en","title","url","source"}]
  isin_or_issuer: DFM symbol (e.g. EMAAR) or ISIN (resolved through the latest samples/roster-*.json, else a live roster read).
Usage: python events.py [SYMBOL|ISIN ...]   (default: EMAAR, EMIRATESNBD, DEWA) writes samples/events-<date>.json
"""
import os, re, sys, json, glob, time, datetime, urllib.parse
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://api2.dfm.ae/efsah/v1/prototype_efsah'
PAGE = 'https://www.dfm.ae/the-exchange/news-disclosures/disclosures'
DOCS = 'https://feeds.dfm.ae/documents'
SOURCE = 'DFM eFSAH disclosures (api2.dfm.ae/efsah/v1/prototype_efsah, announcement_type=Disclosure)'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'application/json', 'Origin': 'https://www.dfm.ae', 'Referer': PAGE}
TAKE = 20      # the store's page cap
GAP = 0.6
ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
_SYM = {}


def _get(params, tries=4):
    for i in range(tries):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=90)
            if r.status_code == 200:
                return json.loads(r.text.lstrip('﻿')).get('root') or []
        except (requests.RequestException, ValueError):
            pass
        time.sleep(4 * (i + 1))
    raise RuntimeError('api2.dfm.ae (efsah) did not answer')


def _symbol(q):
    if not ISIN_RE.match(q):
        return q
    if not _SYM:
        files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
        if files:
            rows = json.load(open(files[-1], encoding='utf-8'))['rows']
        else:
            sys.path.insert(0, HERE); import roster; rows = roster.fetch(with_lei=False)['rows']
        _SYM.update({r['isin']: r['ticker'] for r in rows if r.get('isin')})
    return _SYM.get(q)


def _date(s):
    return datetime.datetime.strptime(s.strip(), '%b %d, %Y %I:%M:%S %p')


def fetch(isin_or_issuer, since, lang='en'):
    """since: 'YYYY-MM-DD' or date. Newest first."""
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    sym = _symbol(isin_or_issuer)
    if not sym:
        return []
    out, seen, skip = [], set(), 0
    while True:
        items = _get({'announcement_type': 'Disclosure', 'symbol': sym, 'lang': lang, 'take': TAKE, 'skip': skip, 'cms_resources': 'true'})
        if not items:
            break
        stop = False
        for x in items:
            try:
                d = _date(x['publication_date'])
            except (KeyError, ValueError):
                continue
            if d.date() < since:
                stop = True; break
            if x['id'] in seen:
                continue
            seen.add(x['id'])
            docs = [DOCS + urllib.parse.quote(r['r_path']) for r in (x.get('resources') or []) if r.get('r_path')]
            out.append({'date': d.strftime('%Y-%m-%dT%H:%M:%S') + '+04:00', 'type': x.get('announcement_type') or '', 'type_en': x.get('announcement_type') or '',
                        'title': re.sub(r'\s+', ' ', x.get('headline') or '').strip(), 'url': f'{PAGE}/{x["id"]}', 'documents': docs,
                        'issuer': (x.get('issuer') or '').strip(), 'symbol': x.get('issuer_symbol'), 'report_interval': x.get('report_interval'),
                        'language': lang, 'source': SOURCE})
        if stop or len(items) < TAKE:
            break
        skip += TAKE
        time.sleep(GAP)
    return out


if __name__ == '__main__':
    tests = sys.argv[1:] or ['EMAAR', 'EMIRATESNBD', 'DEWA']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': PAGE, 'endpoint': API + ' (GET announcement_type=Disclosure&symbol=<SYMBOL>&lang=en&take=20&skip=<n>)',
           'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': since.isoformat(),
           'edition': 'English (lang=en); Arabic edition filed separately', 'key_required': False, 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        res['issuers'][q] = {'symbol': _symbol(q), 'count': len(ev), 'by_type': {k: sum(1 for e in ev if e['type'] == k) for k in sorted({e['type'] for e in ev})}, 'events': ev}
        print(q, len(ev), res['issuers'][q]['by_type'], flush=True)
        time.sleep(GAP)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
