// cmrsign.js — NODE-SIGN-01 (DAY ORDER 4, 2026-10-24): every Capital Markets Record served by a node door carries a signature, the shape of the ECO rows:
// { alg: 'EdDSA', kid: 'allooloo-cmr-2026-10', protected, signature, jwks, over } — a detached JWS over base64url(protected) + '.' + base64url(the canonical JSON of
// the record without its `signature` member: keys sorted at every level, compact, as JSON.stringify writes it). Signing key: Worker secret CMR_SIGNING_JWK.
// Keyring of record: https://allooloo.ai/.well-known/jwks.json (also https://mcp.getissuer.ai/.well-known/jwks.json and /.well-known/jwks.json on every node door).
// One copy per Worker folder.
export const CMR_KID = 'allooloo-cmr-2026-10';
export const CMR_JWKS = 'https://allooloo.ai/.well-known/jwks.json';
const enc = new TextEncoder();
const b64u = buf => { let s = ''; for (const c of new Uint8Array(buf)) s += String.fromCharCode(c); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
let KEY = null;
async function key(env) {
  if (KEY) return KEY;
  const j = JSON.parse(String(env.CMR_SIGNING_JWK).replace(/^﻿/, '').trim());
  KEY = await crypto.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: j.x, d: j.d }, { name: 'Ed25519' }, false, ['sign']);
  return KEY;
}
export const canSign = env => !!(env && env.CMR_SIGNING_JWK);
export async function signRecord(env, rec) {
  if (!canSign(env) || !rec || typeof rec !== 'object' || Array.isArray(rec)) return rec;
  const o = { ...rec }; delete o.signature;
  const ph = b64u(enc.encode(JSON.stringify({ alg: 'EdDSA', kid: CMR_KID })));
  const sig = await crypto.subtle.sign('Ed25519', await key(env), enc.encode(ph + '.' + b64u(enc.encode(JSON.stringify(sortDeep(o))))));
  return { ...o, signature: { alg: 'EdDSA', kid: CMR_KID, protected: ph, signature: b64u(sig), jwks: CMR_JWKS, over: "base64url(protected) + '.' + base64url(canonical JSON of the record without signature: keys sorted, compact)" } };
}
export const sigRef = rec => rec && rec.signature ? { alg: rec.signature.alg, kid: rec.signature.kid, jwks: rec.signature.jwks, jws: rec.signature.protected + '..' + rec.signature.signature } : null;
