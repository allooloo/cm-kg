// cmkg-node-gate — RCO-A-01 + X402-A-01 (DAY ORDER 3, 2026-10-24). A route Worker on mcp.<cc>-cm-kg.ai/* (the twelve node doors). Every request passes to
// the node's own Container App unchanged (same hostname, same region, same bytes); the gate adds two things only:
//  · the Record of Cleared Orders — a tools/call of resolve_issuer from an outside caller (an ISIN resolved on this node's register) is given a decision_id,
//    answers with a `receipt` block and the header X-RCO-Receipt-Id; its v1 receipt is written to mcp.rco-records.ai before the answer (RCO-MOVE);
//  · x402 — record reads (tools/call resolve_issuer · get_record · list_events_since · list_aliases; GET /record · /events) are free inside the per-agent
//    free for every agent (no rationing, CEO ruling 2026-10-24) and answer the x402 v2 offer only when asked; a paid read is verified, served, settled, and its receipt names the settlement.
// /mcp.json and /.well-known/mcp.json carry the payment door, the routing block and the receipt door. Allooloo's own renderers pass untouched.
// The apex reaches the nodes on their Container Apps origins, not through here, and meters and writes its own receipts.
import { sha256, receiptLinks, writeReceipt, answerHash } from './rco.js';
import { decide, settle, paymentDoor } from './x402gate.js';
import { signRecord, signEvents, sigRef } from './cmrsign.js';   // NODE-SIGN-01
import { bookPath, serveBook, cardWithBook, ECO_JWK_PUBLIC } from './book.js';   // BOOK-04: the chapter under /book/, from the Book mirror
import { AIO_TOOL, getOrderability, cardWithTool, withListing } from './aio.js';   // AIO-01: the orderability door
import { stampClass } from './stampclass.js';   // BOOK-05: instrument_class on the record (schema v0.2), stamped before signing
import { TM_NAMES, TM_READS, TM_TOOLS, TM_JWK_PUBLIC, tmCall, tmSkills } from './tm.js';   // TMKT-02: the Target Market door (read and file) on every node door
import { ASOF_NAME, ASOF_TOOL, getAsOf, asofLine, asofLlms, asofSkill, ASOF_PAGE, ASOF_MCP } from './asof.js';   // ASOF-01: get_as_of, the point-in-time door, on every node door
const JWKS = { keys: [ECO_JWK_PUBLIC, {"kty": "OKP", "crv": "Ed25519", "x": "cqa-iPbl2AD_Yw3bIxQCPAmzSiBemxU6ajL2nI1w9QA", "kid": "allooloo-cmr-2026-10", "alg": "EdDSA", "use": "sig"}, {"kty": "OKP", "crv": "Ed25519", "x": "N-knqz1-H9xwNGvOS0Eu7CDrmdPgzFjCgvExLJt2lQw", "kid": "allooloo-rco-2026-10", "alg": "EdDSA", "use": "sig"}, TM_JWK_PUBLIC] };   // TMKT-02: + the Target Market key (kid allooloo-tm-2026-11)
const signs = (env, node) => { const s = String(env.SIGN_NODES || '').trim(); return s === 'all' || s.split(/[ ,]+/).includes(node.split('-')[0]); };
// DAY ORDER 5 ZONES-01 (2026-10-24): the door name rule of record — a market with its own zone answers on mcp.<cc>-cm-kg.ai (card agent.<cc>-cm-kg.ai);
// the European nodes answer under the EU regime zone, <cc>.eu-cm-kg.ai (door /mcp, card /.well-known/agent-card.json). Receipts name the door they were read on.
const nodeOf = h => { const m = /^([a-z]{2})\.eu-cm-kg\.ai$/.exec(h); return m ? `${m[1]}-cm-kg` : h.replace(/^(mcp|agent)\./, '').replace(/\.ai$/, ''); };
const VERSION = '2026-11-05.1';   // .1 = ASOF-01: get_as_of answered here (the sealed vintage via the door's own get_record as_of; signed kid allooloo-cmr-2026-10; receipted with the node as writer); on tools/list, the card, the page, llms.txt, facts.json, mcp.json; was 2026-11-02.4
const VERSION_PRIOR_ASOF01 = '2026-11-02.4';   // .4 = TMKT-04: get_target_market carries tm-verify's drift marks; outcomes stamp AIO-10060 v1.2; was 2026-11-02.3 —   // .3 = TMKT-03: get_orderability carries the discharge (the statement on file against the Book's manufacturer_evidence_accepted; the signal never changed); R-039 on the wire (the offer only when asked); the filing receipt record beside each statement; was 2026-11-02.2 —   // .2 = TMKT-02 fix: the store is the container target-market (blobs tm/<subject>/v<N>.json; tm alone is under Azure's three-character minimum); was 2026-11-02.1 —   // .1 = TMKT-02: get_target_market · list_target_market_versions · verify_target_market · file_target_market answered here (tm.js; the node's pond, container tm); the descriptor's payment.page (data-paygo.ai)
const VERSION_PRIOR_TMKT02 = '2026-11-01.4';   // .4 = DEFECTS-01: ACM-404 on the category lists the categories the chapter names (evidence_gaps); the caller key on get_orderability receipts
const VERSION_PRIOR_DEFECTS01 = '2026-11-01.3';   // .3 = BOOK-08: the product-scope test reads the scope bridge (product_scope cfi_categories, ISO 10962)
const VERSION_PRIOR_BOOK08 = '2026-11-01.2';   // .2 = BOOK-07: the gate rule, final (scope only; conditions carried, firm-held where no evidence; regime exclusion = ACM-403)   // .2 = BOOK-07: the gate rule, final (scope only; conditions carried, firm-held where no evidence; regime exclusion = ACM-403)
const VERSION_PRIOR_BOOK07 = '2026-11-01.1';   // .1 = BOOK-06: the gate rule (distribution_conditions + the category block; the rest named, firm-held gaps) · instrument_class from the CFI (ISO 10962)
const VERSION_PRIOR_BOOK06 = '2026-10-31.4';   // .4 = get_orderability outcomes stamp AIO-10060 v1.1
const VERSION_PRIOR_ZONES04 = '2026-10-31.3';   // .3 = BOOK-05: records carry instrument_class (schema v0.2); get_orderability tests product_scope against it
const VERSION_PRIOR_BOOK05 = '2026-10-31.2';   // .2 = AIO-01: get_orderability answered here (AIO-10060 §7.1 outcome, signed allooloo-eco-2026-10, receipted with the node as writer); listed on tools/list, the card, the page, llms.txt, facts.json
const VERSION_PRIOR_AIO01 = '2026-10-31.1';   // .1 = BOOK-04: /book/ (manifest + five sections, signed allooloo-eco-2026-10), the card's book link, the ECO key in the door keyring
const VERSION_PRIOR_BOOK04 = '2026-10-30.2';   // .2 = RCO-03: caller (RCO-Key header or x402 payer) on every receipt · .1 = RCO-MOVE: v1 receipts on mcp.rco-records.ai, written before the answer, answer_hash on every write
const VERSION_PRIOR = '2026-10-27.1';   // .1 = SHELF-01 fix: every event line served (list_events_since, GET /events/) carries its own signature
// prior:   // .1 = DOORS-02: the 402 offer signed (kid allooloo-cmr-2026-10)   // 2026-10-24.4 = DAY ORDER 5: EU regime zone doors   // .3 = NODE-SIGN-01: records and resolve summaries signed (kid allooloo-cmr-2026-10)
const ISIN = /^[A-Z]{2}[A-Z0-9]{9}\d$/, LEI = /^[A-Z0-9]{18}[0-9]{2}$/;
const INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer|issuerwire-stores)/;   // ISSUERWIRE-03 (DAY ORDER 5): Issuerwire's nightly store read is Allooloo's own (it was metered from 2026-10-24 and refused past the free tier)
const PAID_TOOLS = ['resolve_issuer', 'get_record', 'list_events_since', 'list_aliases', 'get_timeline', 'list_events', 'get_score'];   // SHELF-01: the shelf's door tools are reads at the standing rate
const ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: 'https://mcp.getissuer.ai/mcp' }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-records.ai/mcp' }];

async function receiptFor(d, node, rh, door) {
  const ident = String((d.args && d.args.identifier) || '').trim(), up = ident.toUpperCase();
  const type = ISIN.test(up) ? 'isin' : LEI.test(up) ? 'lei' : /^[a-z]{2}-cm-kg\//i.test(ident) ? 'cmr' : 'ticker';
  const m = (d.sc && d.sc.matches) || [];
  const records = [];
  for (const x of m.slice(0, 6)) records.push({ url: x.record_url, as_of: x.as_of || null, sha256: await sha256(x), signature: sigRef(x) });
  if (!records.length) records.push({ url: `${door}/nodes.json`, as_of: rh.asOf || null, sha256: null, signature: null });
  const body = { answer_hash: d.answer_hash, object: { type, id: ident.slice(0, 80) }, actor_class: 'ai-agent (MCP client)', rule: { id: `${node} register (the node's current roster)`, version: `door ${rh.version || '?'} · as_of ${rh.asOf || '?'}` },
    records_read: records.filter(r => r.url), signal: m.length ? 'ACM-200' : 'ACM-404', decided_at: d.at, issuing_door: `${door}/mcp` };
  if (d.settlement) body.settlement = d.settlement;
  if (d.caller_key) body.caller_key = d.caller_key; else if (d.payer) body.caller = 'x402:' + String(d.payer).toLowerCase();   // RCO-03: caller = the customer key (door hashes its id) or the x402 wallet handle
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

// TMKT-02: the node door's card, page, llms.txt, facts.json and descriptor name the four Target Market tools beside get_orderability
async function tmCard(resp, door) {
  if (!resp.ok || !(resp.headers.get('content-type') || '').includes('json')) return resp;
  let c; try { c = await resp.clone().json(); } catch (e) { return resp; }
  if (!c || typeof c !== 'object' || Array.isArray(c)) return resp;
  const skills = (Array.isArray(c.skills) ? c.skills.filter(s => s && !TM_NAMES.includes(s.id)) : []).concat(tmSkills(door));
  const h = new Headers(resp.headers); h.delete('content-length');
  const sk2 = skills.filter(s => s && s.id !== ASOF_NAME).concat([asofSkill(door)]);   // ASOF-01
  return new Response(JSON.stringify({ ...c, skills: sk2, target_market: { door: `${door}/mcp`, tools: TM_NAMES, page: 'https://gettargetmarket.ai/', router: 'https://mcp.gettargetmarket.ai/mcp (routes by subject to the home node)' }, as_of: { door: `${door}/mcp`, tool: ASOF_NAME, page: ASOF_PAGE, router: `${ASOF_MCP} (routes by issuer to the owning node)` } }), { status: resp.status, headers: h });
}
async function tmListing(resp, p, door) {
  const ct = resp.headers.get('content-type') || ''; if (!resp.ok) return resp;
  let t = await resp.text(); const h = new Headers(resp.headers); h.delete('content-length');
  if (p === '/facts.json' && ct.includes('json')) { try { const j = JSON.parse(t); if (Array.isArray(j.tools)) for (const n of TM_NAMES) if (!j.tools.includes(n)) j.tools.push(n); j.target_market = { door: `${door}/mcp`, tools: TM_NAMES, page: 'https://gettargetmarket.ai/', store: "this node's own pond, container target-market (tm/<subject>/v<N>.json)" }; if (Array.isArray(j.tools) && !j.tools.includes(ASOF_NAME)) j.tools.push(ASOF_NAME); j.as_of = { door: `${door}/mcp`, tool: ASOF_NAME, page: ASOF_PAGE, store: "the node's sealed vintage (backfill/replay/<year>/), read through get_record as_of" }; t = JSON.stringify(j); } catch (e) {} }   // ASOF-01
  else if (p === '/' && ct.includes('html')) t = t.replace(/(<p>Orderability door:[\s\S]*?<\/p>)/, `$1<p>Target Market door: <a href="${door}/mcp">${door}/mcp</a> — ${TM_NAMES.join(' · ')}: the manufacturer's target market statement for a product listed on this node, stored here under tm/, signed by the node and receipted at mcp.rco-records.ai (<a href="https://gettargetmarket.ai/">gettargetmarket.ai</a>).</p>${asofLine(door)}`);   // ASOF-01: the As Of line after the Target Market line
  else if (p === '/llms.txt') t = t.replace(/^(Tools: .*)$/m, `$1, ${TM_NAMES.join(', ')} (the manufacturer's target market statement for a product listed on this node: read, list, verify, file — https://gettargetmarket.ai/), ${asofLlms()}`);   // ASOF-01
  return new Response(t, { status: resp.status, headers: h });
}
const tmDescTools = tools => Array.isArray(tools) ? tools.concat(TM_TOOLS.concat([ASOF_TOOL]).filter(t => !tools.find(x => x && x.name === t.name)).map(t => ({ name: t.name, description: t.description }))) : tools;   // ASOF-01: + get_as_of
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url); const p = url.pathname.replace(/\/+$/, '') || '/';
    const node = nodeOf(url.hostname); const DOOR = `https://${url.hostname}`;   // DAY ORDER 5: <cc>.eu-cm-kg.ai and agent.<cc>-cm-kg.ai name their node too
    const internal = INTERNAL.test(request.headers.get('user-agent') || '');
    const RDOOR = url.hostname.startsWith('agent.') ? `https://mcp.${url.hostname.slice(6)}` : DOOR;   // BOOK-04: the card host names its record door
    if (bookPath(p)) return serveBook(request, env, ctx, node, RDOOR);
    if (request.method === 'GET' && p === '/.well-known/agent-card.json') return tmCard(await cardWithTool(await cardWithBook(await fetch(request), RDOOR), RDOOR), RDOOR);   // AIO-01: the card lists get_orderability · TMKT-02: and the four Target Market tools
    if (request.method === 'GET' && (p === '/' || p === '/llms.txt' || p === '/facts.json') && !url.hostname.startsWith('agent.')) return tmListing(await withListing(await fetch(request), p, RDOOR), p, RDOOR);
    if (request.method === 'GET' && p === '/.well-known/jwks.json') return new Response(JSON.stringify(JWKS, null, 1), { headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=3600', 'access-control-allow-origin': '*' } });
    if (request.method === 'GET' && (p === '/mcp.json' || p === '/.well-known/mcp.json')) {
      const o = await fetch(new Request(url.origin + '/mcp.json', { headers: request.headers })); let j = null; try { j = await o.json(); } catch (e) { return o; }
      return new Response(JSON.stringify({ ...j, tools: tmDescTools(j.tools), payment: paymentDoor(env), routing: ROUTING, receipts: { door: 'https://mcp.rco-records.ai/mcp', keyring: 'https://rco-records.ai/.well-known/jwks.json', note: 'every resolve_issuer on this door leaves an RCO receipt; the answer carries its id' } }, null, 1),
        { status: 200, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', 'X-Node-Gate': VERSION } });
    }
    if (request.method === 'GET' && /^\/(record|events)\//.test(p)) {
      const g = internal ? { pass: true } : await decide(request, env, { door: node, resource: `https://${url.hostname}${url.pathname}`, description: `One record read on the ${node} node door (Allooloo Technologies Corp.)` });
      if (g.response) return signOffer(env, node, g.response);
      let resp = await fetch(request);
      if (resp.ok && /^\/events\//.test(p) && signs(env, node) && (resp.headers.get('content-type') || '').includes('json')) { const ev = await signEvents(env, await resp.json()); const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-CMR-Signed', 'allooloo-cmr-2026-10'); resp = new Response(JSON.stringify(ev), { status: 200, headers: h }); }
      if (resp.ok && /^\/record\//.test(p) && signs(env, node) && (resp.headers.get('content-type') || '').includes('json')) { const rec = await signRecord(env, stampClass(await resp.json())); const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-CMR-Signed', 'allooloo-cmr-2026-10'); resp = new Response(JSON.stringify(rec), { status: 200, headers: h }); }
      if (!g.paid || !resp.ok) return resp;
      const pay = await settle(env, g.paid, node); return pay.settled ? withPay(resp, pay) : settleFail(pay);
    }
    if (request.method !== 'POST' || p !== '/mcp') return fetch(request);
    const raw = await request.text();
    let msg = null; try { msg = JSON.parse(raw); } catch (e) { return fetch(new Request(request, { body: raw })); }
    const list = Array.isArray(msg) ? msg : [msg];
    // TMKT-02: the Target Market tools are answered by the gate (it holds the node's store credential, the signing keys and the receipt writer); reads are free for every
    // agent and answer the x402 offer only when asked; verify is public; a filing is free. A call routed by the apex (user-agent Allooloo tm-router) was metered there.
    const tmCalls = list.filter(x => x && x.method === 'tools/call' && x.params && TM_NAMES.includes(x.params.name));
    if (tmCalls.length) {
      const routed = /^Allooloo tm-router/.test(request.headers.get('user-agent') || '');
      let settlement = null, tmPay = null;
      if (routed) { try { settlement = JSON.parse(request.headers.get('x-tm-settlement') || 'null'); } catch (e) { settlement = null; } }
      const units = routed || internal ? 0 : tmCalls.filter(x => TM_READS.includes(x.params.name)).length;
      if (units) {
        const g = await decide(request, env, { door: node, resource: `https://${url.hostname}/mcp`, description: `One target market statement read on the ${node} node door (Allooloo Technologies Corp.)`, units });
        if (g.response) return signOffer(env, node, g.response);
        if (g.paid) { tmPay = await settle(env, g.paid, node); if (!tmPay.settled) return settleFail(tmPay); settlement = { network: tmPay.pr.network, transaction: tmPay.tx, payer: tmPay.payer }; }
      }
      const rest = list.filter(x => !tmCalls.includes(x));
      const mine = await Promise.all(tmCalls.map(async x => { const r = await tmCall(env, ctx, request, { node, host: url.hostname, door: RDOOR, callerKey: request.headers.get('rco-key') || undefined, routed, settlement }, x.params.name, (x.params && x.params.arguments) || {}); return { jsonrpc: '2.0', id: x.id, result: { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: r.isError } }; }));
      let others = [];
      if (rest.length) { const r2 = await fetch(new Request(request, { body: JSON.stringify(Array.isArray(msg) ? rest : rest[0]) })); try { const j2 = await r2.json(); others = Array.isArray(j2) ? j2 : [j2]; } catch (e) { others = []; } }
      const all = mine.concat(others);
      const resp = new Response(JSON.stringify(Array.isArray(msg) ? all : all[0]), { status: 200, headers: { 'content-type': 'application/json', 'cache-control': 'no-store', 'access-control-allow-origin': '*', 'X-Node-Gate': VERSION,
        'X-RCO-Receipt-Id': mine.map(m => (m.result.structuredContent || {}).receipt_id).filter(Boolean).join(', '), 'access-control-expose-headers': 'X-RCO-Receipt-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' } });
      return withPay(resp, tmPay);
    }
    // ASOF-01: get_as_of is answered by the gate (the door's own get_record as_of, the node's record key, the receipt writer); free for every agent, the signed
    // HTTP 402 offer only when asked (x402-pay: 1) or paid (R-039, as get_orderability); a call routed by the router was metered there and names its settlement
    const asofCalls = list.filter(x => x && x.method === 'tools/call' && x.params && x.params.name === ASOF_NAME);
    if (asofCalls.length) {
      let asPay = null, asSettle = null; const asRouted = /^getissuer apex \(get_as_of route\)/.test(request.headers.get('user-agent') || '');
      if (asRouted) { try { asSettle = JSON.parse(request.headers.get('x-asof-settlement') || 'null'); } catch (e) { asSettle = null; } }
      if (!internal && !asRouted && (request.headers.get('x402-pay') === '1' || request.headers.get('payment-signature') || request.headers.get('x-payment'))) {
        const g = await decide(request, env, { door: node, resource: `https://${url.hostname}/mcp`, description: `One as-of record read on the ${node} node door (Allooloo Technologies Corp.)`, units: asofCalls.length });
        if (g.response) return signOffer(env, node, g.response);
        if (g.paid) { asPay = await settle(env, g.paid, node); if (!asPay.settled) return settleFail(asPay); asSettle = { network: asPay.pr.network, transaction: asPay.tx, payer: asPay.payer }; }
      }
      const rest = list.filter(x => !asofCalls.includes(x));
      const mine = await Promise.all(asofCalls.map(async x => { const r = await getAsOf(env, ctx, { node, host: url.hostname, door: RDOOR, callerKey: request.headers.get('rco-key') || undefined, payer: asSettle ? asSettle.payer : undefined, settlement: asSettle ? { network: asSettle.network, transaction: asSettle.transaction } : undefined }, (x.params && x.params.arguments) || {}); return { m: { jsonrpc: '2.0', id: x.id, result: { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: !!r.err } }, rid: r.receipt_id }; }));
      let others = [];
      if (rest.length) { const r2 = await fetch(new Request(request, { body: JSON.stringify(Array.isArray(msg) ? rest : rest[0]) })); try { const j2 = await r2.json(); others = Array.isArray(j2) ? j2 : [j2]; } catch (e) { others = []; } }
      const all = mine.map(x => x.m).concat(others);
      return withPay(new Response(JSON.stringify(Array.isArray(msg) ? all : all[0]), { status: 200, headers: { 'content-type': 'application/json', 'cache-control': 'no-store', 'access-control-allow-origin': '*', 'X-Node-Gate': VERSION,
        'X-RCO-Receipt-Id': mine.map(x => x.rid).filter(Boolean).join(', '), 'access-control-expose-headers': 'X-RCO-Receipt-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' } }), asPay);
    }
    // AIO-01: get_orderability is answered by the gate (it holds the chapter reader, the node's ECO key and the receipt writer); other calls of a batch pass to the door
    const aioCalls = list.filter(x => x && x.method === 'tools/call' && x.params && x.params.name === 'get_orderability');
    if (aioCalls.length) {
      // TMKT-03 (R-039 on the wire): free and unmetered for every agent; the HTTP 402 signed offer only when the agent asks (x402-pay: 1) or pays; a call routed by the apex was metered there
      let aioPay = null; const aioRouted = /^getissuer apex \(get_orderability route\)/.test(request.headers.get('user-agent') || '');
      if (!internal && !aioRouted && (request.headers.get('x402-pay') === '1' || request.headers.get('payment-signature') || request.headers.get('x-payment'))) {
        const g = await decide(request, env, { door: node, resource: `https://${url.hostname}/mcp`, description: `One orderability outcome on the ${node} node door (Allooloo Technologies Corp.)`, units: aioCalls.length });
        if (g.response) return signOffer(env, node, g.response);
        if (g.paid) { aioPay = await settle(env, g.paid, node); if (!aioPay.settled) return settleFail(aioPay); }
      }
      const rest = list.filter(x => !aioCalls.includes(x));
      const mine = await Promise.all(aioCalls.map(async x => { const o = await getOrderability(env, ctx, { node, host: url.hostname, door: RDOOR, callerKey: request.headers.get('rco-key') || undefined, payer: aioPay ? aioPay.payer : undefined }, (x.params && x.params.arguments) || {}); return { jsonrpc: '2.0', id: x.id, result: { content: [{ type: 'text', text: JSON.stringify(o) }], structuredContent: o, isError: !!o.error } }; }));
      let others = [];
      if (rest.length) { const r2 = await fetch(new Request(request, { body: JSON.stringify(Array.isArray(msg) ? rest : rest[0]) })); try { const j2 = await r2.json(); others = Array.isArray(j2) ? j2 : [j2]; } catch (e) { others = []; } }
      const all = mine.concat(others);
      return withPay(new Response(JSON.stringify(Array.isArray(msg) ? all : all[0]), { status: 200, headers: { 'content-type': 'application/json', 'cache-control': 'no-store', 'access-control-allow-origin': '*', 'X-Node-Gate': VERSION,
        'X-RCO-Receipt-Id': mine.map(m => ((m.result.structuredContent || {}).receipt || {}).id).filter(Boolean).join(', '), 'access-control-expose-headers': 'X-RCO-Receipt-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' } }), aioPay);   // TMKT-03: a paid outcome carries the payment response
    }
    const units = internal ? 0 : list.filter(x => x && x.method === 'tools/call' && x.params && PAID_TOOLS.includes(x.params.name)).length;
    const g = units ? await decide(request, env, { door: node, resource: `https://${url.hostname}/mcp`, description: `One record read on the ${node} node door (Allooloo Technologies Corp.)`, units }) : { pass: true };
    if (g.response) return signOffer(env, node, g.response);
    const resp = await fetch(new Request(request, { body: raw }));
    if (!resp.ok || !(resp.headers.get('content-type') || '').includes('application/json')) return resp;
    let pay = null; if (g.paid) { pay = await settle(env, g.paid, node); if (!pay.settled) return settleFail(pay); }
    if (list.length === 1 && list[0] && list[0].method === 'tools/list') {   // AIO-01: tools/list names the tool the gate answers
      const t0 = await resp.text(); let j0; try { j0 = JSON.parse(t0); } catch (e) { return withPay(new Response(t0, { status: resp.status, headers: resp.headers }), pay); }
      if (j0 && j0.result && Array.isArray(j0.result.tools) && !j0.result.tools.find(t => t.name === 'get_orderability')) j0.result.tools.push(AIO_TOOL);
      if (j0 && j0.result && Array.isArray(j0.result.tools)) for (const tt of TM_TOOLS) if (!j0.result.tools.find(t => t.name === tt.name)) j0.result.tools.push(tt);   // TMKT-02
      if (j0 && j0.result && Array.isArray(j0.result.tools) && !j0.result.tools.find(t => t.name === ASOF_NAME)) j0.result.tools.push(ASOF_TOOL);   // ASOF-01
      const h0 = new Headers(resp.headers); h0.delete('content-length'); h0.set('X-Node-Gate', VERSION); return withPay(new Response(JSON.stringify(j0), { status: resp.status, headers: h0 }), pay);
    }
    const calls = internal ? [] : list.filter(x => x && x.method === 'tools/call' && x.params && x.params.name === 'resolve_issuer');
    const recCalls = signs(env, node) ? list.filter(x => x && x.method === 'tools/call' && x.params && (x.params.name === 'get_record' || x.params.name === 'resolve_issuer' || x.params.name === 'list_events_since' || x.params.name === 'get_timeline' || x.params.name === 'list_events')) : [];
    if (!calls.length && !recCalls.length) return withPay(resp, pay);
    const text = await resp.text(); let j; try { j = JSON.parse(text); } catch (e) { return withPay(new Response(text, { status: resp.status, headers: resp.headers }), pay); }
    const arr = Array.isArray(j) ? j : [j], decisions = [], at = new Date().toISOString();
    for (const r of arr) {
      const rc = recCalls.find(c => c.id === r.id);
      if (rc && r.result) { let sc = r.result.structuredContent; if (!sc) { try { sc = JSON.parse(r.result.content[0].text); } catch (e) { sc = null; } }
        if (sc && !sc.error) { if (rc.params.name === 'get_record') sc = await signRecord(env, stampClass(sc)); else if (['list_events_since', 'get_timeline', 'list_events'].includes(rc.params.name)) sc = await signEvents(env, sc); else if (Array.isArray(sc.matches)) sc.matches = await Promise.all(sc.matches.map(x => signRecord(env, stampClass(x)))); r.result.structuredContent = sc; r.result.content = [{ type: 'text', text: JSON.stringify(sc) }]; } }
      const call = calls.find(c => c.id === r.id); if (!call || !r.result) continue;
      let sc = r.result.structuredContent; if (!sc) { try { sc = JSON.parse(r.result.content[0].text); } catch (e) { continue; } }
      // RCO-MOVE: the v1 receipt is written before the answer leaves (its id derives from its hash); answer_hash covers the answer without the receipt block
      decisions.push({ r, args: call.params.arguments || {}, sc, at, answer_hash: await answerHash(sc), settlement: pay ? { network: pay.pr.network, transaction: pay.tx } : undefined, payer: pay ? pay.payer : undefined, caller_key: request.headers.get('rco-key') || undefined });   // RCO-03: the reader's customer key, checked by the door
    }
    if (!decisions.length) { const h0 = new Headers(resp.headers); h0.delete('content-length'); return withPay(new Response(JSON.stringify(Array.isArray(j) ? arr : arr[0]), { status: resp.status, headers: h0 }), pay); }
    const rh = { version: resp.headers.get('x-cmr-version'), asOf: resp.headers.get('x-cmr-as-of') };
    const outs = await Promise.all(decisions.map(async d => writeReceipt(env, await receiptFor(d, node, rh, DOOR))));
    decisions.forEach((d, i) => { d.sc.receipt = receiptLinks(outs[i]); d.id = d.sc.receipt.id || ''; d.r.result.structuredContent = d.sc; d.r.result.content = [{ type: 'text', text: JSON.stringify(d.sc) }]; });
    const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-RCO-Receipt-Id', decisions.map(d => d.id).filter(Boolean).join(', ')); h.set('X-Node-Gate', VERSION);
    h.set('access-control-expose-headers', (resp.headers.get('access-control-expose-headers') || '') + ', X-RCO-Receipt-Id');
    return withPay(new Response(JSON.stringify(Array.isArray(j) ? arr : arr[0]), { status: resp.status, headers: h }), pay);
  }
};
