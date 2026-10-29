"""IT events (Width 1): regulated information of Italian listed issuers from the two Consob-authorised storage mechanisms (SDIR / storage).
An Italian issuer files with ONE of them (and may switch), so both are read and merged. Public, no key:
  eMarket STORAGE (Teleborsa):   GET https://www.emarketstorage.it/it/comunicati-finanziari?azienda=<id>&data_from=YYYY-MM-DD&data_to=YYYY-MM-DD
                                     &categoria=<id>&page=<n>   (HTML, 24 per page; issuer ids from the "azienda" select on the same page)
                                 "type" = the eMarket category (Directive 2004/109 sub-class / REGEM / MANTRA ...): the list rows carry no
                                 category, so the reader runs one pass per category id and tags each protocol number; rows seen only in the
                                 unfiltered pass get type None.
  1INFO (Computershare):         POST https://www.1info.it/PORTALE1INFO/API/Comunicati  (DataTables server-side JSON; form fields
                                     draw/start/length/order/columns + SearchFilter[emittente][]=<ndg>, SearchFilter[dataDiffusione][from|to]=<epoch s>)
                                 issuers: GET .../API/companies/comunicatistoccati ; categories: GET .../API/comunicati/Categories
                                 document: https://www.1info.it/PORTALE1INFO/Pdf/Pdf?pdf=<pdf>&data=<year>&filetype=comunicati
                                 "type" = 1INFO category code + description as filed (e.g. "2.2 ... Informazioni privilegiate", "IRAG01 ...", "REGEM").
ISIN -> store issuer: FIRDS name and Borsa Italiana A-Z name from the latest samples/roster-*.json, matched to each store's issuer list after
removing legal-form words (S.p.A., N.V., Group, Holding ...). An issuer name may also be passed directly.
Titles are as filed (Italian and/or English; many issuers file both as separate items).

fetch(isin_or_issuer, since) -> [{"date", "type", "title", "url", "source", "store", "store_issuer", "protocol"}]
Run: python events.py  -> samples/events-<date>.json for Enel, Intesa Sanpaolo, Eni.
"""
import datetime as dt, glob, html, json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
EM = 'https://www.emarketstorage.it'
EM_LIST = EM + '/it/comunicati-finanziari'
ONE = 'https://www.1info.it/PORTALE1INFO'
EM_ROW = re.compile(r'data-protocollo="(\d+)".*?<time[^>]*class="datetime">([^<]*)</time>.*?news-azienda"><a[^>]*>([^<]*)</a>.*?'
                    r'news-title"><a href="([^"]*)"[^>]*>(.*?)</a>', re.S)
_cache = {}


def _req(method, url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.request(method, url, headers={**UA, **kw.pop('headers', {})}, timeout=120, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            r.raise_for_status(); return r
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(4 * (i + 1))


def _norm(s):
    s = html.unescape(s or '').lower()
    s = re.sub(r's\.\s*p\.\s*a\.?', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\b(spa|s p a|nv|n v|se|sa|plc|ag|group|gruppo|holding|holdings|company|co|societa|per azioni|the|siiq|sicaf)\b', ' ', s)
    return ' '.join(s.split())


def em_meta():
    if 'em' not in _cache:
        t = _req('GET', EM_LIST).text
        def opts(name):
            i = t.find('name="%s"' % name); seg = t[i:t.find('</select>', i)]
            return [(v, html.unescape(n).strip()) for v, n in re.findall(r'<option value="([^"]*)"[^>]*>([^<]*)', seg) if v and v != 'All']
        _cache['em'] = {'azienda': opts('azienda'), 'categoria': opts('categoria')}
    return _cache['em']


def one_meta():
    if 'one' not in _cache:
        comp = _req('GET', ONE + '/API/companies/comunicatistoccati').json()
        cats = _req('GET', ONE + '/API/comunicati/Categories').json()
        _cache['one'] = {'azienda': [(c['ndg'], c['descrizione'].strip()) for c in comp], 'categoria': {c['codice']: c['descrizione'].strip() for c in cats}}
    return _cache['one']


def names_for(isin_or_issuer):
    q = (isin_or_issuer or '').strip()
    cands = [q]
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', q):
        cands = []
        files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
        d = json.load(open(files[-1], encoding='utf-8')) if files else {'rows': []}
        for r in d['rows']:
            if r['isin'] == q:
                cands.append(r['name'])
        for line in (d.get('cross_check') or {}).get('exchange_only', []):
            if line.startswith(q):
                cands.append(line.split(' ', 2)[2])
    return {_norm(c) for c in cands if c}


def _em_pages(params):
    out, page = [], 0
    while True:
        t = _req('GET', EM_LIST, params=dict(params, page=page)).text
        rows = EM_ROW.findall(t)
        out += rows
        if len(rows) < 24 or not re.search(r'page=%d\b' % (page + 1), t):
            return out
        page += 1
        time.sleep(0.2)


def em_events(keys, a, b):
    out = []
    for aid, name in em_meta()['azienda']:
        if _norm(name) not in keys:
            continue
        base = {'azienda': aid, 'data_from': a.isoformat(), 'data_to': b.isoformat()}
        cat_of = {}
        for cid, cname in em_meta()['categoria']:
            for p, *_ in _em_pages(dict(base, categoria=cid)):
                cat_of[p] = cname
        for p, when, issuer, href, title in _em_pages(base):
            d = dt.datetime.strptime(when.strip(), '%d/%m/%Y - %H:%M')
            out.append({'date': d.strftime('%Y-%m-%d %H:%M'), 'type': cat_of.get(p), 'title': html.unescape(re.sub(r'<[^>]+>', '', title)).strip(),
                        'url': EM + href if href.startswith('/') else href, 'source': 'eMarket STORAGE (Consob-authorised storage)', 'store': 'emarket',
                        'store_issuer': html.unescape(issuer).strip(), 'protocol': p})
    return out


def one_events(keys, a, b):
    out = []
    cats = one_meta()['categoria']
    for ndg, name in one_meta()['azienda']:
        if _norm(name) not in keys:
            continue
        start = 0
        while True:
            data = {'draw': 1, 'start': start, 'length': 100, 'order[0][column]': 0, 'order[0][dir]': 'desc', 'columns[0][data]': 'data',
                    'SearchFilter[emittente][]': ndg, 'SearchFilter[sdir1info]': 'true', 'SearchFilter[sdirTerzi]': 'true',
                    'SearchFilter[dataDiffusione][from]': int(dt.datetime(a.year, a.month, a.day, tzinfo=dt.timezone.utc).timestamp()),
                    'SearchFilter[dataDiffusione][to]': int(dt.datetime(b.year, b.month, b.day, 23, 59, tzinfo=dt.timezone.utc).timestamp())}
            j = _req('POST', ONE + '/API/Comunicati', data=data, headers={'X-Requested-With': 'XMLHttpRequest'}).json()
            rows = [r for r in j.get('data') or [] if r.get('pdf')]
            for r in rows:
                ts = r.get('dataDiffusione') or r.get('data')
                d = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
                code = r.get('categoria')
                out.append({'date': d.strftime('%Y-%m-%d %H:%M'), 'type': cats.get(code, code), 'type_code': code, 'title': (r.get('oggetto') or '').strip(),
                            'url': ONE + '/Pdf/Pdf?pdf=%s&data=%s&filetype=comunicati' % (r['pdf'].replace('.pdf', ''), d.year),
                            'source': '1INFO (Consob-authorised storage, Computershare)', 'store': '1info', 'store_issuer': r.get('mittente'),
                            'protocol': r['pdf'], 'sdir': r.get('sdir')})
            start += 100
            if start >= int(j.get('recordsFiltered') or 0) or not rows:
                break
    return out


def fetch(isin_or_issuer, since=None):
    a = dt.date.fromisoformat(since) if since else dt.date.today() - dt.timedelta(days=365)
    b = dt.datetime.now(dt.timezone.utc).date()
    keys = names_for(isin_or_issuer)
    out = em_events(keys, a, b) + one_events(keys, a, b)
    out.sort(key=lambda e: e['date'], reverse=True)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    since = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=365)).isoformat()
    tests = ['IT0003128367', 'IT0000072618', 'IT0003132476']   # Enel, Intesa Sanpaolo, Eni
    res = {}
    for t in tests:
        ev = fetch(t, since)
        res[t] = {'match_keys': sorted(names_for(t)), 'count': len(ev), 'by_store': {s: sum(1 for e in ev if e['store'] == s) for s in ('emarket', '1info')},
                  'untyped': sum(1 for e in ev if not e['type']), 'events': ev}
        print(t, res[t]['match_keys'], len(ev), res[t]['by_store'], 'untyped', res[t]['untyped'], (ev[0]['date'], (ev[0]['type'] or '')[:40], ev[0]['title'][:70]) if ev else '')
    out = {'source_url': EM_LIST + ' | ' + ONE + '/API/Comunicati', 'read_by': 'eu-sources/it/events.py',
           'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'since': since, 'issuers': res}
    p = os.path.join(HERE, 'samples', 'events-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', p)
