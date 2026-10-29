r"""LIST-02 (2026-10-26) — roll the node doors to cmkg-door:0.16.3 one at a time (the card carries the roster read from the apex). Own anchor per door =
the revision and image before (written to roll-0163.json). Gate after each door, through its public door: initialize serverInfo.version 0.16.3, tools/list 5,
resolve_issuer on its roster example answers a record, the agent card answers with roster.nodes == the roster count and its own example. Stops on the first
failing gate (that door stays on the new revision's predecessor via the anchor). Usage: python -X utf8 -I roll_doors_0163.py <cc> [cc …] | all"""
import json, os, sys, time, subprocess, urllib.request
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
IMG = 'allooloocmkg.azurecr.io/cmkg-door:0.16.3'; HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'roll-0163.json')
def az(*a): p = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8'); return (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr[-300:]
apps = {a['name']: a for a in az('containerapp', 'list', '--query', "[?starts_with(name,'cmkg-door-')].{name:name,g:resourceGroup,i:properties.template.containers[0].image,rev:properties.latestRevisionName}")[0]}
nodes = {n['node'].split('-')[0]: n for n in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))}
UA = {'user-agent': 'Allooloo eco-pages LIST-02 roll gate', 'content-type': 'application/json', 'accept': 'application/json, text/event-stream'}
def rpc(door, method, params, sid=None):
    h = dict(UA, **({'mcp-session-id': sid} if sid else {})); r = urllib.request.urlopen(urllib.request.Request(door, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(), headers=h), timeout=60)
    t = r.read().decode(); return json.loads(t[t.index('{'):]), r.headers.get('mcp-session-id')
def gate(cc):
    n = nodes[cc]; door = n['door'].rstrip('/') + ('' if n['door'].rstrip('/').endswith('/mcp') else '/mcp'); ex = (n.get('example') or {}).get('isin') or (n.get('example') or {}).get('ticker')
    g = {}
    try:
        ini, sid = rpc(door, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'list02-gate', 'version': '1'}}); g['version'] = ini['result']['serverInfo'].get('version')
        g['tools'] = len(rpc(door, 'tools/list', {}, sid)[0]['result']['tools'])
        sc = rpc(door, 'tools/call', {'name': 'get_record', 'arguments': {'identifier': ex}}, sid)[0]['result'].get('structuredContent') or {}; g['record'] = sc.get('cmr') or sc.get('error')
        card_url = door[:-len('/mcp')] + '/.well-known/agent-card.json'   # the door host serves its own card
        c = json.load(urllib.request.urlopen(urllib.request.Request(card_url, headers=UA), timeout=30)); ro = (c.get('x-cmkg') or {}).get('roster') or {}
        g['card_roster_nodes'] = ro.get('nodes'); g['card_example'] = (ro.get('example') or {}).get('isin')
    except Exception as e: g['error'] = repr(e)[:200]
    g['PASS'] = g.get('version') == '0.16.3' and g.get('tools') == 5 and isinstance(g.get('record'), str) and '/' in g['record'] and g.get('card_roster_nodes') == len(nodes) and g.get('card_example') == (nodes[cc].get('example') or {}).get('isin')
    return g
rep = json.load(open(OUT)) if os.path.exists(OUT) else {}
want = list(nodes) if sys.argv[1:] == ['all'] else sys.argv[1:]
for cc in want:
    a = apps.get(f'cmkg-door-{cc}')
    if not a: print(cc, 'no door app'); continue
    if rep.get(cc, {}).get('gate', {}).get('PASS'): print(cc, 'already rolled and gated'); continue
    anchor = {'image': a['i'], 'revision': a['rev']}
    if a['i'] != IMG:
        res, err = az('containerapp', 'update', '-n', a['name'], '-g', a['g'], '--image', IMG, '--revision-suffix', 'v0163-1026', '--query', '{rev:properties.latestRevisionName,state:properties.provisioningState}')
        if not res: print(cc, 'UPDATE FAILED', err); rep[cc] = {'anchor': anchor, 'error': err}; break
    for _ in range(12):
        g = gate(cc)
        if g['PASS'] or (g.get('version') == '0.16.3' and 'error' not in g): break
        time.sleep(15)
    rep[cc] = {'anchor': anchor, 'image': IMG, 'gate': g, 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}; json.dump(rep, open(OUT, 'w'), indent=1)
    print(cc, 'PASS' if g['PASS'] else 'FAIL', g)
    if not g['PASS']: print('STOP on the first failing gate; anchor', anchor); break
