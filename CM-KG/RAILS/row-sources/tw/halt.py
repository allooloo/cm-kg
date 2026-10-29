"""Taiwan halts - official current trading suspensions (暫停交易 / 停止買賣) on TWSE (XTAI) and TPEx (ROCO), plus the altered-trading
lists (變更交易, full-cash-delivery / periodic call auction), which are a trading restriction, not a halt, and are returned apart.

TWSE
- 暫停交易證券 (securities with trading suspended): page https://www.twse.com.tw/zh/page/trading/exchange/TWTAWU.html, data
  https://www.twse.com.tw/rwd/zh/afterTrading/TWTAWU?response=json&startDate=YYYYMMDD&endDate=YYYYMMDD (fields 編號, 證券代號, 證券名稱,
  暫停交易日期, 暫停交易時間, 恢復交易日期, 恢復交易時間; ROC dates). A 12-month range answered "no data" on 2026-10-24 while monthly
  ranges answered, so the reader asks month by month for the last 12 months. Current = suspension date reached (or announced) and no
  resumption date, or a resumption date still ahead.
- 經營權異動且營業範圍重大變更停止買賣公司 (stopped from trading after a change of control + business change): TWSE OpenAPI
  https://openapi.twse.com.tw/v1/opendata/t187ap26_L.
- 變更交易 (altered trading): https://www.twse.com.tw/rwd/zh/fullDelivery/TWT85U?response=json&date=YYYYMMDD (page TWT85U.html).
TPEx (OpenAPI, https://www.tpex.org.tw/openapi/)
- tpex_spendi_history 上櫃歷史公布暫停/恢復交易股票 (this year's suspension and resumption notices; current derived as above).
- tpex_cmode 上櫃股票變更交易、分盤交易、管理股票與停止交易資訊 (flags AlteredTrading, PeriodicTrading, ManagedStock, SuspensionOfTrading).
- mopsfin_t187ap26_O 經營權異動且營業範圍重大變更停止買賣公司.
Rows cover every security on those lists (warrants too: a warrant suspended before expiry stays "suspended"); equity_share marks
rows whose code is in the 股票/創新板 sections of the ISIN lists. ISIN: joined by security code to the TWSE ISIN lists (isin.twse.com.tw, cache/isin_map.json from roster.py). No reason text is
published on these lists (the reason is in the issuer's MOPS material information); reason = the list's own name where it says why.

fetch() -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page", ...}], "altered":[...]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, sys, json, time, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
TZ = datetime.timezone(datetime.timedelta(hours=8))
TWTAWU_PAGE = 'https://www.twse.com.tw/zh/page/trading/exchange/TWTAWU.html'
TWTAWU = 'https://www.twse.com.tw/rwd/zh/afterTrading/TWTAWU'
TWT85U_PAGE = 'https://www.twse.com.tw/zh/page/trading/exchange/TWT85U.html'
TWT85U = 'https://www.twse.com.tw/rwd/zh/fullDelivery/TWT85U'
TWSE_STOP = 'https://openapi.twse.com.tw/v1/opendata/t187ap26_L'
TPEX = 'https://www.tpex.org.tw/openapi/v1/'
STOP_REASON = '經營權異動且營業範圍重大變更停止買賣'


def _json(url, params=None):
    for i in range(4):
        try:
            time.sleep(0.6)
            r = requests.get(url, params=params, headers=UA, timeout=90)
            if r.status_code == 200:
                return r.json()
        except (requests.RequestException, ValueError):
            pass
        time.sleep(4 * (i + 1))
    raise RuntimeError(f'no answer: {url}')


def _roc(s):
    """'115/08/13' or '1150813' -> 'YYYY-MM-DD' (ROC year + 1911)."""
    s = (s or '').strip().replace('/', '')
    if len(s) < 6 or not s.isdigit():
        return None
    y, m, d = int(s[:-4]), int(s[-4:-2]), int(s[-2:])
    return datetime.date(y + 1911, m, d).isoformat()


def _isin_map():
    p = os.path.join(HERE, 'cache', 'isin_map.json')
    if not os.path.exists(p):
        sys.path.insert(0, HERE); import roster; roster.fetch(with_lei=False)
    return json.load(open(p, encoding='utf-8'))['map']


def twse_suspended(today):
    rows, first = [], today.replace(day=1)
    for k in range(12):
        y, m = first.year, first.month - k
        while m <= 0:
            m += 12; y -= 1
        start = datetime.date(y, m, 1)
        end = (datetime.date(y + (m == 12), m % 12 + 1, 1) - datetime.timedelta(days=1))
        js = _json(TWTAWU, {'response': 'json', 'startDate': start.strftime('%Y%m%d'), 'endDate': min(end, today + datetime.timedelta(days=31)).strftime('%Y%m%d')})
        if js.get('stat') == 'OK':
            f = js['fields']
            rows += [dict(zip(f, x)) for x in js.get('data', [])]
    latest = {}
    for r in rows:
        code = str(r['證券代號']).strip(); s = _roc(r['暫停交易日期'])
        if s and (code not in latest or s > latest[code]['since']):
            latest[code] = {'code': code, 'name': r['證券名稱'].strip(), 'since': s, 'since_time': r.get('暫停交易時間'), 'resume': _roc(r.get('恢復交易日期')),
                            'resume_time': r.get('恢復交易時間')}
    return [v for v in latest.values() if not v['resume'] or v['resume'] > today.isoformat()], len(rows)


def tpex_suspended(today):
    rows = _json(TPEX + 'tpex_spendi_history'); last = {}
    for r in rows:
        code = (r.get('SecuritiesCompanyCode') or '').strip()
        if not code:
            continue
        x = last.setdefault(code, {'code': code, 'name': (r.get('CompanyName') or '').strip(), 'since': None, 'resume': None})
        s, e = _roc(r.get('DateOfSuspendedTrading')), _roc(r.get('DateOfResumedTrading'))
        if s and (not x['since'] or s > x['since']):
            x['since'] = s; x['since_time'] = r.get('TimeOfSuspendedTrading')
        if e and (not x['resume'] or e > x['resume']):
            x['resume'] = e
    cur = [v for v in last.values() if v['since'] and (not v['resume'] or v['resume'] < v['since'] or v['resume'] > today.isoformat())]
    return cur, len(rows)


def fetch():
    read_at = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'); today = datetime.datetime.now(TZ).date()
    im = _isin_map(); halted, altered, seen = [], [], {}

    def add(venue, code, name, since, reason, page, kind, **extra):
        isin = (im.get(code) or {}).get('isin')
        k = (venue, code)
        if k in seen:
            h = seen[k]; h['kinds'].append(kind)
            if since and not h['since']:
                h['since'] = since
            return
        h = {'isin': isin, 'ticker': code, 'name': name, 'since': since, 'reason': reason, 'page': page, 'venue': venue, 'kinds': [kind],
             'section': (im.get(code) or {}).get('section'), 'equity_share': (im.get(code) or {}).get('section') in ('股票', '創新板'), **extra}
        seen[k] = h; halted.append(h)

    tw, n_tw = twse_suspended(today)
    for v in tw:
        add('XTAI', v['code'], v['name'], v['since'], None, TWTAWU_PAGE, '暫停交易', until=v['resume'], announced=v['since'] > today.isoformat())
    for r in _json(TWSE_STOP):
        if (r.get('公司代號') or '').strip():
            add('XTAI', r['公司代號'].strip(), (r.get('公司名稱') or '').strip(), _roc(r.get('停止買賣開始日')), STOP_REASON, TWSE_STOP, '停止買賣')
    tp, n_tp = tpex_suspended(today)
    for v in tp:
        add('ROCO', v['code'], v['name'], v['since'], None, TPEX + 'tpex_spendi_history', '暫停交易', until=v['resume'] if v['resume'] and v['resume'] > v['since'] else None,
            announced=v['since'] > today.isoformat())
    for r in _json(TPEX + 'mopsfin_t187ap26_O'):
        if (r.get('SecuritiesCompanyCode') or '').strip():
            add('ROCO', r['SecuritiesCompanyCode'].strip(), (r.get('CompanyName') or '').strip(), _roc(r.get('停止買賣開始日')), STOP_REASON, TPEX + 'mopsfin_t187ap26_O', '停止買賣')
    cmode = _json(TPEX + 'tpex_cmode'); cmode_date = None
    for r in cmode:
        r = {k.strip(): (v or '').strip() for k, v in r.items()}
        code = r.get('SecuritiesCompanyCode'); cmode_date = _roc(r.get('Date')) or cmode_date
        if not code:
            continue
        flags = [k for k in ('AlteredTrading', 'PeriodicTrading', 'ManagedStock', 'MatchingFrequency', 'SuspensionOfTrading', 'FinancialAnnouncements') if r.get(k) in ('Ｙ', 'Y')]
        if 'SuspensionOfTrading' in flags:
            add('ROCO', code, r.get('CompanyName'), None, None, TPEX + 'tpex_cmode', '停止交易 (tpex_cmode SuspensionOfTrading)', cmode_flags=flags)
        if 'AlteredTrading' in flags or 'PeriodicTrading' in flags:
            altered.append({'isin': (im.get(code) or {}).get('isin'), 'ticker': code, 'name': r.get('CompanyName'), 'venue': 'ROCO', 'as_of': cmode_date,
                            'flags': flags, 'page': TPEX + 'tpex_cmode'})
    d = today; t85 = None
    for _ in range(10):
        js = _json(TWT85U, {'response': 'json', 'date': d.strftime('%Y%m%d')})
        if js.get('stat') == 'OK' and js.get('data'):
            t85 = js; break
        d -= datetime.timedelta(days=1)
    for x in (t85 or {}).get('data', []):
        code = str(x[0]).strip()
        altered.append({'isin': (im.get(code) or {}).get('isin'), 'ticker': code, 'name': str(x[1]).strip(), 'venue': 'XTAI', 'as_of': d.isoformat(),
                        'flags': ['變更交易'] + (['分盤集合競價'] if '**' in str(x[2]) else []), 'page': TWT85U_PAGE})
    from collections import Counter
    return {'source_url': TWTAWU_PAGE, 'sources': {'twse_suspended': TWTAWU, 'twse_stop': TWSE_STOP, 'twse_altered': TWT85U,
                                                  'tpex_suspended': TPEX + 'tpex_spendi_history', 'tpex_status': TPEX + 'tpex_cmode', 'tpex_stop': TPEX + 'mopsfin_t187ap26_O'},
            'read_by': 'TWSE 暫停交易證券 (TWTAWU, last 12 months, monthly) + TWSE/TPEx 停止買賣 (t187ap26) + TPEx 暫停/恢復交易 history + TPEx tpex_cmode; '
                       'current = suspended and not resumed (or resumption ahead); ISIN joined by code to isin.twse.com.tw lists',
            'read_at': read_at, 'count': len(halted), 'count_by_venue': dict(Counter(h['venue'] for h in halted)),
            'count_isin_null': sum(1 for h in halted if not h['isin']), 'count_equity_shares': sum(1 for h in halted if h['equity_share']), 'notices_read': {'twse_TWTAWU_rows': n_tw, 'tpex_spendi_rows': n_tp},
            'count_altered': len(altered), 'altered_by_venue': dict(Counter(a['venue'] for a in altered)), 'language': 'zh-TW', 'halted': halted, 'altered': altered}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('halted', res['count'], res['count_by_venue'], 'equity shares', res['count_equity_shares'], 'altered', res['count_altered'], res['altered_by_venue'], 'isin null', res['count_isin_null'], '->', out)
