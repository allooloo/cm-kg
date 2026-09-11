// CM-KG door — one Worker, node hosts and the global door: mcp.ca-cm-kg.ai (Canada), mcp.uk-cm-kg.ai (United Kingdom, ORDER-010), mcp.au-cm-kg.ai (Australia, ORDER-013),
// mcp.capitalmarketsknowledgegraph.ai (global door: routes by identifier to the node that holds the name).
// Read-only. No auth. Public-record only. Streamable HTTP MCP at /mcp (JSON-RPC 2.0, stateless). Data = Cloudflare D1 (one database cm-kg, node column;
// tables records / events / idx / meta, loaded by CM-KG\RAILS\door\load_d1.py) since the CEO's D1 order of 2026-09-11; favicons stay on static assets.
const OPERATOR = 'Allooloo Technologies Corp.';
const SERVER_VERSION = '0.3.0';
const PROTOCOL = '2025-06-18';
const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
const TOOLS = [
  { name: 'resolve_issuer', title: 'Resolve issuer', annotations: { title: 'Resolve issuer', ...ANN }, description: 'Find a listed company by ticker, ISIN or LEI and return its record summary, node and current version.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker (SHOP, TSX:SHOP, SHOP.TO, SHEL, LSE:SHEL, SHEL.L, AIM:4BB, AQSE:DGQ, BHP, ASX:BHP, BHP.AX), ISIN (CA82509L1076, GB00BP6MXD84, AU000000BHP4), LEI (20 characters), or an exact legal name or sourced alias.' } }, required: ['identifier'] } },
  { name: 'get_record', title: 'Get Capital Markets Record', annotations: { title: 'Get Capital Markets Record', ...ANN }, description: 'Return the full Capital Markets Record for an issuer, with per-field source, reader and state; optionally a prior version.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker, ISIN, LEI, or a CMR key such as ca-cm-kg/TSX/SHOP, uk-cm-kg/LSE/SHEL or au-cm-kg/ASX/BHP.' }, version: { type: 'integer', description: 'Prior version number; omitted = current.' } }, required: ['identifier'] } },
  { name: 'list_events_since', title: 'List disclosure events since a date', annotations: { title: 'List disclosure events since a date', ...ANN }, description: 'Return dated, URL\'d disclosure events for an issuer (regulatory announcements, registry filings, releases, bulletins, halts, corporate actions, statement and record dates) since a date.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string' }, since: { type: 'string', description: 'YYYY-MM-DD; omitted = full 12-month window.' }, cursor: { type: 'integer', description: 'Offset returned by the previous page.' }, limit: { type: 'integer', description: 'Page size, default 50, max 200.' } }, required: ['identifier'] } },
  { name: 'list_aliases', title: 'List sourced aliases', annotations: { title: 'List sourced aliases', ...ANN }, description: 'Return the sourced trade and former names an issuer releases under.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string' } }, required: ['identifier'] } },
  { name: 'list_nodes', title: 'List market nodes', annotations: { title: 'List market nodes', ...ANN }, description: 'Return the twelve market nodes, which are live, and their record counts.', inputSchema: { type: 'object', properties: {} } },
];
let FACTS = null, NODES = null, BOOTED = 0;
async function meta(env, k) { const row = await env.DB.prepare('SELECT json FROM meta WHERE k = ?').bind(k).first(); return row ? JSON.parse(row.json) : null; }
async function boot(env, origin) {
  if (!FACTS || Date.now() - BOOTED > 300000) { [FACTS, NODES] = await Promise.all([meta(env, 'facts'), meta(env, 'nodes')]); FACTS = FACTS || { nodes: {} }; NODES = NODES || []; BOOTED = Date.now(); }
}
async function lookup(env, kind, value) { const rs = await env.DB.prepare('SELECT cmr FROM idx WHERE kind = ? AND value = ?').bind(kind, value).all(); return (rs.results || []).map(r => r.cmr); }
const HOST_NODE = { 'mcp.ca-cm-kg.ai': 'ca-cm-kg', 'mcp.uk-cm-kg.ai': 'uk-cm-kg', 'mcp.au-cm-kg.ai': 'au-cm-kg' };
function nodeOf(host) { return HOST_NODE[host] || 'global'; }
function nodeFacts(node) { return (FACTS && FACTS.nodes && FACTS.nodes[node]) || null; }
function headers(extra = {}, asOf = '', version = '') {
  return { 'X-CMR-Node': extra.node || '', 'X-CMR-As-Of': asOf, 'X-CMR-Version': String(version), 'X-CMR-Source': 'public-record', 'X-CMR-Operator': OPERATOR, 'X-CMR-Registry': 'io.github.allooloo/cm-kg', 'Strict-Transport-Security': 'max-age=31536000',
    'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization', 'Access-Control-Expose-Headers': 'X-CMR-Node, X-CMR-As-Of, X-CMR-Version, X-CMR-Source, X-CMR-Operator, Mcp-Session-Id', ...extra.h };
}
function json(obj, status, node, asOf, version, cache) {
  return new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': cache || 'no-store', ...headers({ node }, asOf, version) } });
}
// ---- identifiers: exchange prefixes and suffixes per node; suffix L (London) covers LSE and AIM alike; AX (Australia) is ASX
const SUFFIX = { TO: ['TSX'], V: ['TSXV'], CN: ['CSE'], C: ['CSE'], NE: ['CBOE-CANADA'], CB: ['CBOE-CANADA'], L: ['LSE', 'AIM'], LN: ['LSE', 'AIM'], AQ: ['AQSE'], AX: ['ASX'], AU: ['ASX'], NS: ['NSX'] };
const PREFIX = { TSX: 'TSX', TSXV: 'TSXV', 'TSX-V': 'TSXV', CVE: 'TSXV', CSE: 'CSE', CNSX: 'CSE', CNQ: 'CSE', NEO: 'CBOE-CANADA', CBOE: 'CBOE-CANADA', 'CBOE-CANADA': 'CBOE-CANADA', LSE: 'LSE', LON: 'LSE', MAIN: 'LSE', AIM: 'AIM', AQSE: 'AQSE', AQUIS: 'AQSE', NEX: 'AQSE', ASX: 'ASX', XASX: 'ASX', NSX: 'NSX', XNEC: 'NSX' };
const EX_NODE = { TSX: 'ca-cm-kg', TSXV: 'ca-cm-kg', CSE: 'ca-cm-kg', 'CBOE-CANADA': 'ca-cm-kg', LSE: 'uk-cm-kg', AIM: 'uk-cm-kg', AQSE: 'uk-cm-kg', ASX: 'au-cm-kg', NSX: 'au-cm-kg' };
async function resolveKeys(env, idRaw, node) {
  const id = (idRaw || '').trim();
  if (!id) return { keys: [], kind: 'empty' };
  const up = id.toUpperCase();
  const scope = keys => node === 'global' ? keys : keys.filter(k => k.startsWith(node + '/'));
  if (/^[A-Z]{2}-CM-KG\//.test(up)) return { keys: scope(await lookup(env, 'cmr', up)), kind: 'cmr' };
  if (/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { keys: scope(await lookup(env, 'isin', up)), kind: 'isin' };
  if (/^[A-Z0-9]{18}[0-9]{2}$/.test(up) && !/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { keys: scope(await lookup(env, 'lei', up)), kind: 'lei' };
  let exs = null, t = up;
  const pm = up.match(/^([A-Z\-]+):(.+)$/); if (pm && PREFIX[pm[1]]) { exs = [PREFIX[pm[1]]]; t = pm[2]; }
  const sm = t.match(/^(.+)\.([A-Z]{1,2})$/); if (!exs && sm && SUFFIX[sm[2]] && !(await lookup(env, 'ticker', t)).length) { exs = SUFFIX[sm[2]]; t = sm[1]; }
  let keys = scope(await lookup(env, 'ticker', t));
  if (exs) keys = keys.filter(k => exs.includes(k.split('/')[1]));
  if (keys.length) return { keys, kind: 'ticker', exchange: exs ? exs.join('/') : null, ticker: t };
  const nk = id.toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
  { const k = scope(await lookup(env, 'alias', nk)); if (k.length) return { keys: k, kind: 'alias', matched: id }; }
  { const k = scope(await lookup(env, 'name', nk)); if (k.length) return { keys: k, kind: 'name', matched: id }; }
  return { keys: [], kind: 'ticker', exchange: exs ? exs.join('/') : null, ticker: t };
}
async function record(env, origin, key) { const row = await env.DB.prepare('SELECT json FROM records WHERE cmr = ?').bind(key).first(); return row ? JSON.parse(row.json) : null; }
async function eventsOf(env, origin, key) { const rs = await env.DB.prepare('SELECT json FROM events WHERE cmr = ? ORDER BY date DESC, id ASC').bind(key).all(); return (rs.results || []).map(r => JSON.parse(r.json)); }
function summary(r) {
  const v = f => r.identity[f] ? r.identity[f].value : null;
  return { cmr: r.cmr, node: r.node, version: r.version, as_of: r.as_of, name: v('name'), ticker: v('ticker'), exchange: v('exchange'), security_type: v('security_type'), isin: v('isin'), lei: v('lei'), sector: v('sector'), event_count: r.event_count, events_url: r.events_url, record_url: r.events_url.replace('/events/', '/record/') };
}
function liveNodes() { return NODES.filter(n => n.live).map(n => n.node); }
// ---- tools
async function callTool(env, origin, host, name, args) {
  const node = nodeOf(host); args = args || {};
  if (name === 'list_nodes') return { door: node === 'global' ? 'global door: routes by identifier to the node that holds the name' : `${node} node door`, live_nodes: liveNodes(), nodes: NODES };
  const res = await resolveKeys(env, args.identifier, node);
  if (!res.keys.length) return { error: 'not_found', identifier: args.identifier, kind: res.kind, note: node === 'global' ? `no live node holds this identifier (live today: ${liveNodes().join(', ')})` : `no record on ${node} for this identifier` };
  if (name === 'resolve_issuer') {
    const recs = await Promise.all(res.keys.map(k => record(env, origin, k)));
    return { matches: recs.filter(Boolean).map(summary), matched_by: res.kind, ambiguous: res.keys.length > 1, note: res.keys.length > 1 ? 'identifier matches more than one listing; pick by exchange prefix (TSX:, TSXV:, CSE:, CBOE:, LSE:, AIM:, AQSE:) or the CMR key' : (res.kind === 'alias' ? 'matched on a sourced alias' : undefined) };
  }
  if (res.keys.length > 1) return { error: 'ambiguous', matches: res.keys, note: 'more than one listing matches; call again with an exchange prefix or the CMR key' };
  const key = res.keys[0];
  if (name === 'get_record') {
    const r = await record(env, origin, key);
    if (args.version && args.version !== r.version) return { error: 'version_unavailable', requested: args.version, current: r.version, note: 'prior versions begin when the second signed-off sweep lands; version 1 is the only version today' };
    return r;
  }
  if (name === 'list_aliases') { const r = await record(env, origin, key); return { cmr: r.cmr, name: r.identity.name.value, aliases: r.aliases, note: r.aliases.length ? undefined : 'no sourced alias on record' }; }
  if (name === 'list_events_since') {
    let evs = await eventsOf(env, origin, key);
    if (args.since) evs = evs.filter(e => e.date >= args.since);
    const limit = Math.min(Math.max(parseInt(args.limit || 50, 10), 1), 200); const cursor = Math.max(parseInt(args.cursor || 0, 10), 0);
    const page = evs.slice(cursor, cursor + limit);
    return { cmr: key, since: args.since || null, total: evs.length, cursor, limit, next_cursor: cursor + limit < evs.length ? cursor + limit : null, events: page };
  }
  return { error: 'unknown_tool', name };
}
// ---- MCP (Streamable HTTP, stateless)
function rpcResult(id, result) { return { jsonrpc: '2.0', id, result }; }
function rpcError(id, code, message) { return { jsonrpc: '2.0', id: id === undefined ? null : id, error: { code, message } }; }
async function handleRpc(env, origin, host, msg) {
  const { id, method, params } = msg || {}; const node = nodeOf(host);
  if (!method) return rpcError(id, -32600, 'Invalid Request');
  if (method === 'initialize') return rpcResult(id, { protocolVersion: (params && params.protocolVersion) || PROTOCOL, capabilities: { tools: { listChanged: false } }, serverInfo: { name: node === 'global' ? 'capitalmarketsknowledgegraph' : node, version: SERVER_VERSION },
    instructions: `Capital Markets Knowledge Graph door. Read-only, public-record only, no auth. Identify issuers by ticker (SHOP, TSX:SHOP, SHEL, SHEL.L, AIM:4BB), ISIN or LEI. Live nodes: ${liveNodes().join(', ')}. Every field carries source_url, read_by and state; null values carry the reason. No prices or market data.` });
  if (method === 'notifications/initialized' || method.startsWith('notifications/')) return null;
  if (method === 'ping') return rpcResult(id, {});
  if (method === 'tools/list') return rpcResult(id, { tools: TOOLS });
  if (method === 'tools/call') {
    const name = params && params.name; const args = (params && params.arguments) || {};
    if (!TOOLS.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`);
    const out = await callTool(env, origin, host, name, args);
    return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(out) }], structuredContent: out, isError: !!(out && out.error && out.error !== 'ambiguous') });
  }
  if (method === 'resources/list') return rpcResult(id, { resources: [] });
  if (method === 'prompts/list') return rpcResult(id, { prompts: [] });
  return rpcError(id, -32601, `Method not found: ${method}`);
}
// ---- pages
const NODE_COPY = {
  'ca-cm-kg': { title: 'Capital Markets Knowledge Graph — Canada node door', scope: 'Scope: TSX, TSXV, CSE, Cboe Canada.', example: 'TSX/SHOP', exchanges: 'TSX, TSXV, CSE, CBOE-CANADA', ids: 'SHOP, TSX:SHOP, SHOP.TO, CSE:AWR, AUMB.V' },
  'uk-cm-kg': { title: 'Capital Markets Knowledge Graph — United Kingdom node door', scope: 'Scope: LSE Main Market, AIM, Aquis Stock Exchange.', example: 'LSE/SHEL', exchanges: 'LSE, AIM, AQSE', ids: 'SHEL, LSE:SHEL, SHEL.L, AIM:4BB, AQSE:DGQ' },
  'au-cm-kg': { title: 'Capital Markets Knowledge Graph — Australia node door', scope: 'Scope: ASX, NSX (National Stock Exchange of Australia). TMX Australia listings await a machine-readable list.', example: 'ASX/BHP', exchanges: 'ASX, NSX', ids: 'BHP, ASX:BHP, BHP.AX, NSX:SBL' },
};
function human(host, node) {
  const c = NODE_COPY[node] || { title: 'Capital Markets Knowledge Graph — global door', scope: `Routes by identifier to the node that holds the name. Live today: ${liveNodes().join(', ')}.`, example: 'uk-cm-kg/LSE/SHEL', exchanges: 'per node', ids: 'SHOP, SHEL, SHEL.L, AIM:4BB, BHP.AX' };
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${c.title}</title><link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest"><meta name="theme-color" content="#14213D"><style>body{font-family:system-ui,sans-serif;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.5}code{background:#f3f4f6;padding:.1em .3em}h1{font-size:1.4rem}</style></head><body><h1>${c.title}</h1>
<p>A read-only MCP door over the Capital Markets Knowledge Graph. ${c.scope} Public-record only: no prices, no quotes, no licensed market data. No authentication.</p>
<p>MCP endpoint (Streamable HTTP): <code>https://${host}/mcp</code><br>Facts: <a href="/facts.json">/facts.json</a> · <a href="/llms.txt">/llms.txt</a> · record: <code>/record/${c.example}</code> · events: <code>/events/${c.example}?since=2026-06-01</code></p>
<p>Tools: resolve_issuer · get_record · list_events_since · list_aliases · list_nodes. Identifiers: ${c.ids}, an ISIN or an LEI. Every field carries its source, its reader and a state (sourced · filled · confirmed · conflict). Records are versioned and never deleted; no signature is present until cm-record signing exists.</p>
<p>Operator: Allooloo Technologies Corp., Vancouver, Canada.</p></body></html>`;
}
function llms(host, node) {
  const c = NODE_COPY[node]; const nf = nodeFacts(node);
  const scope = c ? `${c.scope} ${nf ? nf.records + ' records, ' + nf.events + ' dated, URL-carrying disclosure events over 12 months for the corporate issuers.' : ''}` : `Routes by identifier to the node that holds the name. Live nodes today: ${liveNodes().join(', ')}. The other nodes are named by list_nodes and marked not live.`;
  return `# ${c ? c.title : 'Capital Markets Knowledge Graph — global door'}
Operator: Allooloo Technologies Corp. Read-only MCP server, Streamable HTTP at https://${host}/mcp, JSON-RPC 2.0, no authentication. Public-record only: no prices, quotes or licensed market data.
${scope}
Tools: resolve_issuer (ticker, ISIN or LEI -> record summary), get_record (full Capital Markets Record with per-field source_url, read_by and state), list_events_since (paged events since a date), list_aliases (sourced trade and former names), list_nodes (the twelve market nodes, which are live, record counts).
Identifiers: ticker with or without exchange (${c ? c.ids : 'SHOP, TSX:SHOP, SHOP.TO, SHEL, SHEL.L, AIM:4BB, AQSE:DGQ, BHP.AX'}), ISIN, LEI. An ambiguous ticker returns every match; the door never guesses.
Record spec: CMR v0 (cm-record.org, draft). Blank stays blank: a field with no value is present with value null and its reason. No signature key exists yet; it is omitted, not stubbed.
GET paths: / (this door), /facts.json, /llms.txt, /nodes.json, /record/<EXCHANGE>/<TICKER> (node hosts) or /record/<node>/<EXCHANGE>/<TICKER> (any host), /events/… likewise with ?since=YYYY-MM-DD&cursor=0&limit=50. Exchanges: ${c ? c.exchanges : 'TSX, TSXV, CSE, CBOE-CANADA (ca-cm-kg); LSE, AIM, AQSE (uk-cm-kg); ASX, NSX (au-cm-kg)'}.
`;
}
export default {
  async fetch(request, env, ctx) {
    if (request.method === 'GET') {
      const cache = caches.default; const hit = await cache.match(request);
      if (hit) { const h = new Headers(hit.headers); h.set('X-CMR-Cache', 'HIT'); return new Response(hit.body, { status: hit.status, headers: h }); }
      const res = await this.handle(request, env);
      const cc = res.headers.get('cache-control') || '';
      if (res.status === 200 && cc.includes('public')) { ctx.waitUntil(cache.put(request, res.clone())); }
      const h = new Headers(res.headers); h.set('X-CMR-Cache', 'MISS'); return new Response(res.body, { status: res.status, headers: h });
    }
    return this.handle(request, env);
  },
  async handle(request, env) {
    const url = new URL(request.url); const host = url.hostname; const origin = url.origin; const node = nodeOf(host);
    await boot(env, origin);
    const nf = nodeFacts(node); const asOf = nf ? nf.as_of : (FACTS ? FACTS.as_of : ''); const ver = nf ? nf.version : (FACTS ? (FACTS.version || 1) : '');
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: headers({ node }, asOf, ver) });
    if (env.RL) { try { const ip = request.headers.get('cf-connecting-ip') || 'anon'; const { success } = await env.RL.limit({ key: ip }); if (!success) return json({ error: 'rate_limited', note: 'generous per-IP limit; try again in a minute' }, 429, node, asOf, ver); } catch (e) {} }
    const p = url.pathname.replace(/\/+$/, '') || '/';
    if (p === '/mcp') {
      if (request.method === 'GET') return new Response('Method Not Allowed: this door serves stateless Streamable HTTP; POST JSON-RPC to /mcp', { status: 405, headers: { 'content-type': 'text/plain', Allow: 'POST, OPTIONS', ...headers({ node }, asOf, ver) } });
      if (request.method === 'DELETE') return new Response(null, { status: 204, headers: headers({ node }, asOf, ver) });
      if (request.method !== 'POST') return new Response('Method Not Allowed', { status: 405, headers: headers({ node }, asOf, ver) });
      let body; try { body = await request.json(); } catch (e) { return json(rpcError(null, -32700, 'Parse error'), 400, node, asOf, ver); }
      const batch = Array.isArray(body); const msgs = batch ? body : [body];
      const outs = []; for (const m of msgs) { const r = await handleRpc(env, origin, host, m); if (r) outs.push(r); }
      if (!outs.length) return new Response(null, { status: 202, headers: headers({ node }, asOf, ver) });
      return json(batch ? outs : outs[0], 200, node, asOf, ver, 'no-store');
    }
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405, headers: headers({ node }, asOf, ver) });
    if (p === '/') return new Response(human(host, node), { status: 200, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300', ...headers({ node }, asOf, ver) } });
    if (p === '/llms.txt') return new Response(llms(host, node), { status: 200, headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=3600', ...headers({ node }, asOf, ver) } });
    if (p === '/facts.json') return json({ door: host, scope: node, ...(node === 'global' ? FACTS : { ...FACTS, node, ...(nf || {}) }), live_nodes: liveNodes(), mcp_url: `https://${host}/mcp` }, 200, node, asOf, ver, 'public, max-age=300');
    if (p === '/nodes.json') return json(NODES, 200, node, asOf, ver, 'public, max-age=3600');
    if (p === '/robots.txt') return new Response('User-agent: *\nAllow: /\n', { headers: { 'content-type': 'text/plain', ...headers({ node }, asOf, ver) } });
    if (['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest'].includes(p)) {
      const a = await env.ASSETS.fetch(new Request(origin + p));
      if (!a.ok) return json({ error: 'not_found' }, 404, node, asOf, ver);
      const h = new Headers(a.headers); h.set('cache-control', 'public, max-age=86400'); for (const [k, v] of Object.entries(headers({ node }, asOf, ver))) h.set(k, v);
      return new Response(a.body, { status: 200, headers: h });
    }
    // /record/<node>/<EX>/<T> on any host; /record/<EX>/<T> on a node host (or, on the global door, resolved by the exchange's node)
    let m = p.match(/^\/(record|events)\/([a-z]{2}-cm-kg)\/([A-Z\-]+)\/(.+)$/i) || p.match(/^\/(record|events)\/([A-Z\-]+)\/(.+)$/i);
    if (m) {
      const kind = m[1].toLowerCase(); let key;
      if (m.length === 5) key = `${m[2].toLowerCase()}/${m[3].toUpperCase()}/${decodeURIComponent(m[4])}`;
      else { const ex = m[2].toUpperCase(); const n = node !== 'global' ? node : (EX_NODE[ex] || 'ca-cm-kg'); key = `${n}/${ex}/${decodeURIComponent(m[3])}`; }
      if (kind === 'record') { const r = await record(env, origin, key); return r ? json(r, 200, node, asOf, ver, 'public, max-age=3600') : json({ error: 'not_found', key }, 404, node, asOf, ver); }
      const out = await callTool(env, origin, host, 'list_events_since', { identifier: key, since: url.searchParams.get('since') || undefined, cursor: url.searchParams.get('cursor') || 0, limit: url.searchParams.get('limit') || 50 });
      return json(out, out.error ? 404 : 200, node, asOf, ver, 'public, max-age=3600');
    }
    return json({ error: 'not_found', doors: ['/', '/mcp', '/facts.json', '/llms.txt', '/nodes.json', '/record/<EXCHANGE>/<TICKER>', '/record/<node>/<EXCHANGE>/<TICKER>', '/events/…'] }, 404, node, asOf, ver);
  }
};
