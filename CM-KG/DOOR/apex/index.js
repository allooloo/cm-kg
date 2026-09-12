// CM-KG apex router (ORDER-018 re-cut): mcp.capitalmarketsknowledgegraph.ai. Control plane global, data plane regional. This Worker holds only the
// index (ticker / ISIN / LEI / name / alias / CMR key -> node) as a static asset and the node list; list_nodes answers here; every record and
// event call is forwarded to the owning node's regional door (Azure Container App in the node's region). No record body is stored or cached
// at the apex. No fallback: if a node's regional door does not answer, the apex returns unavailable for that node — never a record from
// another store. The old shared Worker + D1 door (cm-kg-door) stays deployed beside this one and is listed for CEO deletion at end of scope.
// Agent Card at agent.capitalmarketsknowledgegraph.ai describes the router and lists the node agents.
const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.11.0'; const PROTOCOL = '2025-06-18';
const REGIONAL = {  // node -> regional door origin (Container Apps FQDN; direct to the origin, not through the node's Cloudflare hostname)
  'ca-cm-kg': 'https://cmkg-door-ca.nicemushroom-8b4ba259.canadacentral.azurecontainerapps.io', 'uk-cm-kg': 'https://cmkg-door-uk.livelybay-3553b0b4.uksouth.azurecontainerapps.io', 'au-cm-kg': 'https://cmkg-door-au.politeplant-e73e0a46.australiaeast.azurecontainerapps.io',
  'sg-cm-kg': 'https://cmkg-door-sg.ambitioussand-03ccaab5.southeastasia.azurecontainerapps.io', 'ch-cm-kg': 'https://cmkg-door-ch.gentledune-3c70acd2.switzerlandnorth.azurecontainerapps.io', 'de-cm-kg': 'https://cmkg-door-de.greensand-6ae55941.germanywestcentral.azurecontainerapps.io',
  'fr-cm-kg': 'https://cmkg-door-fr.agreeablehill-d2a7639b.francecentral.azurecontainerapps.io', 'nl-cm-kg': 'https://cmkg-door-nl.purpleisland-61490c7a.westeurope.azurecontainerapps.io', 'jp-cm-kg': 'https://cmkg-door-jp.calmpebble-18a3633a.japaneast.azurecontainerapps.io',
  'kr-cm-kg': 'https://cmkg-door-kr.calmpond-68249885.koreacentral.azurecontainerapps.io', 'us-cm-kg': 'https://cmkg-door-us.purpleglacier-e6bfd21c.eastus.azurecontainerapps.io' };
const PUBLIC = {}; for (const n of Object.keys(REGIONAL)) PUBLIC[n] = { door: `https://mcp.${n}.ai/mcp`, agent_card: `https://agent.${n}.ai/.well-known/agent-card.json` };
const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
const TOOLS = [
  { name: 'resolve_issuer', title: 'Resolve issuer', annotations: { title: 'Resolve issuer', ...ANN }, description: 'Find a listed company by ticker, ISIN or LEI: the apex names the owning node and forwards to that node\'s regional door for the record summary.', inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker with or without exchange (SHOP, TSX:SHOP, SHEL.L, BHP.AX, D05.SI, NESN.SW, SAP.DE, 7203.T, 005930.KS), ISIN, LEI, an exact legal name or a sourced alias.' } }, required: ['identifier'] } },
  { name: 'get_record', title: 'Get Capital Markets Record', annotations: { title: 'Get Capital Markets Record', ...ANN }, description: 'Return the full Capital Markets Record, served by the owning node\'s regional door (never stored at the apex).', inputSchema: { type: 'object', properties: { identifier: { type: 'string' }, version: { type: 'integer' } }, required: ['identifier'] } },
  { name: 'list_events_since', title: 'List disclosure events since a date', annotations: { title: 'List disclosure events since a date', ...ANN }, description: 'Dated, URL\'d disclosure events for an issuer since a date, served by the owning node\'s regional door.', inputSchema: { type: 'object', properties: { identifier: { type: 'string' }, since: { type: 'string' }, cursor: { type: 'integer' }, limit: { type: 'integer' } }, required: ['identifier'] } },
  { name: 'list_aliases', title: 'List sourced aliases', annotations: { title: 'List sourced aliases', ...ANN }, description: 'Sourced trade and former names, served by the owning node\'s regional door.', inputSchema: { type: 'object', properties: { identifier: { type: 'string' } }, required: ['identifier'] } },
  { name: 'list_nodes', title: 'List market nodes', annotations: { title: 'List market nodes', ...ANN }, description: 'The twelve market nodes, which are live, their regional doors and Agent Cards.', inputSchema: { type: 'object', properties: {} } },
];
let INDEX = null, NODES = null;
async function boot(env, origin) {
  if (INDEX) return;
  const [i, n] = await Promise.all([env.ASSETS.fetch(new Request(origin + '/index.json')), env.ASSETS.fetch(new Request(origin + '/nodes.json'))]);
  INDEX = i.ok ? await i.json() : { ticker: {}, isin: {}, lei: {}, alias: {}, name: {}, cmr: {} }; NODES = n.ok ? await n.json() : [];
}
const SUFFIX = { TO: 'ca-cm-kg', V: 'ca-cm-kg', CN: 'ca-cm-kg', NE: 'ca-cm-kg', L: 'uk-cm-kg', LN: 'uk-cm-kg', AQ: 'uk-cm-kg', AX: 'au-cm-kg', AU: 'au-cm-kg', NS: 'au-cm-kg', SI: 'sg-cm-kg', SG: 'sg-cm-kg', SW: 'ch-cm-kg', VX: 'ch-cm-kg', BX: 'ch-cm-kg', DE: 'de-cm-kg', F: 'de-cm-kg', XE: 'de-cm-kg', PA: 'fr-cm-kg', AS: 'nl-cm-kg', NA: 'nl-cm-kg', T: 'jp-cm-kg', JP: 'jp-cm-kg', KS: 'kr-cm-kg', KQ: 'kr-cm-kg', KN: 'kr-cm-kg', N: 'us-cm-kg', O: 'us-cm-kg', OQ: 'us-cm-kg', US: 'us-cm-kg' };
const PREFIX = { TSX: 'ca-cm-kg', TSXV: 'ca-cm-kg', 'TSX-V': 'ca-cm-kg', CVE: 'ca-cm-kg', CSE: 'ca-cm-kg', CNSX: 'ca-cm-kg', NEO: 'ca-cm-kg', CBOE: 'ca-cm-kg', 'CBOE-CANADA': 'ca-cm-kg', LSE: 'uk-cm-kg', LON: 'uk-cm-kg', AIM: 'uk-cm-kg', AQSE: 'uk-cm-kg', ASX: 'au-cm-kg', NSX: 'au-cm-kg', SGX: 'sg-cm-kg', CATALIST: 'sg-cm-kg', 'SGX-CATALIST': 'sg-cm-kg', SIX: 'ch-cm-kg', SWX: 'ch-cm-kg', BX: 'ch-cm-kg', XETRA: 'de-cm-kg', ETR: 'de-cm-kg', FRA: 'de-cm-kg', DE: 'de-cm-kg', EUREX: 'de-cm-kg', XPAR: 'fr-cm-kg', EPA: 'fr-cm-kg', ALXP: 'fr-cm-kg', XMLI: 'fr-cm-kg', EURONEXT: 'fr-cm-kg', XAMS: 'nl-cm-kg', AMS: 'nl-cm-kg', AEX: 'nl-cm-kg', ALXA: 'nl-cm-kg', TSE: 'jp-cm-kg', TYO: 'jp-cm-kg', JPX: 'jp-cm-kg', 'TSE-PRIME': 'jp-cm-kg', 'TSE-STANDARD': 'jp-cm-kg', 'TSE-GROWTH': 'jp-cm-kg', 'TSE-PRO': 'jp-cm-kg', 'TSE-REIT': 'jp-cm-kg', KRX: 'kr-cm-kg', KOSPI: 'kr-cm-kg', KOSDAQ: 'kr-cm-kg', KONEX: 'kr-cm-kg', NYSE: 'us-cm-kg', NASDAQ: 'us-cm-kg', XNYS: 'us-cm-kg', XNAS: 'us-cm-kg' };
function nodesFor(kind, value) { const v = INDEX[kind] && INDEX[kind][value]; return v ? [].concat(v) : []; }
function whichNode(idRaw) {
  const id = (idRaw || '').trim(); if (!id) return { nodes: [], kind: 'empty' };
  const up = id.toUpperCase(); let m;
  if ((m = up.match(/^([A-Z]{2}-CM-KG)\//))) return { nodes: [m[1].toLowerCase()], kind: 'cmr' };
  if (/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { nodes: nodesFor('isin', up), kind: 'isin' };
  if (/^[A-Z0-9]{18}[0-9]{2}$/.test(up)) return { nodes: nodesFor('lei', up), kind: 'lei' };
  const pm = up.match(/^([A-Z\-]+):(.+)$/); if (pm && PREFIX[pm[1]]) return { nodes: [PREFIX[pm[1]]], kind: 'ticker' };
  const sm = up.match(/^(.+)\.([A-Z]{1,2})$/); if (sm && SUFFIX[sm[2]] && !nodesFor('ticker', up).length) return { nodes: [SUFFIX[sm[2]]], kind: 'ticker' };
  let n = nodesFor('ticker', up); if (n.length) return { nodes: n, kind: 'ticker' };
  const nk = id.toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
  n = nodesFor('alias', nk); if (n.length) return { nodes: n, kind: 'alias' };
  n = nodesFor('name', nk); if (n.length) return { nodes: n, kind: 'name' };
  return { nodes: [], kind: 'ticker' };
}
async function forward(node, name, args) {
  const origin = REGIONAL[node]; if (!origin) return { error: 'unavailable', node, note: 'no regional door configured for this node' };
  try {
    const r = await fetch(origin + '/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(20000) });
    if (!r.ok) return { error: 'unavailable', node, note: `regional door answered ${r.status}`, regional_door: PUBLIC[node].door };
    const j = await r.json(); const out = (j.result && j.result.structuredContent) || { error: 'unavailable', node, note: 'regional door returned no structured content' };
    if (out && typeof out === 'object' && !Array.isArray(out)) out.served_by = { node, regional_door: PUBLIC[node].door, agent_card: PUBLIC[node].agent_card };
    return out;
  } catch (e) { return { error: 'unavailable', node, note: `regional door did not answer (${e.name || 'error'}); no fallback — the record lives only in its own region`, regional_door: PUBLIC[node].door }; }
}
async function callTool(name, args) {
  args = args || {};
  if (name === 'list_nodes') return { door: 'apex router: index only; records and events are served by each node\'s regional door', live_nodes: NODES.filter(n => n.live).map(n => n.node), nodes: NODES.map(n => ({ ...n, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null, agent_card: PUBLIC[n.node] ? PUBLIC[n.node].agent_card : null })) };
  const w = whichNode(args.identifier);
  if (!w.nodes.length) return { error: 'not_found', identifier: args.identifier, kind: w.kind, note: 'no node in the index holds this identifier' };
  if (name === 'resolve_issuer') {
    const outs = await Promise.all(w.nodes.map(n => forward(n, name, args)));
    const matches = [].concat(...outs.map(o => o.matches || [])); const unavailable = outs.filter(o => o.error === 'unavailable');
    return { matches, matched_by: w.kind, ambiguous: matches.length > 1, nodes_asked: w.nodes, unavailable: unavailable.length ? unavailable : undefined, note: unavailable.length ? 'one or more regional doors did not answer; no fallback store' : undefined };
  }
  if (w.nodes.length > 1) return { error: 'ambiguous', nodes: w.nodes, note: 'the identifier lives on more than one node; add an exchange prefix or use the CMR key' };
  return forward(w.nodes[0], name, args);
}
function rpcResult(id, result) { return { jsonrpc: '2.0', id, result }; }
function rpcError(id, code, message) { return { jsonrpc: '2.0', id: id === undefined ? null : id, error: { code, message } }; }
async function handleRpc(msg) {
  const { id, method, params } = msg || {};
  if (!method) return rpcError(id, -32600, 'Invalid Request');
  if (method === 'initialize') return rpcResult(id, { protocolVersion: (params && params.protocolVersion) || PROTOCOL, capabilities: { tools: { listChanged: false } }, serverInfo: { name: 'capitalmarketsknowledgegraph', version: SERVER_VERSION }, instructions: 'Capital Markets Knowledge Graph apex: an index-only router. Identify an issuer by ticker, ISIN or LEI; the record is served by the owning node\'s regional door in its own jurisdiction. Read-only, public-record only, no auth, no prices.' });
  if (method.startsWith('notifications/')) return null;
  if (method === 'ping') return rpcResult(id, {});
  if (method === 'tools/list') return rpcResult(id, { tools: TOOLS });
  if (method === 'tools/call') { const name = params && params.name; if (!TOOLS.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`); const out = await callTool(name, (params && params.arguments) || {}); return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(out) }], structuredContent: out, isError: !!(out && out.error && out.error !== 'ambiguous') }); }
  if (method === 'resources/list') return rpcResult(id, { resources: [] });
  if (method === 'prompts/list') return rpcResult(id, { prompts: [] });
  return rpcError(id, -32601, `Method not found: ${method}`);
}
function agentCard() {
  return { name: 'Capital Markets Knowledge Graph — apex router', description: 'Index-only router over the Capital Markets Knowledge Graph: names the node that holds an issuer (ticker, ISIN, LEI, legal name or sourced alias) and forwards record and event calls to that node\'s regional door. No record body is stored or served from the apex; each node\'s data lives and is served in its own jurisdiction. Read-only, public-record only, no auth, no prices.',
    url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp', preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp', transport: 'JSONRPC' }], additionalInterfaces: [{ url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp', transport: 'JSONRPC' }], securitySchemes: {}, security: [], defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'], iconUrl: 'https://mcp.capitalmarketsknowledgegraph.ai/icon-512.png', provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: SERVER_VERSION, documentationUrl: 'https://mcp.capitalmarketsknowledgegraph.ai/llms.txt', protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false }, defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'],
    skills: TOOLS.map(t => ({ id: t.name, name: t.title, description: t.description, tags: ['capital-markets', 'public-record', 'router', 'mcp'] })),
    'x-cmkg': { role: 'apex router', transport: 'MCP Streamable HTTP (JSON-RPC 2.0, stateless, no auth)', registry: 'io.github.allooloo/cm-kg', contact: 'allooloo@users.noreply.github.com', node_agents: (NODES || []).map(n => ({ node: n.node, country: n.country, live: !!n.live, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null, agent_card: PUBLIC[n.node] ? PUBLIC[n.node].agent_card : null })), old_shared_door: 'the Cloudflare Worker + D1 door (cm-kg-door) stays deployed beside this router and is listed for CEO deletion at end of scope' } };
}
function headers(extra = {}) { return { 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-CMR-Node': 'apex', 'X-CMR-Source': 'public-record', 'X-CMR-Operator': OPERATOR, 'X-CMR-Registry': 'io.github.allooloo/cm-kg', 'X-CMR-Version': SERVER_VERSION, 'Strict-Transport-Security': 'max-age=31536000', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization', 'Access-Control-Expose-Headers': 'X-CMR-Node, X-CMR-Source, X-CMR-Operator, X-CMR-Version, Mcp-Session-Id', ...extra }; }
function json(obj, status = 200, cache = 'no-store') { return new Response(JSON.stringify(obj), { status, headers: headers({ 'content-type': 'application/json; charset=utf-8', 'cache-control': cache }) }); }
function human() {
  const live = NODES.filter(n => n.live);
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capital Markets Knowledge Graph — apex router</title><link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><meta name="theme-color" content="#14213D"><style>body{font-family:system-ui,sans-serif;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.5}code{background:#f3f4f6;padding:.1em .3em}h1{font-size:1.4rem}</style></head><body><h1>Capital Markets Knowledge Graph — apex router</h1>
<p>Index-only. This door names the node that holds an issuer and forwards record and event calls to that node's regional door; no record body lives here. Each node's data is served in its own jurisdiction. Read-only, public-record only, no authentication, no prices.</p>
<p>MCP endpoint (Streamable HTTP): <code>https://mcp.capitalmarketsknowledgegraph.ai/mcp</code> · Agent Card: <a href="https://agent.capitalmarketsknowledgegraph.ai/.well-known/agent-card.json">agent.capitalmarketsknowledgegraph.ai</a> · <a href="/nodes.json">/nodes.json</a> · <a href="/llms.txt">/llms.txt</a></p>
<p>Live nodes (${live.length}): ${live.map(n => `<a href="${PUBLIC[n.node] ? PUBLIC[n.node].door.replace('/mcp', '/') : '#'}">${n.country}</a>`).join(' · ')}</p>
<p>Operator: Allooloo Technologies Corp., Vancouver, Canada.</p></body></html>`;
}
function llms() { return `# Capital Markets Knowledge Graph — apex router\nOperator: Allooloo Technologies Corp. Read-only MCP server at https://mcp.capitalmarketsknowledgegraph.ai/mcp (Streamable HTTP, JSON-RPC 2.0, no auth). Index only: ticker / ISIN / LEI / legal name / sourced alias -> node. Records and events are served by each node's regional door in its own jurisdiction and forwarded through here; nothing is stored at the apex; no fallback store.\nTools: resolve_issuer, get_record, list_events_since, list_aliases (forwarded), list_nodes (answered here).\nNodes: ${(NODES || []).map(n => `${n.node} (${n.country}, ${n.live ? 'live' : 'not live'}) door ${PUBLIC[n.node] ? PUBLIC[n.node].door : '-'} card ${PUBLIC[n.node] ? PUBLIC[n.node].agent_card : '-'}`).join('; ')}\nGET paths: /, /nodes.json, /llms.txt, /.well-known/agent-card.json, /record/<node>/<EXCHANGE>/<CODE> and /events/<node>/<EXCHANGE>/<CODE> (forwarded to the node).\n`; }
const CSP = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; base-uri 'none'; form-action https://formspree.io; frame-ancestors 'none'; upgrade-insecure-requests";
const ROBOTS = host => `User-agent: *\nAllow: /\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: Claude-User\nAllow: /\n\nUser-agent: Claude-SearchBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: Perplexity-User\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\nUser-agent: Bingbot\nAllow: /\n\nUser-agent: Applebot\nAllow: /\n\nUser-agent: Applebot-Extended\nAllow: /\n\nUser-agent: Amazonbot\nAllow: /\n\nUser-agent: CCBot\nAllow: /\n\nUser-agent: DuckAssistBot\nAllow: /\n\nUser-agent: meta-externalagent\nAllow: /\n\nUser-agent: Bytespider\nAllow: /\n\nUser-agent: cohere-ai\nAllow: /\n\nUser-agent: Diffbot\nAllow: /\n\nUser-agent: YouBot\nAllow: /\n\nUser-agent: MistralAI-User\nAllow: /\n\nUser-agent: xAI-Grok\nAllow: /\n\nSitemap: https://${host}/sitemap.xml\n`;
const SECURITY = host => `Contact: mailto:developers@allooloo.ai\nContact: https://allooloo.io\nExpires: 2027-09-12T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: https://allooloo.io\n`;
const KIT_PATHS = ['/', '/llms.txt', '/facts.json', '/nodes.json', '/robots.txt', '/sitemap.xml', '/mcp.json', '/openapi.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
function sitemap(host) { return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${KIT_PATHS.filter(x => x !== '/robots.txt').map(x => `<url><loc>https://${host}${x === '/' ? '/' : x}</loc></url>`).join('')}</urlset>\n`; }
function mcpJson(host) { const live = NODES.filter(n => n.live); return { name: 'cm-kg apex', description: 'Capital Markets Knowledge Graph — apex router: index only, forwards every call to the node that holds the identifier; no record body leaves its jurisdiction', version: SERVER_VERSION, transport: 'streamable-http', url: `https://${host}/mcp`, authentication: 'none', tools: TOOLS.map(t => ({ name: t.name, description: t.description })), agent_card: 'https://agent.capitalmarketsknowledgegraph.ai/.well-known/agent-card.json', openapi: `https://${host}/openapi.json`, llms: `https://${host}/llms.txt`, facts: `https://${host}/facts.json`, operator: OPERATOR, contact: 'developers@allooloo.ai', registry: 'io.github.allooloo/cm-kg', live_nodes: live.map(n => n.node), records: live.reduce((a, n) => a + (n.records || 0), 0), events: live.reduce((a, n) => a + (n.events || 0), 0), regional_doors: Object.fromEntries(live.map(n => [n.node, PUBLIC[n.node] ? PUBLIC[n.node].door : null])) }; }
function openapi(host) {
  const params = [{ name: 'node', in: 'path', required: true, schema: { type: 'string' } }, { name: 'exchange', in: 'path', required: true, schema: { type: 'string' } }, { name: 'code', in: 'path', required: true, schema: { type: 'string' } }];
  return { openapi: '3.1.0', info: { title: 'cm-kg apex router', version: SERVER_VERSION, description: 'Apex router of the Capital Markets Knowledge Graph: MCP over Streamable HTTP at /mcp; identifier index only; forwards to the regional door that holds the record. Public-record only.', contact: { name: OPERATOR, email: 'developers@allooloo.ai', url: 'https://allooloo.io' } }, servers: [{ url: `https://${host}` }],
    paths: { '/mcp': { post: { summary: 'MCP JSON-RPC (tools/list, tools/call)', requestBody: { required: true, content: { 'application/json': { schema: { type: 'object' } } } }, responses: { 200: { description: 'JSON-RPC response' } } } },
      '/record/{node}/{exchange}/{code}': { get: { summary: 'Capital Markets Record, forwarded to the owning node', parameters: params, responses: { 200: { description: 'record' }, 404: { description: 'not found' }, 503: { description: 'node unavailable, no fallback' } } } },
      '/events/{node}/{exchange}/{code}': { get: { summary: 'Dated disclosure events, forwarded to the owning node', parameters: params, responses: { 200: { description: 'events page' } } } },
      '/nodes.json': { get: { summary: 'The twelve nodes with live counts', responses: { 200: { description: 'nodes' } } } }, '/facts.json': { get: { summary: 'Apex facts', responses: { 200: { description: 'facts' } } } }, '/llms.txt': { get: { summary: 'Machine instructions', responses: { 200: { description: 'text' } } } }, '/.well-known/agent-card.json': { get: { summary: 'A2A Agent Card', responses: { 200: { description: 'card' } } } } } };
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url); const host = url.hostname; const origin = url.origin; await boot(env, origin);
    const p = url.pathname.replace(/\/+$/, '') || '/';
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: headers() });
    if (p === '/mcp') {
      if (request.method !== 'POST') return new Response('POST JSON-RPC to /mcp', { status: 405, headers: headers({ 'content-type': 'text/plain', Allow: 'POST, OPTIONS' }) });
      let body; try { body = await request.json(); } catch (e) { return json(rpcError(null, -32700, 'Parse error'), 400); }
      const batch = Array.isArray(body); const outs = []; for (const m of (batch ? body : [body])) { const r = await handleRpc(m); if (r) outs.push(r); }
      if (!outs.length) return new Response(null, { status: 202, headers: headers() });
      return json(batch ? outs : outs[0]);
    }
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405, headers: headers() });
    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json' || (host.startsWith('agent.') && p === '/')) return json(agentCard(), 200, 'public, max-age=300');
    if (p === '/') return new Response(human(), { status: 200, headers: headers({ 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' }) });
    if (p === '/llms.txt') return new Response(llms(), { status: 200, headers: headers({ 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=3600' }) });
    if (p === '/nodes.json') return json(NODES.map(n => ({ ...n, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null, agent_card: PUBLIC[n.node] ? PUBLIC[n.node].agent_card : null })), 200, 'public, max-age=3600');
    if (p === '/facts.json') return json({ door: host, role: 'apex router (index only)', live_nodes: NODES.filter(n => n.live).map(n => n.node), nodes: Object.fromEntries(NODES.map(n => [n.node, { live: !!n.live, records: n.records, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null }])), operator: OPERATOR, source: 'public-record', mcp_url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp' }, 200, 'public, max-age=300');
    if (p === '/robots.txt') return new Response(ROBOTS(host), { headers: headers({ 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=86400' }) });
    if (p === '/.well-known/security.txt') return new Response(SECURITY(host), { headers: headers({ 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=86400' }) });
    if (p === '/sitemap.xml') return new Response(sitemap(host), { headers: headers({ 'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=3600' }) });
    if (p === '/mcp.json') return json(mcpJson(host), 200, 'public, max-age=300');
    if (p === '/openapi.json') return json(openapi(host), 200, 'public, max-age=3600');
    if (['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-48.png', '/icon-96.png', '/icon-144.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest'].includes(p)) { const a = await env.ASSETS.fetch(new Request(origin + p)); return a.ok ? new Response(a.body, { status: 200, headers: headers({ 'content-type': a.headers.get('content-type') || 'application/octet-stream', 'cache-control': 'public, max-age=86400' }) }) : json({ error: 'not_found' }, 404); }
    let m = p.match(/^\/(record|events)\/([a-z]{2}-cm-kg)\/([A-Z\-]+)\/(.+)$/i);
    if (m) { const node = m[2].toLowerCase(); const key = `${node}/${m[3].toUpperCase()}/${decodeURIComponent(m[4])}`; const out = m[1].toLowerCase() === 'record' ? await forward(node, 'get_record', { identifier: key }) : await forward(node, 'list_events_since', { identifier: key, since: url.searchParams.get('since') || undefined, cursor: url.searchParams.get('cursor') || 0, limit: url.searchParams.get('limit') || 50 }); return json(out, out.error ? (out.error === 'unavailable' ? 503 : 404) : 200); }
    return json({ error: 'not_found', doors: ['/', '/mcp', '/nodes.json', '/facts.json', '/llms.txt', '/.well-known/agent-card.json', '/record/<node>/<EXCHANGE>/<CODE>', '/events/<node>/<EXCHANGE>/<CODE>'] }, 404);
  }
};
