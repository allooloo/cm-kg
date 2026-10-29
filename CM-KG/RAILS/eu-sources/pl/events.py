"""Poland Width 1 events - issuer regulated information (ESPI and EBI reports) as published by GPW.

ESPI (Elektroniczny System Przekazywania Informacji) is the KNF-run channel by which issuers on the regulated market file
current and periodic reports; EBI (Elektroniczna Baza Informacji) is GPW's channel for NewConnect / Catalyst issuers.
GPW republishes both on its "ESPI/EBI reports" page (https://www.gpw.pl/espi-ebi-reports); the page loads its list with a
POST to https://www.gpw.pl/ajaxindex.php (action=GPWEspiReportUnion). searchText takes an ISIN, ticker or issuer name.
No key, no login. Report pages: https://www.gpw.pl/espi-ebi-report?geru_id=<id>.

Notes
- gpw.pl resets curl (schannel) connections; Python requests is answered. Be gentle: one request per page of 100.
- Titles are as filed (mostly Polish; some issuers file English titles). The list also carries a price/change column,
  which is discarded (no prices).
- Report kinds as the store categorises them: Current (RB, biezacy), Periodic/Quarterly/Half-yearly/Annual (P/Q/O/R).

fetch(isin_or_issuer, since) -> [{"date","type","title","url","source"}]
Usage: python events.py [ISIN ...]   (default: three large issuers) writes samples/events-<date>.json
"""
import re, sys, os, json, time, html, datetime
from urllib.parse import urljoin
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'https://www.gpw.pl/espi-ebi-reports'
AJAX = 'https://www.gpw.pl/ajaxindex.php'
SOURCE = 'GPW ESPI/EBI reports (gpw.pl, action=GPWEspiReportUnion)'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept-Language': 'en-US,en;q=0.9', 'X-Requested-With': 'XMLHttpRequest', 'Referer': PAGE}
LIMIT = 100
ITEM = re.compile(r'<li[^>]*>\s*<span class="date">([^<]*)</span>\s*<strong class="name">\s*<a href="([^"]+)">\s*(.*?)\s*</a>.*?<p>\s*(.*?)\s*</p>', re.S)


def _post(s, data):
    for i in range(4):
        try:
            r = s.post(AJAX, data=data, timeout=90)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(5 * (i + 1))
    raise RuntimeError('gpw.pl did not answer')


def _form(text, offset):
    return [('action', 'GPWEspiReportUnion'), ('start', 'ajaxSearch'), ('page', 'espi-ebi-reports'), ('format', 'html'), ('lang', 'EN'),
            ('letter', ''), ('offset', str(offset)), ('limit', str(LIMIT)), ('categoryRaports[]', 'ESPI'), ('categoryRaports[]', 'EBI'),
            ('typeRaports[]', 'RB'), ('typeRaports[]', 'P'), ('typeRaports[]', 'Q'), ('typeRaports[]', 'O'), ('typeRaports[]', 'R'),
            ('searchText', text), ('date', '')]


def fetch(isin_or_issuer, since):
    """since: 'YYYY-MM-DD' or date. Returns newest first."""
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    s = requests.Session(); s.headers.update(UA)
    out, seen, offset = [], set(), 0
    while True:
        t = _post(s, _form(isin_or_issuer, offset))
        items = ITEM.findall(t)
        if not items:
            break
        stop = False
        for dt, href, issuer, title in items:
            parts = [p.strip() for p in dt.split('|')]
            try:
                d = datetime.datetime.strptime(parts[0], '%d-%m-%Y %H:%M:%S')
            except ValueError:
                continue
            if d.date() < since:
                stop = True; break
            url = urljoin('https://www.gpw.pl/', html.unescape(href))
            if url in seen:
                continue
            seen.add(url)
            kind = parts[1] if len(parts) > 1 else ''; chan = parts[2] if len(parts) > 2 else ''; num = parts[3] if len(parts) > 3 else ''
            out.append({'date': d.strftime('%Y-%m-%dT%H:%M:%S') + '+local(Europe/Warsaw)', 'type': f'{chan} {kind}'.strip(),
                        'report_no': num, 'title': html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', title))).strip(),
                        'issuer': html.unescape(re.sub(r'\s+', ' ', issuer)).strip(), 'url': url, 'source': SOURCE})
        if stop or len(items) < LIMIT:
            break
        offset += LIMIT
        time.sleep(1)
    return out


if __name__ == '__main__':
    tests = sys.argv[1:] or ['PLPKO0000016', 'PLPKN0000018', 'PLPZU0000011']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': PAGE, 'endpoint': AJAX + ' (POST action=GPWEspiReportUnion, searchText=<ISIN>)', 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'since': since.isoformat(), 'key_required': False, 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        res['issuers'][q] = {'count': len(ev), 'by_type': {k: sum(1 for e in ev if e['type'] == k) for k in sorted({e['type'] for e in ev})}, 'events': ev}
        print(q, len(ev), res['issuers'][q]['by_type'], flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
