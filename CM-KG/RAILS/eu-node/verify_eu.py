r"""verify_eu.py — NODE-EU close read (DAY ORDER 4, 2026-10-24): for each of the fourteen European nodes, its door's machine files (mcp.json with the
routing / payment / receipt blocks, agent card, llms.txt, facts), the resolver's get_signal on the node's example ISIN (signal, home node, halt flag
source, record signature kid, RCO receipt), and the ECO page's NODE LIVE line. Writes verify-eu-2026-10-24.json beside. Usage: python -X utf8 verify_eu.py"""
import json, os, re, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); EX = json.load(open(r'C:\ALLOOLOO\CM-KG\ECO\examples.json', encoding='utf-8'))
UA = {'user-agent': 'curl/8 DAY-ORDER-4 NODE-EU close read', 'content-type': 'application/json'}
def get(u, body=None):
    r = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(body).encode() if body else None, headers=UA), timeout=60); return r.status, r.read().decode('utf-8', 'replace')
out = []
for cc in 'it es se dk no fi be ie at pl pt lu gr cz'.split():
    door = open(os.path.join(HERE, f'door-{cc}.txt')).read().split()[-1] if os.path.exists(os.path.join(HERE, f'door-{cc}.txt')) else 'https://cmkg-door-it.kindcliff-313fa995.italynorth.azurecontainerapps.io'
    row = {'node': f'{cc}-cm-kg', 'door': door}
    try:
        row['files'] = {p: get(door + p)[0] for p in ('/mcp.json', '/.well-known/agent-card.json', '/llms.txt', '/facts.json')}
        m = json.loads(get(door + '/mcp.json')[1]); row['payment'] = m['payment']['asset']; row['routing'] = [r['resolves'] for r in m['routing']]
        f = json.loads(get(door + '/facts.json')[1]); row['records'] = f['records']; row['events'] = f['events']; row['as_of'] = f['as_of']
        isin = EX[cc]['isin']; s = json.loads(get('https://mcp.getissuer.ai/mcp', {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'get_signal', 'arguments': {'identifier': isin}}})[1])['result']['structuredContent']
        row.update({'example': isin, 'signal': s.get('signal'), 'issuer': s.get('issuer'), 'home': s.get('node'), 'halt': (s.get('halt') or {}).get('read_by'), 'kid': (s.get('record_signature') or {}).get('kid'), 'receipt': (s.get('receipt') or {}).get('decision_id')})
        page = get(f'https://{cc}-eco.ai/')[1]; mm = re.search(r'NODE LIVE[^<"]*', page); row['eco'] = mm.group(0)[:60] if mm else None
    except Exception as e: row['error'] = repr(e)[:200]
    out.append(row); print(cc, row.get('records'), row.get('events'), row.get('signal'), row.get('home'), row.get('kid'), row.get('receipt'), '| eco', bool(row.get('eco')), '| files', set((row.get('files') or {}).values()), '| halt', (row.get('halt') or '')[:50], row.get('error', ''))
json.dump(out, open(os.path.join(HERE, 'verify-eu-2026-10-24.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
