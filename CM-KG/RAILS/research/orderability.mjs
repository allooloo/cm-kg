// orderability.mjs — USR-01 (2026-11-11): the orderability outcome on the research page, read from the node's own door so the page and get_orderability agree.
// The gate's rule (AIO-10060 v1.2; NODE-GATE\worker\aio.js) reaches its signal from: the market's chapter (rule revision, client categories, product scope,
// the regime's exclusions), the subject on the register, its halt flag and its instrument class. So per node: the chapter's client categories are read from
// <door>/book/aio.json; every record is given its instrument class by the gate's own stampclass.js; issuers are grouped by (instrument class, CFI category,
// halted); one live get_orderability per group and client category is read on one member, and its signal stands for the group. Where the chapter names no
// client category the outcome is not determinable for every issuer, and one live read states it. Each live read leaves its RCO receipt (the node as writer).
// Output: CM-KG\RESEARCH\orderability\<cc>.json. Usage: node orderability.mjs <cc> [...]
import fs from 'node:fs'; import path from 'node:path'; import readline from 'node:readline';
import { stampClass } from '../../NODE-GATE/worker/stampclass.js';
const POND = 'C:\\ALLOOLOO\\CM-KG\\POND', OUT = 'C:\\ALLOOLOO\\CM-KG\\RESEARCH\\orderability'; fs.mkdirSync(OUT, { recursive: true });
const UA = 'Allooloo digest (USR-01 research roll-up)';
const NODES = JSON.parse(fs.readFileSync('C:\\ALLOOLOO\\SITE\\USR-01\\list_nodes.json', 'utf8')).result.structuredContent.nodes;
const doorOf = cc => String(NODES.find(n => n.node === `${cc}-cm-kg`).door).replace(/\/mcp$/, '').replace(/\/$/, '');
const latest = cc => { const b = path.join(POND, `${cc}-cm-kg`, 'research'); const ds = fs.readdirSync(b).filter(d => fs.existsSync(path.join(b, d, 'node.json'))).sort((a, c) => (a.slice(0, 10) + String(Number(a.slice(11) || 1)).padStart(3, '0')).localeCompare(c.slice(0, 10) + String(Number(c.slice(11) || 1)).padStart(3, '0'))); return path.join(b, ds[ds.length - 1]); };
async function call(door, name, args) {
  for (let i = 0; i < 4; i++) {
    try {
      const r = await fetch(`${door}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': UA }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(90000) });
      const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{'))); const res = j.result || {}; const o = res.structuredContent || JSON.parse(res.content[0].text);
      if (o && o.error === 'unavailable') throw new Error('unavailable'); return o;
    } catch (e) { if (i === 3) throw e; await new Promise(r => setTimeout(r, 4000 * (i + 1))); }
  }
}
const slim = o => ({ signal: o.signal || null, determinable: !!o.determinable, rule_version: o.rule_version || null, chapter_as_of: o.as_of || null, section: o.section_ref ? o.section_ref.section : null, outcome_id: o.outcome_id || null,
  blocking_gaps: (o.evidence_gaps || []).filter(g => g.blocks_conclusion).map(g => ({ family: g.family, field: g.field, reason: g.reason })), ...(o.signal_basis ? { signal_basis: o.signal_basis.map(b => b.reason || b.field || b.basis) } : {}), read_on: o.subject ? o.subject.cmr : null, receipt: o.receipt ? o.receipt.id : null, ...(o.error ? { error: o.error } : {}) });
async function node(cc) {
  const door = doorOf(cc); const d = latest(cc); const groups = new Map(); const of = {};
  for await (const l of readline.createInterface({ input: fs.createReadStream(path.join(d, 'records.jsonl'), 'utf8') })) {
    if (!l) continue; const rec = JSON.parse(l); if (String(rec.kind || '').startsWith('reference')) continue;
    const ic = stampClass(rec).instrument_class || {}; const g = JSON.stringify([ic.value || null, ic.cfi ? String(ic.cfi).slice(0, 2).toUpperCase() : null, !!(rec.halt && rec.halt.value === true)]);
    if (!groups.has(g)) groups.set(g, rec.cmr); of[rec.cmr] = g;
  }
  const aio = await (await fetch(`${door}/book/aio.json`, { headers: { 'user-agent': UA }, signal: AbortSignal.timeout(60000) })).json();
  const cf = ((aio.section || {}).fields || []).find(f => f && f.name === 'client_categories' && !f.inferred); const found = cf && cf.value && cf.value !== 'not_found';
  const items = found ? (Array.isArray(cf.value) ? cf.value : [cf.value]) : []; const cats = items.map(it => it && typeof it === 'object' ? (it.identifier || it.category || it.name || it.client_category) : String(it)).filter(Boolean);
  const out = { node: `${cc}-cm-kg`, door: `${door}/mcp`, tool: 'get_orderability', chapter_file: `${door}/book/aio.json`, section: (aio.section || {}).version || aio.version || null, client_categories: cats, groups: {}, of };
  if (!cats.length) {
    const rep = groups.values().next().value; const o = await call(door, 'get_orderability', { subject: rep, client_category: 'retail client' });
    out.node_outcome = { ...slim(o), note: "the chapter's orderability section names no client category: the outcome is not determinable for every issuer of this market" };
  } else {
    for (const [g, rep] of groups) { out.groups[g] = {}; for (const c of cats) out.groups[g][c] = slim(await call(door, 'get_orderability', { subject: rep, client_category: c })); }
  }
  fs.writeFileSync(path.join(OUT, `${cc}.json`), JSON.stringify(out));
  console.log(cc, 'categories', cats.length, 'groups', groups.size, 'live reads', cats.length ? groups.size * cats.length : 1, cats.length ? JSON.stringify(Object.values(out.groups).flatMap(x => Object.values(x).map(y => y.signal || 'none')).reduce((a, s) => (a[s] = (a[s] || 0) + 1, a), {})) : (out.node_outcome.blocking_gaps[0] || {}).field);
}
let bad = 0;
for (const cc of process.argv.slice(2)) { try { await node(cc); } catch (e) { bad++; console.log(cc, 'FAILED', String(e).slice(0, 200)); } }
process.exit(bad ? 1 : 0);
