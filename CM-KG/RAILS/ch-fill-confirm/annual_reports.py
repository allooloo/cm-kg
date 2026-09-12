"""Pass 2.3 input — the latest annual report per issuer, found on the issuer's own site by Tavily (query "<name> Geschäftsbericht annual report pdf",
PDF results only, issuer name in the page title / URL host, newest year in the URL or title wins). Kept per document in raw/reports/<key-hash>.json: the pages
that carry the independent auditor's report (Bericht der Revisionsstelle / Bestätigungsvermerk), the share-register mention, the period-end statement and
going-concern language (text windows), never the whole document. Read-by for the documents: 'issuer-site annual report PDF (found by Tavily)'."""
import io, hashlib
import pypdf
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
AUD = re.compile(r"(?i)independent auditor|auditor'?s'? report|report on the audit|bericht der revisionsstelle|bestätigungsvermerk|revisionsstelle|rapport de l'organe de révision|wirtschaftsprüfer")
REG = re.compile(r'(?i)\bshare regist(?:ry|rar|er)\b|\baktienregister\b|\bregistre des actions\b')
GC = re.compile(r'(?i)going concern|fortführung|unternehmensfortführung|continuité')
PE = re.compile(r'(?i)for the (?:financial )?year ended|geschäftsjahr (?:zum|per|endend)|für das geschäftsjahr|exercice clos|year ended 31 december|per 31\. dezember')
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
def find_report(r):
    nm = r.get('full_name') or r['name']
    j = tavily({'query': f"{nm} Geschäftsbericht annual report {TODAY.year - 1} pdf", 'max_results': 10})
    best = None
    for x in j.get('results', []):
        u = x['url']
        if not re.search(r'(?i)\.pdf(\?|$)', u): continue
        if not name_match(x['title'] + ' ' + u, r['name'], (r.get('full_name'),))[0] in ('full', 'distinctive'): continue
        if not re.search(r'(?i)annual|geschäftsbericht|jahresbericht|rapport annuel|financial report|finanzbericht|integrated report', x['title'] + u): continue
        y = re.findall(r'20(2[0-9])', x['title'] + ' ' + u); year = max((int('20' + v) for v in y), default=0)
        if best is None or year > best[0]: best = (year, u, x['title'])
    return best
def fetch(r):
    k = key(r); h = hashlib.md5(k.encode()).hexdigest()[:12]; fn = f"raw/reports/{h}.json"
    if os.path.exists(fn): return {'idsId': h, 'cached': True}
    b = find_report(r)
    out = {'idsId': h, 'key': k, 'kind': 'annual_report'}
    if not b: out['error'] = 'no annual report PDF found on the issuer site (Tavily)'; json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return out
    year, u, title = b; out.update({'viewer': u, 'pdf_url': u, 'date': f'{year}-12-31' if year else '', 'headline': title[:160]})
    y = get(u, tries=2, timeout=180); data = y.content if y is not None and y.status_code == 200 and (y.headers.get('content-type') or '').lower().find('pdf') >= 0 or (y is not None and y.status_code == 200 and y.content[:5] == b'%PDF-') else None
    if not data: out['error'] = 'PDF not fetched'; json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return out
    try: out.update(read_pdf(data))
    except Exception as e: out['error'] = repr(e)[:160]
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return {k2: out[k2] for k2 in ('idsId', 'key', 'kind', 'pdf_url', 'pages', 'text_chars', 'auditor_pages', 'error') if k2 in out}
if __name__ == '__main__':
    items = issuers
    print('issuers to search for an annual report PDF:', len(items), flush=True)
    shard = E.get('SHARD')
    if shard:
        i, n = (int(x) for x in shard.split('/')); items = [it for j, it in enumerate(items) if j % n == i]
    resume('annual_reports' + (f'_s{shard.split("/")[0]}' if shard else ''), fetch, items, threads=int(E.get('THREADS', '4')), keyf=lambda it: hashlib.md5(key(it).encode()).hexdigest()[:12])
