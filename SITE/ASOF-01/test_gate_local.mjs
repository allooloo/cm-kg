// test_gate_local.mjs — ASOF-01: the node gate's get_as_of in Node before the deploy. The node door's reads go to the live us door (real sealed vintage,
// read only); the receipt door and the KV are in memory; the node's record key is a throwaway made here (never the published key). No write leaves the laptop.
// Usage: node SITE\ASOF-01\test_gate_local.mjs   (exit 0 = every case as expected)
import { webcrypto } from 'node:crypto';
const realFetch = globalThis.fetch;
const kp = await webcrypto.subtle.generateKey({ name: 'Ed25519' }, true, ['sign', 'verify']); const jwk = await webcrypto.subtle.exportKey('jwk', kp.privateKey);
const receipts = []; const kv = new Map(); let seq = 76000;
globalThis.fetch = async (u, init = {}) => {
  const url = typeof u === 'string' ? u : u.url;
  if (url === 'https://mcp.rco-records.ai/mcp') { const b = JSON.parse(init.body); receipts.push({ args: b.params.arguments, writer: (init.headers || {})['x-rco-writer'] }); const id = 'dec_' + String(++seq).padStart(24, '0');
    return new Response(JSON.stringify({ jsonrpc: '2.0', id: 1, result: { structuredContent: { receipt: { id, seq, hash: 'sha256:test' } } } }), { headers: { 'content-type': 'application/json' } }); }
  if (url === 'https://mcp.us-cm-kg.ai/mcp' && typeof u !== 'string') { const b = await u.text(); return realFetch(url, { method: u.method, headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'Allooloo asof-01 local test' }, body: b }); }
  if (url === 'https://mcp.us-cm-kg.ai/mcp') return realFetch(url, { ...init, headers: { ...(init.headers || {}), 'user-agent': 'Allooloo asof-01 local test' } });   // the live door: its get_record/resolve pass the live gate unchanged
  throw new Error('unexpected fetch ' + url);
};
const gate = (await import('file:///C:/ALLOOLOO/CM-KG/NODE-GATE/worker/index.js')).default;
const env = { CMR_SIGNING_JWK: JSON.stringify(jwk), RCO_DOOR_TOKEN: 'test', SIGN_NODES: 'all', X402: { get: async k => kv.get(k) || null, put: async (k, v) => { kv.set(k, v); } } };
const waits = []; const ctx = { waitUntil: p => waits.push(p) };
const call = async (args, id = 1) => { const r = await gate.fetch(new Request('https://mcp.us-cm-kg.ai/mcp', { method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': 'local-test-agent' }, body: JSON.stringify({ jsonrpc: '2.0', id, method: 'tools/call', params: { name: 'get_as_of', arguments: args } }) }), env, ctx); return { h: r.headers, j: await r.json() }; };
let fails = 0; const check = (name, ok, detail) => { console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ' · ' + detail : ''}`); if (!ok) fails++; };
const verify = async o => { const { signature: s, ...rest } = o; const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
  const { receipt, ...unsigned } = rest; const msg = s.protected + '.' + Buffer.from(JSON.stringify(sortDeep(unsigned))).toString('base64url');
  return webcrypto.subtle.verify('Ed25519', kp.publicKey, Buffer.from(s.signature, 'base64url'), new TextEncoder().encode(msg)); };
// 1 a sealed read
let r = await call({ issuer: 'AAPL', as_of: '2024-06-28' }); let o = r.j.result.structuredContent;
check('sealed read AAPL 2024-06-28', !o.error && o.cmr === 'us-cm-kg/NASDAQ/AAPL' && o.version && o.version.vintage.year === 2024 && o.events_count > 0, `events ${o.events_count} · fields held ${o.fields_held} · version ${o.version && o.version.id}`);
check('every line dated on or before as_of', (o.events || []).every(e => (e.date || '') <= '2024-06-28'));
check('node signature verifies (kid allooloo-cmr-2026-10)', o.signature && o.signature.kid === 'allooloo-cmr-2026-10' && await verify(o));
check('receipt id in the answer and the header', o.receipt && o.receipt.id && r.h.get('X-RCO-Receipt-Id') === o.receipt.id, o.receipt && o.receipt.id);
const rc = receipts[receipts.length - 1]; check('receipt: writer = the node, subject the CMR, answer hash', rc.writer === 'us-cm-kg' && rc.args.subject === 'us-cm-kg/NASDAQ/AAPL' && /^sha256:/.test(rc.args.answer_hash) && /get_as_of/.test(rc.args.rule_version), rc.args.rule_version);
// 2 before the vintage
r = await call({ issuer: 'AAPL', as_of: '2020-06-30' }); o = r.j.result.structuredContent;
check('2020: not_sealed, names the earliest sealed date', o.error === 'not_sealed' && o.earliest_sealed_date === '2021-01-04', `${o.error} · earliest ${o.earliest_sealed_date}`);
// 3 after the current seal
r = await call({ issuer: 'AAPL', as_of: '2026-11-04' }); o = r.j.result.structuredContent;
check('2026-11-04: not_sealed past the seal run, sealed_through named', o.error === 'not_sealed' && !!o.sealed_through, `${o.error} · sealed_through ${o.sealed_through}`);
// 4 unknown issuer, invalid date, ambiguous
r = await call({ issuer: 'ZZZZNOTANISSUER', as_of: '2024-06-28' }); o = r.j.result.structuredContent; check('unknown_issuer, no receipt', o.error === 'unknown_issuer' && !o.receipt && r.j.result.isError === true);
r = await call({ issuer: 'AAPL', as_of: '2024-02-30' }); o = r.j.result.structuredContent; check('invalid date → invalid_request', o.error === 'invalid_request');
// 5 tools/list carries get_as_of
const tl = await gate.fetch(new Request('https://mcp.us-cm-kg.ai/mcp', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 9, method: 'tools/list' }) }), env, ctx).catch(e => null);
check('tools/list names get_as_of', tl ? (await tl.json()).result.tools.some(t => t.name === 'get_as_of') : false);
await Promise.all(waits); check('receipts counter bumped', Number(kv.get('tot:asof_receipts') || 0) >= 1, `tot:asof_receipts ${kv.get('tot:asof_receipts')}`);
console.log(fails ? `ASOF-01 gate local: ${fails} FAIL` : 'ASOF-01 gate local: PASS'); process.exit(fails ? 1 : 0);
