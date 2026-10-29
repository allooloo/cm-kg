// cmkg-node-gate — RCO-A-01 + X402-A-01 (DAY ORDER 3, 2026-10-24). A route Worker on mcp.<cc>-cm-kg.ai/* (the twelve node doors). Every request passes to
// the node's own Container App unchanged (same hostname, same region, same bytes); the gate adds two things only:
//  · the Record of Cleared Orders — a tools/call of resolve_issuer from an outside caller (an ISIN resolved on this node's register) is given a decision_id,
//    answers with a `receipt` block and the header X-RCO-Decision-Id, and its receipt is written to mcp.rco-a2a.ai after the answer (ctx.waitUntil);
//  · x402 — record reads (tools/call resolve_issuer · get_record · list_events_since · list_aliases; GET /record · /events) are free inside the per-agent
//    free for every agent (no rationing, CEO ruling 2026-10-24) and answer the x402 v2 offer only when asked; a paid read is verified, served, settled, and its receipt names the settlement.
// /mcp.json and /.well-known/mcp.json carry the payment door, the routing block and the receipt door. Allooloo's own renderers pass untouched.
// The apex reaches the nodes on their Container Apps origins, not through here, and meters and writes its own receipts.
import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';
import { decide, settle, paymentDoor } from './x402gate.js';
import { signRecord, signEvents, sigRef } from './cmrsign.js';   // NODE-SIGN-01
const JWKS = { keys: [{"kty": "OKP", "crv": "Ed25519", "x": "cqa-iPbl2AD_Yw3bIxQCPAmzSiBemxU6ajL2nI1w9QA", "kid": "allooloo-cmr-2026-10", "alg": "EdDSA", "use": "sig"}, {"kty": "OKP", "crv": "Ed25519", "x": "N-knqz1-H9xwNGvOS0Eu7CDrmdPgzFjCgvExLJt2lQw", "kid": "allooloo-rco-2026-10", "alg": "EdDSA", "use": "sig"}] };
const signs = (env, node) => { const s = String(env.SIGN_NODES || '').trim(); return s === 'all' || s.split(/[ ,]+/).includes(node.split('-')[0]); };
// DAY ORDER 5 ZONES-01 (2026-10-24): the door name rule of record — a market with its own zone answers on mcp.<cc>-cm-kg.ai (card agent.<cc>-cm-kg.ai);
// the European nodes answer under the EU regime zone, <cc>.eu-cm-kg.ai (door /mcp, card /.well-known/agent-card.json). Receipts name the door they were read on.
const nodeOf = h => { const m = /^([a-z]{2})\.eu-cm-kg\.ai$/.exec(h); return m ? `${m[1]}-cm-kg` : h.replace(/^(mcp|agent)\./, '').replace(/\.ai$/, ''); };
const VERSION = '2026-10-27.1';   // .1 = SHELF-01 fix: every event line served (list_events_since, GET /events/) carries its own signature
// prior:   // .1 = DOORS-02: the 402 offer signed (kid allooloo-cmr-2026-10)   // 2026-10-24.4 = DAY ORDER 5: EU regime zone doors   // .3 = NODE-SIGN-01: records and resolve summaries signed (kid allooloo-cmr-2026-10)
const ISIN = /^[A-Z]{2}[A-Z0-9]{9}\d$/, LEI = /^[A-Z0-9]{18}[0-9]{2}$/;
const INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer|issuerwire-stores)/;   // ISSUERWIRE-03 (DAY ORDER 5): Issuerwire's nightly store read is Allooloo's own (it was metered from 2026-10-24 and refused past the free tier)
const PAID_TOOLS = ['resolve_issuer', 'get_record', 'list_events_since', 'list_aliases', 'get_timeline', 'list_events', 'get_score'];   // SHELF-01: the shelf's door tools are reads at the standing rate
const ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: 'https://mcp.getissuer.ai/mcp' }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-a2a.ai/mcp' }];

async function receiptFor(d, node, rh, door) {
  const ident = String((d.args && d.args.identifier) || '').trim(), up = ident.toUpperCase();
  const type = ISIN.test(up) ? 'isin' : LEI.test(up) ? 'lei' : /^[a-z]{2}-cm-kg\//i.test(ident) ? 'cmr' : 'ticker';
  const m = (d.sc && d.sc.matches) || [];
  const records = [];
  for (const x of m.slice(0, 6)) records.push({ url: x.record_url, as_of: x.as_of || null, sha256: await sha256(x), signature: sigRef(x) });
  if (!records.length) records.push({ url: `${door}/nodes.json`, as_of: rh.asOf || null, sha256: null, signature: null });
  const body = { decision_id: d.id, object: { type, id: ident.slice(0, 80) }, actor_class: 'ai-agent (MCP client)', rule: { id: `${node} register (the node's current roster)`, version: `door ${rh.version || '?'} · as_of ${rh.asOf || '?'}` },
    records_read: records.filter(r => r.url), signal: m.length ? 'ACM-200' : 'ACM-404', decided_at: d.at, issuing_door: `${door}/mcp` };
  if (d.settlement) body.settlement = d.settlement;
  return body;
}
const withPay = (resp, pay) => { if (!pay) return resp; const h = new Headers(resp.headers); h.set('PAYMENT-RESPONSE', pay.header); h.set('X-PAYMENT-RESPONSE', pay.header); h.set('access-control-expose-headers', (h.get('access-control-expose-headers') || '') + ', PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, PAYMENT-REQUIRED, X-RCO-Decision-Id'); return new Response(resp.body, { status: resp.status, headers: h }); };
// DOORS-02 (2026-10-26): the 402 offer is signed like a record (kid allooloo-cmr-2026-10, detached JWS over the canonical body without `signature`, keyring
// allooloo.ai/.well-known/jwks.json); the PAYMENT-REQUIRED header carries the same signed body, base64.
async function signOffer(env, node, resp) {
  if (!resp || resp.status !== 402 || !signs(env, node)) return resp;
  let body; try { body = await resp.clone().json(); } catch (e) { return resp; }
  const sb = await signRecord(env, body); if (!sb.signature) return resp;
  const txt = JSON.stringify(sb, null, 1), h = new Headers(resp.headers); h.delete('content-length');
  const b64 = btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(sb)))); h.set('PAYMENT-REQUIRED', b64); h.set('X-CMR-Signed', sb.signature.kid); h.set('X-Node-Gate', VERSION);
  return new Response(txt, { status: 402, headers: h });
}
const settleFail = pay =>new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } });

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url); const p = url.pathname.replace(/\/+$/, '') || '/';
    const node = nodeOf(url.hostname); const DOOR = `https://${url.hostname}`;   // DAY ORDER 5: <cc>.eu-cm-kg.ai and agent.<cc>-cm-kg.ai name their node too
    const internal = INTERNAL.test(request.headers.get('user-agent') || '');
    if (request.method === 'GET' && p === '/.well-known/jwks.json') return new Response(JSON.stringify(JWKS, null, 1), { headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=3600', 'access-control-allow-origin': '*' } });
    if (request.method === 'GET' && (p === '/mcp.json' || p === '/.well-known/mcp.json')) {
      const o = await fetch(new Request(url.origin + '/mcp.json', { headers: request.headers })); let j = null; try { j = await o.json(); } catch (e) { return o; }
      return new Response(JSON.stringify({ ...j, payment: paymentDoor(env), routing: ROUTING, receipts: { door: 'https://mcp.rco-a2a.ai/mcp', keyring: 'https://mcp.getissuer.ai/.well-known/jwks.json', note: 'every resolve_issuer on this door leaves an RCO receipt; the answer carries its decision_id' } }, null, 1),
        { status: 200, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', 'X-Node-Gate': VERSION } });
    }
    if (request.method === 'GET' && /^\/(record|events)\//.test(p)) {
      const g = internal ? { pass: true } : await decide(request, env, { door: node, resource: `https://${url.hostname}${url.pathname}`, description: `One record read on the ${node} node door (Allooloo Technologies Corp.)` });
      if (g.response) return signOffer(env, node, g.response);
      let resp = await fetch(request);
      if (resp.ok && /^\/events\//.test(p) && signs(env, node) && (resp.headers.get('content-type') || '').includes('json')) { const ev = await signEvents(env, await resp.json()); const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-CMR-Signed', 'allooloo-cmr-2026-10'); resp = new Response(JSON.stringify(ev), { status: 200, headers: h }); }
      if (resp.ok && /^\/record\//.test(p) && signs(env, node) && (resp.headers.get('content-type') || '').includes('json')) { const rec = await signRecord(env, await resp.json()); const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-CMR-Signed', 'allooloo-cmr-2026-10'); resp = new Response(JSON.stringify(rec), { status: 200, headers: h }); }
      if (!g.paid || !resp.ok) return resp;
      const pay = await settle(env, g.paid, node); return pay.settled ? withPay(resp, pay) : settleFail(pay);
    }
    if (request.method !== 'POST' || p !== '/mcp') return fetch(request);
    const raw = await request.text();
    let msg = null; try { msg = JSON.parse(raw); } catch (e) { return fetch(new Request(request, { body: raw })); }
    const list = Array.isArray(msg) ? msg : [msg];
    const units = internal ? 0 : list.filter(x => x && x.method === 'tools/call' && x.params && PAID_TOOLS.includes(x.params.name)).length;
    const g = units ? await decide(request, env, { door: node, resource: `https://${url.hostname}/mcp`, description: `One record read on the ${node} node door (Allooloo Technologies Corp.)`, units }) : { pass: true };
    if (g.response) return signOffer(env, node, g.response);
    const resp = await fetch(new Request(request, { body: raw }));
    if (!resp.ok || !(resp.headers.get('content-type') || '').includes('application/json')) return resp;
    let pay = null; if (g.paid) { pay = await settle(env, g.paid, node); if (!pay.settled) return settleFail(pay); }
    const calls = internal ? [] : list.filter(x => x && x.method === 'tools/call' && x.params && x.params.name === 'resolve_issuer');
    const recCalls = signs(env, node) ? list.filter(x => x && x.method === 'tools/call' && x.params && (x.params.name === 'get_record' || x.params.name === 'resolve_issuer' || x.params.name === 'list_events_since' || x.params.name === 'get_timeline' || x.params.name === 'list_events')) : [];
    if (!calls.length && !recCalls.length) return withPay(resp, pay);
    const text = await resp.text(); let j; try { j = JSON.parse(text); } catch (e) { return withPay(new Response(text, { status: resp.status, headers: resp.headers }), pay); }
    const arr = Array.isArray(j) ? j : [j], decisions = [], at = new Date().toISOString();
    for (const r of arr) {
      const rc = recCalls.find(c => c.id === r.id);
      if (rc && r.result) { let sc = r.result.structuredContent; if (!sc) { try { sc = JSON.parse(r.result.content[0].text); } catch (e) { sc = null; } }
        if (sc && !sc.error) { if (rc.params.name === 'get_record') sc = await signRecord(env, sc); else if (['list_events_since', 'get_timeline', 'list_events'].includes(rc.params.name)) sc = await signEvents(env, sc); else if (Array.isArray(sc.matches)) sc.matches = await Promise.all(sc.matches.map(x => signRecord(env, x))); r.result.structuredContent = sc; r.result.content = [{ type: 'text', text: JSON.stringify(sc) }]; } }
      const call = calls.find(c => c.id === r.id); if (!call || !r.result) continue;
      let sc = r.result.structuredContent; if (!sc) { try { sc = JSON.parse(r.result.content[0].text); } catch (e) { continue; } }
      const id = decisionId(); sc.receipt = receiptLinks(id); r.result.structuredContent = sc; r.result.content = [{ type: 'text', text: JSON.stringify(sc) }];
      decisions.push({ id, args: call.params.arguments || {}, sc, at, settlement: pay ? { network: pay.pr.network, transaction: pay.tx } : undefined });
    }
    if (!decisions.length) { const h0 = new Headers(resp.headers); h0.delete('content-length'); return withPay(new Response(JSON.stringify(Array.isArray(j) ? arr : arr[0]), { status: resp.status, headers: h0 }), pay); }
    const rh = { version: resp.headers.get('x-cmr-version'), asOf: resp.headers.get('x-cmr-as-of') };
    ctx.waitUntil(Promise.all(decisions.map(async d => writeReceipt(env, await receiptFor(d, node, rh, DOOR)))));
    const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-RCO-Decision-Id', decisions.map(d => d.id).join(', ')); h.set('X-Node-Gate', VERSION);
    h.set('access-control-expose-headers', (resp.headers.get('access-control-expose-headers') || '') + ', X-RCO-Decision-Id');
    return withPay(new Response(JSON.stringify(Array.isArray(j) ? arr : arr[0]), { status: resp.status, headers: h }), pay);
  }
};
