"""Pass 2.1b — the structured facts of the latest 有価証券報告書 per issuer from EDINET's XBRL-to-CSV download (documents/<docID>?type=5, keyed): the
audit firm as a tagged fact (jpcrp_cor:AuditFirm1Consolidated / AuditFirm1NonConsolidated, AuditFirm2…), the fiscal year end (jpdei_cor:
CurrentFiscalYearEndDateDEI), the filer names as filed (jpdei_cor:FilerNameInJapaneseDEI / FilerNameInEnglishDEI), the securities code, plus the text
blocks that carry the shareholder-register administrator (株主名簿管理人) and going-concern notes (継続企業の前提) as Japanese windows for the Gemini
reader. A tagged fact is the regulator's own structured value: it is written as SOURCED (read-by names the XBRL element), never as a lab read.
Fast (about one second a document, ~80 KB). Kept per document in raw/xbrl/<key-hash>.json. Resumable."""
import io, hashlib, glob, zipfile, csv
from fc_common import *
EK = os.environ['EDINET_API_KEY']
issuers = load_issuers()
VIEW = 'https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?'
def latest_120():
    best = {}
    for p in [q for d, q in pond.drops(NODE, 'width1')]:
        for fn in glob.glob(os.path.join(p, 'edinet_daily', '*.json')):
            for it in json.load(open(fn, encoding='utf-8')).get('results') or []:
                if str(it.get('docTypeCode')) != '120' or not it.get('edinetCode'): continue
                dt = (it.get('submitDateTime') or '')[:10]
                if dt > (best.get(it['edinetCode']) or {}).get('date', ''): best[it['edinetCode']] = {'docID': it['docID'], 'date': dt}
    return best
L120 = latest_120()
REG = re.compile(r'株主名簿管理人'); GC = re.compile(r'継続企業の前提')
def windows(text, pat, before=150, after=350, cap=2):
    out = []
    for m in pat.finditer(text):
        w = re.sub(r'\s+', ' ', text[max(0, m.start() - before): m.end() + after]).strip()
        if not any(w[:60] == o[:60] for o in out): out.append(w)
        if len(out) >= cap: break
    return out
def parse(b):
    z = zipfile.ZipFile(io.BytesIO(b)); facts = {}; blocks = []
    for n in z.namelist():
        if not n.lower().endswith('.csv'): continue
        raw = z.read(n); t = None
        for enc in ('utf-16', 'utf-8-sig', 'cp932'):
            try: t = raw.decode(enc); break
            except Exception: pass
        if not t: continue
        rd = csv.reader(io.StringIO(t), delimiter='\t')
        try: hdr = next(rd)
        except StopIteration: continue
        for row in rd:
            if len(row) < 9: continue
            el, label, ctx, val = row[0], row[1], row[2], row[8]
            if not val or val == '－': continue
            if 'TextBlock' in el:
                if REG.search(val) or GC.search(val): blocks.append((el, label, val))
            else:
                facts.setdefault(el, []).append({'label': label, 'context': ctx, 'value': val})
    return facts, blocks
def first(facts, el):
    v = facts.get(el) or []
    return v[0]['value'].strip() if v else ''
def fetch(r):
    d = L120.get(r.get('reg_id') or '')
    if not d: return {'gap': 'no 有価証券報告書 (docTypeCode 120) in the 12-month lists'}
    h = hashlib.md5(key(r).encode()).hexdigest()[:12]; fn = f'raw/xbrl/{h}.json'
    if os.path.exists(fn): return {**json.load(open(fn, encoding='utf-8')), 'cached': True}
    b = None
    for i in range(4):
        try:
            x = requests.get(f"https://api.edinet-fsa.go.jp/api/v2/documents/{d['docID']}", params={'type': 5, 'Subscription-Key': EK}, headers=UA, timeout=180)
            if x.status_code == 200 and x.content[:2] == b'PK': b = x.content; break
            if x.status_code == 404: return {'gap': 'no XBRL-to-CSV file for this document (type=5 answers 404)', 'docID': d['docID']}
            time.sleep(4 * (i + 1))
        except Exception: time.sleep(4 * (i + 1))
    if b is None: return {'error': 'XBRL-CSV not downloadable', 'docID': d['docID']}
    facts, blocks = parse(b)
    firms = []
    for el in sorted(facts):
        if re.match(r'jpcrp_cor:AuditFirm\d(Consolidated|NonConsolidated)$', el):
            for f in facts[el]:
                v = f['value'].strip()
                if v and v not in [x['name'] for x in firms]: firms.append({'name': v, 'element': el})
    out = {'docID': d['docID'], 'document_url': VIEW + d['docID'], 'doc_date': d['date'], 'read_by': 'EDINET XBRL-to-CSV facts (API v2 type=5, 有価証券報告書 docTypeCode 120)',
           'audit_firms': firms, 'auditor': firms[0]['name'] if firms else '', 'auditor_element': firms[0]['element'] if firms else '',
           'fiscal_year_end': first(facts, 'jpdei_cor:CurrentFiscalYearEndDateDEI'), 'fiscal_year_start': first(facts, 'jpdei_cor:CurrentFiscalYearStartDateDEI'), 'filer_name_ja': first(facts, 'jpdei_cor:FilerNameInJapaneseDEI'), 'filer_name_en': first(facts, 'jpdei_cor:FilerNameInEnglishDEI'), 'sec_code': first(facts, 'jpdei_cor:SecurityCodeDEI'), 'edinet_code': first(facts, 'jpdei_cor:EDINETCodeDEI'),
           'audit_opinion_block': next((v[:600] for el, l, v in blocks if 'AuditOpinion' in el), ''),
           'registrar_windows': [w for el, l, v in blocks for w in windows(v, REG)][:3], 'registrar_elements': sorted({el for el, l, v in blocks if REG.search(v)})[:4],
           'going_concern_windows': [w for el, l, v in blocks for w in windows(v, GC)][:3], 'going_concern_elements': sorted({el for el, l, v in blocks if GC.search(v)})[:6], 'n_facts': sum(len(v) for v in facts.values())}
    os.makedirs('raw/xbrl', exist_ok=True); json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
    return out
if __name__ == '__main__':
    targets = [r for r in issuers if L120.get(r.get('reg_id') or '')]
    sh = E.get('SHARD')
    if sh: i, n = map(int, sh.split('/')); targets = targets[i::n]
    print('issuers with a 120 in the window:', len(targets), flush=True)
    resume('edinet_xbrl', fetch, targets, threads=int(E.get('THREADS', '4')), delay=0.2)
    rows = jload('raw/edinet_xbrl.jsonl'); print('xbrl rows', len(rows), 'with auditor fact', sum(1 for d in rows if d.get('auditor')), 'fiscal year end', sum(1 for d in rows if d.get('fiscal_year_end')), 'registrar windows', sum(1 for d in rows if d.get('registrar_windows')), 'going concern blocks', sum(1 for d in rows if d.get('going_concern_windows')), flush=True)
