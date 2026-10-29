"""SITE-03B — set on every zone: AI bots allowed (ai_bots_protection disabled; crawler_protection disabled where it was on), Bot Fight Mode off, Super Bot Fight Mode
verified bots → allow (where the plan carries it), managed robots.txt off, and every WAF custom rule that challenges or blocks on a bot term disabled (never deleted).
Security level and every other setting untouched. Dry run by default; --apply writes. Usage: python -X utf8 -I crawl_apply.py <crawl_state.json> <log.json> [--apply]"""
import json, sys, time, threading, concurrent.futures as cf, urllib.request, urllib.error
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt').read().strip(); H = {'Authorization': 'Bearer ' + T, 'Content-Type': 'application/json'}; B = 'https://api.cloudflare.com/client/v4'
APPLY = '--apply' in sys.argv; Z = json.load(open(sys.argv[1], encoding='utf-8'))['zones']
lock = threading.Lock(); last = [0.0]; GAP = 0.25
def call(method, path, body=None):
    with lock:
        w = last[0] + GAP - time.time()
        if w > 0: time.sleep(w)
        last[0] = time.time()
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method), timeout=60))
        except urllib.error.HTTPError as e:
            try: return json.load(e)
            except Exception: return {'success': False, 'errors': [{'code': e.code}]}
        except Exception as e:
            if attempt == 3: return {'success': False, 'errors': [{'message': repr(e)[:100]}]}
            time.sleep(3 * (attempt + 1))
def one(o):
    zid = o['zone_id']; log = {'zone': o['zone'], 'estate': o['estate'], 'actions': []}
    def act(name, ok, detail=''): log['actions'].append({'action': name, 'ok': ok, 'detail': detail})
    bm = {}
    if o.get('ai_bots_protection') not in (None, 'disabled'): bm['ai_bots_protection'] = 'disabled'
    if o.get('crawler_protection') == 'enabled': bm['crawler_protection'] = 'disabled'
    if o.get('fight_mode') is True: bm['fight_mode'] = False
    if o.get('sbfm_verified_bots') not in (None, 'allow'): bm['sbfm_verified_bots'] = 'allow'
    if o.get('is_robots_txt_managed') is True: bm['is_robots_txt_managed'] = False
    if bm:
        name = 'bot_management ' + ', '.join(f'{k}={v}' for k, v in bm.items())
        if APPLY: r = call('PUT', f'/zones/{zid}/bot_management', bm); act(name, r.get('success'), str(r.get('errors') or '')[:160])
        else: act(name, None, 'dry run')
    for rule in o.get('waf_custom_bot_rules', []):
        if rule.get('enabled') is False: continue
        name = f"waf custom rule disabled: {rule['action']} on {rule['expression'][:60]}"
        if APPLY: r = call('PATCH', f"/zones/{zid}/rulesets/{rule['ruleset']}/rules/{rule['id']}", {'enabled': False}); act(name, r.get('success'), str(r.get('errors') or '')[:160])
        else: act(name, None, 'dry run')
    return log
t0 = time.time(); out = []
with cf.ThreadPoolExecutor(6) as ex:
    for i, r in enumerate(ex.map(one, Z), 1):
        out.append(r)
        if i % 300 == 0: print(i, 'zones', round(time.time() - t0), 's', flush=True)
json.dump({'applied': APPLY, 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'zones': out}, open(sys.argv[2], 'w', encoding='utf-8'), indent=0)
from collections import Counter
print('done', len(out), 'zones changed', sum(1 for z in out if z['actions']), 'by estate', Counter(z['estate'] for z in out if z['actions']))
print('settings', Counter(k for z in out for a in z['actions'] for k in ([x.split('=')[0] for x in a['action'].replace('bot_management ', '').split(', ')] if a['action'].startswith('bot_management') else ['waf rule'])))
fails = [(z['zone'], a) for z in out for a in z['actions'] if a['ok'] is False]; print('failures', len(fails)); [print(' ', f) for f in fails[:30]]
