r"""patch_apex_b.py — USR-04 item 3: the getresearch door host on the apex router, so get_research carries the same descriptor as the other seven doors:
mcp.getresearch.ai / agent.getresearch.ai are a host profile of the same router (tools get_research · resolve_issuer · list_nodes; its own card, llms.txt,
mcp.json, pricing). get_research stays on mcp.getissuer.ai's own tool list too. 0.26.0 -> 0.27.0. index.pre-usr04-2026-11-12.js beside. Idempotent."""
import pathlib, shutil
D = pathlib.Path(r'C:\ALLOOLOO\CM-KG\DOOR\apex'); p = D / 'index.js'; pre = D / 'index.pre-usr04-2026-11-12.js'; s = p.read_text(encoding='utf-8')
if 'RS_HOST' in s: raise SystemExit('already patched')
if not pre.exists(): shutil.copy2(p, pre)
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:80]); s = s.replace(o, n)
rep("const SERVER_VERSION = '0.26.0';", "const SERVER_VERSION = '0.27.0';   // 0.27.0 = USR-04 (2026-11-12): mcp.getresearch.ai · agent.getresearch.ai on this router (the getresearch door host: get_research · resolve_issuer · list_nodes) · ")
rep("const D01_UA = 'getissuer apex (doors route)';", "const D01_UA = 'getissuer apex (doors route)';\n"
    "// USR-04: the getresearch door host — the same descriptor shape as the other get_ doors (its own card, llms.txt, mcp.json); the tool is answered here\n"
    "const RS_HOST = h => /^(mcp|agent)\\.getresearch\\.ai$/.test(h || ''); const RS_MCP = 'https://mcp.getresearch.ai/mcp'; const RS_AGENT = 'https://agent.getresearch.ai/.well-known/agent-card.json'; const RS_TOOLS = [RESEARCH_NAME, 'resolve_issuer', 'list_nodes'];\n"
    "const RS_INSTR = RESEARCH_LEAD + ` This door (getresearch, Allooloo Technologies Corp.) is the same router as https://mcp.getissuer.ai/mcp: an index only. get_research resolves the issuer on its node, reads the page from the page store, signs it (kid allooloo-cmr-2026-10) and receipts it at mcp.rco-records.ai (writer: allooloo). Free reads; the x402 offer only when asked (x402-pay: 1). ${DESKS_LINE}.`;\n"
    "function rsCard() {\n"
    "  const tl = RS_TOOLS.map(n => TOOLS.concat(EXTRA_TOOLS).find(x => x.name === n)).filter(Boolean);\n"
    "  return { name: 'getresearch', description: RESEARCH_LEAD, url: RS_MCP, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: RS_MCP, transport: 'JSONRPC' }], additionalInterfaces: [{ url: 'https://mcp.getissuer.ai/mcp', transport: 'JSONRPC', description: 'the same router (getissuer)' }], securitySchemes: {}, security: [],\n"
    "    defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], iconUrl: 'https://mcp.getissuer.ai/icon-512.png', provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: SERVER_VERSION, documentationUrl: RESEARCH_PAGE + 'llms.txt', protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false },\n"
    "    skills: tl.map(x => ({ id: x.name, name: x.title, description: x.description, tags: ['capital-markets', 'public-record', 'mcp'] })),\n"
    "    'x-allooloo': { role: 'the getresearch door on the apex router (index only; the page is read from the page store, the record lives at the owning node)', page: RESEARCH_PAGE, receipts: 'https://mcp.rco-records.ai/mcp', keyring: 'https://allooloo.ai/.well-known/jwks.json', payment: 'https://data-paygo.ai/', doors: DESKS.map(([a, b]) => `${a} ${b}`), same_router_as: 'https://mcp.getissuer.ai/mcp' } };\n"
    "}\n"
    "const rsLlms = () => `# get_research — Data Research: the research page of a listed company\\n${RESEARCH_LEAD}\\nDoor: ${RS_MCP} (Streamable HTTP, JSON-RPC 2.0, no auth) — the same router as https://mcp.getissuer.ai/mcp. Agent Card: ${RS_AGENT}. Page: ${RESEARCH_PAGE}.\\nTools: ${RS_TOOLS.join(', ')}. get_research takes a ticker with its exchange, or an ISIN, or an LEI; the router resolves the issuer on its node, reads the page, signs it (EdDSA, kid allooloo-cmr-2026-10, keyring https://allooloo.ai/.well-known/jwks.json) and receipts it at https://mcp.rco-records.ai/mcp (verify_receipt, public; writer: allooloo). Typed errors: unknown_issuer, ambiguous, no_page, invalid_request. Licensed research: none loaded.\\nPaying for a read: https://data-paygo.ai/ (x402, USDC or Open USD on Base; reads are free, the offer answers only when asked) · licence: https://data-licence.ai/\\n${DESKS_LINE}\\n`;")
rep("  const d01 = !prof && cx && D01_HOST(cx.host);   // DOORS-01", "  const d01 = !prof && cx && D01_HOST(cx.host);   // DOORS-01\n  const rsh = !prof && cx && RS_HOST(cx.host);   // USR-04")
rep("  const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : d01 ?", "  const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : rsh ? RS_TOOLS.map(n => ALL.find(t => t.name === n)).filter(Boolean) : d01 ?")
rep("serverInfo: { name: prof ? prof.name : d01 ?", "serverInfo: { name: prof ? prof.name : rsh ? 'getresearch' : d01 ?")
rep("instructions: prof ? prof.instructions : d01 ?", "instructions: prof ? prof.instructions : rsh ? RS_INSTR : d01 ?")
rep("  if (D01_HOST(host)) return d01Card(D01_HOST(host));   // DOORS-01", "  if (RS_HOST(host)) return rsCard();   // USR-04\n  if (D01_HOST(host)) return d01Card(D01_HOST(host));   // DOORS-01")
rep("  if (D01_HOST(host)) { const t = D01_HOST(host); return `<!doctype html>", "  if (RS_HOST(host)) return `<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>get_research — the door</title><link rel=\"canonical\" href=\"${RESEARCH_PAGE}\"></head><body><h1>get_research</h1><p>${RESEARCH_LEAD.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</p><p>MCP endpoint: <code>${RS_MCP}</code> · the page: <a href=\"${RESEARCH_PAGE}\">${RESEARCH_PAGE}</a></p><p>Operator: Allooloo Technologies Corp., Richmond, BC, Canada.</p></body></html>`;   // USR-04\n  if (D01_HOST(host)) { const t = D01_HOST(host); return `<!doctype html>")
rep("function llms(host) { if (D01_HOST(host))", "function llms(host) { if (RS_HOST(host)) return rsLlms(); if (D01_HOST(host))")
rep("(D01_HOST(host) || ASOF_HOST(host) || TM_HOST(host) || ORD_HOST(host) ? '' : RESEARCH_LLMS)", "(RS_HOST(host) || D01_HOST(host) || ASOF_HOST(host) || TM_HOST(host) || ORD_HOST(host) ? '' : RESEARCH_LLMS)")
rep("  if (D01_HOST(host)) { const t = D01_HOST(host); const ALL = TOOLS.concat(EXTRA_TOOLS, DOOR_TOOLS); return { name: t.replace('_', ''),",
    "  if (RS_HOST(host)) { const ALL = TOOLS.concat(EXTRA_TOOLS); return { name: 'getresearch', description: 'The get_research door on the apex router: the research page of a listed company, read from the page store, signed and receipted; index only', version: SERVER_VERSION, transport: 'streamable-http', url: RS_MCP, authentication: 'none', tools: RS_TOOLS.map(n => ALL.find(x => x.name === n)).filter(Boolean).map(x => ({ name: x.name, description: x.description })), errors: ['unknown_issuer', 'ambiguous', 'no_page', 'invalid_request'], page: RESEARCH_PAGE, keyring: 'https://allooloo.ai/.well-known/jwks.json', price: { unit: 'one record read', rate: 'the per-call till (data-paygo.ai): reads are free; the x402 offer answers only when asked', pricing: `https://${host}/x402/pricing.json` }, doors: DESKS.map(([a, b]) => `${a} ${b}`), same_router_as: 'https://mcp.getissuer.ai/mcp', operator: OPERATOR }; }   // USR-04\n"
    "  if (D01_HOST(host)) { const t = D01_HOST(host); const ALL = TOOLS.concat(EXTRA_TOOLS, DOOR_TOOLS); return { name: t.replace('_', ''),")
rep("      const g = units ? await decide(request, env, D01_HOST(host) ? {", "      const g = units ? await decide(request, env, RS_HOST(host) ? { door: 'getresearch', resource: `https://${host}/mcp`, description: 'One research page read on getresearch (Allooloo Technologies Corp.)', units } : D01_HOST(host) ? {")
p.write_text(s, encoding='utf-8')
r = D / 'research.js'; t = r.read_text(encoding='utf-8')
if 'cx.host' not in t:
    shutil.copy2(r, D / 'research.pre-usr04-2026-11-12.js')
    o = "args = args || {}; const base = { tool: RESEARCH_NAME, door: 'https://mcp.getissuer.ai/mcp', page: RESEARCH_PAGE };"; assert t.count(o) == 1
    t = t.replace(o, "args = args || {}; const base = { tool: RESEARCH_NAME, door: `https://${/^mcp\\.getresearch\\.ai$/.test(cx.host || '') ? 'mcp.getresearch.ai' : 'mcp.getissuer.ai'}/mcp`, page: RESEARCH_PAGE };   // USR-04: the door host the call came in on"); r.write_text(t, encoding='utf-8')
print('patched')
