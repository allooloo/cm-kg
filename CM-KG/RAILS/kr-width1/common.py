"""Shared pieces for the South Korea Width 1 (Disclosure) rail (ORDER-017 re-cut). Same shape as the Swiss rail; South Korea issuers and the regulator filing trail; no Tavily search layer on this node (ORDER-017: Perplexity Search + preset fast at the Fill pass, Tavily extraction only).
Pond-native: raw\\ is a junction to the open drop POND\\nl-cm-kg\\width1\\<date>\\ (pond_open.py); assemblers read every drop."""
import os, re, json, sys, time, threading, datetime, html
import requests, openpyxl
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\kr-width0')
import keys  # loads AGENT KEYS into env; never printed
import pond
NODE = 'kr-cm-kg'; CC = 'kr'
ISSUERS_XLSX = pond.latest_assembled(NODE, f'{CC}-issuers.xlsx') or rf'C:\ALLOOLOO\CM-KG\ISSUERS\{CC}-issuers.xlsx'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
TAV = os.environ.get('TAVILY_API_KEY', ''); TH = {'Authorization': 'Bearer ' + TAV}
TODAY = datetime.date.today()
WINDOW_DAYS = int(os.environ.get('WINDOW_DAYS', '365'))
SINCE = TODAY - datetime.timedelta(days=WINDOW_DAYS)
os.makedirs('raw', exist_ok=True)
TABS = ['KOSPI', 'KOSDAQ', 'KONEX']; TICKER_COL = 'Symbol'; REG_COL = 'DART corp code'; HOME_ISIN = ''
STOP = {'limited', 'ltd', 'the', 'company', 'co', 'group', 'groep', 'holdings', 'holding', 'trust', 'fund', 'inc', 'corp', 'corporation', 'international', 'global', 'capital', 'investments', 'investment', 'nv', 'n', 'v', 'bv', 'se', 'and', 'en', 'technologies', 'technology', 'industries', 'engineering', 'nederland', 'netherlands', 'dutch', 'europe', 'koninklijke', 'royal', 'maatschappij', 'beheer', 'participaties'}
def norm(s): return re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower().replace('&', ' and ').replace('é', 'e').replace('ü', 'u').replace('ö', 'o').replace('ä', 'a'))
def keytoks(n):
    t = [w for w in norm(n).split() if w not in STOP]
    if not t: t = [w for w in norm(n).split() if w not in ('limited', 'ltd', 'the')]
    return t[:2] if t else norm(n).split()[:1]
_UNIQUE = None; _COMMON = None
def _unique_tokens():
    global _UNIQUE
    if _UNIQUE is None:
        from collections import Counter
        c = Counter(); wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True)
        for ex in TABS:
            if ex not in wb.sheetnames: continue
            ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it); i = next(hdr.index(c) for c in ('Legal name (English, DART)', 'Legal name (Korean)', 'Legal name') if c in hdr)
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
_LEIREC = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
def load_issuers(types=('Corporate', 'SPAC (by name)')):
    """Roster lines of the carried types from the Width 0 workbook (ISIN is often blank at Width 0 on this node: the symbol is the key)."""
    wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True); out = []
    for ex in TABS:
        if ex not in wb.sheetnames: continue
        ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it)
        for r in it:
            d = dict(zip(hdr, r))
            if str(d.get('Security type')) not in types or not d.get(TICKER_COL): continue
            nm = d.get('Legal name (English, DART)') or d.get('Legal name (Korean)') or ''
            out.append({'exchange': ex, 'ticker': str(d[TICKER_COL]), 'name': nm, 'name_native': d.get('Legal name (Korean)') or '', 'full_name': (_LEIREC.get(d.get('LEI') or '') or {}).get('name') or nm, 'isin': d.get('ISIN') or '', 'lei': d.get('LEI') or '', 'reg_id': str(d.get(REG_COL) or ''),
                        'wire': (d.get('Newswire of habit') or '').split(' (')[0], 'wire_urls': [], 'website': d.get('Website') or '', 'legal_seat': d.get('HQ city') or ''})
    return out
def key(r): return r['exchange'] + '|' + r['ticker']
MON = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
def to_iso(s):
    if not s: return ''
    s = str(s).strip()
    m = re.match(r'(20\d\d)-(\d\d)-(\d\d)', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m = re.match(r'(\d{1,2})\.(\d{1,2})\.(20\d\d)', s)  # 13.04.2026
    if m: return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    m = re.match(r'(\d{1,2})/(\d{1,2})/(20\d\d)', s)
    if m: return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    m = re.match(r'(\d{1,2}) ([A-Za-z]{3,9})\.? (20\d\d)', s)
    if m and m.group(2)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(2)[:3].lower()]:02d}-{int(m.group(1)):02d}'
    m = re.match(r'([A-Za-z]{3,9})\.? (\d{1,2}), (20\d\d)', s)
    if m and m.group(1)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}'
    m = re.match(r'[A-Za-z]{3}, (\d{1,2}) ([A-Za-z]{3}) (20\d\d)', s)
    if m and m.group(2).lower() in MON: return f'{m.group(3)}-{MON[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'
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
WIRE_DOMS = {'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'prnewswire.com': 'PR Newswire', 'accesswire.com': 'ACCESS Newswire', 'newsfilecorp.com': 'Newsfile'}
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
# ORDER-015 types: ad hoc, results, AGM/EGM, dividend, halt/suspension, major holder (voting rights), directors' dealings, name change, register events (SHAB)
TYPE_RULES = [
    ('halt_suspension', r'\btrading halt\b|\bsuspension\b|\bsuspended\b|\bhandelsaussetzung\b|\bsuspension de la cotation\b|\bdelist'),
    ('results', r'\bfinancial statements?\b|\bfull[- ]year\b|\bhalf[- ]year\b|\bhalbjahr|\bjahresergebnis|\bjahresabschluss|\bquartals|\bfirst quarter\b|\bsecond quarter\b|\bthird quarter\b|\bfourth quarter\b|\bq[1-4]\b.{0,20}\b(results|ergebnis)|\bannual report\b|\bgeschäftsbericht|\brapport annuel\b|\bresults? (announcement|20\d\d)\b|\bfinancial results\b|\bergebnisse? 20\d\d\b|\bpreliminary (results|figures)\b|\bvorläufige\b.{0,20}\bzahlen\b|\bresultats\b|\bumsatz\b.{0,30}\b(gj|geschäftsjahr|quartal|halbjahr)\b|\bkennzahlen\b'),
    ('major_holder', r'\bvoting rights\b|\bstimmrechts|\bmajor (share|unit)?holder\b|\bsignificant shareholder\b|\bdisclosure of (significant )?shareholding\b|\bbeteiligungsmeldung\b|\bfranchissement de seuil\b|\bnet short\b|\btotal voting rights\b'),
    ('directors_dealings', r"\bdirectors'? dealings?\b|\bmanagers'? transactions?\b|\beigengeschäfte\b|\bmanagement transactions?\b|\bopérations de dirigeants\b"),
    ('director_change', r'\bappointment of\b.{0,40}\b(director|chairman|chief executive|ceo|cfo|board member|verwaltungsrat|vorstand)\b|\bresignation of\b|\bchange of (ceo|cfo|chief|chairman|director|board|management|auditor)\b|\bneuer (ceo|cfo|verwaltungsratspräsident|vorstand)|\bwechsel im (vorstand|verwaltungsrat|aufsichtsrat)\b|\bpersonalie|\bpersonnel change\b|\bmanagement change\b'),
    ('agm_egm', r'\bannual general meeting\b|\bagm\b|\bextraordinary general meeting\b|\begm\b|\bgeneralversammlung\b|\bhauptversammlung\b|\bassemblée générale\b|\bnotice of (general )?meeting\b|\brecord date\b|\beinladung zur\b|\bconvocation\b|\bresults of (the )?(annual|extraordinary)?\s?general meeting\b|\bhv\b|\bgv\b'),
    ('dividend', r'\bdividend\b|\bdividende\b|\bausschüttung\b|\bdistribution\b(?! agreement)|\bkapitalrückzahlung\b'),
    ('name_change', r'\bchange of (company )?name\b|\bname change\b|\brenamed\b|\bnamensänderung\b|\bumfirmierung\b|\bchangement de (nom|raison sociale)\b'),
    ('ad_hoc', r'\bad[- ]?hoc\b|\bad hoc announcement\b|\bad-hoc-mitteilung\b|\binsiderinformation\b|\binside information\b|\bcommunication ad hoc\b|\bkey word\(s\)\b|\bgewinnwarnung\b|\bprofit warning\b|\bguidance\b'),
    ('exchange_bulletin', r'.*'),
]
NOT_FIN = re.compile(r'drill|assay|exploration|sampling|geophys|geochem|intercept|mineral resource|resource estimate|feasibility|test results|survey results|trial results|study results|clinical|phase [123]|voting results|results of (the )?(annual|gen|extraordinary|scheme)')
def classify(title, default='corporate_news'):
    t = (title or '').lower()
    for typ, pat in TYPE_RULES[:-1]:
        if re.search(pat, t):
            if typ == 'results' and NOT_FIN.search(t): continue
            return typ
    return default
def event(issuer, etype, date, title, source, url, read_by, wire='', detail='', category='', reference='', language=''):
    return {'exchange': issuer['exchange'], 'ticker': issuer['ticker'], 'isin': issuer.get('isin', ''), 'lei': issuer.get('lei', ''), 'issuer': issuer['name'],
            'event_type': etype, 'date': date, 'title': html.unescape((title or '')).strip()[:300], 'wire': wire, 'source': source, 'url': url, 'read_by': read_by, 'detail': detail,
            'category': category, 'reference': reference, 'language': language}
