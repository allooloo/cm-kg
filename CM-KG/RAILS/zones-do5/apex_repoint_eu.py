r"""apex_repoint_eu.py — DAY ORDER 5 ZONES-01 (2026-10-24): the fourteen European doors leave their Container Apps hostnames on every public surface.
  · DOOR\apex\index.js EU_DOOR: <cc>-cm-kg → https://<cc>.eu-cm-kg.ai (door /mcp, card /.well-known/agent-card.json); lu leaves EU_DOOR and takes the
    own-zone default (mcp.lu-cm-kg.ai/mcp, agent.lu-cm-kg.ai). REGIONAL (how the apex reaches the node, its origin) is unchanged.
  · DOOR\apex\static\nodes.json: each European line's door = its public door.
  · ECO\examples.json: record_url on the public door.
.pre copies beside (.pre-do5zones-20261024). Usage: python -X utf8 -I apex_repoint_eu.py"""
import io, os, re, json, shutil
R = r'C:\ALLOOLOO\CM-KG'
EU = 'it es se dk no fi be ie at pl pt gr cz'.split(); ALL = EU + ['lu']
pub = lambda cc: 'https://mcp.lu-cm-kg.ai' if cc == 'lu' else f'https://{cc}.eu-cm-kg.ai'
def pre(p):
    if not os.path.exists(p + '.pre-do5zones-20261024'): shutil.copy2(p, p + '.pre-do5zones-20261024')
IDX = os.path.join(R, 'DOOR', 'apex', 'index.js'); pre(IDX)
t = io.open(IDX, encoding='utf-8', newline='').read()
line = re.search(r"^const EU_DOOR = \{.*?\};.*$", t, re.M).group(0)
new = "const EU_DOOR = { " + ", ".join(f"'{cc}-cm-kg': 'https://{cc}.eu-cm-kg.ai'" for cc in EU) + " };   // DAY ORDER 5 ZONES-01 (2026-10-24): the European doors answer under the EU regime zone, <cc>.eu-cm-kg.ai (path card); Luxembourg has its own zone (mcp.lu-cm-kg.ai) and takes the default"
t = t.replace(line, new, 1); io.open(IDX, 'w', encoding='utf-8', newline='').write(t)
NJ = os.path.join(R, 'DOOR', 'apex', 'static', 'nodes.json'); pre(NJ)
nodes = json.load(open(NJ, encoding='utf-8')); n = 0
for x in nodes:
    cc = x.get('node', '').split('-')[0]
    if cc in ALL: x['door'] = pub(cc); n += 1   # the field of record, as the twelve carry it (origin, no path)
json.dump(nodes, open(NJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
EX = os.path.join(R, 'ECO', 'examples.json'); pre(EX)
ex = json.load(open(EX, encoding='utf-8')); m = 0
for cc in ALL:
    if cc in ex and ex[cc].get('record_url'):
        ex[cc]['record_url'] = re.sub(r'^https://[^/]+', pub(cc), ex[cc]['record_url']); m += 1
json.dump(ex, open(EX, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('EU_DOOR', len(EU), '· nodes.json lines', n, '· eco examples', m)
