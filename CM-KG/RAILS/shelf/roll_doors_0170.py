r"""SHELF-01 — roll the market doors to cmkg-door:0.17.0 one at a time (the shelf's door tools beside the five; get_record without as_of unchanged).
Own anchor per door = the revision and image before (roll-0170.json beside). Gate after each door, through its public door: initialize serverInfo.version
0.17.0, tools/list 8 (the five + get_timeline, list_events, get_score), get_record on the roster example answers ONE record exactly as before (same cmr,
no as_of), get_timeline on it answers its lines, and the agent card answers the roster. Stops on the first failing gate (that door goes back to its anchor).
Usage: python -X utf8 -I roll_doors_0170.py <cc> [cc …] | all"""
import json, os, sys, time, subprocess, urllib.request
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
IMG = 'allooloocmkg.azurecr.io/cmkg-door:0.17.0'; HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'roll-0170.json')
def az(*a): p = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8'); return (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr[-300:]
apps = {a['name']: a for a in az('containerapp', 'list', '--query', "[?starts_with(name,'cmkg-door-')].{name:name,g:resourceGroup,i:properties.template.containers[0].image,rev:properties.latestRevisionName}")[0]}
nodes = {n['node'].split('-')[0]: n for n in json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))}
UA = {'user-agent': 'Allooloo SHELF-01 roll gate', 'content-type': 'application/json', 'accept': 'application/json, text/event-stream'}
def rpc(door, method, params, sid=None):
    h = dict(UA, **({'mcp-session-id': sid} if sid else {})); r = urllib.request.urlopen(urllib.request.Request(door, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(), headers=h), timeout=60)
    t = r.read().decode(); return json.loads(t[t.index('{'):]), r.headers.get('mcp-session-id')
def gate(cc):
    n = nodes[cc]; door = n['door'].rstrip('/') + ('' if n['door'].rstrip('/').endswith('/mcp') else '/mcp'); ex = (n.get('example') or {}).get('isin') or (n.get('example') or {}).get('ticker'); g = {}
    try:
        ini, sid = rpc(door, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'shelf-gate', 'version': '1'}}); g['version'] = ini['result']['serverInfo'].get('version')
        tl = [t['name'] for t in rpc(door, 'tools/list', {}, sid)[0]['result']['tools']]; g['tools'] = len(tl); g['new_tools'] = all(x in tl for x in ('get_timeline', 'list_events', 'get_score'))
        sc = rpc(door, 'tools/call', {'name': 'get_record', 'arguments': {'identifier': ex}}, sid)[0]['result'].get('structuredContent') or {}; g['record'] = sc.get('cmr') or sc.get('error'); g['record_has_status'] = 'status' in sc
        tm = rpc(door, 'tools/call', {'name': 'get_timeline', 'arguments': {'identifier': ex}}, sid)[0]['result'].get('structuredContent') or {}; g['timeline_lines'] = tm.get('total'); g['timeline_signed'] = bool(tm.get('events') and (tm['events'][0] or {}).get('signature'))
    except Exception as e: g['error'] = repr(e)[:200]
    g['PASS'] = g.get('version') == '0.17.0' and g.get('tools') == 8 and g.get('new_tools') and isinstance(g.get('record'), str) and '/' in g['record'] and not g.get('record_has_status') and isinstance(g.get('timeline_lines'), int)
    return g
rep = json.load(open(OUT)) if os.path.exists(OUT) else {}
want = list(nodes) if sys.argv[1:] == ['all'] else sys.argv[1:]
for cc in want:
    a = apps.get(f'cmkg-door-{cc}')
    if not a: print(cc, 'no door app'); continue
    if rep.get(cc, {}).get('gate', {}).get('PASS'): print(cc, 'already rolled and gated'); continue
    anchor = {'image': a['i'], 'revision': a['rev']}
    if a['i'] != IMG:
        res, err = az('containerapp', 'update', '-n', a['name'], '-g', a['g'], '--image', IMG, '--revision-suffix', 'v0170-1027', '--query', '{rev:properties.latestRevisionName,state:properties.provisioningState}')
        if not res: print(cc, 'UPDATE FAILED', err); rep[cc] = {'anchor': anchor, 'error': err}; json.dump(rep, open(OUT, 'w'), indent=1); break
    for _ in range(12):
        g = gate(cc)
        if g['PASS']: break
        time.sleep(15)
    rep[cc] = {'anchor': anchor, 'image': IMG, 'gate': g, 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}; json.dump(rep, open(OUT, 'w'), indent=1)
    print(cc, 'PASS' if g['PASS'] else 'FAIL', g)
    if not g['PASS']:
        az('containerapp', 'update', '-n', a['name'], '-g', a['g'], '--image', anchor['image'], '--revision-suffix', 'back-1027'); print('STOP: back to the anchor', anchor); break
