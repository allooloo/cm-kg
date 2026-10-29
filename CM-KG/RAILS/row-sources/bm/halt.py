"""Bermuda halts - the BSX's own current list of suspended securities.

Source: BSX Listed Securities filtered to Status = Suspended, https://www.bsx.com/listed-securities?CoStatus=3 (all security
types, paged ?page=N), plus each line's company page (https://www.bsx.com/company/<id>) for ISIN / Ticker / Status.
This is a current list (not derived).  The BSX publishes neither a suspension date nor a reason on the list or the
company page, so since / reason stay blank; the reader adds the latest filing on the company page whose title says
"Suspension" (date + title + link) as evidence when there is one, never as a guessed reason.
Scope: every BSX security type (equity boards, funds, debt, ILS, ...); equity = the four equity boards (see roster.py).

fetch(equity_only=False) -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page"}]}
Usage: python halt.py [--equity]   writes samples/halts-<date>.json
"""
import os, re, sys, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bsxhttp, roster, events

HERE = os.path.dirname(os.path.abspath(__file__))
URL = 'https://www.bsx.com/listed-securities?CoStatus=3'


def fetch(equity_only=False):
    lines = roster.list_lines('All', status='3')
    halted = []
    for ln in lines:
        if equity_only and ln['type'] not in roster.EQUITY_TYPES.values():
            continue
        f, t = roster.company_fields(ln['page'])
        isin = (f.get('ISIN') or '').strip().upper()
        ev = None
        for d, href, title in events.ROW.findall(t):
            if re.search(r'suspen', title, re.I):
                ev = {'date': d, 'title': events._clean(title), 'url': events.quote(events.urljoin(bsxhttp.BASE + '/', events.html.unescape(href)), safe=':/?&=%#')}
                break
        halted.append({'isin': isin if roster.ISIN_RE.match(isin) else None, 'ticker': f.get('Ticker') or None, 'name': ln['name'],
                       'since': None, 'reason': None, 'page': ln['page'], 'status': f.get('Status'), 'listing_type': ln['type'],
                       'currency': ln['currency'], 'domicile': f.get('Domicile'), 'latest_suspension_filing': ev})
    eq = set(roster.EQUITY_TYPES.values())
    return {'source_url': URL, 'read_by': 'BSX Listed Securities, Status = Suspended (CoStatus=3), every page; company page for ISIN / Ticker / Status. '
                                          'Current list as published; BSX gives no suspension date or reason',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'derived': False,
            'count': len(halted), 'count_equity_boards': sum(1 for h in halted if h['listing_type'] in eq),
            'count_by_type': {k: sum(1 for h in halted if h['listing_type'] == k) for k in sorted({h['listing_type'] for h in halted})},
            'count_with_isin': sum(1 for h in halted if h['isin']),
            'scope': 'equity boards only' if equity_only else 'all BSX security types', 'language': 'en', 'halted': halted}


if __name__ == '__main__':
    res = fetch(equity_only='--equity' in sys.argv)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('suspended', res['count'], 'equity boards', res['count_equity_boards'], res['count_by_type'], 'with ISIN', res['count_with_isin'], '->', out)
