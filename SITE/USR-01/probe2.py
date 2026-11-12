import json, urllib.request
def call(door, name, args):
    b = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}).encode()
    j = json.loads(urllib.request.urlopen(urllib.request.Request(door, data=b, headers={'content-type': 'application/json', 'accept': 'application/json', 'user-agent': 'Allooloo digest (USR-01 probe)'}), timeout=90).read())
    r = j['result']; return r.get('structuredContent') or json.loads(r['content'][0]['text'])
for a in ('2026-11-06', '2025-06-30'):
    o = call('https://mcp.ca-cm-kg.ai/mcp', 'get_as_of', {'issuer': 'TSX:SHOP', 'as_of': a}); print({k: v for k, v in o.items() if k in ('error', 'year', 'sealed_through', 'earliest_sealed_date', 'years_sealed', 'note', 'vintage')})
o = call('https://mcp.ca-cm-kg.ai/mcp', 'get_record', {'identifier': 'ca-cm-kg/TSX/SHOP', 'as_of': '2026-11-06'}); print({k: (v if k in ('status', 'year', 'ledger', 'manifest', 'error', 'note') else '…') for k, v in o.items()})
