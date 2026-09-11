"""Proof of a door with a real MCP client: a direct JSON-RPC probe of the host, then the Claude API's MCP connector (Messages API, beta
mcp-client-2025-04-04) attaching the door as an MCP server and calling its tools. Usage: python prove.py https://mcp.uk-cm-kg.ai [id ...]
Default identifiers per host: global door -> SHOP (TSX), SHEL (LSE Main Market), 4BB (AIM), AQSE:DGQ (Aquis); uk host -> SHEL, 4BB, AQSE:DGQ; ca host -> SHOP, AUMB.V, CSE:AWR."""
import sys, os, json, requests
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0'); import keys
E = os.environ
DEFAULTS = {'uk': ['SHEL', 'AIM:4BB', 'AQSE:DGQ', 'GB00BP6MXD84'], 'ca': ['SHOP', 'AUMB.V', 'CSE:AWR'], 'global': ['SHOP', 'SHEL', 'AIM:4BB', 'AQSE:DGQ', 'GB00BP6MXD84']}
def rpc(base, method, params=None, id_=1):
    r = requests.post(base + '/mcp', json={'jsonrpc': '2.0', 'id': id_, 'method': method, 'params': params or {}}, headers={'Accept': 'application/json, text/event-stream'}, timeout=60)
    return r.status_code, r.headers, (r.json() if r.text else None)
def direct(base, ids):
    print(f'## direct JSON-RPC probe of {base}')
    st, h, j = rpc(base, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'prove.py', 'version': '0'}})
    print('initialize', st, j['result']['serverInfo'], '| headers:', {k: v for k, v in h.items() if k.lower().startswith('x-cmr')})
    st, h, j = rpc(base, 'tools/list'); print('tools/list', st, [t['name'] for t in j['result']['tools']])
    st, h, j = rpc(base, 'tools/call', {'name': 'list_nodes', 'arguments': {}}); sc = j['result']['structuredContent']
    print('list_nodes ->', 'live:', sc.get('live_nodes'), [(n['node'], n['records']) for n in sc['nodes'] if n['live']])
    for i in ids:
        st, h, j = rpc(base, 'tools/call', {'name': 'resolve_issuer', 'arguments': {'identifier': i}}); print('resolve_issuer', i, '->', json.dumps(j['result']['structuredContent'])[:420])
    st, h, j = rpc(base, 'tools/call', {'name': 'list_events_since', 'arguments': {'identifier': ids[0], 'limit': 2}}); print('list_events_since', ids[0], '->', json.dumps(j['result']['structuredContent'])[:400])
def connector(base, ids):
    print(f'## Claude API MCP connector against {base}')
    ask = '; '.join(f'resolve_issuer for {i}' for i in ids)
    body = {'model': 'claude-sonnet-5', 'max_tokens': 4000, 'mcp_servers': [{'type': 'url', 'url': base + '/mcp', 'name': 'cm-kg'}],
            'messages': [{'role': 'user', 'content': f'Using only the cm-kg MCP tools: (1) call list_nodes; (2) call {ask}. Then reply with exactly the JSON the tools returned, one block per call, no commentary.'}]}
    r = requests.post('https://api.anthropic.com/v1/messages', headers={'x-api-key': E['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'anthropic-beta': 'mcp-client-2025-04-04', 'content-type': 'application/json'}, json=body, timeout=300)
    print('http', r.status_code)
    if not r.ok: print(r.text[:600]); return
    j = r.json(); calls = 0
    for b in j.get('content', []):
        if b.get('type') == 'mcp_tool_use': calls += 1; print('TOOL CALL', b.get('name'), json.dumps(b.get('input')))
        elif b.get('type') == 'mcp_tool_result':
            txt = ''.join(c.get('text', '') for c in (b.get('content') or []) if isinstance(c, dict)); print('TOOL RESULT', ('ERROR ' if b.get('is_error') else ''), txt[:500])
        elif b.get('type') == 'text': print('CLAUDE TEXT', b['text'][:1200])
    print('tool calls made by the client:', calls, '| usage:', j.get('usage'))
if __name__ == '__main__':
    base = sys.argv[1].rstrip('/'); ids = [a for a in sys.argv[2:] if not a.startswith('--')]
    kind = 'uk' if 'uk-cm-kg' in base else ('ca' if 'ca-cm-kg' in base else 'global')
    ids = ids or DEFAULTS[kind]
    direct(base, ids)
    if '--no-connector' not in sys.argv: connector(base, ids)
