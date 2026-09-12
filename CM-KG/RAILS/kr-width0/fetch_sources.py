"""Step 1 — pull the Korean roster and register references into raw/ (a junction to the open pond drop POND\\kr-cm-kg\\width0\\<date>\\).
  KIND (KRX) listed-company list ... corpList.do?method=download (searchType=13 = all markets): company name (Korean), 6-digit stock code, market,
                                     industry, main products, listing date, fiscal month, CEO, website, region — an EUC-KR HTML table served as .xls
  DART corpCode.xml ................. every DART filer with corp_code, Korean and English names, stock code (keyed with AGENT KEYS\\dart.txt)
  DART company.json ................. per listed corp_code: English name, stock name, corporate registration number (jurir_no), business registration
                                     number (bizr_no — the GLEIF register key at RA000657), address, homepage, IR page, industry code, establishment
                                     date, fiscal month, corp class (Y KOSPI, K KOSDAQ, N KONEX, E other)
No price or market data is carried. Korean text is carried as published; English names are the ones DART publishes."""
import requests, json, os, io, re, zipfile, datetime, time, html, threading, sys
from concurrent.futures import ThreadPoolExecutor
import keys
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
os.makedirs('raw', exist_ok=True); TODAY = datetime.date.today().isoformat()
DK = os.environ['DART_API_KEY']
KIND = 'https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
def kind():
    b = requests.get(KIND, headers=UA, timeout=300).content; open('raw/kind_corplist.xls', 'wb').write(b)
    t = b.decode('euc-kr', 'replace'); trs = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S)
    rows = []; hdr = None
    for tr in trs:
        cells = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
        if not cells: continue
        if hdr is None: hdr = cells; continue
        rows.append(dict(zip(hdr, cells)))
    json.dump({'src': KIND, 'fetched': TODAY, 'header': hdr, 'rows': rows}, open('raw/kind_list.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('KIND rows', len(rows), 'header', hdr, flush=True)
def corpcode():
    b = requests.get('https://opendart.fss.or.kr/api/corpCode.xml', params={'crtfc_key': DK}, headers=UA, timeout=300).content
    z = zipfile.ZipFile(io.BytesIO(b)); t = z.read(z.namelist()[0]).decode('utf-8', 'replace')
    out = []
    for m in re.finditer(r'<list>(.*?)</list>', t, re.S):
        g = lambda k: (re.search(rf'<{k}>(.*?)</{k}>', m.group(1), re.S) or [None, ''])[1].strip() if re.search(rf'<{k}>(.*?)</{k}>', m.group(1), re.S) else ''
        sc = g('stock_code')
        if re.fullmatch(r'\d{6}', sc): out.append({'corp_code': g('corp_code'), 'corp_name': g('corp_name'), 'corp_eng_name': g('corp_eng_name'), 'stock_code': sc, 'modify_date': g('modify_date')})
    json.dump({'src': 'https://opendart.fss.or.kr/api/corpCode.xml', 'fetched': TODAY, 'rows': out}, open('raw/dart_corpcode.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('DART corp codes with a stock code', len(out), flush=True); return out
_gate = threading.Lock(); _last = [0.0]
def company(cc):
    with _gate:
        w = 0.25 - (time.time() - _last[0])
        if w > 0: time.sleep(w)
        _last[0] = time.time()
    for i in range(4):
        try:
            r = requests.get('https://opendart.fss.or.kr/api/company.json', params={'crtfc_key': DK, 'corp_code': cc}, headers=UA, timeout=60)
            if r.status_code != 200: time.sleep(3 * (i + 1)); continue
            j = r.json(); j['src'] = f'https://opendart.fss.or.kr/api/company.json?corp_code={cc}'; return j
        except Exception: time.sleep(3 * (i + 1))
    return {'corp_code': cc, 'status': 'error'}
def companies(codes):
    fn = 'raw/dart_company.jsonl'; done = set()
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try: done.add(json.loads(line)['corp_code'])
            except Exception: pass
    todo = [c for c in codes if c not in done]; print('company.json todo', len(todo), 'done', len(done), flush=True)
    out = open(fn, 'a', encoding='utf-8'); lock = threading.Lock(); cnt = [0]
    def work(cc):
        j = company(cc)
        with lock:
            out.write(json.dumps(j, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 250 == 0: print('company.json', cnt[0], '/', len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '3'))) as ex: list(ex.map(work, todo))
    print('company.json DONE', flush=True)
if __name__ == '__main__':
    if not os.path.exists('raw/kind_list.json'): kind()
    cc = corpcode() if not os.path.exists('raw/dart_corpcode.json') else json.load(open('raw/dart_corpcode.json', encoding='utf-8'))['rows']
    companies([c['corp_code'] for c in cc])
