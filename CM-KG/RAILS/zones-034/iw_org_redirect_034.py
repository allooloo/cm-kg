"""ORDER-034 (2026-10-22) — issuerwire.org carries the signed-row standard, so the ISSUERWIRE-01 edge redirect issuerwire.org → issuerwire.ai is taken off that one zone.
The zone's dynamic-redirect entrypoint ruleset is exported beside first (pre-<stamp>-issuerwire.org-redirects.json); the rule is removed from the entrypoint, never the ruleset deleted.
The other eight Issuerwire forwards (issuerwire.com/.io, issuer-wire.*, agentmarketnews.ai, a2a-amn.ai) are not touched. Token by file name, in-process."""
import json, os, urllib.request, urllib.error, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip()
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); Z = 'issuerwire.org'
def cf(m, p, b=None):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + p, data=json.dumps(b).encode() if b is not None else None, method=m, headers={'Authorization': 'Bearer ' + TOK, 'content-type': 'application/json'})
    try: return json.load(urllib.request.urlopen(r, timeout=60))
    except urllib.error.HTTPError as e: return json.load(e)
zid = cf('GET', f'/zones?name={Z}')['result'][0]['id']
ep = cf('GET', f'/zones/{zid}/rulesets/phases/http_request_dynamic_redirect/entrypoint')
with open(os.path.join(HERE, f'pre-{STAMP}-{Z}-redirects.json'), 'x', encoding='utf-8') as f: json.dump(ep, f, indent=1)
rs = ep['result']; keep = [r for r in rs['rules'] if 'issuerwire.org' not in (r.get('expression') or '')]
print(f"{Z}: {len(rs['rules'])} rule(s) on the entrypoint, removing {len(rs['rules']) - len(keep)}")
body = {'rules': [{k: r[k] for k in ('action', 'action_parameters', 'expression', 'description', 'enabled') if k in r} for r in keep]}
res = cf('PUT', f"/zones/{zid}/rulesets/{rs['id']}", body)
print('ok' if res.get('success') else [(e.get('code'), e.get('message')) for e in res.get('errors', [])])
