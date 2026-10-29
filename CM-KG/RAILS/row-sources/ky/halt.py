"""Cayman Islands halts - CSX suspension notices (derived; the CSX publishes no current-suspensions list).

Source: the CSX announcement store by year, https://www.csx.ky/_data/Announcements.asp?SearchText=&Year=<YYYY> (the data
behind https://www.csx.ky/companies/announcements.asp), scanned from 2007 to this year; each notice at
https://www.csx.ky/companies/announcement.asp?Id=<id>.  The CSX's own exchange notices are titled:
  suspend : "CSX SUSPENDS <name>" / "CSX Suspends the Listing of <name>" / "CSX SUSPENDS TRADING IN SHARES OF <name>"
  lift    : "CSX REINSTATES <name>" / "CSX REMOVES SUSPENSION OF TRADING IN SHARES OF <name>" / "CSX RE-ADMITS <name>"
  removal : "CSX CANCELS|CANCEL|CANCELLS <name> FROM THE OFFICIAL LIST" / "CSX DELIST|DE-LIST|DELISTING <name>"
DERIVED current halt = a suspend notice with no later CSX lift or removal notice whose title contains the same name, or
whose lift notice names a leading part of it (e.g. lift "BANK OF N.T.BUTTERFIELD" for suspended "BANK OF N.T. BUTTERFIELD &
SON LIMITED"); names compared after upper-casing and reducing punctuation to spaces - no fuzzy score.
reason = the notice page's "Reason for suspension:" sentence when present, else blank; since = the notice date.
on_current_list = the suspended name equals (same normalisation) an issuer on today's CSX Equity or Investment Funds list;
old suspensions of issuers no longer on any list are kept but flagged, since the CSX does not always publish a removal.
isin / ticker are filled only when the name equals a roster issuer that has a sourced ISIN (cache/roster-latest.json).

fetch() -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page"}]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, re, sys, json, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csxhttp

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = 'https://www.csx.ky/_data/Announcements.asp?SearchText=&Year={y}'
FIRST_YEAR = 2007
SUSP = re.compile(r'^CSX\s+SUSPENDS\s+(?:THE\s+LISTING\s+OF\s+(?:THE\s+)?)?(?:TRADING\s+(?:IN|OF)\s+(?:THE\s+)?(?:SHARES\s+(?:IN|OF)\s+)?)?(.+?)(?:\s+AT\s+REQUEST\s+OF\s+ISSUER|\s+DUE\s+TO\s+.*)?\s*$', re.I)
LIFT = re.compile(r'^CSX\s+(REINSTATES|REMOVES\s+SUSPENSION|RE-ADMITS|LIFTS|RESTORES)', re.I)
GONE = re.compile(r'^CSX\s+(CANCEL\w*|DELIST\w*|DE-LIST\w*|REMOVES\s+(?!SUSPENSION))', re.I)


def _clean(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def norm(s):
    return ' '.join(re.sub(r'[^A-Z0-9]+', ' ', s.upper()).split())


END_NAME = re.compile(r'^CSX\s+(?:REINSTATES|RE-ADMITS|LIFTS|RESTORES|REMOVES\s+SUSPENSION\s+OF\s+TRADING\s+IN\s+(?:THE\s+)?SHARES\s+OF)\s+(.+?)(?:\s+LISTING|\s+TO\s+(?:THE\s+)?OFFICIAL\s+LIST.*)?\s*$', re.I)


def _names(key, e):
    """Same issuer: the suspended name appears in the lift/removal title, or the name a lift notice gives
    (e.g. 'BANK OF N.T.BUTTERFIELD') is the leading part of the suspended name. Normalised strings only; no fuzzy score."""
    if key in norm(e['title']):
        return True
    m = END_NAME.match(e['title'])
    if m:
        k2 = norm(m.group(1))
        return len(k2) >= 8 and key.startswith(k2)
    return False


def notices():
    out = []
    for y in range(datetime.date.today().year, FIRST_YEAR - 1, -1):
        t = csxhttp.text(STORE.format(y=y))
        for d, i, x in re.findall(r'<TD[^>]*>([^<]*)</TD><TD><a[^>]*Id=(\d+)>(.*?)</a>', t, re.S):
            try:
                dt = datetime.datetime.strptime(d.strip(), '%d-%b-%Y').date()
            except ValueError:
                continue
            out.append({'date': dt, 'id': i, 'title': _clean(x), 'page': f'https://www.csx.ky/companies/announcement.asp?Id={i}'})
    return out


def _roster():
    p = os.path.join(HERE, 'cache', 'roster-latest.json')
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))['rows'], 'cache/roster-latest.json'
    import roster
    return roster.fetch(with_lei=False)['rows'], 'roster.fetch()'


def fetch():
    ns = notices()
    sus = []
    for n in ns:
        m = SUSP.match(n['title'])
        if m:
            sus.append({**n, 'name': m.group(1).strip(' .'), 'key': norm(m.group(1))})
    ends = [n for n in ns if LIFT.match(n['title']) or GONE.match(n['title'])]
    current = []
    for s in sus:
        later = [e for e in ends if e['date'] >= s['date'] and e['id'] != s['id'] and _names(s['key'], e)]
        resus = [o for o in sus if o['key'] == s['key'] and (o['date'], o['id']) > (s['date'], s['id'])]
        if later or resus:
            continue
        current.append(s)
    rows, rsrc = _roster()
    by_name = {}
    for r in rows:
        by_name.setdefault(norm(r['name']), []).append(r)
    halted = []
    for s in current:
        t = csxhttp.text(s['page'])
        i = t.find('id="content"'); body = t[i:] if i >= 0 else t; txt = _clean(re.sub(r'<style[^>]*>.*?</style>|<script[^>]*>.*?</script>', ' ', body, flags=re.S | re.I))
        m = re.search(r'Reason\s+for\s+suspension:\s*(.+?)(?:\.\s|\s+The suspension|\s+Copyright)', txt, re.S | re.I)
        reason = m.group(1).strip().rstrip('.') if m else None
        hits = by_name.get(s['key'], [])
        isins = sorted({h['isin'] for h in hits if h.get('isin')})
        halted.append({'isin': isins[0] if len(isins) == 1 else None, 'isins_on_roster': isins if len(isins) > 1 else None,
                       'ticker': next((h['ticker'] for h in hits if h.get('ticker')), None), 'name': s['name'],
                       'since': s['date'].isoformat(), 'reason': reason, 'page': s['page'], 'notice_title': s['title'],
                       'on_current_list': bool(hits)})
    return {'source_url': 'https://www.csx.ky/companies/announcements.asp',
            'read_by': f'DERIVED from CSX exchange notices {FIRST_YEAR}-{datetime.date.today().year} (/_data/Announcements.asp?Year=): latest CSX SUSPENDS notice per name with no later '
                       'CSX REINSTATES / REMOVES SUSPENSION / RE-ADMITS / CANCELS / DELIST notice naming it; the CSX publishes no current-suspensions list',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'derived': True,
            'notices_scanned': len(ns), 'suspension_notices': len(sus), 'count': len(halted),
            'count_on_current_list': sum(1 for h in halted if h['on_current_list']), 'roster_used': rsrc, 'language': 'en', 'halted': halted}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('notices', res['notices_scanned'], 'suspend notices', res['suspension_notices'], 'derived current', res['count'], 'on current list', res['count_on_current_list'], '->', out)
