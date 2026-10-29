// verify_fleet.mjs — DAY ORDER 4 close read (2026-10-24): per node, one record from its own door — signature verified against the keyring it names,
// halt flag present (value, source, read_at); then the resolver: ISIN → ACM-200 for a listed US and KR issuer (NODE-ISIN-01), ACM-403 from a node halt flag
// on a real halted issuer (NODE-HALT-01). Writes verify-fleet-<date>.json beside. Usage: node verify_fleet.mjs
import { webcrypto as C } from 'node:crypto'; import fs from 'node:fs';
const PICK = { ca: 'TSX/SHOP', uk: 'LSE/SHEL', us: 'NASDAQ/AAPL', de: 'XETRA/SAP', fr: 'XPAR/FR0000120271', nl: 'XAMS/NL0010273215', ch: 'SIX/NESN', au: 'ASX/BHP', sg: 'SGX/D05', jp: 'TSE-PRIME/7203', kr: 'KOSPI/005930', hk: 'HKEX/00005' };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
const b64u = b => Buffer.from(b).toString('base64url'), unb = s => Buffer.from(s, 'base64url');
const rings = {};
async function verify(rec) {
  const s = rec.signature; if (!s) return false;
  rings[s.jwks] = rings[s.jwks] || await (await fetch(s.jwks)).json(); const jwk = rings[s.jwks].keys.find(k => k.kid === s.kid);
  const o = { ...rec }; delete o.signature; const key = await C.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: jwk.x }, { name: 'Ed25519' }, false, ['verify']);
  return C.subtle.verify('Ed25519', key, unb(s.signature), Buffer.from(s.protected + '.' + b64u(Buffer.from(JSON.stringify(sortDeep(o)), 'utf8'))));
}
const out = { nodes: [], resolver: [] };
for (const cc of Object.keys(PICK)) {
  const r = await fetch(`https://mcp.${cc}-cm-kg.ai/record/${PICK[cc]}`, { headers: { 'user-agent': 'curl/8 DAY-ORDER-4 close read' } }); const rec = await r.json();
  const row = { node: cc, http: r.status, cmr: rec.cmr, signed: !!rec.signature, verified: await verify(rec), halt_value: rec.halt ? rec.halt.value : undefined, halt_state: rec.halt ? rec.halt.state : undefined, halt_read_by: rec.halt ? rec.halt.read_by : undefined, halt_read_at: rec.halt ? rec.halt.read_at : undefined, isin: rec.identity && rec.identity.isin ? rec.identity.isin.value : null };
  out.nodes.push(row); console.log(cc, row.http, row.cmr, 'verified', row.verified, '· halt', row.halt_value, row.halt_state, '·', row.halt_read_by || '', '· isin', row.isin);
}
for (const id of ['US0378331005', 'KR7005930003', '8366.T', 'TXSE:CECO']) {
  const j = await (await fetch('https://mcp.getissuer.ai/mcp', { method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': 'curl/8 DAY-ORDER-4 close read' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'get_signal', arguments: { identifier: id } } }) })).json();
  const s = j.result.structuredContent; const row = { identifier: id, signal: s.signal, issuer: s.issuer, node: s.node, halted: s.halted || null, advisory: !!s.advisory_403, receipt: s.receipt && s.receipt.decision_id };
  out.resolver.push(row); console.log(id, s.signal, s.issuer, s.node, s.halted ? JSON.stringify(s.halted).slice(0, 160) : '', '· receipt', row.receipt);
}
fs.writeFileSync(new URL('./verify-fleet-2026-10-24.json', import.meta.url), JSON.stringify(out, null, 1));
