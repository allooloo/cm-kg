// DOORS-03 (d): on a door, resolve_issuer with a bare ISIN returns one record; get_record returns it signed (verified against the published JWKS) with its listing lines.
// Usage: node check_one.mjs <door mcp url> <isin> [<isin> …]
import { webcrypto as C } from 'node:crypto';
const [door, ...ids] = process.argv.slice(2); const UA = { 'user-agent': 'allooloo-doors03-check/1.0', 'content-type': 'application/json', accept: 'application/json' };
const ring = await (await fetch('https://allooloo.ai/.well-known/jwks.json')).json();
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
const b64u = b => Buffer.from(b).toString('base64url');
async function verify(o) { const s = o && o.signature; if (!s) return false; const jwk = ring.keys.find(k => k.kid === s.kid); const b = { ...o }; delete b.signature; const key = await C.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: jwk.x }, { name: 'Ed25519' }, false, ['verify']); return C.subtle.verify('Ed25519', key, Buffer.from(s.signature, 'base64url'), Buffer.from(s.protected + '.' + b64u(Buffer.from(JSON.stringify(sortDeep(b)), 'utf8')))); }
const call = async (name, identifier) => (await (await fetch(door, { method: 'POST', headers: UA, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: { identifier } } }) })).json()).result.structuredContent;
for (const id of ids) {
  const r = await call('resolve_issuer', id); const g = await call('get_record', id);
  console.log(`${id} · resolve_issuer: ${(r.matches || []).length} match(es) ${(r.matches || []).map(m => m.cmr).join(', ')} ambiguous=${r.ambiguous} · get_record: ${g.cmr || g.error} signed+verified=${await verify(g)} kid=${g.signature && g.signature.kid} · listing lines: ${(g.listings || []).map(l => `${l.exchange}/${l.code} (${l.type})`).join(' · ') || 'none'}`);
}
