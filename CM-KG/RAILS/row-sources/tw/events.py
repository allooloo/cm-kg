"""Taiwan Width 1 events - material information (重大訊息) filed on MOPS, the Market Observation Post System (公開資訊觀測站),
run by TWSE under FSC rules; one store for TWSE-listed (sii), TPEx (otc), emerging (rotc) and public companies.

Store: https://mops.twse.com.tw/mops/#/web/t05st01 (歷史重大訊息, historical material information). The page is a single-page app
whose own JSON API is called here:
  list   POST https://mops.twse.com.tw/mops/api/t05st01         {"companyId":"2330","year":"115","month":"all","firstDay":"","lastDay":""}
         (year = ROC year = Gregorian - 1911; month "all" = the whole year) -> rows [code, name, 發言日期, 發言時間, 主旨, {detail key}]
  detail POST https://mops.twse.com.tw/mops/api/t05st01_detail  {"marketKind":"sii","companyId":"2330","serialNumber":"1","enterDate":"1151015"}
         -> 主旨 (subject), 符合條款 (the rule clause the filing meets, e.g. "第51款"), 事實發生日, 說明 (text)
type    = 符合條款 as filed (the store's own category: the item of the TWSE/TPEx material-information procedures the filing meets).
type_en = the English MOPS label of that item. The English MOPS (https://emops.twse.com.tw/server-java/t05st01_e, detail field
          "To which item it meets") prints item 第N款 as "paragraph N" (checked on matching Chinese/English filings, see README);
          any 符合條款 not of the form 第N款 keeps type_en null.
title   = 主旨 exactly as filed (Chinese, as filed; line breaks kept as \n).
date    = 發言日期 + 發言時間 (Taipei local, +08:00).
url     = the MOPS page for the issuer plus the store's own detail key (there is no per-filing GET URL on the new MOPS; the exact
          filing is the detail API call recorded in detail_api).
No key, no login. The 12-month window = two list calls (previous and current ROC year) + one detail call per filing.
Pass detail=False (or env TW_EVENTS_DETAIL=0) to skip the detail calls: type/type_en are then null.

fetch(isin_or_issuer, since, detail=True) -> [{"date","type","type_en","title","url","source", ...}]
Usage: python events.py [code|ISIN ...]   (default: TSMC 2330, Hon Hai 2317, MediaTek 2454) writes samples/events-<date>.json
"""
import os, re, sys, json, time, datetime, threading
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://mops.twse.com.tw/mops/api/'
PAGE = 'https://mops.twse.com.tw/mops/#/web/t05st01'
EN_PAGE = 'https://emops.twse.com.tw/server-java/t05st01_e'
SOURCE = 'MOPS 歷史重大訊息 (mops.twse.com.tw api t05st01 / t05st01_detail)'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Content-Type': 'application/json', 'Accept': 'application/json, text/plain, */*', 'Origin': 'https://mops.twse.com.tw', 'Referer': 'https://mops.twse.com.tw/mops/'}
TZ = datetime.timezone(datetime.timedelta(hours=8))
_lock = threading.Lock(); _last = [0.0]; _map = {}


def _pace(gap=0.55):          # <= 2 requests / second across threads
    with _lock:
        w = _last[0] + gap - time.time()
        if w > 0:
            time.sleep(w)
        _last[0] = time.time()


def _post(name, body):
    for i in range(5):
        _pace()
        try:
            r = requests.post(API + name, headers=UA, data=json.dumps(body), timeout=90)
            if r.status_code == 200:
                js = r.json()
                if js.get('code') == 200:
                    return js['result']
                if js.get('code') in (500, 406) and '查無' in (js.get('message') or ''):
                    return None
                if js.get('code') == 500:
                    return None
        except (requests.RequestException, ValueError):
            pass
        time.sleep(5 * (i + 1))
    raise RuntimeError(f'MOPS {name} did not answer for {body}')


def _code(q):
    q = q.strip().upper()
    if re.fullmatch(r'[0-9A-Z]{4,6}', q) and not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}[0-9]', q):
        return q
    if not _map:
        p = os.path.join(HERE, 'cache', 'isin_map.json')
        if not os.path.exists(p):
            sys.path.insert(0, HERE); import roster; roster.fetch(with_lei=False)
        m = json.load(open(p, encoding='utf-8'))['map']
        _map.update({v['isin']: k for k, v in m.items()})
    return _map.get(q)


def clause_en(c):
    m = re.fullmatch(r'第\s*(\d+)\s*款', (c or '').strip())
    return f'paragraph {int(m.group(1))}' if m else None


def _roc(s):  # '115/10/15' -> date
    y, m, d = (int(x) for x in s.split('/'))
    return datetime.date(y + 1911, m, d)


def fetch(isin_or_issuer, since, detail=None):
    """since: 'YYYY-MM-DD' or date. Returns newest first."""
    detail = (os.environ.get('TW_EVENTS_DETAIL', '1') != '0') if detail is None else detail
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    code = _code(isin_or_issuer)
    if not code:
        return []
    today = datetime.datetime.now(TZ).date(); out = []
    for y in range(since.year, today.year + 1):
        res = _post('t05st01', {'companyId': code, 'year': str(y - 1911), 'month': 'all', 'firstDay': '', 'lastDay': ''})
        if not res:
            continue
        market = res.get('marketName')
        for row in res.get('data') or []:
            try:
                d = _roc(row[2])
            except (ValueError, IndexError):
                continue
            if d < since:
                continue
            key = row[5].get('parameters', {}) if isinstance(row[5], dict) else {}
            t = row[3] if len(row[3]) == 8 else row[3].rjust(8, '0')
            url = f"{PAGE}?companyId={code}&marketKind={key.get('marketKind', '')}&enterDate={key.get('enterDate', '')}&serialNumber={key.get('serialNumber', '')}"
            out.append({'date': f'{d.isoformat()}T{t}+08:00', 'type': None, 'type_en': None, 'title': (row[4] or '').replace('\r\n', '\n').strip(),
                        'url': url, 'source': SOURCE, 'issuer_code': code, 'issuer_short': row[1], 'market': market,
                        'detail_api': {'endpoint': API + 't05st01_detail', 'body': key}})
    if detail:
        for e in out:
            res = _post('t05st01_detail', e['detail_api']['body'])
            rows = (res or {}).get('data') or []
            if rows:
                titles = [x['main'] for x in res.get('titles', [])]
                rec = dict(zip(titles, rows[0]))
                e['type'] = (rec.get('符合條款') or '').strip() or None
                e['type_en'] = clause_en(e['type'])
                e['fact_date'] = (rec.get('事實發生日') or '').strip() or None
    out.sort(key=lambda e: e['date'], reverse=True)
    return out


if __name__ == '__main__':
    tests = sys.argv[1:] or ['TW0002330008', 'TW0002317005', 'TW0002454006']   # TSMC, Hon Hai, MediaTek
    today = datetime.datetime.now(datetime.timezone.utc).date(); since = today - datetime.timedelta(days=365)
    res = {'source_url': PAGE, 'endpoint': API + 't05st01 + ' + API + 't05st01_detail (POST JSON)', 'type_en_source': EN_PAGE + ' detail field "To which item it meets"',
           'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': since.isoformat(), 'key_required': False, 'issuers': {}}
    for q in tests:
        ev = fetch(q, since, detail=True)
        res['issuers'][q] = {'code': _code(q), 'count': len(ev), 'by_type': {k: sum(1 for e in ev if (e['type'] or '') == k) for k in sorted({e['type'] or '' for e in ev})},
                             'type_null': sum(1 for e in ev if not e['type']), 'events': ev}
        print(q, _code(q), len(ev), res['issuers'][q]['by_type'], flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
