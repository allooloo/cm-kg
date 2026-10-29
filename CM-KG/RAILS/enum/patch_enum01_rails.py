r"""ENUM-01 (DAY ORDER 6, 2026-10-25) — the rails read the roster. One-shot patcher; .pre-enum01-20261025 beside every file touched; asserts every anchor."""
import os, shutil, io
R = r'C:\ALLOOLOO\CM-KG'; SUF = '.pre-enum01-20261025'; ROSTER = os.path.join(R, 'RAILS', 'job', 'roster.py')
def rd(p): return io.open(p, encoding='utf-8', newline='').read()
def patch(rel, pairs):
    p = os.path.join(R, rel); s = rd(p)
    if not os.path.exists(p + SUF): shutil.copy2(p, p + SUF)
    for a, b in pairs:
        assert a in s, f'{rel}: anchor not found: {a[:80]}'
        s = s.replace(a, b, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s); print('patched', rel)
for d in (r'DOOR\apex', 'ECO', 'RAILS', r'RAILS\eu-node', r'RAILS\enum'):   # one copy per rails folder (the pond rule), identical
    shutil.copy2(ROSTER, os.path.join(R, d, 'roster.py'))
RI = "import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import roster   # ENUM-01 (DAY ORDER 6): the roster of record\n"

# 1 the producer: build_index indexes the roster entries themselves (region.store), not twelve typed + live.json
patch(r'DOOR\apex\build_index.py', [(
"""NODES = {'ca': 'canadacentral', 'uk': 'uksouth', 'au': 'australiaeast', 'sg': 'southeastasia', 'ch': 'switzerlandnorth',
         'de': 'germanywestcentral', 'fr': 'francecentral', 'nl': 'westeurope', 'jp': 'japaneast', 'kr': 'koreacentral', 'us': 'eastus', 'hk': 'eastasia'}   # hk: ORDER-035 (2026-10-22)
# NODE-EU (DAY ORDER 4, 2026-10-24): the European nodes join here when their door is live (RAILS\\eu-node\\live.json: {cc: region})
import json as _j, os as _o
try: NODES.update(_j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '..', '..', 'RAILS', 'eu-node', 'live.json'), encoding='utf-8')))
except Exception: pass
""",
"""# ENUM-01 (DAY ORDER 6, 2026-10-25): the stores indexed are the roster entries themselves (static/nodes.json; region.store written by apex_join and
# nodes_region.py) — no typed list, no second roster file. A roster entry with no store region stops the build and is named.
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
_o.environ.setdefault('ROSTER_FILE', _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), 'static', 'nodes.json')); import roster
NODES = {roster.cc_of(n): (n.get('region') or {}).get('store') for n in roster.load(live_only=False)}
roster.require('store region (region.store)', {c: r for c, r in NODES.items() if r})
""")])

# 2 the apex job
patch(r'RAILS\job\job_apex.py', [(
"NODES = [('nl', 'westeurope'), ('ch', 'switzerlandnorth')", "NODES_TYPED_BEFORE_ENUM01 = [('nl', 'westeurope'), ('ch', 'switzerlandnorth')"), (
"""try: NODES += [(c, r) for c, r in _j.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'eu-node', 'live.json'), encoding='utf-8')).items()]
except Exception: pass""",
"# ENUM-01 (DAY ORDER 6, 2026-10-25): the nodes are the roster of record (list_nodes / nodes.json); the typed list above is kept as the record of what it was\n"
+ RI + "NODES = [(roster.cc_of(n), (n.get('region') or {}).get('store')) for n in roster.load()]")])

# 3 apex_join writes the store region on the roster entry from the hour a node joins; live.json is still written, read by nothing on the wire
patch(r'RAILS\eu-node\apex_join.py', [(
"json.dump(nodes, open(NJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)",
"nodes[-1].setdefault('region', {'store': region, 'read_from': 'apex_join.py argument (nodes_region.py replaces it from Azure)'})   # ENUM-01 (DAY ORDER 6): the entry carries its store region from the join\n"
"json.dump(nodes, open(NJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)")])

# 4 provision_jobs: default job set = the roster; per-market maps stay explicit and must cover every roster entry
patch(r'RAILS\job\provision_jobs.py', [(
"LAB = ['tavily',",
"""# ENUM-01 (DAY ORDER 6, 2026-10-25): region / ark / nightly / vault stay explicit per market (policy and infrastructure lines), but the jobs a run touches by
# default are the roster's live entries (never a market that is only in a map — sa is a policy line, not a node), and the rail refuses when a roster entry has no
# line in a map (the gap is named). The roster's store region must match the map's.
""" + RI + """ROSTER_CC = roster.codes()
for _name, _m in (('region (NODES)', NODES), ('ark region (ARK)', ARK), ('nightly cron (NIGHTLY)', NIGHTLY)): roster.require(_name, _m, ROSTER_CC)
_bad = [c for c in ROSTER_CC if roster.region(c) and roster.region(c) != NODES[c]]
if _bad: raise SystemExit('ROSTER POLICY GAP · store region differs from the roster for: ' + ', '.join(_bad) + ' — rail refused')
LAB = ['tavily',"""),
("tag = sys.argv[2]; ccs = sys.argv[3:] or list(NODES);", "tag = sys.argv[2]; ccs = sys.argv[3:] or list(ROSTER_CC) + ['apex'];"),
("    for cc in (sys.argv[2:] or list(NODES) + ['apex']):", "    for cc in (sys.argv[2:] or list(ROSTER_CC) + ['apex']):"),
("    for cc in (sys.argv[3:] or list(NODES) + ['apex']):", "    for cc in (sys.argv[3:] or list(ROSTER_CC) + ['apex']):"),
("    for cc in (sys.argv[2:] or list(NODES) + ['apex']):", "    for cc in (sys.argv[2:] or list(ROSTER_CC) + ['apex']):"),
])

# 5 surfaces snapshot (apex job nightly)
patch(r'RAILS\snapshot_surfaces.py', [(
"NODES = ['ca', 'us', 'uk', 'fr', 'nl', 'ch', 'de', 'au', 'sg', 'jp', 'kr', 'hk']",
RI + "NODES = roster.codes()   # ENUM-01: every roster node's surfaces (the twelve were typed here)")])

# 6 eco-refresh: LIVE from the roster
patch(r'ECO\build_eco.py', [(
"""LIVE = ["ca", "uk", "us", "de", "fr", "nl", "ch", "au", "sg", "jp", "kr", "hk"]""",
"# ENUM-01 (DAY ORDER 6, 2026-10-25): a market is LIVE on its ECO page when the roster of record says so (list_nodes, else nodes.json) — no list of its own\n"
+ RI + "LIVE = roster.codes()\n_LIVE_TYPED_BEFORE_ENUM01 = [\"ca\", \"uk\", \"us\", \"de\", \"fr\", \"nl\", \"ch\", \"au\", \"sg\", \"jp\", \"kr\", \"hk\"]"),
("try: LIVE += [c for c in json.load(", "if False: LIVE += [c for c in json.load(")])
patch(r'ECO\build_specs.py', [(
"MARKETS = TWELVE + EU14 + ROW\nEU13 = [c for c in EU14 if c != 'lu']\ndoor_of = lambda cc: f'https://{cc}.eu-cm-kg.ai' if cc in EU13 else f'https://mcp.{cc}-cm-kg.ai'\ncard_of = lambda cc: f'https://{cc}.eu-cm-kg.ai/.well-known/agent-card.json' if cc in EU13 else f'https://agent.{cc}-cm-kg.ai/.well-known/agent-card.json'",
RI + """MARKETS = roster.codes()   # ENUM-01: the roster (the typed TWELVE/EU14/ROW above kept as the record only)
EU13 = [c for c in EU14 if c != 'lu']
_door = {roster.cc_of(n): n['door'].rstrip('/') for n in roster.load()}
door_of = lambda cc: _door[cc]   # the roster's door field of record
card_of = lambda cc: (_door[cc] + '/.well-known/agent-card.json') if '.eu-cm-kg.ai' in _door[cc] else _door[cc].replace('://mcp.', '://agent.') + '/.well-known/agent-card.json'""")])

# 7 monitoring
patch(r'RAILS\job\alerts.py', [(
"NODES = {'nl': 'westeurope', 'ch': 'switzerlandnorth', 'fr': 'francecentral', 'de': 'germanywestcentral', 'sg': 'southeastasia', 'au': 'australiaeast', 'uk': 'uksouth', 'ca': 'canadacentral', 'jp': 'japaneast', 'kr': 'koreacentral', 'us': 'eastus'}",
RI + "NODES = {roster.cc_of(n): (n.get('region') or {}).get('store') for n in roster.load()}   # ENUM-01: one rule per roster job (eleven were typed)")])

# 8 the close scripts: fleet moves read the roster
for rel in (r'RAILS\eu-node\eu_job.sh', r'RAILS\zones-do5\row_job.sh'):
    patch(rel, [("provision_jobs.py upgrade $TAG nl ch fr de sg au uk ca jp kr hk us $LIVE apex", "provision_jobs.py upgrade $TAG   # ENUM-01: no cc list = every roster node + apex")])
# 9 eco image carries the roster file (build_eco reads list_nodes first, the file when the apex does not answer)
patch(r'ECO\job\build_context.sh', [(
'cp /c/ALLOOLOO/CM-KG/RAILS/eu-node/live.json "$OUT/CM-KG/RAILS/eu-node/"',
'cp /c/ALLOOLOO/CM-KG/RAILS/eu-node/live.json "$OUT/CM-KG/RAILS/eu-node/"; mkdir -p "$OUT/CM-KG/DOOR/apex/static" "$OUT/CM-KG/ECO" && cp /c/ALLOOLOO/CM-KG/DOOR/apex/static/nodes.json "$OUT/CM-KG/DOOR/apex/static/"   # ENUM-01: the roster file beside')])
print('done')
