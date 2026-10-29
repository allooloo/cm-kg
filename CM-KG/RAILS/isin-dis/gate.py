r"""ISIN disambiguation (2026-10-27) — the door health gate (as LIST-02's roll gate, RAILS\doors-04\roll_doors_0163.py), no image change:
through the node's public door — initialize serverInfo.version, tools/list 5, get_record on the roster example (its ISIN) answers ONE record (not
'ambiguous'), the agent card answers with the roster count and this node's example. Also reads the door image off the Container App.
Writes gate-<stamp>.json beside. Usage: python -X utf8 -I gate.py cc [cc …]"""
import json, os, sys, datetime, subprocess, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
nodes = {n['node'].split('-')[0]: n for n in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))}
UA = {'user-agent': 'Allooloo ISIN disambiguation gate', 'content-type': 'application/json', 'accept': 'application/json, text/event-stream'}
def rpc(door, method, params, sid=None):
    h = dict(UA, **({'mcp-session-id': sid} if sid else {})); r = urllib.request.urlopen(urllib.request.Request(door, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(), headers=h), timeout=60)
    t = r.read().decode(); return json.loads(t[t.index('{'):]), r.headers.get('mcp-session-id')
def gate(cc):
    n = nodes[cc]; door = n['door'].rstrip('/') + ('' if n['door'].rstrip('/').endswith('/mcp') else '/mcp'); ex = (n.get('example') or {}).get('isin') or (n.get('example') or {}).get('ticker')
    g = {'door': door, 'example': ex}
    p = subprocess.run([*AZ, 'containerapp', 'show', '-n', f'cmkg-door-{cc}', '-g', f"allooloo-cmkg-{n['region']['store']}", '--query', 'properties.template.containers[0].image', '-o', 'tsv'], capture_output=True, text=True, env=ENV)
    g['image'] = p.stdout.strip()
    try:
        ini, sid = rpc(door, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'isin-gate', 'version': '1'}}); g['version'] = ini['result']['serverInfo'].get('version')
        g['tools'] = len(rpc(door, 'tools/list', {}, sid)[0]['result']['tools'])
        sc = rpc(door, 'tools/call', {'name': 'get_record', 'arguments': {'identifier': ex}}, sid)[0]['result'].get('structuredContent') or {}
        g['record'] = sc.get('cmr') or sc.get('error'); g['record_name'] = ((sc.get('identity') or {}).get('name') or {}).get('value'); g['listings'] = [l.get('cmr') for l in sc.get('listings') or []]
        ri = rpc(door, 'tools/call', {'name': 'resolve_issuer', 'arguments': {'identifier': ex}}, sid)[0]['result'].get('structuredContent') or {}
        g['resolve_matches'] = len(ri.get('matches') or []); g['resolve_ambiguous'] = ri.get('ambiguous')
        c = json.load(urllib.request.urlopen(urllib.request.Request(door[:-len('/mcp')] + '/.well-known/agent-card.json', headers=UA), timeout=30)); ro = (c.get('x-cmkg') or {}).get('roster') or {}
        g['card_roster_nodes'] = ro.get('nodes'); g['card_example'] = (ro.get('example') or {}).get('isin')
    except Exception as e: g['error'] = repr(e)[:200]
    g['PASS'] = (not g.get('error') and g.get('tools') == 5 and isinstance(g.get('record'), str) and '/' in g['record'] and g.get('resolve_matches') == 1
                 and g.get('card_roster_nodes') == len(nodes) and g.get('card_example') == (n.get('example') or {}).get('isin') and g.get('version') == g['image'].rsplit(':', 1)[-1])
    return g
out = {cc: gate(cc) for cc in sys.argv[1:]}
for cc, g in out.items(): print(cc, json.dumps(g, ensure_ascii=False))
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ'); json.dump(out, open(os.path.join(HERE, f'gate-{stamp}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
