"""Newswire releases outside the ASX platform, via Tavily, for every corporate issuer (the wire of habit first, then the other wires):
   (1) topic=news, days=<window>, wire domains, 20 results  -> published_date from Tavily
   (2) general search "<short name>" announces on the wire domains -> URL date or Tavily published_date
Hits must carry the issuer's name in the title (name rule enforced again in the assembler). Read-by: 'Tavily search (wire domains) + published_date' or '+ URL date'."""
import re
from common import *
DOMS = ['prnewswire.com', 'globenewswire.com', 'businesswire.com', 'accesswire.com', 'newsfilecorp.com', 'medianet.com.au', 'prwire.com.au']
INDEX = re.compile(r'globenewswire\.com/(organization|search)|prnewswire\.com/news/[^/]+/?$|accesswire\.com/newsroom|newsfilecorp\.com/company/|businesswire\.com/(news/home/\?|portal)')
def clean(u):
    u = u.split('#')[0]; return re.sub(r'^https?://(rss|secure|www2|ml-eu|mb)\.', 'https://www.', u)
def short_name(n):
    s = re.sub(r'\b(Limited|Ltd\.?|NL|Holdings|Group|Company|Co\.?|Inc\.?|Corp\.?|Corporation|Pty)\b\.?', '', n, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip(' ,.-')
def fetch(r):
    evs = []; seen = set(); amb = 0; undated = []
    queries = [({'query': r['name'], 'max_results': 20, 'topic': 'news', 'days': WINDOW_DAYS, 'include_domains': DOMS}, 'Tavily search (wire domains) + published_date'),
               ({'query': f'"{short_name(r["name"])}" announces', 'max_results': 20, 'include_domains': DOMS}, 'Tavily search (wire domains) + URL date')]
    for payload, rb in queries:
        j = tavily(payload)
        for x in j.get('results', []):
            u = clean(x['url']); w = wire_of(u)
            if not w or INDEX.search(u) or u in seen: continue
            if not name_in(x['title'], r['name']): amb += 1; continue
            seen.add(u)
            date = to_iso(x.get('published_date', '')); how = 'Tavily search (wire domains) + published_date'
            if not date: date = url_date(u); how = 'Tavily search (wire domains) + URL date'
            if not date: undated.append({'url': u, 'title': x['title'], 'wire': w}); continue
            if in_window(date): evs.append(event(r, classify(x['title'], default='newswire_release'), date, x['title'], w, u, how, wire=w))
    return {'events': evs, 'n': len(evs), 'ambiguous': amb, 'undated': undated[:40]}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('wire_search', fetch, issuers, threads=int(os.environ.get('THREADS', '4')))
