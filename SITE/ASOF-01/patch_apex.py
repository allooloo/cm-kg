r"""patch_apex.py — ASOF-01: the As Of door on the apex router (CM-KG\DOOR\apex\index.js; index.pre-asof01-2026-11-05.js beside). mcp.getasof.ai and
agent.getasof.ai are the same router (getissuer): index only. get_as_of is routed by issuer (and market, when given) to the owning node's public door (the gate),
which reads the sealed vintage, signs and receipts; the router forwards the answer unchanged. A paid read settles at the router first and the node's receipt
names the settlement (x-asof-settlement), as the Target Market door. asof.js is the gate's copy (constants only are used here). Server 0.23.0 -> 0.24.0.
Usage: python -X utf8 -I patch_apex.py"""
import pathlib, shutil
D = pathlib.Path(r'C:\ALLOOLOO\CM-KG\DOOR\apex'); p = D / 'index.js'; pre = D / 'index.pre-asof01-2026-11-05.js'
if not pre.exists(): shutil.copy2(p, pre)
shutil.copy2(r'C:\ALLOOLOO\CM-KG\NODE-GATE\worker\asof.js', D / 'asof.js')
s = p.read_text(encoding='utf-8')
if "from './asof.js'" in s: raise SystemExit('already patched')
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:80]); s = s.replace(o, n)
rep("import { TM_TOOLS, TM_NAMES, TM_JWK_PUBLIC, CMR_JWK_PUBLIC, verifyStatement } from './tm.js';   // TMKT-02: the Target Market door (the gate's copy)",
    "import { TM_TOOLS, TM_NAMES, TM_JWK_PUBLIC, CMR_JWK_PUBLIC, verifyStatement } from './tm.js';   // TMKT-02: the Target Market door (the gate's copy)\n"
    "import { ASOF_NAME, ASOF_TOOL, ASOF_LEAD } from './asof.js';   // ASOF-01: the As Of door (the gate's copy; the tool is answered at the node)")
rep("const PAID_TOOLS = ['resolve_issuer', 'get_signal', 'get_record', 'list_events_since', 'list_aliases', 'get_eco', 'get_target_market', 'list_target_market_versions', 'get_orderability'];",
    "const PAID_TOOLS = ['resolve_issuer', 'get_signal', 'get_record', 'list_events_since', 'list_aliases', 'get_eco', 'get_target_market', 'list_target_market_versions', 'get_orderability', 'get_as_of'];   // ASOF-01: get_as_of on the till (free, the offer only when asked)")
rep("const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.23.0';",
    "const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.24.0';   // 0.24.0 = ASOF-01 (2026-11-05): the As Of door — mcp.getasof.ai on this router: get_as_of routed by issuer to the owning node (the node reads the sealed vintage, signs and receipts; the router forwards unchanged) · ")
rep("// GETORD-01 (2026-11-02): mcp.getorderability.ai and agent.getorderability.ai are the orderability door on this same router — same index, no second store.",
    "// ASOF-01 (2026-11-05): mcp.getasof.ai and agent.getasof.ai are the As Of door on this same router — same index, no second copy of the history.\n"
    "const ASOF_HOST = h => /^(mcp|agent)\\.getasof\\.ai$/.test(h || '');\n"
    "const ASOF_MCP = 'https://mcp.getasof.ai/mcp'; const ASOF_AGENT = 'https://agent.getasof.ai/.well-known/agent-card.json'; const ASOF_PAGE = 'https://getasof.ai/';\n"
    "const ASOF_TOOLS = ['get_as_of', 'resolve_issuer', 'list_events_since', 'list_nodes'];\n"
    "const ASOF_INSTR = ASOF_LEAD + ' This door (getasof, Allooloo Technologies Corp.) is the same router as https://mcp.getissuer.ai/mcp: an index only. get_as_of(issuer, as_of, market?) is routed to the node of the issuer\\'s listing; the node reads its sealed vintage (the Replay store under Data Vintage), signs the answer (kid allooloo-cmr-2026-10) and receipts it at mcp.rco-records.ai (writer: the node); the router forwards it unchanged. Reads need no authentication and are free; the x402 offer answers only when asked (x402-pay: 1). list_events_since stays where it is; get_as_of reads the same history.';\n"
    "const ASOF_UA = 'getissuer apex (get_as_of route)';\n"
    "async function asofRoute(args, cx) {\n"
    "  args = args || {}; const issuer = String(args.issuer || '').trim(); const mk = String(args.market || '').trim().toLowerCase();\n"
    "  if (!issuer || !/^\\d{4}-\\d{2}-\\d{2}$/.test(String(args.as_of || ''))) return { o: { tool: ASOF_NAME, issuer, as_of: args.as_of || null, error: 'invalid_request', note: 'issuer (ticker, ISIN or LEI) and as_of (YYYY-MM-DD) are required' }, isError: true };\n"
    "  let nodes = mk ? (PUBLIC[mk + '-cm-kg'] ? [mk + '-cm-kg'] : []) : whichNode(issuer).nodes;\n"
    "  if (mk && !nodes.length) return { o: { tool: ASOF_NAME, issuer, as_of: args.as_of, market: mk, error: 'not_found', note: 'no node on the roster for this market', nodes: (NODES || []).map(n => n.node) }, isError: true };\n"
    "  if (!nodes.length) return { o: { tool: ASOF_NAME, issuer, as_of: args.as_of, error: 'unknown_issuer', note: 'no node in the index holds this identifier' }, isError: true };\n"
    "  if (nodes.length > 1) return { o: { tool: ASOF_NAME, issuer, as_of: args.as_of, error: 'ambiguous', nodes, note: 'the issuer is listed on more than one node: give market, an exchange prefix or the ISIN' }, isError: true };\n"
    "  const n = nodes[0]; const door = PUBLIC[n] && PUBLIC[n].door; if (!door) return { o: { tool: ASOF_NAME, issuer, error: 'unavailable', node: n, note: 'no public door on the roster for this node' }, isError: true };\n"
    "  try {\n"
    "    const h = { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': ASOF_UA }; if (cx.callerKey) h['rco-key'] = cx.callerKey; if (cx.settlement) h['x-asof-settlement'] = JSON.stringify(cx.settlement);\n"
    "    const r = await fetch(door, { method: 'POST', headers: h, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: ASOF_NAME, arguments: args } }), signal: AbortSignal.timeout(60000) });\n"
    "    const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{'))); const res = j.result || {};\n"
    "    return { o: res.structuredContent || JSON.parse(res.content[0].text), isError: !!res.isError };   // the node's signed answer and its receipt pass unchanged\n"
    "  } catch (e) { return { o: { tool: ASOF_NAME, issuer, error: 'unavailable', node: n, door, note: `the node's door did not answer (${e.name || 'error'}); nothing is answered elsewhere` }, isError: true }; }\n"
    "}\n"
    "function asofCard(host) {\n"
    "  const ALL = TOOLS.concat(EXTRA_TOOLS, [ASOF_TOOL]); const tl = ASOF_TOOLS.map(n => ALL.find(t => t.name === n)).filter(Boolean);\n"
    "  return { name: 'getasof', description: ASOF_LEAD, url: ASOF_MCP, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: ASOF_MCP, transport: 'JSONRPC' }], additionalInterfaces: [{ url: 'https://mcp.getissuer.ai/mcp', transport: 'JSONRPC', description: 'the same router (getissuer): same index, no second copy' }], securitySchemes: {}, security: [],\n"
    "    defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], iconUrl: 'https://mcp.getissuer.ai/icon-512.png', provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: SERVER_VERSION, documentationUrl: ASOF_PAGE + 'llms.txt', protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false },\n"
    "    skills: tl.map(t => ({ id: t.name, name: t.title, description: t.description, tags: t.name === ASOF_NAME ? ['point-in-time', 'data-vintage', 'replay', 'rco-10060', 'mcp'] : ['capital-markets', 'mcp'] })),\n"
    "    'x-allooloo': { role: 'the As Of door on the apex router (index only; the vintage lives at the owning node)', page: ASOF_PAGE, shelf: 'Data Vintage (https://data-vintage.ai/) · Replay', receipts: 'https://mcp.rco-records.ai/mcp', keyring: 'https://allooloo.ai/.well-known/jwks.json', payment: 'https://data-paygo.ai/', licence: 'https://data-licence.ai/', products: ['Issuer https://getissuer.ai/', 'Orderability https://getorderability.ai/', 'Target Market https://gettargetmarket.ai/', 'As Of https://getasof.ai/', 'Issuerwire https://issuerwire.ai/'], same_router_as: 'https://mcp.getissuer.ai/mcp' } };\n"
    "}\n"
    "const asofHuman = host => `<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>getasof — the As Of door</title><link rel=\"canonical\" href=\"${ASOF_PAGE}\"><link rel=\"icon\" href=\"/favicon.ico\" sizes=\"any\"><meta name=\"theme-color\" content=\"#14213D\"><style>body{font-family:system-ui,sans-serif;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.5}code{background:#f3f4f6;padding:.1em .3em}h1{font-size:1.4rem}</style></head><body><h1>getasof — the As Of door</h1><p>${ASOF_LEAD.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</p><p>MCP endpoint (Streamable HTTP): <code>${ASOF_MCP}</code> — the same router as <code>https://mcp.getissuer.ai/mcp</code> · Agent Card: <a href=\"${ASOF_AGENT}\">agent.getasof.ai</a> · the page: <a href=\"${ASOF_PAGE}\">getasof.ai</a></p><p>Operator: Allooloo Technologies Corp., Richmond, BC, Canada.</p></body></html>`;\n"
    "const asofLlms = host => `# ${host} — getasof, the As Of door (MCP)\\n${ASOF_LEAD}\\nDoor: ${ASOF_MCP} (Streamable HTTP, JSON-RPC 2.0, no auth) — the same router as https://mcp.getissuer.ai/mcp: same index, no second copy of the history. Agent Card: ${ASOF_AGENT}. Page: ${ASOF_PAGE}.\\nTools: ${ASOF_TOOLS.join(', ')}. get_as_of(issuer, as_of, market?) is routed to the node of the issuer's listing, which reads its sealed vintage (Data Vintage, the Replay store), signs the answer (EdDSA, kid allooloo-cmr-2026-10, keyring https://allooloo.ai/.well-known/jwks.json) and receipts it at https://mcp.rco-records.ai/mcp (verify_receipt, public; writer: the node). Typed errors: unknown_issuer, before_record, not_sealed, not_found.\\nPaying for a read: https://data-paygo.ai/ (x402, USDC or Open USD on Base; reads are free, the offer answers only when asked) · licence: https://data-licence.ai/\\nProducts: Issuer https://getissuer.ai/ · Orderability https://getorderability.ai/ · Target Market https://gettargetmarket.ai/ · As Of https://getasof.ai/ · Issuerwire https://issuerwire.ai/\\n`;\n"
    "// GETORD-01 (2026-11-02): mcp.getorderability.ai and agent.getorderability.ai are the orderability door on this same router — same index, no second store.")
rep("  const prof = cx && cx.profile ? PROFILES[cx.profile] : null; const ALL = TOOLS.concat(EXTRA_TOOLS); const ord = !prof && cx && ORD_HOST(cx.host);   // GETORD-01",
    "  const prof = cx && cx.profile ? PROFILES[cx.profile] : null; const ALL = TOOLS.concat(EXTRA_TOOLS); const ord = !prof && cx && ORD_HOST(cx.host);   // GETORD-01\n"
    "  const asof = !prof && cx && ASOF_HOST(cx.host);   // ASOF-01")
rep("  const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : tmh ?",
    "  const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : asof ? ASOF_TOOLS.map(n => n === ASOF_NAME ? ASOF_TOOL : ALL.find(t => t.name === n)).filter(Boolean) : tmh ?")
rep("serverInfo: { name: prof ? prof.name : tmh ? 'gettargetmarket' : ord ? 'getorderability' : 'capitalmarketsknowledgegraph', version: SERVER_VERSION }, instructions: prof ? prof.instructions : tmh ? TM_INSTR : ord ? ORD_INSTR :",
    "serverInfo: { name: prof ? prof.name : asof ? 'getasof' : tmh ? 'gettargetmarket' : ord ? 'getorderability' : 'capitalmarketsknowledgegraph', version: SERVER_VERSION }, instructions: prof ? prof.instructions : asof ? ASOF_INSTR : tmh ? TM_INSTR : ord ? ORD_INSTR :")
rep("    if (TM_NAMES.includes(name)) { const r = await tmRoute(name, args, cx || {}); return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: r.isError }); }   // TMKT-02: the node's answer unchanged",
    "    if (TM_NAMES.includes(name)) { const r = await tmRoute(name, args, cx || {}); return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: r.isError }); }   // TMKT-02: the node's answer unchanged\n"
    "    if (name === ASOF_NAME) { const r = await asofRoute(args, cx || {}); return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: r.isError }); }   // ASOF-01: the node's signed answer and receipt unchanged")
rep("  if (TM_HOST(host)) return tmCard(host);   // TMKT-02",
    "  if (ASOF_HOST(host)) return asofCard(host);   // ASOF-01\n  if (TM_HOST(host)) return tmCard(host);   // TMKT-02")
rep("  if (TM_HOST(host)) return tmHuman(host);   // TMKT-02",
    "  if (ASOF_HOST(host)) return asofHuman(host);   // ASOF-01\n  if (TM_HOST(host)) return tmHuman(host);   // TMKT-02")
rep("function llms(host) { if (TM_HOST(host)) return tmLlms(host);",
    "function llms(host) { if (ASOF_HOST(host)) return asofLlms(host); if (TM_HOST(host)) return tmLlms(host);")
rep("function mcpJson(host) { const live = NODES.filter(n => n.live); if (TM_HOST(host)) {",
    "function mcpJson(host) { const live = NODES.filter(n => n.live);\n"
    "  if (ASOF_HOST(host)) { const ALL = TOOLS.concat(EXTRA_TOOLS); return { name: 'getasof', description: 'The As Of door on the apex router: get_as_of routed by issuer to the owning node, which reads its sealed vintage, signs and receipts; index only, no second copy of the history', version: SERVER_VERSION, transport: 'streamable-http', url: ASOF_MCP, authentication: 'none', tools: ASOF_TOOLS.map(n => n === ASOF_NAME ? ASOF_TOOL : ALL.find(t => t.name === n)).filter(Boolean).map(t => ({ name: t.name, description: t.description })), errors: ['unknown_issuer', 'before_record', 'not_sealed', 'not_found'], agent_card: ASOF_AGENT, page: ASOF_PAGE, keyring: 'https://allooloo.ai/.well-known/jwks.json', price: { unit: 'one as-of record read', rate: 'the per-call till (data-paygo.ai): reads are free; the x402 offer answers only when asked; the price of record is the CEO\\'s — to be set for get_as_of', pricing: `https://${host}/x402/pricing.json` }, same_router_as: 'https://mcp.getissuer.ai/mcp', llms: `https://${host}/llms.txt`, operator: OPERATOR, contact: 'developers@allooloo.ai', registry: 'io.github.allooloo/getasof (ASOF-01)', live_nodes: live.map(n => n.node) }; }   // ASOF-01\n"
    "  if (TM_HOST(host)) {")
rep("      if (g.paid && TM_HOST(host)) { pay = await settle(env, g.paid, 'gettargetmarket');",
    "      if (g.paid && ASOF_HOST(host)) { pay = await settle(env, g.paid, 'getasof'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } }); cx.settlement = { network: pay.pr.network, transaction: pay.tx, payer: pay.payer }; }   // ASOF-01: settled before the route, so the node's receipt names it\n"
    "      if (g.paid && TM_HOST(host)) { pay = await settle(env, g.paid, 'gettargetmarket');")
rep("      const g = units ? await decide(request, env, TM_HOST(host) ? {",
    "      const g = units ? await decide(request, env, ASOF_HOST(host) ? { door: 'getasof', resource: `https://${host}/mcp`, description: 'One as-of record read on getasof, the point-in-time door (Allooloo Technologies Corp.)', units } : TM_HOST(host) ? {")
p.write_text(s, encoding='utf-8'); print('patched', p)
