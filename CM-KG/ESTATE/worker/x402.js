// X402 TEST RECEIVER (CEO, Sept 13 2026) — agentic-trades.ai: one paid route /x402/record/{node}/{exchange}/{code} returning the same record as the
// free route, priced $0.01 USDC on Base, settled to the CEO's address (Worker secret X402_PAYTO — never in code, never in the transcript).
// Facilitator: x402.org hosted, Base Sepolia (eip155:84532) first; Coinbase CDP on Base mainnet (eip155:8453) on the CEO's word (env X402_NETWORK).
// Flow: no payment → 402 with the requirements (body + PAYMENT-REQUIRED header) → client pays (PAYMENT-SIGNATURE / X-PAYMENT) → facilitator verify → 200 with the record
// → facilitator settle → PAYMENT-RESPONSE / X-PAYMENT-RESPONSE header; the settlement (tx hash, amount) is counted in KV for RADAR's "paid calls" line.
import { APEX, OPERATOR, headers, json } from './chrome.js';

const NETWORKS = {
  'base-sepolia': { caip2: 'eip155:84532', usdc: '0x036CbD53842c5426634e7929541eC2318f3dCF7e', facilitator: 'https://x402.org/facilitator', explorer: 'https://sepolia.basescan.org/tx/' },
  'base': { caip2: 'eip155:8453', usdc: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', facilitator: 'https://api.cdp.coinbase.com/platform/v2/x402', fallback: 'https://facilitator.payai.network', explorer: 'https://basescan.org/tx/' }
};
export const PRICE_ATOMIC = '10000';   // $0.01 in USDC (6 decimals)
const b64 = o => btoa(unescape(encodeURIComponent(JSON.stringify(o))));
const unb64 = s => JSON.parse(decodeURIComponent(escape(atob(s))));

export function requirements(env, url) {
  const net = NETWORKS[env.X402_NETWORK || 'base-sepolia'] || NETWORKS['base-sepolia'];
  return { scheme: 'exact', network: net.caip2, amount: PRICE_ATOMIC, maxAmountRequired: PRICE_ATOMIC, asset: net.usdc, payTo: env.X402_PAYTO, maxTimeoutSeconds: 300,
    resource: url.origin + url.pathname, description: 'Capital Markets Record (paid route, $0.01 USDC) — the same record the free route serves', mimeType: 'application/json', extra: { name: 'USDC', version: '2' } };
}
function paymentRequired(env, url, error) {
  const req = requirements(env, url);
  const body = { x402Version: 2, error: error || 'Payment required: $0.01 USDC on ' + req.network, accepts: [req], resource: { url: req.resource, description: req.description, mimeType: req.mimeType }, free_route: `${APEX}${url.pathname.replace('/x402', '')}`, operator: OPERATOR };
  return new Response(JSON.stringify(body, null, 1), { status: 402, headers: headers({ node: 'x402' }, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'PAYMENT-REQUIRED': b64(body), 'access-control-allow-origin': '*', 'access-control-expose-headers': 'PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' }) });
}
// ---- Coinbase CDP per-request JWT (Secret API key: Ed25519 base64 64-byte secret, or legacy ES256 PEM). Never logged.
const b64uBuf = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const b64uStr = str => b64uBuf(new TextEncoder().encode(str));
const pemDer = pem => Uint8Array.from(atob(pem.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '')), c => c.charCodeAt(0));
async function cdpJwt(env, method, host, path) {
  const id = env.CDP_API_KEY_ID, secret = env.CDP_API_KEY_SECRET; if (!id || !secret) return null;
  const now = Math.floor(Date.now() / 1000); const nonce = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
  const claims = { sub: id, iss: 'cdp', aud: ['cdp_service'], nbf: now, exp: now + 120, uris: [`${method} ${host}${path}`] };
  let alg, key, sigAlg;
  if (secret.includes('BEGIN')) { alg = 'ES256'; key = await crypto.subtle.importKey('pkcs8', pemDer(secret), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']); sigAlg = { name: 'ECDSA', hash: 'SHA-256' }; }
  else { alg = 'EdDSA'; const raw = Uint8Array.from(atob(secret), c => c.charCodeAt(0)); const seed = raw.slice(0, 32); const pkcs8 = new Uint8Array([0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20, ...seed]); key = await crypto.subtle.importKey('pkcs8', pkcs8, { name: 'Ed25519' }, false, ['sign']); sigAlg = { name: 'Ed25519' }; }
  const h = b64uStr(JSON.stringify({ alg, kid: id, typ: 'JWT', nonce })); const p = b64uStr(JSON.stringify(claims));
  const sig = await crypto.subtle.sign(sigAlg, key, new TextEncoder().encode(`${h}.${p}`));
  return `${h}.${p}.${b64uBuf(sig)}`;
}
export function facilitatorUrl(env) {
  const net = NETWORKS[env.X402_NETWORK || 'base-sepolia'] || NETWORKS['base-sepolia'];
  if (env.X402_FACILITATOR) return env.X402_FACILITATOR;
  if (net.fallback && !(env.CDP_API_KEY_ID && env.CDP_API_KEY_SECRET)) return net.fallback;
  return net.facilitator;
}
async function facilitator(env, path, body) {
  const base = facilitatorUrl(env); const u = new URL(base + path);
  const h = { 'content-type': 'application/json', accept: 'application/json' };
  if (u.hostname.endsWith('coinbase.com')) { const jwt = await cdpJwt(env, 'POST', u.hostname, u.pathname); if (jwt) h['Authorization'] = 'Bearer ' + jwt; }
  const r = await fetch(u.toString(), { method: 'POST', headers: h, body: JSON.stringify(body), signal: AbortSignal.timeout(30000) });
  let j = null; try { j = await r.json(); } catch (e) { j = { error: 'facilitator answered ' + r.status }; }
  return { status: r.status, body: j };
}
export async function handlePaid(request, env, url, m) {
  if (!env.X402_PAYTO) return json({ error: 'receiver_not_configured', note: 'the pay-to address (Worker secret X402_PAYTO) is not set; the CEO supplies it out of band', free_route: `${APEX}${url.pathname.replace('/x402', '')}` }, { node: 'x402' }, 'no-store', 503);
  const sig = request.headers.get('PAYMENT-SIGNATURE') || request.headers.get('X-PAYMENT');
  if (!sig) return paymentRequired(env, url);
  let payload; try { payload = unb64(sig); } catch (e) { return paymentRequired(env, url, 'PAYMENT-SIGNATURE is not base64 JSON'); }
  const req = requirements(env, url);
  const v = await facilitator(env, '/verify', { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req });
  if (!(v.body && v.body.isValid)) return paymentRequired(env, url, 'payment not valid: ' + ((v.body && (v.body.invalidReason || v.body.error)) || v.status));
  // serve the same record the free route serves (forwarded to the owning node by the apex; no body stored here)
  const rec = await fetch(`${APEX}/record/${m[1]}/${m[2]}/${m[3]}`, { headers: { accept: 'application/json' }, signal: AbortSignal.timeout(30000) });
  const recBody = await rec.text();
  const s = await facilitator(env, '/settle', { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req });
  const settled = !!(s.body && (s.body.success || s.body.transaction || s.body.txHash));
  const tx = s.body && (s.body.transaction || s.body.txHash || null);
  const receipt = { x402Version: 2, success: settled, transaction: tx, network: req.network, amount: req.amount, asset: req.asset, payer: s.body && (s.body.payer || null), explorer: tx ? ((NETWORKS[env.X402_NETWORK || 'base-sepolia'] || NETWORKS['base-sepolia']).explorer + tx) : null, errorReason: settled ? null : (s.body && (s.body.errorReason || s.body.error)) || null };
  try { const c = parseInt((await env.STATUS.get('x402:count')) || '0', 10) + (settled ? 1 : 0); await env.STATUS.put('x402:count', String(c)); if (settled) await env.STATUS.put('x402:last', JSON.stringify({ ...receipt, at: new Date().toISOString(), resource: req.resource })); } catch (e) { /* counter is best-effort */ }
  const enc = b64(receipt);
  return new Response(recBody, { status: rec.status, headers: headers({ node: 'x402' }, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'PAYMENT-RESPONSE': enc, 'X-PAYMENT-RESPONSE': enc, 'access-control-allow-origin': '*', 'access-control-expose-headers': 'PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' }) });
}
export async function paidStats(env) {
  try { const c = parseInt((await env.STATUS.get('x402:count')) || '0', 10); const last = await env.STATUS.get('x402:last', 'json'); return { paid_calls: c, last, price_usdc: '0.01', facilitator: facilitatorUrl(env), route: 'https://agentic-trades.ai/x402/record/{node}/{exchange}/{code}', network: (NETWORKS[env.X402_NETWORK || 'base-sepolia'] || NETWORKS['base-sepolia']).caip2, receiver_configured: !!env.X402_PAYTO, source: 'facilitator settlement receipts counted in KV' }; } catch (e) { return { paid_calls: 0, last: null, source: 'KV unavailable' }; }
}
