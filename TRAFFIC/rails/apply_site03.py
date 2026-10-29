"""SITE-03 — the writes, per zone, from the plan (§5) and the measured state: for every Allooloo zone whose role is 301, an addressed + proxied apex (AAAA 100:: at the
apex and www where none exists) and the one redirect rule in the http_request_dynamic_redirect phase (prior rules kept in the apply log, never silently dropped);
AI-bot block OFF and DNSSEC ON on every Allooloo zone; the tag TXT (_estate) on every Allooloo zone. Dormant GSC stock (list from merge_site03.py) is re-pointed the same way.
Dry run by default; --apply writes. Usage: python -X utf8 -I apply_site03.py <plan.json> <log.json> [--apply]"""
import json, sys, time, threading, concurrent.futures as cf, urllib.request, urllib.error
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt').read().strip(); H = {'Authorization': 'Bearer ' + T, 'Content-Type': 'application/json'}
B = 'https://api.cloudflare.com/client/v4'; APPLY = '--apply' in sys.argv
P = json.load(open(sys.argv[1], encoding='utf-8'))
lock = threading.Lock(); last = [0.0]; GAP = 0.3
def call(method, path, body=None):
    with lock:
        w = last[0] + GAP - time.time()
        if w > 0: time.sleep(w)
        last[0] = time.time()
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method), timeout=60); return json.load(r)
        except urllib.error.HTTPError as e:
            try: return json.load(e)
            except Exception: return {'success': False, 'errors': [{'code': e.code}]}
        except Exception as e:
            if attempt == 3: return {'success': False, 'errors': [{'message': repr(e)[:120]}]}
            time.sleep(3 * (attempt + 1))
def redirect_rule(target, desc):
    if '#' in target or target.endswith('/'): tu = {'value': target}
    else: tu = {'expression': f'concat("{target}", http.request.uri.path)'}
    return {'action': 'redirect', 'expression': 'true', 'description': desc, 'enabled': True, 'action_parameters': {'from_value': {'status_code': 301, 'target_url': tu, 'preserve_query_string': True}}}
def one(p):
    zid = p['zone_id']; n = p['zone']; log = {'zone': n, 'actions': []}
    def act(name, ok, detail=''): log['actions'].append({'action': name, 'ok': ok, 'detail': detail})
    # 1. addressed + proxied apex for a 301 zone
    if p.get('role') == '301':
        for host, have in ((n, p['apex_addressed']), ('www.' + n, p['www_addressed'])):
            if not have:
                if APPLY: r = call('POST', f'/zones/{zid}/dns_records', {'type': 'AAAA', 'name': host, 'content': '100::', 'proxied': True, 'ttl': 1, 'comment': 'SITE-03 (2026-10-28): proxied placeholder so the redirect rule fires'}); act('dns AAAA 100:: ' + host, r.get('success'), str(r.get('errors') or '')[:120])
                else: act('dns AAAA 100:: ' + host, None, 'dry run')
        rules = [redirect_rule(p['target'], f"SITE-03 (Site Build Plan v2.2 §5, 2026-10-28): {p['role_source']} — 301 → {p['target']}, path and query kept")]
        if p.get('prior_rules'): log['prior_rules_kept_in_log'] = p['prior_rules']
        if APPLY: r = call('PUT', f'/zones/{zid}/rulesets/phases/http_request_dynamic_redirect/entrypoint', {'rules': rules}); act('redirect rule → ' + p['target'], r.get('success'), str(r.get('errors') or '')[:160])
        else: act('redirect rule → ' + p['target'], None, 'dry run')
    # 2. AI-bot block off
    if p.get('ai_bots_protection') not in ('disabled', None) and not str(p.get('ai_bots_protection', '')).startswith('unreadable'):
        if APPLY: r = call('PUT', f'/zones/{zid}/bot_management', {'ai_bots_protection': 'disabled'}); act('ai_bots_protection → disabled', r.get('success'), str(r.get('errors') or '')[:120])
        else: act('ai_bots_protection → disabled', None, 'dry run')
    # 3. DNSSEC on
    if p.get('dnssec') == 'disabled':
        if APPLY: r = call('PATCH', f'/zones/{zid}/dnssec', {'status': 'active'}); act('dnssec → active', r.get('success'), ((r.get('result') or {}).get('status') or str(r.get('errors') or ''))[:120])
        else: act('dnssec → active', None, 'dry run')
    # 4. the tag TXT (the token cannot write Cloudflare zone tags — the CEO's hand; the TXT is the tag of record until then)
    if p.get('tag_txt'):
        existing = [d for d in p.get('dns', []) if d['type'] == 'TXT' and d['name'] == '_estate.' + n]
        if not existing:
            if APPLY: r = call('POST', f'/zones/{zid}/dns_records', {'type': 'TXT', 'name': '_estate.' + n, 'content': p['tag_txt'], 'ttl': 1, 'comment': 'SITE-03 (2026-10-28): estate and lens tag of record'}); act('tag TXT _estate', r.get('success'), str(r.get('errors') or '')[:120])
            else: act('tag TXT _estate', None, 'dry run')
        else: act('tag TXT _estate', True, 'already present')
    return log
t0 = time.time(); out = []
with cf.ThreadPoolExecutor(6) as ex:
    for i, r in enumerate(ex.map(one, P), 1):
        out.append(r)
        if i % 100 == 0: print(i, 'zones', round(time.time() - t0), 's', flush=True)
json.dump({'applied': APPLY, 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'zones': out}, open(sys.argv[2], 'w', encoding='utf-8'), indent=0)
from collections import Counter
c = Counter((a['action'].split(' →')[0].split(' _')[0].split(' 100')[0], a['ok']) for z in out for a in z['actions'])
print('done', len(out), 'zones;', 'actions:', dict(c))
fails = [(z['zone'], a) for z in out for a in z['actions'] if a['ok'] is False]
print('failures', len(fails)); [print(' ', f) for f in fails[:40]]
