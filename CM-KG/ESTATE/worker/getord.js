// GETORD-01 (CEO 2026-11-02) — getorderability.ai, the orderability door's page, built to the getissuer.ai page pattern (doors027.js getissuerBody): same chrome,
// nav (the AIO tab current), eyebrow, numbered sections, signal table, access block, estate table, machine kit, contact, closing card (the footer band), footer.
// Page text is the copy of record, verbatim: START_ME_UP\Allooloo_getorderability_Page-Copy-of-Record_v1.1_2026-11-02.docx (GETORD-01a: §2.2; v1.0 beside; bracketed lines there are build notes).
// Every count is read at render: list_nodes (ctx.live) and each node's signed AIO section (/book/aio.json on its own door: chapter, section version, client
// categories, product scope); the gate version is the X-Node-Gate header of a node door. Nothing typed. Zones: getorderability.ai the page; .com/.org/.io twins
// (the same body, no 301 — served as getorderability.ai); get-orderability.ai/.com/.org/.io 301 here, path kept. www answers on each.
import { OPERATOR, CORPORATE, CONTACT, APEX, SURFACES_VERSION, esc, int, today, num, table, contactSection } from './chrome.js';
export const ORD = 'https://getorderability.ai';
const MCP = 'https://mcp.getorderability.ai/mcp';
const AGENT = 'https://agent.getorderability.ai/.well-known/agent-card.json';
const GI_MCP = 'https://mcp.getissuer.ai/mcp';
const RCO = 'https://mcp.rco-records.ai/mcp';
export const TAG = 'Whether, before where.';
export const BAND = 'Allooloo is the intelligence layer under the trade, not the trade. One sourced, signed, receipted answer to whether a capital product may be ordered for a category of client, in every market it serves, from the issuer\'s own jurisdiction, callable by any agent over MCP and A2A.';
export const TITLE = 'AIO — get_orderability, whether a capital product may be ordered for a client category, for AI agents';
export const H1 = 'get_orderability — whether a capital product may be ordered for a client category, for AI agents.';

export function classifyG(h) {
  if (/^getorderability\.(ai|com|org|io)$/.test(h)) return { kind: 'getord' };
  if (/^get-orderability\.(ai|com|org|io)$/.test(h)) return { kind: 'redirect', canonical: ORD, status: 301 };
  return null;
}
// the twins and every www answer with the door's own body: the request is served as getorderability.ai (no 301)
export const serveAs = h => /^(www\.)?getorderability\.(ai|com|org|io)$/.test(h || '') ? 'getorderability.ai' : null;

// ---------- read at render: every node's signed AIO section, and the gate version (five-minute cache in the isolate, as liveNodes)
let BOOK = null, BOOK_AT = 0;
const origin = n => String(n.door || n.regional_door || '').replace(/\/mcp$/, '').replace(/\/$/, '');
export async function bookData(live) {
  if (BOOK && Date.now() - BOOK_AT < 300000) return BOOK;
  const nodes = Object.values(live || {}).filter(n => n && n.node);
  const rows = await Promise.all(nodes.map(async n => {
    const o = origin(n); const row = { node: n.node, market: n.country, region: (n.region && n.region.azure) || null, live: !!n.live, as_of: n.as_of || null, door: o ? o + '/mcp' : null, book: o ? o + '/book/aio.json' : null };
    if (!o) return { ...row, read: 'no door on the roster' };
    try {
      const r = await fetch(o + '/book/aio.json', { headers: { accept: 'application/json', 'user-agent': 'Allooloo estate (getorderability.ai)' }, cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(9000) });
      if (!r.ok) return { ...row, read: `HTTP ${r.status}` };
      const j = await r.json(); const f = name => ((j.section && j.section.fields) || []).find(x => x.name === name);
      const cats = f('client_categories'); const scope = f('product_scope');
      const count = v => Array.isArray(v) ? v.length : (v && typeof v === 'object' ? 1 : (v && v !== 'not_found' ? 1 : 0));
      return { ...row, read: 'ok', chapter: j.chapter || null, section: j.version || (j.section && j.section.version) || null, categories: cats ? count(cats.value) : 0, scope: scope ? count(scope.value) : 0 };
    } catch (e) { return { ...row, read: 'did not answer' }; }
  }));
  let gate = null;
  for (const x of rows.filter(r => r.read === 'ok' && r.door)) {
    try { const r = await fetch(x.door, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list' }), signal: AbortSignal.timeout(8000) }); gate = r.headers.get('x-node-gate'); if (gate) break; } catch (e) { /* the next door */ }
  }
  BOOK = { rows: rows.sort((a, b) => a.node.localeCompare(b.node)), gate, read_at: new Date().toISOString() }; BOOK_AT = Date.now();
  return BOOK;
}
const sweepDate = live => Object.values(live || {}).filter(n => n && n.live && n.as_of).map(n => String(n.as_of)).sort().slice(-1)[0] || today();
const onFile = b => ({ cats: b.rows.filter(r => r.categories > 0).length, scope: b.rows.filter(r => r.scope > 0).length });

// ---------- the copy of record, verbatim
const LEAD = 'get_orderability is the orderability outcome: for one listed security, one client category and one market, what that market\'s own rules say — may this product be ordered for this category of client, under the rule revision in force today. The answer is built from the Book of Markets, the sourced chapter of every market\'s product-governance, design-and-distribution or know-your-product duty; it is signed by the node of the issuer\'s own country and receipted before it is served. An agent at a manufacturer, a distributor or a dealer asks it before an order proceeds; the firm keeps the receipt and shows afterwards what rule it relied on.';
const S1 = ['Unit: one subject, one client category, one market, one rule revision → one signed outcome in the AIO-10060 §7.1 shape, keyed <market>-cm-kg/<venue>/<code>, resolved by ticker, ISIN or LEI.',
  'Scope: the product by its record version and instrument class; the client category in the market\'s own classification (Paragraph (o) · Professionelle Kunden · elective professional client · Privatkundinnen und -kunden); the market; the immutable rule revision applied.',
  'Signal: one ACM-68000 (Agent Clearance Manifest) clearance signal, or none where the evidence does not reach a conclusion.',
  'Basis: every distribution condition the regime imposes, with the party it binds and the evidence that discharges it where the regime names one, marked firm-held where it names none; the scope object the subject\'s class falls within, cited to the provision; each line naming the chapter field it rests on.',
  'Gaps: the items the regime requires and the firm holds — target-market statement, product scope statement, product documentation, required assessments — each cited to the Book, each listed as firm-held. Where a category is not one the rule names, the outcome lists the categories the chapter does name, in the regime\'s words, so the question can be asked again correctly.',
  'Review: the triggers after which the outcome must be produced again — a new rule revision, a new chapter section version, a change on the record.',
  'Nothing inferred: a value the reader marked inferred, or prose it could not structure, is visible in the Book and never used; a regulator\'s page the reader could not reach is recorded as not found with the pages checked.'];
const S2_LEAD = 'get_orderability turns the chapter, the rule revision and the record into one answer for a product and a client category in the product\'s home market — the ACM-68000 signal, with the outcome\'s signature, the node, the chapter section version and the receipt id on the same answer.';
export const SIGNALS = [['ACM-200', 'CLEARED', 'the category is one the market\'s securities rule names; the subject is on the register and not halted; a rule revision exists; the instrument class is within the rule\'s product scope. The conditions ride on the outcome; the firm holds the evidence'],
  ['ACM-403', 'EXCLUDED', 'the regime itself states an exclusion for this category and this class of instrument — a product-intervention measure, a retail ban — cited to the measure'],
  ['ACM-404', 'NOT NAMED', 'the category is not one the market\'s rule names; the outcome lists the categories it does'],
  ['ACM-451', 'READ THE FILING', 'a regulatory filing for the issuer is dated in the last three days; a person reads it before the agent acts'],
  ['no signal', 'NOT DETERMINABLE', 'the evidence does not reach a conclusion; the outcome carries evidence_gaps with the pages checked, and stops']];
const CALL = { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'get_orderability', arguments: { subject: 'XETRA:SAP', client_category: 'Professionelle Kunden' } } };
const S4 = ['Every outcome is signed by the producing node under its record key (EdDSA); verify against the node\'s /.well-known/jwks.json named in the answer. The outcome stamps the AIO-10060 text version and the gate version it was produced under.',
  'Every read is receipted at https://mcp.rco-records.ai/mcp with the node as writer; the receipt\'s answer_hash binds it to the exact signed outcome; verify_receipt is public and works offline against rco-records.ai/.well-known/jwks.json. The receipt id is on every answer (receipt_id).',
  'Every basis line names the chapter field it rests on; every chapter field carries its source URL, the date the page bears, the time it was read and the pages checked. The section version the outcome read stays published, unchanged, for as long as the receipt exists.',
  'Public rule text only: the regulator\'s own pages and statutes; nothing licensed from a third party; nothing inferred. A source that refuses automated reading is recorded as not found, not worked around.',
  'Re-read weekly by the Book\'s readers — a search reader, a reading model and a review model that rejects what the page does not say — and on targeted passes when a provision changes. No staff on the line.'];
const S5 = ['The subject names the market: an exchange prefix (TSX:, LSE:, XETRA:), a suffix (.TO, .L, .DE), an ISIN country code, or an LEI resolved through the apex index.',
  'The client category is in the market\'s own words. Every market page opens with \'Ask get_orderability with:\' and the categories its chapter names; a category the rule does not name returns ACM-404 and the list.',
  'Default scope: the market the name belongs to. A name listed on two nodes returns two outcomes, each from its own door under its own chapter; nothing is joined across borders inside a door.',
  'No node answers for another: if a door is unavailable the answer says so (no-fallback rule).',
  'Every answer is an outcome with sources, never a summary. The desk for a person: ask.allooloo.io.'];
const S6 = 'The outcome is built from the Book of Markets: one chapter per market, five sections — the record fields, the rule register, the orderability objects, the venues by Market Identifier Code, the disclosure classes — every value in one field shape with its source, date and pages checked. The chapter is served signed from the issuer\'s node at /book/manifest.json and rendered at sm-eco-10060.org/market/<market>/. The Book is the market-and-duty link of the stack; get_orderability is the door onto the question it answers.';
const S7 = ['Not advice, not an individual suitability assessment, not permission, not a venue and not an order. It says what the sourced rules of a market say about a product and a category of client.',
  'Not the firm\'s evidence. Where a regime requires a target-market statement, an assessment or product documentation and does not publish the document that satisfies it, the outcome records the requirement and marks the evidence firm-held. The condition rides on the outcome; the firm holds the proof.',
  'Not a count. No page of this door states how many markets, outcomes or categories it holds; the figures above are read at render.'];
const S8 = [['agent-kyp.ai', 'Know Your Product (KYP), Canada · categories under National Instrument 31-103'],
  ['agent-prod.ai', 'the Product Intervention and Product Governance Sourcebook (PROD) and the Consumer Duty, UK · categories under COBS 3'],
  ['agent-mifid.ai', 'the product governance rules of the second Markets in Financial Instruments Directive (MiFID II), Germany · France · Netherlands · categories under Annex II as transposed'],
  ['agent-finsa.ai', 'the Financial Services Act (FinSA), Switzerland · categories under Art. 4'],
  ['agent-ddo.ai', 'the Design and Distribution Obligations (DDO), Australia'],
  ['agent-regbi.ai', 'Regulation Best Interest (Reg BI), United States']];
const S8_LAST = 'Each door points an agent at the outcome under that duty, from the node of that market, in that regime\'s own category words; the duty decision stays with the firm.';
const S9 = 'Every outcome\'s receipt is a permanent address on rco-records.ai that resolves to exactly what the door served — the outcome, the node, the chapter section version, the serving time, the signing key and the source page of each basis line. A second call never changes the first receipt. The receipt of a cleared read is the RCO receipt id on every door answer (receipt_id), readable at https://mcp.rco-records.ai/mcp and at cite-fact.ai.';
const S10 = ['The router holds an index only and forwards each call to the node of the listing; the outcome is produced, signed and receipted in its own country; no fallback across borders.', 'Every count on this page is read at render; nothing is typed.'];
const KIT = ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/mcp.json', '/openapi.json'];
const TWINS = ['getorderability.com', 'getorderability.org', 'getorderability.io'];
const FORWARDS = ['get-orderability.ai', 'get-orderability.com', 'get-orderability.org', 'get-orderability.io'];

// links inside verbatim copy: the text is the copy's; only addresses it names become links
const linkify = s => esc(s)
  .replace(/https:\/\/mcp\.rco-records\.ai\/mcp/g, '<code>https://mcp.rco-records.ai/mcp</code>')
  .replace(/rco-records\.ai\/\.well-known\/jwks\.json/g, '<a href="https://rco-records.ai/.well-known/jwks.json">rco-records.ai/.well-known/jwks.json</a>')
  .replace(/(^|[\s(])ask\.allooloo\.io/g, '$1<a href="https://ask.allooloo.io/">ask.allooloo.io</a>')
  .replace(/sm-eco-10060\.org\/market\/&lt;market&gt;\//g, '<code>sm-eco-10060.org/market/&lt;market&gt;/</code>')
  .replace(/(at |and at )cite-fact\.ai/g, '$1<a href="https://cite-fact.ai/">cite-fact.ai</a>')
  .replace(/ACM-68000 \(Agent Clearance Manifest\)/g, '<a href="https://acm-68000.org/">ACM-68000</a> (Agent Clearance Manifest)');
const h2 = (id, n, t) => `<h2 id="${id}">${n ? n + ' ' : ''}${esc(t)}</h2>`;

export function liveLineText(b, live) {
  const f = onFile(b);
  return `${int(f.cats)} markets with client categories on file · ${int(f.scope)} with product scope on file`;   // CEO ruling (GETORD-01): no receipt figure — the receipt door publishes no counts
}
export function getordBody(ctx, host) {
  const b = ctx.book || { rows: [], gate: null }; const date = sweepDate(ctx.live);
  const install = JSON.stringify({ mcpServers: { getorderability: { type: 'http', url: MCP } } }, null, 2);
  const estate = b.rows.map(r => [`<code class="nw">${esc(r.node)}</code>`, esc(r.market || ''), esc(r.region || ''), esc(r.live ? 'live' : 'not live'),
    r.read === 'ok' ? `<span class="n">${esc(int(r.categories))}</span>` : `<span class="muted">${esc(r.read)}</span>`, r.read === 'ok' ? (r.scope ? `<span class="n">${esc(int(r.scope))}</span>` : '<span class="muted">not found</span>') : '',
    r.read === 'ok' ? `<a href="${esc(r.book)}"><code>${esc([r.chapter, r.section].filter(Boolean).join(' · '))}</code></a>` : '', `<a href="https://sm-eco-10060.org/market/${esc(r.node.slice(0, 2))}/">sm-eco-10060.org/market/${esc(r.node.slice(0, 2))}/</a>`]);
  return `<p class="kicker">AIO · AI Orderability</p>
<p class="lead"><strong>${esc(liveLineText(b, ctx.live))}</strong> <span class="muted">— live from the Book manifest at render, sweep market date ${esc(date)}</span></p>
<p class="lead">${esc(LEAD)}</p>
${h2('outcome', 1, 'The outcome')}${num(1, S1.map(linkify))}
${h2('signal', 2, 'The signal')}<p>${linkify(S2_LEAD)}</p>${table(['signal', 'state', 'when'], SIGNALS.map(([s, st, w]) => [s.startsWith('ACM-') ? `<code><a href="https://acm-${s.slice(4)}.ai/">${esc(s)}</a></code>` : esc(s), esc(st), esc(w)]))}${num(2, [`One call: <pre>${esc(JSON.stringify(CALL))}</pre> at <code>${esc(MCP)}</code> .`, '<code>ACM-000</code>, <code>ACM-300</code> and <code>ACM-500</code> are reserved by <a href="https://acm-68000.org/">ACM-68000</a> and never served. An identifier that is not a listed security, a bare ticker that names more than one issuer, and a home node that did not answer are reported as errors with their reason, not as signals; nothing is served from another country.', 'The vocabulary is the open standard at <a href="https://acm-68000.org/">acm-68000.org</a>; the outcome\'s shape is <a href="https://aio-10060.org/">aio-10060.org</a>; the chapter is the market\'s Book of Markets page at <code>sm-eco-10060.org/market/&lt;market&gt;/</code>.'])}
${h2('access', 3, 'Access')}<p>Any MCP client that speaks Streamable HTTP:</p><pre>${esc(install)}</pre><p>Claude Code:</p><pre>claude mcp add --transport http getorderability ${esc(MCP)}</pre>${num(3, [`Door: <code>${esc(MCP)}</code> — the same router as <code>${esc(GI_MCP)}</code> : same index, no second store; read-only, no authentication, no account. get_orderability is routed to the node of the subject's listing; the node signs; the router forwards.`, `Agent Card (A2A): <a href="${AGENT}"><code>${esc(AGENT)}</code></a> .`, 'Tools: <code>get_orderability</code>, with <code>resolve_issuer</code> · <code>get_record</code> · <code>get_signal</code> · <code>list_aliases</code> · <code>list_events_since</code> · <code>list_nodes</code> on the same door.', 'Regional doors: <code>mcp.&lt;market&gt;-cm-kg.ai/mcp</code> and <code>&lt;market&gt;.eu-cm-kg.ai/mcp</code> for the European nodes — each answers its own market only; the roster entry of each (list_nodes, fields <code>regional_door</code> and <code>agent_card</code>) is the address of record.', 'Registry entry: <code>registry.modelcontextprotocol.io · io.github.allooloo/getorderability</code>. Documentation: <a href="/docs">getorderability.ai/docs</a>; enterprise connector setup: <a href="https://allooloo.io/setup">allooloo.io/setup</a>.', 'Paying for a read: every read is free unless the agent asks for the offer (header <code>x402-pay: 1</code>); the door then answers HTTP 402 with a signed offer and the same call carries the payment and the receipt — <a href="https://agentic-x402.ai/">agentic-x402.ai</a>.'])}
${h2('provenance', 4, 'Provenance')}${num(4, S4.map(linkify))}
${h2('ask', 5, 'Ask about any product')}${num(5, S5.map(linkify))}
${h2('book', 6, 'The Book of Markets')}<p>${linkify(S6)}</p>
${h2('not', 7, 'What it is not')}${num(7, S7.map(linkify))}
${h2('duty-doors', 8, 'The duty doors')}${num(8, S8.map(([z, t]) => `<a href="https://${z}/">${esc(z)}</a> — ${esc(t)}`).concat([esc(S8_LAST)]))}
${h2('receipts', 9, 'Receipts')}<p>${linkify(S9)}</p>
${h2('estate', 10, 'The estate')}<div class="wrap">${table(['node', 'market', 'region', 'state', 'categories on file', 'scope on file', 'chapter section version', 'surface'], estate)}</div><p class="src">source: list_nodes at <code>${esc(GI_MCP)}</code> and /book/manifest.json, read at render</p>${num(10, S10.map(esc))}
${h2('kit', 11, 'Machine kit')}${num(11, [KIT.map(x => `<a href="${x}"><code>${x}</code></a>`).join(' · '), `Twins (same body, no 301): ${TWINS.join(', ')}. Forwards here (301, path kept): ${FORWARDS.join(', ')}.`])}${contactSection(host)}`;
}
// the documentation page (copy section 3 names getorderability.ai/docs): the access, the call, the signal and the provenance of the copy, nothing new
export function docsBodyG() {
  const install = JSON.stringify({ mcpServers: { getorderability: { type: 'http', url: MCP } } }, null, 2);
  return `<p class="lead">${esc(LEAD)}</p>${h2('connect', 1, 'Access')}<pre>${esc(install)}</pre><pre>claude mcp add --transport http getorderability ${esc(MCP)}</pre>${num(1, [`Door: <code>${esc(MCP)}</code> — the same router as <code>${esc(GI_MCP)}</code> : same index, no second store; read-only, no authentication, no account.`, `Agent Card (A2A): <a href="${AGENT}"><code>${esc(AGENT)}</code></a> .`])}
${h2('call', 2, 'One call')}<pre>${esc(JSON.stringify(CALL))}</pre>${table(['signal', 'state', 'when'], SIGNALS.map(([s, st, w]) => [esc(s), esc(st), esc(w)]))}
${h2('outcome', 3, 'The outcome')}${num(3, S1.map(linkify))}
${h2('provenance', 4, 'Provenance')}${num(4, S4.map(linkify))}<p><a href="/">getorderability.ai</a></p>`;
}
export function factsG(host, live, b) {
  const f = onFile(b || { rows: [] });
  return { domain: host, kind: 'product door', product: 'AIO — AI Orderability (get_orderability)', head: H1.replace(/\.$/, ''), operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: sweepDate(live), surface_version: SURFACES_VERSION, source: 'public-record',
    markets_with_client_categories: f.cats, markets_with_product_scope: f.scope, counts_from: 'list_nodes and each node\'s signed /book/aio.json (live on each render)', book_read_at: (b && b.read_at) || null, gate: (b && b.gate) || null,
    mcp_url: MCP, same_router_as: GI_MCP, agent_card: AGENT, tools: ['get_orderability', 'resolve_issuer', 'get_record', 'get_signal', 'list_aliases', 'list_events_since', 'list_nodes'], standard: 'https://aio-10060.org/', signal_vocabulary: 'https://acm-68000.org/', receipts: RCO,
    signals: SIGNALS.map(([s, st]) => `${s} ${st}`), reserved: { codes: ['ACM-000', 'ACM-300', 'ACM-500'], text: 'ACM-000, ACM-300 and ACM-500 are reserved by ACM-68000 and never served. An identifier that is not a listed security, a bare ticker that names more than one issuer, and a home node that did not answer are reported as errors with their reason, not as signals; nothing is served from another country.' }, twins: TWINS, forwards_here: FORWARDS, registry: 'io.github.allooloo/getorderability', machine_paths: KIT,
    estate: ((b && b.rows) || []).map(r => ({ node: r.node, market: r.market, region: r.region, state: r.live ? 'live' : 'not live', categories_on_file: r.read === 'ok' ? r.categories : null, scope_on_file: r.read === 'ok' ? r.scope : null, chapter: r.chapter || null, section: r.section || null, book: r.book, surface: `https://sm-eco-10060.org/market/${r.node.slice(0, 2)}/`, read: r.read })) };
}
export function llmsG(host, live, b) {
  const f = onFile(b || { rows: [] });
  return [`# ${host} — AIO · AI Orderability: ${H1.replace(/\.$/, '')}`, `1. ${LEAD}`, `2. At render: ${f.cats} markets with client categories on file · ${f.scope} with product scope on file (each node's signed /book/aio.json); sweep market date ${sweepDate(live)}; gate ${(b && b.gate) || 'not read'}.`,
    `3. Door: ${MCP} (MCP Streamable HTTP, no auth) — the same router as ${GI_MCP}: same index, no second store. Agent Card: ${AGENT}.`, '4. Tools: get_orderability, with resolve_issuer · get_record · get_signal · list_aliases · list_events_since · list_nodes on the same door.',
    `5. One call: ${JSON.stringify(CALL)}`, '6. The signal: ' + SIGNALS.map(([s, st]) => `${s} ${st}`).join(' · ') + '. ACM-000, ACM-300 and ACM-500 are reserved by ACM-68000 and never served. An identifier that is not a listed security, a bare ticker that names more than one issuer, and a home node that did not answer are reported as errors with their reason, not as signals; nothing is served from another country.',
    `7. Provenance: the producing node signs (EdDSA, its /.well-known/jwks.json); every read is receipted at ${RCO} with the node as writer; verify_receipt is public. Standard https://aio-10060.org/ · vocabulary https://acm-68000.org/ · chapter https://sm-eco-10060.org/market/ followed by the market code.`,
    `8. Twins (same body, no 301): ${TWINS.join(', ')}. Forwards here (301, path kept): ${FORWARDS.join(', ')}.`, `9. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}. Not advice, not permission, not a venue and not an order.`,
    `10. Machine paths: ${KIT.join(' ')} · /docs`, `11. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
}
export const descG = () => `${H1} AIO · AI Orderability: the outcome, the signal, access, provenance, the Book of Markets, the duty doors, receipts and the estate, read at render; one MCP door at ${MCP}.`;
export const targetG = () => ({ kind: 'apex', mcp: MCP, agent: AGENT, openapi: 'https://mcp.getorderability.ai/openapi.json', mcpjson: 'https://mcp.getorderability.ai/mcp.json', name: 'getorderability' });
export const pathsG = () => ['/', '/docs'].concat(KIT);
export const sweep = sweepDate;
