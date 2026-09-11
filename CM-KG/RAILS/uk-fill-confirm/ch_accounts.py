"""Pass 2.3 input — the latest accounts filing per issuer from the Companies House document API (key in AGENT KEYS; never printed):
   filing (from Width 0 ch_api.jsonl) -> GET /company/<n>/filing-history/<tid> -> links.document_metadata -> GET <meta>/content (Accept: application/pdf)
The PDF is read in memory with pypdf; the pages that carry the independent auditor's report (and the strategic/directors' report mentions of
registrar and auditor) are kept as text windows in raw/accounts_text/<number>.json for the ChatGPT batch read. The PDF bytes are kept in raw/accounts_pdf/ for the ChatGPT
batch read (Companies House accounts are image PDFs; pypdf finds no text layer). Resource types on the document (pdf / xhtml) are recorded. Nothing else from the accounts is kept. Rate limit 600 calls per five minutes."""
import io, re, json, sys, os, time, threading
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0'); import keys
import requests, pypdf
from concurrent.futures import ThreadPoolExecutor
KEY = open(r'C:\ALLOOLOO\AGENT KEYS\companieshouse.txt', encoding='utf-8').read().strip()
API = 'https://api.company-information.service.gov.uk'
os.makedirs('raw/accounts_text', exist_ok=True); os.makedirs('raw/accounts_pdf', exist_ok=True)
lock = threading.Lock(); calls = [0]; window = [time.time()]
def throttle():
    with lock:
        if calls[0] >= 550:
            wait = 300 - (time.time() - window[0])
            if wait > 0: time.sleep(wait)
            calls[0] = 0; window[0] = time.time()
        calls[0] += 1
def get(url, **kw):
    for attempt in range(5):
        throttle()
        try:
            r = requests.get(url, auth=(KEY, ''), timeout=300, **kw)
            if r.status_code == 429: time.sleep(30); continue
            return r
        except Exception:
            time.sleep(5)
    return None
AUD = re.compile(r"(?i)independent auditor|auditor'?s'? report|statutory auditor|report on the audit of the financial statements")
REG = re.compile(r'(?i)\bregistrars?\b')
rows = [json.loads(l) for l in open(r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0\raw\ch_api.jsonl', encoding='utf-8')]
items = [r for r in rows if (r.get('accounts_filing') or {}).get('transaction_id')]
done = set(f[:-5] for f in os.listdir('raw/accounts_text'))
todo = [r for r in items if r['number'] not in done]
print('accounts filings', len(items), 'todo', len(todo), flush=True)
def work(r):
    num = r['number']; tid = r['accounts_filing']['transaction_id']; out = {'number': num, 'key': r['key'], 'filing_date': r['accounts_filing'].get('date'), 'description': r['accounts_filing'].get('description'), 'transaction_id': tid,
                                                                             'document_url': f'https://find-and-update.company-information.service.gov.uk/company/{num}/filing-history/{tid}/document?format=pdf&download=0'}
    try:
        fh = get(f'{API}/company/{num}/filing-history/{tid}')
        meta_url = ((fh.json().get('links') or {}).get('document_metadata')) if fh is not None and fh.status_code == 200 else None
        if not meta_url: out['error'] = f'filing HTTP {fh.status_code if fh is not None else "none"} / no document link'; return out
        m = get(meta_url); mj = m.json() if m is not None and m.status_code == 200 else {}
        out['pages'] = mj.get('pages'); out['bytes'] = ((mj.get('resources') or {}).get('application/pdf') or {}).get('content_length'); out['resources'] = list((mj.get('resources') or {}).keys())
        c = get(meta_url + '/content', headers={'Accept': 'application/pdf'}, allow_redirects=True)
        if c is None or c.status_code != 200: out['error'] = f'document content HTTP {c.status_code if c is not None else "none"}'; return out
        open(f'raw/accounts_pdf/{num}.pdf', 'wb').write(c.content); out['pdf'] = f'raw/accounts_pdf/{num}.pdf'
        rd = pypdf.PdfReader(io.BytesIO(c.content)); n = len(rd.pages); out['pages_read'] = n
        texts = []; aud_pages = []; reg_pages = []; chars = 0
        for i in range(n):
            try: t = rd.pages[i].extract_text() or ''
            except Exception: t = ''
            texts.append(t); chars += len(t)
            if AUD.search(t): aud_pages.append(i)
            if REG.search(t): reg_pages.append(i)
        out['text_chars'] = chars
        if chars < 200 * max(1, n) // 10: out['no_text_layer'] = True
        win = []
        for i in aud_pages[:12]: win.append({'page': i + 1, 'text': texts[i][:6000]})
        rwin = []
        for i in reg_pages[:6]:
            for mm in REG.finditer(texts[i]):
                rwin.append({'page': i + 1, 'text': texts[i][max(0, mm.start() - 300):mm.end() + 300]}); break
        out['auditor_pages'] = [i + 1 for i in aud_pages]; out['auditor_windows'] = win; out['registrar_windows'] = rwin
        out['front_text'] = (texts[0] + '\n' + (texts[1] if n > 1 else ''))[:2500]
    except Exception as e:
        out['error'] = repr(e)[:200]
    return out
def save(o):
    with lock: json.dump(o, open(f"raw/accounts_text/{o['number']}.json", 'w', encoding='utf-8'), ensure_ascii=False)
cnt = [0]
def run(r):
    o = work(r); save(o)
    with lock:
        cnt[0] += 1
        if cnt[0] % 50 == 0: print(cnt[0], '/', len(todo), flush=True)
with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '3'))) as ex: list(ex.map(run, todo))
print('DONE', flush=True)
