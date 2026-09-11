"""Pass 2.3 input — the latest annual report per issuer from the ASX announcements platform (the link recorded at Width 0), plus the Appendix 4E / 4D
announcements from Width 1. The viewer page carries the PDF link (announcements.asx.com.au/asxpdf/…); the PDF answers plain clients and carries a
text layer. Kept per document in raw/reports/<idsId>.json: the pages that carry the independent auditor's report, the share-registry mention,
the period-end statement and going-concern language (text windows), never the whole document. Read-by for the documents: 'ASX announcement PDF'."""
import io, hashlib
import pypdf
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + r['ASX code']: r for r in all_rows()}
AUD = re.compile(r"(?i)independent auditor|auditor'?s'? report|report on the audit|lead auditor|auditor'?s'? independence declaration")
REG = re.compile(r'(?i)\bshare regist(?:ry|rar)\b|\bsecurities registry\b')
GC = re.compile(r'(?i)going concern')
PE = re.compile(r'(?i)for the (?:financial )?year ended|for the half[- ]year ended|for the period ended|year ended 30 June|year ended 31 December')
def windows(text, pat, n=6, span=1500):
    out = []
    for m in pat.finditer(text):
        out.append(text[max(0, m.start() - span // 3):m.end() + span]);
        if len(out) >= n: break
    return out
def read_pdf(data, idsId):
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
    pdf_url, data = asx_pdf(it['viewer'])
    out = {'idsId': it['idsId'], 'key': it['key'], 'kind': it['kind'], 'viewer': it['viewer'], 'pdf_url': pdf_url, 'date': it['date'], 'headline': it['headline']}
    if not data: out['error'] = 'PDF not fetched'; json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return out
    try: out.update(read_pdf(data, it['idsId']))
    except Exception as e: out['error'] = repr(e)[:160]
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return {k: out[k] for k in ('idsId', 'key', 'kind', 'pdf_url', 'pages', 'text_chars', 'auditor_pages', 'error') if k in out}
if __name__ == '__main__':
    items = []; seen = set()
    for k, row in rows.items():
        v = row.get('Annual report (ASX announcement)') or ''
        m = re.search(r'idsId=(\d+)', v)
        if m and k in byk and m.group(1) not in seen:
            seen.add(m.group(1)); items.append({'idsId': m.group(1), 'key': k, 'kind': 'annual_report', 'viewer': v.split('  [')[0], 'date': (re.search(r'\[(\d{4}-\d{2}-\d{2})', v) or [None, ''])[1], 'headline': (v.split('  [')[1].rstrip(']')[11:] if '  [' in v else '')})
    for e in events():
        if e.get('event_type') == 'financial_statement' and re.search(r'(?i)appendix 4[ed]', e.get('title', '')) and e.get('read_by', '').startswith('asx.com.au'):
            m = re.search(r'idsId=(\d+)', e['url'])
            if m and m.group(1) not in seen: seen.add(m.group(1)); items.append({'idsId': m.group(1), 'key': e['exchange'] + '|' + e['ticker'], 'kind': 'appendix_4e_4d', 'viewer': e['url'], 'date': e['date'], 'headline': e['title']})
    print('documents to read: annual reports', sum(1 for i in items if i['kind'] == 'annual_report'), 'appendix 4E/4D', sum(1 for i in items if i['kind'] != 'annual_report'), flush=True)
    resume('annual_reports', fetch, items, threads=int(E.get('THREADS', '4')), keyf=lambda it: it['idsId'])
