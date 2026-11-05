// tm.js — TMKT-02 (CEO, 2026-11-01): the Target Market door on every node door — the read and the file. Design of record: START_ME_UP\Allooloo_Program_gettargetmarket_Build-Plan_v1.0
// §3 (the thirteen fields), §4 (the tools), §5.1 (filer key, the first cut), §5.3 (the test filer), §5.4 (never), §6 (storage), §10 (security).
//   get_target_market(subject, version?, as_of?)   the statement at its current version (or a version, or the last version filed at or before as_of); both signatures;
//                                                   receipted at mcp.rco-records.ai with the door as writer (gettargetmarket) and the reader as caller (RCO-Key, a filer value, or the x402 payer)
//   list_target_market_versions(subject)            every version with filed_at and supersedes; nothing is deleted
//   verify_target_market(statement | subject+version)  the manufacturer-side signature (kid allooloo-tm-2026-11, made by the door on the filer's behalf, §5.1) and the
//                                                   node's signature (node_sig, the node's record key allooloo-cmr-2026-10); public; with a statement given it reads nothing
//   file_target_market(subject, manufacturer, statement)  Authorization: Bearer <filer value>. Shape, filer identity, LEI and subject checked; stored at this node as
//                                                   tm/<subject>/v<N>.json (immutable, If-None-Match: *; a change is a new version that supersedes the last); receipted with the
//                                                   door as writer and the filer as caller; filing is free (CEO, TMKT-02: the x402 offer stays on reads only)
// Storage: the node's own pond (allooloocmkg<cc>pond), container target-market (blobs tm/<subject>/v<N>.json), written with a container SAS under the stored policy tm-gate (read, create, list — no write over a blob,
// no delete) held in the Worker secret TM_SAS ({cc: sas}); the write path reaches the target-market container and nothing else. The apex holds no statement.
// Filer identities: KV tm-filers (binding TM_FILERS), key "filer:" + sha256 hex of the value; the value is shown once at mint and never held in clear (rail CM-KG\DOOR\gettargetmarket\tm_mint.py).
// The test filer (Allooloo Test Manufacturer, LEI prefix TEST00) files only TEST: subjects; a real filer never files a TEST: subject; nothing filed under TEST: attaches to a live record.
import { sha256, canon, writeReceipt, receiptLinks } from './rco.js';
export const TM_KID = 'allooloo-tm-2026-11';
export const TM_JWK_PUBLIC = { kty: 'OKP', crv: 'Ed25519', x: 'yS_wJaADI8ANDwLVY2mhUUN0wM56gAPtBRKx9pT_cSo', kid: TM_KID, alg: 'EdDSA', use: 'sig' };
export const CMR_JWK_PUBLIC = { kty: 'OKP', crv: 'Ed25519', x: 'cqa-iPbl2AD_Yw3bIxQCPAmzSiBemxU6ajL2nI1w9QA', kid: 'allooloo-cmr-2026-10', alg: 'EdDSA', use: 'sig' };
export const TM_WRITER = 'gettargetmarket';   // the receipt door's published writer mapping (rco-door 2.5.0, /writers.json)
export const TM_NAMES = ['get_target_market', 'list_target_market_versions', 'verify_target_market', 'file_target_market'];
export const TM_READS = ['get_target_market', 'list_target_market_versions'];   // the x402 offer when asked (free for every agent otherwise); verify is public, filing is free
export const TEST_LEI_PREFIX = 'TEST00';
// the markets a statement may name: the chapters of the Book of Markets on the live nodes (the roster of record at TMKT-02, mcp.getissuer.ai/nodes.json)
export const MARKETS = new Set(['ae', 'at', 'au', 'be', 'bm', 'br', 'ca', 'ch', 'cz', 'de', 'dk', 'es', 'fi', 'fr', 'gr', 'hk', 'ie', 'in', 'it', 'je', 'jp', 'kr', 'ky', 'lu', 'mx', 'nl', 'no', 'pl', 'pt', 'se', 'sg', 'tw', 'uk', 'us']);
const KEYRING = 'https://mcp.gettargetmarket.ai/.well-known/jwks.json';
const SCHEMA = 'AIO-10060 v1.2 §6 target market statement · machine schema tm-0.1';   // TMKT-04: v1.2 published (was: draft, unpublished until TMKT-04)
const RATE_PER_HOUR = 30;
const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
const SUBJ = { type: 'string', description: 'The ISIN (TEST:<ISIN-shaped> for the test namespace).' };
export const TM_TOOLS = [
  { name: 'get_target_market', title: 'Read a target market statement', annotations: { title: 'Read a target market statement', ...ANN },
    description: "The manufacturer's target market statement for an ISIN, stored at the subject's home node: the current version, or a version, or the last version filed at or before as_of; both signatures (the manufacturer-side signature and the node's); every read is receipted at mcp.rco-records.ai with the door as writer. A subject with no statement answers status not_found (no error).",
    inputSchema: { type: 'object', properties: { subject: SUBJ, version: { type: 'integer', minimum: 1, description: 'A version number (default: the current version).' }, as_of: { type: 'string', description: 'An ISO 8601 time: the last version filed at or before it.' } }, required: ['subject'] } },
  { name: 'list_target_market_versions', title: 'List the statement versions', annotations: { title: 'List the statement versions', ...ANN },
    description: 'Every version of the target market statement for an ISIN with filed_at, supersedes, its path under tm/ and its sha256; nothing is deleted.',
    inputSchema: { type: 'object', properties: { subject: SUBJ }, required: ['subject'] } },
  { name: 'verify_target_market', title: 'Verify a statement', annotations: { title: 'Verify a statement', ...ANN },
    description: "Whether a stored statement's two signatures verify against the published keys: sig (kid allooloo-tm-2026-11, the door's signature on the filer's behalf, filer id in the payload) and node_sig (the home node's record key, kid allooloo-cmr-2026-10). Give the statement itself (nothing is read) or subject and version. Public; offline: the keys are in the answer and at https://mcp.gettargetmarket.ai/.well-known/jwks.json.",
    inputSchema: { type: 'object', properties: { statement: { type: 'object', description: 'A statement exactly as get_target_market served it.' }, subject: SUBJ, version: { type: 'integer', minimum: 1 } } } },
  { name: 'file_target_market', title: 'File a target market statement', annotations: { title: 'File a target market statement', readOnlyHint: false, destructiveHint: false, openWorldHint: false, idempotentHint: false },
    description: "The manufacturer's agent files a target market statement for an ISIN its Legal Entity Identifier issues, under its filer identity (Authorization: Bearer <filer value>). The door checks shape, identity, LEI and subject, stores the statement at the subject's home node as the next version (immutable; a change is a new version that supersedes the last), signs it on the filer's behalf and under the node's record key, and receipts the filing with the door as writer and the filer as caller. Free.",
    inputSchema: { type: 'object', properties: { subject: SUBJ, manufacturer: { type: 'string', description: "The manufacturer's LEI (it must be the filer identity's LEI and, for a live subject, the LEI on the subject's record)." },
      statement: { type: 'object', description: 'manufacturer_name, markets, positive_target_market, negative_target_market, distribution_strategy, product_scope_statement, documentation, assessments, source (and supersedes, optional: the version it replaces). The door adds subject, manufacturer, version, filed_at, supersedes, filer, kid, sig, node, node_sig.' } }, required: ['subject', 'manufacturer', 'statement'] } }];

// ---------- identifiers
const ISIN_RE = /^[A-Z]{2}[A-Z0-9]{9}\d$/;
export function isinOk(s) {
  if (!ISIN_RE.test(s)) return false;
  const digits = s.slice(0, 11).split('').map(c => /\d/.test(c) ? c : String(c.charCodeAt(0) - 55)).join('');
  let sum = 0, dbl = true;
  for (let i = digits.length - 1; i >= 0; i--) { let d = +digits[i]; if (dbl) { d *= 2; if (d > 9) d -= 9; } sum += d; dbl = !dbl; }
  return (10 - (sum % 10)) % 10 === +s[11];
}
export function leiOk(s) {
  if (!/^[A-Z0-9]{18}\d{2}$/.test(s)) return false;
  let r = 0; for (const c of s) { const v = /\d/.test(c) ? c : String(c.charCodeAt(0) - 55); for (const d of v) r = (r * 10 + +d) % 97; }
  return r === 1;
}
// a subject: an ISIN, or TEST:<ISIN-shaped> (the test namespace; its first two letters name the home node). Returns { key, isin, test } or null
export function subjectOf(raw) {
  const s = String(raw || '').trim().toUpperCase();
  if (s.startsWith('TEST:')) { const i = s.slice(5); return ISIN_RE.test(i) ? { key: 'TEST:' + i, isin: i, test: true } : null; }
  return isinOk(s) ? { key: s, isin: s, test: false } : null;
}

// ---------- signatures (the house JWS: base64url(protected) + '.' + base64url(canonical JSON: keys sorted at every level, compact))
const enc = new TextEncoder();
const b64u = buf => { let s = ''; for (const c of new Uint8Array(buf)) s += String.fromCharCode(c); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const unb64u = s => { const t = atob(String(s).replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - String(s).length % 4) % 4)); return Uint8Array.from(t, c => c.charCodeAt(0)); };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
const KEYS = {};
async function privKey(env, name) {
  if (KEYS[name]) return KEYS[name];
  const j = JSON.parse(String(env[name]).replace(/^﻿/, '').trim());
  KEYS[name] = await crypto.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: j.x, d: j.d }, { name: 'Ed25519' }, false, ['sign']);
  return KEYS[name];
}
async function jws(env, secret, kid, obj, jwks) {
  const ph = b64u(enc.encode(JSON.stringify({ alg: 'EdDSA', kid })));
  const sig = await crypto.subtle.sign('Ed25519', await privKey(env, secret), enc.encode(ph + '.' + b64u(enc.encode(JSON.stringify(sortDeep(obj))))));
  return { alg: 'EdDSA', kid, protected: ph, signature: b64u(sig), jwks };
}
async function jwsOk(pub, s, obj) {
  try {
    if (!s || !s.protected || !s.signature) return false;
    const k = await crypto.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: pub.x }, { name: 'Ed25519' }, false, ['verify']);
    return await crypto.subtle.verify('Ed25519', k, unb64u(s.signature), enc.encode(s.protected + '.' + b64u(enc.encode(JSON.stringify(sortDeep(obj))))));
  } catch (e) { return false; }
}
// what each signature covers: sig = the statement without sig, node, node_sig; node_sig = the statement without node_sig (sig and node inside)
const sigBody = st => { const o = { ...st }; delete o.sig; delete o.node; delete o.node_sig; return o; };
const nodeBody = st => { const o = { ...st }; delete o.node_sig; return o; };
export async function verifyStatement(st) {
  const sig_ok = !!(st && st.kid === TM_KID && st.sig && st.sig.kid === TM_KID) && await jwsOk(TM_JWK_PUBLIC, st.sig, sigBody(st));
  const node_sig_ok = !!(st && st.node_sig && st.node_sig.kid === CMR_JWK_PUBLIC.kid) && await jwsOk(CMR_JWK_PUBLIC, st.node_sig, nodeBody(st));
  return { valid: sig_ok && node_sig_ok, sig_ok, node_sig_ok, sig_kid: st && st.sig ? st.sig.kid : null, node_sig_kid: st && st.node_sig ? st.node_sig.kid : null, filer: st && st.filer ? st.filer.id : null, node: st ? st.node || null : null,
    keys: [TM_JWK_PUBLIC, CMR_JWK_PUBLIC], keyring: KEYRING,
    method: "sig: Ed25519 over base64url(protected) + '.' + base64url(canonical JSON of the statement without sig, node and node_sig); node_sig: the same over the statement without node_sig. Canonical JSON: keys sorted at every level, compact." };
}

// ---------- the store: allooloocmkg<cc>pond / target-market / tm/<subject>/v<N>.json (Azure container names are 3 to 63 characters: tm alone is refused)
const acct = cc => `https://allooloocmkg${cc}pond.blob.core.windows.net/target-market`;
const sasOf = (env, cc) => { try { const m = JSON.parse(String(env.TM_SAS || '{}').replace(/^﻿/, '')); return m[cc] ? String(m[cc]).replace(/^\?/, '') : null; } catch (e) { return null; } };
const XV = { 'x-ms-version': '2021-08-06' };
const blobName = (key, n) => `tm/${encodeURIComponent(key)}/v${n}.json`;
async function versions(env, cc, key) {
  const sas = sasOf(env, cc); if (!sas) throw new Error('store not wired');
  const r = await fetch(`${acct(cc)}?restype=container&comp=list&prefix=${encodeURIComponent('tm/' + key + '/')}&${sas}`, { headers: XV, cf: { cacheTtl: 0 } });
  if (!r.ok) throw new Error(`store list ${r.status}`);
  const xml = await r.text();
  return [...xml.matchAll(/<Name>([^<]+)<\/Name>/g)].map(m => Number((/\/v(\d+)\.json$/.exec(m[1]) || [])[1] || 0)).filter(Boolean).sort((a, b) => a - b);
}
async function readV(env, cc, key, n) {
  const r = await fetch(`${acct(cc)}/${blobName(key, n)}?${sas(env, cc)}`, { headers: XV, cf: { cacheTtl: 0 } });
  if (r.status === 404) return null; if (!r.ok) throw new Error(`store read ${r.status}`);
  return r.json();
}
const sas = (env, cc) => { const s = sasOf(env, cc); if (!s) throw new Error('store not wired'); return s; };
async function putNew(env, cc, key, n, obj) {
  const r = await fetch(`${acct(cc)}/${blobName(key, n)}?${sas(env, cc)}`, { method: 'PUT', body: JSON.stringify(obj, null, 1),
    headers: { ...XV, 'x-ms-blob-type': 'BlockBlob', 'If-None-Match': '*', 'content-type': 'application/json; charset=utf-8' } });
  return r.status;   // 201 created · 409/412 the blob exists (never overwritten) · 403 refused by the policy
}

// ---------- filer identities (KV tm-filers): filer:<sha256 hex of the value> -> { filer_id, lei, name, test, domain, claim, minted_at }
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
async function filerOf(env, request) {
  const m = /^Bearer\s+(tmfk_f[0-9a-f]{10}_[A-Za-z0-9_-]{30,})$/i.exec(request.headers.get('authorization') || ''); if (!m || !env.TM_FILERS) return null;
  const h = hex(await crypto.subtle.digest('SHA-256', enc.encode(m[1])));
  const f = await env.TM_FILERS.get('filer:' + h, 'json');
  return f && !f.revoked_at && /^f[0-9a-f]{10}$/.test(f.filer_id || '') ? f : null;
}
async function rateOk(env, filer) {
  const k = `rate:${filer.filer_id}:${new Date().toISOString().slice(0, 13)}`;
  const n = Number(await env.TM_FILERS.get(k) || 0); if (n >= RATE_PER_HOUR) return false;
  await env.TM_FILERS.put(k, String(n + 1), { expirationTtl: 7200 }); return true;
}

// ---------- shape (§3): what the filer gives; the door adds the rest
const DS = ['execution-only', 'with appropriateness', 'advised', 'portfolio management'];
const PTM = ['client_categories', 'knowledge_and_experience', 'ability_to_bear_loss', 'risk_tolerance', 'objectives_and_needs'];
const str = (v, n = 2000) => typeof v === 'string' && v.trim() && v.length <= n;
const said = v => str(v) || (Array.isArray(v) && v.length && v.every(x => str(x)));
const HASH = /^sha256:[0-9a-f]{64}$/;
function shape(s, live) {
  const bad = []; if (!s || typeof s !== 'object' || Array.isArray(s)) return { bad: ['statement must be an object'] };
  if (!str(s.manufacturer_name, 300)) bad.push('manufacturer_name: the manufacturer\'s name as on its LEI record');
  const mk = Array.isArray(s.markets) ? s.markets.map(x => String(typeof x === 'object' && x ? x.market : x).toLowerCase().trim()) : [];
  if (!mk.length || !mk.every(m => /^[a-z]{2}$/.test(m)) || (live && !mk.every(m => live.has(m)))) bad.push('markets: one or more market codes, each a chapter of the Book of Markets on a live node');
  const markets = [...new Set(mk)].map(m => ({ market: m, chapter: `https://sm-eco-10060.org/market/${m}/` }));
  const per = (name, test) => { const o = s[name]; if (!o || typeof o !== 'object' || Array.isArray(o) || !mk.length || !mk.every(m => o[m] && test(o[m]))) bad.push(name + ': an object keyed by each market named'); };
  per('positive_target_market', o => typeof o === 'object' && PTM.every(k => said(o[k])));
  if (bad.length && bad[bad.length - 1].startsWith('positive')) bad[bad.length - 1] += ', each holding ' + PTM.join(', ') + ' in the regime\'s own category words';
  per('negative_target_market', o => said(o) || (typeof o === 'object' && Object.values(o).every(said)));
  const ds = s.distribution_strategy;
  const dsOk = x => Array.isArray(x) && x.length && x.every(v => DS.includes(String(v).toLowerCase()));
  if (!(dsOk(ds) || (ds && typeof ds === 'object' && !Array.isArray(ds) && mk.every(m => dsOk(ds[m]))))) bad.push('distribution_strategy: ' + DS.join(' · ') + ' (a list, or a list per market)');
  const ps = s.product_scope_statement; if (!ps || typeof ps !== 'object' || !str(ps.statement) || !str(ps.instrument_class, 200)) bad.push('product_scope_statement: { statement, instrument_class, scope_bridge_term (optional) }');
  const doc = s.documentation; if (!Array.isArray(doc) || !doc.length || !doc.every(d => d && str(d.kind, 120) && /^https:\/\//.test(String(d.url || '')) && /^\d{4}-\d{2}-\d{2}$/.test(String(d.document_date || '')) && HASH.test(String(d.sha256 || '')))) bad.push('documentation: [{ kind, url (https), document_date (YYYY-MM-DD), sha256 (sha256:<64 hex>, the hash at filing) }]');
  const as = s.assessments; if (!Array.isArray(as) || !as.every(a => a && str(a.name, 200) && /^\d{4}-\d{2}-\d{2}$/.test(String(a.date || '')))) bad.push('assessments: [{ name, date (YYYY-MM-DD) }] — named and dated, not attached');
  const so = s.source; if (!so || !['emt', 'direct'].includes(so.kind) || (so.kind === 'emt' && !(str(so.emt_version, 40) && HASH.test(String(so.sha256 || ''))))) bad.push('source: { kind: "direct" } or { kind: "emt", emt_version, sha256 }');
  return { bad, markets };
}

async function driftOf(env, cc, key, n) {   // TMKT-04: the drift marks tm-verify wrote beside a statement (tm/<subject>/v<N>.drift-<date>.json); nothing is removed
  try {
    const pre = `tm/${key}/v${n}.drift-`; const r = await fetch(`${acct(cc)}?restype=container&comp=list&prefix=${encodeURIComponent(pre)}&${sas(env, cc)}`, { headers: XV, cf: { cacheTtl: 0 } });
    if (!r.ok) return [];
    const names = [...(await r.text()).matchAll(/<Name>([^<]+)<\/Name>/g)].map(m => m[1]);
    return (await Promise.all(names.map(async nm => { const b = await fetch(`${acct(cc)}/${nm.split('/').map(encodeURIComponent).join('/')}?${sas(env, cc)}`, { headers: XV, cf: { cacheTtl: 0 } }); return b.ok ? { record: nm, ...(await b.json()) } : null; }))).filter(Boolean);
  } catch (e) { return []; }
}

// ---------- TMKT-03: the statement on file, as get_orderability reads it (the discharge)
const receiptName = (key, n) => `tm/${encodeURIComponent(key)}/v${n}.receipt.json`;
async function putReceiptRecord(env, cc, key, n, obj) {   // create-only beside the statement (If-None-Match: *): the filing receipt id, so a reader names it
  try { const r = await fetch(`${acct(cc)}/${receiptName(key, n)}?${sas(env, cc)}`, { method: 'PUT', body: JSON.stringify(obj), headers: { ...XV, 'x-ms-blob-type': 'BlockBlob', 'If-None-Match': '*', 'content-type': 'application/json; charset=utf-8' } }); return r.status; } catch (e) { return 0; }
}
async function readReceiptRecord(env, cc, key, n) {
  try { const r = await fetch(`${acct(cc)}/${receiptName(key, n)}?${sas(env, cc)}`, { headers: XV, cf: { cacheTtl: 0 } }); return r.ok ? await r.json() : null; } catch (e) { return null; }
}
export async function statementFor(env, raw, here, isin) {   // { key, home, version, ... } · null (none on file) · { error }
  const sj = subjectOf(raw) || (isin ? subjectOf(isin) : null); if (!sj) return null;
  const pre = sj.isin.slice(0, 2).toLowerCase();
  const homes = sj.test ? [pre] : [...new Set([here, pre].filter(c => MARKETS.has(c)))];
  for (const cc of homes) {
    let vs; try { vs = await versions(env, cc, sj.key); } catch (e) { return { error: 'unavailable', home: cc, note: String(e.message || e).slice(0, 80) }; }
    if (!vs.length) continue;
    const n = vs[vs.length - 1]; const st = await readV(env, cc, sj.key, n); if (!st) return { error: 'unavailable', home: cc };
    const v = await verifyStatement(st); const rr = await readReceiptRecord(env, cc, sj.key, n);
    return { key: sj.key, home: cc, node: `${cc}-cm-kg`, version: n, filed_at: st.filed_at, kid: (st.sig && st.sig.kid) || TM_KID, path: pathOf(sj.key, n), sha256: await sha256(canon(st)),
             signatures_valid: !!v.valid, filer: st.filer ? st.filer.id : null, receipt_id: rr ? rr.receipt_id : null, statement: st };
  }
  return null;
}

// ---------- the record (live subjects): this node's register, through the node's own door origin, as get_orderability reads it
async function recordLei(host, isin) {
  try {
    const r = await fetch(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'Allooloo node-gate (target market)' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'get_record', arguments: { identifier: isin } } }), signal: AbortSignal.timeout(20000) });
    const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{')));
    const sc = (j.result && (j.result.structuredContent || (j.result.content && JSON.parse(j.result.content[0].text)))) || {};
    if (sc.error) return { error: sc.error };
    const l = sc.identity && sc.identity.lei; return { cmr: sc.cmr || null, lei: l && l.value ? String(l.value).toUpperCase() : null };
  } catch (e) { return { error: 'unavailable' }; }
}

// ---------- the tools
const out = (o, isError) => ({ o, isError: !!isError });
const refuse = (code, note, extra) => out({ error: code, note, tool: 'file_target_market', ...(extra || {}) }, true);
const pathOf = (key, n) => `tm/${key}/v${n}.json`;
const chapterRefs = (st, door) => (st.markets || []).map(m => ({ market: m.market, chapter: m.chapter, aio_section: m.market === door.cc ? `${door.url}/book/aio.json` : `the ${m.market} node door's /book/aio.json` }));
export async function tmCall(env, ctx, request, { node, host, door, callerKey, routed, settlement, liveMarkets }, name, args) {
  const cc = node.split('-')[0]; const D = { cc, url: door };
  args = args || {}; const at = new Date().toISOString();
  if (name === 'verify_target_market' && args.statement && typeof args.statement === 'object') return out({ ...(await verifyStatement(args.statement)), subject: args.statement.subject || null, version: args.statement.version || null, read: 'nothing: the statement given was verified as it stands' });
  const sj = subjectOf(args.subject);
  if (!sj) return out({ error: 'invalid_arguments', note: 'subject must be an ISIN (with its check digit) or TEST:<ISIN-shaped>', tool: name }, true);
  // a live ISIN is stored at the node of its listing (the router finds it in the index); a TEST: subject's home node is the one its first two letters name
  if (sj.test && sj.isin.slice(0, 2).toLowerCase() !== cc) return out({ error: 'wrong_node', note: `a TEST: subject is stored at the node its first two letters name (${sj.isin.slice(0, 2).toLowerCase()}-cm-kg), not here`, node }, true);
  let vs; try { vs = await versions(env, cc, sj.key); } catch (e) { return out({ error: 'unavailable', note: `the ${node} store did not answer (${String(e.message || e).slice(0, 80)}); nothing is answered from memory`, node }, true); }
  if (name === 'list_target_market_versions') {
    const rows = []; for (const n of vs) { const st = await readV(env, cc, sj.key, n); if (st) rows.push({ version: st.version, filed_at: st.filed_at, supersedes: st.supersedes, path: pathOf(sj.key, n), sha256: await sha256(canon(st)) }); }
    return out({ subject: sj.key, node, door: `${door}/mcp`, versions: rows, status: rows.length ? 'on_file' : 'not_found', note: rows.length ? 'every version stays published; nothing is deleted' : 'no target market statement is on file for this subject at this node' });
  }
  if (name === 'get_target_market' || name === 'verify_target_market') {
    let n = null;
    if (args.version !== undefined && args.version !== null && args.version !== '') { n = Number(args.version); if (!vs.includes(n)) n = -1; }
    else if (args.as_of && name === 'get_target_market') {
      const t = Date.parse(args.as_of); if (isNaN(t)) return out({ error: 'invalid_arguments', note: 'as_of must be an ISO 8601 time', tool: name }, true);
      for (const v of [...vs].reverse()) { const st = await readV(env, cc, sj.key, v); if (st && Date.parse(st.filed_at) <= t) { n = v; break; } } if (n === null) n = -1;
    } else n = vs.length ? vs[vs.length - 1] : -1;
    if (n === -1) return out({ subject: sj.key, status: 'not_found', node, door: `${door}/mcp`, versions_on_file: vs, note: vs.length ? 'no version of the statement matches the version or as_of asked' : 'no target market statement is on file for this subject at this node; the outcome\'s firm-held conditions stay firm-held', read_at: at });
    const st = await readV(env, cc, sj.key, n);
    if (!st) return out({ error: 'unavailable', note: 'the version was listed but did not read', node }, true);
    if (name === 'verify_target_market') return out({ ...(await verifyStatement(st)), subject: sj.key, version: st.version, path: pathOf(sj.key, n), node });
    const answer_hash = await sha256(canon(st));   // binds the exact statement version served
    const reader = callerKey ? null : await filerOf(env, request);   // a filer reading its own (or any) statement under its filer value is named as the caller
    const rcpt = await writeReceipt(env, { object: { type: sj.test ? 'test-isin' : 'isin', id: sj.key }, market: cc.toUpperCase(), rule_version: `gettargetmarket get_target_market · ${pathOf(sj.key, n)} · ${node}`, decided_at: at, answer_hash,
      actor_class: 'ai-agent (MCP client)', ...(callerKey ? { caller_key: callerKey } : reader ? { caller: 'filer:' + reader.filer_id } : settlement && settlement.payer ? { caller: 'x402:' + String(settlement.payer).toLowerCase() } : {}) }, TM_WRITER);
    const receipt = receiptLinks(rcpt);
    const documentation_drift = await driftOf(env, cc, sj.key, n);   // TMKT-04: tm-verify's marks, beside the statement
    return out({ subject: sj.key, status: 'on_file', version: st.version, versions_on_file: vs, current: n === vs[vs.length - 1], path: pathOf(sj.key, n), statement: st, answer_hash, documentation_drift, chapter_sections: chapterRefs(st, D),
      verify: { tool: 'verify_target_market', arguments: { subject: sj.key, version: st.version }, keyring: KEYRING }, node, door: `${door}/mcp`, read_at: at, ...(settlement && settlement.transaction ? { settlement: { network: settlement.network, transaction: settlement.transaction } } : {}),
      receipt_id: receipt.id || null, receipt });
  }
  if (name !== 'file_target_market') return out({ error: 'unknown_tool', tool: name }, true);
  // ---- the write (§5.1, §5.4, §6)
  const filer = await filerOf(env, request);
  if (!filer) return refuse('not_authorised', 'file_target_market needs Authorization: Bearer <filer value>, a filer identity issued by Allooloo bound to the manufacturer\'s LEI (gettargetmarket.ai/file)');
  const lei = String(args.manufacturer || '').trim().toUpperCase();
  if (!leiOk(lei)) return refuse('invalid_arguments', 'manufacturer must be a Legal Entity Identifier (ISO 17442, with its check digits)');
  if (lei !== filer.lei) return refuse('not_issuer', 'the manufacturer LEI is not the LEI the filer identity is bound to');
  const testFiler = !!filer.test && filer.lei.startsWith(TEST_LEI_PREFIX);
  if (sj.test !== testFiler) return refuse('not_issuer', testFiler ? 'the test filer files only TEST: subjects' : 'a TEST: subject is filed only by the test filer');
  let cmr = null;
  if (!sj.test) {
    const rec = await recordLei(host, sj.isin);
    if (rec.error === 'unavailable') return refuse('unavailable', "this node's register did not answer; nothing is filed");
    if (rec.error || !rec.cmr) return refuse('not_on_register', "the subject is not on this node's register; a statement is filed at the node of the subject's listing");
    if (!rec.lei || rec.lei !== lei) return refuse('not_issuer', "the filer's LEI does not issue this subject (the LEI on the subject's record differs or is not on the record)", { record: rec.cmr });
    cmr = rec.cmr;
  }
  const s = args.statement || {};
  const sh = shape(s, liveMarkets || MARKETS); if (sh.bad.length) return refuse('invalid_statement', 'the statement does not have the shape of AIO-10060 v1.2 §6', { fields: sh.bad });
  if (!(await rateOk(env, filer))) return refuse('rate_limited', `a filer files at most ${RATE_PER_HOUR} statements an hour`);
  const last = vs.length ? vs[vs.length - 1] : null;
  if (s.supersedes !== undefined && s.supersedes !== null && Number(s.supersedes) !== last) return refuse('stale_supersedes', `the current version is ${last === null ? 'none' : 'v' + last}; a new statement supersedes the current version`, { current: last });
  const N = (last || 0) + 1;
  const body = { schema: SCHEMA, subject: sj.key, ...(cmr ? { record: cmr } : {}), ...(sj.test ? { test: true } : {}), manufacturer: { lei, name: String(s.manufacturer_name).trim() }, version: N, filed_at: at, supersedes: last,
    markets: sh.markets, positive_target_market: s.positive_target_market, negative_target_market: s.negative_target_market, distribution_strategy: s.distribution_strategy, product_scope_statement: s.product_scope_statement,
    documentation: s.documentation, assessments: s.assessments, source: s.source, filer: { id: filer.filer_id, model: 'filer key (gettargetmarket build plan §5.1): signed by the door on the filer\'s behalf' }, kid: TM_KID };
  if (!env.TM_SIGNING_JWK || !env.CMR_SIGNING_JWK) return refuse('unavailable', 'the door\'s signing keys are not placed on this gate; nothing is filed');
  const sig = await jws(env, 'TM_SIGNING_JWK', TM_KID, body, KEYRING);
  const withSig = { ...body, sig, node };
  const stored = { ...withSig, node_sig: await jws(env, 'CMR_SIGNING_JWK', CMR_JWK_PUBLIC.kid, withSig, 'https://allooloo.ai/.well-known/jwks.json') };
  const st = await putNew(env, cc, sj.key, N, stored);
  if (st === 409 || st === 412) return refuse('overwrite_refused', `tm/${sj.key}/v${N}.json already exists; a filing never overwrites (another filing took this version — read the current version and file again)`, { current: N });
  if (st !== 201) return refuse('unavailable', `the store refused the write (HTTP ${st}); nothing is filed`);
  const answer_hash = await sha256(canon(stored));
  const rcpt = await writeReceipt(env, { object: { type: sj.test ? 'test-isin' : 'isin', id: sj.key }, market: cc.toUpperCase(), rule_version: `gettargetmarket file_target_market · ${pathOf(sj.key, N)} · ${node}`, decided_at: at, answer_hash,
    actor_class: 'ai-agent (MCP client) · filer', caller: 'filer:' + filer.filer_id }, TM_WRITER);
  const receipt = receiptLinks(rcpt);
  if (receipt.id) await putReceiptRecord(env, cc, sj.key, N, { receipt_id: receipt.id, answer_hash, filed_at: at, path: pathOf(sj.key, N) });   // TMKT-03: the filing receipt beside the statement
  return out({ filed: true, subject: sj.key, version: N, supersedes: last, filed_at: at, path: pathOf(sj.key, N), node, door: `${door}/mcp`, kid: TM_KID, sig, node_sig: stored.node_sig, answer_hash, statement: stored,
    verify: { tool: 'verify_target_market', arguments: { subject: sj.key, version: N }, keyring: KEYRING }, receipt_id: receipt.id || null, receipt });
}
// the card, the page, llms.txt and facts.json of the node door list the four tools beside get_orderability
export const tmSkills = door => TM_TOOLS.map(t => ({ id: t.name, name: t.title, description: t.description, tags: ['target-market', 'product-governance', 'aio-10060', 'mcp'], examples: [`${t.name} at ${door}/mcp`] }));
