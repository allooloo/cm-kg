"""UAE halts - DFM's own market notices (announcement_type "DFM News") of trading suspension and resumption. DERIVED: DFM publishes no
standing list of currently suspended securities; current halts are derived from the notices.

Store: eFSAH, the feed behind https://www.dfm.ae/the-exchange/news-disclosures/market-announcements
  GET https://api2.dfm.ae/efsah/v1/prototype_efsah?announcement_type=DFM News&keyword=<Suspend|Resume>&lang=en&take=20&skip=<n>
  (20 per call, newest first, whole history paged by skip). Keyless.
Notice forms seen: "Suspend trading on <SYM> shares starting from ... as its BOD meeting is being held today ...",
  "Suspend trading on <SYM> shares for not submitting ...", "Resume trading on [<Name> -]<SYM> shares after ...".
Current halt = the latest suspension notice for a symbol with no later resumption notice for that symbol, and the symbol is on the
active roster (samples/roster-*.json). Unresolved suspensions of symbols no longer listed are kept apart, not counted.
Intraday BOD-meeting suspensions normally resume the same or next day, so a notice from today can show as current until DFM posts the
resumption. Nasdaq Dubai and ADX halts are not covered (ADX needs a gateway key; Nasdaq Dubai notices are on nasdaqdubai.com, not read).

fetch() -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page"}]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, re, sys, json, glob, time, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://api2.dfm.ae/efsah/v1/prototype_efsah'
PAGE = 'https://www.dfm.ae/the-exchange/news-disclosures/market-announcements'
ITEM = 'https://www.dfm.ae/the-exchange/news-disclosures/disclosures/{id}'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'application/json', 'Origin': 'https://www.dfm.ae', 'Referer': PAGE}
TAKE, GAP = 20, 0.6
SUSP = re.compile(r'\b(?:Suspend(?:ing)?|Suspension of)\s+(?:the\s+)?trading\s+(?:on|in|of)\s+(?:the\s+)?(?:[^\n]{0,80}?\s-\s*)?([A-Z][A-Z0-9_\-]{1,20})\s+(?:shares|share|securities|units)', re.I)
RESU = re.compile(r'\b(?:Resum(?:e|es|ing|ption of))\s+(?:the\s+)?trading\s+(?:on|in|of)\s+(?:the\s+)?(?:[^\n]{0,80}?\s-\s*)?([A-Z][A-Z0-9_\-]{1,20})\s+(?:shares|share|securities|units)', re.I)


def _get(params, tries=4):
    for i in range(tries):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=90)
            if r.status_code == 200:
                return json.loads(r.text.lstrip('﻿')).get('root') or []
        except (requests.RequestException, ValueError):
            pass
        time.sleep(4 * (i + 1))
    raise RuntimeError('api2.dfm.ae (efsah) did not answer')


def notices(keyword, max_pages=400):
    out, skip = [], 0
    for _ in range(max_pages):
        items = _get({'announcement_type': 'DFM News', 'keyword': keyword, 'lang': 'en', 'take': TAKE, 'skip': skip, 'cms_resources': 'true'})
        out += items
        if len(items) < TAKE:
            break
        skip += TAKE
        time.sleep(GAP)
    return out


def _dt(s):
    return datetime.datetime.strptime(s.strip(), '%b %d, %Y %I:%M:%S %p')


def _roster():
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    return {r['ticker']: r for r in json.load(open(files[-1], encoding='utf-8'))['rows']} if files else {}


def fetch():
    sus, res = notices('Suspend'), notices('Resume')
    last_s, last_r, unparsed = {}, {}, 0
    for x in sus:
        m = SUSP.search(x.get('headline') or '')
        if not m:
            unparsed += 1; continue
        sym = m.group(1).upper(); d = _dt(x['publication_date'])
        if sym not in last_s or d > last_s[sym][0]:
            last_s[sym] = (d, x)
    for x in res:
        m = RESU.search(x.get('headline') or '')
        if not m:
            continue
        sym = m.group(1).upper(); d = _dt(x['publication_date'])
        if sym not in last_r or d > last_r[sym]:
            last_r[sym] = d
    ros = _roster(); halted, stale = [], []
    for sym, (d, x) in sorted(last_s.items(), key=lambda kv: kv[1][0], reverse=True):
        if sym in last_r and last_r[sym] >= d:
            continue
        r = ros.get(sym, {})
        h = {'isin': r.get('isin'), 'ticker': sym, 'name': r.get('name') or '', 'since': d.strftime('%Y-%m-%dT%H:%M:%S') + '+04:00',
             'reason': re.sub(r'\s+', ' ', x.get('headline') or '').strip(), 'page': ITEM.format(id=x['id'])}
        # a symbol no longer on the active list (delisted, acquired, renamed) is not a current halt: kept apart, not counted
        (halted if (sym in ros or not ros) else stale).append(h)
    return {'source_url': PAGE, 'endpoint': API + ' (GET announcement_type=DFM News&keyword=Suspend|Resume, paged)',
            'read_by': 'derived: DFM market notices (DFM News) of suspension and resumption; current = latest suspension with no later resumption for the symbol',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'suspension_notices_read': len(sus), 'resumption_notices_read': len(res), 'suspension_notices_unparsed': unparsed,
            'oldest_notice_read': min((x['publication_date'] for x in sus), key=_dt, default=None),
            'count': len(halted), 'roster_used': bool(ros),
            'unresolved_not_on_active_roster': stale, 'count_unresolved_not_on_active_roster': len(stale),
            'scope': 'DFM (XDFM) notices only; ADX and Nasdaq Dubai not covered', 'language': 'en', 'halted': halted}


if __name__ == '__main__':
    out_ = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    p = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(out_, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('suspensions read', out_['suspension_notices_read'], 'resumptions read', out_['resumption_notices_read'], 'unparsed', out_['suspension_notices_unparsed'],
          'current', out_['count'], 'unresolved off-roster', out_['count_unresolved_not_on_active_roster'], '->', p)
