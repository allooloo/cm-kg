// test_gate_local.mjs — DOORS-01: the gate's get_filings · get_ticker · get_auditor in Node before the deploy, against the live us and de doors (read only); the
// receipt door and KV in memory; a throwaway record key. Usage: node SITE\DOORS-01\test_gate_local.mjs
import { webcrypto } from 'node:crypto';
const realFetch = globalThis.fetch;
const kp = await webcrypto.subtle.generateKey({ name: 'Ed25519' }, true, ['sign', 'verify']); const jwk = await webcrypto.subtle.exportKey('jwk', kp.privateKey);
const receipts = []; const kv = new Map(); let seq = 0;
globalThis.fetch = async (u, init = {}) => {
  const url = typeof u === 'string' ? u : u.url;
  if (url === 'https://mcp.rco-records.ai/mcp') { const b = JSON.parse(init.body); receipts.push({ args: b.params.arguments, writer: (init.headers || {})['x-rco-writer'] }); return new Response(JSON.stringify({ jsonrpc: '2.0', id: 1, result: { structuredContent: { receipt: { id: 'dec_test' + (++seq), seq } } } }), { headers: { 'content-type': 'application/json' } }); }
  if (/^https:\/\/mcp\.(us|de)-cm-kg\.ai\/mcp$/.test(url)) { if (typeof u !== 'string') { const b = await u.text(); return realFetch(url, { method: u.method, headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'Allooloo doors-01 local test' }, body: b }); } return realFetch(url, { ...init, headers: { ...(init.headers || {}), 'user-agent': 'Allooloo doors-01 local test' } }); }
  throw new Error('unexpected fetch ' + url);
};
const gate = (await import('file:///C:/ALLOOLOO/CM-KG/NODE-GATE/worker/index.js')).default;
const env = { CMR_SIGNING_JWK: JSON.stringify(jwk), RCO_DOOR_TOKEN: 'test', SIGN_NODES: 'all', X402: { get: async k => kv.get(k) || null, put: async (k, v) => { kv.set(k, v); } } };
const waits = []; const ctx = { waitUntil: p => waits.push(p) };
const call = async (host, name, args) => { const r = await gate.fetch(new Request(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': 'local-test-agent' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }) }), env, ctx); return (await r.json()).result.structuredContent; };
let fails = 0; const ok = (n, c, d) => { console.log(`${c ? 'PASS' : 'FAIL'} ${n}${d ? ' · ' + d : ''}`); if (!c) fails++; };
let o = await call('mcp.us-cm-kg.ai', 'get_filings', { issuer: 'NASDAQ:AAPL', from: '2026-01-01', to: '2026-06-30' });
ok('get_filings AAPL H1 2026', !o.error && o.count > 0 && o.filings.every(f => f.date >= '2026-01-01' && f.date <= '2026-06-30' && f.type && f.source), `${o.count} filings · first ${o.filings && o.filings[0] && o.filings[0].type}`);
ok('signed + receipted', o.signature && o.signature.kid === 'allooloo-cmr-2026-10' && o.receipt && o.receipt.id && receipts.at(-1).writer === 'us-cm-kg');
o = await call('mcp.us-cm-kg.ai', 'get_ticker', { identifier: 'AAPL', exchange: 'NASDAQ' });
ok('get_ticker AAPL', o.isin && o.isin.value === 'US0378331005' && o.lei && o.lei.value && o.listing.exchange.value === 'NASDAQ' && o.status && o.status.value, `${o.isin && o.isin.value} · ${o.lei && o.lei.value} · ${o.status && o.status.value}`);
o = await call('mcp.us-cm-kg.ai', 'get_ticker', { identifier: 'US0378331005' }); ok('get_ticker by ISIN', o.cmr === 'us-cm-kg/NASDAQ/AAPL');
o = await call('mcp.us-cm-kg.ai', 'get_auditor', { issuer: 'NASDAQ:AAPL' });
ok('get_auditor AAPL', o.auditor && o.auditor.value && o.auditor.source && (Array.isArray(o.changes) || o.changes.state === 'not_on_record'), `${o.auditor && o.auditor.value} · changes ${Array.isArray(o.changes) ? o.changes.length : o.changes.state}`);
o = await call('mcp.de-cm-kg.ai', 'get_auditor', { issuer: 'SAP.DE' });
ok('get_auditor SAP (de): not_on_record with the record reason', o.auditor && o.auditor.state === 'not_on_record' && o.auditor.market === 'DE', `${JSON.stringify(o.auditor).slice(0, 120)}`);
o = await call('mcp.us-cm-kg.ai', 'get_filings', { issuer: 'NASDAQ:AAPL', from: '2026-13-01' }); ok('invalid range → invalid_request', o.error === 'invalid_request');
o = await call('mcp.us-cm-kg.ai', 'get_ticker', { identifier: 'ZZZZNOPE9' }); ok('unknown_issuer, no receipt', o.error === 'unknown_issuer' && !o.receipt);
const tl = await gate.fetch(new Request('https://mcp.us-cm-kg.ai/mcp', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 9, method: 'tools/list' }) }), env, ctx);
const names = (await tl.json()).result.tools.map(t => t.name); ok('tools/list carries the three', ['get_filings', 'get_ticker', 'get_auditor', 'get_as_of'].every(n => names.includes(n)));
await Promise.all(waits); ok('counters', Number(kv.get('tot:get_filings_receipts')) >= 1 && Number(kv.get('tot:get_auditor_receipts')) >= 1);
console.log(fails ? `DOORS-01 gate local: ${fails} FAIL` : 'DOORS-01 gate local: PASS'); process.exit(fails ? 1 : 0);
