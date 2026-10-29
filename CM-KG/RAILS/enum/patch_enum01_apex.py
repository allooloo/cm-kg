r"""ENUM-01 (DAY ORDER 6, 2026-10-25) — the apex Worker (cm-kg-apex) reads its own roster: public doors from nodes.json `door`, ECO markets from the ECO pages
themselves, no typed market count in its answers. One-shot; .pre-enum01-20261025 beside; asserts every anchor."""
import os, shutil, io
P = r'C:\ALLOOLOO\CM-KG\DOOR\apex\index.js'; SUF = '.pre-enum01-20261025'
s = io.open(P, encoding='utf-8', newline='').read()
if not os.path.exists(P + SUF): shutil.copy2(P, P + SUF)
pairs = [
 ("  INDEX = i.ok ? await i.json() : { ticker: {}, isin: {}, lei: {}, alias: {}, name: {}, cmr: {} }; NODES = n.ok ? await n.json() : [];",
  "  INDEX = i.ok ? await i.json() : { ticker: {}, isin: {}, lei: {}, alias: {}, name: {}, cmr: {} }; NODES = n.ok ? await n.json() : [];\n"
  "  // ENUM-01 (DAY ORDER 6, 2026-10-25): a node's public door and card are its roster entry's `door` (the field of record); EU_DOOR above stays as the record\n"
  "  for (const x of NODES) if (x.door) { const d = String(x.door).replace(/\\/mcp$/, '').replace(/\\/$/, ''); PUBLIC[x.node] = { door: d + '/mcp', agent_card: d.includes('.eu-cm-kg.ai') ? d + '/.well-known/agent-card.json' : d.replace('://mcp.', '://agent.') + '/.well-known/agent-card.json' }; }"),
 ("if (!ECO_MARKETS.includes(cc)) return { error: 'not_found', market: args.market, markets: ECO_MARKETS };",
  "if (!/^[a-z]{2}$/.test(cc)) return { error: 'not_found', market: args.market, markets: 'https://allooloo.ai/markets' };   // ENUM-01: the ECO page itself says whether a market has an object (ECO_MARKETS above, 49, is the record of ECO-01 only)"),
 ("const j = await r.json(); return { market: cc, page: `https://${cc}-eco.ai/`, ...j }; }",
  "if (r.status === 404) return { error: 'not_found', market: cc, markets: 'https://allooloo.ai/markets' }; const j = await r.json(); return { market: cc, page: `https://${cc}-eco.ai/`, ...j }; }"),
 ("get_eco(market) for the disclosure regime of one of 49 markets,", "get_eco(market) for the disclosure regime of a market (index: allooloo.ai/markets),"),
 ("'Not on the register of any of the twelve markets: do not act on it as listed.'", "'Not on the register of any market on the roster: do not act on it as listed.'"),
 ("note: 'no node of the twelve holds this identifier'", "note: 'no node on the roster holds this identifier'"),
 ("'getissuer resolve_issuer — the twelve registers (index only)'", "'getissuer resolve_issuer — the registers of every node on the roster (index only)'"),
 ("summary: 'The twelve nodes with live counts'", "summary: 'The roster of record: every node with live counts'"),
]
for a, b in pairs:
    assert a in s, 'anchor not found: ' + a[:90]
    s = s.replace(a, b, 1)
io.open(P, 'w', encoding='utf-8', newline='').write(s); print('patched apex index.js')
