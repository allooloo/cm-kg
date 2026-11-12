// research.js — USR-03 (2026-11-11): get_research, the eighth door, answered by the apex router. Data Research: one research page per listed company on the
// record, written from the signed record (CM-KG\RAILS\research: rollup → orderability → coverage → write), held in the page store (KV allooloo-research,
// binding RESEARCH; key p:<cmr>) and served here signed (kid allooloo-cmr-2026-10), dated (the record's as_of) and receipted at mcp.rco-records.ai
// (writer allooloo) before the answer leaves. The router resolves the issuer on its owning node (resolve_issuer on the node's regional door), then reads the
// page for that record key. The page is the record's research on the issuer — no analyst, no rating, no view. A licensed row is served only to an agent whose
// firm holds that licence; none is loaded. Typed errors: unknown_issuer · ambiguous · no_page · invalid_request · unavailable.
import { signRecord } from './cmrsign.js';
import { answerHash, writeReceipt, receiptLinks } from './rco.js';
const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
export const RESEARCH_NAME = 'get_research';
export const RESEARCH_PAGE = 'https://getresearch.ai/';
export const RESEARCH_FENCE = "The page is the record's research on the issuer — no analyst, no rating, no view.";
export const RESEARCH_LEAD = `get_research is Data Research: one research page per listed company on the record, written from the signed record — identity and listing, the disclosure read (filings in the trailing twelve months, cadence, latency against the issuer's exchange and sector), auditor, events and halts, orderability, coverage, open research, licensed (none loaded), as-of depth and sources — with its as-of date and its receipt. ${RESEARCH_FENCE}`;
export const RESEARCH_TOOL = { name: RESEARCH_NAME, title: 'Get the research page of an issuer', annotations: { title: 'Get the research page of an issuer', ...ANN },
  description: RESEARCH_FENCE + ' ' + RESEARCH_LEAD.replace(' ' + RESEARCH_FENCE, '') + ' Input: ticker with exchange, or ISIN, or LEI. Output: the page (sections and Markdown), its numbers with the source page and read date of every value, its as-of date, the signature and the RCO receipt. Typed errors: unknown_issuer, ambiguous, no_page, invalid_request. Page: https://getresearch.ai/',
  inputSchema: { type: 'object', properties: { ticker: { type: 'string', description: 'Ticker (AAPL), with exchange in the exchange argument or as NASDAQ:AAPL.' }, exchange: { type: 'string', description: 'Exchange for the ticker (NASDAQ, NYSE, LSE, TSX, …).' }, isin: { type: 'string', description: 'ISIN (12 characters).' }, lei: { type: 'string', description: 'LEI (20 characters).' } } } };
export const researchKey = cmr => 'p:' + cmr;
export async function researchCall(env, cx, args, { whichNode, forward }) {
  args = args || {}; const base = { tool: RESEARCH_NAME, door: 'https://mcp.getissuer.ai/mcp', page: RESEARCH_PAGE };
  const isin = String(args.isin || '').trim().toUpperCase(), lei = String(args.lei || '').trim().toUpperCase(), tick = String(args.ticker || args.identifier || args.issuer || '').trim(), ex = String(args.exchange || '').trim().toUpperCase();
  const idf = isin || lei || (tick && ex && !/:/.test(tick) ? `${ex}:${tick}` : tick);
  if (!idf) return { o: { ...base, error: 'invalid_request', note: 'give a ticker with its exchange, or an ISIN, or an LEI' }, isError: true };
  if (!env.RESEARCH) return { o: { ...base, issuer: idf, error: 'unavailable', note: 'the page store is not bound on this router' }, isError: true };
  const w = whichNode(idf);
  if (!w.nodes.length) return { o: { ...base, issuer: idf, error: 'unknown_issuer', note: 'no node in the index holds this identifier' }, isError: true };
  if (w.nodes.length > 1) return { o: { ...base, issuer: idf, error: 'ambiguous', nodes: w.nodes, note: 'listed on more than one node: give the exchange with the ticker, or the ISIN' }, isError: true };
  const node = w.nodes[0]; const res = await forward(node, 'resolve_issuer', { identifier: idf });
  if (!res || res.error === 'unavailable') return { o: { ...base, issuer: idf, node, error: 'unavailable', note: "the node's door did not answer; nothing is answered from memory" }, isError: true };
  const m = (res && res.matches) || []; const cmrs = [...new Set(m.map(x => x.cmr).filter(Boolean))];
  if (!cmrs.length) return { o: { ...base, issuer: idf, node, error: 'unknown_issuer', note: `no issuer on the ${node} register for this identifier` }, isError: true };
  if (cmrs.length > 1) return { o: { ...base, issuer: idf, node, error: 'ambiguous', candidates: m.map(x => ({ cmr: x.cmr, name: x.name, exchange: x.exchange, isin: x.isin || null })), note: 'more than one listing matches: name the exchange or give the ISIN' }, isError: true };
  const cmr = cmrs[0]; let pg = null; try { pg = await env.RESEARCH.get(researchKey(cmr), 'json'); } catch (e) { pg = null; }
  if (!pg) return { o: { ...base, issuer: idf, cmr, node, error: 'no_page', note: 'the issuer is on the record; its research page is not written yet for this market' }, isError: true };
  const at = new Date().toISOString();
  const out = { ...base, issuer: idf, cmr, node: pg.node, market: pg.market, fence: pg.fence, title: pg.title, as_of: pg.as_of, page_url: 'https://getresearch.ai' + pg.path, numbers_hash: pg.numbers_hash, writer: pg.writer, sections: pg.sections, markdown: pg.markdown, sources: pg.sources, numbers: pg.numbers,
    licensed: { rows: [], rule: pg.numbers && pg.numbers.licensed ? pg.numbers.licensed.rule : null, note: 'none loaded' }, served_utc: at };
  const signed = await signRecord(env, out);
  const rc = await writeReceipt(env, { object: { type: 'cmr', id: cmr }, market: pg.market, rule_version: `get_research · record ${pg.as_of} · page ${String(pg.numbers_hash).slice(7, 23)}`, decided_at: at, answer_hash: await answerHash(signed), actor_class: 'ai-agent (MCP client)',
    ...(cx.callerKey ? { caller_key: cx.callerKey } : cx.settlement && cx.settlement.payer ? { caller: 'x402:' + String(cx.settlement.payer).toLowerCase() } : {}), ...(cx.settlement ? { settlement: { network: cx.settlement.network, transaction: cx.settlement.transaction } } : {}) });
  const receipt = receiptLinks(rc); if (rc && rc.receipt && rc.receipt.hash) receipt.hash = rc.receipt.hash;
  if (receipt.id && env.X402 && cx.ctx) cx.ctx.waitUntil((async () => { try { const n = parseInt((await env.X402.get('tot:get_research_receipts')) || '0', 10) + 1; await env.X402.put('tot:get_research_receipts', String(n)); } catch (e) { } })());
  return { o: { ...signed, receipt }, isError: false, receipt_id: receipt.id || null };
}
