r"""ENUM-01 (DAY ORDER 6, 2026-10-25) — estate-pages reads the roster. One-shot patcher; .pre-enum01-20261025 beside every file touched; asserts every anchor.
The status block of site.js is replaced whole from the scratch file given as argv[1]."""
import os, sys, shutil, io
W = r'C:\ALLOOLOO\CM-KG\ESTATE\worker'; SUF = '.pre-enum01-20261025'
def rd(p): return io.open(p, encoding='utf-8', newline='').read()
def patch(name, pairs):
    p = os.path.join(W, name); s = rd(p)
    if not os.path.exists(p + SUF): shutil.copy2(p, p + SUF)
    for a, b in pairs:
        assert a in s, f'{name}: anchor not found: {a[:90]}'
        s = s.replace(a, b, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s); print('patched', name)

# site.js: the status block (lines from "// ---------- status (§6)" to the end of probe) replaced by the roster-driven block; copy without typed counts
p = os.path.join(W, 'site.js'); s = rd(p)
if not os.path.exists(p + SUF): shutil.copy2(p, p + SUF)
i = s.index('// ---------- status (§6): probe results from KV')
new = rd(sys.argv[1]); s = s[:i] + new
for a, b in [("'markets · 11 Azure regions · served in-country'", "'markets · each in its own Azure region · served in-country'"),
             ("'Surfaces covered: allooloo.io, the twelve node surfaces", "'Surfaces covered: allooloo.io, the node surfaces")]:
    assert a in s, a; s = s.replace(a, b, 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s); print('patched site.js (status block + copy)')

patch('surfaces.js', [
    ("import NODE_DATA from './nodes.js';", "import NODE_DATA from './nodes.js';\nimport { setRoster } from './roster.js';   // ENUM-01 (DAY ORDER 6): every list_nodes read sets the roster the modules read"),
    ("const j = await r.json(); const m = {}; for (const n of j.result.structuredContent.nodes) m[n.node] = n; LIVE = m; LIVE_AT = Date.now();",
     "const j = await r.json(); const m = {}; for (const n of j.result.structuredContent.nodes) m[n.node] = n; LIVE = m; LIVE_AT = Date.now(); setRoster(j.result.structuredContent.nodes);"),
    ("-cm-kg\\.(ai|org|com)$/)) && NODE_DATA[m[1]]) return", "-cm-kg\\.(ai|org|com)$/)) && NODE_DATA[m[1]] && !NODE_DATA[m[1]].stub) return"),
    ("The other twelve nodes answer through the apex router", "The other nodes on the roster answer through the apex router"),
    ("twelve regional doors mcp.<cc>-cm-kg.ai/mcp; Hong Kong a beacon.", "one regional door per node, each named by its roster entry (list_nodes, field door)."),
    ("Twelve sovereign market nodes", "Sovereign market nodes, one per market on the roster"),
    ("desc: 'Twelve doors probed every five minutes with one real resolve_issuer; response times, 24h median, last drop. Hong Kong a beacon.', h1: 'Status — the twelve doors'",
     "desc: 'Every live node door on the roster probed every five minutes with one real resolve_issuer; response times, 24h median, last drop.', h1: 'Status — the node doors'"),
])
patch('products.js', [
    ("const ORDER = ['ca', 'us', 'uk', 'fr', 'nl', 'ch', 'de', 'au', 'sg', 'jp', 'kr', 'hk'];",
     "const ORDER = [];   // ENUM-01 (DAY ORDER 6, 2026-10-25): the live node codes, set in place from list_nodes by roster.js (the twelve were typed here)"),
    ("Twelve doors in twelve Azure regions", "One door per market on the roster, each in its own Azure region"),
    ("and its twelve sovereign doors", "and its sovereign market doors"),
    ("; twelve doors'", "; one door per market'"),
    ("Markets: twelve nodes, twelve live doors;", "Markets: every node on the roster, each with its live door;"),
    ("across any of the twelve markets", "across any market on the roster"),
    ("the twelve regional doors and the apex stay public", "the regional doors and the apex stay public"),
])
patch('radar.js', [("(twelve node agents + the apex agent)", "(one per roster node + the apex agent)")])
patch('aeo.js', [
    ("which of the twelve market nodes are live", "which market nodes are live"),
])
patch('docs.js', [
    ("Twelve live nodes, one Microsoft Azure region each", "Every live node on the roster, each in its own Microsoft Azure region"),
    ("`<code class=\"nw\">https://mcp.${cc}-cm-kg.ai/mcp</code>`, `<code class=\"nw\">https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json</code>`",
     "`<code class=\"nw\">${esc(doorOf(n))}/mcp</code>`, `<code class=\"nw\">${esc(cardOf(n))}</code>`"),
    ("import { ORDER } from './products.js';", "import { ORDER } from './products.js';\nimport { doorOf, cardOf } from './roster.js';   // ENUM-01: doors from the roster entry"),
    ("esc(REGION_FULL[cc].replace(' (', ' Azure ('))", "esc((REGION_FULL[cc] || '').replace(' (', ' Azure ('))"),
])
patch('kyp-copy.js', [("across eleven national markets", "across the national markets on the roster"), ("on the exchanges of eleven national markets", "on the exchanges of every national market on the roster")])
patch('x402.js', [("(eleven markets, in-country)", "(every market on the roster, in-country)")])
patch('sovereign034.js', [("The eleven markets and their regions are named on the node pages.", "The markets and their regions are named on the node pages and in list_nodes.")])
patch('do5.js', [("'Fourteen European node doors, one subdomain each:", "'The European node doors, one subdomain each:")])
patch('nodes.js', [("which of the twelve nodes holds", "which node on the roster holds")])
print('done')
