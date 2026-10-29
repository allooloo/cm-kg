r"""health01.py — HEALTH-01 (DAY ORDER 6, 2026-10-25): a2a-health.ai renders allooloo.io/status — same page, same data, no copy.
  · the zone's redirect rule to a2a-wellness.ai is disabled, never deleted (the ruleset is backed up beside first)
  · a2a-health.ai and www.a2a-health.ai are routed to estate-pages (Worker routes) (the Worker answers / and /status with the status page and
    /status.json with its twin, canonical allooloo.io/status; protocols.js); the proxied AAAA 100:: placeholders are kept as records of what was there
Usage: python -X utf8 -I health01.py"""
import os, sys, json, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'zones-do5')); from cf import cf, zones
ACCT = 'dd2832b36f171b815f84c8487aada36b'; Z = 'a2a-health.ai'; HERE = os.path.dirname(os.path.abspath(__file__)); day = datetime.date.today().isoformat()
z = zones(Z)[0]; zid = z['id']
ph = 'http_request_dynamic_redirect'; rs = cf('GET', f'/zones/{zid}/rulesets/phases/{ph}/entrypoint').get('result') or {}
json.dump(rs, open(os.path.join(HERE, f'health01-redirect-backup-{day}.json'), 'w', encoding='utf-8'), indent=1)
for r in rs.get('rules') or []:
    if r.get('enabled') and 'a2a-wellness.ai' in json.dumps(r.get('action_parameters') or {}):
        body = {k: r[k] for k in ('action', 'expression', 'description', 'action_parameters') if k in r}; body['enabled'] = False
        out = cf('PATCH', f"/zones/{zid}/rulesets/{rs['id']}/rules/{r['id']}", body); print('redirect rule', r['id'], 'disabled' if out.get('success') else out)
# a Workers custom domain is refused over the existing proxied AAAA 100:: placeholders (code 100117, 2026-10-25), so the hosts are Worker routes on them —
# the pattern of the other estate zones (applied 2026-10-25; the zone answered 522 for about a minute between the rule disable and the routes)
have = {r['pattern'] for r in cf('GET', f'/zones/{zid}/workers/routes').get('result', [])}
for pat in (Z + '/*', 'www.' + Z + '/*'):
    if pat in have: print(pat, 'routed'); continue
    out = cf('POST', f'/zones/{zid}/workers/routes', {'pattern': pat, 'script': 'estate-pages'}); print(pat, 'routed to estate-pages' if out.get('success') else out.get('errors'))
