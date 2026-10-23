"""ORDER-034 — DNS-AID discovery records (the dns_aid_records.py shape) on the fourteen served ORDER-034 zones; additive, an existing record at a name is left as it is.
  _index._agents.<zone> SVCB → the zone itself · TXT agents=records:mcp,estate:a2a · _mcp._agents.<zone> SVCB → mcp.getissuer.ai · _a2a._agents.<zone> SVCB → agent.getissuer.ai
issuerwire.org points its _mcp at mcp.issuerwire.ai (the door it describes). hk-issuer.ai: index records only until the ORDER-035 door answers. Token cloudflare.txt in-process."""
import json, os, sys, datetime, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip()
H = {'authorization': 'Bearer ' + TOK, 'content-type': 'application/json'}
def cf(path, method='GET', body=None):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, data=json.dumps(body).encode() if body else None, method=method, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return json.loads(x.read())
    except urllib.error.HTTPError as e: return json.loads(e.read())
ZONES = {f'{c}-issuer.ai': ('mcp.getissuer.ai', 'agent.getissuer.ai') for c in 'ca uk us de fr nl ch au sg jp kr'.split()}
ZONES['hk-issuer.ai'] = ('mcp.getissuer.ai', 'agent.getissuer.ai') if (len(sys.argv) > 1 and sys.argv[1] == 'hk-armed') else (None, None)
ZONES['kyp-model.org'] = ('mcp.getissuer.ai', 'agent.getissuer.ai'); ZONES['issuerwire.org'] = ('mcp.issuerwire.ai', 'issuerwire.ai')
if len(sys.argv) > 1 and sys.argv[1] == 'hk-armed': ZONES = {'hk-issuer.ai': ZONES['hk-issuer.ai']}
SVC = 'alpn="h2" port=443'; out = {}; n = {'created': 0, 'existing': 0, 'failed': 0}
for zone, (mcp, agent) in ZONES.items():
    zid = cf(f'/zones?name={zone}')['result'][0]['id']
    existing = {}
    for rec in (cf(f'/zones/{zid}/dns_records?per_page=500').get('result') or []):
        if '._agents.' in rec['name']: existing.setdefault(rec['name'], []).append(rec['type'])
    wanted = [('SVCB', f'_index._agents.{zone}', {'priority': 1, 'target': zone + '.', 'value': SVC}), ('TXT', f'_index._agents.{zone}', 'agents=records:mcp,estate:a2a' if mcp else 'agents=')]
    if mcp: wanted += [('SVCB', f'_mcp._agents.{zone}', {'priority': 1, 'target': mcp + '.', 'value': SVC}), ('SVCB', f'_a2a._agents.{zone}', {'priority': 1, 'target': agent + '.', 'value': SVC})]
    res = []
    for typ, name, val in wanted:
        if typ in existing.get(name, []): res.append((typ, name, 'exists')); n['existing'] += 1; continue
        body = {'type': typ, 'name': name, 'ttl': 3600, 'comment': 'DNS-AID discovery record (ORDER-034, 2026-10-22)'}
        body['content' if typ == 'TXT' else 'data'] = val
        r = cf(f'/zones/{zid}/dns_records', 'POST', body); ok = r.get('success'); n['created' if ok else 'failed'] += 1
        res.append((typ, name, 'created' if ok else 'FAILED ' + json.dumps(r.get('errors'))[:160]))
    out[zone] = res; print(zone, ' · '.join(f'{t} {nm.split(".")[0]} {s}' for t, nm, s in res))
print(n)
json.dump(out, open(os.path.join(HERE, f"dns-aid-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"), 'x'), indent=1)
