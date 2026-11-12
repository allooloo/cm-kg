// DOORS-01 (CEO 2026-11-05) — getfilings.ai, getticker.ai, getauditor.ai: three one-tool door pages (kind 'desk'), built to the getasof.ai pattern: same chrome, nav
// (no new nav item; none of the three is current), the hero leads with the tool name as the mark ("get_filings — …"), page title and llms.txt first line the same;
// what it answers, who it is for, what it is not, live tiles read from the record (list_nodes counts and the gate's receipt counter tot:<tool>_receipts on KV
// X402), the tool card, access, machine kit, the Formspree contact form above the footer. No price on the page; the price of a read lives in the machine files
// and the 402 offer. Forwards (getfilings.io, getticker.org/.io, getauditor.org/.io) are whole-zone redirect rules.
import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, esc, int, today, num, table, scale, contactSection } from './chrome.js';
const GI_MCP = 'https://mcp.getissuer.ai/mcp'; const RCO = 'https://mcp.rco-records.ai/mcp';
export const DESKS = [['get_issuer', 'https://getissuer.ai/', 'https://mcp.getissuer.ai/mcp.json'], ['get_orderability', 'https://getorderability.ai/', 'https://mcp.getorderability.ai/mcp.json'], ['get_target_market', 'https://gettargetmarket.ai/', 'https://mcp.gettargetmarket.ai/mcp.json'], ['get_as_of', 'https://getasof.ai/', 'https://mcp.getasof.ai/mcp.json'], ['get_filings', 'https://getfilings.ai/', 'https://mcp.getfilings.ai/mcp.json'], ['get_ticker', 'https://getticker.ai/', 'https://mcp.getticker.ai/mcp.json'], ['get_auditor', 'https://getauditor.ai/', 'https://mcp.getauditor.ai/mcp.json'], ['get_research', 'https://getresearch.ai/', null]];   // USR-03: get_research is the router's own tool (no host of its own): live when the router's tool list carries it (nav02 runDesks)   // FOR DESKS order: nav order first, then the rest
const D = {
  filings: { tool: 'get_filings', host: 'getfilings.ai', mark: 'get_filings — the disclosures of an issuer in a date range, with the receipt.',
    lead: 'get_filings is the disclosures of an issuer in a date range: an issuer by ticker, ISIN or LEI plus a date range returns every filing and release on the record for that issuer in that range, each with its type, its date, its source page and its read date — signed by the node of the issuer\'s market and receipted. Served from the record as read; nothing new is collected and nothing is inferred.',
    answers: ['Input: issuer (ticker, ISIN or LEI) · from (ISO date) · to (ISO date, default today) · market (optional; the owning node resolves it if absent).', 'Output: every disclosure line on the record for the issuer dated in the range, oldest first — date, type, category, title, source page, read date, reference — each line signed as served; the answer signed by the node and its RCO receipt (id, hash).', 'Types: the record\'s own (results, agm_egm, directors_dealings, auditor_change, listing, delisting, name_change and the rest of the market\'s classes); a market whose record does not carry a type says so.'],
    who: 'Compliance, research and surveillance agents that need what an issuer disclosed, and when, before they act or cite it.', not: 'Not a news feed. Not a document archive: each line links to the source. Not a summary. Not a restated history.',
    call: { issuer: 'NASDAQ:AAPL', from: '2026-01-01', to: '2026-06-30' }, tiles: v => [[v.events, 'dated disclosures on the record', 'list_nodes', 'record'], [v.markets, 'markets live', 'list_nodes', 'ring']], fwd: ['getfilings.io'] },
  ticker: { tool: 'get_ticker', host: 'getticker.ai', mark: 'get_ticker — the issuer behind a ticker, with the receipt.',
    lead: 'get_ticker is the issuer behind a ticker: a ticker and its exchange, or an ISIN or LEI, returns the issuer, its ISIN, its LEI, its listing and its status — every value with its source page and read date, signed by the node of the listing\'s market and receipted. Served from the record as read; a value the market\'s record does not carry says not_on_record.',
    answers: ['Input: identifier (ticker, ISIN or LEI) · exchange (optional, for a ticker) · market (optional).', 'Output: the issuer\'s name, ISIN, LEI and ticker; the listing (exchange, security type, segment); the status (listed; halted where the node\'s halt flag says so) — each with its source page and read date; the answer signed by the node and its RCO receipt.', 'A ticker that names more than one listing answers ambiguous with the candidates; name the exchange or give the ISIN.'],
    who: 'Agents resolving a symbol before an order, a read or a citation: order routers, KYC and reference-data checks, research agents.', not: 'Not a price. Not a quote. Not a reference-data licence. Not a symbol guess: a ticker the record does not hold answers unknown_issuer.',
    call: { identifier: 'AAPL', exchange: 'NASDAQ' }, tiles: v => [[v.records, 'issuers on the record', 'list_nodes', 'issuer'], [v.markets, 'markets live', 'list_nodes', 'ring']], fwd: ['getticker.org', 'getticker.io'] },
  auditor: { tool: 'get_auditor', host: 'getauditor.ai', mark: 'get_auditor — the auditor of an issuer and every change, with the receipt.',
    lead: 'get_auditor is the auditor of an issuer: an issuer by ticker, ISIN or LEI returns its auditor of record and every auditor change on the record, dated — each with its source page and read date, signed by the node of the issuer\'s market and receipted. Where a market\'s record does not carry the auditor, the answer says not_on_record for that market; nothing is inferred.',
    answers: ['Input: issuer (ticker, ISIN or LEI) · market (optional).', 'Output: the auditor of record (with its location and firm id where the record carries them) and every auditor change on the record, dated, each with its source page and read date; the answer signed by the node and its RCO receipt.', 'not_on_record names the market and the record\'s own reason where it states one; a market whose lifecycle index carries no auditor_change says so for the changes.'],
    who: 'Due-diligence, audit-committee, model-risk and counterparty agents that cite who audits an issuer and since when.', not: 'Not an opinion on audit quality. Not an audit. Not a rating. Not inferred from a name.',
    call: { issuer: 'NASDAQ:AAPL' }, tiles: v => [[v.records, 'issuers on the record', 'list_nodes', 'issuer'], [v.markets, 'markets live', 'list_nodes', 'ring']], fwd: ['getauditor.org', 'getauditor.io'] } };
const KIT = ['/llms.txt', '/index.md', '/facts.json', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/x402.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/mcp.json'];
const ERRORS = [['unknown_issuer', 'no issuer on the register for this identifier'], ['ambiguous', 'more than one listing matches; the candidates are named'], ['not_on_record', 'the market\'s record does not carry this field; the market and the record\'s reason are named'], ['invalid_request', 'a required argument is missing or not a date']];
export function classifyD(h) {
  for (const [k, d] of Object.entries(D)) { if (h === d.host) return { kind: 'desk', key: k }; if (d.fwd.includes(h)) return { kind: 'redirect', canonical: `https://${d.host}`, status: 301 }; }
  return null;
}
export const serveAs = h => { const m = /^www\.(get(filings|ticker|auditor)\.ai)$/.exec(h || ''); return m ? m[1] : null; };
const mcpOf = d => `https://mcp.${d.host}/mcp`; const agentOf = d => `https://agent.${d.host}/.well-known/agent-card.json`;
let RC = {}, RC_AT = {};
export async function deskData(env, key) {
  const t = D[key].tool; if (RC[t] != null && Date.now() - (RC_AT[t] || 0) < 300000) return { receipts: RC[t] };
  let n = null; try { if (env.X402) { const v = await env.X402.get(`tot:${t}_receipts`); n = v == null ? 0 : parseInt(v, 10); } } catch (e) { n = null; }
  if (n != null) { RC[t] = n; RC_AT[t] = Date.now(); } return { receipts: n };
}
const totals = live => { const l = Object.values(live || {}).filter(n => n && n.live); return { records: l.reduce((a, n) => a + (Number(n.records) || 0), 0), events: l.reduce((a, n) => a + (Number(n.events) || 0), 0), markets: l.length, asOf: l.map(n => String(n.as_of || '')).sort().slice(-1)[0] || today() }; };
const h2 = (id, n, t) => `<h2 id="${id}">${n ? n + ' ' : ''}${esc(t)}</h2>`;
export const titleD = c => D[c.key].mark; export const h1D = c => D[c.key].mark;
export function deskBody(c, ctx, host) {
  const d = D[c.key]; const v = totals(ctx.live); const dd = ctx.desk || {};
  const call = { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: d.tool, arguments: d.call } }; const install = JSON.stringify({ mcpServers: { [d.tool.replace('_', '')]: { type: 'http', url: mcpOf(d) } } }, null, 2);
  const tv = d.tiles({ records: esc(int(v.records)), events: esc(int(v.events)), markets: esc(int(v.markets)) });
  return `<p class="kicker">${esc(d.tool)} · on the record</p>
${scale(tv.concat([[dd.receipts != null ? esc(int(dd.receipts)) : '', 'receipts written', `${d.tool} reads, receipted`, 'key']]))}<p class="src">read at render: list_nodes at <code>${esc(GI_MCP)}</code> and the gate's receipt counter</p>
<p class="lead">${esc(d.lead)}</p>
${h2('answers', 1, 'What it answers')}${num(1, d.answers.map(esc))}
${h2('who', 2, 'Who it is for')}<p>${esc(d.who)}</p>
${h2('not', 3, 'What it is not')}<p><strong>${esc(d.not)}</strong></p>
${h2('tool', 4, 'The tool')}${table(['typed error', 'when'], ERRORS.map(([e, w]) => [`<code>${esc(e)}</code>`, esc(w)]))}${num(4, [`One call: <pre>${esc(JSON.stringify(call))}</pre> at <code>${esc(mcpOf(d))}</code> .`, `Every answer is signed by the node of the issuer's market (EdDSA, kid allooloo-cmr-2026-10, keyring <a href="https://allooloo.ai/.well-known/jwks.json">allooloo.ai/.well-known/jwks.json</a>) and receipted at <code>${esc(RCO)}</code> with the node as writer; verify_receipt is public.`, 'Paying for a read: every read is free unless the agent asks for the offer (header <code>x402-pay: 1</code>); the door then answers HTTP 402 with a signed offer and the same call carries the payment and the receipt — <a href="https://data-paygo.ai/">data-paygo.ai</a>.'])}
${h2('access', 5, 'Access')}<pre>${esc(install)}</pre><pre>claude mcp add --transport http ${esc(d.tool.replace('_', ''))} ${esc(mcpOf(d))}</pre>${num(5, [`Door: <code>${esc(mcpOf(d))}</code> — the same router as <code>${esc(GI_MCP)}</code> : index only; read-only, no authentication, no account. The call is routed to the node of the issuer's listing; the node reads the record, signs and receipts.`, `Agent Card (A2A): <a href="${agentOf(d)}"><code>${esc(agentOf(d))}</code></a> .`, `Every node door answers ${esc(d.tool)} for its own market (<code>mcp.&lt;market&gt;-cm-kg.ai/mcp</code>).`, `Registry entry: <code>registry.modelcontextprotocol.io · io.github.allooloo/${esc(d.tool.replace('_', ''))}</code>.`])}
${h2('kit', 6, 'Machine kit')}${num(6, [KIT.map(x => `<a href="${x}"><code>${x}</code></a>`).join(' · '), `Forwards here (301, whole zone): ${d.fwd.join(', ')}.`])}${contactSection(host)}`;
}
const doorsList = () => DESKS.map(([t, u]) => `${t} ${u}`);
export function factsD(c, host, live, ctx) {
  const d = D[c.key]; const v = totals(live);
  return { domain: host, kind: 'product door', product: `${d.tool} — ${d.mark.split(' — ')[1].replace(/\.$/, '')}`, head: d.mark.replace(/\.$/, ''), definition: d.lead, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: v.asOf, surface_version: SURFACES_VERSION, source: 'public-record',
    issuers_on_record: v.records, disclosures_on_record: v.events, markets_live: v.markets, receipts_written: ctx && ctx.desk ? ctx.desk.receipts : null, counts_from: 'list_nodes and the gate counter, read at render', mcp_url: mcpOf(d), agent_card: agentOf(d), tools: [d.tool, 'resolve_issuer', 'list_nodes'], errors: ERRORS.map(([e]) => e), receipts: RCO,
    price: { lane: 'x402 per-call till (USDC and Open USD on Base)', offer: 'the HTTP 402 offer on the door, only when asked (x402-pay: 1)', unit: 'one record read', pricing: `https://mcp.${d.host}/x402/pricing.json` }, licence: 'https://data-licence.ai/', doors: doorsList(), forwards_here: d.fwd, registry: `io.github.allooloo/${d.tool.replace('_', '')}`, machine_paths: KIT };
}
export function llmsD(c, host, live, ctx) {
  const d = D[c.key]; const v = totals(live); const call = { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: d.tool, arguments: d.call } };
  return [`# ${d.mark}`, `1. ${d.lead}`, `2. At render: ${v.records} issuers on the record · ${v.events} dated disclosures · ${v.markets} markets live (list_nodes); receipts written ${ctx && ctx.desk && ctx.desk.receipts != null ? ctx.desk.receipts : 'not read'}.`, `3. Door: ${mcpOf(d)} (MCP Streamable HTTP, no auth) — the same router as ${GI_MCP}. Agent Card: ${agentOf(d)}.`,
    `4. Tools: ${d.tool}, with resolve_issuer · list_nodes on the same door; every node door answers ${d.tool} for its own market.`, `5. One call: ${JSON.stringify(call)}`, '6. Typed errors: ' + ERRORS.map(([e, w]) => `${e} (${w})`).join(' · ') + '. Nothing is inferred.',
    `7. Provenance: the producing node signs (EdDSA, kid allooloo-cmr-2026-10, keyring https://allooloo.ai/.well-known/jwks.json); every read is receipted at ${RCO} (writer: the node, under the Allooloo writer key); verify_receipt is public.`, '8. Price: x402 on the per-call till, USDC and Open USD on Base; reads are free and the HTTP 402 offer answers only when asked (x402-pay: 1); the price of a read is the till\'s, quoted in the offer. Licence: https://data-licence.ai/',
    `9. ${d.not}`, '10. Doors: ' + doorsList().join(' · '), `11. Forwards here (301, whole zone): ${d.fwd.join(', ')}. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`, `12. Machine paths: ${KIT.join(' ')}`, `13. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
}
export function agentCardD(c, host) {
  const d = D[c.key];
  return { name: d.tool.replace('_', ''), description: d.lead, url: mcpOf(d), preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: mcpOf(d), transport: 'JSONRPC' }], additionalInterfaces: [{ url: GI_MCP, transport: 'JSONRPC', description: 'the same router (getissuer)' }], securitySchemes: {}, security: [],
    defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], iconUrl: `https://${host}/icon-512.png`, provider: { organization: OPERATOR, url: CORPORATE }, version: SURFACES_VERSION, documentationUrl: `https://${host}/llms.txt`, protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false },
    skills: [{ id: d.tool, name: d.mark, description: d.lead, tags: ['capital-markets', 'public-record', 'rco-10060', 'mcp'], examples: [JSON.stringify(d.call)] }], 'x-allooloo': { page: `https://${host}/`, router_card: agentOf(d), receipts: RCO, doors: doorsList() } };
}
export const descriptorD = c => { const d = D[c.key]; return { name: d.tool.replace('_', ''), kind: 'pointer (the door is the router)', url: mcpOf(d), mcp_json: `https://mcp.${d.host}/mcp.json`, agent_card: agentOf(d), tools: [d.tool, 'resolve_issuer', 'list_nodes'], authentication: 'none', operator: OPERATOR }; };
export const x402D = c => { const d = D[c.key]; return { x402Version: 2, resource: mcpOf(d), lane: 'the per-call till: x402 v2, scheme exact, Base (eip155:8453); USDC (EIP-3009) first, Open USD (Permit2, gas-sponsored) second', when: 'reads are free; the HTTP 402 offer answers only when the agent asks (x402-pay: 1) or sends a payment', price: { unit: 'one record read', pricing: `https://mcp.${d.host}/x402/pricing.json` }, receipt: 'a paid read\'s RCO receipt names its settlement (network and transaction)', operator: OPERATOR }; };
export const descD = c => `${D[c.key].mark} One MCP door at ${mcpOf(D[c.key])}.`;
export const targetD = c => ({ kind: 'apex', mcp: mcpOf(D[c.key]), agent: agentOf(D[c.key]), openapi: null, mcpjson: `https://mcp.${D[c.key].host}/mcp.json`, name: D[c.key].tool.replace('_', '') });
export const pathsD = () => ['/'].concat(KIT);
export const sweepD = live => totals(live).asOf;
