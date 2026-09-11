"""Shared pieces for the Canada Width 1 (Disclosure) rail."""
import os, re, json, sys, time, threading, datetime, html
import requests, openpyxl
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\ca-width0')
import keys  # loads AGENT KEYS into env; never printed
ISSUERS_XLSX = r'C:\ALLOOLOO\CM-KG\ISSUERS\ca-issuers.xlsx'
TMX_XLSX = r'C:\ALLOOLOO\CM-KG\RAILS\ca-width0\raw\tmx_571.xlsx'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
TAV = os.environ.get('TAVILY_API_KEY', ''); TH = {'Authorization': 'Bearer ' + TAV}
TODAY = datetime.date.today()
WINDOW_DAYS = int(os.environ.get('WINDOW_DAYS', '365'))
SINCE = TODAY - datetime.timedelta(days=WINDOW_DAYS)
os.makedirs('raw', exist_ok=True)
CORP_TYPES = ('Corporate', 'CPC', 'Income Trust', 'Corporate (unclassified)')
STOP = {'inc', 'corp', 'corporation', 'ltd', 'limited', 'the', 'company', 'co', 'trust', 'fund', 'group', 'holdings', 'plc', 'ltee', 'incorporated', 'income', 'reit', 'resources', 'mining', 'gold', 'minerals', 'metals', 'energy', 'capital', 'ventures', 'technologies', 'technology', 'international', 'global', 'canada', 'canadian', 'exploration', 'and'}
def norm(s): return re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower().replace('&', ' and '))
def keytoks(n):
    t = [w for w in norm(n).split() if w not in STOP]
    if not t: t = [w for w in norm(n).split() if w not in ('inc', 'corp', 'ltd', 'the')]
    return t[:2] if t else norm(n).split()[:1]
_UNIQUE = None; _COMMON = None
def _unique_tokens():
    """tokens (len>=5, not STOP) that occur in exactly one issuer name across the FULL 4,820-row roster (all four tabs, funds included)"""
    global _UNIQUE
    if _UNIQUE is None:
        from collections import Counter
        c = Counter()
        wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True)
        for ex in ['TSX', 'TSXV', 'CSE', 'Cboe Canada']:
            ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it); i = hdr.index('Legal name')
            for row in it:
                for t in set(w for w in norm(row[i] or '').split() if w not in STOP and len(w) >= 5): c[t] += 1
        _UNIQUE = set(t for t, n in c.items() if n == 1)
    return _UNIQUE
def _common_words():
    """common English + French words (google-10000-english + top 15,000 French frequency list), ascii-folded; kept in the rail as common_words.txt"""
    global _COMMON
    if _COMMON is None:
        fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'common_words.txt')
        _COMMON = set(l.strip() for l in open(fn, encoding='utf-8')) if os.path.exists(fn) else set()
    return _COMMON
def name_match(text, name):
    """('full', '') when every key token of the issuer name is in the text;
       ('distinctive', tok) when a name token in the text is unique across the full roster AND not a common English/French word;
       ('ambiguous', tok) when the only name token(s) in the text fail either test; ('none', '') when no name token is in the text."""
    n = norm(text); toks = keytoks(name)
    if all(k in n for k in toks): return 'full', ''
    words = set(n.split()); uniq = _unique_tokens(); common = _common_words()
    core = [w for w in norm(name).split() if w not in STOP and len(w) >= 5]
    present = [w for w in core if w in words]
    for w in present:
        if w in uniq and w not in common: return 'distinctive', w
    return ('ambiguous', present[0]) if present else ('none', '')
def name_in(text, name): return name_match(text, name)[0] in ('full', 'distinctive')
def load_issuers():
    """Corporate issuers from ca-issuers.xlsx, plus TSXV PO ids from the TMX workbook."""
    wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True); out = []
    for ex in ['TSX', 'TSXV', 'CSE', 'Cboe Canada']:
        ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it)
        for r in it:
            d = dict(zip(hdr, r))
            if str(d['Security type']).split(' (')[0] not in CORP_TYPES and str(d['Security type']) not in CORP_TYPES: continue
            out.append({'exchange': ex, 'ticker': d['Ticker'], 'root': d['Root ticker'], 'name': d['Legal name'], 'isin': d['ISIN'] or '', 'lei': d['LEI'] or '',
                        'wire': (d['Newswire of habit'] or '').split(' (')[0], 'wire_urls': (d['Newswire releases seen'] or '').split('\n') if d['Newswire releases seen'] else [], 'sedar_no': d['SEDAR+ issuer number'] or ''})
    po = {}
    if os.path.exists(TMX_XLSX):
        wb2 = openpyxl.load_workbook(TMX_XLSX, read_only=True)
        sheet = next(s for s in wb2.sheetnames if s.upper().startswith('TSXV ISSUERS')); rr = list(wb2[sheet].iter_rows(values_only=True))
        hi = next(i for i, row in enumerate(rr) if row and 'Exchange' in [str(c).strip() for c in row if c]); hdr = [str(c).replace('\n', ' ').strip() if c else None for c in rr[hi]]
        for r in rr[hi + 1:]:
            d = dict(zip(hdr, r))
            if d.get('PO ID'): po[str(d['Root Ticker']).split('.')[0]] = str(d['PO ID'])
    for r in out:
        if r['exchange'] == 'TSXV': r['po_id'] = po.get(r['root'], '')
    return out
def key(r): return r['exchange'] + '|' + r['ticker']
MON = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
def to_iso(s):
    """'Aug 25, 2026' / 'September 3, 2026' / '17/Jun/2026' / '2026-09-09T15:16:09-04:00' / '20230621' -> 'YYYY-MM-DD' or ''"""
    if not s: return ''
    s = str(s).strip()
    m = re.match(r'(20\d\d)-(\d\d)-(\d\d)', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m = re.match(r'([A-Za-z]{3,9})\.? (\d{1,2}), (20\d\d)', s)
    if m and m.group(1)[:3].lower() in MON: return f'{m.group(3)}-{MON[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}'
    m = re.match(r'(\d{1,2})/([A-Za-z]{3})/(20\d\d)', s)
    if m and m.group(2).lower() in MON: return f'{m.group(3)}-{MON[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'
    m = re.match(r'(20\d\d)(\d\d)(\d\d)$', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m = re.match(r'(20\d\d)/(\d\d)/(\d\d)', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m = re.match(r'[A-Za-z]{3}, (\d{1,2}) ([A-Za-z]{3}) (20\d\d)', s)  # 'Tue, 05 May 2026 ...'
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
WIRE_DOMS = {'newswire.ca': 'Canada Newswire (CNW)', 'prnewswire.com': 'PR Newswire', 'newsfilecorp.com': 'Newsfile', 'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'accesswire.com': 'ACCESS Newswire', 'accessnewswire.com': 'ACCESS Newswire', 'thenewswire.com': 'TheNewswire'}
def wire_of(url):
    d = re.sub(r'^https?://', '', url).split('/')[0].lower(); d = '.'.join(d.split('.')[-2:]); return WIRE_DOMS.get(d, '')
def url_date(url):
    m = re.search(r'/(20\d\d)/(\d{1,2})/(\d{1,2})/', url)      # globenewswire (month/day may be one digit)
    if m: return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    m = re.search(r'/news/home/(20\d\d)(\d\d)(\d\d)', url)     # businesswire
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    return ''
# ---- event typing from a title (wire releases and bulletins) — the event date is always the release/bulletin date, never a date read out of the headline
TYPE_RULES = [
    ('halt_resume', r'\b(trading )?halt(ed|s)?\b|\bresum(es|ed|ption)\b.*\btrading\b|\bresume trading\b|\bcease trade\b'),
    ('early_warning', r'early warning|\bform 62-103\b|\bacquisition of (common )?shares of\b.*\bearly warning\b|files early warning'),
    ('financial_statement', r'\bfinancial results\b|\b(first|second|third|fourth|q[1-4])[ -]quarter\b.{0,50}\b(results|earnings|financials)\b|\b(results|earnings)\b.{0,40}\b(first|second|third|fourth|q[1-4])[ -]quarter\b|\b(annual|year[- ]end|full[- ]year|fiscal (year|20\d\d|q[1-4]))\b.{0,50}\b(results|earnings)\b|\bfinancial statements\b|\bmd&a\b|\b(quarterly|annual) (financial )?(results|earnings)\b|\b(reports?|announces?)\b.{0,30}\b(fy|h[12]|20\d\d)\b.{0,20}\bresults\b|\bearnings\b'),
    ('agm_record_date', r'annual (general |and special )?meeting|\bagm\b|\bannual meeting\b|\bspecial meeting\b|meeting of shareholders|\brecord date\b'),
    ('corporate_action', r'\bdividend\b|\bdistribution\b|\bconsolidat(ion|es|ed)\b|reverse split|\bstock split\b|\bshare split\b|rights offering|\bspin[- ]?off\b|\bname change\b|change of name|\bsymbol change\b|\bdelist(ing|ed)?\b|\bnew listing\b|\bgraduat(es|ion)\b|normal course issuer bid|\bncib\b|\bcusip\b|\bexchange offer\b|\bwarrant expir'),
    ('exchange_bulletin', r'.*'),
]
NOT_FIN = re.compile(r'metallurg|drill|assay|exploration|sampling|geophys|geochem|intercept|mineral resource|resource estimate|feasibility|test results|survey results|trial results|study results|clinical|phase [123]|voting results|results of (the )?(annual|special|shareholder)|election results|results of (its )?(annual|special)')
def classify(title, default='newswire_release'):
    t = (title or '').lower()
    for typ, pat in TYPE_RULES[:-1]:
        if re.search(pat, t):
            if typ == 'financial_statement' and NOT_FIN.search(t): continue
            return typ
    return default
def event(issuer, etype, date, title, source, url, read_by, wire='', detail=''):
    return {'exchange': issuer['exchange'], 'ticker': issuer['ticker'], 'isin': issuer.get('isin', ''), 'lei': issuer.get('lei', ''), 'issuer': issuer['name'],
            'event_type': etype, 'date': date, 'title': (title or '').strip()[:300], 'wire': wire, 'source': source, 'url': url, 'read_by': read_by, 'detail': detail}
