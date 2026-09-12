"""Pass 2.1 input — the latest annual securities report (有価証券報告書, docTypeCode 120) per issuer from the Width 1 EDINET daily lists, downloaded as
PDF through the EDINET API (type=2, AGENT KEYS\\edinet.txt) and reduced to text windows: the auditor (会計監査人 / 監査法人 mentions in the governance
section and the audit report), the shareholder-register administrator (株主名簿管理人), the fiscal period statement (事業年度 自…至…) and going-concern
language (継続企業の前提). Kept per document in raw/reports/<key-hash>.json — the windows, never the whole document; the PDF is not stored.
Read-by for the documents: 'EDINET 有価証券報告書 PDF (API v2, docTypeCode 120)'. Resumable; SHARD=i/n splits the issuer list."""
import io, hashlib, glob
import pypdf
from fc_common import *
EK = os.environ['EDINET_API_KEY']
issuers = load_issuers(); byk = {key(r): r for r in issuers}
VIEW = 'https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?'
AUD = re.compile(r'監査法人|会計監査人|公認会計士')
REG = re.compile(r'株主名簿管理人')
GC = re.compile(r'継続企業の前提')
PE = re.compile(r'事業年度|当連結会計年度|自\s*\d{4}年\s*\d{1,2}月\s*\d{1,2}日\s*至|（自\s*\d{4}年')
def latest_120():
    """docID of the newest 有価証券報告書 per EDINET code from the width1 daily cache (every drop)."""
    best = {}
    for p in [q for d, q in pond.drops(NODE, 'width1')]:
        for fn in glob.glob(os.path.join(p, 'edinet_daily', '*.json')):
            for it in json.load(open(fn, encoding='utf-8')).get('results') or []:
                if str(it.get('docTypeCode')) != '120' or not it.get('edinetCode'): continue
                dt = (it.get('submitDateTime') or '')[:10]
                if dt > (best.get(it['edinetCode']) or {}).get('date', ''): best[it['edinetCode']] = {'docID': it['docID'], 'date': dt, 'desc': it.get('docDescription') or '', 'period': f"{it.get('periodStart')}..{it.get('periodEnd')}"}
    return best
L120 = latest_120()
def windows(text, pat, before=200, after=400, cap=4):
    out = []
    for m in pat.finditer(text):
        w = re.sub(r'\s+', ' ', text[max(0, m.start() - before): m.end() + after]).strip()
        if not any(w[:60] == o[:60] for o in out): out.append(w)
        if len(out) >= cap: break
    return out
def fetch(r):
    d = L120.get(r.get('reg_id') or '')
    if not d: return {'gap': 'no 有価証券報告書 (docTypeCode 120) for this EDINET code in the 12-month lists'}
    h = hashlib.md5(key(r).encode()).hexdigest()[:12]; fn = f'raw/reports/{h}.json'
    if os.path.exists(fn): return {**json.load(open(fn, encoding='utf-8')), 'cached': True}
    u = f"https://api.edinet-fsa.go.jp/api/v2/documents/{d['docID']}?type=2&Subscription-Key={EK}"
    b = None
    for i in range(4):
        try:
            x = requests.get(u, headers=UA, timeout=180)
            if x.status_code == 200 and x.content[:4] == b'%PDF': b = x.content; break
            time.sleep(4 * (i + 1))
        except Exception: time.sleep(4 * (i + 1))
    if b is None: return {'error': 'PDF not downloadable', 'docID': d['docID']}
    pdf = pypdf.PdfReader(io.BytesIO(b)); pages = []
    for p in pdf.pages:
        try: pages.append(p.extract_text() or '')
        except Exception: pages.append('')
    text = '\n'.join(pages)
    out = {'docID': d['docID'], 'document_url': VIEW + d['docID'], 'doc_date': d['date'], 'desc': d['desc'], 'period': d['period'], 'pages': len(pages), 'bytes': len(b), 'read_by': 'EDINET 有価証券報告書 PDF (API v2, docTypeCode 120)',
           'auditor_windows': windows(text, AUD), 'registrar_windows': windows(text, REG, cap=2), 'period_windows': windows(text, PE, before=60, after=160, cap=2), 'going_concern_windows': windows(text, GC, before=150, after=300, cap=2)}
    os.makedirs('raw/reports', exist_ok=True); json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
    return out
if __name__ == '__main__':
    targets = [r for r in issuers if r.get('reg_id')]
    sh = E.get('SHARD')
    if sh: i, n = map(int, sh.split('/')); targets = targets[i::n]
    print('issuers with an EDINET code:', len(targets), '| with a 120 in the window:', sum(1 for r in targets if L120.get(r['reg_id'])), flush=True)
    resume('edinet_docs', fetch, targets, threads=int(E.get('THREADS', '3')), delay=0.3)
