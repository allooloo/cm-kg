// CM-KG regional node door (ORDER-018, sovereign estate). One image, one node per container: NODE (e.g. jp-cm-kg), REGION (e.g. japaneast),
// STORAGE_ACCOUNT / STORAGE_KEY / STORAGE_CONTAINER (the node's regional pond), PUBLIC_HOST (mcp.<node>.ai). Same five MCP tools, same headers and
// paths as the Cloudflare Worker door, reading its own regional store only: door/index.json (loaded at boot, refreshed every ten minutes),
// door/records/<EX>/<code>.json and door/events/<EX>/<code>.json fetched on demand and cached in memory. No record body from any other node.
// A2A Agent Card at /.well-known/agent-card.json (and /.well-known/agent.json), and at / on the agent.<node>.ai host. Read-only, no auth, public-record only.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';
const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.11.0'; const PROTOCOL = '2025-06-18';
const NODE = process.env.NODE || 'ca-cm-kg'; const REGION = process.env.REGION || ''; const PUBLIC_HOST = process.env.PUBLIC_HOST || `mcp.${NODE}.ai`; const AGENT_HOST = `agent.${NODE}.ai`;
const CONTACT = process.env.CONTACT || 'allooloo@users.noreply.github.com'; const PORT = parseInt(process.env.PORT || '8080', 10);
const cred = new StorageSharedKeyCredential(process.env.STORAGE_ACCOUNT, process.env.STORAGE_KEY);
const container = new BlobServiceClient(`https://${process.env.STORAGE_ACCOUNT}.blob.core.windows.net`, cred).getContainerClient(process.env.STORAGE_CONTAINER || 'pond');
const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
const TOOLS = [
  { name: 'resolve_issuer', title: 'Resolve issuer', annotations: { title: 'Resolve issuer', ...ANN }, description: 'Find a listed company by ticker, ISIN or LEI and return its record summary, node and current version.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker with or without exchange (SHOP, TSX:SHOP, SHOP.TO, SHEL.L, BHP.AX, D05.SI, NESN.SW, SAP.DE, 7203.T, 005930.KS; on the Euronext nodes the ISIN is the key), ISIN, LEI (20 characters), or an exact legal name or sourced alias.' } }, required: ['identifier'] } },
  { name: 'get_record', title: 'Get Capital Markets Record', annotations: { title: 'Get Capital Markets Record', ...ANN }, description: 'Return the full Capital Markets Record for an issuer, with per-field source, reader and state; optionally a prior version.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker, ISIN, LEI, or a CMR key such as ca-cm-kg/TSX/SHOP.' }, version: { type: 'integer', description: 'Prior version number; omitted = current.' } }, required: ['identifier'] } },
  { name: 'list_events_since', title: 'List disclosure events since a date', annotations: { title: 'List disclosure events since a date', ...ANN }, description: 'Return dated, URL\'d disclosure events for an issuer (regulatory announcements, registry filings, releases, bulletins, halts, corporate actions, statement and record dates) since a date.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string' }, since: { type: 'string', description: 'YYYY-MM-DD; omitted = full 12-month window.' }, cursor: { type: 'integer', description: 'Offset returned by the previous page.' }, limit: { type: 'integer', description: 'Page size, default 50, max 200.' } }, required: ['identifier'] } },
  { name: 'list_aliases', title: 'List sourced aliases', annotations: { title: 'List sourced aliases', ...ANN }, description: 'Return the sourced trade and former names an issuer releases under.', inputSchema: { type: 'object', properties: { identifier: { type: 'string' } }, required: ['identifier'] } },
  { name: 'list_nodes', title: 'List market nodes', annotations: { title: 'List market nodes', ...ANN }, description: 'Return the twelve market nodes, which are live, and their record counts.', inputSchema: { type: 'object', properties: {} } },
];
const SUFFIX = { TO: ['TSX'], V: ['TSXV'], CN: ['CSE'], C: ['CSE'], NE: ['CBOE-CANADA'], CB: ['CBOE-CANADA'], L: ['LSE', 'AIM'], LN: ['LSE', 'AIM'], AQ: ['AQSE'], AX: ['ASX'], AU: ['ASX'], NS: ['NSX'], SI: ['SGX', 'SGX-CATALIST'], SG: ['SGX', 'SGX-CATALIST'], SW: ['SIX'], VX: ['SIX'], BX: ['BX'], DE: ['XETRA'], F: ['XETRA'], XE: ['XETRA'], PA: ['XPAR', 'ALXP', 'XMLI'], AS: ['XAMS', 'ALXA'], NA: ['XAMS', 'ALXA'], T: ['TSE-PRIME', 'TSE-STANDARD', 'TSE-GROWTH', 'TSE-PRO', 'TSE-REIT'], JP: ['TSE-PRIME', 'TSE-STANDARD', 'TSE-GROWTH', 'TSE-PRO', 'TSE-REIT'], KS: ['KOSPI'], KQ: ['KOSDAQ'], KN: ['KONEX'], N: ['NYSE'], O: ['NASDAQ'], OQ: ['NASDAQ'], US: ['NYSE', 'NASDAQ', 'CBOE'] };
const PREFIX = { TSX: 'TSX', TSXV: 'TSXV', 'TSX-V': 'TSXV', CVE: 'TSXV', CSE: 'CSE', CNSX: 'CSE', CNQ: 'CSE', NEO: 'CBOE-CANADA', CBOE: 'CBOE-CANADA', 'CBOE-CANADA': 'CBOE-CANADA', LSE: 'LSE', LON: 'LSE', MAIN: 'LSE', AIM: 'AIM', AQSE: 'AQSE', AQUIS: 'AQSE', NEX: 'AQSE', ASX: 'ASX', XASX: 'ASX', NSX: 'NSX', XNEC: 'NSX', SGX: 'SGX', XSES: 'SGX', SES: 'SGX', MAINBOARD: 'SGX', CATALIST: 'SGX-CATALIST', 'SGX-CATALIST': 'SGX-CATALIST', SIX: 'SIX', SWX: 'SIX', XSWX: 'SIX', VTX: 'SIX', BX: 'BX', XBRN: 'BX', XETRA: 'XETRA', XETR: 'XETRA', ETR: 'XETRA', FRA: 'XETRA', FWB: 'XETRA', DE: 'XETRA', EUREX: 'EUREX', XEUR: 'EUREX', XPAR: 'XPAR', EPA: 'XPAR', PAR: 'XPAR', ENXTPA: 'XPAR', EURONEXT: 'XPAR', 'EURONEXT-PARIS': 'XPAR', ALXP: 'ALXP', 'EURONEXT-GROWTH': 'ALXP', XMLI: 'XMLI', 'EURONEXT-ACCESS': 'XMLI', XAMS: 'XAMS', AMS: 'XAMS', AEX: 'XAMS', ENXTAM: 'XAMS', 'EURONEXT-AMSTERDAM': 'XAMS', ALXA: 'ALXA', TSE: ['TSE-PRIME', 'TSE-STANDARD', 'TSE-GROWTH', 'TSE-PRO', 'TSE-REIT'], TYO: ['TSE-PRIME', 'TSE-STANDARD', 'TSE-GROWTH', 'TSE-PRO', 'TSE-REIT'], JPX: ['TSE-PRIME', 'TSE-STANDARD', 'TSE-GROWTH', 'TSE-PRO', 'TSE-REIT'], XJPX: ['TSE-PRIME', 'TSE-STANDARD', 'TSE-GROWTH', 'TSE-PRO', 'TSE-REIT'], 'TSE-PRIME': 'TSE-PRIME', 'TSE-STANDARD': 'TSE-STANDARD', 'TSE-GROWTH': 'TSE-GROWTH', 'TSE-PRO': 'TSE-PRO', 'TSE-REIT': 'TSE-REIT', KRX: ['KOSPI', 'KOSDAQ', 'KONEX'], XKRX: ['KOSPI', 'KOSDAQ', 'KONEX'], KOSPI: 'KOSPI', KOSDAQ: 'KOSDAQ', XKOS: 'KOSDAQ', KONEX: 'KONEX', NYSE: 'NYSE', XNYS: 'NYSE', NASDAQ: 'NASDAQ', XNAS: 'NASDAQ', NAS: 'NASDAQ', BATS: 'CBOE', XCBO: 'CBOE' };
const NODE_COPY = {
  'ca-cm-kg': { country: 'Canada', jurisdiction: 'CA', duty: 'KYP (Know Your Product)', scope: 'TSX, TSXV, CSE, Cboe Canada.', example: 'TSX/SHOP', exchanges: 'TSX, TSXV, CSE, CBOE-CANADA', ids: 'SHOP, TSX:SHOP, SHOP.TO, CSE:AWR, AUMB.V' },
  'uk-cm-kg': { country: 'United Kingdom', jurisdiction: 'GB', duty: 'product governance (FCA PROD sourcebook)', scope: 'LSE Main Market, AIM, Aquis Stock Exchange.', example: 'LSE/SHEL', exchanges: 'LSE, AIM, AQSE', ids: 'SHEL, LSE:SHEL, SHEL.L, AIM:4BB, AQSE:DGQ' },
  'au-cm-kg': { country: 'Australia', jurisdiction: 'AU', duty: 'DDO (Design and Distribution Obligations)', scope: 'ASX, NSX (National Stock Exchange of Australia).', example: 'ASX/BHP', exchanges: 'ASX, NSX', ids: 'BHP, ASX:BHP, BHP.AX, NSX:SBL' },
  'sg-cm-kg': { country: 'Singapore', jurisdiction: 'SG', duty: 'MAS product due diligence', scope: 'SGX Mainboard and Catalist (corporates, REITs, business trusts, depositary receipts).', example: 'SGX/D05', exchanges: 'SGX, SGX-CATALIST', ids: 'D05, SGX:D05, D05.SI, CATALIST:5WH' },
  'ch-cm-kg': { country: 'Switzerland', jurisdiction: 'CH', duty: 'FinSA (Financial Services Act) product duties', scope: 'SIX Swiss Exchange share lines and BX Swiss share lines with a Swiss ISIN.', example: 'SIX/NESN', exchanges: 'SIX, BX', ids: 'NESN, SIX:NESN, NESN.SW, ROG' },
  'de-cm-kg': { country: 'Germany', jurisdiction: 'DE', duty: 'MiFID II product governance (Produktüberwachung)', scope: 'Xetra common shares in the German product groups, plus Eurex derivatives reference data as EUREX records linked to their Xetra underlying.', example: 'XETRA/SAP', exchanges: 'XETRA, EUREX', ids: 'SAP, XETRA:SAP, SAP.DE, EUREX:FDAX' },
  'fr-cm-kg': { country: 'France', jurisdiction: 'FR', duty: 'MiFID II product governance', scope: 'Euronext Paris, Euronext Growth Paris and Euronext Access Paris equity lines (ESMA FIRDS roster); records keyed by ISIN.', example: 'XPAR/FR0000120271', exchanges: 'XPAR, ALXP, XMLI', ids: 'FR0000120271, XPAR:FR0000120271, TotalEnergies SE' },
  'nl-cm-kg': { country: 'Netherlands', jurisdiction: 'NL', duty: 'MiFID II product governance', scope: 'Euronext Amsterdam equity lines (ESMA FIRDS roster); records keyed by ISIN.', example: 'XAMS/NL0000009165', exchanges: 'XAMS, ALXA', ids: 'NL0000009165, AMS:NL0000009165, Heineken N.V.' },
  'jp-cm-kg': { country: 'Japan', jurisdiction: 'JP', duty: 'suitability principle (FIEA Article 40)', scope: 'Tokyo Stock Exchange Prime, Standard, Growth and PRO Market lines and listed REITs / funds; Japanese names as published.', example: 'TSE-PRIME/7203', exchanges: 'TSE-PRIME, TSE-STANDARD, TSE-GROWTH, TSE-PRO, TSE-REIT', ids: '7203, TSE:7203, 7203.T, Toyota Motor Corporation' },
  'kr-cm-kg': { country: 'South Korea', jurisdiction: 'KR', duty: 'suitability and appropriateness (FSCMA Articles 46 and 46-2)', scope: 'KOSPI, KOSDAQ and KONEX companies; Korean names as published.', example: 'KOSPI/005930', exchanges: 'KOSPI, KOSDAQ, KONEX', ids: '005930, KOSPI:005930, 005930.KS, Samsung Electronics' },
  'us-cm-kg': { country: 'United States', jurisdiction: 'US', duty: 'reasonable-basis suitability (FINRA Rule 2111)', scope: 'NYSE, Nasdaq and Cboe-listed EDGAR filers (SEC EDGAR roster and headers).', example: 'NASDAQ/AAPL', exchanges: 'NYSE, NASDAQ, CBOE', ids: 'AAPL, NASDAQ:AAPL, NYSE:IBM, Apple Inc.' },
};
const COPY = NODE_COPY[NODE] || { country: NODE, jurisdiction: '', duty: '', scope: '', example: '', exchanges: '', ids: '' };
// ---- store
let INDEX = null, FACTS = null, NODES = null, BOOTED = 0, BOOT_ERR = '';
const CACHE = new Map(); const CACHE_MAX = 6000;
async function blobJson(name) {
  try { const b = await container.getBlobClient(name).downloadToBuffer(); return JSON.parse(b.toString('utf8')); } catch (e) { if (e.statusCode === 404) return null; throw e; }
}
async function boot(force = false) {
  if (INDEX && !force && Date.now() - BOOTED < 600000) return;
  try { const [i, f, n] = await Promise.all([blobJson('door/index.json'), blobJson('door/facts.json'), blobJson('door/nodes.json')]); if (i) { INDEX = i; FACTS = f || { nodes: {} }; NODES = n || []; BOOTED = Date.now(); BOOT_ERR = ''; } else BOOT_ERR = 'door/index.json not in the regional store'; }
  catch (e) { BOOT_ERR = String(e.message || e); if (!INDEX) { INDEX = { ticker: {}, isin: {}, lei: {}, alias: {}, name: {}, cmr: {}, keys: [] }; FACTS = { nodes: {} }; NODES = []; } }
}
function lookup(kind, value) { const m = INDEX && INDEX[kind]; return (m && m[value]) || []; }
function slug(t) { return String(t).replace(/[^A-Za-z0-9.\-]/g, '_'); }
async function cached(name) {
  if (CACHE.has(name)) { const v = CACHE.get(name); CACHE.delete(name); CACHE.set(name, v); return v; }
  const v = await blobJson(name); if (CACHE.size >= CACHE_MAX) CACHE.delete(CACHE.keys().next().value); CACHE.set(name, v); return v;
}
async function record(key) { const [, ex, t] = key.split('/'); return cached(`door/records/${ex}/${slug(t)}.json`); }
async function eventsOf(key) { const [, ex, t] = key.split('/'); return (await cached(`door/events/${ex}/${slug(t)}.json`)) || []; }
function nodeFacts() { return (FACTS && FACTS.nodes && FACTS.nodes[NODE]) || null; }
function liveNodes() { return (NODES || []).filter(n => n.live).map(n => n.node); }
function summary(r) { const v = f => r.identity[f] ? r.identity[f].value : null; return { cmr: r.cmr, node: r.node, version: r.version, as_of: r.as_of, name: v('name'), ticker: v('ticker'), exchange: v('exchange'), security_type: v('security_type'), isin: v('isin'), lei: v('lei'), sector: v('sector'), event_count: r.event_count, events_url: `https://${PUBLIC_HOST}/events/${r.cmr.split('/').slice(1).join('/')}`, record_url: `https://${PUBLIC_HOST}/record/${r.cmr.split('/').slice(1).join('/')}` }; }
async function resolveKeys(idRaw) {
  const id = (idRaw || '').trim(); if (!id) return { keys: [], kind: 'empty' };
  const up = id.toUpperCase(); const scope = keys => keys.filter(k => k.startsWith(NODE + '/'));
  if (/^[A-Z]{2}-CM-KG\//.test(up)) return { keys: scope(lookup('cmr', up)), kind: 'cmr' };
  if (/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { keys: scope(lookup('isin', up)), kind: 'isin' };
  if (/^[A-Z0-9]{18}[0-9]{2}$/.test(up) && !/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { keys: scope(lookup('lei', up)), kind: 'lei' };
  let exs = null, t = up;
  const pm = up.match(/^([A-Z\-]+):(.+)$/); if (pm && PREFIX[pm[1]]) { exs = [].concat(PREFIX[pm[1]]); t = pm[2]; }
  const sm = t.match(/^(.+)\.([A-Z]{1,2})$/); if (!exs && sm && SUFFIX[sm[2]] && !lookup('ticker', t).length) { exs = SUFFIX[sm[2]]; t = sm[1]; }
  let keys = scope(lookup('ticker', t));
  if (exs) keys = keys.filter(k => exs.includes(k.split('/')[1]));
  else if (keys.length > 1) { const iss = keys.filter(k => k.split('/')[1] !== 'EUREX'); if (iss.length) keys = iss; }
  if (keys.length) return { keys, kind: 'ticker', exchange: exs ? exs.join('/') : null, ticker: t };
  const nk = id.toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
  { const k = scope(lookup('alias', nk)); if (k.length) return { keys: k, kind: 'alias', matched: id }; }
  { const k = scope(lookup('name', nk)); if (k.length) return { keys: k, kind: 'name', matched: id }; }
  return { keys: [], kind: 'ticker', exchange: exs ? exs.join('/') : null, ticker: t };
}
async function callTool(name, args) {
  args = args || {};
  if (name === 'list_nodes') return { door: `${NODE} node door (${REGION})`, live_nodes: liveNodes(), nodes: NODES };
  const res = await resolveKeys(args.identifier);
  if (!res.keys.length) return { error: 'not_found', identifier: args.identifier, kind: res.kind, note: `no record on ${NODE} for this identifier` };
  if (name === 'resolve_issuer') { const recs = await Promise.all(res.keys.map(record)); return { matches: recs.filter(Boolean).map(summary), matched_by: res.kind, ambiguous: res.keys.length > 1, note: res.keys.length > 1 ? 'identifier matches more than one listing; pick by exchange prefix or the CMR key' : (res.kind === 'alias' ? 'matched on a sourced alias' : undefined) }; }
  if (res.keys.length > 1) return { error: 'ambiguous', matches: res.keys, note: 'more than one listing matches; call again with an exchange prefix or the CMR key' };
  const key = res.keys[0];
  if (name === 'get_record') { const r = await record(key); if (!r) return { error: 'not_found', key }; if (args.version && args.version !== r.version) return { error: 'version_unavailable', requested: args.version, current: r.version, note: 'prior versions begin when the second signed-off sweep lands' }; return r; }
  if (name === 'list_aliases') { const r = await record(key); if (!r) return { error: 'not_found', key }; return { cmr: r.cmr, name: r.identity.name.value, aliases: r.aliases, note: r.aliases.length ? undefined : 'no sourced alias on record' }; }
  if (name === 'list_events_since') {
    let evs = await eventsOf(key); if (args.since) evs = evs.filter(e => e.date >= args.since);
    const limit = Math.min(Math.max(parseInt(args.limit || 50, 10), 1), 200); const cursor = Math.max(parseInt(args.cursor || 0, 10), 0);
    return { cmr: key, since: args.since || null, total: evs.length, cursor, limit, next_cursor: cursor + limit < evs.length ? cursor + limit : null, events: evs.slice(cursor, cursor + limit) };
  }
  return { error: 'unknown_tool', name };
}
function rpcResult(id, result) { return { jsonrpc: '2.0', id, result }; }
function rpcError(id, code, message) { return { jsonrpc: '2.0', id: id === undefined ? null : id, error: { code, message } }; }
async function handleRpc(msg) {
  const { id, method, params } = msg || {};
  if (!method) return rpcError(id, -32600, 'Invalid Request');
  if (method === 'initialize') return rpcResult(id, { protocolVersion: (params && params.protocolVersion) || PROTOCOL, capabilities: { tools: { listChanged: false } }, serverInfo: { name: NODE, version: SERVER_VERSION }, instructions: `Capital Markets Knowledge Graph — ${COPY.country} node door, served from ${REGION}. Read-only, public-record only, no auth. Identify issuers by ticker, ISIN or LEI. Every field carries source_url, read_by and state; null values carry the reason. No prices or market data.` });
  if (method.startsWith('notifications/')) return null;
  if (method === 'ping') return rpcResult(id, {});
  if (method === 'tools/list') return rpcResult(id, { tools: TOOLS });
  if (method === 'tools/call') { const name = params && params.name; if (!TOOLS.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`); const out = await callTool(name, (params && params.arguments) || {}); return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(out) }], structuredContent: out, isError: !!(out && out.error && out.error !== 'ambiguous') }); }
  if (method === 'resources/list') return rpcResult(id, { resources: [] });
  if (method === 'prompts/list') return rpcResult(id, { prompts: [] });
  return rpcError(id, -32601, `Method not found: ${method}`);
}
// ---- Agent Card (A2A)
function agentCard() {
  const nf = nodeFacts() || {};
  return { name: `${COPY.country} node — Capital Markets Knowledge Graph`, description: `Read-only door over the ${COPY.country} node of the Capital Markets Knowledge Graph: ${COPY.scope} ${nf.records ? nf.records + ' records, ' + nf.events + ' dated, URL-carrying disclosure events over 12 months.' : ''} Public-record only; no prices, quotes or licensed market data. Records and events are served from ${REGION} and never leave the jurisdiction.`,
    url: `https://${PUBLIC_HOST}/mcp`, provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: SERVER_VERSION, documentationUrl: `https://${PUBLIC_HOST}/llms.txt`, protocolVersion: '0.3.0',
    capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false }, defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'],
    skills: TOOLS.map(t => ({ id: t.name, name: t.title, description: t.description, tags: ['capital-markets', 'public-record', COPY.jurisdiction.toLowerCase(), 'mcp'], examples: t.name === 'list_nodes' ? ['list_nodes'] : [`${t.name} ${COPY.ids.split(',')[0]}`] })),
    'x-cmkg': { node: NODE, jurisdiction: COPY.jurisdiction, country: COPY.country, region: REGION, duty: COPY.duty, exchanges: COPY.exchanges, transport: 'MCP Streamable HTTP (JSON-RPC 2.0, stateless, no auth)', mcp_url: `https://${PUBLIC_HOST}/mcp`, agent_card_url: `https://${AGENT_HOST}/.well-known/agent-card.json`, registry: 'io.github.allooloo/cm-kg', contact: CONTACT, as_of: nf.as_of || null, records: nf.records || null, events: nf.events || null, source: 'public-record', store: `Azure Storage, ${REGION} (regional pond; blob per record and per issuer event list)` } };
}
function human(host) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capital Markets Knowledge Graph — ${COPY.country} node door</title><link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><meta name="theme-color" content="#14213D"><style>body{font-family:system-ui,sans-serif;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.5}code{background:#f3f4f6;padding:.1em .3em}h1{font-size:1.4rem}</style></head><body><h1>Capital Markets Knowledge Graph — ${COPY.country} node door</h1>
<p>A read-only MCP door over the ${COPY.country} node. Scope: ${COPY.scope} Served from ${REGION}: records and events live in their own jurisdiction. Public-record only: no prices, no quotes, no licensed market data. No authentication.</p>
<p>MCP endpoint (Streamable HTTP): <code>https://${host}/mcp</code><br>Agent Card: <a href="https://${AGENT_HOST}/.well-known/agent-card.json">https://${AGENT_HOST}/.well-known/agent-card.json</a><br>Facts: <a href="/facts.json">/facts.json</a> · <a href="/llms.txt">/llms.txt</a> · record: <code>/record/${COPY.example}</code> · events: <code>/events/${COPY.example}?since=2026-06-01</code></p>
<p>Tools: resolve_issuer · get_record · list_events_since · list_aliases · list_nodes. Identifiers: ${COPY.ids}, an ISIN or an LEI. Every field carries its source, its reader and a state (sourced · filled · confirmed · conflict). Records are versioned and never deleted.</p>
<p>Duty served: ${COPY.duty}. Operator: Allooloo Technologies Corp., Vancouver, Canada.</p></body></html>`;
}
function llms(host) {
  const nf = nodeFacts();
  return `# Capital Markets Knowledge Graph — ${COPY.country} node door (${REGION})
Operator: Allooloo Technologies Corp. Read-only MCP server, Streamable HTTP at https://${host}/mcp, JSON-RPC 2.0, no authentication. Public-record only: no prices, quotes or licensed market data. Data plane regional: this node's records and events are served from ${REGION} and never from another store.
Scope: ${COPY.scope} ${nf ? nf.records + ' records, ' + nf.events + ' dated, URL-carrying disclosure events over 12 months.' : ''}
Tools: resolve_issuer (ticker, ISIN or LEI -> record summary), get_record (full Capital Markets Record with per-field source_url, read_by and state), list_events_since (paged events since a date), list_aliases (sourced trade and former names), list_nodes (the twelve market nodes, which are live, record counts).
Identifiers: ${COPY.ids}, ISIN, LEI. An ambiguous ticker returns every match; the door never guesses.
A2A Agent Card: https://${AGENT_HOST}/.well-known/agent-card.json (also /.well-known/agent-card.json on this host).
GET paths: /, /facts.json, /llms.txt, /nodes.json, /record/<EXCHANGE>/<CODE>, /events/<EXCHANGE>/<CODE>?since=YYYY-MM-DD&cursor=0&limit=50. Exchanges: ${COPY.exchanges}.
`;
}
function hdrs(asOf, ver, extra = {}) { return { 'X-CMR-Node': NODE, 'X-CMR-Region': REGION, 'X-CMR-As-Of': asOf || '', 'X-CMR-Version': String(ver || ''), 'X-CMR-Source': 'public-record', 'X-CMR-Contact': 'CEO mk@allooloo.ai', 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-CMR-Operator': OPERATOR, 'X-CMR-Registry': 'io.github.allooloo/cm-kg', 'Strict-Transport-Security': 'max-age=31536000', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization', 'Access-Control-Expose-Headers': 'X-CMR-Node, X-CMR-Region, X-CMR-As-Of, X-CMR-Version, X-CMR-Source, X-CMR-Operator, Mcp-Session-Id', ...extra }; }
function send(res, status, body, type, asOf, ver, cache) { const h = hdrs(asOf, ver, { 'content-type': type, 'cache-control': cache || 'no-store' }); res.writeHead(status, h); res.end(body); }
function sendJson(res, obj, status, asOf, ver, cache) { send(res, status, JSON.stringify(obj), 'application/json; charset=utf-8', asOf, ver, cache); }
const CSP = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; base-uri 'none'; form-action https://formspree.io; frame-ancestors 'none'; upgrade-insecure-requests";
const ROBOTS = host => `User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: Claude-User\nAllow: /\n\nUser-agent: Claude-SearchBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: Perplexity-User\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\nUser-agent: Bingbot\nAllow: /\n\nUser-agent: Applebot\nAllow: /\n\nUser-agent: Applebot-Extended\nAllow: /\n\nUser-agent: Amazonbot\nAllow: /\n\nUser-agent: CCBot\nAllow: /\n\nUser-agent: DuckAssistBot\nAllow: /\n\nUser-agent: meta-externalagent\nAllow: /\n\nUser-agent: Bytespider\nAllow: /\n\nUser-agent: cohere-ai\nAllow: /\n\nUser-agent: Diffbot\nAllow: /\n\nUser-agent: YouBot\nAllow: /\n\nUser-agent: MistralAI-User\nAllow: /\n\nUser-agent: xAI-Grok\nAllow: /\n\nSitemap: https://${host}/sitemap.xml\n`;
const SECURITY = host => `Contact: mailto:developers@allooloo.ai\nContact: https://allooloo.io\nExpires: 2027-09-12T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: https://allooloo.io\n`;
const KIT_PATHS = ['/', '/llms.txt', '/facts.json', '/nodes.json', '/robots.txt', '/sitemap.xml', '/mcp.json', '/openapi.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
function sitemap(host) { return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${KIT_PATHS.filter(x => x !== '/robots.txt').map(x => `<url><loc>https://${host}${x === '/' ? '/' : x}</loc></url>`).join('')}</urlset>\n`; }
function mcpJson(host, nf) { return { name: `cm-kg ${NODE}`, description: `Capital Markets Knowledge Graph — ${NODE} regional door (${REGION}); read-only, public-record only; answers scoped to this node`, version: (nf && nf.version) ? String(nf.version) : '1', transport: 'streamable-http', url: `https://${host}/mcp`, authentication: 'none', tools: TOOLS.map(t => ({ name: t.name, description: t.description })), agent_card: `https://${AGENT_HOST}/.well-known/agent-card.json`, openapi: `https://${host}/openapi.json`, llms: `https://${host}/llms.txt`, facts: `https://${host}/facts.json`, operator: 'Allooloo Technologies Corp.', contact: 'developers@allooloo.ai', registry: 'io.github.allooloo/cm-kg', records: nf ? nf.records : null, events: nf ? nf.events : null, as_of: nf ? nf.as_of : null }; }
function openapi(host, nf) {
  const params = [{ name: 'exchange', in: 'path', required: true, schema: { type: 'string' } }, { name: 'code', in: 'path', required: true, schema: { type: 'string' } }];
  return { openapi: '3.1.0', info: { title: `cm-kg ${NODE} door`, version: (nf && nf.version) ? String(nf.version) : '1', description: `Regional door of the Capital Markets Knowledge Graph for ${NODE}: MCP over Streamable HTTP at /mcp plus read-only HTTP paths. Public-record only; every field carries its source URL, reader and state.`, contact: { name: 'Allooloo Technologies Corp.', email: 'developers@allooloo.ai', url: 'https://allooloo.io' } }, servers: [{ url: `https://${host}` }],
    paths: { '/mcp': { post: { summary: 'MCP JSON-RPC (tools/list, tools/call)', requestBody: { required: true, content: { 'application/json': { schema: { type: 'object' } } } }, responses: { 200: { description: 'JSON-RPC response' } } } },
      '/record/{exchange}/{code}': { get: { summary: 'Capital Markets Record for one issuer', parameters: params, responses: { 200: { description: 'record' }, 404: { description: 'not on this node' } } } },
      '/events/{exchange}/{code}': { get: { summary: 'Dated disclosure events for one issuer', parameters: [...params, { name: 'since', in: 'query', schema: { type: 'string', format: 'date' } }, { name: 'cursor', in: 'query', schema: { type: 'integer' } }, { name: 'limit', in: 'query', schema: { type: 'integer' } }], responses: { 200: { description: 'events page' } } } },
      '/facts.json': { get: { summary: 'Node facts (live counts)', responses: { 200: { description: 'facts' } } } }, '/nodes.json': { get: { summary: 'The twelve nodes', responses: { 200: { description: 'nodes' } } } }, '/llms.txt': { get: { summary: 'Machine instructions', responses: { 200: { description: 'text' } } } }, '/.well-known/agent-card.json': { get: { summary: 'A2A Agent Card', responses: { 200: { description: 'card' } } } }, '/healthz': { get: { summary: 'Health', responses: { 200: { description: 'ok' }, 503: { description: 'store not loaded' } } } } } };
}
const STATIC = path.join(process.cwd(), 'static'); const MIME = { '.ico': 'image/x-icon', '.svg': 'image/svg+xml', '.png': 'image/png', '.webmanifest': 'application/manifest+json' };
const server = http.createServer(async (req, res) => {
  try {
    await boot();
    const host = (req.headers['x-forwarded-host'] || req.headers.host || PUBLIC_HOST).split(',')[0].trim().split(':')[0]; const url = new URL(req.url, `https://${host}`); const p = url.pathname.replace(/\/+$/, '') || '/';
    const nf = nodeFacts(); const asOf = nf ? nf.as_of : (FACTS ? FACTS.as_of : ''); const ver = nf ? nf.version : 1;
    if (req.method === 'OPTIONS') { res.writeHead(204, hdrs(asOf, ver)); return res.end(); }
    if (p === '/healthz') return sendJson(res, { ok: !!(INDEX && INDEX.keys && INDEX.keys.length), node: NODE, region: REGION, keys: INDEX ? (INDEX.keys || []).length : 0, boot_error: BOOT_ERR || undefined, booted: new Date(BOOTED).toISOString() }, INDEX && INDEX.keys && INDEX.keys.length ? 200 : 503, asOf, ver);
    if (p === '/mcp') {
      if (req.method === 'GET') return send(res, 405, 'Method Not Allowed: this door serves stateless Streamable HTTP; POST JSON-RPC to /mcp', 'text/plain', asOf, ver);
      if (req.method === 'DELETE') { res.writeHead(204, hdrs(asOf, ver)); return res.end(); }
      if (req.method !== 'POST') return send(res, 405, 'Method Not Allowed', 'text/plain', asOf, ver);
      let raw = ''; for await (const chunk of req) { raw += chunk; if (raw.length > 1e6) break; }
      let body; try { body = JSON.parse(raw); } catch (e) { return sendJson(res, rpcError(null, -32700, 'Parse error'), 400, asOf, ver); }
      const batch = Array.isArray(body); const outs = []; for (const m of (batch ? body : [body])) { const r = await handleRpc(m); if (r) outs.push(r); }
      if (!outs.length) { res.writeHead(202, hdrs(asOf, ver)); return res.end(); }
      return sendJson(res, batch ? outs : outs[0], 200, asOf, ver, 'no-store');
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') return send(res, 405, 'Method Not Allowed', 'text/plain', asOf, ver);
    const isAgentHost = host.startsWith('agent.');
    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json' || (isAgentHost && p === '/')) return sendJson(res, agentCard(), 200, asOf, ver, 'public, max-age=300');
    if (p === '/') return send(res, 200, human(host), 'text/html; charset=utf-8', asOf, ver, 'public, max-age=300');
    if (p === '/llms.txt') return send(res, 200, llms(host), 'text/plain; charset=utf-8', asOf, ver, 'public, max-age=3600');
    if (p === '/facts.json') return sendJson(res, { door: host, scope: NODE, region: REGION, ...(FACTS || {}), node: NODE, ...(nf || {}), live_nodes: liveNodes(), mcp_url: `https://${PUBLIC_HOST}/mcp`, agent_card_url: `https://${AGENT_HOST}/.well-known/agent-card.json` }, 200, asOf, ver, 'public, max-age=300');
    if (p === '/nodes.json') return sendJson(res, NODES, 200, asOf, ver, 'public, max-age=3600');
    if (p === '/robots.txt') return send(res, 200, ROBOTS(host), 'text/plain; charset=utf-8', asOf, ver, 'public, max-age=86400');
    if (p === '/.well-known/security.txt') return send(res, 200, SECURITY(host), 'text/plain; charset=utf-8', asOf, ver, 'public, max-age=86400');
    if (p === '/sitemap.xml') return send(res, 200, sitemap(host), 'application/xml; charset=utf-8', asOf, ver, 'public, max-age=3600');
    if (p === '/mcp.json') return sendJson(res, mcpJson(host, nf), 200, asOf, ver, 'public, max-age=300');
    if (p === '/openapi.json') return sendJson(res, openapi(host, nf), 200, asOf, ver, 'public, max-age=3600');
    const ext = path.extname(p); if (MIME[ext] && !p.includes('..')) { const f = path.join(STATIC, path.basename(p)); if (fs.existsSync(f)) return send(res, 200, fs.readFileSync(f), MIME[ext], asOf, ver, 'public, max-age=86400'); }
    let m = p.match(/^\/(record|events)\/([a-z]{2}-cm-kg)\/([A-Z\-]+)\/(.+)$/i) || p.match(/^\/(record|events)\/([A-Z\-]+)\/(.+)$/i);
    if (m) {
      const kind = m[1].toLowerCase(); const key = m.length === 5 ? `${m[2].toLowerCase()}/${m[3].toUpperCase()}/${decodeURIComponent(m[4])}` : `${NODE}/${m[2].toUpperCase()}/${decodeURIComponent(m[3])}`;
      if (!key.startsWith(NODE + '/')) return sendJson(res, { error: 'not_this_node', key, note: `this door serves ${NODE} only; ask the apex or the owning node` }, 404, asOf, ver);
      if (kind === 'record') { const r = await record(key); return r ? sendJson(res, r, 200, asOf, ver, 'public, max-age=3600') : sendJson(res, { error: 'not_found', key }, 404, asOf, ver); }
      const out = await callTool('list_events_since', { identifier: key, since: url.searchParams.get('since') || undefined, cursor: url.searchParams.get('cursor') || 0, limit: url.searchParams.get('limit') || 50 });
      return sendJson(res, out, out.error ? 404 : 200, asOf, ver, 'public, max-age=3600');
    }
    return sendJson(res, { error: 'not_found', doors: ['/', '/mcp', '/facts.json', '/llms.txt', '/nodes.json', '/.well-known/agent-card.json', '/record/<EXCHANGE>/<CODE>', '/events/…'] }, 404, asOf, ver);
  } catch (e) { console.error(e); sendJson(res, { error: 'internal', note: String(e.message || e) }, 500, '', ''); }
});
server.listen(PORT, () => { console.log(`cmkg door ${NODE} (${REGION}) on :${PORT}`); boot(true).then(() => console.log('index keys', INDEX ? (INDEX.keys || []).length : 0, BOOT_ERR || '')); });
