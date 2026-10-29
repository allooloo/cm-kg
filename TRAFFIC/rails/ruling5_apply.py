"""ruling5_apply.py — SITE-04, ruling (5) (CEO 2026-10-28): data-lifecycle.ai → role 301 → https://data-vintage.ai/ (estate allooloo, lens Shelf).
The SITE-03 pattern: AAAA 100:: proxied at apex and www so the redirect fires, one redirect rule in the http_request_dynamic_redirect phase (static target,
query kept), the TXT _estate tag of record updated to role:301. Token read by file name, in-process. Usage: python -X utf8 -I ruling5_apply.py [--apply]"""
import json, sys, urllib.request, urllib.error
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt').read().strip(); H = {'Authorization': 'Bearer ' + T, 'Content-Type': 'application/json'}; B = 'https://api.cloudflare.com/client/v4'
APPLY = '--apply' in sys.argv; ZONE = 'data-lifecycle.ai'; ZID = 'cd4efe8a25d3c2276557c8a0d4f48d74'; TARGET = 'https://data-vintage.ai/'
def call(method, path, body=None):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(B + path, data=json.dumps(body).encode() if body is not None else None, headers=H, method=method), timeout=60))
    except urllib.error.HTTPError as e: return json.load(e)
log = []
dns = call('GET', f'/zones/{ZID}/dns_records')['result']
for host in (ZONE, 'www.' + ZONE):
    if not any(d['type'] in ('A', 'AAAA', 'CNAME') and d['name'] == host for d in dns):
        r = call('POST', f'/zones/{ZID}/dns_records', {'type': 'AAAA', 'name': host, 'content': '100::', 'proxied': True, 'ttl': 1, 'comment': 'SITE-04 ruling (5) (2026-10-28): proxied placeholder so the redirect rule fires'}) if APPLY else {'success': None}
        log.append(('AAAA 100:: ' + host, r.get('success'), str(r.get('errors') or '')[:120]))
    else: log.append(('address ' + host, True, 'already present'))
rule = {'action': 'redirect', 'expression': 'true', 'description': f'SITE-04 ruling (5) (2026-10-28): data-lifecycle.ai → 301 → {TARGET}, query kept', 'enabled': True,
        'action_parameters': {'from_value': {'status_code': 301, 'target_url': {'value': TARGET}, 'preserve_query_string': True}}}
r = call('PUT', f'/zones/{ZID}/rulesets/phases/http_request_dynamic_redirect/entrypoint', {'rules': [rule]}) if APPLY else {'success': None}
log.append(('redirect rule → ' + TARGET, r.get('success'), str(r.get('errors') or '')[:160]))
tag = [d for d in dns if d['type'] == 'TXT' and d['name'] == '_estate.' + ZONE]
content = 'estate:allooloo lens:Shelf family:shelf role:301 target:data-vintage.ai site-04:2026-10-28 ruling:5'
if tag:
    r = call('PATCH', f'/zones/{ZID}/dns_records/{tag[0]["id"]}', {'content': content}) if APPLY else {'success': None}
else:
    r = call('POST', f'/zones/{ZID}/dns_records', {'type': 'TXT', 'name': '_estate.' + ZONE, 'content': content, 'ttl': 1}) if APPLY else {'success': None}
log.append(('tag TXT _estate role:301', r.get('success'), str(r.get('errors') or '')[:120]))
print('applied' if APPLY else 'dry run'); [print(' ', l) for l in log]
json.dump({'applied': APPLY, 'zone': ZONE, 'target': TARGET, 'actions': log}, open(r'C:\ALLOOLOO\TRAFFIC\inputs\ruling5_apply.json', 'w', encoding='utf-8'), indent=1)
