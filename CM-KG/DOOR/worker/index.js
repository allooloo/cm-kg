// CM-KG door — one Worker, two hosts: mcp.ca-cm-kg.ai (Canada node) and mcp.capitalmarketsknowledgegraph.ai (global door).
// Read-only. No auth. Public-record only. Streamable HTTP MCP at /mcp (JSON-RPC 2.0, stateless). Data = Workers Static Assets under /data.
const OPERATOR = 'Allooloo Technologies Corp.';
const SERVER_VERSION = '0.1.0';
const PROTOCOL = '2025-06-18';
const TOOLS = [
  { name: 'resolve_issuer', description: 'Find a listed company by ticker, ISIN or LEI and return its record summary, node and current version.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker (SHOP, TSX:SHOP, SHOP.TO), ISIN (CA82509L1076), LEI (20 characters), or an exact legal name or sourced alias (CPKC).' } }, required: ['identifier'] } },
  { name: 'get_record', description: 'Return the full Capital Markets Record for an issuer, with per-field source, reader and state; optionally a prior version.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker, ISIN, LEI, or a CMR key such as ca-cm-kg/TSX/SHOP.' }, version: { type: 'integer', description: 'Prior version number; omitted = current.' } }, required: ['identifier'] } },
  { name: 'list_events_since', description: 'Return dated, URL\'d disclosure events for an issuer (releases, bulletins, halts, corporate actions, statement and record dates) since a date.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string' }, since: { type: 'string', description: 'YYYY-MM-DD; omitted = full 12-month window.' }, cursor: { type: 'integer', description: 'Offset returned by the previous page.' }, limit: { type: 'integer', description: 'Page size, default 50, max 200.' } }, required: ['identifier'] } },
  { name: 'list_aliases', description: 'Return the sourced trade and former names an issuer releases under.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string' } }, required: ['identifier'] } },
  { name: 'list_nodes', description: 'Return the twelve market nodes and which are live.', inputSchema: { type: 'object', properties: {} } },
];
let INDEX = null, FACTS = null, NODES = null;
async function asset(env, origin, path) {
  const r = await env.ASSETS.fetch(new Request(origin + path));
  return r.ok ? r.json() : null;
}
async function boot(env, origin) {
  if (!INDEX) { [INDEX, FACTS, NODES] = await Promise.all([asset(env, origin, '/index.json'), asset(env, origin, '/facts.json'), asset(env, origin, '/nodes.json')]); }
}
function nodeOf(host) { return host.startsWith('mcp.capitalmarketsknowledgegraph') ? 'global' : 'ca-cm-kg'; }
function headers(extra = {}, asOf = '', version = '') {
  return { 'X-CMR-Node': extra.node || '', 'X-CMR-As-Of': asOf, 'X-CMR-Version': String(version), 'X-CMR-Source': 'public-record', 'X-CMR-Operator': OPERATOR, 'X-CMR-Registry': 'io.github.allooloo/cm-kg', 'Strict-Transport-Security': 'max-age=31536000',
    'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization', 'Access-Control-Expose-Headers': 'X-CMR-Node, X-CMR-As-Of, X-CMR-Version, X-CMR-Source, X-CMR-Operator, Mcp-Session-Id', ...extra.h };
}
function json(obj, status, node, asOf, version, cache) {
  return new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': cache || 'no-store', ...headers({ node }, asOf, version) } });
}
// ---- identifiers
const SUFFIX = { TO: 'TSX', V: 'TSXV', CN: 'CSE', C: 'CSE', NE: 'CBOE-CANADA', CB: 'CBOE-CANADA' };
const PREFIX = { TSX: 'TSX', TSXV: 'TSXV', 'TSX-V': 'TSXV', CVE: 'TSXV', CSE: 'CSE', CNSX: 'CSE', CNQ: 'CSE', NEO: 'CBOE-CANADA', CBOE: 'CBOE-CANADA', 'CBOE-CANADA': 'CBOE-CANADA' };
function resolveKeys(idRaw) {
  const id = (idRaw || '').trim();
  if (!id) return { keys: [], kind: 'empty' };
  const up = id.toUpperCase();
  if (/^CA-CM-KG\//.test(up)) { const k = INDEX.keys.find(x => x.toUpperCase() === up); return { keys: k ? [k] : [], kind: 'cmr' }; }
  if (/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { keys: INDEX.isin[up] || [], kind: 'isin' };
  if (/^[A-Z0-9]{18}[0-9]{2}$/.test(up) && !/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { keys: INDEX.lei[up] || [], kind: 'lei' };
  let ex = null, t = up;
  const pm = up.match(/^([A-Z\-]+):(.+)$/); if (pm && PREFIX[pm[1]]) { ex = PREFIX[pm[1]]; t = pm[2]; }
  const sm = t.match(/^(.+)\.([A-Z]{1,2})$/); if (!ex && sm && SUFFIX[sm[2]] && !(INDEX.ticker[t])) { ex = SUFFIX[sm[2]]; t = sm[1]; }
  let keys = INDEX.ticker[t] || [];
  if (ex) keys = keys.filter(k => k.split('/')[1] === ex);
  if (keys.length) return { keys, kind: 'ticker', exchange: ex, ticker: t };
  // sourced alias or exact legal name (normalised); never fuzzy
  const nk = id.toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
  if (INDEX.alias && INDEX.alias[nk]) return { keys: INDEX.alias[nk], kind: 'alias', matched: id };
  if (INDEX.name && INDEX.name[nk]) return { keys: INDEX.name[nk], kind: 'name', matched: id };
  return { keys: [], kind: 'ticker', exchange: ex, ticker: t };
}
async function record(env, origin, key) { const [, ex, t] = key.split('/'); return asset(env, origin, `/records/${ex}/${encodeURIComponent(t)}.json`); }
async function eventsOf(env, origin, key) { const [, ex, t] = key.split('/'); return (await asset(env, origin, `/events/${ex}/${encodeURIComponent(t)}.json`)) || []; }
function summary(r) {
  const v = f => r.identity[f] ? r.identity[f].value : null;
  return { cmr: r.cmr, node: r.node, version: r.version, as_of: r.as_of, name: v('name'), ticker: v('ticker'), exchange: v('exchange'), security_type: v('security_type'), isin: v('isin'), lei: v('lei'), sector: v('sector'), event_count: r.event_count, events_url: r.events_url, record_url: r.events_url.replace('/events/', '/record/') };
}
// ---- tools
async function callTool(env, origin, host, name, args) {
  const node = nodeOf(host); args = args || {};
  if (name === 'list_nodes') return { doors: node === 'global' ? 'global door: routes by identifier to the node that holds the name' : 'Canada node door', live_nodes: NODES.filter(n => n.live).map(n => n.node), nodes: NODES };
  const res = resolveKeys(args.identifier);
  if (!res.keys.length) return { error: 'not_found', identifier: args.identifier, kind: res.kind, note: node === 'global' ? 'no live node holds this identifier (live today: ca-cm-kg)' : 'no record on ca-cm-kg for this identifier' };
  if (name === 'resolve_issuer') {
    const recs = await Promise.all(res.keys.map(k => record(env, origin, k)));
    return { matches: recs.filter(Boolean).map(summary), matched_by: res.kind, ambiguous: res.keys.length > 1, note: res.keys.length > 1 ? 'identifier matches more than one listing; pick by exchange prefix (TSX:, TSXV:, CSE:, CBOE:)' : (res.kind === 'alias' ? 'matched on a sourced alias' : undefined) };
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
  const { id, method, params } = msg || {};
  if (!method) return rpcError(id, -32600, 'Invalid Request');
  if (method === 'initialize') return rpcResult(id, { protocolVersion: (params && params.protocolVersion) || PROTOCOL, capabilities: { tools: { listChanged: false } }, serverInfo: { name: nodeOf(host) === 'global' ? 'capitalmarketsknowledgegraph' : 'ca-cm-kg', version: SERVER_VERSION },
    instructions: 'Capital Markets Knowledge Graph door. Read-only, public-record only, no auth. Identify issuers by ticker (SHOP, TSX:SHOP, SHOP.TO), ISIN or LEI. Every field carries source_url, read_by and state; null values carry the reason. No prices or market data.' });
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
function human(host, node) {
  const title = node === 'global' ? 'Capital Markets Knowledge Graph — global door' : 'Capital Markets Knowledge Graph — Canada node door';
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest"><meta name="theme-color" content="#14213D"><style>body{font-family:system-ui,sans-serif;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.5}code{background:#f3f4f6;padding:.1em .3em}h1{font-size:1.4rem}</style></head><body><h1>${title}</h1>
<p>A read-only MCP door over the Capital Markets Knowledge Graph. ${node === 'global' ? 'Routes by identifier to the node that holds the name. Live today: Canada (ca-cm-kg).' : 'Scope: TSX, TSXV, CSE, Cboe Canada.'} Public-record only: no prices, no quotes, no licensed market data. No authentication.</p>
<p>MCP endpoint (Streamable HTTP): <code>https://${host}/mcp</code><br>Facts: <a href="/facts.json">/facts.json</a> · <a href="/llms.txt">/llms.txt</a> · record: <code>/record/TSX/SHOP</code> · events: <code>/events/TSX/SHOP?since=2026-06-01</code></p>
<p>Tools: resolve_issuer · get_record · list_events_since · list_aliases · list_nodes. Every field carries its source, its reader and a state (sourced · filled · confirmed · conflict). Records are versioned and never deleted; no signature is present until cm-record signing exists.</p>
<p>Operator: Allooloo Technologies Corp., Vancouver, Canada.</p></body></html>`;
}
function llms(host, node) {
  return `# ${node === 'global' ? 'Capital Markets Knowledge Graph — global door' : 'Capital Markets Knowledge Graph — Canada node door'}
Operator: Allooloo Technologies Corp. Read-only MCP server, Streamable HTTP at https://${host}/mcp, JSON-RPC 2.0, no authentication. Public-record only: no prices, quotes or licensed market data.
${node === 'global' ? 'Routes by identifier to the node that holds the name. Live nodes today: ca-cm-kg (Canada). The other eleven nodes are named by list_nodes and marked not live.' : 'Scope: every listed security on TSX, TSXV, CSE and Cboe Canada (4,820 records, corporate and fund rows alike), with 12 months of dated, URL-carrying disclosure events for the corporate issuers.'}
Tools: resolve_issuer (ticker, ISIN or LEI -> record summary), get_record (full Capital Markets Record with per-field source_url, read_by and state), list_events_since (paged events since a date), list_aliases (sourced trade and former names), list_nodes (the twelve market nodes and which are live).
Identifiers: ticker with or without exchange (SHOP, TSX:SHOP, SHOP.TO, CSE:AWR, AUMB.V), ISIN, LEI. An ambiguous ticker returns every match; the door never guesses.
Record spec: CMR v0 (cm-record.org, draft). Blank stays blank: a field with no value is present with value null and its reason. No signature key exists yet; it is omitted, not stubbed.
GET paths: / (this door), /facts.json, /llms.txt, /record/<EXCHANGE>/<TICKER>, /events/<EXCHANGE>/<TICKER>?since=YYYY-MM-DD&cursor=0&limit=50. Exchanges: TSX, TSXV, CSE, CBOE-CANADA.
`;
}
export default {
  async fetch(request, env, ctx) {
    // edge cache on GET paths (Worker responses are only stored when the Worker puts them there); MCP POST is never cached
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
    const asOf = FACTS ? FACTS.as_of : ''; const ver = FACTS ? FACTS.version : '';
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
    if (p === '/facts.json') return json({ door: host, scope: node, ...FACTS, live_nodes: NODES.filter(n => n.live).map(n => n.node), mcp_url: `https://${host}/mcp` }, 200, node, asOf, ver, 'public, max-age=300');
    if (p === '/nodes.json') return json(NODES, 200, node, asOf, ver, 'public, max-age=3600');
    if (p === '/robots.txt') return new Response('User-agent: *\nAllow: /\n', { headers: { 'content-type': 'text/plain', ...headers({ node }, asOf, ver) } });
    if (['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest'].includes(p)) {
      const a = await env.ASSETS.fetch(new Request(origin + p));
      if (!a.ok) return json({ error: 'not_found' }, 404, node, asOf, ver);
      const h = new Headers(a.headers); h.set('cache-control', 'public, max-age=86400'); for (const [k, v] of Object.entries(headers({ node }, asOf, ver))) h.set(k, v);
      return new Response(a.body, { status: 200, headers: h });
    }
    let m = p.match(/^\/record\/([A-Z\-]+)\/(.+)$/i);
    if (m) { const r = await record(env, origin, `ca-cm-kg/${m[1].toUpperCase()}/${decodeURIComponent(m[2])}`); return r ? json(r, 200, node, asOf, ver, 'public, max-age=3600') : json({ error: 'not_found' }, 404, node, asOf, ver); }
    m = p.match(/^\/events\/([A-Z\-]+)\/(.+)$/i);
    if (m) { const out = await callTool(env, origin, host, 'list_events_since', { identifier: `ca-cm-kg/${m[1].toUpperCase()}/${decodeURIComponent(m[2])}`, since: url.searchParams.get('since') || undefined, cursor: url.searchParams.get('cursor') || 0, limit: url.searchParams.get('limit') || 50 }); return json(out, out.error ? 404 : 200, node, asOf, ver, 'public, max-age=3600'); }
    return json({ error: 'not_found', doors: ['/', '/mcp', '/facts.json', '/llms.txt', '/record/<EXCHANGE>/<TICKER>', '/events/<EXCHANGE>/<TICKER>'] }, 404, node, asOf, ver);
  }
};
