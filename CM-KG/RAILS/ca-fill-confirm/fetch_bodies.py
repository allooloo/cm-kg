"""Release bodies for the labs to read: every financial_statement and agm_record_date event, plus French-titled releases.
Cision, PR Newswire, TheNewswire, Accesswire and GlobeNewswire (plain UA) fetch normally; Newsfile is paced at one request
per NF_DELAY seconds on one thread (its bot protection); Business Wire blocks machines (left to Gaps).
Bodies are cached in raw/bodies/<sha1>.txt; raw/bodies.jsonl records url, wire, status, chars."""
import hashlib, re
from fc_common import *
FR = re.compile(r"\b(annonce|résultats|trimestre|exercice|assemblée|actionnaires|financiers|société|dividende|clôture|conseil d'administration|nomination|acquisition de|émission)\b", re.I)
def wanted(e):
    return e['event_type'] in ('financial_statement', 'agm_record_date') or bool(FR.search(e['title']))
def target_list():
    seen = {}
    for e in events():
        if wanted(e) and e['url'] not in seen: seen[e['url']] = {'url': e['url'], 'wire': e['wire'], 'exchange': e['exchange'], 'ticker': e['ticker'], 'event_type': e['event_type']}
    return list(seen.values())
def fetch(it):
    u = it['url']; fn = 'raw/bodies/' + hashlib.sha1(u.encode()).hexdigest() + '.txt'
    if os.path.exists(fn): return {'url': u, 'status': 200, 'chars': os.path.getsize(fn), 'cached': True}
    if 'businesswire.com' in u: return {'url': u, 'status': 'blocked', 'chars': 0, 'gap': 'Business Wire blocks machine fetch'}
    t, st = page_text(u)
    if t is None: return {'url': u, 'status': st, 'chars': 0, 'gap': f'http {st}'}
    open(fn, 'w', encoding='utf-8').write(t); return {'url': u, 'status': 200, 'chars': len(t)}
if __name__ == '__main__':
    items = target_list(); mode = sys.argv[1] if len(sys.argv) > 1 else 'fast'
    if mode == 'fast':
        items = [i for i in items if 'newsfilecorp.com' not in i['url']]
        resume('bodies', fetch, items, threads=int(E.get('THREADS', '6')), keyf=lambda r: r['url'])
    else:  # newsfile, paced
        items = [i for i in items if 'newsfilecorp.com' in i['url']]
        resume('bodies', fetch, items, threads=1, keyf=lambda r: r['url'], delay=float(E.get('NF_DELAY', '3')))
