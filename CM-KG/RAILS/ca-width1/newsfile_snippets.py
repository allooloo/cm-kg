"""Newsfile releases without touching newsfilecorp.com (its bot protection blocks machines):
   (1) Tavily general search on newsfilecorp.com, two query forms, 20 results each — the date is read from the release's own
       dateline as indexed in the snippet: 'City, Province--(Newsfile Corp. - Month D, YYYY) - Issuer ...'
   (2) Tavily news search on newsfilecorp.com with published_date.
Runs for issuers whose newswire of habit is Newsfile and for any issuer with undated Newsfile search hits.
Read-by: 'Tavily search (newsfilecorp.com) + dateline in indexed snippet' / '+ published_date'."""
import re, json
from common import *
DL = re.compile(r'\(Newsfile Corp\.?\s*[-–—]\s*((?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, 20\d\d)\)')
def fetch(r):
    evs = []; seen = set(); amb = 0
    for payload, rb in [({'query': r['name'], 'max_results': 20, 'include_domains': ['newsfilecorp.com']}, 'Tavily search (newsfilecorp.com) + dateline in indexed snippet'),
                        ({'query': f"{r['name']} announces", 'max_results': 20, 'include_domains': ['newsfilecorp.com']}, 'Tavily search (newsfilecorp.com) + dateline in indexed snippet'),
                        ({'query': r['name'], 'max_results': 20, 'topic': 'news', 'days': WINDOW_DAYS, 'include_domains': ['newsfilecorp.com']}, 'Tavily search (newsfilecorp.com) + published_date')]:
        j = tavily(payload)
        for x in j.get('results', []):
            u = x['url'].split('?')[0]
            if '/release/' not in u or u in seen: continue
            if not name_in(x['title'], r['name']): amb += 1; continue
            m = DL.search(x.get('content', '') or ''); date = to_iso(m.group(1)) if m else (to_iso(x.get('published_date', '')) if 'published_date' in rb else '')
            if not date: continue
            seen.add(u)
            if in_window(date): evs.append(event(r, classify(x['title']), date, x['title'], 'Newsfile', u, rb, wire='Newsfile'))
    return {'events': evs, 'n': len(evs), 'ambiguous': amb}
iss = load_issuers(); need = set()
if os.path.exists('raw/wire_search.jsonl'):
    for line in open('raw/wire_search.jsonl', encoding='utf-8'):
        d = json.loads(line)
        if any(u['wire'] == 'Newsfile' for u in d.get('undated', [])): need.add(d['key'])
issuers = [r for r in iss if r['wire'] == 'Newsfile' or key(r) in need]
if __name__ == '__main__':
    print('newsfile_snippets issuers', len(issuers), flush=True)
    run_workers('newsfile_snippets', fetch, issuers, threads=int(os.environ.get('THREADS', '12')))
