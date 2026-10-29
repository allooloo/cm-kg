// x402gate.js — X402-A-01 (DAY ORDER 3, 2026-10-24). x402 v2 on the Allooloo doors: the resolver, the twelve node doors, the ECO records (and, in the
// RCO door, the receipt write path). Base mainnet, USD Coin (EIP-3009), scheme exact, Coinbase CDP facilitator (per-request JWT, Worker secrets
// CDP_API_KEY_ID / CDP_API_KEY_SECRET), payTo = Worker secret X402_PAYTO (the MK wallet of gsc-x402.ai, read from AGENT KEYS by name). Lifted from the
// estate module (CM-KG\ESTATE\worker\x402.js), never a rewrite of its payment path. One copy per Worker folder.
// Free reads: unlimited for every agent (CEO ruling 2026-10-24, DAY ORDER 5 — no rationing; X402_FREE_PER_DAY is no longer read by decide()). Was: the first X402_FREE_PER_DAY reads per agent per UTC day were free; an agent is the hash of its address, User-Agent and
// optional X-Agent-Id (one agent behind a shared egress counts as one). A caller may ask for the offer at any time (header x402-pay: 1 or ?x402=1) —
// a paid read is processed whenever a PAYMENT-SIGNATURE is sent. Pricing (atomic USDC, 6 decimals): every record read 10000 ($0.01). Counts only
// are published (KV X402: settlements, offers, free reads by day and by door) — never amounts on a page.
export const NETWORK = { caip2: 'eip155:8453', usdc: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', name: 'USD Coin', facilitator: 'https://api.cdp.coinbase.com/platform/v2/x402', fallback: 'https://facilitator.payai.network', explorer: 'https://basescan.org/tx/' };
export const PRICE = '10000';
// X402-A-01 rider (CEO 2026-10-24): Open USD on Base as the second accept entry, the estate's terms (AL-x402-01): Permit2 + the facilitator's
// eip2612GasSponsoring extension (OUSD has no EIP-3009); payTo = Worker secret X402_PAYTO_OUSD (the CB Wallet, AGENT KEYS x402-payto-ousd). USDC stays first.
export const OUSD = { asset: '0xB2000000000000000000002fEb517dFeC7415344', name: 'OpenUSD', version: '1' };
const EIP2612_GAS_SPONSORING = { eip2612GasSponsoring: { info: { description: 'The facilitator accepts EIP-2612 gasless Permit to Permit2 canonical contract.', version: '1' }, schema: { type: 'object' } } };
export function accepts(env, resource, description) {
  const usdc = requirements(env, resource, description); const to = String(env.X402_PAYTO_OUSD || '').replace(/^﻿/, '').trim();
  return to ? [usdc, { ...usdc, asset: OUSD.asset, payTo: to, extra: { assetTransferMethod: 'permit2', name: OUSD.name, version: OUSD.version } }] : [usdc];
}
export const PRICING = { network: 'eip155:8453 (Base)', asset: 'USDC (EIP-3009) first; Open USD (Permit2, gas-sponsored) second', scheme: 'exact', unit: 'one record read', reads: { resolver: 'tools/call resolve_issuer · get_signal · get_record · list_events_since · list_aliases; GET /record · /events · /signal', nodes: 'the same five tools and GET paths on each node door', eco: 'GET /eco.json · /isin/{ISIN} · /ticker/{EXCHANGE:SYMBOL}' }, free: 'list_nodes, tools/list, initialize, pages, machine files; receipts are read free', free_per_agent_per_day_default: 100 };
const enc = new TextEncoder();
const b64 = o => btoa(unescape(encodeURIComponent(JSON.stringify(o))));
const unb64 = s => JSON.parse(decodeURIComponent(escape(atob(s))));
const b64uBuf = buf => { let s = ''; for (const c of new Uint8Array(buf)) s += String.fromCharCode(c); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const b64uStr = str => b64uBuf(enc.encode(str));
const pemDer = pem => Uint8Array.from(atob(pem.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '')), c => c.charCodeAt(0));
const clean = s => String(s || '').replace(/^﻿/, '').trim();
export const freePerDay = env => { const n = parseInt(env.X402_FREE_PER_DAY || '100', 10); return isNaN(n) ? 100 : n; };
const day = () => new Date().toISOString().slice(0, 10);
async function hex(s) { return [...new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode(s)))].map(b => b.toString(16).padStart(2, '0')).join(''); }
export async function agentKey(request) { return (await hex([request.headers.get('cf-connecting-ip') || '', request.headers.get('user-agent') || '', request.headers.get('x-agent-id') || ''].join('|'))).slice(0, 24); }
// sharded counters (a KV key takes one write a second): cnt:<day>:<metric>:<door>:<shard>
export async function bump(env, metric, door, n = 1) {
  if (!env.X402) return; const k = `cnt:${day()}:${metric}:${door}:${Math.floor(Math.random() * 4)}`;   // the count rides in the key's metadata, so a listing reads it
  try { const v = parseInt((await env.X402.get(k)) || '0', 10) + n; await env.X402.put(k, String(v), { expirationTtl: 400 * 86400, metadata: { v } }); } catch (e) { }
  if (metric === 'settled') for (const tk of ['tot:settled', `tot:settled:${door}`]) { try { const v = parseInt((await env.X402.get(tk)) || '0', 10) + n; await env.X402.put(tk, String(v)); } catch (e) { } }
}
export function requirements(env, resource, description) {
  return { scheme: 'exact', network: NETWORK.caip2, amount: PRICE, maxAmountRequired: PRICE, asset: NETWORK.usdc, payTo: clean(env.X402_PAYTO), maxTimeoutSeconds: 120, resource, description, mimeType: 'application/json', extra: { name: NETWORK.name, version: '2' } };
}
export function paymentRequired(env, resource, description, error, door) {
  const acc = accepts(env, resource, description);
  const body = { x402Version: 2, error: error || 'The x402 offer, as asked: every read is free (no rationing, CEO ruling 2026-10-24); to pay by choice, one record read settles in USDC or Open USD on Base', accepts: acc, resource: { url: resource, description, mimeType: 'application/json' }, extensions: acc.length > 1 ? { ...EIP2612_GAS_SPONSORING } : {}, door, pricing: 'https://allooloo.ai/x402/pricing.json' };
  return new Response(JSON.stringify(body, null, 1), { status: 402, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'PAYMENT-REQUIRED': b64(body), 'access-control-allow-origin': '*', 'access-control-expose-headers': 'PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, X-RCO-Decision-Id', 'X-Allooloo-x402': 'offer' } });
}
async function cdpJwt(env, method, host, path) {
  const id = clean(env.CDP_API_KEY_ID), secret = clean(env.CDP_API_KEY_SECRET); if (!id || !secret) return null;
  const now = Math.floor(Date.now() / 1000); const nonce = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
  const claims = { sub: id, iss: 'cdp', aud: ['cdp_service'], nbf: now, exp: now + 120, uris: [`${method} ${host}${path}`] };
  let alg, key, sigAlg;
  if (secret.includes('BEGIN')) { alg = 'ES256'; key = await crypto.subtle.importKey('pkcs8', pemDer(secret), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']); sigAlg = { name: 'ECDSA', hash: 'SHA-256' }; }
  else { alg = 'EdDSA'; const raw = Uint8Array.from(atob(secret), c => c.charCodeAt(0)); const seed = raw.slice(0, 32); const pkcs8 = new Uint8Array([0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20, ...seed]); key = await crypto.subtle.importKey('pkcs8', pkcs8, { name: 'Ed25519' }, false, ['sign']); sigAlg = { name: 'Ed25519' }; }
  const h = b64uStr(JSON.stringify({ alg, kid: id, typ: 'JWT', nonce })); const p = b64uStr(JSON.stringify(claims));
  const sig = await crypto.subtle.sign(sigAlg, key, enc.encode(`${h}.${p}`));
  return `${h}.${p}.${b64uBuf(sig)}`;
}
async function facilitator(env, path, body) {
  const base = clean(env.CDP_API_KEY_ID) && clean(env.CDP_API_KEY_SECRET) ? NETWORK.facilitator : NETWORK.fallback; const u = new URL(base + path);
  const h = { 'content-type': 'application/json', accept: 'application/json' };
  if (u.hostname.endsWith('coinbase.com')) { const jwt = await cdpJwt(env, 'POST', u.hostname, u.pathname); if (jwt) h['Authorization'] = 'Bearer ' + jwt; }
  const r = await fetch(u.toString(), { method: 'POST', headers: h, body: JSON.stringify(body), signal: AbortSignal.timeout(30000) });
  let j = null; try { j = await r.json(); } catch (e) { j = { error: 'facilitator answered ' + r.status }; }
  return { status: r.status, body: j };
}
// decide(): the gate for one paid-eligible request. Returns { pass: true, free: true } inside the free tier, { pass: true, paid: {...} } after a valid
// payment (settle later with settle()), or { response } (the 402 offer).
export async function decide(request, env, opts) {
  const { door, resource, description, units = 1 } = opts; const url = new URL(request.url);
  if (!clean(env.X402_PAYTO)) return { pass: true, free: true, note: 'receiver not configured' };
  const sig = request.headers.get('PAYMENT-SIGNATURE') || request.headers.get('X-PAYMENT');
  if (sig) {
    let payload; try { payload = unb64(sig); } catch (e) { await bump(env, 'offers', door); return { response: paymentRequired(env, resource, description, 'PAYMENT-SIGNATURE is not base64 JSON', door) }; }
    const offered = accepts(env, resource, description); const chosen = String((payload.accepted && payload.accepted.asset) || '').toLowerCase();
    const req = offered.find(a => a.asset.toLowerCase() === chosen) || offered[0];   // the door settles the entry the payer chose
    const v = await facilitator(env, '/verify', { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req });
    if (!(v.body && v.body.isValid)) { await bump(env, 'offers', door); return { response: paymentRequired(env, resource, description, 'payment not valid: ' + ((v.body && (v.body.invalidReason || v.body.error)) || v.status), door) }; }
    return { pass: true, paid: { payload, req } };
  }
  const ask = request.headers.get('x402-pay') === '1' || url.searchParams.get('x402') === '1';
  // CEO ruling 2026-10-24 (DAY ORDER 5): no x402 rationing — every read is free for every agent, house or outside, with no count per agent; the offer is
  // answered only to an agent that asks for it (x402-pay: 1 or ?x402=1), and a payment it sends is verified, settled and carried on the receipt.
  if (!ask) { if (env.X402) await bump(env, 'free', door, units); return { pass: true, free: true }; }
  await bump(env, 'offers', door);
  return { response: paymentRequired(env, resource, description, ask ? 'the offer, asked for' : null, door) };
}
export async function settle(env, paid, door) {
  const s = await facilitator(env, '/settle', { x402Version: paid.payload.x402Version || 2, paymentPayload: paid.payload, paymentRequirements: paid.req });
  const settled = !!(s.body && (s.body.success || s.body.transaction || s.body.txHash)); const tx = s.body && (s.body.transaction || s.body.txHash || null);
  const payer = (s.body && s.body.payer) || (paid.payload.payload && paid.payload.payload.authorization && paid.payload.payload.authorization.from) || null;
  if (settled) { await bump(env, 'settled', door); try { await env.X402.put('last', JSON.stringify({ door, transaction: tx, network: NETWORK.caip2, at: new Date().toISOString() })); } catch (e) { } }
  const pr = { x402Version: 2, success: settled, transaction: tx, network: NETWORK.caip2, asset: paid.req.asset, payer, errorReason: settled ? null : (s.body && (s.body.errorReason || s.body.error)) || null };
  return { settled, tx, payer, header: b64(pr), pr };
}
export function paymentDoor(env) {
  return { protocol: 'x402', version: 2, network: NETWORK.caip2, asset: env.X402_PAYTO_OUSD ? 'USDC, OUSD' : 'USDC', asset_address: NETWORK.usdc, ousd_address: env.X402_PAYTO_OUSD ? OUSD.asset : undefined, scheme: 'exact', facilitator: 'Coinbase CDP', free_reads_per_agent_per_day: 'unlimited', rationing: 'none — every read is free for every agent (CEO ruling 2026-10-24); pay only if you choose to: ask for the offer, then pay',
    ask_for_the_offer: 'header x402-pay: 1 (or ?x402=1 on GET)', pay_with: 'PAYMENT-SIGNATURE header (x402 v2) on the same call', pricing: 'https://allooloo.ai/x402/pricing.json', settlements: 'https://allooloo.ai/x402/settled.json', receipts: 'a paid read carries its RCO receipt (decision_id) — https://mcp.rco-a2a.ai/mcp' };
}
// counts by day and door (for allooloo.ai/x402 and the digest)
export async function counts(env, days = 14) {
  const out = { settled: 0, by_day: {}, free_by_day: {}, offers_by_day: {}, by_door: {}, last: null, as_of: new Date().toISOString(), network: NETWORK.caip2, asset: 'USDC', note: 'counts only, never amounts' };
  if (!env.X402) return out;
  try {
    for (let i = 0; i < days; i++) { const d = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10); let cursor;
      do { const l = await env.X402.list({ prefix: `cnt:${d}:`, cursor }); for (const k of l.keys) { const [, , metric] = k.name.split(':'); const v = (k.metadata && k.metadata.v) || 0;
        const tgt = metric === 'settled' ? out.by_day : metric === 'free' ? out.free_by_day : out.offers_by_day; tgt[d] = (tgt[d] || 0) + v; } cursor = l.list_complete ? null : l.cursor; } while (cursor); }
    out.settled = parseInt((await env.X402.get('tot:settled')) || '0', 10);
    const tl = await env.X402.list({ prefix: 'tot:settled:' }); for (const k of tl.keys) out.by_door[k.name.slice(12)] = parseInt((await env.X402.get(k.name)) || '0', 10);
    out.last = await env.X402.get('last', 'json');
  } catch (e) { out.error = 'register unavailable'; }
  return out;
}

// X402-A-01 rider: a facilitator relay for the RCO door (no CDP key on that door). It verifies and settles only payments to the Allooloo wallets
// (payTo = X402_PAYTO or X402_PAYTO_OUSD) on Base, so it has no use to anyone but a payer paying us.
export async function relay(request, env, path) {
  let b; try { b = await request.json(); } catch (e) { return new Response('{"error":"bad json"}', { status: 400 }); }
  const rq = b && b.paymentRequirements, mine = [clean(env.X402_PAYTO), clean(env.X402_PAYTO_OUSD)].filter(Boolean).map(x => x.toLowerCase());
  if (!rq || rq.network !== NETWORK.caip2 || !mine.includes(String(rq.payTo || '').toLowerCase())) return new Response('{"error":"relay settles payments to the Allooloo wallets only"}', { status: 403, headers: { 'content-type': 'application/json' } });
  const r = await facilitator(env, path, b); return new Response(JSON.stringify(r.body), { status: r.status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });
}
