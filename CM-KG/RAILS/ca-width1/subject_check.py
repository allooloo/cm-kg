r"""SHELF-01 fix (2026-10-27) — one pass over the history: every wire-search line in ca's newest assembled events whose title does not pass the subject rule
(common.subject_in) has its release page read once; the page's own issuer line (PR Newswire "News provided by", GlobeNewswire/Newsfile "Source:", meta
author) decides. Writes subject_check.jsonl {url, ticker, issuer, title, provider, issued_by_issuer, read_at} to the ca store as a width1 drop
(pond/width1/<UTC date>/subject_check.jsonl) — the assembler keeps a line only when the rule or the page says it is the issuer's own.
Usage: python -X utf8 subject_check.py [--local]   (store read and write with the account key; nothing deleted)"""
import sys, os, json, datetime, concurrent.futures as cf, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'isin-dis'))
from common import subject_in, issued_by, get
import store
c = store.cont('ca')
ds = sorted({b.name.split('/')[2] for b in c.list_blobs(name_starts_with='pond/assembled/') if b.name.endswith('ca-events.jsonl')})
rows = [json.loads(l) for l in c.download_blob(f'pond/assembled/{ds[-1]}/ca-events.jsonl').readall().decode().split('\n') if l.strip()]
todo = {}
for e in rows:
    if str(e.get('read_by', '')).startswith('Tavily search') and e.get('url') and not subject_in(e.get('title', ''), e.get('issuer', ''), (e.get('ticker'),)):
        todo.setdefault(e['url'], e)
print('assembled', ds[-1], '· wire-search lines failing the title rule:', len(todo), flush=True)
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def one(u):
    e = todo[u]
    try: pv, ok = issued_by(get(u, tries=2, timeout=30).text, e.get('issuer', ''), (e.get('ticker'),)); err = None
    except Exception as x: pv, ok, err = None, False, repr(x)[:120]
    return {'url': u, 'ticker': e.get('ticker'), 'issuer': e.get('issuer'), 'title': e.get('title'), 'provider': pv, 'issued_by_issuer': ok, 'error': err, 'read_at': now}
out = []
with cf.ThreadPoolExecutor(6) as ex:
    for i, r in enumerate(ex.map(one, list(todo)), 1):
        out.append(r)
        if i % 250 == 0: print(i, 'read', flush=True)
k = collections.Counter('kept (page names the issuer)' if r['issued_by_issuer'] else ('page not read' if r['error'] else ('no issuer line on the page' if not r['provider'] else 'dropped (another issuer)')) for r in out)
print(dict(k), flush=True)
day = now[:10]; body = '\n'.join(json.dumps(r, ensure_ascii=False) for r in out) + '\n'
open(os.path.join(HERE, f'subject_check-{day}.jsonl'), 'w', encoding='utf-8').write(body)
if '--local' not in sys.argv:
    c.upload_blob(f'pond/width1/{day}/subject_check.jsonl', body.encode('utf-8'), overwrite=False)
    print('written', f'pond/width1/{day}/subject_check.jsonl', flush=True)
