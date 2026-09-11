"""Pass 2 input — announcement bodies for the readers. Investegate answers machines, so every financial_statement and agm_record_date
regulatory announcement (and any results-type wire release) is fetched once and its visible text cached in raw/bodies/<sha1(url)>.txt.
GlobeNewswire pages are fetched with a plain UA; Business Wire blocks fetch (recorded). Nothing is read here — the labs read the cache."""
import hashlib
from fc_common import *
EV = events()
TYPES = ('financial_statement', 'agm_record_date')
urls = {}
for e in EV:
    if e['event_type'] in TYPES and e['url'] not in urls: urls[e['url']] = e
items = [{'url': u, 'exchange': e['exchange'], 'ticker': e['ticker']} for u, e in urls.items()]
print('bodies to fetch', len(items), flush=True)
def body_fn(url): return 'raw/bodies/' + hashlib.sha1(url.encode()).hexdigest() + '.txt'
def fetch(it):
    fn = body_fn(it['url'])
    if os.path.exists(fn): return {'url': it['url'], 'cached': True}
    if 'businesswire.com' in it['url']: return {'url': it['url'], 'gap': 'Business Wire blocks fetch'}
    t, st = page_text(it['url'], timeout=60)
    if not t: return {'url': it['url'], 'gap': f'http {st}'}
    if 'investegate.co.uk' in it['url']:
        i = t.find('RNS Number'); j = t.rfind('END')
        if i > 0: t = t[i:]
    open(fn, 'w', encoding='utf-8').write(t[:200000])
    return {'url': it['url'], 'chars': len(t)}
if __name__ == '__main__':
    resume('fetch_bodies', fetch, items, threads=int(E.get('THREADS', '4')), keyf=lambda it: it['url'], delay=float(E.get('DELAY', '0')))
