"""EQS News (eqs-news.com, the EQS Group / DGAP platform that carries ad hoc announcements, corporate news, voting-rights notifications and directors'
dealings for German, Swiss and Austrian issuers). The site's own news endpoints refuse plain clients (404 / no API), but every news page is public and indexed:
discovery is by Tavily (news search over the window + general search, both restricted to eqs-news.com) per issuer. The URL path names the EQS category
(/news/<category>/<slug>/<id>_<lang>): ad hoc, corporate news, voting rights, directors' dealings, other capital market information, annual reports, …
The event date is Tavily's published_date; the language is the URL suffix (_en / _de / _fr) when present. Name rule applies in the assembler.
Read-by: 'Tavily search (eqs-news.com) + published_date'. Label of the wire: 'EQS News'."""
import re
from common import *
CAT = {'adhoc': 'ad_hoc', 'ad-hoc': 'ad_hoc', 'corporate-news': 'corporate_news', 'corporate': 'corporate_news', 'voting-rights': 'major_holder', 'directors-dealings': 'directors_dealings', 'other-capital-market-information': 'exchange_bulletin', 'annual-reports': 'results', 'financial-reports': 'results', 'net-asset-value': 'corporate_news', 'total-voting-rights': 'major_holder', 'general-meeting': 'agm_egm', 'dividend': 'dividend', 'ir-news': 'corporate_news', 'press-release': 'corporate_news', 'pvr': 'major_holder', 'preliminary-announcement': 'results'}
def fetch(r):
    evs = []; seen = set(); amb = 0
    names = [r['name']] + ([r['full_name']] if r.get('full_name') and r['full_name'] != r['name'] else [])
    for nm in names[:2]:
        for payload in ({'query': nm, 'max_results': 20, 'topic': 'news', 'days': WINDOW_DAYS, 'include_domains': ['eqs-news.com']}, {'query': f'"{nm}"', 'max_results': 20, 'include_domains': ['eqs-news.com']}):
            j = tavily(payload)
            for x in j.get('results', []):
                u = x['url'].split('#')[0].split('?')[0]
                if u in seen or '/news/' not in u: continue
                if not name_in(x['title'] + ' ' + (x.get('content') or '')[:200], r['name'], (r.get('full_name'),)): amb += 1; continue
                seen.add(u)
                m = re.search(r'/news/([^/]+)/', u); cat = m.group(1) if m else ''
                lang = (re.search(r'_([a-z]{2})/?$', u) or [None, ''])[1]
                dt = to_iso(x.get('published_date', ''))
                if not dt or not in_window(dt): continue
                et = CAT.get(cat) or classify(x['title'], default='corporate_news')
                evs.append(event(r, et, dt, x['title'], 'EQS News', u, 'Tavily search (eqs-news.com) + published_date', wire='EQS News', category=cat, language=lang))
    return {'events': evs, 'n': len(evs), 'ambiguous': amb}
issuers = load_issuers()
if __name__ == '__main__':
    run_workers('eqs_search', fetch, issuers, threads=int(os.environ.get('THREADS', '4')))
