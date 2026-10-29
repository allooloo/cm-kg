"""SITE-03 — the Cloudflare state of every Allooloo zone, read-only: apex DNS records, the http_request_dynamic_redirect entrypoint (existing redirect rules),
bot_management.ai_bots_protection, dnssec.status, and the zone's tags (where the token can read them). Token: AGENT KEYS\\cloudflare.txt, read in-process.
Usage: python -X utf8 -I api_state.py <zones_v12.json> <out.json>"""
import json, sys, time, threading, concurrent.futures as cf, urllib.request, urllib.error
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt').read().strip(); H = {'Authorization': 'Bearer ' + T}
B = 'https://api.cloudflare.com/client/v4'
ESTATES = set((sys.argv[3] if len(sys.argv) > 3 else 'allooloo').split(','))
Z = [z for z in json.load(open(sys.argv[1], encoding='utf-8')) if z['estate'] in ESTATES]
lock = threading.Lock(); last = [0.0]; GAP = 0.3   # ~200 calls a minute, under the 1,200 / 5 min limit
def get(path):
    with lock:
        w = last[0] + GAP - time.time()
        if w > 0: time.sleep(w)
        last[0] = time.time()
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(B + path, headers=H), timeout=60); return json.load(r)
        except urllib.error.HTTPError as e:
            try: return json.load(e)
            except Exception: return {'success': False, 'errors': [{'code': e.code}]}
        except Exception as e:
            if attempt == 3: return {'success': False, 'errors': [{'message': repr(e)[:120]}]}
            time.sleep(3 * (attempt + 1))
def one(z):
    zid = z['zone_id']; n = z['zone']; o = {'zone': n, 'zone_id': zid}
    d = get(f'/zones/{zid}/dns_records?per_page=100'); recs = d.get('result') or []
    o['dns'] = [{'type': r['type'], 'name': r['name'], 'content': r['content'][:60], 'proxied': r.get('proxied')} for r in recs if r['type'] in ('A', 'AAAA', 'CNAME', 'MX', 'TXT') or r['name'] in (n, 'www.' + n)]
    o['apex_addressed'] = any(r['name'] == n and r['type'] in ('A', 'AAAA', 'CNAME') for r in recs); o['www_addressed'] = any(r['name'] == 'www.' + n and r['type'] in ('A', 'AAAA', 'CNAME') for r in recs)
    o['apex_proxied'] = any(r['name'] == n and r['type'] in ('A', 'AAAA', 'CNAME') and r.get('proxied') for r in recs)
    e = get(f'/zones/{zid}/rulesets/phases/http_request_dynamic_redirect/entrypoint'); o['redirect_rules'] = [{'id': r.get('id'), 'description': r.get('description'), 'expression': r.get('expression'), 'enabled': r.get('enabled'), 'target': ((r.get('action_parameters') or {}).get('from_value') or {}).get('target_url')} for r in ((e.get('result') or {}).get('rules') or [])] if e.get('success') else None
    o['redirect_ruleset_id'] = ((e.get('result') or {}).get('id')) if e.get('success') else None
    b = get(f'/zones/{zid}/bot_management'); o['ai_bots_protection'] = ((b.get('result') or {}).get('ai_bots_protection')) if b.get('success') else f"unreadable {b.get('errors')}"
    s = get(f'/zones/{zid}/dnssec'); o['dnssec'] = ((s.get('result') or {}).get('status')) if s.get('success') else f"unreadable {s.get('errors')}"
    o['dnssec_ds'] = ((s.get('result') or {}).get('ds') or '')[:60] if s.get('success') else ''
    t = get(f'/zones/{zid}/tags'); o['tags'] = (t.get('result') if t.get('success') else 'unreadable (token scope)')
    return o
t0 = time.time(); out = []
with cf.ThreadPoolExecutor(6) as ex:
    for i, r in enumerate(ex.map(one, Z), 1):
        out.append(r)
        if i % 100 == 0: print(i, 'zones', round(time.time() - t0), 's', flush=True)
json.dump({'read_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'zones': out}, open(sys.argv[2], 'w', encoding='utf-8'), indent=0)
from collections import Counter
print('done', len(out), 'ai_bots', Counter(str(o['ai_bots_protection']) for o in out), 'dnssec', Counter(str(o['dnssec']) for o in out), 'apex addressed', Counter(o['apex_addressed'] for o in out), 'with redirect rules', sum(1 for o in out if o['redirect_rules']))
