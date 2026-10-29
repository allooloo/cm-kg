// verify_doors02.mjs — DOORS-02 (2026-10-26): the signing check across every door on the roster of record (apex list_nodes).
// Per door, three reads, each verified against the published keyring (https://allooloo.ai/.well-known/jwks.json, kid named in the signature):
//   1. MCP tools/call get_record with the roster example (ISIN first, as COMPS-01 wire-check called it) — record signed?
//   2. GET <record_url> from the roster example — record signed?
//   3. the same tools/call asking for the offer (x402-pay: 1) — HTTP 402, $0.01, body signed?
// Writes verify-doors02-<date>.json beside and prints the table. Usage: node verify_doors02.mjs [label]
import { webcrypto as C } from 'node:crypto'; import fs from 'node:fs';
const JWKS_URL = 'https://allooloo.ai/.well-known/jwks.json';
const UA = { 'user-agent': 'allooloo-doors02-check/1.0' };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
const b64u = b => Buffer.from(b).toString('base64url'), unb = s => Buffer.from(s, 'base64url');
const ring = await (await fetch(JWKS_URL, { headers: UA })).json();
async function verify(o) {
  const s = o && o.signature; if (!s || !s.kid) return { signed: false, verified: false, kid: null };
  const jwk = ring.keys.find(k => k.kid === s.kid); if (!jwk) return { signed: true, verified: false, kid: s.kid, why: 'kid not in published JWKS' };
  if (s.jwks !== JWKS_URL) return { signed: true, verified: false, kid: s.kid, why: 'names another keyring ' + s.jwks };
  const body = { ...o }; delete body.signature;
  const key = await C.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: jwk.x }, { name: 'Ed25519' }, false, ['verify']);
  const ph = JSON.parse(unb(s.protected).toString()); if (ph.kid !== s.kid || ph.alg !== 'EdDSA') return { signed: true, verified: false, kid: s.kid, why: 'protected header mismatch' };
  const ok = await C.subtle.verify('Ed25519', key, unb(s.signature), Buffer.from(s.protected + '.' + b64u(Buffer.from(JSON.stringify(sortDeep(body)), 'utf8'))));
  return { signed: true, verified: ok, kid: s.kid, alg: ph.alg };
}
async function rpc(door, method, params, extra = {}, sid) {
  const r = await fetch(door, { method: 'POST', headers: { ...UA, 'content-type': 'application/json', accept: 'application/json, text/event-stream', ...(sid ? { 'mcp-session-id': sid } : {}), ...extra }, body: JSON.stringify({ jsonrpc: '2.0', id: 3, method, params }) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t.replace(/^data: /m, '')); } catch (e) { const m = /^data: (.*)$/m.exec(t); try { j = m ? JSON.parse(m[1]) : null; } catch (e2) { } }
  return { status: r.status, headers: r.headers, text: t, json: j };
}
const lst = (await rpc('https://mcp.getissuer.ai/mcp', 'tools/call', { name: 'list_nodes', arguments: {} })).json.result.structuredContent.nodes;
const nodes = lst.filter(n => n.regional_door);
const rows = await Promise.all(nodes.map(async n => {
  const door = n.regional_door.endsWith('/mcp') ? n.regional_door : n.regional_door.replace(/\/$/, '') + '/mcp';
  const ex = n.example || {}; const ident = ex.isin || ex.ticker; const row = { node: n.node, door, example: ident, record_url: ex.record_url || null };
  try {
    const init = await rpc(door, 'initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'allooloo-doors02-check', version: '1.0' } });
    const sid = init.headers.get('mcp-session-id');
    const a = await rpc(door, 'tools/call', { name: 'get_record', arguments: { identifier: ident } }, {}, sid);
    let sc = a.json && a.json.result && (a.json.result.structuredContent || (() => { try { return JSON.parse(a.json.result.content[0].text); } catch (e) { return null; } })());
    row.mcp_http = a.status; row.mcp_answer = sc && sc.error ? 'error: ' + sc.error : sc && sc.cmr ? sc.cmr : 'no record';
    Object.assign(row, Object.fromEntries(Object.entries(await verify(sc)).map(([k, v]) => ['mcp_' + k, v])));
    if (ex.record_url) { const g = await fetch(ex.record_url, { headers: UA }); let rec = null; try { rec = await g.json(); } catch (e) { } row.get_http = g.status; row.get_cmr = rec && rec.cmr; Object.assign(row, Object.fromEntries(Object.entries(await verify(rec)).map(([k, v]) => ['get_' + k, v]))); }
    const o = await rpc(door, 'tools/call', { name: 'get_record', arguments: { identifier: ident } }, { 'x402-pay': '1' }, sid);
    row.offer_http = o.status; const oj = o.status === 402 ? JSON.parse(o.text) : null;
    row.offer_usd = oj && oj.accepts ? Number(oj.accepts[0].amount) / 1e6 : null;
    Object.assign(row, Object.fromEntries(Object.entries(await verify(oj)).map(([k, v]) => ['offer_' + k, v])));
    if (oj) { const hdr = o.headers.get('payment-required'); row.offer_header_matches_body = hdr ? Buffer.from(hdr, 'base64').toString() === JSON.stringify(oj) || JSON.stringify(JSON.parse(Buffer.from(hdr, 'base64').toString())) === JSON.stringify(oj) : null; }
  } catch (e) { row.error = String(e).slice(0, 160); }
  return row;
}));
rows.sort((x, y) => x.node.localeCompare(y.node));
const y = v => v === true ? 'yes' : v === false ? 'NO' : '—';
console.log('| node | example | get_record (MCP) | signed+verified | GET record | signed+verified | 402 | $ | 402 body signed+verified | kid |');
console.log('|---|---|---|---|---|---|---|---|---|---|');
for (const r of rows) console.log(`| ${r.node} | ${r.example} | ${r.mcp_answer || r.error} | ${y(r.mcp_verified)} | ${r.get_cmr || r.get_http || '—'} | ${y(r.get_verified)} | ${r.offer_http} | ${r.offer_usd ?? '—'} | ${y(r.offer_verified)} | ${r.offer_kid || r.get_kid || r.mcp_kid || '—'} |`);
const sum = k => rows.filter(r => r[k] === true).length;
console.log(`\n${rows.length} doors · MCP record verified ${sum('mcp_verified')} · GET record verified ${sum('get_verified')} · 402 answered ${rows.filter(r => r.offer_http === 402).length} · 402 body verified ${sum('offer_verified')}`);
const label = process.argv[2] || 'run';
fs.writeFileSync(new URL(`./verify-doors02-${new Date().toISOString().slice(0, 10)}-${label}.json`, import.meta.url), JSON.stringify({ at: new Date().toISOString(), jwks: JWKS_URL, rows }, null, 1));
