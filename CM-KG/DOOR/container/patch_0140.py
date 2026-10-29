r"""patch_0140.py — NODE-EU-01…14 (DAY ORDER 4, 2026-10-24): cmkg-door 0.13.3 -> 0.14.0, for the fourteen European doors only (the twelve stay on their tags).
  · NODE_COPY for it es se dk no fi be ie at pl pt lu gr cz (country, jurisdiction, MiFID II product governance, scope, ISIN-keyed); COPY.example from env NODE_EXAMPLE.
  · the door's own machine files carry what the edge gate adds on the twelve hostnames (these doors answer on their Container Apps hostnames until their
    zones exist): mcp.json + /.well-known/mcp.json with the routing block, the x402 payment door (USDC first, Open USD second; the resolver meters) and the
    receipt door; the agent card names the resolver; llms.txt carries the routing block under its title. index.js.pre-nodeeu-20261024 beside."""
import io
P = r"C:\ALLOOLOO\CM-KG\DOOR\container\index.js"; t = io.open(P, encoding="utf-8", newline="").read()
def sub(o, n):
    global t; assert t.count(o) == 1, o[:80]; t = t.replace(o, n)
EU = {'it': ('Italy', 'IT', 'Euronext Milan and Euronext Growth Milan'), 'es': ('Spain', 'ES', 'BME (Bolsa de Madrid) and BME Growth'), 'se': ('Sweden', 'SE', 'Nasdaq Stockholm and First North Sweden'),
      'dk': ('Denmark', 'DK', 'Nasdaq Copenhagen and First North Denmark'), 'no': ('Norway', 'NO', 'Euronext Oslo Børs, Euronext Expand and Euronext Growth Oslo'), 'fi': ('Finland', 'FI', 'Nasdaq Helsinki and First North Finland'),
      'be': ('Belgium', 'BE', 'Euronext Brussels and Euronext Growth Brussels'), 'ie': ('Ireland', 'IE', 'Euronext Dublin and Euronext Growth Dublin'), 'at': ('Austria', 'AT', 'Wiener Börse'),
      'pl': ('Poland', 'PL', 'GPW Warsaw Main Market and NewConnect'), 'pt': ('Portugal', 'PT', 'Euronext Lisbon'), 'lu': ('Luxembourg', 'LU', 'Luxembourg Stock Exchange (regulated market and Euro MTF)'),
      'gr': ('Greece', 'GR', 'Euronext Athens (Athens Exchange) and EN.A. Growth'), 'cz': ('Czech Republic', 'CZ', 'Prague Stock Exchange (Prime, Standard) and START')}
rows = "".join("  '%s-cm-kg': { country: '%s', jurisdiction: '%s', duty: 'MiFID II product governance', scope: '%s equity lines (ESMA FIRDS roster); records keyed by ISIN; filings from the national regulated-information store.', example: '', exchanges: 'by MIC', ids: 'ISIN (the record key), LEI, legal name' },\n" % (cc, c, j, s.replace("'", "\\'")) for cc, (c, j, s) in EU.items())
sub("const NODE_COPY = {\n", "const NODE_COPY = {\n" + rows)
sub("const COPY = NODE_COPY[NODE] || { country: NODE, jurisdiction: '', duty: '', scope: '', example: '', exchanges: '', ids: '' };",
    "const COPY = { ...(NODE_COPY[NODE] || { country: NODE, jurisdiction: '', duty: '', scope: '', example: '', exchanges: '', ids: '' }) }; if (process.env.NODE_EXAMPLE) COPY.example = process.env.NODE_EXAMPLE;\n"
    "// 0.14.0 (NODE-EU, 2026-10-24): the door's own machine files carry the routing, the payment door and the receipt door\n"
    "const ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: 'https://mcp.getissuer.ai/mcp' }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-a2a.ai/mcp' }];\n"
    "const PAYMENT = { protocol: 'x402', version: 2, network: 'eip155:8453', asset: 'USDC, OUSD', metered_at: 'https://mcp.getissuer.ai/mcp (the resolver forwards to this door; reads there are free for the first reads per agent per day, then x402)', pricing: 'https://allooloo.ai/x402/pricing.json' };\n"
    "const RECEIPTS = { door: 'https://mcp.rco-a2a.ai/mcp', keyring: 'https://allooloo.ai/.well-known/jwks.json', note: 'resolve_issuer and get_signal through the resolver leave an RCO receipt' };")
sub("const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.13.3';", "const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.14.0';   // 0.14.0 = NODE-EU (2026-10-24): the fourteen European doors, routing/payment/receipts in the door's own files.")
sub("    if (p === '/mcp.json') return sendJson(res, mcpJson(host, nf), 200, asOf, ver, 'public, max-age=300');",
    "    if (p === '/mcp.json' || p === '/.well-known/mcp.json') return sendJson(res, { ...mcpJson(host, nf), routing: ROUTING, payment: PAYMENT, receipts: RECEIPTS, resolver: 'https://mcp.getissuer.ai/mcp' }, 200, asOf, ver, 'public, max-age=300');")
sub("    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json' || (isAgentHost && p === '/')) return sendJson(res, agentCard(), 200, asOf, ver, 'public, max-age=300');",
    "    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json' || (isAgentHost && p === '/')) { const c = agentCard(); c.supportedInterfaces = [{ url: 'https://mcp.getissuer.ai/mcp', transport: 'JSONRPC', description: 'getissuer — the listed-issuer resolver (start here)' }, ...(c.supportedInterfaces || [])]; c.resolver = 'https://mcp.getissuer.ai/mcp'; c.routing = ROUTING; c.payment = PAYMENT; return sendJson(res, c, 200, asOf, ver, 'public, max-age=300'); }")
sub("  return `# Capital Markets Knowledge Graph — ${COPY.country} node door (${REGION})\n",
    "  return `# Capital Markets Knowledge Graph — ${COPY.country} node door (${REGION})\n\nDoors by what they resolve:\n${ROUTING.map(r => `- ${r.what} → ${r.door}`).join('\\n')}\n\n")
io.open(P, "w", encoding="utf-8", newline="").write(t); print("door 0.14.0")
