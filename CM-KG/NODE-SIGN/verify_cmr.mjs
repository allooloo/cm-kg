// verify_cmr.mjs — NODE-SIGN-01 read-the-wire check: fetch one CMR record per node from its door, verify its signature against the keyring it names
// (or the door's own /.well-known/jwks.json), recomputing the canonical form (the record without `signature`, keys sorted, compact). Usage: node verify_cmr.mjs [cc ...]
import { webcrypto as C } from 'node:crypto';
const PICK = { ca: 'TSX/SHOP', uk: 'LSE/SHEL', us: 'NASDAQ/AAPL', de: 'XETRA/SAP', fr: 'XPAR/FR0000120271', nl: 'XAMS/NL0010273215', ch: 'SIX/NESN', au: 'ASX/BHP', sg: 'SGX/D05', jp: 'TSE-PRIME/7203', kr: 'KOSPI/005930', hk: 'HKEX/00005' };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
const b64u = b => Buffer.from(b).toString('base64url'), unb = s => Buffer.from(s, 'base64url');
const out = [];
for (const cc of (process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(PICK))) {
  const url = `https://mcp.${cc}-cm-kg.ai/record/${PICK[cc]}`; const row = { node: cc, url };
  try {
    const r = await fetch(url, { headers: { 'user-agent': 'curl/8 NODE-SIGN-01 verify' } }); row.http = r.status; const rec = await r.json(); const s = rec.signature;
    if (!s) { row.signed = false; out.push(row); console.log(cc, r.status, 'UNSIGNED'); continue; }
    const ring = await (await fetch(s.jwks)).json(); const jwk = (ring.keys || []).find(k => k.kid === s.kid);
    const o = { ...rec }; delete o.signature;
    const key = await C.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: jwk.x }, { name: 'Ed25519' }, false, ['verify']);
    row.verified = await C.subtle.verify('Ed25519', key, unb(s.signature), Buffer.from(s.protected + '.' + b64u(Buffer.from(JSON.stringify(sortDeep(o)), 'utf8'))));
    row.kid = s.kid; row.jwks = s.jwks; row.cmr = rec.cmr; row.as_of = rec.as_of;
  } catch (e) { row.error = String(e).slice(0, 200); }
  out.push(row); console.log(cc, row.http, row.cmr, row.kid, 'verified', row.verified, row.error || '');
}
(await import('node:fs')).writeFileSync(new URL('./verify-cmr-' + new Date().toISOString().slice(0, 10) + '.json', import.meta.url), JSON.stringify(out, null, 1));
