r"""recut_server_json.py — LIST-02 (2026-10-26): the io.github.allooloo/cm-kg registry card re-cut from the live roster (apex list_nodes): the market count,
the live nodes, the agent-card list and the country keywords are read at cut time, never typed. Writes CM-KG\DOOR\server.json (.pre copy beside).
Usage: python -X utf8 -I recut_server_json.py <version>"""
import json, sys, os, shutil, datetime, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'server.json'); ver = sys.argv[1]
b = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'list_nodes', 'arguments': {}}}).encode()
nodes = json.load(urllib.request.urlopen(urllib.request.Request('https://mcp.getissuer.ai/mcp', data=b, headers={'content-type': 'application/json', 'accept': 'application/json', 'user-agent': 'Allooloo LIST-02 recut'}), timeout=60))['result']['structuredContent']['nodes']
live = [n for n in nodes if n.get('live')]; N = len(live)
s = json.load(open(P, encoding='utf-8')); shutil.copy2(P, P + '.pre-list02-' + datetime.date.today().isoformat())
s['version'] = ver
s['title'] = f'Capital Markets Agents: MCP+A2A — {N} markets'
s['description'] = f'KYP Agentic Trading with the Capital Markets Knowledge Graph — {N} markets, each served in-country.'
m = s['_meta']['io.modelcontextprotocol.registry/publisher-provided']
base = [k for k in m.get('keywords', []) if k in ('agentic market dataset', 'capital markets', 'issuer record', 'ISIN', 'LEI', 'KYP')]
m['keywords'] = base + sorted({n['country'] for n in live})
m['nodes_live'] = [n['node'] for n in live]
m['markets_live'] = N
m['agent_cards'] = 'https://agent.getissuer.ai/.well-known/agent-card.json (apex) and one per node in nodes_live, named on its roster entry (list_nodes: agent_card)'   # the registry caps this block at 4 KB: the node list lives once, in nodes_live
m['counts_from'] = 'apex list_nodes at cut time (' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ') + '); facts at https://mcp.getissuer.ai/facts.json'
json.dump(s, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('server.json', ver, '|', s['title'], '|', s['description'], len(s['description']), 'chars |', N, 'nodes')
