r"""apex_join.py — NODE-EU (DAY ORDER 4, 2026-10-24): one European node joins the apex router, the live list and the static node list.
  · CM-KG\DOOR\apex\index.js: REGIONAL[<node>] = the door's Container Apps origin; its public door is that origin until the node's zone exists
    (EU_DOOR map, so PUBLIC names a door that answers); HOME[<ISIN prefix>] = the node. A node already present is left as it is.
  · RAILS\eu-node\live.json: {cc: region} — read by build_index.py, job_apex.py and job_digest.py.
  · DOOR\apex\static\nodes.json: the node's line (country, door, live, as_of, records, exchanges, events) from its facts.json.
.pre copies beside on the first run of the day. Usage: python -X utf8 -I apex_join.py <cc> <region> <fqdn>"""
import io, os, sys, json, shutil
cc, region, fqdn = sys.argv[1], sys.argv[2], sys.argv[3].rstrip('/'); node = f'{cc}-cm-kg'
R = r'C:\ALLOOLOO\CM-KG'; IDX = os.path.join(R, 'DOOR', 'apex', 'index.js'); NJ = os.path.join(R, 'DOOR', 'apex', 'static', 'nodes.json'); LJ = os.path.join(R, 'RAILS', 'eu-node', 'live.json')
NAMES = {'it': 'Italy', 'es': 'Spain', 'se': 'Sweden', 'dk': 'Denmark', 'no': 'Norway', 'fi': 'Finland', 'be': 'Belgium', 'ie': 'Ireland', 'at': 'Austria', 'pl': 'Poland', 'pt': 'Portugal', 'lu': 'Luxembourg', 'gr': 'Greece', 'cz': 'Czech Republic', 'ky': 'Cayman Islands', 'bm': 'Bermuda', 'je': 'Jersey', 'in': 'India', 'tw': 'Taiwan', 'sa': 'Saudi Arabia', 'ae': 'United Arab Emirates', 'br': 'Brazil', 'mx': 'Mexico'}
for p in (IDX, NJ, LJ):
    if os.path.exists(p) and not os.path.exists(p + '.pre-join-' + cc): shutil.copy2(p, p + '.pre-join-' + cc)
t = io.open(IDX, encoding='utf-8', newline='').read()
if f"'{node}':" not in t.split('const PUBLIC')[0]:
    t = t.replace("  'hk-cm-kg': 'https://cmkg-door-hk", f"  '{node}': 'https://{fqdn}',   // NODE-EU (2026-10-24)\n  'hk-cm-kg': 'https://cmkg-door-hk", 1)
ROW = ['ky', 'bm', 'je', 'in', 'tw', 'sa', 'ae', 'br', 'mx']   # NODE-ROW (DAY ORDER 5, 2026-10-24): own zone (mcp.<cc>-cm-kg.ai) — never in EU_DOOR; ky bm je never in HOME (KY/BM/JE ISINs are incorporation prefixes, the listings sit on HKEX, LSE and others)
if cc not in ROW and 'const EU_DOOR = ' not in t:
    t = t.replace("const PUBLIC = {}; for (const n of Object.keys(REGIONAL)) PUBLIC[n] =",
                  "const EU_DOOR = {};   // NODE-EU (2026-10-24): a European node's public door is its Container Apps origin until its zone exists\nconst PUBLIC = {}; for (const n of Object.keys(REGIONAL)) PUBLIC[n] = EU_DOOR[n] ? { door: EU_DOOR[n] + '/mcp', agent_card: EU_DOOR[n] + '/.well-known/agent-card.json' } :", 1)
if cc not in ROW and (f"'{node}': 'https://{fqdn}'" not in t.split('const PUBLIC')[0].split('const EU_DOOR')[1] if 'const EU_DOOR' in t else True):
    t = t.replace("const EU_DOOR = {};", f"const EU_DOOR = {{ '{node}': 'https://{fqdn}' }};", 1) if "const EU_DOOR = {};" in t else t.replace("const EU_DOOR = { ", f"const EU_DOOR = {{ '{node}': 'https://{fqdn}', ", 1)
if cc not in ('ky', 'bm', 'je') and f"{cc.upper()}: '{node}'" not in t:
    t = t.replace("const HOME = { ", f"const HOME = {{ {cc.upper()}: '{node}', ", 1)
io.open(IDX, 'w', encoding='utf-8', newline='').write(t)
live = json.load(open(LJ, encoding='utf-8')) if os.path.exists(LJ) else {}; live[cc] = region; json.dump(live, open(LJ, 'w'), indent=1)
facts = json.load(open(os.path.join(R, 'DOOR', 'data', 'facts.json'), encoding='utf-8'))['nodes'].get(node, {})
nodes = json.load(open(NJ, encoding='utf-8')); nodes = [x for x in nodes if x.get('node') != node]
nodes.append({'node': node, 'country': NAMES[cc], 'registry': None, 'door': f'https://mcp.{node}.ai' if cc in ROW else f'https://{cc}.eu-cm-kg.ai' if cc != 'lu' else 'https://mcp.lu-cm-kg.ai', 'live': True, 'as_of': facts.get('as_of'), 'records': facts.get('records'), 'exchanges': facts.get('exchanges'), 'events': facts.get('events'), 'issuers_with_events': facts.get('issuers_with_events')})
nodes[-1].setdefault('region', {'store': region, 'read_from': 'apex_join.py argument (nodes_region.py replaces it from Azure)'})   # ENUM-01 (DAY ORDER 6): the entry carries its store region from the join
json.dump(nodes, open(NJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(node, 'joined: REGIONAL + EU_DOOR + HOME', cc.upper(), '· live.json', sorted(live), '· nodes.json', len(nodes))
