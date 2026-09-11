"""SGXNet announcements without the SGX API (401 to machines): the announcement pages on links.sgx.com are public and machine-readable
(https://links.sgx.com/1.0.0/corporate-announcements/<ID>: Issuer/Manager, Securities (name - ISIN - code), Announcement Title = SGXNet category,
Date & Time of Broadcast, Sub Title, Announcement Reference). Discovery is by Tavily: a news search over the window and a general search, both
restricted to links.sgx.com, per corporate issuer. Every page hit is fetched and parsed; a PDF hit under /corporate-announcements/<ID>/ is resolved
to its page. The page's own Securities line must carry the issuer's SGX code or ISIN (the exchange record; exempt from the name rule); a FileOpen PDF
with no page carries only Tavily's published_date and title and passes the name rule in the assembler.
Read-by: 'links.sgx.com announcement page (SGXNet record; found by Tavily search)' / 'Tavily search (links.sgx.com) + published_date'.
Coverage is bounded by Tavily's index of links.sgx.com: reported as thin where thin, never padded."""
import re, os, json
from common import *
os.makedirs('raw/sgxnet_pages', exist_ok=True)
PAGE = re.compile(r'https?://links\.sgx\.com/1\.0\.0/corporate-announcements/([A-Z0-9]{16})(?:/|$|\?)')
def parse_page(html_text):
    t = html.unescape(html_text)
    def grab(label):
        m = re.search(re.escape(label) + r'\s*</dt>\s*<dd[^>]*>(.*?)</dd>', t, re.S | re.I)
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', m.group(1))).strip() if m else ''
    d = {'issuer': grab('Issuer/ Manager') or grab('Issuer/Manager'), 'securities': grab('Securities'), 'category': grab('Announcement Title'), 'broadcast': grab('Date &Time of Broadcast') or grab('Date & Time of Broadcast') or grab('Date &amp;Time of Broadcast'),
         'subtitle': grab('Announcement Sub Title'), 'reference': grab('Announcement Reference'), 'status': grab('Status')}
    if not d['category']:
        m = re.search(r'<title>(.*?)</title>', t, re.S)
        if m:
            parts = re.sub(r'\s+', ' ', m.group(1)).split('::'); d['category'] = parts[0].strip(); d['subtitle'] = d['subtitle'] or (parts[1].strip() if len(parts) > 1 else '')
    return d
def page(aid):
    fn = f'raw/sgxnet_pages/{aid}.json'
    if os.path.exists(fn): return json.load(open(fn, encoding='utf-8'))
    r = get(f'https://links.sgx.com/1.0.0/corporate-announcements/{aid}', timeout=60)
    d = parse_page(r.text) if r is not None and r.status_code == 200 else {'error': r.status_code if r is not None else 'no response'}
    d['aid'] = aid; json.dump(d, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return d
def fetch(r):
    evs = []; seen = set(); undated = []; foreign = 0; pages = 0; errors = 0
    q1 = {'query': r['name'], 'max_results': 20, 'topic': 'news', 'days': WINDOW_DAYS, 'include_domains': ['links.sgx.com']}
    q2 = {'query': f"{r['trading_name'] or r['name']} announcement", 'max_results': 20, 'include_domains': ['links.sgx.com']}
    for payload in (q1, q2):
        j = tavily(payload)
        for x in j.get('results', []):
            u = x['url']; m = PAGE.search(u)
            if m:
                aid = m.group(1)
                if aid in seen: continue
                seen.add(aid); d = page(aid); pages += 1
                if d.get('error'): errors += 1; continue
                sec = d.get('securities', '')
                if not (re.search(r'\b' + re.escape(r['ticker']) + r'\b', sec) or (r['isin'] and r['isin'] in sec)): foreign += 1; continue
                dt = to_iso(d.get('broadcast', ''))
                if not dt: undated.append({'url': f'https://links.sgx.com/1.0.0/corporate-announcements/{aid}', 'title': d.get('subtitle') or d.get('category')}); continue
                if not in_window(dt): continue
                title = (d.get('category') or 'SGXNet announcement') + (': ' + d['subtitle'] if d.get('subtitle') else '')
                evs.append(event(r, classify(d.get('subtitle') or d.get('category')), dt, title, 'SGXNet (links.sgx.com announcement page)', f'https://links.sgx.com/1.0.0/corporate-announcements/{aid}',
                                 'links.sgx.com announcement page (SGXNet record; found by Tavily search)', wire='SGXNet', sgx_category=d.get('category', ''), reference=d.get('reference', '')))
            elif 'links.sgx.com/FileOpen' in u:
                if u in seen: continue
                seen.add(u); dt = to_iso(x.get('published_date', ''))
                if not dt: undated.append({'url': u, 'title': x['title']}); continue
                if not in_window(dt): continue
                evs.append(event(r, classify(x['title']), dt, x['title'], 'SGXNet (links.sgx.com document)', u, 'Tavily search (links.sgx.com) + published_date', wire='SGXNet'))
    return {'events': evs, 'n': len(evs), 'pages': pages, 'other_issuer': foreign, 'page_errors': errors, 'undated': undated[:40]}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('sgxnet_search', fetch, issuers, threads=int(os.environ.get('THREADS', '4')))
