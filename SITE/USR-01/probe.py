import json, urllib.request
def call(door, name, args):
    b = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}).encode()
    j = json.loads(urllib.request.urlopen(urllib.request.Request(door, data=b, headers={'content-type': 'application/json', 'accept': 'application/json', 'user-agent': 'Allooloo USR-01 agreement test'}), timeout=90).read())
    r = j['result']; return r.get('structuredContent') or json.loads(r['content'][0]['text'])
o = call('https://mcp.getasof.ai/mcp', 'get_as_of', {'issuer': 'NASDAQ:AAPL', 'as_of': '2026-11-08'}); print({k: (v if k not in ('fields', 'events', 'signature') else '…') for k, v in o.items()})
o = call('https://mcp.getasof.ai/mcp', 'get_as_of', {'issuer': 'NL0000008977', 'as_of': '2026-11-06'}); print({k: (v if k not in ('fields', 'events', 'signature') else '…') for k, v in o.items()})
o = call('https://mcp.gettargetmarket.ai/mcp', 'get_target_market', {'subject': 'US0378331005'}); print(json.dumps(o)[:500])
o = call('https://mcp.getissuer.ai/mcp', 'resolve_issuer', {'identifier': 'US0378331005'}); m = o['matches'][0]; print({k: (v if k != 'signature' else '…') for k, v in m.items()})
