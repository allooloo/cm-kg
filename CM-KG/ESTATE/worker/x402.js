// X402 TEST RECEIVER (CEO, Sept 13 2026) — agentic-trades.ai: one paid route /x402/record/{node}/{exchange}/{code} returning the same record as the
// free route, priced $0.01 USDC on Base, settled to the CEO's address (Worker secret X402_PAYTO — never in code, never in the transcript).
// Facilitator: x402.org hosted, Base Sepolia (eip155:84532) first; Coinbase CDP on Base mainnet (eip155:8453) on the CEO's word (env X402_NETWORK).
// Flow: no payment → 402 with the requirements (body + PAYMENT-REQUIRED header) → client pays (PAYMENT-SIGNATURE / X-PAYMENT) → facilitator verify → 200 with the record
// → facilitator settle → PAYMENT-RESPONSE / X-PAYMENT-RESPONSE header; the settlement (tx hash, amount) is counted in KV for RADAR's "paid calls" line.
import { APEX, OPERATOR, headers, json } from './chrome.js';

const NETWORKS = {
  'base-sepolia': { caip2: 'eip155:84532', usdc: '0x036CbD53842c5426634e7929541eC2318f3dCF7e', name: 'USDC', facilitator: 'https://x402.org/facilitator', explorer: 'https://sepolia.basescan.org/tx/' },
  'base': { caip2: 'eip155:8453', usdc: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', name: 'USD Coin', facilitator: 'https://api.cdp.coinbase.com/platform/v2/x402', fallback: 'https://facilitator.payai.network', explorer: 'https://basescan.org/tx/' }
};
export const PRICE_ATOMIC = '10000';   // $0.01 in USDC (6 decimals)
const b64 = o => btoa(unescape(encodeURIComponent(JSON.stringify(o))));
const unb64 = s => JSON.parse(decodeURIComponent(escape(atob(s))));

export function netKey(env, url) { return url && url.pathname === '/api' ? (env.X402_API_NETWORK || 'base-sepolia') : (env.X402_NETWORK || 'base-sepolia'); }   // every /api door (all surfaces) rides the API network; the trades record route rides X402_NETWORK
const IS_API = url => url && url.hostname === 'agentic-x402.ai';
const IS_SURFACE_API = url => url && url.pathname === '/api' && url.hostname !== 'agentic-x402.ai';
export function describe(url) {
  if (IS_SURFACE_API(url)) return `One paid call on ${url.hostname} for $0.01 USDC: the surface's own statement of record (a market node: its list_nodes line; a product: its record of record; allooloo.io: the estate scale block), public-record only, with an EdDSA-signed receipt that resolves forever at https://${url.hostname}/x402/receipt/{nonce}. Doctrine: https://agentic-x402.ai/.`;
  return IS_API(url)
    ? 'Allooloo Capital Markets estate index for $0.01 USDC: every market node (Canada, United Kingdom, United States, Germany, France, Netherlands, Switzerland, Australia, Singapore, Japan, South Korea), issuer and disclosure-event counts, drop date; add ?record=node/exchange/code (e.g. uk-cm-kg/LSE/BARC) for one Capital Markets Record, sourced per field, public-record only. Every settlement answers with an EdDSA-signed receipt that resolves forever at /x402/receipt/{nonce}.'
    : 'One Capital Markets Record for $0.01 USDC — a listed issuer\'s identity, registry identifiers, aliases, listing, disclosure events, auditor and transfer agent, each field sourced to the public filing, served from the node of the issuer\'s own market (eleven markets, in-country). Path: /x402/record/{node}/{exchange}/{code}, e.g. uk-cm-kg/LSE/BARC. The same record the free MCP door serves; the payment buys the receipted call.';
}
// x402 Bazaar discovery extension (CDP facilitator indexes the resource on its first settlement)
export function bazaar(url) {
  const api = IS_API(url);
  if (IS_SURFACE_API(url)) return { bazaar: { info: { input: { type: 'http', method: 'GET' }, output: { type: 'json', example: { receipt: { receipt_url: `https://${url.hostname}/x402/receipt/{nonce}`, settled: true, amount_usdc: '0.01' }, data: { surface: url.hostname, statement: 'the surface\'s record of record' } } } }, schema: { '$schema': 'https://json-schema.org/draft/2020-12/schema', type: 'object', properties: { input: { type: 'object', properties: { type: { type: 'string', const: 'http' }, method: { type: 'string', enum: ['GET', 'HEAD', 'DELETE'] } }, required: ['type', 'method'] }, output: { type: 'object' } }, required: ['input'] } } };
  const input = api
    ? { type: 'http', method: 'GET', queryParams: { record: { type: 'string', required: false, description: 'optional node/exchange/code — returns that Capital Markets Record instead of the estate index', example: 'uk-cm-kg/LSE/BARC' } } }
    : { type: 'http', method: 'GET', pathParams: { node: { type: 'string', required: true, description: 'market node, e.g. uk-cm-kg', example: 'uk-cm-kg' }, exchange: { type: 'string', required: true, description: 'exchange code, e.g. LSE', example: 'LSE' }, code: { type: 'string', required: true, description: 'ticker, ISIN or LEI', example: 'BARC' } } };
  const example = api
    ? { receipt: { receipt_url: 'https://agentic-x402.ai/x402/receipt/{nonce}', settled: true, amount_usdc: '0.01', network: 'eip155:8453' }, data: { nodes: [{ node: 'uk-cm-kg', live: true, records: 1930, events: 6100, as_of: '2026-09-11' }] } }
    : { cmr: 'v0', node: 'uk-cm-kg', identity: { name: 'Barclays PLC', lei: '213800LBQA1Y9L22JB70' }, aliases: [], events: [] };
  return { bazaar: { info: { input, output: { type: 'json', example } }, schema: { '$schema': 'https://json-schema.org/draft/2020-12/schema', type: 'object', properties: { input: { type: 'object', properties: { type: { type: 'string', const: 'http' }, method: { type: 'string', enum: ['GET', 'HEAD', 'DELETE'] }, queryParams: { type: 'object' }, pathParams: { type: 'object' } }, required: ['type', 'method'] }, output: { type: 'object', properties: { type: { type: 'string' }, example: { type: 'object' } } } }, required: ['input'] } } };
}
export function requirements(env, url) {
  const net = NETWORKS[netKey(env, url)] || NETWORKS['base-sepolia'];
  return { scheme: 'exact', network: net.caip2, amount: PRICE_ATOMIC, maxAmountRequired: PRICE_ATOMIC, asset: net.usdc, payTo: env.X402_PAYTO, maxTimeoutSeconds: url && url.hostname === 'agentic-x402.ai' ? 60 : 300,
    resource: url.origin + url.pathname, description: describe(url), mimeType: 'application/json', extra: { name: net.name, version: '2' } };   // EIP-712 domain of the USDC contract per network: Base mainnet 'USD Coin', Base Sepolia test contract 'USDC'
}
function paymentRequired(env, url, error) {
  const req = requirements(env, url);
  const body = { x402Version: 2, error: error || 'Payment required: $0.01 USDC on ' + req.network, accepts: [req], resource: { url: req.resource, description: req.description, mimeType: req.mimeType }, extensions: bazaar(url), free_route: url.pathname === '/api' ? `https://${url.hostname}/facts.json` : `${APEX}${url.pathname.replace('/x402', '')}`, operator: OPERATOR };
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
export function facilitatorUrl(env, url) {
  const net = NETWORKS[netKey(env, url)] || NETWORKS['base-sepolia'];
  if (env.X402_FACILITATOR) return env.X402_FACILITATOR;
  if (net.fallback && !(env.CDP_API_KEY_ID && env.CDP_API_KEY_SECRET)) return net.fallback;
  return net.facilitator;
}
async function facilitator(env, path, body, url) {
  const base = facilitatorUrl(env, url); const u = new URL(base + path);
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
  const v = await facilitator(env, '/verify', { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req }, url);
  if (!(v.body && v.body.isValid)) return paymentRequired(env, url, 'payment not valid: ' + ((v.body && (v.body.invalidReason || v.body.error)) || v.status));
  // serve the same record the free route serves (forwarded to the owning node by the apex; no body stored here)
  const rec = await fetch(`${APEX}/record/${m[1]}/${m[2]}/${m[3]}`, { headers: { accept: 'application/json' }, signal: AbortSignal.timeout(30000) });
  const recBody = await rec.text();
  const s = await facilitator(env, '/settle', { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req }, url);
  const settled = !!(s.body && (s.body.success || s.body.transaction || s.body.txHash));
  const tx = s.body && (s.body.transaction || s.body.txHash || null);
  const receipt = { x402Version: 2, success: settled, transaction: tx, network: req.network, amount: req.amount, asset: req.asset, payer: s.body && (s.body.payer || null), explorer: tx ? ((NETWORKS[netKey(env, url)] || NETWORKS['base-sepolia']).explorer + tx) : null, errorReason: settled ? null : (s.body && (s.body.errorReason || s.body.error)) || null };
  try { const c = parseInt((await env.STATUS.get('x402:count')) || '0', 10) + (settled ? 1 : 0); await env.STATUS.put('x402:count', String(c)); if (settled) await env.STATUS.put('x402:last', JSON.stringify({ ...receipt, at: new Date().toISOString(), resource: req.resource })); } catch (e) { /* counter is best-effort */ }
  const enc = b64(receipt);
  return new Response(recBody, { status: rec.status, headers: headers({ node: 'x402' }, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'PAYMENT-RESPONSE': enc, 'X-PAYMENT-RESPONSE': enc, 'access-control-allow-origin': '*', 'access-control-expose-headers': 'PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' }) });
}
export async function paidStats(env) {
  try { const c = parseInt((await env.STATUS.get('x402:count')) || '0', 10); const last = await env.STATUS.get('x402:last', 'json'); return { paid_calls: c, last, price_usdc: '0.01', facilitator: facilitatorUrl(env), route: 'https://agentic-trades.ai/x402/record/{node}/{exchange}/{code}', network: (NETWORKS[env.X402_NETWORK || 'base-sepolia'] || NETWORKS['base-sepolia']).caip2, receiver_configured: !!env.X402_PAYTO, source: 'facilitator settlement receipts counted in KV' }; } catch (e) { return { paid_calls: 0, last: null, source: 'KV unavailable' }; }
}

// ---- AGENTIC-X402.AI (23rd surface): /api — a paid call with a signed receipt. EdDSA (Ed25519) receipts, kid allooloo-x402-receipts-2026-09, kept forever.
const RECEIPT_KID = 'allooloo-x402-receipts-2026-09';
export async function receiptJwks(env) { try { const prv = JSON.parse(env.X402_RECEIPT_JWK); const { d, ...pub } = prv; pub.use = 'sig'; pub.alg = 'EdDSA'; pub.kid = pub.kid || RECEIPT_KID; return { keys: [pub] }; } catch (e) { return { keys: [] }; } }
async function signReceipt(env, claims) {
  const prv = JSON.parse(env.X402_RECEIPT_JWK); const key = await crypto.subtle.importKey('jwk', { kty: prv.kty, crv: prv.crv, x: prv.x, d: prv.d }, { name: 'Ed25519' }, false, ['sign']);
  const h = b64uStr(JSON.stringify({ alg: 'EdDSA', typ: 'JWT', kid: prv.kid || RECEIPT_KID })); const p = b64uStr(JSON.stringify(claims));
  const sig = await crypto.subtle.sign({ name: 'Ed25519' }, key, new TextEncoder().encode(`${h}.${p}`)); return `${h}.${p}.${b64uBuf(sig)}`;
}
export async function receiptLookup(env, nonce) { try { return await env.STATUS.get(`x402:receipt:${nonce}`, 'json'); } catch (e) { return null; } }
// resolve(url) → { data, status }: what this surface's paid call buys (surfaces.js paidResource); agentic-x402.ai keeps its index / ?record= contract
export async function handleApi(request, env, url, resolve) {
  const base = url.origin;
  if (!env.X402_PAYTO) return json({ error: 'receiver_not_configured', note: 'the pay-to address (Worker secret X402_PAYTO) is not set' }, { node: 'x402' }, 'no-store', 503);
  const sig = request.headers.get('PAYMENT-SIGNATURE') || request.headers.get('X-PAYMENT');
  if (!sig) return paymentRequired(env, url);
  let payload; try { payload = unb64(sig); } catch (e) { return paymentRequired(env, url, 'PAYMENT-SIGNATURE is not base64 JSON'); }
  const req = requirements(env, url);
  const v = await facilitator(env, '/verify', { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req }, url);
  if (!(v.body && v.body.isValid)) return paymentRequired(env, url, 'payment not valid: ' + ((v.body && (v.body.invalidReason || v.body.error)) || v.status));
  // what the call buys: the estate index (every node, its counts and drop) — or one record when ?record=node/exchange/code is given
  const rq = IS_API(url) ? url.searchParams.get('record') : null; let data, dataStatus = 200;
  if (resolve && !IS_API(url)) { try { const r = await resolve(url); data = r.data; dataStatus = r.status || 200; } catch (e) { data = { error: 'statement unavailable' }; dataStatus = 503; } }
  else if (rq && /^[a-z]{2}-cm-kg\/[A-Za-z\-]+\/.+$/i.test(rq)) { const r = await fetch(`${APEX}/record/${rq}`, { headers: { accept: 'application/json' }, signal: AbortSignal.timeout(30000) }); dataStatus = r.status; try { data = await r.json(); } catch (e) { data = { error: 'record fetch failed', status: r.status }; } }
  else { const r = await fetch(`${APEX}/nodes.json`, { headers: { accept: 'application/json' }, signal: AbortSignal.timeout(30000) }); try { data = await r.json(); } catch (e) { data = { error: 'index fetch failed', status: r.status }; } }
  const s = await facilitator(env, '/settle', { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req }, url);
  const settled = !!(s.body && (s.body.success || s.body.transaction || s.body.txHash)); const tx = s.body && (s.body.transaction || s.body.txHash || null);
  const net = NETWORKS[netKey(env, url)] || NETWORKS['base-sepolia']; const now = Math.floor(Date.now() / 1000);
  const nonce = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
  const sha = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(data)))), b => b.toString(16).padStart(2, '0')).join('');
  const claims = { iss: base, surface: url.hostname, data_sha256: sha, sub: (s.body && s.body.payer) || (payload.payload && payload.payload.authorization && payload.payload.authorization.from) || 'payer', jti: nonce, iat: now, resource: req.resource + (rq ? `?record=${rq}` : ''), scheme: 'exact', standard: 'EIP-3009 transferWithAuthorization', network: req.network, asset: req.asset, amount: req.amount, amount_usdc: '0.01', payTo: req.payTo, transaction: tx, explorer: tx ? net.explorer + tx : null, settled, facilitator: facilitatorUrl(env, url), receipt_url: `${base}/x402/receipt/${nonce}`, operator: OPERATOR };
  let jwt = null; try { jwt = await signReceipt(env, claims); } catch (e) { jwt = null; }
  const receipt = { ...claims, jwt, kid: RECEIPT_KID, jwks: `${base}/x402/jwks.json` };
  try { await env.STATUS.put(`x402:receipt:${nonce}`, JSON.stringify(receipt)); } catch (e) { /* the receipt is also in the response */ }
  try { const c = parseInt((await env.STATUS.get('x402:count')) || '0', 10) + (settled ? 1 : 0); await env.STATUS.put('x402:count', String(c)); if (settled) await env.STATUS.put('x402:last', JSON.stringify({ x402Version: 2, success: true, transaction: tx, network: req.network, amount: req.amount, asset: req.asset, payer: claims.sub, explorer: claims.explorer, at: new Date().toISOString(), resource: claims.resource, receipt: claims.receipt_url, surface: url.hostname })); } catch (e) { /* best effort */ }
  const pr = { x402Version: 2, success: settled, transaction: tx, network: req.network, amount: req.amount, asset: req.asset, payer: claims.sub, receipt: claims.receipt_url, errorReason: settled ? null : (s.body && (s.body.errorReason || s.body.error)) || null };
  const enc = b64(pr);
  return new Response(JSON.stringify({ receipt, data }, null, 1), { status: settled ? dataStatus : 402, headers: headers({ node: 'x402' }, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'PAYMENT-RESPONSE': enc, 'X-PAYMENT-RESPONSE': enc, 'X-X402-Receipt': claims.receipt_url, 'access-control-allow-origin': '*', 'access-control-expose-headers': 'PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, X-X402-Receipt' }) });
}

export function openapi() {
  const R = { type: 'object', description: 'EdDSA-signed receipt (kid allooloo-x402-receipts-2026-09); jwt verifies against /x402/jwks.json', properties: { iss: { type: 'string' }, sub: { type: 'string', description: 'payer address' }, jti: { type: 'string', description: 'nonce' }, iat: { type: 'integer' }, resource: { type: 'string' }, network: { type: 'string', example: 'eip155:8453' }, asset: { type: 'string' }, amount: { type: 'string', example: '10000' }, amount_usdc: { type: 'string', example: '0.01' }, payTo: { type: 'string' }, transaction: { type: 'string', nullable: true }, explorer: { type: 'string', nullable: true }, settled: { type: 'boolean' }, facilitator: { type: 'string' }, receipt_url: { type: 'string' }, jwt: { type: 'string' }, kid: { type: 'string' }, jwks: { type: 'string' } } };
  const PR = { type: 'object', description: 'x402 v2 PaymentRequired', properties: { x402Version: { type: 'integer', const: 2 }, error: { type: 'string' }, accepts: { type: 'array', items: { type: 'object', properties: { scheme: { type: 'string', const: 'exact' }, network: { type: 'string', example: 'eip155:8453' }, amount: { type: 'string', example: '10000' }, asset: { type: 'string' }, payTo: { type: 'string' }, maxTimeoutSeconds: { type: 'integer', example: 60 }, resource: { type: 'string' }, description: { type: 'string' } } } }, extensions: { type: 'object' } } };
  return { openapi: '3.1.0', info: { title: 'Agentic x402 — a paid call with a signed receipt', version: '1.0.0', description: 'One call, one cent, one receipt. GET /api answers 402 Payment Required (x402 v2, scheme exact = EIP-3009 transferWithAuthorization, $0.01 USDC on Base, 60 s window); repeat the call with PAYMENT-SIGNATURE to receive the data and an EdDSA-signed receipt that resolves forever. Public-record only. Operator: Allooloo Technologies Corp.', contact: { name: 'Allooloo Technologies Corp.', url: 'https://allooloo.io/#contact' }, termsOfService: 'https://allooloo.io/terms' },
    servers: [{ url: 'https://agentic-x402.ai' }], externalDocs: { description: 'agentic-x402.ai', url: 'https://agentic-x402.ai/' },
    paths: {
      '/api': { get: { operationId: 'paidCall', summary: 'Paid call: the estate index, or one Capital Markets Record with ?record=', description: 'Without payment: 402 with the offer (body + PAYMENT-REQUIRED header). With a valid PAYMENT-SIGNATURE: 200 { receipt, data }; headers PAYMENT-RESPONSE and X-X402-Receipt.', parameters: [{ name: 'record', in: 'query', required: false, schema: { type: 'string' }, example: 'uk-cm-kg/LSE/BARC', description: 'node/exchange/code — returns that record instead of the index' }, { name: 'PAYMENT-SIGNATURE', in: 'header', required: false, schema: { type: 'string' }, description: 'base64 x402 v2 payment payload (X-PAYMENT accepted)' }],
        responses: { '200': { description: 'settled: the data and the receipt', headers: { 'PAYMENT-RESPONSE': { schema: { type: 'string' } }, 'X-X402-Receipt': { schema: { type: 'string' } } }, content: { 'application/json': { schema: { type: 'object', properties: { receipt: R, data: { type: 'object' } } } } } }, '402': { description: 'payment required — the offer', headers: { 'PAYMENT-REQUIRED': { schema: { type: 'string' } } }, content: { 'application/json': { schema: PR } } }, '503': { description: 'receiver not configured' } } } },
      '/x402/jwks.json': { get: { operationId: 'receiptJwks', summary: 'Receipt signing key (Ed25519, kid allooloo-x402-receipts-2026-09)', responses: { '200': { description: 'JWKS', content: { 'application/json': { schema: { type: 'object', properties: { keys: { type: 'array', items: { type: 'object' } } } } } } } } } },
      '/x402/receipt/{nonce}': { get: { operationId: 'receipt', summary: 'Resolve a receipt, forever', parameters: [{ name: 'nonce', in: 'path', required: true, schema: { type: 'string', pattern: '^[a-f0-9]{32}$' } }], responses: { '200': { description: 'the receipt', content: { 'application/json': { schema: R } } }, '404': { description: 'unknown nonce' } } } }
    },
    'x-cmr': { operator: 'Allooloo Technologies Corp.', identity_headers: ['X-CMR-X402: ready', 'X-CMR-Operator', 'X-CMR-Contact', 'X-CMR-Node', 'X-CMR-Version', 'X-CMR-Source: public-record'], receipts_kid: 'allooloo-x402-receipts-2026-09', trades_record_route: 'https://agentic-trades.ai/x402/record/{node}/{exchange}/{code}' } };
}
