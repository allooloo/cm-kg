r"""patch_apex.py — DOORS-01: the three doors on the apex router (CM-KG\DOOR\apex\index.js; index.pre-doors01-2026-11-05.js beside). mcp./agent. of getfilings.ai,
getticker.ai and getauditor.ai are host profiles of the same router (getissuer): index only; each tool is routed by issuer (and market) to the owning node's
gate, which reads the record, signs and receipts; the router forwards the answer unchanged; a paid read settles at the router first and the node's receipt names
it. The doors list (FOR DESKS order) on every door profile's card and llms.txt, getasof's included. doors.js is the gate's copy. Server 0.24.0 -> 0.25.0."""
import pathlib, shutil
D = pathlib.Path(r'C:\ALLOOLOO\CM-KG\DOOR\apex'); p = D / 'index.js'; pre = D / 'index.pre-doors01-2026-11-05.js'
if not pre.exists(): shutil.copy2(p, pre)
shutil.copy2(r'C:\ALLOOLOO\CM-KG\NODE-GATE\worker\doors.js', D / 'doors.js')
s = p.read_text(encoding='utf-8')
if "from './doors.js'" in s: raise SystemExit('already patched')
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:80]); s = s.replace(o, n)
rep("import { ASOF_NAME, ASOF_TOOL, ASOF_LEAD } from './asof.js';",
    "import { ASOF_NAME, ASOF_TOOL, ASOF_LEAD } from './asof.js';\nimport { DOORS as D01, DOOR_NAMES, DOOR_TOOLS } from './doors.js';   // DOORS-01: get_filings · get_ticker · get_auditor (the gate's copy; answered at the node)")
rep("'get_orderability', 'get_as_of'];   // ASOF-01", "'get_orderability', 'get_as_of', 'get_filings', 'get_ticker', 'get_auditor'];   // DOORS-01 · ASOF-01")
rep("const SERVER_VERSION = '0.24.0';", "const SERVER_VERSION = '0.25.0';   // 0.25.0 = DOORS-01 (2026-11-05): mcp.getfilings.ai · mcp.getticker.ai · mcp.getauditor.ai on this router, each tool routed by issuer to the owning node · ")
rep("const ASOF_HOST = h => /^(mcp|agent)\\.getasof\\.ai$/.test(h || '');",
    "const ASOF_HOST = h => /^(mcp|agent)\\.getasof\\.ai$/.test(h || '');\n"
    "// DOORS-01: the doors in the FOR DESKS order (nav order first, then the rest) — every live get_ door; a held name is never listed\n"
    "const DESKS = [['get_issuer', 'https://getissuer.ai/'], ['get_orderability', 'https://getorderability.ai/'], ['get_target_market', 'https://gettargetmarket.ai/'], ['get_as_of', 'https://getasof.ai/'], ['get_filings', 'https://getfilings.ai/'], ['get_ticker', 'https://getticker.ai/'], ['get_auditor', 'https://getauditor.ai/']];\n"
    "const DESKS_LINE = 'Doors: ' + DESKS.map(([t, u]) => `${t} ${u}`).join(' · ');\n"
    "const D01_HOST = h => { const m = /^(mcp|agent)\\.get(filings|ticker|auditor)\\.ai$/.exec(h || ''); return m ? 'get_' + m[2] : null; };\n"
    "const D01_UA = 'getissuer apex (doors route)';\n"
    "const d01Tools = t => [t, 'resolve_issuer', 'list_nodes'];\n"
    "async function d01Route(name, args, cx) {\n"
    "  args = args || {}; const idf = String(args.issuer || args.identifier || '').trim(); const mk = String(args.market || '').trim().toLowerCase();\n"
    "  const ex = String(args.exchange || '').trim().toUpperCase(); const id2 = ex && idf && !/:/.test(idf) ? `${ex}:${idf}` : idf;\n"
    "  if (!idf) return { o: { tool: name, error: 'invalid_request', note: 'an issuer (ticker, ISIN or LEI) is required' }, isError: true };\n"
    "  let nodes = mk ? (PUBLIC[mk + '-cm-kg'] ? [mk + '-cm-kg'] : []) : whichNode(id2).nodes;\n"
    "  if (mk && !nodes.length) return { o: { tool: name, issuer: idf, market: mk, error: 'not_on_record', note: 'no node on the roster for this market' }, isError: true };\n"
    "  if (!nodes.length) return { o: { tool: name, issuer: idf, error: 'unknown_issuer', note: 'no node in the index holds this identifier' }, isError: true };\n"
    "  if (nodes.length > 1) return { o: { tool: name, issuer: idf, error: 'ambiguous', nodes, note: 'listed on more than one node: give market, an exchange or the ISIN' }, isError: true };\n"
    "  const n = nodes[0]; const door = PUBLIC[n] && PUBLIC[n].door; if (!door) return { o: { tool: name, error: 'unavailable', node: n }, isError: true };\n"
    "  try {\n"
    "    const h = { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': D01_UA }; if (cx.callerKey) h['rco-key'] = cx.callerKey; if (cx.settlement) h['x-door-settlement'] = JSON.stringify(cx.settlement);\n"
    "    const r = await fetch(door, { method: 'POST', headers: h, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(60000) });\n"
    "    const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{'))); const res = j.result || {};\n"
    "    return { o: res.structuredContent || JSON.parse(res.content[0].text), isError: !!res.isError };   // the node's signed answer and its receipt pass unchanged\n"
    "  } catch (e) { return { o: { tool: name, issuer: idf, error: 'unavailable', node: n, door, note: `the node's door did not answer (${e.name || 'error'}); nothing is answered elsewhere` }, isError: true }; }\n"
    "}\n"
    "const d01Instr = t => D01[t].lead + ` This door (${t.replace('_', '')}, Allooloo Technologies Corp.) is the same router as https://mcp.getissuer.ai/mcp: an index only. ${t} is routed to the node of the issuer's listing, which reads the record, signs the answer (kid allooloo-cmr-2026-10) and receipts it at mcp.rco-records.ai (writer: the node); the router forwards it unchanged. Free reads; the x402 offer only when asked (x402-pay: 1). ${DESKS_LINE}.`;\n"
    "function d01Card(t) {\n"
    "  const ALL = TOOLS.concat(EXTRA_TOOLS, DOOR_TOOLS); const tl = d01Tools(t).map(n => ALL.find(x => x.name === n)).filter(Boolean); const host = t.replace('_', ''); const mcp = D01[t].mcp;\n"
    "  return { name: host, description: D01[t].lead, url: mcp, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: mcp, transport: 'JSONRPC' }], additionalInterfaces: [{ url: 'https://mcp.getissuer.ai/mcp', transport: 'JSONRPC', description: 'the same router (getissuer)' }], securitySchemes: {}, security: [],\n"
    "    defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], iconUrl: 'https://mcp.getissuer.ai/icon-512.png', provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: SERVER_VERSION, documentationUrl: D01[t].page + 'llms.txt', protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false },\n"
    "    skills: tl.map(x => ({ id: x.name, name: x.title, description: x.description, tags: ['capital-markets', 'public-record', 'mcp'] })),\n"
    "    'x-allooloo': { role: `the ${host} door on the apex router (index only; the record lives at the owning node)`, page: D01[t].page, receipts: 'https://mcp.rco-records.ai/mcp', keyring: 'https://allooloo.ai/.well-known/jwks.json', payment: 'https://data-paygo.ai/', doors: DESKS.map(([a, b]) => `${a} ${b}`), same_router_as: 'https://mcp.getissuer.ai/mcp' } };\n"
    "}\n"
    "const d01Llms = (t, host) => `# ${t} — ${D01[t].lead.split(': ')[0].replace(/^get_\\w+ is /, '')}\\n${D01[t].lead}\\nDoor: ${D01[t].mcp} (Streamable HTTP, JSON-RPC 2.0, no auth) — the same router as https://mcp.getissuer.ai/mcp. Agent Card: https://agent.${t.replace('_', '')}.ai/.well-known/agent-card.json. Page: ${D01[t].page}.\\nTools: ${d01Tools(t).join(', ')}. ${t} is routed to the node of the issuer's listing, which signs (EdDSA, kid allooloo-cmr-2026-10, keyring https://allooloo.ai/.well-known/jwks.json) and receipts at https://mcp.rco-records.ai/mcp (verify_receipt, public; writer: the node). A field a market's record does not carry answers not_on_record; nothing is inferred.\\nPaying for a read: https://data-paygo.ai/ (x402, USDC or Open USD on Base; reads are free, the offer answers only when asked) · licence: https://data-licence.ai/\\n${DESKS_LINE}\\n`;\n")
# getasof's card and llms carry the doors list too
rep("payment: 'https://data-paygo.ai/', licence: 'https://data-licence.ai/', products: [", "payment: 'https://data-paygo.ai/', licence: 'https://data-licence.ai/', doors: DESKS.map(([a, b]) => `${a} ${b}`), products: [")
rep("\\nProducts: Issuer https://getissuer.ai/ · Orderability https://getorderability.ai/ · Target Market https://gettargetmarket.ai/ · As Of https://getasof.ai/ · Issuerwire https://issuerwire.ai/\\n`;",
    "\\nProducts: Issuer https://getissuer.ai/ · Orderability https://getorderability.ai/ · Target Market https://gettargetmarket.ai/ · As Of https://getasof.ai/ · Issuerwire https://issuerwire.ai/\\n${DESKS_LINE}\\n`;")
rep("  const asof = !prof && cx && ASOF_HOST(cx.host);   // ASOF-01", "  const asof = !prof && cx && ASOF_HOST(cx.host);   // ASOF-01\n  const d01 = !prof && cx && D01_HOST(cx.host);   // DOORS-01")
rep("  const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : asof ?", "  const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : d01 ? d01Tools(d01).map(n => DOOR_TOOLS.find(t => t.name === n) || ALL.find(t => t.name === n)).filter(Boolean) : asof ?")
rep("serverInfo: { name: prof ? prof.name : asof ? 'getasof' :", "serverInfo: { name: prof ? prof.name : d01 ? d01.replace('_', '') : asof ? 'getasof' :")
rep("instructions: prof ? prof.instructions : asof ? ASOF_INSTR :", "instructions: prof ? prof.instructions : d01 ? d01Instr(d01) : asof ? ASOF_INSTR :")
rep("    if (name === ASOF_NAME) { const r = await asofRoute(args, cx || {});", "    if (DOOR_NAMES.includes(name)) { const r = await d01Route(name, args, cx || {}); return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: r.isError }); }   // DOORS-01\n    if (name === ASOF_NAME) { const r = await asofRoute(args, cx || {});")
rep("  if (ASOF_HOST(host)) return asofCard(host);   // ASOF-01", "  if (D01_HOST(host)) return d01Card(D01_HOST(host));   // DOORS-01\n  if (ASOF_HOST(host)) return asofCard(host);   // ASOF-01")
rep("  if (ASOF_HOST(host)) return asofHuman(host);   // ASOF-01", "  if (D01_HOST(host)) { const t = D01_HOST(host); return `<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>${t} — the door</title><link rel=\"canonical\" href=\"${D01[t].page}\"></head><body><h1>${t}</h1><p>${D01[t].lead.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</p><p>MCP endpoint: <code>${D01[t].mcp}</code> · the page: <a href=\"${D01[t].page}\">${D01[t].page}</a></p><p>Operator: Allooloo Technologies Corp., Richmond, BC, Canada.</p></body></html>`; }   // DOORS-01\n  if (ASOF_HOST(host)) return asofHuman(host);   // ASOF-01")
rep("function llms(host) { if (ASOF_HOST(host)) return asofLlms(host);", "function llms(host) { if (D01_HOST(host)) return d01Llms(D01_HOST(host), host); if (ASOF_HOST(host)) return asofLlms(host);")
rep("  if (ASOF_HOST(host)) { const ALL = TOOLS.concat(EXTRA_TOOLS); return { name: 'getasof',",
    "  if (D01_HOST(host)) { const t = D01_HOST(host); const ALL = TOOLS.concat(EXTRA_TOOLS, DOOR_TOOLS); return { name: t.replace('_', ''), description: `The ${t} door on the apex router: routed by issuer to the owning node, which reads the record, signs and receipts; index only`, version: SERVER_VERSION, transport: 'streamable-http', url: D01[t].mcp, authentication: 'none', tools: d01Tools(t).map(n => ALL.find(x => x.name === n)).filter(Boolean).map(x => ({ name: x.name, description: x.description })), errors: ['unknown_issuer', 'ambiguous', 'not_on_record', 'invalid_request'], page: D01[t].page, keyring: 'https://allooloo.ai/.well-known/jwks.json', price: { unit: 'one record read', rate: 'the per-call till (data-paygo.ai): reads are free; the x402 offer answers only when asked', pricing: `https://${host}/x402/pricing.json` }, doors: DESKS.map(([a, b]) => `${a} ${b}`), same_router_as: 'https://mcp.getissuer.ai/mcp', operator: OPERATOR, registry: `io.github.allooloo/${t.replace('_', '')} (DOORS-01)`, live_nodes: live.map(n => n.node) }; }   // DOORS-01\n"
    "  if (ASOF_HOST(host)) { const ALL = TOOLS.concat(EXTRA_TOOLS); return { name: 'getasof',")
rep("      if (g.paid && ASOF_HOST(host)) { pay = await settle(env, g.paid, 'getasof');",
    "      if (g.paid && D01_HOST(host)) { pay = await settle(env, g.paid, D01_HOST(host).replace('_', '')); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } }); cx.settlement = { network: pay.pr.network, transaction: pay.tx, payer: pay.payer }; }   // DOORS-01\n"
    "      if (g.paid && ASOF_HOST(host)) { pay = await settle(env, g.paid, 'getasof');")
rep("      const g = units ? await decide(request, env, ASOF_HOST(host) ? {", "      const g = units ? await decide(request, env, D01_HOST(host) ? { door: D01_HOST(host).replace('_', ''), resource: `https://${host}/mcp`, description: `One record read on ${D01_HOST(host).replace('_', '')} (Allooloo Technologies Corp.)`, units } : ASOF_HOST(host) ? {")
p.write_text(s, encoding='utf-8'); print('patched', p)
