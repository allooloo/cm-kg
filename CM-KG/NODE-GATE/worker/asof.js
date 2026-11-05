// asof.js — ASOF-01 (2026-11-05): get_as_of, the point-in-time door (getasof.ai), answered by the gate on every node door. A read over the Replay store
// under Data Vintage — the node door's own get_record with as_of (the sealed market-year split, backfill/replay/<year>/), never the live record and never a
// second copy of the history. The gate shapes the contract, signs the answer under the node's record key (kid allooloo-cmr-2026-10) and receipts it at
// mcp.rco-records.ai under the Allooloo writer token with the node as writer (the authorised gate that cleared the read), before the answer is sent.
//   two clocks  identity fields answer on the read-date clock: a field is held only if the record had read it by as_of (else not_held, with its first read);
//               disclosure lines are the sealed vintage: each line a public filing dated on or before as_of, read into the vintage on its read date, signed.
//   typed       unknown_issuer · before_record · not_sealed · not_found (+ invalid_request, ambiguous, unavailable). Nothing is answered from memory.
//               before_record and not_sealed are signed and receipted like a record (a backtest relies on the absence too); the others are not.
import { signRecord } from './cmrsign.js';
import { answerHash, writeReceipt, receiptLinks } from './rco.js';
export const ASOF_NAME = 'get_as_of';
export const ASOF_LEAD = 'get_as_of is the issuer record as it stood on a date: an issuer by ticker, ISIN or LEI plus a date returns the signed record of that day — every field with its source and read date, the sealed disclosure lines of the market-year up to that date — signed by the node of the issuer\'s market and receipted, so a backtest can show what it read and when. Nothing is restated and nothing is filled backwards: before the record existed the answer says before_record; in a market-year not yet sealed it says not_sealed and names the earliest sealed date.';
export const ASOF_TOOL = { name: ASOF_NAME, title: 'Get the issuer record as of a date', annotations: { title: 'Get the issuer record as of a date', readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true },
  description: ASOF_LEAD + ' Served from the Replay store under Data Vintage (sealed market-years, 2021 forward); typed errors unknown_issuer, before_record, not_sealed, not_found; every answer carries the node signature (kid) and its RCO-10060 receipt (verify_receipt at https://mcp.rco-records.ai/mcp).',
  inputSchema: { type: 'object', properties: { issuer: { type: 'string', description: 'Ticker (with exchange where it helps: NASDAQ:AAPL, SHEL.L), ISIN or LEI.' }, as_of: { type: 'string', description: 'ISO date, YYYY-MM-DD: the day the record is read as of.' }, market: { type: 'string', description: 'Optional two-letter market code; the owning node resolves it if absent.' } }, required: ['issuer', 'as_of'] } };
export const ASOF_PAGE = 'https://getasof.ai/'; export const ASOF_MCP = 'https://mcp.getasof.ai/mcp';
const UA = 'Allooloo node-gate (get_as_of)';
async function door(host, name, args) {   // the node door's own tool on its origin (a same-host subrequest from the gate reaches the origin)
  const r = await fetch(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': UA }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(25000) });
  const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{'))); const res = j.result || {};
  return res.structuredContent || JSON.parse((res.content || [{ text: '{}' }])[0].text);
}
const validDate = s => { if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false; const d = new Date(s + 'T00:00:00Z'); return !isNaN(d) && d.toISOString().slice(0, 10) === s; };
const day = s => (s ? String(s).slice(0, 10) : null);
const runDate = run => { const m = /bf-(\d{4})(\d{2})(\d{2})T/.exec(String(run || '')); return m ? `${m[1]}-${m[2]}-${m[3]}` : null; };
const prevDay = s => new Date(Date.parse(s + 'T00:00:00Z') - 86400000).toISOString().slice(0, 10);
function fieldOf(v) {
  if (!v || typeof v !== 'object') return { state: 'not_held' };
  if (v.state === 'not held as of this date') return { state: 'not_held', first_read: v.first_read || null };
  return { value: v.value === undefined ? null : v.value, source: v.source_url || v.source || null, read_date: day(v.read_at || v.as_of), effective_date: day(v.effective || v.effective_date || v.as_of_effective) || null, state: v.state || 'sourced', read_by: v.read_by || null };
}
async function counted(env) { if (!env.X402) return; try { const n = parseInt((await env.X402.get('tot:asof_receipts')) || '0', 10) + 1; await env.X402.put('tot:asof_receipts', String(n)); } catch (e) { } }   // the page's live tile (receipts written)
export async function getAsOf(env, ctx, cx, args) {
  const { node, host, door: doorUrl } = cx; const cc = node.split('-')[0].toUpperCase();
  const issuer = String((args && args.issuer) || '').trim(); const asOf = String((args && args.as_of) || '').trim(); const market = String((args && args.market) || '').trim().toLowerCase();
  const base = { tool: ASOF_NAME, issuer, as_of: asOf, node, market: cc, door: doorUrl + '/mcp', page: ASOF_PAGE };
  if (!issuer || !validDate(asOf)) return { o: { ...base, error: 'invalid_request', note: 'issuer (ticker, ISIN or LEI) and as_of (YYYY-MM-DD, a real date) are required' }, err: true };
  if (market && market !== node.split('-')[0]) return { o: { ...base, error: 'not_found', note: `this door holds market ${cc}; ask ${ASOF_MCP}, which routes by issuer and market` }, err: true };
  let res; try { res = await door(host, 'resolve_issuer', { identifier: issuer }); } catch (e) { return { o: { ...base, error: 'unavailable', note: `the node's door did not answer (${e.name || 'error'}); nothing is answered elsewhere` }, err: true }; }
  const matches = (res && res.matches) || [];
  if (!matches.length) return { o: { ...base, error: 'unknown_issuer', note: `no issuer on the ${node} register for this identifier` }, err: true };
  const cmrs = [...new Set(matches.map(m => m.cmr))];
  if (cmrs.length > 1) return { o: { ...base, error: 'ambiguous', candidates: matches.map(m => ({ cmr: m.cmr, name: m.name, exchange: m.exchange, isin: m.isin || null })), note: 'more than one listing matches: name the exchange (NASDAQ:AAPL) or give the ISIN' }, err: true };
  const cmr = cmrs[0]; const at = new Date().toISOString();
  let rec; try { rec = await door(host, 'get_record', { identifier: cmr, as_of: asOf }); } catch (e) { return { o: { ...base, cmr, error: 'unavailable', note: `the node's door did not answer (${e.name || 'error'})` }, err: true }; }
  let out;
  if (rec && rec.error === 'bad_as_of') return { o: { ...base, cmr, error: 'invalid_request', note: 'as_of must be YYYY-MM-DD' }, err: true };
  if (rec && rec.error) return { o: { ...base, cmr, error: rec.error === 'not_found' ? 'not_found' : 'unavailable', note: rec.note || null }, err: true };
  const ledger = rec && rec.ledger; const sealedYears = ((ledger && ledger.years_sealed) || []).slice().sort();
  if (rec && rec.status === 'not sealed') {
    out = { ...base, cmr, error: 'not_sealed', year: rec.year, earliest_sealed_date: (ledger && ledger.history_from) || null, years_sealed: sealedYears, note: ledger ? `no sealed market-year of ${cc} holds ${asOf}; nothing partial is served as final` : `the ${cc} vintage is not sealed yet; this door answers not_sealed until it is` };
  } else {
    const man = rec.manifest || {}; const rd = runDate(man.run); const year = Number(rec.year);
    const thisYear = new Date().getUTCFullYear();
    if (rd && year >= Number(rd.slice(0, 4)) && asOf >= rd && year >= thisYear) {   // the current market-year is sealed through the day before its seal run; a later date is not sealed yet
      out = { ...base, cmr, error: 'not_sealed', year, sealed_through: prevDay(rd), earliest_sealed_date: (await door(host, 'get_record', { identifier: cmr, as_of: '2000-01-01' }).then(x => x && x.ledger && x.ledger.history_from).catch(() => null)) || null, note: `the ${year} vintage is sealed through ${prevDay(rd)}; ${asOf} is after it` };
    } else {
      const fields = Object.fromEntries(Object.entries(rec.identity_as_of || {}).map(([k, v]) => [k, fieldOf(v)]));
      const held = Object.values(fields).filter(f => f.state !== 'not_held').length; const events = rec.events_as_of || [];
      let earlier = null;
      if (!held && !events.length) {   // nothing in this year up to as_of: did the record hold the issuer in an earlier sealed year?
        for (let y = year - 1; y >= 2021; y--) { try { const r = await door(host, 'get_record', { identifier: cmr, as_of: `${y}-12-31` }); if (r && r.events_in_year_to_date) { earlier = y; break; } if (r && r.status === 'not sealed') break; } catch (e) { break; } }
      }
      if (!held && !events.length && earlier == null) out = { ...base, cmr, error: 'before_record', note: `the record holds nothing on ${cmr} on or before ${asOf}: no identity field read by then and no sealed disclosure line dated by then; nothing is inferred backwards`, vintage: { year, run: man.run || null, hash_tree_root: man.hash_tree_root || null } };
      else out = { ...base, cmr, version: { id: `${cmr}@${asOf}`, vintage: { year, run: man.run || null, hash_tree_root: man.hash_tree_root || null, rows: man.rows || null, rows_file: man.rows_file || null, manifest_signature: man.signature || null }, ...(rd && year >= Number(rd.slice(0, 4)) ? { sealed_through: prevDay(rd) } : {}) },
        clock: 'identity fields on the read-date clock: held only if the record had read them by as_of (else not_held, with the first read); disclosure lines are the sealed vintage: public filings dated on or before as_of, each with its source and read date, each signed',
        fields, fields_held: held, events, events_count: events.length, ...(earlier != null ? { last_lines_in: earlier } : {}), note: 'the answer is a lookup over the sealed vintage, the same answer every time it is asked; nothing restated, nothing back-filled' };
    }
  }
  out.served_utc = at;
  const signed = await signRecord(env, out);
  const rc = await writeReceipt(env, { object: { type: 'cmr', id: cmr }, market: cc, rule_version: `get_as_of · as_of ${asOf}${out.version ? ` · vintage ${out.version.vintage.year} ${out.version.vintage.run || ''}` : out.error ? ` · ${out.error}` : ''}`.trim(), decided_at: at,
    answer_hash: await answerHash(signed), actor_class: 'ai-agent (MCP client)', ...(cx.callerKey ? { caller_key: cx.callerKey } : cx.payer ? { caller: 'x402:' + String(cx.payer).toLowerCase() } : {}), ...(cx.settlement ? { settlement: cx.settlement } : {}) }, node);
  const receipt = receiptLinks(rc); if (rc && rc.receipt && rc.receipt.hash) receipt.hash = rc.receipt.hash;
  if (receipt.id) ctx.waitUntil(counted(env));
  return { o: { ...signed, receipt }, err: false, receipt_id: receipt.id || null };
}
// the node door's page, llms.txt, facts.json and card name the door (THE LIBRARY definition line, cross-linked to getasof.ai)
export const asofLine = d => `<p>As Of door: <a href="${d}/mcp">${d}/mcp</a> — get_as_of: the issuer record as it stood on a date, from this node's sealed vintage, signed and receipted (<a href="${ASOF_PAGE}">getasof.ai</a>).</p>`;
export const asofLlms = () => `get_as_of (the issuer record as it stood on a date, from this node's sealed vintage, signed and receipted — ${ASOF_PAGE})`;
export const asofSkill = d => ({ id: ASOF_NAME, name: ASOF_TOOL.title, description: ASOF_LEAD, tags: ['point-in-time', 'data-vintage', 'replay', 'rco-10060', 'mcp'], examples: [`get_as_of at ${d}/mcp`] });
