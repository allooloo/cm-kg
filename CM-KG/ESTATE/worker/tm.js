// TMKT-01 (2026-11-01) — gettargetmarket.ai, the Target Market door's page, built to the getorderability.ai page pattern (getord.js): same chrome, nav (the TM tab
// current), eyebrow, numbered sections, call table, access block, estate table, machine kit, contact, footer.
// Page text is the copy of record, verbatim: START_ME_UP\Allooloo_gettargetmarket_Page-Copy-of-Record_v1.0_2026-11-01.docx, generated into tm-copy.js
// (CM-KG\DOOR\gettargetmarket\gen_copy.py; bracketed build notes stripped). Design of record: the gettargetmarket build plan v1.0.
// TMKT-02 (2026-11-01): the door serves (mcp.gettargetmarket.ai on the apex router, the four tools on every node door); the markers below are off §2–4 and the
// examples; §6 carries "serving from TMKT-03" (get_orderability reads the statement from TMKT-03). /file and /docs/emt are written. Was, until TMKT-02:
// Until TMKT-02 the door does not serve: sections 2–4 carry the line "serving from TMKT-02" and the call examples are marked not yet resolving; mcp.gettargetmarket.ai
// is not routed. Read at render: list_nodes (ctx.live) and each node's signed AIO section (/book/aio.json): the field manufacturer_evidence_accepted
// (SM-ECO-10060 Appendix C 0.2). tm/ has no reader until the door serves, so the statement figures are not shown as numbers; the receipt door publishes
// no counts (CEO ruling, GETORD-01), so the copy's receipt figure is not rendered. Nothing typed.
// Zones: gettargetmarket.ai the page and agent.gettargetmarket.ai the card; .org/.io twins (the same body, no 301 — served as gettargetmarket.ai);
// get-targetmarket.com 301 here, path kept. www answers on each.
import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, esc, int, today, num, table, contactSection } from './chrome.js';
import C from './tm-copy.js';
export const TM = 'https://gettargetmarket.ai';
const MCP = 'https://mcp.gettargetmarket.ai/mcp';
const AGENT = 'https://agent.gettargetmarket.ai/.well-known/agent-card.json';
const GI_MCP = 'https://mcp.getissuer.ai/mcp';
const RCO = 'https://mcp.rco-records.ai/mcp';
const STATE = 'serving';   // TMKT-02 (was 'serving from TMKT-02')
const GATE_STATE = 'serving';   // §6: get_orderability reads the statement (TMKT-03, 2026-11-02)
const NOT_YET = 'not yet resolving — the door serves from TMKT-02';
export const TITLE = 'TM — get_target_market, the manufacturer\'s target market statement for AI agents';
export const H1 = C.h1;
const TOOLS = [['file_target_market', 'File a target market statement', 'The manufacturer\'s agent files a statement for an ISIN under its filer identity; returns the version, the node signature and the filing receipt id.'],
  ['get_target_market', 'Read a target market statement', 'The statement for an ISIN at its current version (or a version or as-of time), both signatures, the chapter sections it speaks to, the read receipt id.'],
  ['list_target_market_versions', 'List the statement versions', 'Every version for an ISIN with filed_at and supersedes; nothing is deleted.'],
  ['verify_target_market', 'Verify a statement', 'Whether the manufacturer\'s and the node\'s signatures verify against the published keys; works offline.']];
const ALSO = ['get_orderability', 'resolve_issuer', 'get_record', 'list_nodes'];
export const ITEMS = [['negative_target_market', 'negative target market'], ['product_scope_statement', 'product scope statement'], ['product_documentation', 'product documentation'], ['required_assessments', 'required assessments']];
const TWINS = ['gettargetmarket.org', 'gettargetmarket.io'];
const FORWARDS = ['get-targetmarket.com'];
const KIT = ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/mcp.json'];

export function classifyT(h) {
  if (/^gettargetmarket\.(ai|org|io)$/.test(h) || h === 'agent.gettargetmarket.ai') return { kind: 'tm' };
  if (h === 'get-targetmarket.com') return { kind: 'redirect', canonical: TM, status: 301 };
  return null;
}
// the twins, every www and the agent host answer with the door page's own body: the request is served as gettargetmarket.ai (no 301)
export const serveAs = h => /^(www\.)?gettargetmarket\.(ai|org|io)$/.test(h || '') || h === 'agent.gettargetmarket.ai' ? 'gettargetmarket.ai' : null;


// TMKT-03: the page's sample outcome — the test subject asked at the Germany node (the first client category its chapter names), one hour in the isolate
let SAMPLE = null, SAMPLE_AT = 0;
async function sampleOutcome(rows) {
  if (SAMPLE && Date.now() - SAMPLE_AT < 3600000) return SAMPLE;
  try {
    const de = (rows || []).find(r => r.node === 'de-cm-kg'); let cat = null;
    const b = await fetch('https://mcp.de-cm-kg.ai/book/aio.json', { headers: { accept: 'application/json', 'user-agent': 'Allooloo estate (gettargetmarket.ai sample)' }, cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(9000) }).then(r => r.json());
    const cf = ((b.section || b).fields || []).find(f => f.name === 'client_categories'); const it = cf && Array.isArray(cf.value) ? cf.value[0] : null; cat = it && typeof it === 'object' ? (it.identifier || it.category || it.name) : it;
    const r = await fetch('https://mcp.de-cm-kg.ai/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'Allooloo estate (gettargetmarket.ai sample)' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'get_orderability', arguments: { subject: 'TEST:DE000TMKT025', client_category: cat } } }), signal: AbortSignal.timeout(20000) });
    const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{'))); const o = j.result && (j.result.structuredContent || JSON.parse(j.result.content[0].text));
    if (o && o.discharge) { SAMPLE = { category: cat, statement: o.discharge.statement, items: o.discharge.items, signal: o.signal || null, receipt: o.receipt && o.receipt.id, outcome_id: o.outcome_id }; SAMPLE_AT = Date.now(); }
  } catch (e) { /* the last one read */ }
  return SAMPLE;
}
const sampleBlock = s => !s ? '<p class="muted">Sample outcome: not read at this render.</p>' : `<p class="muted">Sample outcome — the test subject TEST:DE000TMKT025, asked at the Germany node for the client category &ldquo;${esc(s.category)}&rdquo;, read at render, receipted at the receipt door (statement v${esc(s.statement && s.statement.version)}, filing receipt <code>${esc(s.statement && s.statement.receipt_id)}</code>):</p>${table(['required item', 'status on the outcome', 'the Book (Germany)'], (s.items || []).map(i => [esc(i.item.replace(/_/g, ' ')), esc(i.status), esc(i.book_status)]))}`;
// ---------- read at render: every node's signed AIO section, the field manufacturer_evidence_accepted (five-minute cache in the isolate, as getord)
let BOOK = null, BOOK_AT = 0;
const origin = n => String(n.door || n.regional_door || '').replace(/\/mcp$/, '').replace(/\/$/, '');
export async function bookData(live) {
  if (BOOK && Date.now() - BOOK_AT < 300000) return BOOK;
  const nodes = Object.values(live || {}).filter(n => n && n.node);
  const rows = await Promise.all(nodes.map(async n => {
    const o = origin(n); const row = { node: n.node, market: n.country, region: (n.region && n.region.azure) || null, live: !!n.live, book: o ? o + '/book/aio.json' : null };
    if (!o) return { ...row, read: 'no door on the roster' };
    try {
      const r = await fetch(o + '/book/aio.json', { headers: { accept: 'application/json', 'user-agent': 'Allooloo estate (gettargetmarket.ai)' }, cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(9000) });
      if (!r.ok) return { ...row, read: `HTTP ${r.status}` };
      const j = await r.json(); const s = j.section || j; const f = (s.fields || []).find(x => x.name === 'manufacturer_evidence_accepted');
      const section = j.version || s.version || null;
      if (!f) return { ...row, read: 'ok', section, mea: 'not read' };   // a chapter still on Appendix C 0.1: the field has not been read for this market
      const items = Array.isArray(f.value) ? Object.fromEntries(f.value.map(x => [x.item, x])) : {};
      return { ...row, read: 'ok', section, mea: Array.isArray(f.value) ? 'read' : 'not_found', items, pages: (f.pages_checked || []).length, source_url: f.source_url || null };
    } catch (e) { return { ...row, read: 'did not answer' }; }
  }));
  let aio = null;   // the AIO-10060 text version in force, from the standard's own descriptor (the eyebrow's "AIO <text version>")
  try { const r = await fetch('https://aio-10060.org/aio-10060.json', { headers: { accept: 'application/json', 'user-agent': 'Allooloo estate (gettargetmarket.ai)' }, cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(8000) }); if (r.ok) aio = (String((await r.json()).version || '').match(/Version (\d+\.\d+)/) || [])[1] || null; } catch (e) { /* not read */ }
  BOOK = { rows: rows.sort((a, b) => a.node.localeCompare(b.node)), aio, read_at: new Date().toISOString() }; BOOK.sample = await sampleOutcome(BOOK.rows); BOOK_AT = Date.now();   // TMKT-03: the sample outcome
  return BOOK;
}
const sweepDate = live => Object.values(live || {}).filter(n => n && n.live && n.as_of).map(n => String(n.as_of)).sort().slice(-1)[0] || today();
const accepting = b => b.rows.filter(r => r.mea === 'read' && Object.values(r.items || {}).some(x => x.status === 'accepted')).length;
const readFor = b => b.rows.filter(r => r.mea === 'read' || r.mea === 'not_found').length;

// ---------- the copy of record (tm-copy.js), with only the addresses it names made links
const linkify = s => esc(s)
  .replace(/https:\/\/mcp\.rco-records\.ai\/mcp/g, '<code>https://mcp.rco-records.ai/mcp</code>')
  .replace(/rco-records\.ai\/\.well-known\/jwks\.json/g, '<a href="https://rco-records.ai/.well-known/jwks.json">rco-records.ai/.well-known/jwks.json</a>')
  .replace(/(at |and at )cite-fact\.ai/g, '$1<a href="https://cite-fact.ai/">cite-fact.ai</a>')
  .replace(/(^|[\s(])aio-10060\.org/g, '$1<a href="https://aio-10060.org/">aio-10060.org</a>').replace(/(^|[\s;])acm-68000\.org/g, '$1<a href="https://acm-68000.org/">acm-68000.org</a>')
  .replace(/sm-eco-10060\.org\/market\/&lt;market&gt;\//g, '<code>sm-eco-10060.org/market/&lt;market&gt;/</code>')
  .replace(/gettargetmarket\.ai\/docs/g, '<a href="/docs">gettargetmarket.ai/docs</a>').replace(/gettargetmarket\.ai\/file/g, '<a href="/file">gettargetmarket.ai/file</a>')
  .replace(/— agentic-x402\.ai/g, '— <a href="https://agentic-x402.ai/">agentic-x402.ai</a>')
  .replace(/(https:\/\/agent\.gettargetmarket\.ai\/\.well-known\/agent-card\.json)/g, '<a href="$1"><code>$1</code></a>')
  .replace(/(https:\/\/mcp\.(gettargetmarket|getissuer)\.ai\/mcp)/g, '<code>$1</code>');
const h2 = (id, t) => `<h2 id="${id}">${esc(t)}</h2>`;
const state = () => `<p class="state"><strong>${esc(STATE)}</strong></p>`;
// a copy line that holds a call example: "<lead>: [JSON block] {…} <tail>" — the example is rendered as code, marked not yet resolving
function example(line) {
  const m = line.match(/^(.*?)\[JSON block\]\s*(\{.*\})\s*(.*)$/s); if (!m) return linkify(line);
  return `${linkify(m[1].trim())} <pre>${esc(m[2])}</pre> ${linkify(m[3].trim())}`;   // TMKT-02: the examples resolve
}
export function liveLineText(b) {
  return `${int(accepting(b))} markets whose rules accept manufacturer evidence`;   // read from the Book; statements and manufacturers come from tm/ once the door serves; no receipt figure (CEO ruling)
}
const MEA_WORD = { accepted: 'accepted', partial: 'partial', not_accepted: 'not accepted', silent: 'silent' };   // BOOK-09 (2026-11-02): the four statuses of an anchored reading; a TMKT-01 not_found item reads "not found"
const meaCell = r => {
  if (r.read !== 'ok') return `<span class="muted">${esc(r.read)}</span>`;
  if (r.mea === 'not read') return '<span class="muted">not read yet (chapter on Appendix C 0.1)</span>';
  if (r.mea === 'not_found') return `<span class="muted">not found</span> <span class="muted">· ${esc(int(r.pages))} pages checked</span>`;
  return ITEMS.map(([k, t]) => { const x = (r.items || {})[k] || {}; const u = x.source_url || ((x.quotes || [])[0] || {}).source_url; const w = MEA_WORD[x.status];   // BOOK-09: the anchored statuses, each linked to its first quoted source
    return `${esc(t)}: ${w && u ? `<a href="${esc(u)}">${esc(w)}</a>` : `<span class="muted">${esc(w || 'not found')}</span>`}`; }).join('<br>');
};
export function tmBody(ctx, host) {
  const b = ctx.book || { rows: [] }; const date = sweepDate(ctx.live);
  const estate = b.rows.map(r => [`<code class="nw">${esc(r.node)}</code>`, esc(r.market || ''), esc(r.region || ''), meaCell(r), `<a href="${esc(String(r.book || '').replace(/\/book\/aio\.json$/, '/mcp'))}">${esc(STATE)}</a>`,
    `<a href="https://sm-eco-10060.org/market/${esc(r.node.slice(0, 2))}/">sm-eco-10060.org/market/${esc(r.node.slice(0, 2))}/</a>`]);
  const s2 = C.s2_table;
  return `<p class="kicker">${esc(C.kicker)}</p>
<p class="lead"><strong>${esc(liveLineText(b))}</strong> <span class="muted">— live from the Book manifest at render, sweep market date ${esc(date)} · statements are stored at each node under tm/; no count of them is published on any page</span></p>
<p class="lead">${esc(C.lead)}</p>
${h2('statement', C.heads.s1)}${num(1, C.s1.map(linkify))}
${h2('calls', C.heads.s2)}${table(s2.head, s2.rows.map(r => [`<code>${esc(r[0])}</code>`, esc(r[1]), esc(r[2])]))}${num(2, C.s2.map(example))}
${h2('access', C.heads.s3)}<p>${esc(C.s3_intro)}</p><pre>${esc(C.s3_install)}</pre><p>${esc(C.s3_cc_label)}</p><pre>${esc(C.s3_cc_cmd)}</pre>${num(3, C.s3.map(linkify))}
${h2('filing', C.heads.s4)}${num(4, C.s4.map(linkify))}
${h2('provenance', C.heads.s5)}${num(5, C.s5.map(linkify))}
${h2('orderability', C.heads.s6)}<p class="state"><strong>${esc(GATE_STATE)}</strong></p>${C.s6.map(x => `<p>${linkify(x)}</p>`).join('')}${sampleBlock(b.sample)}
${h2('not', C.heads.s7)}${num(7, C.s7.map(linkify))}
${h2('receipts', C.heads.s8)}${C.s8.map(x => `<p>${linkify(x)}</p>`).join('')}
${h2('estate', C.heads.s9)}<div class="wrap">${table(['node', 'market', 'region', 'manufacturer evidence accepted (per required item)', 'the door', 'surface'], estate)}</div><p class="src">${linkify(C.s9_source)}</p>
${h2('kit', 'Machine kit')}<p>${KIT.map(x => `<a href="${x}"><code>${x}</code></a>`).join(' · ')}</p><p class="muted">Twins (same body, no 301): ${esc(TWINS.join(', '))}. Forwards here (301, path kept): ${esc(FORWARDS.join(', '))}.</p>${contactSection(host)}`;
}
// /docs (the copy names gettargetmarket.ai/docs): the copy's statement, calls, access and provenance, and the statement's field list from AIO-10060 v1.2 (draft)
const FIELDS = [['subject', 'the ISIN; resolved through the apex index to the record and its home node'], ['manufacturer', 'the manufacturer\'s Legal Entity Identifier (LEI) and name as on the LEI record'],
  ['version · filed_at · supersedes', 'integer version, filing time (UTC), the version it replaces'], ['markets', 'the markets the statement speaks for, each by its chapter; a statement may name one or many'],
  ['positive_target_market', 'per market, in the regime\'s own category words: the client categories; knowledge and experience; ability to bear loss; risk tolerance; objectives and needs — the European MiFID Template (EMT) field groups, carried as the manufacturer states them'],
  ['negative_target_market', 'per market, the categories and profiles the product is not for, in the regime\'s words'], ['distribution_strategy', 'execution-only · with appropriateness · advised · portfolio management — as the regime names them'],
  ['product_scope_statement', 'the manufacturer\'s statement of what the product is, by instrument class, mapped to the scope bridge term'],
  ['documentation', 'the product documents the regime requires (key information document, prospectus, factsheet) — URL, document date, hash at filing'],
  ['assessments', 'the assessments the manufacturer states it performed (product approval, scenario analysis, charging structure review) — named, dated, not attached'],
  ['source', 'where the statement came from: an EMT file (its version and hash) or a direct filing'], ['sig · kid', 'the manufacturer\'s signature over the canonical statement and the key id it was made with'],
  ['node_sig', 'the home node\'s signature over the stored statement, under its record key, as for any record']];
export function docsBodyT() {
  return `<p class="lead">${esc(C.lead)}</p>${state()}
${h2('fields', 'The statement — fields')}<p class="muted">AIO-10060 v1.2 §6 (<a href="https://aio-10060.org/">aio-10060.org</a>).</p>${table(['field', 'meaning'], FIELDS.map(([f, m]) => [`<code>${esc(f)}</code>`, esc(m)]))}
${h2('statement', C.heads.s1)}${num(1, C.s1.map(linkify))}
${h2('calls', C.heads.s2)}${table(C.s2_table.head, C.s2_table.rows.map(r => [`<code>${esc(r[0])}</code>`, esc(r[1]), esc(r[2])]))}${num(2, C.s2.map(example))}
${h2('provenance', C.heads.s5)}${num(5, C.s5.map(linkify))}<p><a href="/">gettargetmarket.ai</a></p>`;
}
// /file and /docs/emt (named by the copy): built at TMKT-02 — the claim form and the EMT mapping; until then the state line and the way back
export const pendingBody = what => `<p class="lead"><strong>${esc(STATE)}</strong> — ${esc(what)}</p><p><a href="/">gettargetmarket.ai</a> · <a href="/docs">documentation</a></p>`;
export function factsT(host, live, b) {
  b = b || { rows: [] };
  return { domain: host, kind: 'product door', product: 'TM — the Target Market door (get_target_market)', head: H1.replace(/\.$/, ''), operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: sweepDate(live), surface_version: SURFACES_VERSION, source: 'public-record',
    state: STATE, door_serving: true, gate_reads_statement: GATE_STATE, markets_whose_rules_accept_manufacturer_evidence: accepting(b), markets_read_for_the_field: readFor(b), counts_from: 'list_nodes and each node\'s signed /book/aio.json, field manufacturer_evidence_accepted (live on each render)',
    statements_on_file: null, statements_note: 'no count of statements is published on any page (build plan §9.1: tm/ counts are kept in the Book of Operations appendix only)', keyring: 'https://mcp.gettargetmarket.ai/.well-known/jwks.json', book_read_at: b.read_at || null,
    mcp_url: MCP, same_router_as: GI_MCP, agent_card: AGENT, tools: TOOLS.map(t => t[0]).concat(ALSO), standard: 'https://aio-10060.org/', signal_vocabulary: 'https://acm-68000.org/', receipts: RCO,
    twins: TWINS, forwards_here: FORWARDS, registry: 'io.github.allooloo/gettargetmarket (TMKT-04)', machine_paths: KIT.concat(['/docs', '/docs/emt', '/file']),
    estate: b.rows.map(r => ({ node: r.node, market: r.market, region: r.region, manufacturer_evidence_accepted: r.read !== 'ok' ? r.read : r.mea === 'read' ? Object.fromEntries(ITEMS.map(([k]) => [k, ((r.items || {})[k] || {}).status || 'not_found'])) : r.mea, section: r.section || null, book: r.book, door: String(r.book || '').replace(/\/book\/aio\.json$/, '/mcp') || null, surface: `https://sm-eco-10060.org/market/${r.node.slice(0, 2)}/` })) };
}
export function llmsT(host, live, b) {
  b = b || { rows: [] };
  return [`# ${host} — TM · the Target Market door: ${H1.replace(/\.$/, '')}`, `1. ${C.lead}`, `2. State: ${STATE} — every call at mcp.gettargetmarket.ai is routed to the subject's home node, which stores, signs and receipts the statement; get_orderability reads the statement from TMKT-03.`,
    `3. At render: ${accepting(b)} markets whose rules accept manufacturer evidence (each node's signed /book/aio.json, field manufacturer_evidence_accepted); sweep market date ${sweepDate(live)}.`,
    `4. Door: ${MCP} (MCP Streamable HTTP; reads need no authentication; a filing needs a filer identity) — the same router as ${GI_MCP}. Agent Card: ${AGENT}.`,
    `5. Tools: ${TOOLS.map(t => t[0]).join(' · ')}, with ${ALSO.join(' · ')} on the same door.`,
    `6. Provenance: two signatures (the manufacturer's, the home node's, EdDSA), both verifiable offline; every filing and read receipted at ${RCO} with the door as writer.`,
    `7. Standard https://aio-10060.org/ (v1.2, the statement object, in draft) · vocabulary https://acm-68000.org/ · chapter https://sm-eco-10060.org/market/ followed by the market code.`,
    `8. Twins (same body, no 301): ${TWINS.join(', ')}. Forwards here (301, path kept): ${FORWARDS.join(', ')}.`, `9. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}. Not a judgment on the product, the manufacturer or the statement.`,
    `10. Machine paths: ${KIT.join(' ')} · /docs · /docs/emt · /file`, `11. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
}
// the door's own Agent Card and MCP descriptor (the router does not serve this door until TMKT-02; this host serves them meanwhile)
export function agentCardT(host) {
  return { name: 'gettargetmarket', description: C.lead, url: MCP, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: MCP, transport: 'JSONRPC' }], version: '0.0.0', protocolVersion: '0.3.0',
    provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `${TM}/docs`, iconUrl: `${TM}/icon-512.png`, capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false, extensions: [] },
    defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], securitySchemes: {}, security: [],
    skills: TOOLS.map(([n, t, d]) => ({ id: n, name: t, description: d, tags: ['target-market', 'product-governance', 'mcp'], inputModes: ['application/json'], outputModes: ['application/json'], examples: [] })),
    agentCardOfRecord: AGENT, 'x-allooloo': { state: STATE, door_serving: true, keyring: 'https://mcp.gettargetmarket.ai/.well-known/jwks.json', same_router_as: GI_MCP, also_on_the_door: ALSO, standard: 'https://aio-10060.org/', surface_version: SURFACES_VERSION } };
}
export function descriptorT() {
  return { name: 'gettargetmarket', state: STATE, door_serving: true, transport: 'streamable-http', url: MCP, authentication: { reads: 'none', file_target_market: 'filer identity bound to the manufacturer\'s LEI' },
    tools: TOOLS.map(([n, t, d]) => ({ name: n, title: t, description: d })).concat(ALSO.map(n => ({ name: n, note: 'on the same router' }))), agentCard: AGENT, same_router_as: GI_MCP, documentation: `${TM}/docs`, registry: 'io.github.allooloo/gettargetmarket (TMKT-04)' };
}
// TMKT-02: /docs/emt — the European MiFID Template (EMT) target market groups and the statement fields they are filed as (the filer maps its own file; the door
// stores what is filed, in the manufacturer's words, with the file's version and hash in source)
const EMT = [['Investor type (retail · professional · eligible counterparty)', 'positive_target_market.<market>.client_categories', 'in the market\'s own category words (its chapter\'s client_categories)'],
  ['Knowledge and/or experience', 'positive_target_market.<market>.knowledge_and_experience', 'as the manufacturer states it'],
  ['Ability to bear losses', 'positive_target_market.<market>.ability_to_bear_loss', 'as the manufacturer states it'],
  ['Risk tolerance', 'positive_target_market.<market>.risk_tolerance', 'as the manufacturer states it (an indicator and its scale, where the file carries one)'],
  ['Client objectives and needs', 'positive_target_market.<market>.objectives_and_needs', 'as the manufacturer states it'],
  ['Any group the file marks negative', 'negative_target_market.<market>', 'the categories and profiles the product is not for, in the regime\'s words'],
  ['Distribution strategy', 'distribution_strategy', 'execution-only · with appropriateness · advised · portfolio management'],
  ['Product identification (ISIN, manufacturer LEI and name)', 'subject · manufacturer', 'the ISIN the statement is filed for; the LEI of the filer identity'],
  ['The file itself (EMT version, the file\'s hash)', 'source', '{ kind: "emt", emt_version, sha256 } — the door carries the version and the hash, never the file']];
export const emtBody = () => `<p class="lead">A manufacturer that already produces the European MiFID Template files it as the statement's source: the template's target market groups are filed as the statement fields below, in the manufacturer's words. The door stores what is filed and carries the file's version and hash; it does not fetch a file and does not judge one.</p>
${h2('mapping', 'The target market groups and the statement fields')}${table(['EMT group', 'statement field', 'as filed'], EMT.map(([g, f, n]) => [esc(g), `<code>${esc(f)}</code>`, esc(n)]))}
<p class="muted">The statement object is AIO-10060 v1.2 §6. Shape checked at filing: <a href="/docs">documentation</a>.</p><p><a href="/">gettargetmarket.ai</a> · <a href="/file">request a filer identity</a></p>`;
// TMKT-02: /file — the filer identity (build plan §5.1, the Issuerwire claim model)
export const fileBody = () => `<p class="lead">A statement is filed by the product's manufacturer, under a filer identity bound to its Legal Entity Identifier (LEI). One identity per manufacturer.</p>
${h2('claim', 'How a manufacturer obtains a filer identity')}${num(1, [
  `Ask through the contact form at <a href="https://data-licence.ai/#contact">data-licence.ai</a> (manufacturers): the LEI, the issuer domain on the product's record and a role address at that domain.`,
  'Allooloo answers with a claim token. The manufacturer shows control of the domain: a DNS TXT record at <code>_allooloo-tm.&lt;domain&gt;</code> holding <code>allooloo-tm-claim=&lt;token&gt;</code>, or the token returned from the role address.',
  'On the claim, Allooloo issues one filer identity bound to the LEI. Its value is shown to the manufacturer once; Allooloo holds only its hash.',
  'The manufacturer\'s agent files with <code>Authorization: Bearer &lt;filer value&gt;</code> on <code>file_target_market</code> at <code>https://mcp.gettargetmarket.ai/mcp</code>.'].map(x => x))}
${h2('rules', 'What a filer identity may do')}${num(2, ['File a statement for an ISIN its LEI issues (the LEI on the subject\'s record). A filing against any other subject is refused.', 'Never overwrite: a change is a new version that supersedes the last; every version stays published.', 'File at a bounded rate; filing is free.', 'The test filer, Allooloo Test Manufacturer, files only subjects in the TEST: namespace; nothing it files attaches to a live record.'].map(esc))}
<p><a href="/">gettargetmarket.ai</a> · <a href="/docs">documentation</a> · <a href="/docs/emt">the EMT mapping</a></p>`;
export const descT = () => `${H1} TM · the Target Market door: the statement, two calls, access, filing, provenance, how get_orderability uses it, receipts and the estate; ${STATE}.`;
export const targetT = () => ({ kind: 'apex', mcp: MCP, agent: AGENT, openapi: null, mcpjson: `${TM}/mcp.json`, name: 'gettargetmarket' });
export const pathsT = () => ['/', '/docs'].concat(KIT);
export const sweep = sweepDate;
