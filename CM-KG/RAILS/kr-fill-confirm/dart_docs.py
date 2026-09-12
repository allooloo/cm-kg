"""Pass 2.2 input — the main document of the latest 사업보고서 (annual report) per issuer through the DART document API (document.xml, keyed): the zip
holds the report XML and its attachments; the main file (<rcept_no>.xml) is reduced to Korean text windows — the transfer agent / register
administrator (명의개서대리인), the auditor line (감사인 / 회계감사인), the fiscal period (사업연도) and going-concern language (계속기업). Kept per document in
raw/reports/<key-hash>.json, never the whole document. The receipt number comes from the auditor endpoint row (dart_auditor.jsonl) or the Width 1
event list. Read-by: 'DART 사업보고서 document (document.xml API)'. Resumable; SHARD=i/n splits the list. DART answers this endpoint slowly (~30 s a
document) — the registrar route is the long pole of the Korean Fill pass."""
import io, hashlib, zipfile
from fc_common import *
DK = os.environ['DART_API_KEY']
issuers = load_issuers(); byk = {key(r): r for r in issuers}
VIEW = 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo='
aud = {d['key']: d for d in jload('raw/dart_auditor.jsonl') if d.get('rcept_no')}
ev_rn = {}
for e in events():
    if (e.get('title') or '').startswith('사업보고서') and e.get('reference'):
        k = e['exchange'] + '|' + e['ticker']
        if e['date'] > ev_rn.get(k, ('', ''))[0]: ev_rn[k] = (e['date'], e['reference'])
REG = re.compile(r'명의개서대리인|명의개서\s*대행')
AUD = re.compile(r'회계감사인|감사인의\s*명칭|독립된\s*감사인')
PE = re.compile(r'사업연도|당기\s*\(제\s*\d+\s*기\)')
GC = re.compile(r'계속기업')
def windows(text, pat, before=200, after=400, cap=3):
    out = []
    for m in pat.finditer(text):
        w = text[max(0, m.start() - before): m.end() + after].strip()
        if not any(w[:60] == o[:60] for o in out): out.append(w)
        if len(out) >= cap: break
    return out
def fetch(r):
    k = key(r); rn = (aud.get(k) or {}).get('rcept_no') or ev_rn.get(k, ('', ''))[1]
    if not rn: return {'gap': 'no 사업보고서 receipt number for this issuer'}
    h = hashlib.md5(k.encode()).hexdigest()[:12]; fn = f'raw/reports/{h}.json'
    if os.path.exists(fn): return {**json.load(open(fn, encoding='utf-8')), 'cached': True}
    b = None
    for i in range(3):
        try:
            x = requests.get('https://opendart.fss.or.kr/api/document.xml', params={'crtfc_key': DK, 'rcept_no': rn}, headers=UA, timeout=300)
            if x.status_code == 200 and x.content[:2] == b'PK': b = x.content; break
            time.sleep(5 * (i + 1))
        except Exception: time.sleep(5 * (i + 1))
    if b is None: return {'error': 'document zip not downloadable', 'docID': rn}
    z = zipfile.ZipFile(io.BytesIO(b)); names = z.namelist(); main = next((n for n in names if n == f'{rn}.xml'), names[0])
    raw = z.read(main); txt = None
    for enc in ('utf-8', 'euc-kr', 'cp949'):
        try: txt = raw.decode(enc); break
        except Exception: pass
    txt = txt or raw.decode('utf-8', 'replace'); t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', txt))
    out = {'docID': rn, 'document_url': VIEW + rn, 'doc_date': f'{rn[:4]}-{rn[4:6]}-{rn[6:8]}', 'files': len(names), 'bytes': len(b), 'chars': len(t), 'read_by': 'DART 사업보고서 document (document.xml API)',
           'registrar_windows': windows(t, REG), 'auditor_windows': windows(t, AUD, cap=2), 'period_windows': windows(t, PE, before=60, after=160, cap=2), 'going_concern_windows': windows(t, GC, before=150, after=300, cap=2)}
    os.makedirs('raw/reports', exist_ok=True); json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
    return out
if __name__ == '__main__':
    targets = [r for r in issuers if key(r) in aud or key(r) in ev_rn]
    sh = E.get('SHARD')
    if sh: i, n = map(int, sh.split('/')); targets = targets[i::n]
    print('issuers with a 사업보고서 receipt:', len(targets), flush=True)
    resume('dart_docs', fetch, targets, threads=int(E.get('THREADS', '4')))
