"""SITE-03 — the wire today: one HEAD/GET per zone apex over HTTPS, redirects followed, final host and status recorded; DNS failures recorded as 'no address'.
Read-only. Output: wire-<date>.json beside the roster. Usage: python -X utf8 -I wire_read.py <zones_all.json> <out.json>"""
import json, sys, time, socket, concurrent.futures as cf, urllib.parse
import requests
zones = json.load(open(sys.argv[1], encoding='utf-8'))['zones']
UA = {'User-Agent': 'Allooloo SITE-03 wire read (read-only)'}
def one(z):
    n = z['name']; out = {'zone': n}
    try: socket.getaddrinfo(n, 443); out['address'] = True
    except Exception: out['address'] = False
    if not out['address']: out.update(status='no address', final='', hops=0); return out
    try:
        r = requests.get(f'https://{n}/', headers=UA, timeout=25, allow_redirects=True, stream=True)
        out.update(status=r.status_code, final=r.url, final_host=urllib.parse.urlparse(r.url).hostname, hops=len(r.history), first=(r.history[0].status_code if r.history else None), first_location=(r.history[0].headers.get('location') if r.history else None), server=r.headers.get('server', ''), surface=r.headers.get('x-surface-version', ''))
        r.close()
    except Exception as e: out.update(status='error', final='', error=repr(e)[:120], hops=0)
    return out
t0 = time.time(); res = []
with cf.ThreadPoolExecutor(24) as ex:
    for i, r in enumerate(ex.map(one, zones), 1):
        res.append(r)
        if i % 250 == 0: print(i, 'zones', round(time.time() - t0), 's', flush=True)
json.dump({'read_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'zones': res}, open(sys.argv[2], 'w', encoding='utf-8'), indent=0)
from collections import Counter
print('done', len(res), Counter(str(r['status']) for r in res).most_common(8))
