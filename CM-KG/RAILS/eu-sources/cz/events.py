"""CZ Width 1 events: issuer filings for Prague-listed issuers.

Intended primary (the Czech OAM): Czech National Bank, Centrální úložiště regulovaných informací (Central Storage of
  Regulated Information), application https://oam.cnb.cz/sipresextdad/SIPRESWEB.WEB21.START_INPUT_OAM?p_lang=en
  (linked from https://www.cnb.cz/en/supervision-financial-market/the-central-storage-of-regulated-information/).
  On 2026-10-24 that host refused TCP connections on 443 and timed out on 80, from two separate networks, so no
  endpoint could be mapped. fetch() probes it first and records the result in every row's 'source' note; the
  OAM parser is NOT built (blocker, see README). No registration key is advertised for public reading.
Working fallback (exchange, official, no key):
  a) PSE news API, exchange-authored items for one ISIN:
     https://www.pse.cz/api/news?lang=<cs|en>&type=PSE&page=<n>&homepage=0&searchKey=&dateFrom=&dateTo=&isin=<ISIN>
     (JSON; the PSE site's own front end sends the static header X-API-Key: PSE, a fixed public value written in the
     site's JavaScript, not a credential issued to anyone). type = the store's own 'type' field (PSE).
  b) PSE issuer reports API (periodic regulated reports the issuer filed with the exchange: annual/half-year/quarterly
     reports, preliminary results): https://www.pse.cz/api/file-reports?isin=<ISIN>
     These carry the report year only, not a filing day: date = 'YYYY'. type = the report label as filed (Czech).
  Press-agency (ČTK) items on the same API are excluded: they are not issuer or exchange publications.
"""
import datetime as dt, json, os, socket, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'application/json', 'X-API-Key': 'PSE'}
OAM_HOST, OAM_URL = 'oam.cnb.cz', 'https://oam.cnb.cz/sipresextdad/SIPRESWEB.WEB21.START_INPUT_OAM?p_lang=en'
NEWS = 'https://www.pse.cz/api/news'
REPORTS = 'https://www.pse.cz/api/file-reports'
_S = requests.Session(); _S.headers.update(UA)


def _get(url, params=None):
    for i in range(4):
        try:
            r = _S.get(url, params=params, timeout=60)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f'unreachable: {url}')


def oam_status():
    try:
        socket.create_connection((OAM_HOST, 443), timeout=15).close()
        return 'reachable (parser not built)'
    except OSError as e:
        return f'unreachable ({e.__class__.__name__}: {e})'


def _news(isin, since, lang):
    out = []
    for page in range(1, 40):
        p = {'lang': lang, 'type': 'PSE', 'page': page, 'homepage': 0, 'searchKey': '', 'dateFrom': since, 'dateTo': '', 'isin': isin}
        data = (_get(NEWS, p).json() or {}).get('data') or []
        if not data:
            break
        for x in data:
            d = (x.get('publishedAt') or '')[:10]
            if d and d >= since and x.get('type') == 'PSE':
                out.append({'date': x['publishedAt'], 'type': 'PSE news', 'title': x.get('title'),
                            'url': f"https://www.pse.cz/{'novinky' if lang == 'cs' else 'en/news'}/{x.get('slug')}"})
        if min((x.get('publishedAt') or '9')[:10] for x in data) < since or len(data) < 10:
            break
    return out


def _reports(isin, since):
    j = _get(REPORTS, {'isin': isin}).json()
    out = []
    for year, items in ((j.get('result') or {}).get('data') or {}).items():
        if str(year) < since[:4]:
            continue
        for x in items:
            out.append({'date': str(year), 'type': x.get('label'), 'title': f"{x.get('label')} ({year})",
                        'url': f"https://www.pse.cz/detail/{isin}?do=download&path=" + (x.get('path') or x.get('ref') or '')})
    return out


def fetch(isin_or_issuer, since=None, lang='cs'):
    since = since or (dt.date.today() - dt.timedelta(days=365)).isoformat()
    isin = str(isin_or_issuer).strip().upper()
    oam = oam_status()
    rows = []
    for e in _news(isin, since, lang):
        rows.append(dict(e, source=f'PSE news API (exchange); CNB OAM {oam}'))
    for e in _reports(isin, since):
        rows.append(dict(e, source=f'PSE issuer reports API (exchange); CNB OAM {oam}'))
    return sorted(rows, key=lambda r: r['date'], reverse=True)


if __name__ == '__main__':
    since = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    tests = sys.argv[1:] or ['CZ0005112300', 'CZ0008019106', 'CZ0008040318']  # CEZ, Komercni banka, Moneta Money Bank
    out = {'source_url': NEWS + ' + ' + REPORTS, 'oam_url': OAM_URL, 'oam_status': oam_status(),
           'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'since': since, 'issuers': {}}
    for t in tests:
        ev = fetch(t, since)
        out['issuers'][t] = {'count': len(ev), 'events': ev}
        print(t, len(ev), flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', f'events-{dt.datetime.now(dt.timezone.utc).date().isoformat()}.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('OAM', out['oam_status'], '->', p)
