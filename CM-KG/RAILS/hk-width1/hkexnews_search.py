"""hk-width1 worker (ORDER-035, 2026-10-22) — HKEXnews public title search, one day at a time, both boards, English titles only.
Source: https://www1.hkexnews.hk/search/titleSearchServlet.do (the JSON the public HKEXnews title search page reads; lang=E; market SEHK = Main Board,
GEM = GEM). Every listed-company document of the day comes back with its stock code(s), the HKEX headline category (the exchange's own code table, in
English), the title as filed in English, the date-time and the document link. One file per board per day in raw\\ (the open pond drop):
raw/hkexnews-<board>-<yyyymmdd>.json. A day already in this drop is skipped (resume). WINDOW_DAYS (default 7) days back from END_DATE (default today,
Hong Kong). Never a source: financialfilings.com (terms). No login, no form, no Chinese-language page."""
import os, sys, json, time, datetime, threading
from concurrent.futures import ThreadPoolExecutor
import requests
URL = 'https://www1.hkexnews.hk/search/titleSearchServlet.do'
UA = 'Mozilla/5.0 (compatible; Allooloo Technologies Corp. CM-KG hk-width1; developers@allooloo.ai)'
BOARDS = {'SEHK': 'Main Board', 'GEM': 'GEM'}
HKT = datetime.timezone(datetime.timedelta(hours=8))
E = os.environ
END = datetime.date.fromisoformat(E['END_DATE']) if E.get('END_DATE') else datetime.datetime.now(HKT).date()
DAYS = int(E.get('WINDOW_DAYS', '7'))
os.makedirs('raw', exist_ok=True)
S = requests.Session(); S.headers['User-Agent'] = UA; lock = threading.Lock(); stats = {'calls': 0, 'rows': 0, 'days': 0, 'skipped': 0, 'errors': 0}
def pull(board, day):
    fn = f'raw/hkexnews-{board}-{day:%Y%m%d}.json'
    if os.path.exists(fn):
        with lock: stats['skipped'] += 1
        return
    q = {'sortDir': '0', 'sortByOptions': 'DateTime', 'category': '0', 'market': board, 'stockId': '-1', 'documentType': '-1', 'fromDate': f'{day:%Y%m%d}', 'toDate': f'{day:%Y%m%d}',
         'title': '', 'searchType': '0', 't1code': '-2', 't2Gcode': '-2', 't2code': '-2', 'rowRange': '6000', 'lang': 'E'}
    for i in range(4):
        try:
            r = S.get(URL, params=q, timeout=90)
            if r.status_code == 200:
                j = r.json(); rows = json.loads(j.get('result') or '[]') if j.get('result') not in (None, 'null') else []
                total = int(rows[0]['TOTAL_COUNT']) if rows else 0
                out = {'board': board, 'board_name': BOARDS[board], 'date': day.isoformat(), 'read_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source': URL, 'query': q,
                       'total_count': total, 'rows_returned': len(rows), 'complete': len(rows) >= total, 'rows': rows}
                with open(fn, 'x', encoding='utf-8') as f: json.dump(out, f, ensure_ascii=False)
                with lock: stats['calls'] += 1; stats['rows'] += len(rows); stats['days'] += 1
                return
        except Exception as e: err = repr(e)
        time.sleep(3 * (i + 1))
    with lock: stats['errors'] += 1
    print('miss', board, day, flush=True)
if __name__ == '__main__':
    days = [END - datetime.timedelta(days=k) for k in range(DAYS)]
    jobs = [(b, d) for d in days for b in BOARDS]
    print(f'hkexnews: {len(jobs)} board-days, {days[-1]} → {days[0]}', flush=True)
    with ThreadPoolExecutor(max_workers=int(E.get('THREADS', '4'))) as ex: list(ex.map(lambda a: pull(*a), jobs))
    print('hkexnews', stats, flush=True)
    sys.exit(1 if stats['errors'] and not stats['days'] else 0)
