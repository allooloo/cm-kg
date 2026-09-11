"""Proof of the door with a real MCP client: the Claude API's MCP connector (Messages API, beta mcp-client-2025-04-04) attaches the
door as an MCP server and Claude calls its tools. Prints what the client received from tools/list and the records returned for the
identifiers asked. Also runs a direct JSON-RPC probe of each host. Usage: python prove.py https://mcp.ca-cm-kg.ai"""
import sys, os, json, time, requests
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\ca-width0'); import keys
E = os.environ
def rpc(base, method, params=None, id_=1):
    r = requests.post(base + '/mcp', json={'jsonrpc': '2.0', 'id': id_, 'method': method, 'params': params or {}}, headers={'Accept': 'application/json, text/event-stream'}, timeout=60)
    return r.status_code, r.headers, (r.json() if r.text else None)
def direct(base):
    print(f'## direct JSON-RPC probe of {base}')
    st, h, j = rpc(base, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'prove.py', 'version': '0'}})
    print('initialize', st, j['result']['serverInfo'], '| headers:', {k: v for k, v in h.items() if k.lower().startswith('x-cmr')})
    st, h, j = rpc(base, 'tools/list'); print('tools/list', st, [t['name'] for t in j['result']['tools']])
    for name, args in [('list_nodes', {}), ('resolve_issuer', {'identifier': 'SHOP'}), ('resolve_issuer', {'identifier': 'AUMB.V'}), ('resolve_issuer', {'identifier': 'CSE:AWR'})]:
        st, h, j = rpc(base, 'tools/call', {'name': name, 'arguments': args}); print(name, args, '->', json.dumps(j['result']['structuredContent'])[:500])
def connector(base):
    print(f'## Claude API MCP connector against {base}')
    body = {'model': 'claude-sonnet-5', 'max_tokens': 4000,
            'mcp_servers': [{'type': 'url', 'url': base + '/mcp', 'name': 'cm-kg'}],
            'messages': [{'role': 'user', 'content': 'Using only the cm-kg MCP tools: (1) call list_nodes; (2) call resolve_issuer for SHOP, for AUMB.V and for CSE:AWR. Then reply with exactly the JSON the tools returned, one block per call, no commentary.'}]}
    r = requests.post('https://api.anthropic.com/v1/messages', headers={'x-api-key': E['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'anthropic-beta': 'mcp-client-2025-04-04', 'content-type': 'application/json'}, json=body, timeout=300)
    print('http', r.status_code)
    if not r.ok: print(r.text[:600]); return
    j = r.json(); calls = 0
    for b in j.get('content', []):
        if b.get('type') == 'mcp_tool_use': calls += 1; print('TOOL CALL', b.get('name'), json.dumps(b.get('input')))
        elif b.get('type') == 'mcp_tool_result':
            txt = ''.join(c.get('text', '') for c in (b.get('content') or []) if isinstance(c, dict)); print('TOOL RESULT', ('ERROR ' if b.get('is_error') else ''), txt[:700])
        elif b.get('type') == 'text': print('CLAUDE TEXT', b['text'][:1500])
    print('tool calls made by the client:', calls, '| usage:', j.get('usage'))
if __name__ == '__main__':
    base = sys.argv[1].rstrip('/')
    direct(base)
    if '--no-connector' not in sys.argv: connector(base)
