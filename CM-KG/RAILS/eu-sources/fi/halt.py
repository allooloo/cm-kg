"""Finland halts: current trading suspensions / halts on Nasdaq Helsinki (XHEL) and First North Finland, derived from the exchange's own
notices. Nasdaq publishes no machine-readable "currently halted" list for Helsinki; suspensions, halts and their lifts are published as
exchange notices (the "Market notices" page, nasdaq.com/european-market-activity/news/market-notices), served by the CNS news API:
  GET https://api.news.eu.nasdaq.com/news/query.action?type=json&globalGroup=exchangeNotice&globalName=exchangeNewsFilterHEX|FirstNorthInformationHEX
      &fromDate=<epoch ms>&limit=200&start=..   (public, no key)
Rule: per instrument (name in the headline, normalised), take the latest suspension / halt / lift / resumption notice in the window; it is
"halted" when the latest one is a suspension or halt. Observation-status notices (RECEIVE OBSERVATION STATUS / REMOVED FROM OBSERVATION)
are reported separately under "observation" -- observation is not a halt. Securitized-derivative and bond notices are skipped.
ISIN / ticker come from the latest samples/roster-*.json (FIRDS + Nasdaq list) by name.

fetch(days=365) -> {"source_url", "count", "halted": [{"isin", "ticker", "name", "since", "reason", "url"}], "observation": [...]}
"""
import datetime as dt, glob, json, os, re, sys, time
import requests

NEWS = 'https://api.news.eu.nasdaq.com/news/query.action'
FILTERS = ['exchangeNewsFilterHEX', 'FirstNorthInformationHEX']
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
HERE = os.path.dirname(os.path.abspath(__file__))
OPEN_PAT = [r'suspension of trading in (?P<n>.+?) at [A-Z]{4}', r'(?:suspension of trading|trading halt|halt in trading|trading suspension)\s*[:\-–]\s*(?P<n>.+)',
            r'trading (?:in|of) (?P<n>.+?) (?:is|has been) (?:suspended|halted)', r'halt of trading in (?P<n>.+?)(?: at [A-Z]{4})?$']
CLOSE_PAT = [r'lift of suspension in (?P<n>.+?) at [A-Z]{4}', r'(?:lift of suspension|resumption of trading|trading resumes|lifting of (?:the )?trading halt|trading halt lifted)\s*[:\-–]?\s*(?:in |of )?(?P<n>.+)',
             r'trading (?:in|of) (?P<n>.+?) (?:is|has been) resumed']
OBS_ON = r'the shares of (?P<n>.+?) (?:receive|given|are given|placed under) observation status'
OBS_OFF = r'the shares of (?P<n>.+?) (?:are )?removed from observation'


def _get(params, tries=4):
    for i in range(tries):
        try:
            r = requests.get(NEWS, params=params, headers=UA, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            r.raise_for_status(); return r.json()
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def _norm(s):
    s = re.sub(r'[^a-z0-9åäö ]', ' ', (s or '').lower())
    s = re.sub(r'\b(oyj|abp|plc|corporation|corp|oy|ab|publ|ltd|se|sa|inc|group|shares?|share|series|class|a|b)\b', ' ', s)
    return ' '.join(s.split())


def notices(days):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    ms = int(since.timestamp() * 1000)
    out = []
    for g in FILTERS:
        start = 0
        while True:
            j = _get({'type': 'json', 'showAttachments': 'false', 'showCnsSpecific': 'true', 'showCompany': 'true', 'countResults': 'true', 'displayLanguage': 'en',
                      'timeZone': 'CET', 'dateMask': 'yyyy-MM-dd HH:mm:ss', 'limit': 200, 'start': start, 'dir': 'DESC', 'globalGroup': 'exchangeNotice',
                      'globalName': g, 'fromDate': ms})
            items = j['results']['item']
            out += [dict(i, _filter=g) for i in items]
            start += len(items)
            if not items or start >= int(j.get('count') or 0):
                break
    return out


def _match(pats, h):
    for p in pats:
        m = re.search(p, h, re.I)
        if m:
            return m.group('n').strip(' .')
    return None


def _roster():
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    return json.load(open(files[-1], encoding='utf-8'))['rows'] if files else []


def fetch(days=365):
    ns = [n for n in notices(days) if 'Securitized' not in (n.get('cnsCategory') or '') and 'Bond' not in (n.get('cnsCategory') or '')]
    state, obs = {}, {}
    for n in sorted(ns, key=lambda x: x['releaseTime']):
        h = n['headline']
        c = _match(CLOSE_PAT, h)
        o = None if c else _match(OPEN_PAT, h)
        if c or o:
            state[_norm(c or o)] = {'open': bool(o), 'name': c or o, 'since': n['releaseTime'], 'reason': h, 'url': n['messageUrl'], 'category': n.get('cnsCategory')}
        on, off = _match([OBS_ON], h), _match([OBS_OFF], h)
        if on or off:
            obs[_norm(on or off)] = {'open': bool(on), 'name': on or off, 'since': n['releaseTime'], 'reason': h, 'url': n['messageUrl']}
    rows = _roster()

    def ids(name):
        k = _norm(name)
        hits = [r for r in rows if _norm(r['name']) == k or (r.get('ticker') and _norm(r['ticker']) == k)]
        return hits

    halted = []
    for k, s in state.items():
        if not s['open']:
            continue
        hits = ids(s['name'])
        for r in hits or [None]:
            halted.append({'isin': r['isin'] if r else None, 'ticker': r.get('ticker') if r else None, 'name': r['name'] if r else s['name'],
                           'mic': r['mic'] if r else None, 'since': s['since'], 'reason': s['reason'], 'url': s['url'],
                           'in_roster': bool(r), 'source': 'Nasdaq Helsinki exchange notice (derived)'})
    observation = []
    for k, s in obs.items():
        if s['open']:
            hits = ids(s['name'])
            observation.append({'isin': hits[0]['isin'] if hits else None, 'ticker': hits[0].get('ticker') if hits else None, 'name': s['name'],
                                'since': s['since'], 'reason': s['reason'], 'url': s['url']})
    return {'source_url': NEWS + '?globalGroup=exchangeNotice&globalName=' + '|'.join(FILTERS), 'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'window_days': days, 'notices_read': len(ns), 'count': sum(1 for h in halted if h['in_roster']),
            'halted': [h for h in halted if h['in_roster']],
            'halted_not_in_roster': [h for h in halted if not h['in_roster']],   # open suspension notice, share no longer in FIRDS (delisted) or not a share
            'observation': observation,
            'closed_in_window': [dict(name=s['name'], last=s['since'], reason=s['reason']) for s in state.values() if not s['open']]}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out = fetch()
    p = os.path.join(HERE, 'samples', 'halts-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('notices', out['notices_read'], 'halted', out['count'], 'observation', len(out['observation']), 'closed', len(out['closed_in_window']), '->', p)
    for h in out['halted']:
        print('  HALT', h['isin'], h['ticker'], h['name'], h['since'], h['reason'])
    for h in out['observation']:
        print('  OBS ', h['isin'], h['ticker'], h['name'], h['since'])
    for h in out['closed_in_window']:
        print('  closed', h)
