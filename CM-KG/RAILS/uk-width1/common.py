"""Shared pieces for the United Kingdom Width 1 (Disclosure) rail. Same shape as the Canada rail; UK issuers, UK sources."""
import os, re, json, sys, time, threading, datetime, html
import requests, openpyxl
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0')
import keys  # loads AGENT KEYS into env; never printed
ISSUERS_XLSX = r'C:\ALLOOLOO\CM-KG\ISSUERS\uk-issuers.xlsx'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
TAV = os.environ.get('TAVILY_API_KEY', ''); TH = {'Authorization': 'Bearer ' + TAV}
CH_KEYFILE = r'C:\ALLOOLOO\AGENT KEYS\companieshouse.txt'
CH_KEY = open(CH_KEYFILE, encoding='utf-8').read().strip() if os.path.exists(CH_KEYFILE) else ''
TODAY = datetime.date.today()
WINDOW_DAYS = int(os.environ.get('WINDOW_DAYS', '365'))
SINCE = TODAY - datetime.timedelta(days=WINDOW_DAYS)
os.makedirs('raw', exist_ok=True)
TABS = ['LSE Main Market', 'AIM', 'Aquis Stock Exchange']
STOP = {'plc', 'p', 'l', 'c', 'the', 'company', 'co', 'ltd', 'limited', 'group', 'holdings', 'holding', 'trust', 'fund', 'inc', 'corp', 'corporation', 'international', 'global', 'capital', 'investments', 'investment', 'resources', 'mining', 'gold', 'minerals', 'metals', 'energy', 'ventures', 'technologies', 'technology', 'partners', 'and', 'uk', 'british', 'london', 'ordinary', 'shares', 'ord', 'sa', 'nv', 'ag', 'se'}
def norm(s): return re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower().replace('&', ' and '))
def keytoks(n):
    t = [w for w in norm(n).split() if w not in STOP]
    if not t: t = [w for w in norm(n).split() if w not in ('plc', 'ltd', 'the')]
    return t[:2] if t else norm(n).split()[:1]
_UNIQUE = None; _COMMON = None
def _unique_tokens():
    """tokens (len>=5, not STOP) that occur in exactly one issuer name across the FULL 1,570-row roster (all three tabs, funds included)"""
    global _UNIQUE
    if _UNIQUE is None:
        from collections import Counter
        c = Counter()
        wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True)
        for ex in TABS:
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
    """('full', '') when every key token of the issuer name (or of a sourced alias) is in the text;
       ('distinctive', tok) when a name token in the text is unique across the full roster AND not a common English word;
       ('ambiguous', tok) when the only name token(s) present fail either test; ('none', '') when no name token is in the text."""
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
    """Corporate issuers from uk-issuers.xlsx (funds, investment companies, depositary receipts and debt out per ORDER-008)."""
    wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True); out = []
    for ex in TABS:
        ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it)
        for r in it:
            d = dict(zip(hdr, r))
            if str(d['Security type']) not in types: continue
            out.append({'exchange': ex, 'ticker': d['Ticker (TIDM)'], 'name': d['Legal name'], 'isin': d['ISIN'] or '', 'lei': d['LEI'] or '', 'ch_number': d['Companies House number'] or '',
                        'wire': (d['Newswire of habit'] or '').split(' (')[0], 'wire_urls': (d['Newswire releases seen'] or '').split('\n') if d['Newswire releases seen'] else [],
                        'website': d.get('Website') or '', 'segment': d.get('Market segment') or ''})
    return out
def key(r): return r['exchange'] + '|' + r['ticker']
MON = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
def to_iso(s):
    """'25 Aug 2026' / 'Aug 25, 2026' / '2026-09-09T15:16:09+00:00' / '20230621' / '25/08/2026' -> 'YYYY-MM-DD' or ''"""
    if not s: return ''
    s = str(s).strip()
    m = re.match(r'(20\d\d)-(\d\d)-(\d\d)', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m = re.match(r'(\d{1,2}) ([A-Za-z]{3,9})\.? (20\d\d)', s)
    if m and m.group(2)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(2)[:3].lower()]:02d}-{int(m.group(1)):02d}'
    m = re.match(r'([A-Za-z]{3,9})\.? (\d{1,2}), (20\d\d)', s)
    if m and m.group(1)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}'
    m = re.match(r'(\d{1,2})/(\d{1,2})/(20\d\d)', s)
    if m: return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    m = re.match(r'(20\d\d)(\d\d)(\d\d)$', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
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
    """Resume-safe fan-out: results appended to raw/<task>.jsonl keyed on item key; each fn returns a dict."""
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
WIRE_DOMS = {'prnewswire.com': 'PR Newswire', 'prnewswire.co.uk': 'PR Newswire', 'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'accesswire.com': 'ACCESS Newswire', 'accessnewswire.com': 'ACCESS Newswire', 'newsfilecorp.com': 'Newsfile', 'newswire.ca': 'Canada Newswire (CNW)', 'londonstockexchange.com': 'RNS', 'investegate.co.uk': 'RNS'}
def wire_of(url):
    d = re.sub(r'^https?://', '', url).split('/')[0].lower()
    d2 = '.'.join(d.split('.')[-2:]); d3 = '.'.join(d.split('.')[-3:])
    return WIRE_DOMS.get(d3) or WIRE_DOMS.get(d2, '')
def url_date(url):
    m = re.search(r'/(20\d\d)/(\d{1,2})/(\d{1,2})/', url)
    if m: return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    m = re.search(r'/news/home/(20\d\d)(\d\d)(\d\d)', url)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    return ''
# ---- event typing from an RNS headline / release title. The event date is always the announcement date, never a date read out of the headline.
TYPE_RULES = [
    ('halt_resume', r'\bsuspension\b|\bsuspended\b|\bsuspend\b|\brestoration\b|\brestored\b|\btrading halt\b|\bcancellation of (admission|listing|trading)\b|\bcancellation\b.{0,30}\b(aim|admission|listing)\b|\bdelist'),
    ('early_warning', r'holding\(s\) in company|\bholdings in company\b|\btr-?1\b|\bnotification of major (holdings?|interest)|\bmajor shareholding\b|form 8\.3|form 8 \(|\brule 8\.3\b|\bdisclosure of interests?\b'),
    ('director_dealing', r'\bdirector/pdmr\b|\bpdmr\b|\bdirector(s)?\'? (share)?dealing|\bdirector shareholding\b|\bdirectors\' dealings\b|\bdirectorate change\b|\bboard change\b|\bappointment of (chief|director|chair|ceo|cfo|non-executive)|\bdirector appointment\b|\bboard appointment\b|\bresignation of\b|\bchange of adviser\b|\bchange of nominated adviser\b|\bchange of broker\b'),
    ('financial_statement', r'\bfinal results\b|\binterim results\b|\bhalf[- ]year(ly)? (results|report)\b|\bannual (results|report)\b|\bpreliminary results\b|\bfull[- ]year results\b|\bq[1-4] results\b|\b(first|second|third|fourth) quarter results\b|\bresults for the (year|period|six months|half year|quarter)\b|\bfinancial results\b|\bannual financial report\b|\bhalf-yearly report\b|\bquarterly report\b|\baudited (annual )?(results|accounts)\b|\bunaudited (interim )?results\b|\bpublication of annual report\b|\bannual report and accounts\b|\btrading (statement|update)\b|\bpre-close (trading )?(statement|update)\b'),
    ('agm_record_date', r'\bagm\b|\bannual general meeting\b|\bgeneral meeting\b|\begm\b|\bnotice of (meeting|agm|gm)\b|\bresult(s)? of (agm|annual general meeting|general meeting|meeting)\b|\bproxy\b|\brecord date\b|\bannual report and notice of\b'),
    ('corporate_action', r'\bdividend\b|\bdistribution\b|\bshare consolidation\b|\bsubdivision\b|\bshare split\b|\bcapital (reorganisation|reduction|return)\b|\bplacing\b|\bfundrais|\bopen offer\b|\brights issue\b|\bissue of (equity|shares)\b|\bblock ?listing\b|\btotal voting rights\b|\btransaction in own shares\b|\bshare buyback\b|\bbuy-?back\b|\bchange of name\b|\bname change\b|\badmission (of|to)\b|\bschedule one\b|\bschedule 1\b|\bfirst day of dealings\b|\bacquisition\b|\bdisposal\b|\brecommended (cash )?offer\b|\boffer for\b|\bscheme of arrangement\b|\btakeover\b|\bdemerger\b|\bmerger\b|\bcapital markets day\b|\bdebt (facility|refinancing)\b|\bconvertible\b|\bwarrant'),
    ('exchange_bulletin', r'.*'),
]
NOT_FIN = re.compile(r'drill|assay|exploration|sampling|geophys|geochem|intercept|mineral resource|resource estimate|feasibility|test results|survey results|trial results|study results|clinical|phase [123]|voting results|results of (the )?(annual|general|shareholder)|election results|results of (its )?(annual|general)|results of (agm|gm|egm|meeting)')
def classify(title, default='regulatory_announcement'):
    t = (title or '').lower()
    for typ, pat in TYPE_RULES[:-1]:
        if re.search(pat, t):
            if typ == 'financial_statement' and NOT_FIN.search(t): continue
            return typ
    return default
# Companies House filing categories -> event type and ch_filing_type (the registry's own category and type code are kept in detail)
CH_CATEGORY = {'accounts': ('ch_accounts_filed', 'accounts'), 'confirmation-statement': ('ch_confirmation_statement', 'confirmation statement'), 'annual-return': ('ch_confirmation_statement', 'annual return'),
               'officers': ('ch_officer_change', 'officers'), 'change-of-name': ('ch_name_change', 'change of name'), 'mortgage': ('ch_charge', 'charges'), 'capital': ('ch_capital', 'capital'),
               'incorporation': ('ch_other', 'incorporation'), 'address': ('ch_other', 'registered office address'), 'resolution': ('ch_resolution', 'resolution'), 'insolvency': ('ch_insolvency', 'insolvency'),
               'gazette': ('ch_gazette', 'gazette'), 'dissolution': ('ch_insolvency', 'dissolution'), 'persons-with-significant-control': ('ch_psc', 'persons with significant control'), 'miscellaneous': ('ch_other', 'miscellaneous'),
               'other': ('ch_other', 'other'), 'auditors': ('ch_auditor', 'auditors'), 'document-replacement': ('ch_other', 'document replacement'), 'change-of-constitution': ('ch_resolution', 'change of constitution'), 'reregistration': ('ch_other', 're-registration')}
def event(issuer, etype, date, title, source, url, read_by, wire='', detail='', rns_category='', ch_filing_type=''):
    return {'exchange': issuer['exchange'], 'ticker': issuer['ticker'], 'isin': issuer.get('isin', ''), 'lei': issuer.get('lei', ''), 'issuer': issuer['name'],
            'event_type': etype, 'date': date, 'title': html.unescape((title or '')).strip()[:300], 'wire': wire, 'source': source, 'url': url, 'read_by': read_by, 'detail': detail,
            'rns_category': rns_category, 'ch_filing_type': ch_filing_type}
