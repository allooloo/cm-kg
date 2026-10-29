r"""ENUM-01 (DAY ORDER 6, 2026-10-25) — eco-pages, acm-signals and the cmkg-door image read the roster (list_nodes) or carry no typed market count.
One-shot; .pre-enum01-20261025 beside each file; asserts every anchor."""
import os, shutil, io
R = r'C:\ALLOOLOO\CM-KG'; SUF = '.pre-enum01-20261025'
def patch(rel, pairs):
    p = os.path.join(R, rel); s = io.open(p, encoding='utf-8', newline='').read()
    if not os.path.exists(p + SUF): shutil.copy2(p, p + SUF)
    for a, b in pairs:
        assert a in s, f'{rel}: anchor not found: {a[:90]}'
        s = s.replace(a, b, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s); print('patched', rel)

patch(r'ECO\worker\index.js', [
    ("const doorOf = cc => EU_DOOR.has(cc) ?", "const doorOf = cc => (NODES && NODES[cc] && (NODES[cc].regional_door || (NODES[cc].door && NODES[cc].door.replace(/\\/$/, '') + '/mcp'))) || (EU_DOOR.has(cc) ?"),
    ("`https://mcp.${cc}-cm-kg.ai/mcp`;   // the door name rule of record (DAY ORDER 5)", "`https://mcp.${cc}-cm-kg.ai/mcp`);   // ENUM-01 (DAY ORDER 6): the roster entry's door first (list_nodes); the DAY ORDER 5 name rule only before the first roster read"),
    ("const DOORS = () => [", "const DOORS = (ns) => [   // ENUM-01 (DAY ORDER 6): the node doors are every live node on the roster (list_nodes), not a typed twelve"),
    ("  ...NODE_CC.map(c => ({ id: `${c}-cm-kg`, resolves: `listed issuers of one market, served in-country (${c})`, mcp: `https://mcp.${c}-cm-kg.ai/mcp`, card: `https://agent.${c}-cm-kg.ai/.well-known/agent-card.json` })),",
     "  ...Object.values(ns || {}).filter(n => n.live).map(n => ({ id: n.node, resolves: `listed issuers of one market, served in-country (${n.node.split('-')[0]})`, mcp: n.regional_door || (String(n.door).replace(/\\/$/, '') + '/mcp'), card: n.agent_card || null })),"),
    ("resolves: 'filings and releases since your last read (twelve markets)'", "resolves: 'filings and releases since your last read (markets: issuerwire.ai/facts.json)'"),
    ("const routing = ROUTING, payment = paymentDoor(env), doors = DOORS();", "const routing = ROUTING, payment = paymentDoor(env), doors = DOORS(await nodes());"),
])
patch(r'ACM-SIGNALS\worker\index.js', [
    ("The security is not on the register of any of the twelve markets", "The security is not on the register of any market on the roster"),
    ("'→ the twelve nodes, live'", "'→ the nodes on the roster, live'"),
    ("The halts pages of the twelve live markets", "The halts pages of the live markets"),
])
patch(r'DOOR\container\index.js', [
    ("description: 'Return the twelve market nodes, which are live,", "description: 'Return the market nodes on the roster of record, which are live,"),
    ("summary: 'The twelve nodes'", "summary: 'The roster of record'"),
])
print('done')
