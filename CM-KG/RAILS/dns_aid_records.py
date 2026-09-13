"""DNS-AID discovery records (draft-mozleywilliams-dnsop-dnsaid) on the 22 served zones — additive, never overwrites:
  _index._agents.<zone>  SVCB 1 <zone>.            alpn="h2" port=443      (well-known entry point = the surface itself; its agent card is at /.well-known/agent-card.json)
  _index._agents.<zone>  TXT  "agents=records:mcp,estate:a2a"               (agent:protocol pairs)
  _mcp._agents.<zone>    SVCB 1 <mcp door host>.   alpn="h2" port=443      (the MCP door of the surface's node, or the apex)
  _a2a._agents.<zone>    SVCB 1 <agent host>.      alpn="h2" port=443      (the A2A agent card host)
Hong Kong is a beacon (no door, no agent): index records only. Existing records at a name are left as they are (reported, not touched).
Token cloudflare.txt read in-process, never printed. Writes AZURE\\dns-aid-records-<date>.json."""
import json, urllib.request, sys, datetime
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
if '=' in TOK and ' ' not in TOK.split('=')[0]: TOK = TOK.split('=', 1)[1].strip()
H = {'authorization': 'Bearer ' + TOK, 'content-type': 'application/json'}
def cf(path, method='GET', body=None):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, data=json.dumps(body).encode() if body else None, method=method, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return json.loads(x.read())
    except urllib.error.HTTPError as e: return json.loads(e.read())
APEX_MCP, APEX_AGENT = 'mcp.capitalmarketsknowledgegraph.ai', 'agent.capitalmarketsknowledgegraph.ai'
NODES = ['ca', 'uk', 'us', 'de', 'fr', 'nl', 'ch', 'au', 'sg', 'jp', 'kr', 'hk']
ZONES = {'allooloo.io': (APEX_MCP, APEX_AGENT), 'kyp-model.ai': (APEX_MCP, APEX_AGENT)}
for p in ['trades', 'ask', 'coverage', 'esg', 'issuers', 'disclosure', 'registries', 'radar', 'x402']: ZONES[f'agentic-{p}.ai'] = (APEX_MCP, APEX_AGENT)
for cc in NODES: ZONES[f'{cc}-cm-kg.ai'] = (None, None) if cc == 'hk' else (f'mcp.{cc}-cm-kg.ai', f'agent.{cc}-cm-kg.ai')
SVC = 'alpn="h2" port=443'
out = {}; created = skipped = failed = 0
for zone, (mcp, agent) in ZONES.items():
    j = cf(f'/zones?name={zone}'); zid = j['result'][0]['id'] if j.get('result') else None
    if not zid: out[zone] = {'error': 'zone not found'}; failed += 1; continue
    existing = {}
    for rec in (cf(f'/zones/{zid}/dns_records?per_page=500').get('result') or []):
        if '._agents.' in rec['name']: existing.setdefault(rec['name'], []).append(rec['type'])
    wanted = [('SVCB', f'_index._agents.{zone}', {'priority': 1, 'target': zone + '.', 'value': SVC}), ('TXT', f'_index._agents.{zone}', 'agents=records:mcp,estate:a2a' if mcp else 'agents=')]
    if mcp: wanted += [('SVCB', f'_mcp._agents.{zone}', {'priority': 1, 'target': mcp + '.', 'value': SVC}), ('SVCB', f'_a2a._agents.{zone}', {'priority': 1, 'target': agent + '.', 'value': SVC})]
    res = []
    for typ, name, val in wanted:
        if typ in existing.get(name, []): res.append((typ, name, 'exists — left as is')); skipped += 1; continue
        body = {'type': typ, 'name': name, 'ttl': 3600, 'comment': 'DNS-AID discovery record (TO 100, 2026-09-13)'}
        if typ == 'TXT': body['content'] = val
        else: body['data'] = val
        r = cf(f'/zones/{zid}/dns_records', 'POST', body)
        if r.get('success'): res.append((typ, name, 'created')); created += 1
        else: res.append((typ, name, 'FAILED ' + json.dumps(r.get('errors'))[:160])); failed += 1
    out[zone] = res
    print(zone, '·', ' · '.join(f'{t} {n.split(".")[0]} {s}' for t, n, s in res))
print(f'created {created} · existing {skipped} · failed {failed}')
json.dump(out, open(rf'C:\ALLOOLOO\AZURE\dns-aid-records-{datetime.date.today()}.json', 'w'), indent=1)
