"""Newswire releases via Tavily, for every corporate issuer (the wire of habit first, then the other wires):
   (1) topic=news, days=<window>, seven wire domains, 20 results  -> published_date from Tavily
   (2) general search on globenewswire.com + businesswire.com     -> date from the release URL
   (3) issuers with no wire of habit: general search across all seven wires
Hits must carry the issuer's name in the title. Releases without a date (Newsfile/Accesswire/TheNewswire found only by search) are left for release_dates.py.
Read-by: 'Tavily search (wire domains) + published_date' or '+ URL date'."""
import re
from common import *
DOMS = ['newswire.ca', 'prnewswire.com', 'newsfilecorp.com', 'globenewswire.com', 'businesswire.com', 'accesswire.com', 'thenewswire.com']
INDEX = re.compile(r'newswire\.ca/news/[^/]+/?(\?|$)|newsfilecorp\.com/company/|globenewswire\.com/(organization|search)|prnewswire\.com/news/[^/]+/?$|accesswire\.com/newsroom')
def clean(u):
    u = u.split('#')[0]
    u = re.sub(r'^https?://(rss|secure|www2|ml-eu)\.', 'https://www.', u)
    return u
MONTHS = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sept\.?|Sep\.?|Oct\.?|Nov\.?|Dec\.?)'
DATELINES = [re.compile(r'\(Newsfile Corp\.?\s*[-–—]\s*(' + MONTHS + r' \d{1,2}, 20\d\d)\)'),
             re.compile(r'(' + MONTHS + r' \d{1,2}, 20\d\d)\s*/(?:CNW|PRNewswire)'),
             re.compile(r'(' + MONTHS + r' \d{1,2}, 20\d\d)\s*[-–—/]\s*(?:ACCESS Newswire|ACCESSWIRE|TheNewswire)', re.I),
             re.compile(r'(?:ACCESSWIRE|TheNewswire|GLOBE NEWSWIRE)\s*[-–—/]+\s*(' + MONTHS + r' \d{1,2}, 20\d\d)', re.I)]
def dateline(content):
    for p in DATELINES:
        m = p.search(content or '')
        if m: return to_iso(re.sub(r'\.', '', m.group(1)).replace('Sept ', 'Sep '))
    return ''
def short_name(n):
    s = re.sub(r'\b(Inc\.?|Corp\.?|Corporation|Ltd\.?|Limited|Ltée|Company|Co\.?|plc|L\.?P\.?|Trust|REIT)\b\.?', '', n, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip(' ,.-')
def fetch(r):
    evs = []; seen = set(); amb = 0; undated = []
    queries = [({'query': r['name'], 'max_results': 20, 'topic': 'news', 'days': WINDOW_DAYS, 'include_domains': DOMS}, 'Tavily search (wire domains) + published_date'),
               ({'query': f'"{short_name(r["name"])}" announces', 'max_results': 20, 'include_domains': DOMS}, 'Tavily search (wire domains) + dateline in indexed snippet')]
    if r['wire'] in ('GlobeNewswire', 'Business Wire') or not r['wire']:
        queries.append(({'query': r['name'], 'max_results': 20, 'include_domains': ['globenewswire.com', 'businesswire.com']}, 'Tavily search (wire domains) + URL date'))
    if not r['wire']:
        queries.append(({'query': f"{r['name']} announces", 'max_results': 20, 'include_domains': DOMS}, 'Tavily search (wire domains)'))
    for payload, rb in queries:
        j = tavily(payload)
        for x in j.get('results', []):
            u = clean(x['url']); w = wire_of(u)
            if not w or INDEX.search(u) or u in seen: continue
            if not name_in(x['title'], r['name']): amb += 1; continue
            seen.add(u)
            date = to_iso(x.get('published_date', '')); how = rb
            if not date:
                date = url_date(u); how = 'Tavily search (wire domains) + URL date'
            if not date:
                date = dateline(x.get('content', '')); how = 'Tavily search (wire domains) + dateline in indexed snippet'
            if not date: undated.append({'url': u, 'title': x['title'], 'wire': w}); continue
            if in_window(date): evs.append(event(r, classify(x['title']), date, x['title'], w, u, how, wire=w))
    return {'events': evs, 'n': len(evs), 'ambiguous': amb, 'undated': undated[:40]}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('wire_search', fetch, issuers, threads=int(os.environ.get('THREADS', '6')))
