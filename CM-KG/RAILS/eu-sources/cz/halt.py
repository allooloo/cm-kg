"""CZ halts: instruments whose trading on the Prague Stock Exchange (XPRA / XPRM incl. START) is currently suspended.

Source : PSE exchange notices through the PSE news API, items of type PSE matching 'suspension':
         https://www.pse.cz/api/news?lang=en&type=PSE&page=<n>&homepage=0&searchKey=suspension&dateFrom=&dateTo=
         (JSON; static public header X-API-Key: PSE as sent by the PSE site itself, not a credential).
         Since 2024 the notices carry a structured block: Action type (Suspension of trading / Cancellation of
         suspension), Reason for the action, Effective from, Effective to, Trading venue(s), and usually the ISIN.
         PSE publishes no standing "suspended instruments" list, so the list is derived: notices are grouped by ISIN;
         an ISIN whose latest notice is a suspension that has not expired ('Effective to' in the past) is halted,
         and so is one whose cancellation notice is published but not yet effective ('lift_effective').
         Instruments of every kind are reported (shares, bonds, fund units); 'kind' says which, from the notice title.
         Lift notices are also recognised from text such as 'terminated the suspension' in other exchange notices.
Limits : a notice without an ISIN in its text cannot be paired and is listed under 'unpaired'. One-day suspensions
         (e.g. during an accelerated book-build) end without a cancellation notice; 'Effective to' or the
         'entire trading day' / 'resumed with the opening' wording or a 'Temporary suspension' title closes
         them once 3 days have passed.
"""
import datetime as dt, glob, html, json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'application/json', 'X-API-Key': 'PSE'}
NEWS = 'https://www.pse.cz/api/news'
ISIN = re.compile(r'\b([A-Z]{2}[A-Z0-9]{9}[0-9])\b')
_S = requests.Session(); _S.headers.update(UA)


def _get(params):
    for i in range(4):
        try:
            r = _S.get(NEWS, params=params, timeout=60)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(3 * (i + 1)); continue
            return r.json()
        except (requests.RequestException, ValueError):
            time.sleep(3 * (i + 1))
    raise RuntimeError('PSE news API unreachable')


def _text(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h or ''))).strip()


def _field(t, name, nxt):
    m = re.search(re.escape(name) + r'\s+(.*?)\s+(?:' + '|'.join(map(re.escape, nxt)) + r'|$)', t)
    return m.group(1).strip() if m else None


FIELDS = ['Date and time of the publication', 'Action type', 'Reason for the action', 'Effective from', 'Effective to', 'Ongoing', 'Trading venue(s)']


def notices(years=3, max_pages=20):
    cutoff = (dt.date.today() - dt.timedelta(days=365 * years)).isoformat()
    out = []
    for page in range(1, max_pages + 1):
        data = (_get({'lang': 'en', 'type': 'PSE', 'page': page, 'homepage': 0, 'searchKey': 'suspension', 'dateFrom': '', 'dateTo': ''}) or {}).get('data') or []
        if not data:
            break
        for x in data:
            t = _text(x.get('content'))
            f = {k: _field(t, k, [n for n in FIELDS if n != k] + ['Instrument', 'ISIN', 'Issuer']) for k in FIELDS}
            title = x.get('title') or ''
            low = (f['Action type'] or title).lower()
            if 'suspen' in low:
                kind = 'lift' if re.search(r'cancell?ation|resum|terminat|lift', low) else 'suspend'
            elif re.search(r'(terminated|cancell?ed|lifted|ended) the suspension', t.lower()):
                kind = 'lift'
            else:
                kind = None
            if not kind:
                continue
            isins = list(dict.fromkeys(ISIN.findall(t) + ([x['isin']] if x.get('isin') else [])))
            out.append({'date': x.get('publishedAt'), 'title': title, 'kind': kind, 'isins': isins, 'text': t,
                        'reason': f['Reason for the action'], 'effective_from': f['Effective from'], 'effective_to': f['Effective to'],
                        'venue': f['Trading venue(s)'], 'url': f"https://www.pse.cz/en/news/{x.get('slug')}"})
        if min((x.get('publishedAt') or '9')[:10] for x in data) < cutoff:
            break
    return [n for n in out if (n['date'] or '')[:10] >= cutoff]


def _roster():
    for p in sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')), reverse=True):
        return {r['isin']: r for r in json.load(open(p, encoding='utf-8'))['rows']}
    return {}


def _kind(title):
    t = title.lower()
    for k, w in (('bond', 'bond'), ('investment share', 'fund'), ('fund', 'fund'), ('share', 'share')):
        if k in t:
            return w
    return None


def fetch():
    ns = sorted(notices(), key=lambda n: n['date'] or '')
    roster, by, unpaired = _roster(), {}, []
    for n in ns:
        if not n['isins']:
            unpaired.append({'date': n['date'], 'title': n['title'], 'kind': n['kind'], 'url': n['url']}); continue
        for i in n['isins']:
            by.setdefault(i, []).append(n)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    halted = []
    for isin, seq in by.items():
        last = seq[-1]
        pending_lift = None
        if last['kind'] == 'lift':
            ef = last['effective_from'] or ''
            prior = [n for n in seq[:-1] if n['kind'] == 'suspend']
            if not (re.match(r'\d{4}-\d{2}-\d{2}', ef) and ef > now[:len(ef)] and prior):
                continue
            pending_lift, last = ef, prior[-1]   # cancellation published but not yet effective: still halted
        to = last['effective_to'] or ''
        if re.match(r'\d{4}-\d{2}-\d{2}', to) and to < now[:len(to)]:
            continue
        tl = last['text'].lower()
        if ('entire trading day' in tl or 'resumed with the opening' in tl or last['title'].lower().startswith('temporary')) and (dt.date.today() - dt.date.fromisoformat(last['date'][:10])).days > 3:
            continue
        r = roster.get(isin, {})
        name = r.get('name') or re.sub(r'^(Temporary )?Suspension of trading (with|in|of)( the)?( issue of)?( shares| bonds| investment shares)?\s*', '', last['title'], flags=re.I).strip() or None
        halted.append({'isin': isin, 'ticker': r.get('ticker'), 'name': name, 'since': last['effective_from'] or last['date'],
                       'reason': last['reason'] or last['text'][:400], 'kind': _kind(last['title']) or ('share' if r else None),
                       'venue': last['venue'], 'notice_url': last['url'], 'lift_effective': pending_lift})
    return {'source_url': NEWS + '?lang=en&type=PSE&searchKey=suspension', 'read_at': now,
            'method': 'derived from PSE suspension / cancellation notices, paired by ISIN', 'notices_read': len(ns),
            'count': len(halted), 'halted': halted, 'unpaired': unpaired}


if __name__ == '__main__':
    out = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', f'halts-{dt.datetime.now(dt.timezone.utc).date().isoformat()}.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('notices', out['notices_read'], 'halted', out['count'], [(h['isin'], h['ticker'], h['name'], (h['since'] or '')[:10], h['kind']) for h in out['halted']],
          'unpaired', len(out['unpaired']), '->', p)
