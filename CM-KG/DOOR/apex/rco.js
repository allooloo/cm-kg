// rco.js — RCO-MOVE (Allooloo build memo v1.0, 2026-10-30): Allooloo's gates write v1 receipts to the Record of Cleared Orders at
// mcp.rco-records.ai (operator Allooloo Technologies Corp.). A read that clears (an issuer resolved, an ECO signal returned) leaves one receipt:
// {subject, subject_type, market, rule_version, cleared_at, answer_hash, caller} — the door adds v, id, seq, writer, prev_hash, hash, sig, kid
// (Ed25519, kid rco-allooloo-2026-10). The write runs BEFORE the answer is sent (the v1 id is derived from the receipt hash, so the answer can only
// carry it once written); answer_hash = sha256 over the canonical JSON (keys sorted, no whitespace) of the answer the agent receives, without the
// `receipt` block this file then adds. A write that fails or takes longer than RCO_WAIT_MS leaves the answer without an id (receipt.status
// "not written") and is logged — never a guessed id. The v0 argument names (decision_id, gtin, actor_class) ride along for the six-month alias
// window and are ignored by the v1 door. Authentication: Worker secret RCO_DOOR_TOKEN. Previous file beside this one as rco.js.pre-rcomove-2026-10-30.
// One copy per Worker folder (CM-KG\NODE-GATE, CM-KG\ECO).
const RCO = 'https://mcp.rco-records.ai/mcp';
const RCO_WAIT_MS = 4000;
export const RCO_KID = 'rco-allooloo-2026-10';
export const RCO_KEYRING = 'https://rco-records.ai/.well-known/jwks.json';
const enc = new TextEncoder();
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
export const decisionId = () => 'dec_' + [...crypto.getRandomValues(new Uint8Array(12))].map(b => b.toString(16).padStart(2, '0')).join('');
export async function sha256(s) { return 'sha256:' + hex(await crypto.subtle.digest('SHA-256', enc.encode(typeof s === 'string' ? s : JSON.stringify(s)))); }
export const canon = v => Array.isArray(v) ? '[' + v.map(canon).join(',') + ']' : v && typeof v === 'object' ? '{' + Object.keys(v).sort().filter(k => v[k] !== undefined).map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}' : JSON.stringify(v === undefined ? null : v);
export async function answerHash(answer) { const a = { ...answer }; delete a.receipt; return 'sha256:' + hex(await crypto.subtle.digest('SHA-256', enc.encode(canon(a)))); }
export const receiptLinks = out => {
  const r = out && (out.receipt || out);
  const id = r && (r.id || r.decision_id);
  if (!id) return { status: 'not written', door: RCO, note: 'the receipt write did not complete; this answer carries no receipt id' };
  return { id, seq: r.seq || null, verify_receipt: { door: RCO, tool: 'verify_receipt', arguments: { id } }, page: `https://rco-records.ai/receipts/${id}`, keyring: RCO_KEYRING };
};
const cc = s => { const m = /^([a-z]{2})-cm-kg/i.exec(String(s || '')); return m ? m[1].toUpperCase() : null; };
export function recordOf(body) {
  const o = body.object || {};
  const subject = String(o.id || body.subject || '').slice(0, 120) || null;
  const market = body.market || cc(body.rule && body.rule.id) || cc(body.issuing_door && new URL(body.issuing_door).hostname.replace(/^mcp\./, '')) || null;
  const rule_version = body.rule ? [body.rule.id, body.rule.version].filter(Boolean).join(' · ') : (body.rule_version || null);
  const cleared_at = body.decided_at || body.cleared_at || new Date().toISOString();
  return { subject, subject_type: o.type || body.subject_type || null, market, rule_version, cleared_at, answer_hash: body.answer_hash || '', ...(body.caller_key ? { caller_key: body.caller_key } : body.caller ? { caller: body.caller } : {}),
    decision_id: body.decision_id || decisionId(), gtin: subject, actor_class: body.actor_class || null };
}
export async function writeReceipt(env, body, writer) {   // AIO-01: writer = the node gate that cleared the read (X-RCO-Writer, under the door's published writer mapping); absent = allooloo
  if (!env || !env.RCO_DOOR_TOKEN) { console.log('rco receipt not written: RCO_DOOR_TOKEN absent'); return null; }
  const record = recordOf(body);
  const deadline = Date.now() + RCO_WAIT_MS;
  try {
    for (let attempt = 1; attempt <= 3 && Date.now() < deadline; attempt++) {
      const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), Math.max(500, deadline - Date.now()));
      const r = await fetch(RCO, { method: 'POST', signal: ctl.signal, headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', authorization: 'Bearer ' + String(env.RCO_DOOR_TOKEN).replace(/^﻿/, '').trim(), 'user-agent': 'Allooloo rco-writer (RCO-MOVE)', ...(writer ? { 'x-rco-writer': writer } : {}) },
        body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'write_receipt', arguments: record } }) }).finally(() => clearTimeout(t));
      const j = await r.json().catch(() => null); const res = j && j.result;
      const out = res && (res.structuredContent || (res.content && res.content[0] && JSON.parse(res.content[0].text)));
      if (res && !res.isError) { console.log('rco receipt written', out && out.receipt ? out.receipt.id : out && out.decision_id); return out; }
      console.log('rco receipt refused', 'attempt', attempt, JSON.stringify(out || j).slice(0, 300));
      if (out && /invalid_receipt|not_authorised/.test(out.code || '')) return null;
      await new Promise(s => setTimeout(s, 300 * attempt));
    }
  } catch (e) { console.log('rco receipt error', String(e).slice(0, 200)); }
  return null;
}
