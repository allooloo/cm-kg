// aio.js — AIO-01 (CEO, 2026-10-31): get_orderability(subject, client_category) on every node door. It produces the AIO-10060 v1.0 §7.1 orderability outcome
// (proposed schema v0.1, unratified) for one listed security, one client category of this market's chapter, this market (taken from the door) and the
// market's current ACM-68000 register revision. Read live: the record from this node's own register (get_record on the door's origin), the chapter from the
// Book mirror (book.js chapter(): the AIO section for the elements, the ACM section for the rule revision).
// Rules, from the text and the order:
//  · Basis — every element points at the chapter field instance it rests on (the SM-ECO-10060 7.2 shape: family, section version, field, item, source_url,
//    source_date, read_at, the door's /book/ file) or at a field of the product record (cmr, version, field path, the record's signature). No value is copied
//    out of a basis. An element without a basis is not written.
//  · Gaps — a field the chapter carries as not_found goes into evidence_gaps with the pages the Book reading checked; an outcome with a gap that blocks the
//    conclusion carries no signal. A rule element with no named party or no discharging evidence is a gap, not a condition (§5). Wording the node cannot test
//    without reading (product scope, negative target market) is a gap, never closed by assumption.
//  · Signal — one ACM-68000 signal (§7.2) only where the evidence reaches it: ACM-404 for a client category the chapter does not name, or a subject not on this
//    node's register; ACM-403 for a record whose halt flag is set; ACM-200 only with no blocking gap. ACM-451 is not reached by this reading. No fifth signal:
//    a not-determinable outcome carries no `signal` member and its evidence_gaps (AIO-10060 v1.1 §1, §7.2: stated after the door's first proof).
// Signed by the node under kid allooloo-eco-2026-10 (the ECO signature profile, Worker secret ECO_SIGNING_JWK), node id in the payload; the envelope sits in
// `proof`. Receipted at mcp.rco-records.ai with the node as writer, answer_hash over the signed outcome (rco.js; no new receipt field).
import { chapter } from './book.js';
import { stampClass } from './stampclass.js';   // BOOK-05
import { signRecord, sigRef } from './cmrsign.js';
import { sha256, canon, answerHash, writeReceipt, receiptLinks } from './rco.js';
import { statementFor } from './tm.js';   // TMKT-03: the statement on file
export const ECO_KID = 'allooloo-eco-2026-10';
export const AIO_TOOL = { name: 'get_orderability', title: 'Get orderability outcome (AIO-10060)',
  annotations: { title: 'Get orderability outcome (AIO-10060)', readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true },
  description: "The AIO-10060 orderability outcome for one listed security, one client category of this market's chapter, this market and the market's current ACM-68000 register revision: one ACM-68000 signal where the evidence reaches it, or evidence_gaps with the pages checked and no signal. Every condition, exclusion, assessment, document and review trigger points at the chapter field or record field it rests on. Signed by the node (kid allooloo-eco-2026-10); every read is receipted at mcp.rco-records.ai.",
  inputSchema: { type: 'object', properties: {
    subject: { type: 'string', description: 'The listed security on this node: ticker with exchange (TSX:SHOP), ISIN, LEI or CMR key.' },
    client_category: { type: 'string', description: "One client category exactly as this market's chapter names it in client_categories[] (read <door>/book/aio.json)." } },
    required: ['subject', 'client_category'] } };
const enc = new TextEncoder();
const b64u = buf => { let s = ''; for (const c of new Uint8Array(buf)) s += String.fromCharCode(c); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
let KEY = null;
async function key(env) {
  if (KEY) return KEY;
  const j = JSON.parse(String(env.ECO_SIGNING_JWK).replace(/^﻿/, '').trim());
  KEY = await crypto.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: j.x, d: j.d }, { name: 'Ed25519' }, false, ['sign']);
  return KEY;
}
async function prove(env, o, door) {
  const body = { ...o }; delete body.proof; delete body.receipt;
  const ph = b64u(enc.encode(JSON.stringify({ alg: 'EdDSA', kid: ECO_KID })));
  const sig = await crypto.subtle.sign('Ed25519', await key(env), enc.encode(ph + '.' + b64u(enc.encode(JSON.stringify(sortDeep(body))))));
  return { ...body, proof: { profile: 'ECO signature profile (ECO-10060)', alg: 'EdDSA', kid: ECO_KID, protected: ph, signature: b64u(sig), jwks: `${door}/.well-known/jwks.json`,
    over: "base64url(protected) + '.' + base64url(canonical JSON of the outcome without proof and receipt: keys sorted at every level, compact)" } };
}
const NF = 'not_found';
const found = f => !!f && f.value !== NF && f.value != null && !(Array.isArray(f.value) && !f.value.length);
const items = f => Array.isArray(f.value) ? f.value : [f.value];
const norm = s => String(s == null ? '' : s).toLowerCase().replace(/\s+/g, ' ').trim();
const PARTY = ['distributor', 'actor', 'party', 'firm', 'manufacturer', 'who'];
const DISCHARGE = ['evidence', 'discharge', 'discharged_by'];
const ELEMENT = ['constraint', 'condition', 'requirement', 'responsibility', 'role', 'exception', 'provision', 'outcome', 'obligation'];
async function getRecord(host, subject) {
  try {
    const r = await fetch(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'Allooloo node-gate (get_orderability)' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'get_record', arguments: { identifier: subject } } }), signal: AbortSignal.timeout(20000) });
    const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{')));
    const sc = (j.result && (j.result.structuredContent || (j.result.content && JSON.parse(j.result.content[0].text)))) || null;
    return sc || { error: 'unavailable' };
  } catch (e) { return { error: 'unavailable', note: String(e.message || e).slice(0, 120) }; }
}
export async function getOrderability(env, ctx, { node, host, door, callerKey, payer }, args) {   // TMKT-03: payer (a paid outcome, R-039)
  const cc = node.split('-')[0]; const market = cc.toUpperCase(); const at = new Date().toISOString();
  const subjectArg = String((args && args.subject) || '').trim(); const catArg = String((args && args.client_category) || '').trim();
  if (!subjectArg || !catArg) return { error: 'invalid_arguments', note: 'subject and client_category are both required', tool: 'get_orderability' };
  let ch; try { ch = await chapter(env, ctx, cc); } catch (e) { ch = null; }
  if (!ch || !ch.secs.AIO) return { error: 'unavailable', note: `no AIO section of the ${cc} chapter could be read from the Book`, node };
  const aio = ch.secs.AIO, acm = ch.secs.ACM || { fields: [] }, aioRef = ch.man.sections.find(s => s.family === 'AIO') || {};
  const F = (sec, name) => (sec.fields || []).find(f => f && f.name === name && !f.inferred);
  const ptr = (fam, sec, f, extra) => ({ basis: 'chapter_field', family: fam, section: sec.version, field: f.name, ...(extra || {}), source_url: f.source_url || null, source_date: f.source_date || null, read_at: f.read_at || null, file: `${door}/book/${fam.toLowerCase()}.json` });
  const gaps = [];
  const gap = (fam, sec, name, reason, blocks, extra) => { const f = F(sec, name) || { name }; gaps.push({ family: fam, section: sec.version, field: name, reason, pages_checked: f.pages_checked || (f.source_url ? [f.source_url] : []), read_at: f.read_at || null, blocks_conclusion: !!blocks, ...(extra || {}) }); };
  // rule_version — the market's current ACM register revision
  const rr = F(acm, 'register_revision_ref'); let rule_version = null, ruleBasis = null;
  if (found(rr) && rr.value && rr.value.rule_version) { rule_version = rr.value.rule_version; ruleBasis = ptr('ACM', acm, rr); }
  else gap('ACM', acm, 'register_revision_ref', 'the chapter carries no current ACM-68000 register revision for this market: the outcome cannot name its rule', true);
  // client_category — from the chapter's own client_categories[]
  const cf = F(aio, 'client_categories'); let client_category = null, catMissing = false;
  if (!found(cf)) gap('AIO', aio, 'client_categories', "the chapter's orderability section carries no client_categories: the outcome cannot name its client category", true);
  else { const i = items(cf).findIndex(it => it && typeof it === 'object' ? [it.identifier, it.category, it.name, it.client_category].some(v => norm(v) === norm(catArg)) : norm(it) === norm(catArg));
    if (i >= 0) client_category = ptr('AIO', aio, cf, { item: i, key: (items(cf)[i] && items(cf)[i].identifier !== undefined) ? 'identifier' : 'category' }); else catMissing = true;
    // DEFECTS-01: a desk that asked in its own words can ask again in the regime's: the categories the chapter names, each with its pointer
    if (catMissing) gaps.push({ family: 'AIO', section: aio.version, field: 'client_categories', reason: `"${catArg}" is not a client category the market's chapter names; ask again with one the chapter names (categories_named, in the regime's own words)`,
      basis: ptr('AIO', aio, cf), categories_named: items(cf).map((it, k) => ({ category: it && typeof it === 'object' ? (it.identifier || it.category || it.name || it.client_category || null) : String(it), ...(it && it.rule ? { rule: it.rule } : {}), pointer: ptr('AIO', aio, cf, { item: k, key: it && typeof it === 'object' && it.identifier !== undefined ? 'identifier' : 'category' }) })),
      pages_checked: cf.pages_checked || (cf.source_url ? [cf.source_url] : []), blocks_conclusion: true }); }
  // subject — the product record on this node's register
  const rec0 = await getRecord(host, subjectArg); let subject = null, subject_type = null, rec = null, subjectMissing = false, subjectAmbiguous = false;
  if (rec0 && !rec0.error && rec0.cmr) {
    rec = await signRecord(env, stampClass(rec0)); const path = rec.cmr.split('/').slice(1).join('/');
    subject = { basis: 'record', cmr: rec.cmr, version: rec.version, as_of: rec.as_of, record_url: `${door}/record/${path}`, sha256: await sha256(canon(rec)), signature: sigRef(rec) };
    const st = rec.identity && rec.identity.security_type;
    if (st && st.value) { subject_type = String(st.value); subject.subject_type_basis = { basis: 'record_field', cmr: rec.cmr, version: rec.version, field: 'identity.security_type', source_url: st.source_url || null }; }
  } else if (rec0 && rec0.error === 'ambiguous') { subjectAmbiguous = true; gaps.push({ family: 'ECO', field: 'subject', reason: 'the subject names more than one record on this register: give the exchange or the ISIN', pages_checked: [`${door}/mcp get_record`], blocks_conclusion: true }); }
  else if (rec0 && rec0.error === 'unavailable') return { error: 'unavailable', node, note: "this node's register did not answer; no outcome is produced from memory" };
  else subjectMissing = true;
  // elements — each one pointing at its field instance
  // BOOK-07 (CEO 2026-11-01), the gate rule, final: blocking is scope only — the category one the market's securities rule names (client_categories),
  // the subject on the register and not halted, a rule revision, and the instrument class within the rule's product scope where the rule states one.
  // Distribution conditions never block: each is carried with its party and its discharging evidence where the regime names one, "firm-held" where it
  // names none, and listed in review_triggers beside the BOOK-06 firm-held items. An exclusion the regime itself states for the category and the subject's
  // class is ACM-403, cited to the measure.
  const conditions = [], exclusions_tested = [], assessments_required = [], documents_required = [], review_triggers = [];
  const ccl = s => norm(s).replace(/s\b/g, '');   // a category or class compared as words, plural folded
  const dc = F(aio, 'distribution_conditions');
  if (!found(dc)) { gaps.push({ family: 'AIO', section: aio.version, field: 'distribution_conditions', reason: 'the chapter carries no distribution conditions; any the firm applies are firm-held', pages_checked: (dc && dc.pages_checked) || [], firm_held: true, blocks_conclusion: false }); review_triggers.push({ firm_held: 'distribution_conditions', requirement: null }); }
  else items(dc).forEach((it, i) => {
    const has = k => it && typeof it === 'object' && String(it[k] || '').trim();
    const el = ELEMENT.find(has), pa = PARTY.find(has), di = DISCHARGE.find(has);
    const c = { rule_element: ptr('AIO', aio, dc, { item: i, key: el || null }), party: pa ? { item: i, key: pa } : 'not stated by the regime',
                discharged_by: di ? { item: i, key: di, ...(it.source_kind ? { source_kind: it.source_kind } : {}) } : 'firm-held', ...(it.source_kind ? { source_kind: it.source_kind } : {}) };
    conditions.push(c); review_triggers.push({ condition: c.rule_element, discharged_by: c.discharged_by, note: 'produce the outcome again when this condition or its evidence changes' });
  });
  for (const name of ['manufacturer_distributor_roles', 'evidence_requirements', 'exceptions']) {   // noted, never blocking
    const f = F(aio, name); if (!found(f)) gap('AIO', aio, name, `the chapter carries no ${name}`, false);
  }
  const firm = (name, what) => {
    const f = F(aio, name); const requirement = found(f) ? ptr('AIO', aio, f) : null;
    gaps.push({ family: 'AIO', section: aio.version, field: name, reason: (requirement ? `${what}: the regime's requirement is cited from the Book` : `${what}: the chapter carries no ${name}`) + '; the evidence is firm-held (held by the distributing firm, not by the node) — a named gap, not a block',
                requirement, pages_checked: f ? (f.pages_checked || (f.source_url ? [f.source_url] : [])) : [], firm_held: true, blocks_conclusion: false });
    review_triggers.push({ firm_held: name, requirement, note: 'produce the outcome again when the firm-held evidence for this requirement changes' });
    return f;
  };
  // exclusions: the regime's own exclusion for this category and the subject's class → ACM-403 (below); every other exclusion is firm-held
  const ntm = firm('negative_target_market', 'negative target market'); let excluded = null;
  const ic = rec && rec.instrument_class; const catItem = client_category ? items(cf)[client_category.item] : null; const catName = catItem ? (catItem.identifier || catItem.category || catItem.name || '') : catArg;
  if (found(ntm)) items(ntm).forEach((it, i) => {
    const t = it && typeof it === 'object' ? it : { exclusion: String(it) }; const forCat = !!(t.applies_to && ccl(t.applies_to) && (ccl(t.applies_to) === ccl(catName) || ccl(t.applies_to) === ccl(catArg)));
    const words = ccl(t.exclusion || ''); const forClass = !!(ic && ic.value && (words.includes(ccl(ic.value)) || (ic.value.includes(' — ') && words.includes(ccl(ic.value.split(' — ').pop())))));
    const e = { exclusion: ptr('AIO', aio, ntm, { item: i }) };
    if (forCat && forClass && t.rule) { e.result = "applies: the regime states this exclusion for the category and the subject's class"; if (!excluded) excluded = { ...ptr('AIO', aio, ntm, { item: i }), measure: { key: 'rule' }, reason: 'an exclusion the regime itself states for this client category and this instrument class' }; }
    else if (forCat) e.result = "considered: stated for this client category; its words do not name the subject's instrument class — not applied";
    else e.result = 'not tested by the node — firm-held';
    exclusions_tested.push(e);
  });
  // the product scope: where the rule states one, the subject's instrument class must be within it — the same class, or a class the scope object names as included
  const ps = F(aio, 'product_scope'); let scope_basis = null;
  review_triggers.push({ firm_held: 'product_scope', requirement: found(ps) ? ptr('AIO', aio, ps) : null, note: 'produce the outcome again when the product scope or the instrument class changes' });
  if (!found(ps)) gaps.push({ family: 'AIO', section: aio.version, field: 'product_scope', reason: 'the rule states no product scope in the Book: no scope test applies', pages_checked: (ps && ps.pages_checked) || [], firm_held: true, blocks_conclusion: false });
  else if (rec) {
    // BOOK-08: the scope bridge — a product_scope object whose cfi_categories (the ISO 10962 categories its provision's words name, verified with the object)
    // hold the first two CFI letters of the subject's class places the subject within the scope; the same class named, or listed as included, still does. Nothing outside the bridge.
    const cat2 = ic && ic.cfi ? String(ic.cfi).slice(0, 2).toUpperCase() : null;
    const codes = it => String((it && it.cfi_categories) || '').toUpperCase().split(/[^A-Z]+/).filter(Boolean);
    let j = cat2 ? items(ps).findIndex(it => it && typeof it === 'object' && codes(it).includes(cat2)) : -1, via = j >= 0 ? 'cfi_categories' : null;
    if (j < 0 && ic && ic.value) { j = items(ps).findIndex(it => it && typeof it === 'object' && (ccl(it.instrument_class) === ccl(ic.value) || (Array.isArray(it.includes) && it.includes.some(x => ccl(x) === ccl(ic.value))))); if (j >= 0) via = 'instrument_class'; }
    if (j >= 0) scope_basis = { record: { basis: 'record_field', cmr: rec.cmr, version: rec.version, field: 'instrument_class', ...(ic.cfi ? { cfi: ic.cfi } : {}), source_url: ic.source_url || null, source_date: ic.source_date || null }, product_scope: ptr('AIO', aio, ps, { item: j, key: via }), ...(via === 'cfi_categories' ? { bridge: `ISO 10962 ${cat2} → ${items(ps)[j].instrument_class}` } : {}) };
    else gaps.push({ family: 'AIO', section: aio.version, field: 'product_scope', reason: !(ic && ic.value) ? "the rule states a product scope and the subject's record carries no instrument class to place within it" : cat2 ? `the rule states a product scope and no scope object's bridge (cfi_categories) holds ISO 10962 ${cat2}, nor names the subject's class: the subject is not shown within the scope` : "the rule states a product scope; the subject's class carries no CFI to place on the scope bridge, and no scope object names the class: the subject is not shown within the scope", basis: ptr('AIO', aio, ps), record_basis: { basis: 'record_field', cmr: rec.cmr, version: rec.version, field: 'instrument_class' }, pages_checked: ps.source_url ? [ps.source_url] : [], blocks_conclusion: true });
  }
  for (const [name, list, what] of [['required_assessments', assessments_required, 'assessment'], ['product_documentation', documents_required, 'document']]) {
    const f = firm(name, name.replace('_', ' '));
    if (found(f)) items(f).forEach((it, i) => list.push({ [what]: ptr('AIO', aio, f, { item: i }) }));
  }
  const rt = F(aio, 'review_triggers');
  if (!found(rt)) gap('AIO', aio, 'review_triggers', 'the chapter carries no review triggers: the outcome cannot say when it must be produced again', false);
  else items(rt).forEach((it, i) => review_triggers.push({ trigger: ptr('AIO', aio, rt, { item: i }) }));
  // the signal — only where the evidence reaches it
  const scopeGap = !rule_version || !found(cf); let signal = null, signal_basis = null;
  if (scopeGap) signal = null;
  else if (catMissing) { signal = 'ACM-404'; signal_basis = [{ ...ptr('AIO', aio, cf), reason: "the client category is not one the market's chapter names", pages_checked: cf.pages_checked || (cf.source_url ? [cf.source_url] : []) }]; }
  else if (subjectMissing) { signal = 'ACM-404'; signal_basis = [{ basis: 'register', reason: "the subject is not on this node's register", pages_checked: [`${door}/mcp get_record`, `${door}/nodes.json`] }]; }
  else if (subjectAmbiguous) signal = null;
  else if (rec && rec.halt && rec.halt.value === true) { signal = 'ACM-403'; signal_basis = [{ basis: 'record_field', cmr: rec.cmr, version: rec.version, field: 'halt', source_url: rec.halt.source_url || rec.halt.page || null, read_at: rec.halt.read_at || null }]; }
  else if (excluded) { signal = 'ACM-403'; signal_basis = [excluded]; }   // BOOK-07: the regime's own exclusion, cited to the measure
  else if (gaps.some(g => g.blocks_conclusion)) signal = null;
  else { signal = 'ACM-200'; signal_basis = [...(client_category ? [client_category] : []), ...(scope_basis ? [scope_basis] : [])]; }   // BOOK-07: scope only; the conditions are carried, firm-held where the regime names no evidence

  // TMKT-03 (CEO, chain 2026-11-02b): the discharge — the statement on file (its home node) against the asked market's Book field manufacturer_evidence_accepted.
  // The clearance signal above is never changed by a statement. A dual-listed subject: the home node's statement applies; this market's Book decides the status.
  const MEA_ITEMS = [['negative_target_market', st => { const v = st.negative_target_market; return v && typeof v === 'object' && !Array.isArray(v) ? (v[cc] ?? v) : v; }],
    ['product_scope_statement', st => st.product_scope_statement], ['product_documentation', st => st.documentation], ['required_assessments', st => st.assessments]];
  const meaF = F(aio, 'manufacturer_evidence_accepted'); const meaItems = meaF && Array.isArray(meaF.value) ? meaF.value : [];
  const isinOfRec = rec && rec.identity && rec.identity.isin && rec.identity.isin.value ? String(rec.identity.isin.value) : null;
  let stm = null; try { stm = await statementFor(env, subjectArg, cc, isinOfRec); } catch (e) { stm = { error: 'unavailable' }; }
  const stmRef = stm && !stm.error ? { subject: stm.key, home_node: stm.node, version: stm.version, filed_at: stm.filed_at, kid: stm.kid, path: stm.path, sha256: stm.sha256, signatures_valid: stm.signatures_valid, filer: stm.filer, receipt_id: stm.receipt_id,
    read: { tool: 'get_target_market', door: `https://mcp.${stm.node}.ai/mcp`, arguments: { subject: stm.key, version: stm.version } } } : null;
  const book = (k, b) => ({ basis: 'chapter_field', family: 'AIO', section: aio.version, field: 'manufacturer_evidence_accepted', item: k, book_status: b ? b.status : (meaF && meaF.value === NF ? 'not_found' : 'not read for this market'), file: `${door}/book/aio.json` });
  const dItems = MEA_ITEMS.map(([k, val]) => {
    const b = meaItems.find(x => x && x.item === k) || null; const base = book(k, b);
    if (!stmRef) return { item: k, status: 'firm-held, no statement', ...base };
    if (b && b.status === 'accepted') return { item: k, status: `discharged by manufacturer statement v${stmRef.version}, filed ${String(stmRef.filed_at).slice(0, 10)}, key ${stmRef.kid}`, statement_receipt_id: stmRef.receipt_id, ...base };
    if (b && b.status === 'partial') return { item: k, status: 'present, firm-held', quotes: { regulator: (b.quotes || []).map(q => ({ quote: q.quote, anchor: q.anchor, source_url: q.source_url })), statement: val(stmRef ? stm.statement : {}) ?? null }, ...base };
    return { item: k, status: 'firm-held', ...base };
  });
  const discharge = { rule: 'AIO-10060 v1.2 §7, the discharge rule (TMKT-03; published TMKT-04): accepted → discharged by the statement; partial → present, firm-held with both quotes; silent, not_found, not_accepted → firm-held; no statement → firm-held, no statement. A statement never changes the clearance signal.',
    statement: stmRef, ...(stm && stm.error ? { statement_error: stm.error } : {}), items: dItems };
  const scope = { subject: subject ? subject.cmr + '@' + subject.version : subjectArg, client_category: client_category ? `${client_category.section}#${client_category.field}[${client_category.item}]` : null, market, rule_version };
  const out = { schema_version: 'AIO-10060 v1.2 §9.1 · proposed machine schema v0.1 (unratified)',   // TMKT-04: the text in force is v1.2 (§9.1, renumbered from v1.1 §7.1) · ZONES-04: was v1.1
    outcome_id: 'aio:' + (await sha256(canon({ ...scope, section: aio.version }))).slice(7, 39),
    requested: { subject: subjectArg, client_category: catArg }, subject, subject_type, market, client_category, rule_version, rule_basis: ruleBasis,
    section_ref: { chapter: ch.man.version, section: aio.version, supersedes: aio.supersedes || null, file: `${door}/book/aio.json`, book_path: aioRef.path || null, book_sha256: aioRef.sha256 || null },
    ...(signal ? { signal, signal_page: `https://acm-${signal.slice(4)}.ai/`, signal_basis } : {}),
    ...(scope_basis ? { scope_basis } : {}), determinable: !!signal, conditions, discharge, exclusions_tested, assessments_required, documents_required, evidence_gaps: gaps, review_triggers,
    as_of: ch.man.as_of, produced_at: at, node, door: `${door}/mcp`, standard: 'https://aio-10060.org/', signal_vocabulary: 'https://acm-68000.org/' };
  if (!signal) out.not_determinable = 'the evidence does not reach a conclusion: the gaps that block it are in evidence_gaps (blocks_conclusion), with the pages checked; no signal is given (AIO-10060 v1.2 §1 and §9.2: a not-determinable outcome carries no signal, evidence_gaps[] not empty, no fifth signal)';
  const signed = await prove(env, out, door);
  const rcpt = await writeReceipt(env, { object: { type: subject ? 'cmr' : 'identifier', id: subject ? subject.cmr : subjectArg }, market, rule_version: rule_version || null, decided_at: at,
    answer_hash: await answerHash(signed), actor_class: 'ai-agent (MCP client)', ...(callerKey ? { caller_key: callerKey } : payer ? { caller: 'x402:' + String(payer).toLowerCase() } : {}) }, node);   // TMKT-03: a paid outcome's receipt names the payer   // DEFECTS-01: the caller identity
  return { ...signed, receipt: receiptLinks(rcpt) };
}
// the agent card lists the tool (a skill entry beside the card's own)
export async function cardWithTool(resp, door) {
  if (!resp.ok || !(resp.headers.get('content-type') || '').includes('json')) return resp;
  let c; try { c = await resp.clone().json(); } catch (e) { return resp; }
  if (!c || typeof c !== 'object' || Array.isArray(c)) return resp;
  const skill = { id: 'get_orderability', name: AIO_TOOL.title, description: AIO_TOOL.description, tags: ['orderability', 'aio-10060', 'acm-68000', 'mcp'], examples: [`get_orderability(subject, client_category) at ${door}/mcp`] };
  const skills = Array.isArray(c.skills) ? c.skills.filter(s => s && s.id !== 'get_orderability').concat([skill]) : [skill];
  const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-AIO', 'card-tool');
  return new Response(JSON.stringify({ ...c, skills, orderability: { door: `${door}/mcp`, tool: 'get_orderability', standard: 'https://aio-10060.org/' } }), { status: resp.status, headers: h });
}
// the node door's own page, llms.txt and facts.json list the tool beside the door's five (the door serves them; the gate adds the one it answers)
export async function withListing(resp, p, door) {
  const ct = resp.headers.get('content-type') || ''; if (!resp.ok) return resp;
  let t = await resp.text(); const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-AIO', 'listed');
  if (p === '/facts.json' && ct.includes('json')) { try { const j = JSON.parse(t); if (Array.isArray(j.tools) && !j.tools.includes('get_orderability')) j.tools.push('get_orderability'); j.orderability = { door: `${door}/mcp`, tool: 'get_orderability', standard: 'https://aio-10060.org/' }; t = JSON.stringify(j); } catch (e) {} }
  else if (p === '/' && ct.includes('html')) t = t.replace('list_aliases · list_nodes.', 'list_aliases · list_nodes · get_orderability.').replace(/(<p>Tools:[\s\S]*?<\/p>)/, `$1<p>Orderability door: <a href="${door}/mcp">${door}/mcp</a> — get_orderability(subject, client_category), the AIO-10060 orderability outcome for one client category of this market's chapter, signed by the node and receipted at mcp.rco-records.ai.</p>`);
  else if (p === '/llms.txt') t = t.replace(/^(Tools: .*)$/m, `$1, get_orderability (subject + client_category -> the AIO-10060 orderability outcome of this market, each element pointing at its chapter or record field, signed by the node, receipted at mcp.rco-records.ai)`);
  return new Response(t, { status: resp.status, headers: h });
}
