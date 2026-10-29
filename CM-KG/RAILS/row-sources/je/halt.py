"""Jersey halts - TISE suspension notices (derived; TISE publishes no current-suspensions list).

Source: TISE Market News, POST https://tisegroup.com/api/news {"PageIndex","PageSize":100,"IssuerSearch":"","IncludeNavs":false},
the whole history back to 1999 (about 52,000 items, ~520 pages), kept in cache/news-index.json and read incrementally after
the first run (new pages are read until an item already in the index is met). Notice codes in the store's own code table:
  SUS      "Suspension of Dealings" / "Suspension of Listing"            (TISE Announcements)
  REN      "Resumption of Dealings" / "Resumption of Listing" / "Lifting of Suspension of Dealings"
  COL-CISX "Cancellation of Listing"
DERIVED current halt = the latest SUS notice per issuer mnemonic with no later REN or COL-CISX notice for that issuer.
Issuer level: a notice may cover one class only; a later partial cancellation (PAR-CISX) is not treated as an end.
since = the "with effect from <date>" in the notice text (else its publication date); reason = the notice's own words
between "suspended dealings in the following securities" and "with effect" (e.g. "at the request of the Issuer"), else blank;
isin = ISINs printed in the notice text ("ISIN - ...") only.
Jersey: the node's scope is Jersey issuers; each halt carries in_je_roster (issuer on roster.py's Jersey list) and
domicile = IssuerDetail.Address.Country of the issuer's security record when the security search finds it.

fetch(jersey_only=False) -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page"}]}
Usage: python halt.py [--jersey]   writes samples/halts-<date>.json
"""
import os, re, sys, json, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tisehttp

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, 'cache', 'news-index.json')
ISIN = re.compile(r'ISIN\W{0,12}([A-Z]{2}[A-Z0-9]{9}[0-9])')
KEEP_TEXT = {'SUS', 'REN', 'COL-CISX'}


def _clean(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or ''))).replace('\xa0', ' ').strip()


def news_index():
    idx = json.load(open(INDEX, encoding='utf-8')) if os.path.exists(INDEX) else []
    known = {n['id'] for n in idx}
    new, p, total = [], 1, None
    while True:
        j = tisehttp.call('/api/news', {'PageIndex': p, 'PageSize': 100, 'IssuerSearch': '', 'IncludeNavs': False}) or {}
        items = j.get('News') or []
        total = (j.get('Pagination') or {}).get('TotalPages')
        hit = False
        for n in items:
            if n['Id'] in known:
                hit = True; continue
            h = n.get('Headline') or {}
            new.append({'id': n['Id'], 'at': n['PublishedAt'], 'code': h.get('Code'), 'headline': h.get('Text'), 'category': h.get('Category'),
                        'issuer': (n.get('Issuer') or {}).get('Mnemonic'), 'issuer_name': (n.get('Issuer') or {}).get('Name'),
                        'text': _clean(n.get('Text')) if h.get('Code') in KEEP_TEXT else None})
            known.add(n['Id'])
        if hit or not items or p >= (total or 0):
            break
        p += 1
    idx = new + idx
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    json.dump(idx, open(INDEX, 'w', encoding='utf-8'), ensure_ascii=False)
    return idx, len(new), p


def _domicile(issuer_mnemonic, issuer_name):
    j = tisehttp.call('/api/Securities', {'PageIndex': 1, 'PageSize': 30, 'Search': issuer_name, 'Country': 'SHOWALL', 'Security': None, 'Subtype': None, 'Currency': 'SHOWALL'}) or {}
    for s in j.get('Securities') or []:
        if (s.get('Issuer') or {}).get('Mnemonic') == issuer_mnemonic:
            d = tisehttp.call('/api/securities/' + s['Mnemonic']) or {}
            c = ((d.get('IssuerDetail') or {}).get('Address') or {}).get('Country') or {}
            return c.get('Code'), s['Mnemonic']
    return None, None


def fetch(jersey_only=False):
    idx, n_new, pages = news_index()
    by_iss = {}
    for n in idx:
        if n['code'] in KEEP_TEXT and n['issuer']:
            by_iss.setdefault(n['issuer'], []).append(n)
    ros = os.path.join(HERE, 'cache', 'roster-latest.json')
    je = {r['issuer_mnemonic'] for r in json.load(open(ros, encoding='utf-8'))['rows']} if os.path.exists(ros) else set()
    halted = []
    for iss, ns in by_iss.items():
        ns.sort(key=lambda x: (x['at'], x['id']))
        last = ns[-1]
        if last['code'] != 'SUS':
            continue
        t = last['text'] or ''
        m = re.search(r'with effect from\s+(?:the time and date of this notice|(\d{1,2} \w+ \d{4}))', t, re.I)
        since = None
        if m and m.group(1):
            try:
                since = datetime.datetime.strptime(m.group(1), '%d %B %Y').date().isoformat()
            except ValueError:
                since = None
        since = since or last['at'][:10]
        r = re.search(r'suspended dealings in the following securities,?\s*(.*?),?\s*with effect', t, re.I)
        reason = r.group(1).strip(' ,') if r and r.group(1).strip(' ,') else None
        isins = sorted(set(ISIN.findall(t)))
        dom, sec = _domicile(iss, last['issuer_name'])
        h = {'isin': isins[0] if len(isins) == 1 else None, 'isins_in_notice': isins if len(isins) > 1 else None, 'ticker': sec, 'name': last['issuer_name'],
             'since': since, 'reason': reason, 'page': f'https://tisegroup.com/market/news/{last["id"]}', 'notice': last['headline'],
             'issuer_mnemonic': iss, 'domicile': dom, 'in_je_roster': iss in je, 'published_at': last['at']}
        if jersey_only and dom != 'JEY':
            continue
        halted.append(h)
    halted.sort(key=lambda x: x['since'], reverse=True)
    return {'source_url': 'https://tisegroup.com/market/news',
            'read_by': 'DERIVED from TISE market news (POST /api/news, full history, cached index): latest SUS notice per issuer with no later REN (resumption / lifting) '
                       'or COL-CISX (cancellation) notice; TISE publishes no current-suspensions list',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'derived': True,
            'news_items_indexed': len(idx), 'news_items_new_this_run': n_new, 'pages_read_this_run': pages,
            'suspension_notices': sum(1 for n in idx if n['code'] == 'SUS'), 'count': len(halted),
            'count_jersey_domicile': sum(1 for h in halted if h['domicile'] == 'JEY'), 'count_in_je_roster': sum(1 for h in halted if h['in_je_roster']),
            'scope': 'Jersey-domiciled issuers only' if jersey_only else 'all TISE issuers (Jersey flagged by domicile)', 'language': 'en', 'halted': halted}


if __name__ == '__main__':
    res = fetch(jersey_only='--jersey' in sys.argv)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('indexed', res['news_items_indexed'], 'new', res['news_items_new_this_run'], 'SUS notices', res['suspension_notices'], 'derived current', res['count'],
          'Jersey', res['count_jersey_domicile'], 'in roster', res['count_in_je_roster'], '->', out)
