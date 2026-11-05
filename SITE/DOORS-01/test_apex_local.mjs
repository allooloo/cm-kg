// test_apex_local.mjs — DOORS-01: the apex router in Node, the three door hosts: tools, a routed call each (to the live us gate, read only), the card's doors
// order, llms.txt first line; getasof's llms carries the doors line; getissuer unchanged.
import { readFile } from 'node:fs/promises';
const realFetch = globalThis.fetch;
const A = (await import('file:///C:/ALLOOLOO/CM-KG/DOOR/apex/index.js')).default;
const ST = 'C:/ALLOOLOO/CM-KG/DOOR/apex/static'; const kv = new Map();
const env = { ASSETS: { fetch: async r => { const p = new URL(r.url).pathname; try { return new Response(await readFile(ST + p)); } catch { return new Response('nf', { status: 404 }); } } }, X402: { get: async k => kv.get(k) ?? null, put: async (k, v) => kv.set(k, v), list: async () => ({ keys: [] }) } };
globalThis.fetch = async (u, init = {}) => { const url = typeof u === 'string' ? u : u.url; if (/^https:\/\/mcp\.us-cm-kg\.ai\/mcp/.test(url)) return realFetch(url, init); throw new Error('unexpected fetch ' + url); };
const rpc = async (host, m) => (await A.fetch(new Request(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': 'doors01-local' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, ...m }) }), env, { waitUntil() {} })).json();
const get = async (host, p) => (await A.fetch(new Request(`https://${host}${p}`, { headers: { 'user-agent': 'doors01-local' } }), env, { waitUntil() {} })).text();
const R = []; const ok = (n, c, d) => { R.push(!!c); console.log(`${c ? 'PASS' : 'FAIL'} ${n}${d ? ' · ' + d : ''}`); };
const ORDER = 'get_issuer,get_orderability,get_target_market,get_as_of,get_filings,get_ticker,get_auditor';
for (const [h, t, args, check] of [['mcp.getfilings.ai', 'get_filings', { issuer: 'NASDAQ:AAPL', from: '2026-01-01', to: '2026-03-31' }, o => o.count > 0], ['mcp.getticker.ai', 'get_ticker', { identifier: 'AAPL', exchange: 'NASDAQ' }, o => o.isin && o.isin.value === 'US0378331005'], ['mcp.getauditor.ai', 'get_auditor', { issuer: 'NASDAQ:AAPL' }, o => o.auditor && o.auditor.value]]) {
  const tl = await rpc(h, { method: 'tools/list' }); ok(`${h} tools`, tl.result.tools.map(x => x.name).join(',') === `${t},resolve_issuer,list_nodes`, tl.result.tools.map(x => x.name).join(','));
  const c = (await rpc(h, { method: 'tools/call', params: { name: t, arguments: args } })).result.structuredContent; ok(`${h} routed ${t}`, check(c) && c.signature && c.receipt && c.receipt.id, c.receipt && c.receipt.id);
  const card = JSON.parse(await get(h.replace('mcp.', 'agent.'), '/.well-known/agent-card.json')); ok(`${h} card doors order`, card['x-allooloo'].doors.map(x => x.split(' ')[0]).join(',') === ORDER);
  const ll = await get(h, '/llms.txt'); ok(`${h} llms first line`, ll.startsWith(`# ${t} — `) && ll.includes('Doors: get_issuer'), ll.split('\n')[0]);
}
ok('getasof llms has the doors line', (await get('mcp.getasof.ai', '/llms.txt')).includes('Doors: get_issuer https://getissuer.ai/ · get_orderability'));
const gi = await rpc('mcp.getissuer.ai', { method: 'tools/list' }); ok('getissuer unchanged', !gi.result.tools.some(x => ['get_filings', 'get_ticker', 'get_auditor'].includes(x.name)));
console.log(R.every(Boolean) ? 'DOORS-01 APEX LOCAL PASS' : 'DOORS-01 APEX LOCAL FAIL'); process.exit(R.every(Boolean) ? 0 : 1);
