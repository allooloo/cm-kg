"""Austria halts - trading suspensions on Wiener Boerse, from the exchange's own notices.

Wiener Boerse publishes no standing "currently suspended" table; each suspension, resumption and delisting is a
"Vienna Stock Exchange News" item (https://www.wienerborse.at/en/news/vienna-stock-exchange-news/). This reader posts the
public news search form (news_source=2 = Vienna Stock Exchange News, date window) on https://www.wienerborse.at/en/news-1/,
pages through it, keeps titles about suspension / resumption / delisting, and takes an instrument as currently halted when
its latest such notice is a suspension with no later resumption or delisting. ISIN and reason are read from the notice page.
The FMA (fma.gv.at) can also order suspensions; those are announced by Wiener Boerse in the same feed.

fetch(months=24) -> {"source_url", "count", "halted": [{"isin","ticker","name","since","reason","notice_url"}], "notices_read"}
Usage: python halt.py [months=24]   writes samples/halts-<date>.json
"""
import re, sys, os, json, time, html, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://www.wienerborse.at'
FORM = SITE + '/en/news-1/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
ROW = re.compile(r'<div class="datetime">\s*([^<]+?)\s*<span[^>]*>.*?</span>\s*([0-9/]+, [0-9:]+)\s*</div>\s*<div class="header-shorten"><a href="([^"]+)"[^>]*>(.*?)</a>', re.S)
KEY = re.compile(r'suspen|resum|delist|aussetz|wiederaufnahme', re.I)


def _text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def notices(months=24, max_pages=80):
    s = requests.Session(); s.headers.update(UA)
    r = s.get(FORM, timeout=60); r.raise_for_status()
    csrf = re.search(r'name="_csrf" value="([^"]+)"', r.text).group(1)
    today = datetime.date.today(); start = today - datetime.timedelta(days=31 * months)
    data = {'_csrf': csrf, 'news_string': '', 'news_isin': '', 'news_source': '2', 'date_from': start.strftime('%m/%d/%Y'), 'date_to': today.strftime('%m/%d/%Y')}
    out, seen = [], set()
    for p in range(1, max_pages + 1):
        r = s.post(f'{FORM}?c93603-page={p}&per-page=25', data=data, timeout=60)
        rows = ROW.findall(r.text)
        new = [x for x in rows if x[2] not in seen]
        if not new:
            break
        for src, dt, href, title in new:
            seen.add(href)
            out.append({'source': src, 'datetime': datetime.datetime.strptime(dt, '%m/%d/%Y, %H:%M:%S').isoformat(), 'title': _text(title), 'url': href if href.startswith('http') else SITE + href})
        time.sleep(0.3)
    return out, s


def _subject(title):
    return title.split(':', 1)[0].strip().lower()


def _kind(title):
    t = title.lower()
    if 'delist' in t:
        return 'delisting'
    if 'resum' in t or 'wiederaufnahme' in t or 'lifting' in t:
        return 'resumption'
    return 'suspension'


def _read_notice(s, url):
    page = s.get(url, timeout=60).text
    i = page.find('<h1'); j = page.find('Disclaimer', i)
    body = _text(page[i:j if j > i else i + 8000]) if i >= 0 else ''
    return body, sorted(set(re.findall(r'([A-Z]{2}[A-Z0-9]{9}[0-9])', body)))


def fetch(months=24):
    allnews, s = notices(months)
    rel = sorted([n for n in allnews if KEY.search(n['title'])], key=lambda n: n['datetime'])
    state = {}  # isin -> (kind, notice, body)
    for n in rel:
        body, isins = _read_notice(s, n['url'])
        kind = _kind(n['title'])
        # A suspension notice that already points to its resumption / delisting notice is resolved.
        if kind == 'suspension' and re.search(r'Details on the (trading resumption|resumption|delisting)', body, re.I):
            kind = 'resolved-in-notice'
        for isin in isins or ['?' + _subject(n['title'])]:
            state[isin] = (kind, n, body)
        time.sleep(0.2)
    halted = []
    for isin, (kind, n, body) in state.items():
        if kind != 'suspension':
            continue
        m = re.search(r'Reason:?\s*(.*?)(All (existing|exchange) orders|Details on|$)', body)
        m2 = re.search(r'([^.]*suspended[^.]*\.)\s*(.*?)(All (existing|exchange) orders|$)', body)
        reason = (m.group(1) if m else (m2.group(2) or m2.group(1)) if m2 else '').strip()
        halted.append({'isin': isin if not isin.startswith('?') else '', 'ticker': '', 'name': n['title'].split(':', 1)[0].strip(), 'since': n['datetime'][:10],
                       'reason': reason[:400], 'page': n['url'], 'notice_title': n['title'], 'notice_url': n['url']})
    oldest = min((n['datetime'] for n in allnews), default='')
    return {'source_url': FORM + ' (news_source=2 Vienna Stock Exchange News)',
            'read_by': 'DERIVED from Wiener Boerse notices: Vienna Stock Exchange News search, titles about suspension / resumption / delisting, '
                       'latest notice per ISIN (Wiener Boerse publishes no standing current-suspensions table)', 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'window_months': months, 'notices_read': len(allnews), 'oldest_notice_read': oldest, 'suspension_notices': len(rel), 'count': len(halted),
            'halted': sorted(halted, key=lambda h: h['since']),
            'method': 'per ISIN, the latest suspension / resumption / delisting notice; halted = latest is a suspension that does not point to its own resumption or delisting'}


if __name__ == '__main__':
    months = int(next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('months=')), 24))
    res = fetch(months)
    fn = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('notices', res['notices_read'], 'suspension-related', res['suspension_notices'], 'halted', res['count'])
    for h in res['halted']:
        print(' ', h['since'], h['isin'], h['name'], '|', h['reason'][:90])
    print('->', fn)
