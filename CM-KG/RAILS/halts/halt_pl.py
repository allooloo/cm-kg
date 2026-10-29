"""Poland halts - GPW's official publication of suspension / removal decisions (MiFID II art. 32/52 publication).

Source: https://www.gpw.pl/zawieszenia-i-wykluczenia ("Publikacja decyzji o zawieszeniu lub wycofaniu instrumentu finansowego
z obrotu lub decyzji o zniesieniu zawieszenia"), server-rendered HTML table, local (Warsaw) time; a UTC twin is at
https://www.gpw.pl/zawieszenia-i-wykluczenia-utc and archives at ...-archiwum / ...-archiwum-utc. One row per decision with:
publication time, action (zawieszenie obrotu = suspension, zniesienie zawieszenia = lift, wycofanie z obrotu = removal),
reason, in force from / to, in force (TAK/NIE), MIC(s), issuer name, issuer LEI, ISIN, instrument short name.
The table covers all GPW venues: XWAR (Main Market), XNCO (NewConnect), WBON/WMTF (Catalyst bonds), XGLO (GlobalConnect), WDER.

Current halt = action "zawieszenie obrotu", in force TAK, "to" empty or later than now, and not followed by a later lift
or removal for the same ISIN. Reasons are in Polish as published. No key.

fetch(equity_only=False) -> {"source_url","count","halted":[{"isin","ticker","name","since","reason", ...}]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import re, os, sys, json, time, html, datetime
import requests
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
URL = 'https://www.gpw.pl/zawieszenia-i-wykluczenia'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'pl,en;q=0.8'}
EQUITY_MICS = {'XWAR', 'XNCO'}
COLS = ['n', 'published', 'action', 'reason', 'from', 'to', 'in_force', 'mic', 'issuer', 'lei', 'isin', 'instrument', 'derivatives', 'other', 'remarks']


def _get(url):
    for i in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=90)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(5 * (i + 1))
    raise RuntimeError('gpw.pl did not answer')


def _clean(c):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', c))).strip()


def decisions():
    t = _get(URL)
    i = t.find('class="table zawieszenia-i-wykluczenia"')
    tb = t[t.find('<tbody>', i):]; tb = tb[:tb.find('</tbody>')]
    rows = []
    for tr in re.findall(r'<tr.*?</tr>', tb, re.S):
        cells = [_clean(c) for c in re.findall(r'<td>(.*?)</td>', tr, re.S)]
        if len(cells) >= 12:
            rows.append(dict(zip(COLS, cells)))
    return rows


def fetch(equity_only=False):
    rows = decisions()
    now = datetime.datetime.now(ZoneInfo('Europe/Warsaw')).replace(tzinfo=None)  # the table is in Warsaw local time
    later = {}
    for r in rows:
        if r['action'] in ('zniesienie zawieszenia', 'wycofanie z obrotu'):
            later.setdefault(r['isin'], []).append(r['published'])
    halted = []
    for r in rows:
        if r['action'] != 'zawieszenie obrotu' or r['in_force'] != 'TAK':
            continue
        if r['to']:
            try:
                if datetime.datetime.strptime(r['to'], '%Y-%m-%d %H:%M:%S') <= now:
                    continue
            except ValueError:
                pass
        if any(p > r['published'] for p in later.get(r['isin'], [])):
            continue
        mics = set(m.strip() for m in r['mic'].split(','))
        if equity_only and not (mics & EQUITY_MICS):
            continue
        halted.append({'isin': r['isin'], 'ticker': r['instrument'], 'name': r['issuer'], 'since': r['from'], 'reason': r['reason'],
                       'page': URL, 'until': r['to'], 'mic': r['mic'], 'lei': r['lei'], 'published': r['published']})
    return {'source_url': URL, 'read_by': 'GPW official table of suspension / lift / removal decisions in force (zawieszenia-i-wykluczenia); '
            'current = suspension in force, end date not passed, no later lift or removal for the ISIN', 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'decisions_on_page': len(rows), 'count': len(halted),
            'count_equity_mics': sum(1 for h in halted if set(m.strip() for m in h['mic'].split(',')) & EQUITY_MICS),
            'scope': 'equity MICs XWAR/XNCO only' if equity_only else 'all GPW venues (XWAR, XNCO, WBON, WMTF, XGLO, WDER)',
            'language': 'pl', 'halted': halted}


if __name__ == '__main__':
    res = fetch(equity_only='--equity' in sys.argv)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('decisions', res['decisions_on_page'], 'halted', res['count'], 'equity', res['count_equity_mics'], '->', out)
