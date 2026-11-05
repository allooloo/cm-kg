// test_apex_local.mjs — ASOF-01: the apex router in Node (static index and roster from DOOR\apex\static), the getasof host profile: initialize, tools/list,
// a routed get_as_of (to the live us gate, read only), unknown_issuer at the router, the card, llms.txt and mcp.json; getissuer's own list unchanged.
import { readFile } from 'node:fs/promises';
const realFetch = globalThis.fetch;
const A = (await import('file:///C:/ALLOOLOO/CM-KG/DOOR/apex/index.js')).default;
const ST = 'C:/ALLOOLOO/CM-KG/DOOR/apex/static'; const kv = new Map();
const env = { ASSETS: { fetch: async r => { const p = new URL(r.url).pathname; try { return new Response(await readFile(ST + p)); } catch { return new Response('nf', { status: 404 }); } } }, X402: { get: async k => kv.get(k) ?? null, put: async (k, v) => kv.set(k, v), list: async () => ({ keys: [] }) } };
let routedUA = null;
globalThis.fetch = async (u, init = {}) => { const url = typeof u === 'string' ? u : u.url; if (/^https:\/\/mcp\.us-cm-kg\.ai\/mcp/.test(url)) { routedUA = (init.headers || {})['user-agent']; return realFetch(url, init); } throw new Error('unexpected fetch ' + url); };
const rpc = async (host, m) => { const r = await A.fetch(new Request(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': 'asof01-local' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, ...m }) }), env, { waitUntil() {} }); return r.json(); };
const get = async (host, p) => { const r = await A.fetch(new Request(`https://${host}${p}`, { headers: { 'user-agent': 'asof01-local' } }), env, { waitUntil() {} }); return r.text(); };
const R = []; const ok = (n, c, d) => { R.push(!!c); console.log(`${c ? 'PASS' : 'FAIL'} ${n}${d ? ' · ' + d : ''}`); };
const ini = await rpc('mcp.getasof.ai', { method: 'initialize', params: {} }); ok('initialize names getasof', ini.result.serverInfo.name === 'getasof' && /get_as_of is the issuer record/.test(ini.result.instructions));
const tl = await rpc('mcp.getasof.ai', { method: 'tools/list' }); ok('tools/list', tl.result.tools.map(t => t.name).join(',') === 'get_as_of,resolve_issuer,list_events_since,list_nodes', tl.result.tools.map(t => t.name).join(','));
const c1 = await rpc('mcp.getasof.ai', { method: 'tools/call', params: { name: 'get_as_of', arguments: { issuer: 'NASDAQ:MSFT', as_of: '2023-03-15' } } }); const o = c1.result.structuredContent;
ok('routed to the us node, answer unchanged', routedUA === 'getissuer apex (get_as_of route)' && o.cmr === 'us-cm-kg/NASDAQ/MSFT' && o.signature && o.receipt && o.receipt.id, `${o.cmr} · receipt ${o.receipt && o.receipt.id}`);
const c2 = await rpc('mcp.getasof.ai', { method: 'tools/call', params: { name: 'get_as_of', arguments: { issuer: 'ZZZZNOPE9', as_of: '2023-03-15' } } }); ok('unknown_issuer at the router', c2.result.structuredContent.error === 'unknown_issuer');
const card = JSON.parse(await get('agent.getasof.ai', '/.well-known/agent-card.json')); ok('card', card.name === 'getasof' && card.skills[0].id === 'get_as_of' && card['x-allooloo'].products[3].startsWith('As Of'));
const ll = await get('mcp.getasof.ai', '/llms.txt'); ok('llms.txt product order', /Target Market https:\/\/gettargetmarket\.ai\/ · As Of https:\/\/getasof\.ai\/ · Issuerwire/.test(ll));
const mj = JSON.parse(await get('mcp.getasof.ai', '/mcp.json')); ok('mcp.json', mj.name === 'getasof' && mj.errors.length === 4 && /to be set/.test(mj.price.rate));
const gi = await rpc('mcp.getissuer.ai', { method: 'tools/list' }); ok('getissuer tools unchanged', !gi.result.tools.some(t => t.name === 'get_as_of'), gi.result.tools.map(t => t.name).join(','));
console.log(R.every(Boolean) ? 'ASOF-01 APEX LOCAL PASS' : 'ASOF-01 APEX LOCAL FAIL'); process.exit(R.every(Boolean) ? 0 : 1);
