"""Saudi Arabia halts - DERIVED, partial.

The Saudi Exchange publishes the suspension / resumption notices of record for XSAU securities, but www.saudiexchange.sa answered 403
Akamai "Access Denied" from this network on 2026-10-24 (see _probe.py). The one official source reachable is the regulator: CMA's
announcements (https://cma.gov.sa/en/MediaCenter/NEWS/Pages/default.aspx, SharePoint list, 30 cards per page, paged by the page's own
"next" link). CMA announces its own suspension decisions (Board resolutions to suspend trading, e.g. on CMA demand) but not the
exchange's routine suspensions (e.g. accumulated losses, late financial statements, BOD/AGM-day halts). So this is a partial,
regulator-only view: current = a CMA suspension announcement in the window with no later CMA lifting / resumption announcement
naming the same company. ISIN and ticker stay blank (CMA cards carry neither). English edition read.

fetch(months=24) -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page"}]}
Usage: python halt.py [months]   writes samples/halts-<date>.json
"""
import os, re, sys, json, time, html, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _probe import probe, SAUDI_EXCHANGE, UA  # noqa: E402

BASE = 'https://cma.gov.sa'
NEWS = BASE + '/en/MediaCenter/NEWS/Pages/default.aspx'
GAP = 0.7
CARD = re.compile(r'<span class="date">([^<]+)</span>.*?<h3[^>]*>(.*?)</h3>.*?<a href="([^"]+)"', re.S)
NEXT = re.compile(r'class="nxtbtn" onclick="javascript:RefreshPageTo\(event, (?:&quot;|")(.*?)(?:&quot;|")\)')
SUSP = re.compile(r'suspen\w*\s+(?:of\s+)?(?:the\s+)?trading|trading\s+suspension', re.I)   # not "suspension of preemptive rights" / licences
LIFT = re.compile(r'(?:lift\w*|resum\w*|reinstat\w*|cancel\w*)\s+(?:of\s+)?(?:the\s+)?(?:suspension|trading)', re.I)
NAME = re.compile(r'(?:shares of|securities of|trading (?:on|in|of)(?: the shares of)?)\s+(.+?)(?:\s+(?:on|in|at|from|for|starting|effective|until|due|as|after)\b|[.,;]|$)', re.I)


def _get(url, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            if r.status_code == 200 and 'The requested URL was rejected' not in r.text[:3000]:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(5 * (i + 1))
    raise RuntimeError(f'cma.gov.sa did not answer: {url}')


def cards(months):
    cutoff = datetime.date.today() - datetime.timedelta(days=int(months * 30.5))
    url, out, pages = NEWS, [], 0
    while url:
        t = _get(url); pages += 1
        stop = False
        for d, ti, href in CARD.findall(t):
            try:
                dd = datetime.datetime.strptime(d.strip(), '%d-%B-%Y').date()
            except ValueError:
                continue
            if dd < cutoff:
                stop = True; break
            out.append({'date': dd.isoformat(), 'title': html.unescape(re.sub(r'<[^>]+>', '', ti)).replace('\xa0', ' ').strip(),
                        'page': BASE + html.unescape(href)})
        m = NEXT.search(t)
        if stop or not m:
            break
        url = BASE + html.unescape(m.group(1)).replace('\\u0026', '&')
        time.sleep(GAP)
    return out, pages


def _name(title):
    m = NAME.search(title)
    return m.group(1).strip() if m else ''


def fetch(months=24):
    ex = probe(SAUDI_EXCHANGE)
    items, pages = cards(months)
    susp = [c for c in items if SUSP.search(c['title']) and not LIFT.search(c['title'])]
    lifts = [c for c in items if LIFT.search(c['title'])]
    halted = []
    for s in susp:
        n = _name(s['title']).lower()
        if n and any(l['date'] >= s['date'] and n in l['title'].lower() for l in lifts):
            continue
        halted.append({'isin': None, 'ticker': None, 'name': _name(s['title']), 'since': s['date'], 'reason': s['title'], 'page': s['page']})
    return {'source_url': NEWS, 'read_by': 'derived, partial: CMA announcements (regulator) naming a trading suspension, no later CMA lifting announcement; '
            'Saudi Exchange notices not read (blocked)', 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'window_months': months, 'cma_cards_read': len(items), 'cma_pages_read': pages, 'oldest_card': items[-1]['date'] if items else None,
            'suspension_cards': len(susp), 'lifting_cards': len(lifts), 'suspension_titles': [c['title'] for c in susp],
            'count': len(halted), 'saudi_exchange': ex, 'language': 'en', 'halted': halted}


if __name__ == '__main__':
    res = fetch(int(sys.argv[1]) if len(sys.argv) > 1 else 24)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('cards', res['cma_cards_read'], 'pages', res['cma_pages_read'], 'oldest', res['oldest_card'], 'suspension cards', res['suspension_cards'],
          'current', res['count'], 'exchange blocked', res['saudi_exchange']['blocked'], '->', out)
