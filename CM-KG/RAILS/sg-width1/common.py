"""Shared pieces for the Singapore Width 1 (Disclosure) rail (ORDER-014 Part A). Same shape as the Australia rail; Singapore issuers and sources.
Pond-native: raw\\ is a junction to the open drop POND\\sg-cm-kg\\width1\\<date>\\ (pond_open.py); assemblers read every drop."""
import os, re, json, sys, time, threading, datetime, html
import requests, openpyxl
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\sg-width0')
import keys  # loads AGENT KEYS into env; never printed
import pond
NODE = 'sg-cm-kg'
ISSUERS_XLSX = pond.latest_assembled(NODE, 'sg-issuers.xlsx') or r'C:\ALLOOLOO\CM-KG\ISSUERS\sg-issuers.xlsx'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
TAV = os.environ.get('TAVILY_API_KEY', ''); TH = {'Authorization': 'Bearer ' + TAV}
TODAY = datetime.date.today()
WINDOW_DAYS = int(os.environ.get('WINDOW_DAYS', '365'))
SINCE = TODAY - datetime.timedelta(days=WINDOW_DAYS)
os.makedirs('raw', exist_ok=True)
TABS = ['SGX Mainboard', 'SGX Catalist']
STOP = {'limited', 'ltd', 'the', 'company', 'co', 'group', 'holdings', 'holding', 'trust', 'fund', 'inc', 'corp', 'corporation', 'international', 'global', 'capital', 'investments', 'investment', 'pte', 'singapore', 'and', 'technologies', 'technology', 'industries', 'engineering', 'asia', 'pacific', 'china', 'ordinary', 'shares', 'bhd', 'berhad', 'enterprises', 'enterprise', 'resources', 'development', 'developments', 'properties', 'property', 'systems', 'services', 'marine', 'energy', 'medical', 'healthcare', 'food', 'foods', 'trading', 'industrial', 'land', 'united', 'new', 'first', 'one'}
def norm(s): return re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower().replace('&', ' and '))
def keytoks(n):
    t = [w for w in norm(n).split() if w not in STOP]
    if not t: t = [w for w in norm(n).split() if w not in ('limited', 'ltd', 'the')]
    return t[:2] if t else norm(n).split()[:1]
_UNIQUE = None; _COMMON = None
def _unique_tokens():
    """tokens (len>=5, not STOP) that occur in exactly one entity name across the FULL SG roster (both tabs, trusts and receipts included)"""
    global _UNIQUE
    if _UNIQUE is None:
        from collections import Counter
        c = Counter(); wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True)
        for ex in TABS:
            if ex not in wb.sheetnames: continue
            ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it); i = hdr.index('Legal name')
            for row in it:
                for t in set(w for w in norm(row[i] or '').split() if w not in STOP and len(w) >= 5): c[t] += 1
        _UNIQUE = set(t for t, n in c.items() if n == 1)
    return _UNIQUE
def _common_words():
    global _COMMON
    if _COMMON is None:
        fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'common_words.txt')
        _COMMON = set(l.strip() for l in open(fn, encoding='utf-8')) if os.path.exists(fn) else set()
    return _COMMON
def name_match(text, name, aliases=()):
    n = norm(text)
    for nm in (name,) + tuple(a for a in aliases if a):
        toks = keytoks(nm)
        if toks and all(k in n for k in toks): return 'full', ''
    words = set(n.split()); uniq = _unique_tokens(); common = _common_words()
    core = [w for w in norm(name).split() if w not in STOP and len(w) >= 5]
    present = [w for w in core if w in words]
    for w in present:
        if w in uniq and w not in common: return 'distinctive', w
    return ('ambiguous', present[0]) if present else ('none', '')
def name_in(text, name, aliases=()): return name_match(text, name, aliases)[0] in ('full', 'distinctive')
def load_issuers(types=('Corporate',)):
    """Corporate entities from sg-issuers.xlsx (REITs, business trusts and depositary receipts out per ORDER-014)."""
    wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True); out = []
    for ex in TABS:
        if ex not in wb.sheetnames: continue
        ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it)
        for r in it:
            d = dict(zip(hdr, r))
            if str(d['Security type']) not in types: continue
            out.append({'exchange': ex, 'ticker': d['SGX code'], 'name': d['Legal name'], 'trading_name': d.get('Trading name') or '', 'isin': d['ISIN'] or '', 'lei': d['LEI'] or '', 'uen': d['UEN'] or '', 'acn': d['UEN'] or '',
                        'wire': (d['Newswire of habit'] or '').split(' (')[0], 'wire_urls': (d['Newswire releases seen'] or '').split('\n') if d['Newswire releases seen'] else [], 'website': d.get('Website') or '', 'ann_link': d.get('SGXNet announcements link') or ''})
    return out
def key(r): return r['exchange'] + '|' + r['ticker']
MON = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
def to_iso(s):
    if not s: return ''
    s = str(s).strip()
    m = re.match(r'(20\d\d)-(\d\d)-(\d\d)', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m = re.match(r'(\d{1,2})-([A-Za-z]{3})-(20\d\d)', s)  # SGXNet broadcast '13-Apr-2026 18:29:13'
    if m and m.group(2).lower() in MON: return f'{m.group(3)}-{MON[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'
    m = re.match(r'(\d{1,2})/(\d{1,2})/(20\d\d)', s)
    if m: return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    m = re.match(r'(\d{1,2}) ([A-Za-z]{3,9})\.? (20\d\d)', s)
    if m and m.group(2)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(2)[:3].lower()]:02d}-{int(m.group(1)):02d}'
    m = re.match(r'([A-Za-z]{3,9})\.? (\d{1,2}), (20\d\d)', s)
    if m and m.group(1)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}'
    m = re.match(r'[A-Za-z]{3}, (\d{1,2}) ([A-Za-z]{3}) (20\d\d)', s)
    if m and m.group(2).lower() in MON: return f'{m.group(3)}-{MON[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'
    m = re.match(r'[A-Za-z]+, ([A-Za-z]+) (\d{1,2}), (20\d\d)', s)
    if m and m.group(1)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}'
    return ''
def in_window(iso): return bool(iso) and iso >= SINCE.isoformat() and iso <= TODAY.isoformat()
def get(url, tries=4, timeout=60, headers=None, **kw):
    h = dict(UA); h.update(headers or {})
    for i in range(tries):
        try:
            r = requests.get(url, headers=h, timeout=timeout, **kw)
            if r.status_code in (202, 429, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return r
        except Exception:
            time.sleep(3 * (i + 1))
    return None
def tavily(payload):
    for i in range(6):
        try:
            x = requests.post('https://api.tavily.com/search', json=payload, headers=TH, timeout=120)
            if x.status_code == 429 or x.status_code >= 500: time.sleep(5 * (i + 1)); continue
            if x.status_code != 200: return {'error': x.status_code}
            return x.json()
        except Exception:
            time.sleep(3 * (i + 1))
    return {'error': 'exhausted'}
lock = threading.Lock()
def run_workers(task, fn, items, threads=4):
    fn_out = f'raw/{task}.jsonl'; done = set()
    if os.path.exists(fn_out):
        for line in open(fn_out, encoding='utf-8'):
            try: done.add(json.loads(line)['key'])
            except Exception: pass
    todo = [r for r in items if key(r) not in done]
    print(task, 'todo', len(todo), 'done', len(done), flush=True)
    out = open(fn_out, 'a', encoding='utf-8'); cnt = [0]
    def work(r):
        try: res = fn(r)
        except Exception as e: res = {'error': repr(e)[:200]}
        res['key'] = key(r)
        with lock:
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 50 == 0: print(task, cnt[0], '/', len(todo), flush=True)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=threads) as ex: list(ex.map(work, todo))
    print(task, 'DONE', flush=True)
WIRE_DOMS = {'prnewswire.com': 'PR Newswire', 'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'accesswire.com': 'ACCESS Newswire', 'accessnewswire.com': 'ACCESS Newswire', 'newsfilecorp.com': 'Newsfile', 'media-outreach.com': 'Media OutReach', 'acnnewswire.com': 'ACN Newswire'}
def wire_of(url):
    d = re.sub(r'^https?://', '', url).split('/')[0].lower()
    d3 = '.'.join(d.split('.')[-3:]); d2 = '.'.join(d.split('.')[-2:])
    return WIRE_DOMS.get(d3) or WIRE_DOMS.get(d2, '')
def url_date(url):
    m = re.search(r'/(20\d\d)/(\d{1,2})/(\d{1,2})/', url)
    if m: return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    m = re.search(r'/news/home/(20\d\d)(\d\d)(\d\d)', url)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    return ''
# ORDER-014 types: results, AGM/EGM, dividend, halt/suspension, substantial shareholder, director change, name change (+ annual_return from the ACRA register)
TYPE_RULES = [
    ('halt_suspension', r'\btrading halt\b|\bsuspension\b|\bsuspended\b|\bresumption of trading\b|\blifting of (the )?(trading )?halt\b|\bdelist'),
    ('results', r'\bfinancial statements?\b|\bfull[- ]year\b|\bhalf[- ]year\b|\bfirst quarter\b|\bsecond quarter\b|\bthird quarter\b|\bfourth quarter\b|\b[1-4]q ?(fy)?\s?20\d\d\b|\bq[1-4]\b.{0,20}\bresults\b|\bannual reports?\b|\bresults? announcement\b|\bfinancial results\b|\bbusiness update\b.{0,20}\bquarter|\bprofit guidance\b|\bunaudited\b|\bcondensed interim\b|\bfy20\d\d\b.{0,20}\bresults\b'),
    ('substantial_shareholder', r'\bsubstantial (share|unit)?holder\b|\bnotice of (a )?change in the percentage level\b|\bdisclosure of interest\b|\bform 1\b|\bform 3\b|\bform 6\b|\bnotice of cessation\b|\bchange of interest\b|\bnotification of interest\b'),
    ('director_change', r'\bappointment of\b.{0,40}\b(director|chairman|chief executive|ceo|cfo|company secretary|auditor)\b|\bresignation of\b|\bcessation of\b.{0,30}\b(director|ceo|cfo|chief|secretary)\b|\bchange of (director|chief|company secretary|auditor|registrar)\b|\bretirement of\b.{0,20}\bdirector\b|\bchange in (board|management)\b|\bappointment of\b.{0,20}\bindependent\b'),
    ('agm_egm', r'\bannual general meeting\b|\bagm\b|\bextraordinary general meeting\b|\begm\b|\bnotice of (general )?meeting\b|\bresults of (the )?(annual|extraordinary)?\s?general meeting\b|\bminutes of\b.{0,20}meeting|\brecord date\b|\bbooks closure\b|\bproxy form\b|\bscheme meeting\b'),
    ('dividend', r'\bdividend\b|\bdistribution\b(?! agreement)|\bcash distribution\b|\bscrip\b'),
    ('name_change', r'\bchange of (company )?name\b|\bname change\b|\brenamed\b'),
    ('exchange_bulletin', r'.*'),
]
NOT_FIN = re.compile(r'drill|assay|exploration|sampling|geophys|geochem|intercept|mineral resource|resource estimate|feasibility|test results|survey results|trial results|study results|clinical|phase [123]|voting results|results of (the )?(annual|gen|extraordinary|scheme)')
def classify(title, default='sgxnet_announcement'):
    t = (title or '').lower()
    for typ, pat in TYPE_RULES[:-1]:
        if re.search(pat, t):
            if typ == 'results' and NOT_FIN.search(t): continue
            return typ
    return default
def event(issuer, etype, date, title, source, url, read_by, wire='', detail='', sgx_category='', reference=''):
    return {'exchange': issuer['exchange'], 'ticker': issuer['ticker'], 'isin': issuer.get('isin', ''), 'lei': issuer.get('lei', ''), 'issuer': issuer['name'],
            'event_type': etype, 'date': date, 'title': html.unescape((title or '')).strip()[:300], 'wire': wire, 'source': source, 'url': url, 'read_by': read_by, 'detail': detail,
            'sgx_category': sgx_category, 'reference': reference}
