// ASOF-01 (CEO 2026-11-04/05) — getasof.ai, the point-in-time door's page (the As Of tab), built to the getorderability.ai page pattern (getord.js): same chrome,
// nav (As Of current), eyebrow, numbered sections, live tiles, access block, markets table, machine kit, contact, closing card, footer. The copy is the build
// book's (START_ME_UP\getasof_Build-Book_v1.0_2026-11-04.docx §2-§8), verbatim where it is copy of record; the hero is the book's working line (the CEO cuts the
// final). Standing rules over the book: no typed count in page text ("Five sealed years" reads "Sealed years"), no price on the human page (the price of a read
// lives in the machine files and the 402 offer only), no company money figure. Tiles read at render: sealed years and markets sealed from the shelf ledger
// (shelf/state.json, tools.replay — written by the apex job; a market lights only when its ledger entry is complete and its manifests verify), receipts
// written from the gate's counter (KV X402 tot:asof_receipts; binding X402 on getasof-pages). getasof.com/.org/.io 301 here, whole zone (a redirect rule).
import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, esc, int, today, num, table, scale, contactSection } from './chrome.js';
export const AS = 'https://getasof.ai';
const MCP = 'https://mcp.getasof.ai/mcp';
const AGENT = 'https://agent.getasof.ai/.well-known/agent-card.json';
const GI_MCP = 'https://mcp.getissuer.ai/mcp';
const RCO = 'https://mcp.rco-records.ai/mcp';
export const TAG = 'Point-in-time proof.';
export const BAND = 'Others sell point-in-time data; Allooloo sells point-in-time proof. The issuer record as it stood on any date, signed by the node of its market and receipted on the Record of Cleared Orders, callable by any agent over MCP and A2A.';
export const TITLE = 'get_as_of — the issuer record, as of any date, with the receipt.';   // ASOF-01 rider (CEO): the tool name as the mark, the gettargetmarket.ai pattern; title, hero, twin and llms.txt first line the same
export const H1 = TITLE;   // ASOF-01 rider: the CEO's cut of the book's working line
export const LEAD = 'get_as_of is the issuer record as it stood on a date: an issuer by ticker, ISIN or LEI plus a date returns the signed record of that day — every field with its source and read date, the sealed disclosure lines of the market-year up to that date — signed by the node of the issuer\'s market and receipted, so a backtest can show what it read and when. Nothing is restated and nothing is filled backwards: before the record existed the answer says before_record; in a market-year not yet sealed it says not_sealed and names the earliest sealed date.';   // THE LIBRARY: the definition line, the shape of get_issuer and get_target_market (the gate's ASOF_LEAD, verbatim)
export function classifyA(h) {
  if (h === 'getasof.ai') return { kind: 'asof' };
  if (/^getasof\.(com|org|io)$/.test(h)) return { kind: 'redirect', canonical: AS, status: 301 };   // the zones carry the whole-zone rule; this is the Worker's answer if one reaches it
  return null;
}
export const serveAs = h => /^www\.getasof\.ai$/.test(h || '') ? 'getasof.ai' : null;
// ---------- read at render (five-minute cache in the isolate)
let D = null, D_AT = 0;
export async function asofData(env, url) {
  if (D && Date.now() - D_AT < 300000) return D;
  let shelf = null; try { const r = await env.ASSETS.fetch(new Request(new URL('/shelf/state.json', url).toString())); shelf = r.ok ? await r.json() : null; } catch (e) { shelf = null; }
  const rep = (shelf && shelf.tools && shelf.tools.replay) || null;
  let receipts = null; try { if (env.X402) { const v = await env.X402.get('tot:asof_receipts'); receipts = v == null ? 0 : parseInt(v, 10); } } catch (e) { receipts = null; }
  const years = rep ? [...new Set(Object.values(rep).flat())].sort() : [];
  const d = { markets: rep ? Object.keys(rep).sort() : null, years, per: rep || {}, receipts, shelf_read_utc: shelf ? (shelf.updated_utc || null) : null, read_at: new Date().toISOString() };
  if (rep) { D = d; D_AT = Date.now(); }   // a failed ledger read is not kept: the next render reads again
  return d;
}
const sweepDate = live => Object.values(live || {}).filter(n => n && n.live && n.as_of).map(n => String(n.as_of)).sort().slice(-1)[0] || today();
// ---------- the copy (book §2 · §3 · §4 · §5 · §8)
const IS = ['Built specifically so an AI agent can read the issuer record as it stood on any date since 2021, with the proof that it read it.', 'Any agent gets in; it pays in the call. A firm licenses the vintage.', 'Sealed years, 2021 forward, done. Each market lights as its vintage seals.'];
const IS_NOT = 'Not a price. Not a terminal. Not a news feed. Not a restated dataset.';
const EDGE_LEAD = 'Point-in-time fundamentals exist as premium products elsewhere; replay exists on terminals. "As of a date" alone is not the edge. The edge is five things the record already has by construction, which no feed vendor built:';
const EDGE = [['Two clocks', 'Every fact carries when it was true in the world (effective) and when the record learned it (read date). get_as_of answers on the second clock — what was knowable that day. That is the only honest basis for a backtest; most feeds have one clock and overwrite.'],
  ['Append-only, signed versions', 'Nothing is restated in place. A change is a new signed version; the old one is kept. The as-of answer is a lookup, never a recomputation, so it is the same answer forever.'],
  ['Per-field provenance', 'Source page and read date on every field. A regulator\'s restatement and our re-read are distinguishable.'],
  ['Receipts (RCO)', 'Every read writes an RCO-10060 receipt chaining the answer hash. The firm can prove what a model relied on.'],
  ['Agent-native, open', 'MCP door, verb-object tool name, human page free to read, x402 to pay. Built for the reader that is actually arriving — an agent — not a human with a seat.']];
const EDGE_LINE = 'Others sell point-in-time data; Allooloo sells point-in-time proof.';
const RCO_LINES = ['Each get_as_of read is cleared and receipted: subject, jurisdiction, rule version, the stated time of the read, the hash of the signed answer, and the link to the previous receipt in the chain. The door signs the receipt; the producing node signs the content under the record key.',
  'verify_receipt is public. Anyone holding the receipt and the answer can confirm the answer is the one that was served, unaltered.',
  'A firm\'s own auditor key (issue_auditor_key) lets model-risk, internal audit or an external auditor list and verify every as-of read behind a model — the signed input list of a backtest, replayable to any date.',
  'The quant\'s artefact is therefore not a CSV. It is a receipt chain: a signed, chained statement of every record the model read, as of when, and what it said. Model validation, MiFID II record-keeping and SR 11-7 style reviews want exactly this and have never been able to buy it.',
  'KYP the facts · Issuerwire the news · RCO the proof.'];
const CALL = { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'get_as_of', arguments: { issuer: 'NASDAQ:MSFT', as_of: '2023-03-15' } } };
export const ERRORS = [['unknown_issuer', 'no issuer on the register for this identifier'], ['before_record', 'the record did not exist on that date; nothing is inferred backwards'], ['not_sealed', 'the market-year is not yet sealed; the answer names the earliest sealed date (and, in the current year, the date it is sealed through); no partial vintage is served as final'], ['not_found', 'the market or record asked for is not on this door']];
const CONTRACT = [['Input', 'issuer (ticker, ISIN or LEI) · as_of (ISO date) · market (optional; the owning node resolves it if absent)'],
  ['Output', 'The signed issuer record version whose validity covers as_of: every field with value, source page, read date and effective date; version id; node signature and key id (kid); the RCO receipt (id, hash)'],
  ['Receipt', 'Written on every cleared read under the Allooloo writer key; the receipt id is returned in the answer.']];
const LANES = [['Agent, per read', 'x402 on the existing per-call till. USDC and Open USD on Base.', 'https://data-paygo.ai/'], ['Firm, licence', 'Data Vintage enterprise licence.', 'https://data-licence.ai/'], ['Audit', 'issue_auditor_key — the firm\'s own key to list and verify its receipt chain.', 'https://rco-records.ai/']];
const PATH = ['Store: the Replay store under Data Vintage — sealed market-years, 2021 forward. get_as_of is a read over it. No new store, no second copy of the history.',
  'Index: the router holds an index only; the record is served by the owning node\'s regional door in its own jurisdiction. getasof.ai routes the same way.',
  'Nightly: the OpsAgents re-slate the trading day; a sealed year is immutable thereafter. Receipts chain per writer.',
  'Two clouds: Azure primary, AWS warm standby (Data Ark). The vintage and the receipt chain are both in the ark.',
  'Markets light one by one as each vintage seals (us first, then the roster). The door answers not_sealed until then rather than guessing.'];
const KIT = ['/llms.txt', '/index.md', '/facts.json', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/x402.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/mcp.json'];
const FORWARDS = ['getasof.com', 'getasof.org', 'getasof.io'];
const h2 = (id, n, t) => `<h2 id="${id}">${n ? n + ' ' : ''}${esc(t)}</h2>`;
const linkify = s => esc(s).replace(/RCO-10060/g, '<a href="https://rco-10060.org/">RCO-10060</a>').replace(/Data Vintage/g, '<a href="https://data-vintage.ai/">Data Vintage</a>').replace(/Data Ark/g, '<a href="https://data-ark.ai/">Data Ark</a>');
export function tiles(d) {
  return scale([[d && d.years.length ? esc(int(d.years.length)) : '', 'sealed years', d && d.years.length ? `${d.years[0]} → ${d.years[d.years.length - 1]}` : '', 'record'], [d && d.markets ? esc(int(d.markets.length)) : '', 'markets sealed', d && d.markets ? d.markets.join(' · ') : '', 'ring'], [d && d.receipts != null ? esc(int(d.receipts)) : '', 'receipts written', 'get_as_of reads, receipted', 'key']]);
}
export function asofBody(ctx, host) {
  const d = ctx.asof || null; const live = ctx.live || {};
  const install = JSON.stringify({ mcpServers: { getasof: { type: 'http', url: MCP } } }, null, 2);
  const rows = Object.values(live).filter(n => n && n.node).sort((a, b) => a.node.localeCompare(b.node)).map(n => { const cc = n.node.slice(0, 2); const ys = (d && d.per[cc]) || null;
    return [`<code class="nw">${esc(n.node)}</code>`, esc(n.country || ''), ys ? `<span class="n">${esc(ys[0])} → ${esc(ys[ys.length - 1])}</span>` : '<span class="muted">not sealed yet — the door answers not_sealed</span>', esc(n.live ? 'live' : 'not live')]; });
  return `<p class="kicker">As Of · on Data Vintage · Replay</p>
${tiles(d)}<p class="src">read at render: the shelf ledger (shelf/state.json, tools.replay) and the gate's receipt counter${d && d.shelf_read_utc ? ` · ledger ${esc(d.shelf_read_utc.slice(0, 10))}` : ''}</p>
<p class="lead">${esc(LEAD)}</p>
${h2('what', 1, 'What it is')}${num(1, IS.map(linkify))}
${h2('not', 2, 'What it is not')}<p><strong>${esc(IS_NOT)}</strong></p>
${h2('tool', 3, 'The tool')}${table(['field', 'specification'], CONTRACT.map(([k, v]) => [esc(k), esc(v)]))}${table(['typed error', 'when'], ERRORS.map(([e, w]) => [`<code>${esc(e)}</code>`, esc(w)]))}${num(3, [`One call: <pre>${esc(JSON.stringify(CALL))}</pre> at <code>${esc(MCP)}</code> .`, 'Nothing is answered from memory. Identity fields answer on the read-date clock: a field is held only if the record had read it by the date asked; the disclosure lines are the sealed vintage — public filings dated on or before that date, each with its source and read date, each signed.', 'Paying for a read: every read is free unless the agent asks for the offer (header <code>x402-pay: 1</code>); the door then answers HTTP 402 with a signed offer and the same call carries the payment and the receipt — <a href="https://data-paygo.ai/">data-paygo.ai</a>.'])}
${h2('edge', 4, 'The edge')}<p>${esc(EDGE_LEAD)}</p>${table(['property', 'what it means for a quant'], EDGE.map(([k, v]) => [esc(k), linkify(v)]))}<p><strong>${esc(EDGE_LINE)}</strong></p>
${h2('receipts', 5, 'The proof')}${num(5, RCO_LINES.map(linkify))}
${h2('access', 6, 'Access')}<p>Any MCP client that speaks Streamable HTTP:</p><pre>${esc(install)}</pre><p>Claude Code:</p><pre>claude mcp add --transport http getasof ${esc(MCP)}</pre>${num(6, [`Door: <code>${esc(MCP)}</code> — the same router as <code>${esc(GI_MCP)}</code> : same index, no second copy of the history; read-only, no authentication, no account. get_as_of is routed to the node of the issuer's listing; the node signs and receipts; the router forwards.`, `Agent Card (A2A): <a href="${AGENT}"><code>${esc(AGENT)}</code></a> .`, 'Tools: <code>get_as_of</code>, with <code>resolve_issuer</code> · <code>list_events_since</code> · <code>list_nodes</code> on the same door. list_events_since stays where it is; get_as_of reads the same history.', 'Regional doors: every node door answers get_as_of for its own market (<code>mcp.&lt;market&gt;-cm-kg.ai/mcp</code>, <code>&lt;market&gt;.eu-cm-kg.ai/mcp</code>).', 'Registry entry: <code>registry.modelcontextprotocol.io · io.github.allooloo/getasof</code>.'])}
${h2('lanes', 7, 'Lanes')}${table(['lane', 'what', 'where'], LANES.map(([l, w, u]) => [esc(l), esc(w), `<a href="${u}">${esc(u.replace(/^https:\/\//, '').replace(/\/$/, ''))}</a>`]))}
${h2('path', 8, 'Data path')}${num(8, PATH.map(linkify))}
${h2('markets', 9, 'Markets')}<div class="wrap">${table(['node', 'market', 'sealed vintage', 'state'], rows)}</div><p class="src">source: list_nodes at <code>${esc(GI_MCP)}</code> and the shelf ledger, read at render</p>
${h2('kit', 10, 'Machine kit')}${num(10, [KIT.map(x => `<a href="${x}"><code>${x}</code></a>`).join(' · '), `Forwards here (301, whole zone): ${FORWARDS.join(', ')}.`])}${contactSection(host)}`;
}
export function factsA(host, live, d) {
  return { domain: host, kind: 'product door', product: 'As Of — the point-in-time door (get_as_of)', head: H1.replace(/\.$/, ''), definition: LEAD, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: sweepDate(live), surface_version: SURFACES_VERSION, source: 'public-record',
    shelf: 'Data Vintage · Replay (the shelf of record is unchanged; getasof.ai is Replay\'s door)', sealed_years: d ? d.years : null, markets_sealed: d ? d.markets : null, receipts_written: d ? d.receipts : null, counts_from: 'the shelf ledger (shelf/state.json tools.replay) and the gate counter (tot:asof_receipts), read at render',
    mcp_url: MCP, same_router_as: GI_MCP, agent_card: AGENT, tools: ['get_as_of', 'resolve_issuer', 'list_events_since', 'list_nodes'], errors: ERRORS.map(([e]) => e), receipts: RCO,
    price: { lane: 'x402 per-call till (USDC and Open USD on Base)', offer: 'the HTTP 402 offer on the door, only when asked (x402-pay: 1)', get_as_of: 'price to be set (the CEO\'s); the offer quotes the till\'s one-record-read amount until it is', pricing: 'https://mcp.getasof.ai/x402/pricing.json' },
    licence: 'https://data-licence.ai/', doors: ['get_issuer https://getissuer.ai/', 'get_orderability https://getorderability.ai/', 'get_target_market https://gettargetmarket.ai/', 'get_as_of https://getasof.ai/', 'get_filings https://getfilings.ai/', 'get_ticker https://getticker.ai/', 'get_auditor https://getauditor.ai/', 'get_research https://getresearch.ai/'], products: ['Issuer https://getissuer.ai/', 'Orderability https://getorderability.ai/', 'Target Market https://gettargetmarket.ai/', 'As Of https://getasof.ai/', 'Issuerwire https://issuerwire.ai/'], forwards_here: FORWARDS, registry: 'io.github.allooloo/getasof', machine_paths: KIT };
}
export function llmsA(host, live, d) {
  return [`# ${TITLE}`, `1. ${LEAD}`,
    `2. At render: sealed years ${d && d.years.length ? d.years.join(', ') : 'not read'}; markets sealed ${d && d.markets ? d.markets.join(', ') : 'not read'}; receipts written ${d && d.receipts != null ? d.receipts : 'not read'} (the shelf ledger and the gate counter).`,
    `3. Door: ${MCP} (MCP Streamable HTTP, no auth) — the same router as ${GI_MCP}: same index, no second copy of the history. Agent Card: ${AGENT}.`, '4. Tools: get_as_of(issuer, as_of, market?), with resolve_issuer · list_events_since · list_nodes on the same door; every node door answers get_as_of for its own market.',
    `5. One call: ${JSON.stringify(CALL)}`, '6. Typed errors: ' + ERRORS.map(([e, w]) => `${e} (${w})`).join(' · ') + '. Nothing is answered from memory.',
    `7. Provenance: the producing node signs the answer (EdDSA, kid allooloo-cmr-2026-10, keyring https://allooloo.ai/.well-known/jwks.json); every read is receipted at ${RCO} (writer: the node, under the Allooloo writer key); verify_receipt is public; issue_auditor_key gives a firm its own key to list and verify its receipt chain.`,
    '8. Price: x402 on the per-call till, USDC and Open USD on Base; reads are free and the HTTP 402 offer answers only when asked (x402-pay: 1). The get_as_of price of record is the CEO\'s: price to be set. Pricing: https://mcp.getasof.ai/x402/pricing.json · licence: https://data-licence.ai/',
    `9. ${IS_NOT} ${EDGE_LINE}`, '10. Products: Issuer https://getissuer.ai/ · Orderability https://getorderability.ai/ · Target Market https://gettargetmarket.ai/ · As Of https://getasof.ai/ · Issuerwire https://issuerwire.ai/ · Doors: get_issuer https://getissuer.ai/ · get_orderability https://getorderability.ai/ · get_target_market https://gettargetmarket.ai/ · get_as_of https://getasof.ai/ · get_filings https://getfilings.ai/ · get_ticker https://getticker.ai/ · get_auditor https://getauditor.ai/ · get_research https://getresearch.ai/',   // DOORS-01: the doors order · USR-03
    `11. Forwards here (301, whole zone): ${FORWARDS.join(', ')}. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`, `12. Machine paths: ${KIT.join(' ')}`, `13. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
}
export function agentCardA(host) {
  return { name: 'getasof', description: LEAD, url: MCP, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: MCP, transport: 'JSONRPC' }], additionalInterfaces: [{ url: GI_MCP, transport: 'JSONRPC', description: 'the same router (getissuer)' }], securitySchemes: {}, security: [],
    defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], iconUrl: `https://${host}/icon-512.png`, provider: { organization: OPERATOR, url: CORPORATE }, version: SURFACES_VERSION, documentationUrl: `https://${host}/llms.txt`, protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false },
    skills: [{ id: 'get_as_of', name: 'Get the issuer record as of a date', description: LEAD, tags: ['point-in-time', 'data-vintage', 'replay', 'rco-10060', 'mcp'], examples: [JSON.stringify(CALL.params.arguments)] }],
    'x-allooloo': { page: `https://${host}/`, router_card: AGENT, receipts: RCO, doors: ['get_issuer https://getissuer.ai/', 'get_orderability https://getorderability.ai/', 'get_target_market https://gettargetmarket.ai/', 'get_as_of https://getasof.ai/', 'get_filings https://getfilings.ai/', 'get_ticker https://getticker.ai/', 'get_auditor https://getauditor.ai/', 'get_research https://getresearch.ai/'], products: ['Issuer https://getissuer.ai/', 'Orderability https://getorderability.ai/', 'Target Market https://gettargetmarket.ai/', 'As Of https://getasof.ai/', 'Issuerwire https://issuerwire.ai/'] } };
}
export const descriptorA = () => ({ name: 'getasof', kind: 'pointer (the door is the router)', url: MCP, mcp_json: 'https://mcp.getasof.ai/mcp.json', agent_card: AGENT, tools: ['get_as_of', 'resolve_issuer', 'list_events_since', 'list_nodes'], authentication: 'none', operator: OPERATOR });
export const x402A = () => ({ x402Version: 2, resource: MCP, lane: 'the per-call till: x402 v2, scheme exact, Base (eip155:8453); USDC (EIP-3009) first, Open USD (Permit2, gas-sponsored) second', when: 'reads are free; the HTTP 402 offer answers only when the agent asks (x402-pay: 1) or sends a payment', price: { get_as_of: 'price to be set (the CEO\'s); until it is, the offer quotes the till\'s one-record-read amount', pricing: 'https://mcp.getasof.ai/x402/pricing.json' }, receipt: 'a paid read\'s RCO receipt names its settlement (network and transaction)', operator: OPERATOR });
export const descA = () => `${H1} get_as_of: the signed issuer record as it stood on a date, from the sealed vintage, with its RCO receipt; one MCP door at ${MCP}.`;
export const targetA = () => ({ kind: 'apex', mcp: MCP, agent: AGENT, openapi: null, mcpjson: 'https://mcp.getasof.ai/mcp.json', name: 'getasof' });
export const pathsA = () => ['/'].concat(KIT);
export const sweep = sweepDate;
