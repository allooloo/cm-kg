r"""purge_nav.py — USR-03: whole-zone purge on every surface the footer and nav touched. The surfaces are the zones with a Worker route to one of the three Workers
that render the shared template (estate-pages, gettargetmarket-pages, getasof-pages), read from the account's routes at run time (never typed), plus the
getasof forwards and held zones (new rules). One purge_everything per zone; the result of each is logged (purge-<stamp>.json). Usage: python -X utf8 -I purge_nav.py plan|apply"""
import os, sys, json, time, datetime, urllib.request, urllib.error
AP = 'apply' in sys.argv[1:]; HERE = os.path.dirname(os.path.abspath(__file__)); TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]
ACCT = 'dd2832b36f171b815f84c8487aada36b'; SCRIPTS = {'estate-pages', 'gettargetmarket-pages', 'getasof-pages', 'getdoors-pages', 'getresearch-pages'}
EXTRA = ['getresearch.ai', 'getresearch.io', 'get-research.ai', 'get-research.com', 'get-research.org', 'get-research.io']
def api(p, m='GET', b=None):
    for a in range(6):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cloudflare.com/client/v4' + p, method=m, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json', 'User-Agent': 'Allooloo USR-01 purge'}, data=json.dumps(b).encode() if b is not None else None), timeout=30).read())
        except urllib.error.HTTPError as e:
            r = json.loads(e.read() or b'{}')
            if e.code == 429: time.sleep(5 * (a + 1)); continue
            return r
        except Exception: time.sleep(3)
    return {'success': False, 'errors': ['retries']}
zones, page = [], 1
while True:
    r = api(f'/zones?account.id={ACCT}&per_page=50&page={page}'); zones += r.get('result') or []
    if page >= ((r.get('result_info') or {}).get('total_pages') or 1): break
    page += 1
print(len(zones), 'zones on the account')
touched = {}
doms = api(f'/accounts/{ACCT}/workers/domains').get('result') or []   # Workers custom domains (the estate binds most of its hosts this way)
byzone = {}
for d in doms:
    if d.get('service') in SCRIPTS: byzone.setdefault(d.get('zone_name'), set()).add(d.get('service'))
print(len(doms), 'custom domains on the account ·', len(byzone), 'zones with a custom domain on the three Workers')
for z in zones:
    if z['name'] in byzone: touched[z['name']] = {'id': z['id'], 'scripts': sorted(byzone[z['name']])}
for z in zones:
    rs = api(f"/zones/{z['id']}/workers/routes").get('result') or []; hit = sorted({x.get('script') for x in rs if x.get('script') in SCRIPTS})
    if hit or z['name'] in EXTRA: touched[z['name']] = {'id': z['id'], 'scripts': sorted(set(hit) | set((touched.get(z['name']) or {}).get('scripts') or [])) or ['redirect rule']}
print(len(touched), 'zones touched by the nav (routes to', sorted(SCRIPTS), ') + the new forwards and held stock')
log = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'apply': AP, 'zones': {}}
for name, v in sorted(touched.items()):
    res = api(f"/zones/{v['id']}/purge_cache", 'POST', {'purge_everything': True}) if AP else {'success': True, 'plan': True}
    log['zones'][name] = {**v, 'purge': 'ok' if res.get('success') else 'FAILED ' + json.dumps(res.get('errors'))[:160]}
fails = [k for k, v in log['zones'].items() if not v['purge'].startswith('ok')]
json.dump(log, open(os.path.join(HERE, f"purge-{'apply' if AP else 'plan'}-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"), 'w', encoding='utf-8'), indent=1)
print('purged' if AP else 'planned', len(touched) - len(fails), 'of', len(touched), '· failed:', fails or 'none'); sys.exit(1 if fails else 0)
