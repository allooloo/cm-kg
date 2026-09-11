"""Newswire releases from the wire's own per-company listing page (dated, complete for the page depth):
   Newsfile  https://www.newsfilecorp.com/company/<id>/<name>   (latest 20; company page found by Tavily site search)
   Cision    https://www.newswire.ca/news/<slug>/?page=N         (25 per page, walked back to the window start; slug derived from the name, Tavily fallback)
   PR Newswire https://www.prnewswire.com/news/<slug>/?page=N    (25 per page; slug keeps trailing punctuation)
Read-by: '<wire> company page'. Only issuers whose newswire of habit is one of these three."""
import re, html, json
from common import *
MONTHS = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
def slug_cnw(n):
    s = n.lower().replace('&', 'and'); return re.sub(r'[^a-z0-9]+', '-', s).strip('-')
def slug_prn(n):
    s = n.lower().replace('&', 'and'); s = re.sub(r'[^a-z0-9.]+', '-', s).strip('-'); return s
def newsfile_page(r):
    url = ''
    for u in r.get('wire_urls', []):
        if 'newsfilecorp.com/release/' in u:
            x = get(u)
            if x is not None and x.status_code == 200:
                m = re.search(r'href="(?:https://www\.newsfilecorp\.com)?(/company/\d+/[^"]+)"', x.text)
                if m: url = 'https://www.newsfilecorp.com' + m.group(1); break
    if not url:
        j = tavily({'query': r['name'], 'max_results': 8, 'include_domains': ['newsfilecorp.com']})
        for x in j.get('results', []):
            if re.search(r'newsfilecorp\.com/company/\d+/', x['url']) and name_in(x['title'] + ' ' + x['url'].replace('-', ' '), r['name']): url = x['url'].split('?')[0]; break
        if not url:
            for x in j.get('results', []):
                if '/release/' in x['url'] and name_in(x['title'], r['name']):
                    y = get(x['url'])
                    if y is not None and y.status_code == 200:
                        m = re.search(r'href="(?:https://www\.newsfilecorp\.com)?(/company/\d+/[^"]+)"', y.text)
                        if m: url = 'https://www.newsfilecorp.com' + m.group(1); break
    if not url: return {'gap': 'Newsfile company page not found', 'events': []}
    x = get(url)
    if x is None or x.status_code != 200: return {'gap': f'Newsfile company page http {x.status_code if x else "none"}', 'events': [], 'page': url}
    evs = []
    for f in re.findall(r'<figure[^>]*>(.*?)</figure>', x.text, re.S):
        a = re.search(r'<a[^>]+href="(/release/\d+/[^"]+)"[^>]*>(.*?)</a>', f, re.S); d = re.search(r'(' + MONTHS + r' \d{1,2}, 20\d\d)', f)
        if not (a and d): continue
        date = to_iso(d.group(1)); title = html.unescape(re.sub(r'<[^>]+>', '', a.group(2))).strip()
        if in_window(date): evs.append(event(r, classify(title), date, title, 'Newsfile', 'https://www.newsfilecorp.com' + a.group(1), 'newsfilecorp.com company page', wire='Newsfile'))
    return {'events': evs, 'page': url, 'n': len(evs), 'note': 'Newsfile company page lists the latest 20 releases only'}
def cision_pages(r, base, slug, wire, read_by):
    evs = []; page = 1; found_page = False; oldest = ''
    while page <= 12:
        u = f'{base}/news/{slug}/' + (f'?page={page}' if page > 1 else '')
        x = get(u)
        if x is None or x.status_code != 200: break
        found_page = True; n_page = 0
        for m in re.finditer(r'<a class="newsreleaseconsolidatelink[^"]*" href="(/news-releases/[^"]+\.html?)"', x.text):
            seg = x.text[m.end():m.end() + 4000]; nxt = seg.find('newsreleaseconsolidatelink'); seg = seg[:nxt] if nxt > 0 else seg
            d = re.search(r'<small>([^<]+)</small>', seg); t = re.search(r'</small>\s*(.*?)</h3>', seg, re.S)
            if not (d and t): continue
            date = to_iso(d.group(1).strip()); title = html.unescape(re.sub(r'<[^>]+>', '', t.group(1))).strip(); n_page += 1; oldest = date or oldest
            if in_window(date): evs.append(event(r, classify(title), date, title, wire, base + m.group(1), read_by, wire=wire))
        if n_page == 0 or (oldest and oldest < SINCE.isoformat()): break
        page += 1
    return evs, found_page, page
def cnw(r):
    slug = slug_cnw(r['name']); evs, ok, pages = cision_pages(r, 'https://www.newswire.ca', slug, 'Canada Newswire (CNW)', 'newswire.ca company page')
    if not ok or not evs:  # page missing, or a stale slug whose releases stop before the window: find the current company page
        j = tavily({'query': r['name'] + ' news releases', 'max_results': 10, 'include_domains': ['newswire.ca']})
        cands = []
        for x in j.get('results', []):
            m = re.match(r'https?://(?:www\.)?newswire\.ca/news/([^/?]+)/?', x['url'])
            if m and m.group(1) != slug and name_in(m.group(1).replace('-', ' '), r['name']) and m.group(1) not in cands: cands.append(m.group(1))
        for c in cands[:3]:
            evs2, ok2, pages2 = cision_pages(r, 'https://www.newswire.ca', c, 'Canada Newswire (CNW)', 'newswire.ca company page')
            if ok2 and evs2: slug, evs, ok, pages = c, evs2, ok2, pages2; break
            if ok2 and not ok: slug, ok, pages = c, ok2, pages2
    if not ok: return {'gap': 'Cision company page not found', 'events': []}
    return {'events': evs, 'page': f'https://www.newswire.ca/news/{slug}/', 'pages': pages, 'n': len(evs)}
def prn(r):
    slugs = [slug_prn(r['name']), slug_cnw(r['name'])]
    j = tavily({'query': r['name'], 'max_results': 10, 'include_domains': ['prnewswire.com']})
    for x in j.get('results', []):
        m = re.match(r'https?://(?:www\.)?prnewswire\.com/news/([^/?]+)/?$', x['url'])
        if m and name_in(m.group(1).replace('-', ' '), r['name']) and m.group(1) not in slugs: slugs.append(m.group(1))
    best = None
    for slug in slugs:
        evs, ok, pages = cision_pages(r, 'https://www.prnewswire.com', slug, 'PR Newswire', 'prnewswire.com company page')
        if ok and evs: return {'events': evs, 'page': f'https://www.prnewswire.com/news/{slug}/', 'pages': pages, 'n': len(evs)}
        if ok and best is None: best = {'events': [], 'page': f'https://www.prnewswire.com/news/{slug}/', 'pages': pages, 'n': 0, 'note': 'company page found but no releases in the window (stale slug?)'}
    return best or {'gap': 'PR Newswire company page not found', 'events': [], 'tried': slugs}
def fetch(r):
    w = r['wire']
    d = float(os.environ.get('DELAY', '0'))
    if d: time.sleep(d)
    only = os.environ.get('ONLY_WIRE', ''); skip = os.environ.get('SKIP_WIRE', '')
    if (only and w != only) or (skip and w == skip): return {'gap': 'skipped in this pass', 'events': []}
    if w == 'Newsfile': return newsfile_page(r)
    if w.startswith('Canada Newswire'): return cnw(r)
    if w == 'PR Newswire': return prn(r)
    return {'gap': 'no company-page source for this wire', 'events': []}
issuers = [r for r in load_issuers() if r['wire'] in ('Newsfile', 'Canada Newswire (CNW)', 'Canada Newswire', 'PR Newswire')]
if __name__ == '__main__':
    run_workers('wire_pages', fetch, issuers, threads=int(os.environ.get('THREADS', '5')))
