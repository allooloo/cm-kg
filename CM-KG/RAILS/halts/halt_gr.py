"""GR halts: shares whose trading on Euronext Athens is currently suspended.

Source : Euronext Athens market notices (the exchange's own announcements as market operator)
         https://athens.euronext.com/en/more-options/announcements?search_api_fulltext=suspension&page=<n>
         The exchange publishes no standing "suspended securities" list that a server can read, so the list is derived:
         every notice whose title is a suspension / continuation of suspension / lift of suspension is grouped by the
         company named in the title; a company whose most recent such notice is not a lift is reported as halted.
         'since' = date of the first suspension notice of the current (unlifted) spell; 'reason' = the notice text's
         text of the latest notice of the spell (truncated to 600 characters); ISIN from the notice text when printed there, else from the
         roster sample by name. Public, no login, no key.
Limits : a temporary intraday suspension lifted the same day without a separate lift notice would look open; the
         reader therefore drops spells opened by a 'Temporary Suspension' notice older than 3 days with no
         continuation notice. Delisting procedures that start with a suspension stay listed until a lift is published.
"""
import datetime as dt, glob, html, json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
BASE = 'https://athens.euronext.com'
LIST = BASE + '/en/more-options/announcements'
_S = requests.Session(); _S.headers.update(UA)


def _get(url, params=None):
    for i in range(4):
        try:
            r = _S.get(url, params=params, timeout=90)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f'unreachable: {url}')


def _text(h):
    i = h.find('<main'); h = h[i:] if i > 0 else h
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()


def _body(h, title):
    """Notice text between its own heading and the page footer."""
    t = _text(h)
    end = t.find('STAY INFORMED')
    t = t[:end] if end > 0 else t
    k = t.lower().rfind(title.lower()[:40])
    return (t[k + len(title):] if k >= 0 else t).strip()


def notices(years=3, max_pages=15):
    cutoff = (dt.date.today() - dt.timedelta(days=365 * years)).isoformat()
    out = []
    for page in range(max_pages):
        t = _get(LIST, {'search_api_fulltext': 'suspension', 'page': page}).text
        rows = re.findall(r'views-field-title"[^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>.*?datetime="([^"]+)"', t, re.S)
        if not rows:
            break
        for href, title, when in rows:
            out.append({'url': BASE + href, 'title': html.unescape(re.sub(r'<[^>]+>', '', title)).strip(), 'date': when})
        if min(r[2][:10] for r in rows) < cutoff:
            break
    return [n for n in out if n['date'][:10] >= cutoff]


def _kind(title):
    t = title.lower()
    if 'suspension' not in t:
        return None
    if re.search(r'\blift|\blifting|resumption|cancell?ation', t):
        return 'lift'
    if 'continuation' in t:
        return 'continue'
    return 'temporary' if 'temporary' in t else 'suspend'


def _company(title):
    m = re.search(r'(?:shares of|trading of|trading in)\s+(?:the\s+)?(?:shares of\s+)?(?:the\s+)?(?:company\s+)?(.+)$', title, re.I)
    c = (m.group(1) if m else title).strip(' "“”.')
    return re.sub(r'\s+', ' ', c).upper()


def _roster():
    for p in sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')), reverse=True):
        return json.load(open(p, encoding='utf-8'))['rows']
    return []


def fetch():
    ns = [dict(n, kind=_kind(n['title'])) for n in notices()]
    ns = [n for n in ns if n['kind']]
    by = {}
    for n in sorted(ns, key=lambda x: x['date']):
        by.setdefault(_company(n['title']), []).append(n)
    roster, halted = _roster(), []
    today = dt.date.today()
    for comp, seq in by.items():
        if seq[-1]['kind'] == 'lift':
            continue
        spell = []
        for n in seq:
            spell = [] if n['kind'] == 'lift' else spell + [n]
        if spell[0]['kind'] == 'temporary' and len(spell) == 1 and (today - dt.date.fromisoformat(spell[0]['date'][:10])).days > 3:
            continue
        body = _body(_get(spell[-1]['url']).text, spell[-1]['title'])
        isins = re.findall(r'\b([A-Z]{2}[A-Z0-9]{9}[0-9])\b', body)
        isin = next((i for i in isins if i[:2] in ('GR', 'CY', 'LU', 'BE', 'CH', 'IE', 'MH', 'NL', 'AT', 'US', 'GB')), None)
        row = next((r for r in roster if r['isin'] == isin), None) if isin else None
        if not row:
            key = set(re.findall(r'[A-Z]{3,}', comp)) - {'THE', 'COMPANY', 'SHARES'}
            row = next((r for r in roster if key and key <= set(re.findall(r'[A-Z]{3,}', (r['name'] or '').upper()))), None)
        sent = body
        halted.append({'isin': isin or (row or {}).get('isin'), 'ticker': (row or {}).get('ticker'), 'name': comp.title(),
                       'since': spell[0]['date'], 'reason': sent[:600], 'notice_url': spell[-1]['url'], 'notices': len(spell)})
    return {'source_url': LIST + '?search_api_fulltext=suspension', 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'method': 'derived from market notices (suspension / continuation / lift)', 'notices_read': len(ns),
            'count': len(halted), 'halted': halted}


if __name__ == '__main__':
    out = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', f'halts-{dt.datetime.now(dt.timezone.utc).date().isoformat()}.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('halted', out['count'], [(h['ticker'], h['name'], h['since'][:10]) for h in out['halted']], '->', p)

# DAY ORDER 4: the read-by label of record (the node's halt flag names its source, not a file)
_fetch_src = fetch
def fetch():
    h = _fetch_src(); h["read_by"] = "Euronext Athens market notices (trading suspensions and resumptions)"; return h
