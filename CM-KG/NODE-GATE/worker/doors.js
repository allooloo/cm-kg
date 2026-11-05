// doors.js — DOORS-01 (2026-11-05): get_filings, get_ticker, get_auditor — three one-tool doors (getfilings.ai, getticker.ai, getauditor.ai), answered by the gate on
// every node door from fields already on the record; nothing new is collected. Each answer: every value with its source page and read date, the node's signature
// (kid allooloo-cmr-2026-10), and an RCO-10060 receipt written at mcp.rco-records.ai under the Allooloo writer token with the node as writer, before the answer leaves.
// A field this market's record does not carry answers not_on_record for this market (with the record's own reason where it states one); nothing is inferred.
//   get_filings  the node's event lines for the issuer (list_events_since), dated in [from, to], each with its type, date, source and signature
//   get_ticker   the issuer behind a ticker (+ exchange) or an ISIN or LEI: name, ISIN, LEI, ticker, exchange, security type, listing and status (the register and the halt flag)
//   get_auditor  the auditor of record (the record's auditor fields) and every auditor change on the record (the lifecycle index, type auditor_change), dated
// get_record, Timeline, resolve_issuer, list_aliases and Events stay where they are.
import { signRecord } from './cmrsign.js';
import { answerHash, writeReceipt, receiptLinks } from './rco.js';
const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
const ID = { type: 'string', description: 'Ticker (with exchange where it helps: NASDAQ:AAPL, SHEL.L), ISIN or LEI.' };
export const DOORS = {
  get_filings: { page: 'https://getfilings.ai/', mcp: 'https://mcp.getfilings.ai/mcp', title: 'Get the filings of an issuer in a date range',
    lead: 'get_filings is the disclosures of an issuer in a date range: an issuer by ticker, ISIN or LEI plus a date range returns every filing and release on the record for that issuer in that range, each with its type, its date, its source page and its read date — signed by the node of the issuer\'s market and receipted. Served from the record as read; nothing new is collected and nothing is inferred.',
    schema: { type: 'object', properties: { issuer: ID, from: { type: 'string', description: 'ISO date, YYYY-MM-DD (inclusive).' }, to: { type: 'string', description: 'ISO date, YYYY-MM-DD (inclusive); default today.' }, market: { type: 'string', description: 'Optional two-letter market code.' } }, required: ['issuer', 'from'] } },
  get_ticker: { page: 'https://getticker.ai/', mcp: 'https://mcp.getticker.ai/mcp', title: 'Get the issuer behind a ticker',
    lead: 'get_ticker is the issuer behind a ticker: a ticker and its exchange, or an ISIN or LEI, returns the issuer, its ISIN, its LEI, its listing and its status — every value with its source page and read date, signed by the node of the listing\'s market and receipted. Served from the record as read; a value the market\'s record does not carry says not_on_record.',
    schema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker, ISIN or LEI.' }, exchange: { type: 'string', description: 'Optional exchange for a ticker (NASDAQ, LSE, XETRA, TSX, …).' }, market: { type: 'string', description: 'Optional two-letter market code.' } }, required: ['identifier'] } },
  get_auditor: { page: 'https://getauditor.ai/', mcp: 'https://mcp.getauditor.ai/mcp', title: 'Get the auditor of an issuer',
    lead: 'get_auditor is the auditor of an issuer: an issuer by ticker, ISIN or LEI returns its auditor of record and every auditor change on the record, dated — each with its source page and read date, signed by the node of the issuer\'s market and receipted. Where a market\'s record does not carry the auditor, the answer says not_on_record for that market; nothing is inferred.',
    schema: { type: 'object', properties: { issuer: ID, market: { type: 'string', description: 'Optional two-letter market code.' } }, required: ['issuer'] } } };
export const DOOR_NAMES = Object.keys(DOORS);
export const DOOR_TOOLS = DOOR_NAMES.map(n => ({ name: n, title: DOORS[n].title, annotations: { title: DOORS[n].title, ...ANN }, description: DOORS[n].lead + ` Typed errors: unknown_issuer, ambiguous, not_on_record (per field, per market), invalid_request. Door: ${DOORS[n].mcp} (routes to the owning node); every node door answers it for its own market.`, inputSchema: DOORS[n].schema }));
const UA = 'Allooloo node-gate (DOORS-01)';
async function door(host, name, args) {
  const r = await fetch(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': UA }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(25000) });
  const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{'))); const res = j.result || {};
  return res.structuredContent || JSON.parse((res.content || [{ text: '{}' }])[0].text);
}
const validDate = s => { if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false; const d = new Date(s + 'T00:00:00Z'); return !isNaN(d) && d.toISOString().slice(0, 10) === s; };
const day = s => (s ? String(s).slice(0, 10) : null);
const field = (v, cc, recAsOf) => {   // read_date: the field's own read time, else its last_seen, else the record version's as_of (the sweep that read it); the basis is named   // one record field in the door's shape; absent or empty → not_on_record for this market
  if (!v || typeof v !== 'object' || v.value === null || v.value === undefined || v.value === '' || v.value === 'not_found') return { state: 'not_on_record', market: cc, ...(v && v.reason ? { reason: v.reason } : {}) };
  const own = day(v.read_at || v.as_of); const seen = day(v.last_seen);
  return { value: v.value, source: v.source_url || v.source || null, read_date: own || seen || day(recAsOf) || null, read_date_basis: own ? 'the field' : seen ? 'last_seen' : recAsOf ? 'the record version as_of' : null, read_by: v.read_by || null, state: v.state || 'sourced' };
};
async function counted(env, name) { if (!env.X402) return; try { const k = `tot:${name}_receipts`; const n = parseInt((await env.X402.get(k)) || '0', 10) + 1; await env.X402.put(k, String(n)); } catch (e) { } }
async function resolveOne(host, node, idf) {
  const res = await door(host, 'resolve_issuer', { identifier: idf }); const m = (res && res.matches) || []; const cmrs = [...new Set(m.map(x => x.cmr))];
  if (!m.length) return { err: { error: 'unknown_issuer', note: `no issuer on the ${node} register for this identifier` } };
  if (cmrs.length > 1) return { err: { error: 'ambiguous', candidates: m.map(x => ({ cmr: x.cmr, name: x.name, exchange: x.exchange, isin: x.isin || null })), note: 'more than one listing matches: name the exchange or give the ISIN' } };
  return { cmr: cmrs[0], match: m[0] };
}
export async function doorCall(env, ctx, cx, name, args) {
  const { node, host, door: doorUrl } = cx; const cc = node.split('-')[0].toUpperCase(); args = args || {}; const D = DOORS[name];
  const base = { tool: name, node, market: cc, door: doorUrl + '/mcp', page: D.page };
  const mk = String(args.market || '').trim().toLowerCase();
  if (mk && mk !== node.split('-')[0]) return { o: { ...base, error: 'not_on_record', note: `this door holds market ${cc}; ask ${D.mcp}, which routes by issuer and market` }, err: true };
  let idf = String(args.issuer || args.identifier || '').trim(); if (name === 'get_ticker' && args.exchange && idf && !/:/.test(idf) && !/^[A-Z]{2}[A-Z0-9]{9}\d$|^[A-Z0-9]{18}[0-9]{2}$/i.test(idf)) idf = `${String(args.exchange).trim().toUpperCase()}:${idf}`;
  if (!idf) return { o: { ...base, error: 'invalid_request', note: name === 'get_ticker' ? 'identifier (ticker, ISIN or LEI) is required' : 'issuer (ticker, ISIN or LEI) is required' }, err: true };
  const from = String(args.from || '').trim(), to = String(args.to || '').trim() || new Date().toISOString().slice(0, 10);
  if (name === 'get_filings' && (!validDate(from) || !validDate(to) || from > to)) return { o: { ...base, issuer: idf, error: 'invalid_request', note: 'from and to are YYYY-MM-DD dates, from on or before to' }, err: true };
  let r1; try { r1 = await resolveOne(host, node, idf); } catch (e) { return { o: { ...base, issuer: idf, error: 'unavailable', note: `the node's door did not answer (${e.name || 'error'})` }, err: true }; }
  if (r1.err) return { o: { ...base, issuer: idf, ...r1.err }, err: true };
  const cmr = r1.cmr; const at = new Date().toISOString(); let out;
  try {
    if (name === 'get_filings') {
      const rows = []; let cursor = 0;
      for (let i = 0; i < 25; i++) { const p = await door(host, 'list_events_since', { identifier: cmr, since: from, cursor, limit: 200 }); for (const e of (p.events || [])) if ((e.date || '') <= to) rows.push(e); if (p.next_cursor == null) break; cursor = p.next_cursor; }
      rows.sort((a, b) => (a.date || '').localeCompare(b.date || ''));
      out = { ...base, issuer: idf, cmr, from, to, filings: rows.map(e => ({ date: e.date, type: e.event_type || null, category: e.category || null, title: e.title || null, source: e.url || null, read_date: day((e.provenance && e.provenance.fetch_time) || e.read_at) || null, read_by: e.read_by || null, reference: e.reference || null, signature: e.signature || null })), count: rows.length,
        note: 'every disclosure line on the record for this issuer dated in the range, oldest first, each line signed as served; nothing new collected' };
    } else {
      const rec = await door(host, 'get_record', { identifier: cmr }); const idn = (rec && rec.identity) || {};
      if (name === 'get_ticker') {
        const halt = rec && rec.halt; const status = halt && halt.value === true ? { value: 'halted', since: halt.since || null, source: halt.page || halt.source_url || null, read_date: day(halt.read_at) } : halt && halt.value === false ? { value: 'listed, not halted', source: halt.page || halt.source_url || null, read_date: day(halt.read_at) } : { value: 'listed', note: `on the ${node} register as of ${rec.as_of}; the node's halt flag was not read for this record`, read_date: day(rec.as_of) };
        out = { ...base, identifier: idf, cmr, issuer: field(idn.name, cc, rec.as_of), isin: field(idn.isin, cc, rec.as_of), lei: field(idn.lei, cc, rec.as_of), ticker: field(idn.ticker, cc, rec.as_of), listing: { exchange: field(idn.exchange, cc, rec.as_of), security_type: field(idn.security_type, cc, rec.as_of), segment: field(idn.segment || idn.market_segment, cc, rec.as_of) }, status, record: { as_of: rec.as_of, version: rec.version } };
      } else {
        const aud = field(idn.auditor, cc, rec.as_of); const loc = idn.auditor_location ? field(idn.auditor_location, cc, rec.as_of) : null; const fid = idn.auditor_firm_id ? field(idn.auditor_firm_id, cc, rec.as_of) : null;
        const ev = await door(host, 'list_events', { identifier: cmr, type: 'auditor_change', limit: 500 }).catch(() => null);
        let changes;
        if (!ev || ev.error === 'not_built') changes = { state: 'not_on_record', market: cc, reason: `the lifecycle index of ${node} is not built` };
        else if (ev.error === 'unknown_type' || (ev.gaps && ev.gaps.auditor_change)) changes = { state: 'not_on_record', market: cc, reason: (ev.gaps && ev.gaps.auditor_change) || 'the lifecycle index of this market carries no auditor_change type' };
        else changes = (ev.events || []).map(e => ({ date: e.date, title: e.title || null, category: e.category || null, source: e.url || null, read_date: day((e.provenance && e.provenance.fetch_time) || e.read_at) || null, read_by: e.read_by || null, reference: e.reference || null })).sort((a, b) => (a.date || '').localeCompare(b.date || ''));
        out = { ...base, issuer: idf, cmr, name: field(idn.name, cc, rec.as_of), auditor: aud, ...(loc ? { auditor_location: loc } : {}), ...(fid ? { auditor_firm_id: fid } : {}), changes, record: { as_of: rec.as_of, version: rec.version } };
      }
    }
  } catch (e) { return { o: { ...base, issuer: idf, cmr, error: 'unavailable', note: `the node's door did not answer (${e.name || 'error'})` }, err: true }; }
  out.served_utc = at;
  const signed = await signRecord(env, out);
  const rc = await writeReceipt(env, { object: { type: 'cmr', id: cmr }, market: cc, rule_version: `${name}${name === 'get_filings' ? ` · ${from} → ${to}` : ''} · record ${(out.record && out.record.as_of) || ''}`.trim(), decided_at: at,
    answer_hash: await answerHash(signed), actor_class: 'ai-agent (MCP client)', ...(cx.callerKey ? { caller_key: cx.callerKey } : cx.payer ? { caller: 'x402:' + String(cx.payer).toLowerCase() } : {}), ...(cx.settlement ? { settlement: cx.settlement } : {}) }, node);
  const receipt = receiptLinks(rc); if (rc && rc.receipt && rc.receipt.hash) receipt.hash = rc.receipt.hash;
  if (receipt.id) ctx.waitUntil(counted(env, name));
  return { o: { ...signed, receipt }, err: false, receipt_id: receipt.id || null };
}
export const doorsLine = d => DOOR_NAMES.map(n => `<p>${n === 'get_filings' ? 'Filings' : n === 'get_ticker' ? 'Ticker' : 'Auditor'} door: <a href="${d}/mcp">${d}/mcp</a> — ${n}: ${DOORS[n].lead.split(':')[0].replace(/^get_\w+ is /, '')}, from this node's record, signed and receipted (<a href="${DOORS[n].page}">${DOORS[n].page.replace(/^https:\/\//, '').replace(/\/$/, '')}</a>).</p>`).join('');
export const doorsLlms = () => DOOR_NAMES.map(n => `${n} (${DOORS[n].lead.split(':')[0].replace(/^get_\w+ is /, '')} — ${DOORS[n].page})`).join(', ');
export const doorsSkills = d => DOOR_NAMES.map(n => ({ id: n, name: DOORS[n].title, description: DOORS[n].lead, tags: ['capital-markets', 'public-record', 'rco-10060', 'mcp'], examples: [`${n} at ${d}/mcp`] }));
