// Directory support pages (CEO order, Sept 13 2026): capitalmarketsknowledgegraph.ai/docs (connector documentation for the apex door) and allooloo.io/support (the support door).
// Shared template, no nav tab underlined, acronyms spelled out on first use, counts live from list_nodes (the live map the Worker already reads) — never typed.
import { OPERATOR, CONTACT2, APEX, APEX_AGENT, SURFACES_VERSION, REGION_FULL, esc, int, table, contactSection } from './chrome.js';
import NODE_DATA from './nodes.js';
import { ORDER } from './products.js';
import { doorOf, cardOf } from './roster.js';   // ENUM-01: doors from the roster entry

const MCP = `${APEX}/mcp`;
const ex = (req, res) => `<pre><code>${esc(JSON.stringify(req))}\n→ ${esc(res)}</code></pre>`;
// Wire examples of record — captured from the apex door on 2026-09-13 (TSX:SHOP, LSE:BARC), trimmed to the fields an integrator reads first.
const EX = {
  signal: ex({ jsonrpc: '2.0', id: 6, method: 'tools/call', params: { name: 'get_signal', arguments: { identifier: 'DE0007164600' } } },
    '{"signal":"ACM-451","state":"READ THE FILING","meaning":"A regulatory filing is dated in the last three days: a person reads it before the agent acts.","signal_page":"https://acm-451.ai/","standard":"https://acm-68000.org/","read_at":"2026-10-28T03:00:16.362Z","record_signature":{"alg":"EdDSA","kid":"allooloo-cmr-2026-10","jwks":"https://allooloo.ai/.well-known/jwks.json","jws":"…"},"identifier":"DE0007164600","issuer":"SAP SE O.N.","node":"de-cm-kg","cmr":"de-cm-kg/XETRA/SAP","exchange":"Xetra","isin":"DE0007164600","lei":"529900D6BF99LW9R2E68","as_of":"2026-10-27","record":"https://mcp.de-cm-kg.ai/record/XETRA/SAP","events":"https://mcp.de-cm-kg.ai/events/XETRA/SAP","eco":"https://de-eco.ai/",…}'),
  resolve: ex({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'resolve_issuer', arguments: { identifier: 'TSX:SHOP' } } },
    '{"matches":[{"cmr":"ca-cm-kg/TSX/SHOP","node":"ca-cm-kg","version":1,"as_of":"2026-09-10","name":"Shopify Inc.","ticker":"SHOP","exchange":"TSX","isin":"CA82509L1076","lei":"549300HGQ43STJLLP808","event_count":2,"record_url":"https://mcp.ca-cm-kg.ai/record/TSX/SHOP"}],"matched_by":"ticker","ambiguous":false,"nodes_asked":["ca-cm-kg"]}'),
  record: ex({ jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name: 'get_record', arguments: { identifier: 'LSE:BARC' } } },
    '{"cmr":"uk-cm-kg/LSE/BARC","node":"uk-cm-kg","as_of":"2026-09-11","version":1,"identity":{"name":{"value":"BARCLAYS PLC","source_url":"https://www.londonstockexchange.com/…","read_by":"LSE price-explorer feed","state":"sourced"},…},"aliases":[…],"events_url":"https://mcp.uk-cm-kg.ai/events/LSE/BARC","event_count":1774,"gaps":[…],"served_by":{"node":"uk-cm-kg","regional_door":"https://mcp.uk-cm-kg.ai/mcp","agent_card":"https://agent.uk-cm-kg.ai/.well-known/agent-card.json"}}'),
  events: ex({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: 'list_events_since', arguments: { identifier: 'LSE:BARC', since: '2026-06-01', limit: 2 } } },
    '{"cmr":"uk-cm-kg/LSE/BARC","since":"2026-06-01","total":…,"cursor":0,"limit":2,"next_cursor":2,"events":[{"date":"2026-09-12","event_type":"newswire_release","title":"Barclays Investor News: …","wire":"GlobeNewswire","source":"GlobeNewswire","url":"https://www.globenewswire.com/news-release/2026/09/11/…"},…],"served_by":{"node":"uk-cm-kg",…}}'),
  aliases: ex({ jsonrpc: '2.0', id: 4, method: 'tools/call', params: { name: 'list_aliases', arguments: { identifier: 'LSE:BARC' } } },
    '{"cmr":"uk-cm-kg/LSE/BARC","name":"BARCLAYS PLC","aliases":[{"value":"Barclays Bank Plc","source_url":"https://find-and-update.company-information.service.gov.uk/company/00048839","read_by":"Companies House REST API (previous names)"},…]}'),
  nodes: ex({ jsonrpc: '2.0', id: 5, method: 'tools/call', params: { name: 'list_nodes', arguments: {} } },
    '{"door":"apex router: index only; records and events are served by each node\'s regional door","live_nodes":["ca-cm-kg","uk-cm-kg",…],"nodes":[{"node":"ca-cm-kg","country":"Canada","door":"https://mcp.ca-cm-kg.ai","live":true,"as_of":"2026-09-10","records":4820,"events":25222,"exchanges":["TSX","TSXV","CSE","CBOE-CANADA"],…},…]}')
};

export function docsBody(live) {
  const ln = ORDER.filter(cc => (live[`${cc}-cm-kg`] || {}).live); const t = ln.reduce((a, cc) => { const n = live[`${cc}-cm-kg`]; a.records += n.records || 0; a.events += n.events || 0; return a; }, { records: 0, events: 0 });
  const rows = ORDER.map(cc => { const n = live[`${cc}-cm-kg`] || {}; return [esc(NODE_DATA[cc].country), esc((REGION_FULL[cc] || '').replace(' (', ' Azure (')), `<code class="nw">${esc(doorOf(n))}/mcp</code>`, `<code class="nw">${esc(cardOf(n))}</code>`, n.live ? int(n.records) : 'not live', n.live ? int(n.events) : '', n.live ? esc(n.as_of || '') : ''] });
  return `<p class="lead">Connector documentation for the apex door of the Capital Markets Knowledge Graph: how to connect, the six tools, the identifiers, the record shape, where records live, what data is handled, limits and versioning, support. Counts on this page are read live from <code>list_nodes</code> at render: ${ln.length} live nodes, ${int(t.records)} issuer records, ${int(t.events)} dated disclosure events.</p>

<h2>1. Connect</h2>
<p>Server URL <code>${esc(MCP)}</code>. Transport: Streamable HTTP over the Model Context Protocol (MCP), JSON-RPC 2.0 (JavaScript Object Notation Remote Procedure Call) over HTTPS. Authentication: none. Sign-in: not required. Claude: Settings → Connectors → Add custom connector → paste the URL. The same URL serves every client; a plain <code>GET</code> on it answers 405 by design — the door speaks JSON-RPC by <code>POST</code>.</p>
${EX.resolve.replace('tools/call', 'tools/call').replace(/^<pre>/, '<pre>')}

<h2>2. Tools</h2>
<p>Six tools, all read-only (every tool carries <code>readOnlyHint: true</code> in its annotations). Parameters marked <code>?</code> are optional.</p>
${table(['tool', 'parameters', 'returns', 'wire example'], [
  ['<code>resolve_issuer</code>', '<code>identifier</code>', 'record summary: node, version, as_of, name, ticker, exchange, ISIN, LEI, event count, record and events URLs; <code>matched_by</code>, <code>ambiguous</code>', EX.resolve],
  ['<code>get_record</code>', '<code>identifier</code>, <code>version?</code>', 'the full Capital Markets Record (CMR): identity fields each with value, source_url, read_by and state; aliases; events URL and count; gaps; served_by', EX.record],
  ['<code>list_events_since</code>', '<code>identifier</code>, <code>since?</code>, <code>cursor?</code>, <code>limit?</code>', 'dated, sourced disclosure events since a date (YYYY-MM-DD; omitted = the full twelve-month window), paged by cursor', EX.events],
  ['<code>list_aliases</code>', '<code>identifier</code>', 'sourced trade and former names, each with its source URL and reader', EX.aliases],
  ['<code>list_nodes</code>', 'none', 'every market node on the roster, which are live, their regional doors, record and event counts, drop dates', EX.nodes],
  ['<code>get_signal</code>', '<code>identifier</code>', 'the ACM-68000 signal for a listed security in its home market — ACM-200 TRADING · ACM-403 HALTED · ACM-404 NOT ON THE REGISTER · ACM-451 READ THE FILING · ACM-300 CONDITIONAL — with the record signature, the node, the record and events URLs and the market\'s ECO page', EX.signal]
])}
<p class="src">Examples of record: <code>TSX:SHOP</code> and <code>LSE:BARC</code>, both verified live on the wire on 2026-09-13; <code>DE0007164600</code> (get_signal) captured 2026-10-28; responses trimmed to the leading fields, "…" marks the cut.</p>

<h2>3. Identifiers</h2>
<p>An <code>identifier</code> is any of: a ticker with or without its exchange (<code>SHOP</code>, <code>TSX:SHOP</code>, <code>SHOP.TO</code>, <code>SHEL.L</code>, <code>BHP.AX</code>, <code>7203.T</code>); an International Securities Identification Number (ISIN); a Legal Entity Identifier (LEI); the exact legal name; a sourced alias; or a CMR key such as <code>ca-cm-kg/TSX/SHOP</code>. The apex holds an index only: it names the owning node and forwards. The record is served by that node's regional door in the issuer's own jurisdiction and is never stored at the apex.</p>

<h2>4. The record shape</h2>
<p>Every field of a Capital Markets Record carries four parts: <code>value</code>, <code>source_url</code> (the public filing or registry page it was read from), <code>read_by</code> (the registry API or the reading engine) and <code>state</code> — one of <code>sourced</code> (read from the filing), <code>filled</code> (read by an engine, not yet confirmed), <code>confirmed</code> (two sources agree), <code>conflict</code> (sources disagree; both kept) or <code>unverified</code>. Record level: <code>as_of</code> (the drop date), <code>version</code>, a <code>gaps</code> list naming what could not be read, and <code>served_by</code> (node, regional door, Agent Card). Machine descriptions: <a href="${APEX}/openapi.json">openapi.json</a> (OpenAPI 3.1, the REST twin of the door) and <a href="${APEX}/mcp.json">mcp.json</a> (the MCP descriptor).</p>

<h2>5. Residency</h2>
<p>Records are stored and served in the issuer's own jurisdiction. Every live node on the roster, each in its own Microsoft Azure region, region written in full; counts and drop dates read live from <code>list_nodes</code> at render.</p>
<div class="wrap">${table(['node', 'Azure region', 'regional door (MCP)', 'Agent Card (A2A)', 'issuer records', 'events', 'drop'], rows)}</div>
<p>Hong Kong is a full node (ORDER-035): English-language filings from HKEXnews, served from East Asia (Hong Kong).</p>

<h2>6. Data handling</h2>
<p>Public-record data only: listing rosters, company registries, exchange notices and newswire releases, each field named to its source. No prices, no quotes, no licensed market data. No user data is collected or stored: the door takes an identifier and returns a record; there is no account, no session, no token on the public routes, no write path, and no cookies on any surface of the estate. Calls are not attributed to a caller. The operator's identity is on every response in the <code>X-CMR-Operator</code> header.</p>

<h2>7. Limits and versioning</h2>
<p>Record version: as it stands on the wire, every record response carries <code>X-CMR-Version: 1</code> and <code>version: 1</code> in the body (record version 1; a prior version can be asked for with <code>get_record(identifier, version)</code>). The apex and node doors report <code>serverInfo.version</code> 0.12.1 on <code>initialize</code>; this surface reports <code>X-Surface-Version: ${esc(SURFACES_VERSION)}</code>. Rate limit: none of the operator's at the edge — no rate-limiting rule is configured on the doors; the doors answer every caller at the same speed, and a caller that floods one will see the edge's ordinary connection limits, not a quota.</p>

<h2>8. Support and security</h2>
<p>Support: <a href="https://allooloo.io/support">allooloo.io/support</a>. Security and responsible disclosure: <a href="https://allooloo.io/security">allooloo.io/security</a> and <a href="/.well-known/security.txt">/.well-known/security.txt</a>.</p>`;
}

// NEWS-01 (2026-10-27): allooloo.io/news — releases of record, newest first; then the newcomers block.
// SITE-01 (Site Build Plan v2.2 §8, 2026-10-28): 'As covered in' — outlet name as anchor text, href = the pickup URL from PR Newswire's C0817 visibility report (Oct 22 2026), appendix A order.
const COVERAGE_20261022 = [
  ['Yahoo! Finance', 'https://finance.yahoo.com/technology/ai/articles/allooloo-technologies-corp-launches-ai-231100929.html'],
  ['Yahoo! Finance Canada', 'https://ca.finance.yahoo.com/news/allooloo-technologies-corp-launches-ai-231100215.html'],
  ['AP News', 'https://apnews.com/press-release/pr-newswire/press-release-b55cf5fd66aa0d6128ead1b144f80c02'],
  ['Morningstar', 'https://www.morningstar.com/news/pr-newswire/20261022va79501/allooloo-technologies-corp-launches-ai-agent-products-for-financial-services-agents-know-your-product-and-news'],
  ['Benzinga', 'https://www.benzinga.com/pressreleases/26/10/n62549655/allooloo-technologies-corp-launches-ai-agent-products-financial-services-agents-know-your-product-an'],
  ['TheStreet', 'https://prconnect.thestreet.com/article/Allooloo-Technologies-Corp-Launches-AI-Agent-Products-for-Financial-Services-Agents-Know-Your-Product-and-News?storyId=6ada98a4dba4ed9cc76d9254'],
  ['KTLA', 'https://www.ktla.com/business/press-releases/cision/20261022VA79501/allooloo-technologies-corp-launches-ai-agent-products-for-financial-services-agents-know-your-product-and-news'],
  ['FinTech Magazine', 'https://fintechmagazine.com/pr_newswire?rkey=20261022EN79501&filter=21513'],
  ['AI Magazine', 'https://aimagazine.com/pr_newswire?rkey=20261022EN79501&filter=21531'],
  ['Procurement Magazine', 'https://procurementmag.com/pr_newswire?rkey=20261022EN79501&filter=22720'],
  ['Business Chief', 'https://businesschief.com/pr_newswire?rkey=20261022VA79501&filter=22716'],
  ['Business Chief APAC', 'https://businesschief.asia/pr_newswire?rkey=20261022AE79501&filter=22718'],
  ['Vulcan Post', 'https://vulcanpost.com/prnewswire/?rkey=20261022AE79501&filter=28460'],
  ['The Malaysian Reserve', 'https://themalaysianreserve.com/2026/10/22/allooloo-technologies-corp-launches-ai-agent-products-for-financial-services-agents-know-your-product-and-news/'],
  ['TechNode Global', 'https://technode.global/prnasia/allooloo-technologies-corp-launches-ai-agent-products-for-financial-services-agents-know-your-product-and-news/'],
  ['Kosmo!', 'https://www.kosmo.com.my/2026/10/22/allooloo-technologies-corp-launches-ai-agent-products-for-financial-services-agents-know-your-product-and-news/'],
  ['huvle', 'https://en.huvle.com/news/view.do?guid=20261023082700948483'],
  ['Deeptech Times', 'https://deeptechtimes.com/breakingnews/?rkey=20261022AE79501&filter=26642'],
  ['Macau Business', 'https://macaubusiness.com/allooloo-technologies-corp-launches-ai-agent-products-for-financial-services-agents-know-your-product-and-news/'],
  ['AAP News', 'https://aapnews.aap.com.au/aapreleases/cision20261022AE79501'],
];
const NEWS = [
  { date: '2026-10-22', title: 'Allooloo Technologies Corp. Launches AI Agent Products for Financial Services Agents: Know Your Product and News', url: 'https://www.prnewswire.co.uk/news-releases/allooloo-technologies-corp-launches-ai-agent-products-for-financial-services-agents-know-your-product-and-news-302917526.html', coverage: COVERAGE_20261022, line: 'Agentic capital markets products for the AI agents of banks, dealers and issuers. Two products — KYP and Issuerwire — 34 countries, paid per read, in the call.' },
];
export const NEWS_AS_OF = NEWS[0].date;
export function newsBody() {
  return NEWS.map(n => `<h2>${esc(n.date)} — <a href="${esc(n.url)}">${esc(n.title)}</a></h2>\n<p>${esc(n.line)}</p>` + (n.coverage ? `
<h3>As covered in</h3>
<ul>${n.coverage.map(([o, u]) => `<li><a href="${esc(u)}">${esc(o)}</a></li>`).join('')}</ul>` : '')).join('\n') + `
<h2>For newcomers</h2>
<p><a href="https://allooloo.io/connect">allooloo.io/connect</a> · <a href="https://allooloo.io/support">allooloo.io/support</a> · <a href="https://www.crunchbase.com/organization/allooloo">Crunchbase</a> · <a href="https://www.linkedin.com/company/allooloo-technologies-corp/">LinkedIn</a></p>`;
}

export function supportBody(host) {
  return `<p class="lead">Bring four things: the identifier you called, the tool, the door that answered (the <code>X-CMR-Node</code> header or <code>served_by</code> in the body), and the <code>as_of</code> on the response.</p>
${contactSection(host)}
<p>Status: <a href="https://allooloo.io/status">allooloo.io/status</a> — every live door on the roster probed every five minutes.</p>
<p>Security: <a href="https://allooloo.io/security">allooloo.io/security</a> and <a href="/.well-known/security.txt">/.well-known/security.txt</a>.</p>
<p>Documentation: <a href="https://getissuer.ai/docs">getissuer.ai/docs</a>.</p>`;
}

// Enterprise setup page (CEO ORDER-022, Sept 16 2026): allooloo.io/setup — what an enterprise AI platform's connector form needs, nothing more.
export function setupBody(host) {
  return `<p class="lead">Enterprise setup for the Capital Markets Knowledge Graph connector: the two fields a connector form asks for, the authentication answer, what the six tools do and do not do, and where support and privacy live.</p>

<h2>1. Server</h2>
${table(['field', 'value'], [
  ['Server URL', `<code>${esc(MCP)}</code>`],
  ['Transport', 'Streamable HTTP (Model Context Protocol, JSON-RPC 2.0 over HTTPS)'],
  ['Name', 'Capital Markets Knowledge Graph'],
  ['Agent card', `<a href="${APEX_AGENT}/.well-known/agent-card.json"><code>${esc(APEX_AGENT)}/.well-known/agent-card.json</code></a>`]
])}
<p>A plain <code>GET</code> on the server URL answers 405 by design: the door speaks JSON-RPC by <code>POST</code>. Documentation for integrators: <a href="https://getissuer.ai/docs">getissuer.ai/docs</a>.</p>

<h2>2. Authentication</h2>
<p><strong>None.</strong> OAuth Client ID and Client Secret stay blank. There is no enterprise managed authentication to configure: the door issues no challenge, needs no token and runs no client registration. If the connector form insists on a method, choose "None" or "No authentication".</p>

<h2>3. Tools and data</h2>
<p>Six read-only tools are open: <code>resolve_issuer</code>, <code>get_record</code>, <code>get_signal</code>, <code>list_events_since</code>, <code>list_aliases</code>, <code>list_nodes</code>. No sign-in. No user data is stored. Nothing is written: there is no write path on the door. Every record is signed (EdDSA, key <code>allooloo-cmr-2026-10</code>); verify against <a href="https://allooloo.ai/.well-known/jwks.json">allooloo.ai/.well-known/jwks.json</a>. Public-record data only — listing rosters, company registries, exchange notices and newswire releases, each field named to its source — and no prices, quotes or licensed market data.</p>

<h2>4. Support and privacy</h2>
<p>Support: <a href="https://allooloo.io/#contact">allooloo.io/#contact</a> (the contact form of record) and <a href="https://allooloo.io/support">allooloo.io/support</a>. Privacy: <a href="https://allooloo.io/privacy">allooloo.io/privacy</a>. Security: <a href="https://allooloo.io/security">allooloo.io/security</a>.</p>`;
}
