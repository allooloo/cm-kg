"""Pass 2.3 input — the latest annual report per issuer and its results announcements, from the SGXNet announcement pages the Width 1 reader found
(category 'Annual Reports and Related Documents' / 'Financial Statements and Related Announcement'): the page lists its PDF attachments on links.sgx.com,
which answer plain clients and carry a text layer. Kept per document in raw/reports/<announcementId>-<n>.json: the pages that carry the independent
auditor's report, the registrar mention, the period-end statement and going-concern language (text windows), never the whole document.
Read-by for the documents: 'SGXNet announcement PDF'."""
import io
import pypdf
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
AUD = re.compile(r"(?i)independent auditor|auditor'?s'? report|report on the audit|audit of the financial statements")
REG = re.compile(r'(?i)\bshare regist(?:ry|rar)\b|\bunit regist(?:ry|rar)\b')
GC = re.compile(r'(?i)going concern')
PE = re.compile(r'(?i)for the (?:financial )?year ended|for the half[- ]year ended|for the (?:first|second|third|fourth) quarter ended|for the period ended|year ended 31 December|year ended 30 June|year ended 31 March')
def windows(text, pat, n=6, span=1500):
    out = []
    for m in pat.finditer(text):
        out.append(text[max(0, m.start() - span // 3):m.end() + span]);
        if len(out) >= n: break
    return out
def read_pdf(data):
    rd = pypdf.PdfReader(io.BytesIO(data)); n = len(rd.pages); texts = []
    for i in range(n):
        try: texts.append(rd.pages[i].extract_text() or '')
        except Exception: texts.append('')
    full = '\n'.join(texts); chars = len(full)
    aud_pages = [i + 1 for i, t in enumerate(texts) if AUD.search(t)]
    return {'pages': n, 'text_chars': chars, 'no_text_layer': chars < 200 * max(1, n) // 10, 'auditor_pages': aud_pages[:12],
            'auditor_windows': [texts[p - 1][:6000] for p in aud_pages[:6]], 'registry_windows': windows(full, REG, 4, 500), 'going_concern_windows': windows(full, GC, 4, 600), 'period_windows': windows(full, PE, 3, 300), 'front_text': (texts[0] + '\n' + (texts[1] if n > 1 else ''))[:2500]}
def fetch(it):
    fn = f"raw/reports/{it['idsId']}.json"
    if os.path.exists(fn): return {'idsId': it['idsId'], 'cached': True}
    out = {'idsId': it['idsId'], 'key': it['key'], 'kind': it['kind'], 'viewer': it['viewer'], 'pdf_url': it['pdf_url'], 'date': it['date'], 'headline': it['headline']}
    y = get(it['pdf_url'], tries=2, timeout=180); data = y.content if y is not None and y.status_code == 200 else None
    if not data: out['error'] = 'PDF not fetched'; json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return out
    try: out.update(read_pdf(data))
    except Exception as e: out['error'] = repr(e)[:160]
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return {k: out[k] for k in ('idsId', 'key', 'kind', 'pdf_url', 'pages', 'text_chars', 'auditor_pages', 'error') if k in out}
if __name__ == '__main__':
    latest_ar = {}; res_ann = {}
    for e in events():
        if not e.get('read_by', '').startswith('links.sgx.com'): continue
        m = re.search(r'corporate-announcements/([A-Z0-9]{16})', e.get('url', ''))
        if not m: continue
        k = e['exchange'] + '|' + e['ticker']
        if k not in byk: continue
        cat = (e.get('sgx_category') or '') + ' ' + (e.get('title') or '')
        if re.search(r'(?i)annual report', cat):
            if k not in latest_ar or e['date'] > latest_ar[k]['date']: latest_ar[k] = {**e, 'aid': m.group(1)}
        elif re.search(r'(?i)financial statements|results', cat) and e.get('event_type') == 'results':
            res_ann.setdefault(k, []).append({**e, 'aid': m.group(1)})
    items = []
    def add(e, kind, want):
        docs = sgx_docs(e['url'], want)
        for i, (u, nm) in enumerate(docs[:2]):
            items.append({'idsId': f"{e['aid']}-{i}", 'key': e['exchange'] + '|' + e['ticker'], 'kind': kind, 'viewer': e['url'], 'pdf_url': u, 'date': e['date'], 'headline': (e.get('title') or '') + ' — ' + nm})
    for k, e in latest_ar.items(): add(e, 'annual_report', r'annual report|AR20|Annual_Report')
    for k, lst in res_ann.items():
        for e in sorted(lst, key=lambda x: x['date'], reverse=True)[:2]: add(e, 'results_announcement', None)
    print('documents to read: annual reports', sum(1 for i in items if i['kind'] == 'annual_report'), 'results announcements', sum(1 for i in items if i['kind'] != 'annual_report'), 'issuers with an annual report page', len(latest_ar), flush=True)
    shard = E.get('SHARD')
    if shard:
        i, n = (int(x) for x in shard.split('/')); items = [it for j, it in enumerate(items) if j % n == i]
    resume('annual_reports' + (f'_s{shard.split("/")[0]}' if shard else ''), fetch, items, threads=int(E.get('THREADS', '4')), keyf=lambda it: it['idsId'])
