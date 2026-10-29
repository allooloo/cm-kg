// rco.js — RCO-A-01 (DAY ORDER 3, 2026-10-24): Allooloo writes receipts. A read that clears a decision (an ISIN resolved, a signal returned, an ECO rule
// read) leaves one RCO receipt on mcp.rco-a2a.ai in the schema of record (plan v1.1 §2.6): decision_id · object · actor_class · rule {id, version} ·
// records_read (with their signatures, or null where the record carries none) · signal · decided_at · issuing_door · signature (EdDSA, kid
// allooloo-rco-2026-10, keyring https://mcp.getissuer.ai/.well-known/jwks.json). The write key was issued by the office (secret RCO_WRITE_KEY); the
// signing key is RCO_SIGNING_JWK. The write runs after the answer (ctx.waitUntil): the caller never waits on the ledger. One copy per Worker folder.
const RCO = 'https://mcp.rco-a2a.ai/mcp';
export const RCO_KID = 'allooloo-rco-2026-10';
export const RCO_KEYRING = 'https://mcp.getissuer.ai/.well-known/jwks.json';
const enc = new TextEncoder();
const b64u = buf => { let s = ''; for (const c of new Uint8Array(buf)) s += String.fromCharCode(c); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
export const decisionId = () => 'dec_' + [...crypto.getRandomValues(new Uint8Array(12))].map(b => b.toString(16).padStart(2, '0')).join('');
export async function sha256(s) { return 'sha256:' + [...new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode(typeof s === 'string' ? s : JSON.stringify(s))))].map(b => b.toString(16).padStart(2, '0')).join(''); }
export const receiptLinks = id => ({ decision_id: id, get_receipt: { door: RCO, tool: 'get_receipt', arguments: { decision_id: id } }, page: `https://rco-a2a.ai/receipts/${id}` });
let KEY = null;
async function signingKey(env) {
  if (KEY) return KEY;
  const j = JSON.parse(String(env.RCO_SIGNING_JWK).replace(/^﻿/, '').trim());   // a secret piped from PowerShell carries a BOM
  KEY = await crypto.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: j.x, d: j.d }, { name: 'Ed25519' }, false, ['sign']);
  return KEY;
}
export async function writeReceipt(env, body) {
  if (!env || !env.RCO_SIGNING_JWK || !env.RCO_WRITE_KEY) { console.log('rco receipt not written: keys absent', body.decision_id); return null; }
  try {
    const ph = b64u(enc.encode(JSON.stringify({ alg: 'EdDSA', kid: RCO_KID })));
    const payload = b64u(enc.encode(JSON.stringify(sortDeep(body))));
    const sig = await crypto.subtle.sign('Ed25519', await signingKey(env), enc.encode(ph + '.' + payload));
    const receipt = { ...body, signature: { alg: 'EdDSA', kid: RCO_KID, jws: ph + '..' + b64u(sig), keyring: RCO_KEYRING } };
    for (let attempt = 1; attempt <= 3; attempt++) {
      const r = await fetch(RCO, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'x-door-key': String(env.RCO_WRITE_KEY).replace(/^﻿/, '').trim(), 'user-agent': 'Allooloo rco-writer (RCO-A-01)' },
        body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'write_receipt', arguments: { receipt } } }) });
      const j = await r.json().catch(() => null); const res = j && j.result;
      const out = res && (res.structuredContent || (res.content && res.content[0] && JSON.parse(res.content[0].text)));
      if (res && !res.isError) { console.log('rco receipt written', body.decision_id, out && out.ledger && out.ledger.transaction_id); return out; }
      console.log('rco receipt refused', body.decision_id, 'attempt', attempt, JSON.stringify(out || j).slice(0, 300));
      if (out && /invalid_receipt|bad_signature|door_not_registered|not_authorised/.test(out.code || '')) return out;
      await new Promise(s => setTimeout(s, 1500 * attempt));
    }
  } catch (e) { console.log('rco receipt error', body.decision_id, String(e).slice(0, 200)); }
  return null;
}
