"""Denmark events (Width 1): issuer filings from Nasdaq Copenhagen company announcements (CNS). Danish OAM: Finanstilsynet's storage (oam.finanstilsynet.dk) receives the same regulated information.
Releases are distributed through Nasdaq's CNS news service, the same API Finland's reader uses (eu-sources/fi/events.py). Public JSON, no key:
  GET https://api.news.eu.nasdaq.com/news/query.action?type=json&globalName=NordicAllMarkets&company=<display name>&fromDate=<epoch ms>
      &toDate=<epoch ms>&limit=..&start=..&dir=DESC&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=true
  GET https://api.news.eu.nasdaq.com/news/metadata.action?globalName=NordicAllMarkets&resultType=company&market=<market>&type=json
      markets: ['Main Market, Copenhagen', 'First North Denmark']
fromDate / toDate are epoch milliseconds (a YYYY-MM-DD value is silently ignored). Message page (as filed): messageUrl (view.news.eu.nasdaq.com).

ISIN -> display names: the Nasdaq Copenhagen share list name (api.nasdaq.com/api/nordic/screener/shares?market=CPH) and the FIRDS name from the latest
samples/roster-*.json, matched against the metadata company list after removing legal-form suffixes.

fetch(isin_or_issuer, since) -> [{"date", "type", "title", "url", "source", "language", ...}]
  "type" = cnsCategory (Nasdaq's category as filed, e.g. "Inside information", "Interim report (Q1 and Q3)", "Changes in board/management/auditors").
  Releases are usually filed in Danish and English as separate items.
Run: python events.py  -> samples/events-<date>.json for the three test issuers below.
"""
import datetime as dt, glob, json, os, re, sys, time
import requests

NEWS = 'https://api.news.eu.nasdaq.com/news/'
SCREENER = 'https://api.nasdaq.com/api/nordic/screener/shares'
MARKETS = ['Main Market, Copenhagen', 'First North Denmark']
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
HERE = os.path.dirname(os.path.abspath(__file__))
_companies = None
_screener = None


def _get(url, params, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            r.raise_for_status(); return r.json()
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _norm(s):
    s = (s or '').lower()
    s = re.sub(r'[^a-z0-9åäöæø ]', ' ', s)
    s = re.sub(r'\b(oyj|abp|plc|corporation|corp|oy|ab|publ|ltd|se|sa|asa|inc|group|konserni|a|b|r|k|i|ii|ser|series|class)\b', ' ', s)
    return ' '.join(s.split())


def companies():
    global _companies
    if _companies is None:
        _companies = set()
        for m in MARKETS:
            j = _get(NEWS + 'metadata.action', {'globalName': 'NordicAllMarkets', 'resultType': 'company', 'market': m, 'type': 'json'})
            _companies |= {f['id'] for f in j.get('facts', [])}
    return _companies


def screener():
    global _screener
    if _screener is None:
        _screener = {}
        for cat in ('MAIN_MARKET', 'FIRST_NORTH'):
            j = _get(SCREENER, {'category': cat, 'tableonly': 'false', 'market': 'CPH'})
            for x in j['data']['instrumentListing']['rows']:
                _screener[x['isin']] = (x['symbol'], x['fullName'])
    return _screener


def names_for(isin_or_issuer):
    q = (isin_or_issuer or '').strip()
    cands = []
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', q):
        if q in screener():
            cands.append(screener()[q][1])
        files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
        for r in (json.load(open(files[-1], encoding='utf-8'))['rows'] if files else []):
            if r['isin'] == q:
                cands.append(r['name'])
    else:
        cands.append(q)
    keys = {_norm(c) for c in cands if c}
    return sorted(c for c in companies() if _norm(c) in keys)


def _ms(d):
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)


def fetch(isin_or_issuer, since=None):
    a = dt.date.fromisoformat(since) if since else dt.date.today() - dt.timedelta(days=365)
    b = dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)
    out, seen = [], set()
    for name in names_for(isin_or_issuer):
        start = 0
        while True:
            j = _get(NEWS + 'query.action', {'type': 'json', 'showAttachments': 'true', 'showCnsSpecific': 'true', 'showCompany': 'true', 'countResults': 'true',
                                             'globalName': 'NordicAllMarkets', 'company': name, 'fromDate': _ms(a), 'toDate': _ms(b), 'displayLanguage': 'en',
                                             'timeZone': 'CET', 'dateMask': 'yyyy-MM-dd HH:mm:ss', 'limit': 200, 'start': start, 'dir': 'DESC'})
            items = j['results']['item']
            for i in items:
                if i['disclosureId'] in seen:
                    continue
                seen.add(i['disclosureId'])
                out.append({'date': i.get('releaseTime') or i.get('published'), 'type': i.get('cnsCategory'), 'title': i.get('headline'), 'url': i.get('messageUrl'),
                            'source': 'Nasdaq Copenhagen company news (CNS)', 'language': i.get('language'), 'market': i.get('market'), 'company': i.get('company'),
                            'disclosure_id': i['disclosureId'], 'attachments': [x.get('attachmentUrl') for x in (i.get('attachment') or [])]})
            start += len(items)
            if not items or start >= int(j.get('count') or 0):
                break
    out.sort(key=lambda e: e['date'] or '', reverse=True)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    since = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=365)).isoformat()
    tests = ['DK0062498333', 'DK0060079531', 'DK0010244508']   # Novo Nordisk B, DSV, A.P. Moller-Maersk B
    res = {}
    for t in tests:
        ev = fetch(t, since)
        res[t] = {'news_company_names': names_for(t), 'count': len(ev), 'events': ev}
        print(t, res[t]['news_company_names'], len(ev), (ev[0]['date'], ev[0]['type'], ev[0]['title']) if ev else '')
    out = {'source_url': NEWS + 'query.action', 'read_by': 'eu-sources/dk/events.py', 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
           'since': since, 'issuers': res}
    p = os.path.join(HERE, 'samples', 'events-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', p)

# DAY ORDER 4 (2026-10-24): eu_node.py reads six issuers at a time; the lazy lists above are filled once, under a lock (unlocked, the first
# thread published an empty set and the other five read no company names: the 2026-10-24 Sweden harvest found events for 2 issuers).
import threading as _th
_LOCK = _th.Lock(); _companies_once, _screener_once = companies, screener
def companies():
    with _LOCK: return _companies_once()
def screener():
    with _LOCK: return _screener_once()
