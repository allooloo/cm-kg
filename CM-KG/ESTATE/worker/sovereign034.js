// ORDER-034 (2026-10-22) — SOVEREIGN NODES: twelve <country>-issuer.ai node pages, gb-issuer.ai (301 → uk-issuer.ai), and the two standards pages kyp-model.org and issuerwire.org.
// Record-grade standard (ORDER-020 §0): under 50 KB a page, zero scripts, two colours (/issuer.css), a markdown twin by Accept negotiation. Five sections a node page:
// market and duty · live count · door · residency · machine kit. Counts are read at render — list_nodes on the apex for get_issuer, issuerwire.ai/facts.json for Issuerwire — never typed.
// Regulator and duty lines come from the live node surfaces (nodes.js, the source <cc>-cm-kg.ai renders); the build memo's table is not copied. /mcp on every node page → 302 to the apex door, never a regional door.
// A market Issuerwire carries prints both doors; which markets it carries is read from its facts.json at render, so a market flips to both doors the night ISSUERWIRE-02 seeds it.
// hk-issuer.ai prints "node arming" in the door section until https://mcp.hk-cm-kg.ai/healthz answers 200 (ORDER-035), then the door. UK in every human string; GB only in the zone name.
// No acronym is left unspelled on first use: every human string passes through spell() with a per-render set (GLOSS below).
import NODE_DATA from './nodes.js';
import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ROBOTS, SECURITY, regionAzure, esc, int, today, headers, sitemap, form, navHeader, estateFooter, SPRITE } from './chrome.js';   // SITE-04A: the nav of record + the estate footer
import * as AEO from './aeo.js';
import * as OAUTH from './oauth.js';
import { KYP_CAPTURE, IW_CAPTURE } from './captures034.js';

const GI = 'https://getissuer.ai', GI_MCP = 'https://mcp.getissuer.ai/mcp', GI_AGENT = 'https://agent.getissuer.ai/.well-known/agent-card.json';
const IW = 'https://issuerwire.ai', IW_MCP = 'https://mcp.issuerwire.ai/mcp', IW_FACTS = 'https://issuerwire.ai/facts.json', IW_KEYS = 'https://issuerwire.ai/.well-known/jwks.json';
const HK_HEALTH = 'https://mcp.hk-cm-kg.ai/healthz';
const NODES = ['ca', 'uk', 'us', 'de', 'fr', 'nl', 'ch', 'au', 'sg', 'jp', 'kr', 'hk'];
const MKT = { ca: 'CA', uk: 'UK', us: 'US', de: 'DE', fr: 'FR', nl: 'NL', ch: 'CH', au: 'AU', sg: 'SG', jp: 'JP', kr: 'KR', hk: 'HK' };   // Issuerwire's market codes (facts.json issuers_by_market keys)
const STD = { kyp: 'kyp-model.org', iw: 'issuerwire.org' };

// ---------- first-use spelling: the acronym → its words, once per page
const GLOSS = {
  UK: 'United Kingdom', MCP: 'Model Context Protocol', A2A: 'Agent-to-Agent', AI: 'artificial intelligence', JSON: 'JavaScript Object Notation', HTTP: 'Hypertext Transfer Protocol', URL: 'web address', API: 'application programming interface',
  KYP: 'Know Your Product', CMR: 'Capital Markets Record', LEI: 'Legal Entity Identifier', ISIN: 'International Securities Identification Number', GLEIF: 'Global Legal Entity Identifier Foundation', CIK: 'Central Index Key', SEDOL: 'Stock Exchange Daily Official List number',
  TSX: 'Toronto Stock Exchange', TSXV: 'TSX Venture Exchange', CSE: 'Canadian Securities Exchange', 'SEDAR+': 'System for Electronic Data Analysis and Retrieval', CDR: 'Canadian Depositary Receipt', CDRs: 'Canadian Depositary Receipts',
  US: 'United States', EIN: 'Employer Identification Number', SIC: 'Standard Industrial Classification', SPAC: 'special purpose acquisition company', MIC: 'Market Identifier Code', HRB: 'Handelsregister Abteilung B', HRA: 'Handelsregister Abteilung A',
  BDIF: 'Base des décisions et informations financières', INSEE: 'Institut national de la statistique et des études économiques', SIREN: 'Système d’identification du répertoire des entreprises', NAF: 'nomenclature d’activités française', KVK: 'Kamer van Koophandel',
  UID: 'Unternehmens-Identifikationsnummer', CR: 'Companies Registry', BRN: 'Business Registration Number', IFRS: 'International Financial Reporting Standards', GAAP: 'generally accepted accounting principles', ADR: 'American Depositary Receipt', ADRs: 'American Depositary Receipts', SPV: 'special purpose vehicle',
  FCA: 'Financial Conduct Authority', PROD: 'Product Intervention and Product Governance Sourcebook', LSE: 'London Stock Exchange', AIM: 'Alternative Investment Market', AQSE: 'Aquis Stock Exchange', RNS: 'Regulatory News Service', NSM: 'National Storage Mechanism', PLC: 'public limited company',
  SEC: 'Securities and Exchange Commission', FINRA: 'Financial Industry Regulatory Authority', NYSE: 'New York Stock Exchange', EDGAR: 'Electronic Data Gathering, Analysis and Retrieval system', 'U.S.': 'United States', XBRL: 'eXtensible Business Reporting Language', iXBRL: 'inline XBRL',
  AMF: 'Autorité des marchés financiers', AFM: 'Autoriteit Financiële Markten', 'MiFID II': 'Markets in Financial Instruments Directive II', FIRDS: 'Financial Instruments Reference Data System', ESMA: 'European Securities and Markets Authority', EU: 'European Union',
  FINMA: 'Swiss Financial Market Supervisory Authority', FinSA: 'Financial Services Act', SHAB: 'Swiss Official Gazette of Commerce', SOGC: 'Swiss Official Gazette of Commerce',
  BaFin: 'Federal Financial Supervisory Authority', FWB: 'Frankfurter Wertpapierbörse', AG: 'Aktiengesellschaft', DGAP: 'Deutsche Gesellschaft für Ad-hoc-Publizität',
  ASIC: 'Australian Securities and Investments Commission', ASX: 'Australian Securities Exchange', NSX: 'National Stock Exchange of Australia', DDO: 'Design and Distribution Obligations', ABN: 'Australian Business Number', ACN: 'Australian Company Number',
  MAS: 'Monetary Authority of Singapore', SGX: 'Singapore Exchange', RegCo: 'Regulation Company', ACRA: 'Accounting and Corporate Regulatory Authority', UEN: 'Unique Entity Number', SGXNet: 'Singapore Exchange network',
  FSA: 'Financial Services Agency', FIEA: 'Financial Instruments and Exchange Act', JPX: 'Japan Exchange Group', EDINET: 'Electronic Disclosure for Investors’ NETwork', TDnet: 'Timely Disclosure network', TSE: 'Tokyo Stock Exchange',
  FSC: 'Financial Services Commission', FSS: 'Financial Supervisory Service', DART: 'Data Analysis, Retrieval and Transfer System', KRX: 'Korea Exchange', FSCMA: 'Financial Investment Services and Capital Markets Act', KIND: 'Korea Investor’s Network for Disclosure', KOSPI: 'Korea Composite Stock Price Index market', KOSDAQ: 'Korea Securities Dealers Automated Quotations market', KONEX: 'Korea New Exchange',
  SFC: 'Securities and Futures Commission', HKEX: 'Hong Kong Exchanges and Clearing', HKEXnews: 'the HKEX disclosure site', GEM: 'Growth Enterprise Market', REIT: 'real estate investment trust', REITs: 'real estate investment trusts',
  ETF: 'exchange-traded fund', ETFs: 'exchange-traded funds', AGM: 'annual general meeting', CEO: 'chief executive officer',
  REST: 'representational state transfer', SME: 'small and medium-sized enterprise', GICS: 'Global Industry Classification Standard', CSV: 'comma-separated values', PDF: 'Portable Document Format', PDFs: 'Portable Document Format files', RSS: 'Really Simple Syndication'
};
const KEYS = Object.keys(GLOSS).sort((a, b) => b.length - a.length);
const RX = new RegExp(`(?<![A-Za-z0-9.])(${KEYS.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})(?![A-Za-z0-9+])`, 'g');
export function speller() {
  const seen = new Set();
  // a form the source already spells — "Words (ACR)" or "ACR (Words)" — counts as the first use and is left as written
  const sp = s => String(s == null ? '' : s).replace(RX, (m, _a, off, str) => {
    if (seen.has(m)) return m; seen.add(m);
    if (str[off - 1] === '(' && str[off + m.length] === ')') return m;
    if (str.slice(off + m.length, off + m.length + 2) === ' (' && str.slice(off + m.length + 2).toLowerCase().startsWith(GLOSS[m].split(' ')[0].toLowerCase())) return m;
    const words = sp(GLOSS[m]); return m === 'U.S.' ? words : `${words} (${m})`;
  });
  return sp;
}

// ---------- the zones
export function classify34(host) {
  const h = host.replace(/^www\./, ''); let m;
  if (h === 'gb-issuer.ai') return { kind: 'redirect', canonical: 'https://uk-issuer.ai', status: 301 };
  if ((m = h.match(/^([a-z]{2})-issuer\.ai$/)) && NODES.includes(m[1])) return { kind: 'sov', cc: m[1], host: h };
  if (h === STD.kyp) return { kind: 'std', which: 'kyp', host: h };
  if (h === STD.iw) return { kind: 'std', which: 'iw', host: h };
  return null;
}

// ---------- live reads (five-minute cache, one isolate)
let IWF = null, IWF_AT = 0, HKU = null, HKU_AT = 0;
async function iwFacts() {
  if (IWF && Date.now() - IWF_AT < 300000) return IWF;
  try { const r = await fetch(IW_FACTS, { headers: { accept: 'application/json', 'user-agent': 'Allooloo estate-pages (ORDER-034)' }, signal: AbortSignal.timeout(8000) }); if (r.ok) { IWF = await r.json(); IWF_AT = Date.now(); } } catch (e) { }
  return IWF || {};
}
async function hkUp() {
  if (HKU !== null && Date.now() - HKU_AT < 300000) return HKU;
  try { const r = await fetch(HK_HEALTH, { signal: AbortSignal.timeout(6000) }); HKU = r.status === 200; } catch (e) { HKU = false; }
  HKU_AT = Date.now(); return HKU;
}
const iwCovers = (iw, cc) => { const k = MKT[cc]; return Array.isArray(iw.markets) && iw.markets.includes(k) && Number((iw.issuers_by_market || {})[k]) > 0; };
const countryName = cc => NODE_DATA[cc].country;

// ---------- per-market lines (who reads the node, in that market's own terms); the regulator and duty values themselves come from NODE_DATA
const READER = {
  ca: 'an investment dealer’s or portfolio manager’s agent that has to know the product on its shelf before it is sold to a Canadian client',
  uk: 'a broker’s, platform’s or wealth manager’s agent that has to show it knew the product and its target market before distributing it to a UK retail client',
  us: 'a broker-dealer’s agent that needs a reasonable basis on the security before a recommendation reaches a United States customer',
  de: 'a German distributor’s agent that has to keep each product inside its approved target market under the German product-oversight rules',
  fr: 'a French distributor’s agent that maps each product to its target market and keeps the file the French regulator can ask for',
  nl: 'a Dutch distributor’s agent that holds the product approval file the Dutch regulator expects for every listed instrument it offers',
  ch: 'a Swiss financial service provider’s agent that has to explain the product, its risks and its costs before advising a client in Switzerland',
  au: 'an Australian distributor’s agent that has to keep each listed product inside the target market determination its issuer published',
  sg: 'a Singapore distributor’s agent that runs product due diligence before a listed product reaches its customers',
  jp: 'a Japanese securities firm’s agent that has to fit each listed product to the customer’s knowledge, experience and assets',
  kr: 'a Korean investment firm’s agent that has to judge suitability and appropriateness before it sells a listed product',
  hk: 'a Hong Kong intermediary’s agent that has to match a listed product to its client before it recommends or solicits'
};

// ---------- the page shell: no script, no inline style, the one stylesheet, the contact block of record, one-row footer
function shell({ host, title, desc, h1, state, asOf, body, sp, kyp }) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="https://${host}/"><meta name="robots" content="index,follow">
<link rel="stylesheet" href="/issuer.css?v=${SURFACES_VERSION}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon.ico" sizes="any">
<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt"><link rel="alternate" type="application/json" href="/facts.json" title="facts.json"><link rel="alternate" type="text/markdown" href="/" title="markdown twin (Accept: text/markdown)"></head><body>${SPRITE}
${navHeader(host, { nocurrent: true, kyp })}</header>
<main><h1>${esc(h1)}</h1><p class="state">${esc(state)} · as of ${esc(asOf || today())} · surfaces ${esc(SURFACES_VERSION)}</p>${body}
<h2>Contact</h2>${form(host)}</main>
${estateFooter(host)}<script src="/webmcp.js"></script></body></html>`;
}
const li = items => `<dl>${items.map((v, i) => `<dt>${i + 1}</dt><dd>${v}</dd>`).join('')}</dl>`;
const code = s => `<code>${esc(s)}</code>`;

// ---------- node page (five sections)
function nodeView(cc, live, iw, hkAnswering) {
  const d = NODE_DATA[cc]; const n = live[`${cc}-cm-kg`] || {}; const isLive = !!n.live;
  const both = iwCovers(iw, cc); const arming = cc === 'hk' && !hkAnswering;
  return { d, n, isLive, both, arming, country: d.country, region: regionAzure(cc), asOf: isLive ? (n.as_of || '') : '' };
}
export function nodeBody(host, cc, live, iw, hkAnswering, sp) {
  const v = nodeView(cc, live, iw, hkAnswering); const d = v.d; const k = MKT[cc]; sp = sp || speller();
  // the market's own particulars carry the page (sources, tiers, register, channel, language — as the node surface renders them); the fixed text stays short
  const s1 = li([esc(sp(`${v.country}: ${d.coverage}.`)),
    esc(sp(`Regulator: ${d.regulator}`)),
    esc(sp(`Duty: ${d.duty} — the record an agent cites under it.`)),
    esc(sp(`Read by ${READER[cc]}.`)),
    esc(sp(`Tiers: ${d.tiers}`)),
    esc(sp(`Sources of record: ${d.sources}.`)),
    esc(sp(`Disclosure channel: ${d.channel}`)),
    esc(sp(`Register: ${d.register}`)),
    esc(sp(`Language: ${d.language}`))]);
  const gi = v.isLive ? `get_issuer: <strong>${int(n_(v.n.records))}</strong> ${esc(sp('issuers'))} · <strong>${int(n_(v.n.events))}</strong> ${esc(sp('dated disclosures'))} · ${esc(sp(`as of ${v.asOf}, the sweep market date`))} <span>(list_nodes)</span>`
    : esc(sp(cc === 'hk' ? 'get_issuer: node arming — no count until its door answers.' : 'get_issuer: not live at render — no count printed.'));
  const iwl = v.both ? `Issuerwire: <strong>${int(n_((iw.issuers_by_market || {})[k]))}</strong> ${esc(sp('issuers'))} · <strong>${int(n_((iw.filings_by_market || {})[k]))}</strong> ${esc(sp('signed filing rows'))} <span>(issuerwire.ai/facts.json)</span>` : esc(sp('Issuerwire: not carried yet.'));
  const s2 = li([gi, iwl]);
  const doors = v.arming
    ? [esc(sp(`Node arming in ${v.region}; no endpoint until it answers.`)), esc(sp('Other markets: ')) + code(GI_MCP)]
    : [esc(sp('get_issuer (MCP, no authentication): ')) + code(GI_MCP)]
      .concat(v.both ? [esc(sp('Issuerwire: ')) + code(IW_MCP)] : [])
      .concat([esc(sp('Agent card (A2A): ')) + code(GI_AGENT), esc(sp('/mcp here: ')) + code(`GET → 302 ${GI_MCP}`)]);
  const s4 = li([esc(sp(`${v.region}.`)), esc(sp(`In-country: stored and served in ${v.region}; the apex holds an index only; no ${v.country} record body leaves ${v.country}; no fallback.`))]);
  const s5 = li([['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/robots.txt', '/sitemap.xml', '/mcp'].map(p => `<a href="${p}">${code(p)}</a>`).join(' · '),
    code('X-CMR-Node X-CMR-As-Of X-CMR-Version X-CMR-Source X-CMR-Operator X-CMR-Contact'),
    `<a href="https://kyp-model.org/">kyp-model.org</a>` + (v.both ? ' · <a href="https://issuerwire.org/">issuerwire.org</a>' : '')]);
  return { html: `<h2>Market and duty</h2>${s1}<h2>Live count</h2>${s2}<h2>Door</h2>${li(doors)}<h2>Residency</h2>${s4}<h2>Machine kit</h2>${s5}`, v };
}
const n_ = x => (typeof x === 'number' ? x : Number(x));
function nodeTitle(cc) { return `${cc}-issuer.ai — the ${countryName(cc)} issuer record for agents`; }
function nodeH1(cc) { return `${countryName(cc)}: the issuer record an agent cites under ${NODE_DATA[cc].duty}`; }
function nodeDesc(cc, v) { return `${v.country} node of the Allooloo issuer record. Regulator, duty, live counts, the door, residency in ${v.region} and the machine kit.`; }
export function nodeLlms(host, cc, live, iw, hkAnswering) {
  const v = nodeView(cc, live, iw, hkAnswering); const d = v.d; const sp = speller(); const k = MKT[cc];
  return [`# ${host} — ${v.country} issuer record (sovereign node page)`,
    sp(`1. Operator: ${OPERATOR}. Contact: ${CONTACT}. This page answers nothing itself; it names the door for ${v.country}.`),
    sp(`2. Market: ${v.country}. Coverage: ${d.coverage}. Regulator: ${d.regulator} Duty: ${d.duty} — the record an agent cites under it.`),
    v.isLive ? sp(`3. get_issuer count (list_nodes, at render): ${v.n.records} issuers, ${v.n.events} dated disclosures, as of ${v.asOf}.`) : sp(`3. get_issuer count: ${cc === 'hk' ? 'node arming — no count yet' : 'not live at render'}.`),
    v.both ? sp(`4. Issuerwire count (issuerwire.ai/facts.json, at render): ${(iw.issuers_by_market || {})[k]} issuers, ${(iw.filings_by_market || {})[k]} signed filing rows.`) : sp(`4. Issuerwire: ${v.country} not carried yet.`),
    v.arming ? sp(`5. Door: node arming in ${v.region}; until it answers, use ${GI_MCP} for every other market.`) : sp(`5. Door (MCP, Streamable HTTP, no authentication): ${GI_MCP} — the apex; never a regional door.${v.both ? ` Also Issuerwire: ${IW_MCP}.` : ''} Agent card: ${GI_AGENT}.`),
    sp(`6. Residency: ${v.region}. In-country; no record body leaves ${v.country}; no fallback.`),
    `7. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /robots.txt /sitemap.xml /mcp (GET → 302 ${GI_MCP}).`,
    `8. Standard of the row: https://kyp-model.org/${v.both ? ' · https://issuerwire.org/' : ''}`,
    `9. Surfaces version ${SURFACES_VERSION}; counts read at render, never typed.`].join('\n') + '\n';
}
export function nodeFacts(host, cc, live, iw, hkAnswering) {
  const v = nodeView(cc, live, iw, hkAnswering); const d = v.d; const k = MKT[cc];
  return { domain: host, kind: 'sovereign node page', node: `${cc}-cm-kg`, market: v.country, regulator: d.regulator, duty: d.duty, line_of_record: `the record an agent cites under ${d.duty}`,
    get_issuer: { door: v.arming ? null : GI_MCP, state: v.arming ? 'node arming' : (v.isLive ? 'live' : 'not live'), issuers: v.isLive ? v.n.records : null, disclosures: v.isLive ? v.n.events : null, as_of: v.asOf || null, counts_from: 'list_nodes on the apex, at render' },
    issuerwire: v.both ? { door: IW_MCP, issuers: (iw.issuers_by_market || {})[k], signed_filing_rows: (iw.filings_by_market || {})[k], store_as_of: iw.store_as_of, counts_from: IW_FACTS } : { door: null, state: 'market not carried yet' },
    residency: v.region, in_country: true, no_fallback: true, mcp_get: `302 → ${GI_MCP}`, agent_card: GI_AGENT, standards: ['https://kyp-model.org/'].concat(v.both ? ['https://issuerwire.org/'] : []),
    operator: OPERATOR, contact: CONTACT, surface_version: SURFACES_VERSION, as_of: today(), machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/robots.txt', '/sitemap.xml', '/mcp'] };
}
function nodeCard(host, cc, live, iw, hkAnswering) {
  const v = nodeView(cc, live, iw, hkAnswering);
  const ifaces = (v.arming ? [] : [{ url: GI_MCP, transport: 'JSONRPC' }]).concat(v.both ? [{ url: IW_MCP, transport: 'JSONRPC' }] : []);
  return { name: `${v.country} issuer record — sovereign node page`, description: `${v.arming ? `Node arming in ${v.region}.` : `The ${v.country} issuer record answers at ${GI_MCP}; the apex hands each ${v.country} call to ${v.region}.`}${v.both ? ` Issuerwire carries ${v.country}: ${IW_MCP}.` : ''} This host is documentation only.`,
    url: v.arming ? `https://${host}/` : GI_MCP, preferredTransport: 'JSONRPC', supportedInterfaces: ifaces, version: SURFACES_VERSION, protocolVersion: '0.3.0', provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, iconUrl: `https://${host}/icon-512.png`,
    capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], securitySchemes: {}, security: [], agentCardOfRecord: GI_AGENT,
    skills: [{ id: 'where-the-door-is', name: `Where ${v.country} answers`, description: `Resolve, read, alias, event and node calls for ${v.country} go to ${v.arming ? 'the door once it answers' : GI_MCP}.`, tags: ['capital-markets', 'issuer-record', cc] }] };
}

// ---------- the standards pages (clause form)
export function stdBody(which, live, iw, sp) {
  sp = sp || speller();
  if (which === 'kyp') {
    const duty = NODES.filter(cc => NODE_DATA[cc]).map(cc => `<tr><td>${esc(sp(NODE_DATA[cc].country))}</td><td>${esc(sp(NODE_DATA[cc].duty))}</td><td><a href="https://${cc}-issuer.ai/">${cc}-issuer.ai</a></td></tr>`).join('');
    const c = [
      sp('The row. One Capital Markets Record (CMR) per listed issuer, keyed node/exchange/code (for example uk-cm-kg/LSE/SHEL). The node is the market that holds it; the record is stored and served in that market’s own Azure region.'),
      sp('The fields. Identity first (name, ticker, exchange, segment, ISIN, LEI, register number, registered office), then disclosure. Every field is an object: value, source_url, read_by, state.'),
      sp('State. One of sourced (read from its source of record), filled (found by a reader and not yet confirmed), confirmed (a second independent source agrees), conflict (two sources disagree; both kept). A blank stays blank; nothing is inferred.'),
      sp('The source page. Every field carries the web address it was read from. A field without one is not served.'),
      sp('The read date. The record carries as_of, the sweep’s market date; each field keeps its own read date. The two are never merged.'),
      sp('The signature. Every record is signed (EdDSA, key allooloo-cmr-2026-10); verify against https://allooloo.ai/.well-known/jwks.json. A row is proved by its source page, its read date and its signature, and by the receipt in clause 8 once it is issued.'),
      sp('The delta. list_events_since(identifier, since) answers the dated disclosures for one issuer since a date the agent holds; the agent keeps its own last read.'),
      sp('The receipt. cite-fact.ai is the permanent address for what a door served: payload, node, as_of, serving time, key and the source page of each field. Receipts are not issued yet and none is stubbed.'),
      sp('The duty map. The same row serves each market’s duty; the table below is read from the live node surfaces.'),
      sp('Versioning. The record carries an integer version; a change lands as a new version beside the old; nothing is deleted.'),
      sp('What is not carried. No prices, no quotes, no licensed market data, no ratings, no opinions, no summaries.')];
    const ex = KYP_CAPTURE;
    return `<h2>Clauses</h2>${li(c.map(esc))}<table><thead><tr><th>market</th><th>duty</th><th>node page</th></tr></thead><tbody>${duty}</tbody></table>
<h2>On the record</h2><p>${esc(sp(`Captured from the wire ${ex.captured} at ${ex.door}:`))}</p><pre>${esc(JSON.stringify(ex.request, null, 1))}</pre><pre>${esc(JSON.stringify(ex.response, null, 1))}</pre>
<h2>The door it describes</h2>${li([esc(sp('get_issuer (MCP, Streamable HTTP, no authentication): ')) + code(GI_MCP), esc(sp('Where the record lives: each market in its own Azure region, in-country; the apex holds an index only. The markets and their regions are named on the node pages and in list_nodes.'))])}`;
  }
  const mk = Array.isArray(iw.markets) ? iw.markets.map(m => m === 'UK' ? 'United Kingdom (UK)' : m === 'US' ? 'United States' : m === 'CA' ? 'Canada' : m).join(', ') : '';
  const c = [
    sp('The row. One row per filing or release: id, issuer_key, type, date, title, the source page. A row is never edited; a correction is a new row beside it.'),
    sp('The source page. Every row carries the web address of the filing as published by the issuer’s register or exchange. A row without one is not served.'),
    sp('Type. Written in English from the register’s own code table (the register’s code is kept beside it). Identifiers (ISIN, LEI, register numbers) are language-free.'),
    sp('Title. Exactly as filed, in its original language. Never machine-translated; no translation is written to the record.'),
    sp(`The signature. Every row is signed with Ed25519, key id amn-2026-10; the public keys are at ${IW_KEYS}. The full signed row is returned on the paid call (x402, one cent inside the call).`),
    sp('The delta. get_delta(issuer, since) answers every row for one issuer since the agent’s last read; the agent keeps the cursor.'),
    sp(`Markets carried at render: ${mk || 'none read'}. A market joins the night its store is seeded; its node page then prints both doors.`),
    sp('What is not carried. No summaries, no ratings, no prices, no opinions, no translations.')];
  const ex = IW_CAPTURE;
  return `<h2>Clauses</h2>${li(c.map(esc))}
<h2>On the wire</h2><p>${esc(sp(`Captured from the wire ${ex.captured} at ${ex.door} (the free answer; the signature comes on the paid call):`))}</p><pre>${esc(JSON.stringify(ex.request, null, 1))}</pre><pre>${esc(JSON.stringify((ex.response || {}).row || ex.response, null, 1))}</pre>
<h2>The door it describes</h2>${li([esc(sp('Issuerwire (MCP, Streamable HTTP): ')) + code(IW_MCP), esc(sp('Where the record lives: France Central Azure (Paris, France).'))])}`;
}
const STD_COPY = {
  kyp: { title: 'kyp-model.org — the KYP record standard', h1: 'The KYP record standard: what a get_issuer row is', desc: 'Clause-form standard for the issuer record served by get_issuer: the row, the fields, state, source page, read date, signature, delta, receipt, the duty map by market, versioning, what is not carried.' },
  iw: { title: 'issuerwire.org — the signed-row standard for the wire', h1: 'The signed-row standard: one row per filing, signed', desc: 'Clause-form standard for Issuerwire rows: one row per filing, the source page, type in English, title as filed, the Ed25519 signature, the delta, the markets carried, what is not carried.' }
};
function stdLlms(which, host, iw) {
  const sp = speller();
  return which === 'kyp'
    ? [`# ${host} — the KYP record standard`, sp('1. A get_issuer row: one Capital Markets Record (CMR) per listed issuer, keyed node/exchange/code; every field = value, source_url, read_by, state (sourced · filled · confirmed · conflict).'), '2. as_of = the sweep market date; field read dates kept separately.', '3. Signing: every record is signed (EdDSA, key allooloo-cmr-2026-10); keyring https://allooloo.ai/.well-known/jwks.json; receipts at https://cite-fact.ai/ (not issued yet).', '4. Delta: list_events_since(identifier, since).', '5. Versioning: integer version; nothing deleted.', '6. Not carried: prices, quotes, licensed market data, ratings, opinions, summaries.', `7. Door: ${GI_MCP}. Residency: each market in its own Azure region; node pages at https://<cc>-issuer.ai/.`, `8. Example on the record: get_record LSE:SHEL (captured ${KYP_CAPTURE.captured}).`].join('\n') + '\n'
    : [`# ${host} — the signed-row standard for Issuerwire`, '1. One row per filing: id, issuer_key, type, date, title, source page; never edited.', '2. Type in English from the register\'s code table; title exactly as filed in its original language; never machine-translated; identifiers language-free.', `3. Signature: Ed25519, kid amn-2026-10; keys ${IW_KEYS}; the full signed row on the paid call (x402).`, '4. Delta: get_delta(issuer, since).', `5. Markets carried at render: ${(iw.markets || []).join(', ')}.`, '6. Not carried: summaries, ratings, prices, opinions, translations.', `7. Door: ${IW_MCP}. Residency: France Central Azure (Paris, France).`].join('\n') + '\n';
}

// ---------- RADAR-02 (2026-10-23): one row per ORDER-034 zone for RADAR (the counts read at render, as the pages print them; the scanner level from zones-scan.json, as read)
export async function sovereignZones(live, scan) {
  const [iw, hk] = await Promise.all([iwFacts(), hkUp()]); const z = (scan && scan.zones) || {}; const lv = h => (z[h] && z[h].level != null) ? { level: z[h].level, passed: z[h].passed, scored: z[h].scored } : null;
  const rows = NODES.map(cc => { const v = nodeView(cc, live, iw, hk); const k = MKT[cc]; const h = `${cc}-issuer.ai`;
    return { zone: h, market: v.country, duty: `the record an agent cites under ${v.d.duty}`, doors: v.arming ? [] : [GI_MCP].concat(v.both ? [IW_MCP] : []),
      get_issuer: v.isLive ? { issuers: n_(v.n.records), disclosures: n_(v.n.events) } : null, issuerwire: v.both ? { issuers: n_((iw.issuers_by_market || {})[k]), signed_rows: n_((iw.filings_by_market || {})[k]) } : null,
      as_of: v.asOf || null, state: v.arming ? 'node arming' : (v.isLive ? 'live' : 'not live'), scanner: lv(h) }; });
  const recs = Object.values(live).filter(n => n.live).reduce((a, n) => a + n_(n.records), 0);
  rows.push({ zone: 'gb-issuer.ai', market: 'United Kingdom', duty: '301 → https://uk-issuer.ai/ (one hop, path kept)', doors: [], get_issuer: null, issuerwire: null, as_of: null, state: '301', scanner: null });
  rows.push({ zone: STD.kyp, market: 'every market on the roster', duty: 'the KYP record standard: what a get_issuer row is', doors: [GI_MCP], get_issuer: { issuers: recs }, issuerwire: null, as_of: today(), state: 'live', scanner: lv(STD.kyp) });
  rows.push({ zone: STD.iw, market: 'the markets Issuerwire carries', duty: 'the signed-row standard: one row per filing, signed', doors: [IW_MCP], get_issuer: null, issuerwire: iw.issuers_held != null ? { issuers: n_(iw.issuers_held), signed_rows: n_(iw.signed_rows != null ? iw.signed_rows : iw.filings_held) } : null, as_of: iw.store_as_of ? String(iw.store_as_of).slice(0, 10) : null, state: iw.issuers_held != null ? 'live' : 'facts not read', scanner: lv(STD.iw) });
  return { rows, iw, scan_read_at: (scan && scan.read_at) || null, scan_instrument: (scan && scan.instrument) || 'isitagentready.com', source: `list_nodes at ${GI_MCP} (read at render); ${IW_FACTS} (read at render); zones-scan.json (the ORDER-034 scan, as read)` };
}
export { iwFacts };

// ---------- the handler
const TGT = { kind: 'apex', mcp: GI_MCP, agent: GI_AGENT, openapi: 'https://mcp.getissuer.ai/openapi.json', mcpjson: 'https://mcp.getissuer.ai/mcp.json', name: 'getissuer' };
function respond(res, node, asOf, version) {
  const h = new Headers(res.headers); const add = headers({ node, as_of: asOf || today(), version: version || SURFACES_VERSION });
  for (const [k, v] of Object.entries(add)) if (!h.has(k)) h.set(k, v);
  h.delete('X-CMR-X402');   // no paid route on these zones
  h.set('X-CMR-Contact', 'mk@allooloo.ai');
  return new Response(res.body, { status: res.status, headers: h });
}
export async function handle34(request, env, url, c, liveNodes) {
  const host = c.host; const p = url.pathname.replace(/\/+$/, '') || '/';
  if (url.hostname !== host) return Response.redirect(`https://${host}${url.pathname}${url.search}`, 301);
  const node = c.kind === 'sov' ? `${c.cc}-cm-kg` : (c.which === 'kyp' ? 'kyp-model' : 'issuerwire');
  if (c.kind === 'sov' && p === '/mcp') { if (request.method === 'GET' || request.method === 'HEAD') return respond(new Response(null, { status: 302, headers: { location: GI_MCP } }), node); return respond(new Response(JSON.stringify({ error: 'post_to_the_door', door: GI_MCP }), { status: 405, headers: { 'content-type': 'application/json', allow: 'GET, HEAD' } }), node); }
  if (request.method !== 'GET' && request.method !== 'HEAD') return respond(new Response('Method Not Allowed', { status: 405, headers: { 'content-type': 'text/plain' } }), node);
  if (['/issuer.css', '/favicon.svg', '/favicon.ico', '/mark.svg', '/allooloo-logo.svg', '/allooloo-logo-dark.svg', '/icon-512.png', '/icon-192.png', '/apple-touch-icon.png'].includes(p)) { const a = await env.ASSETS.fetch(new Request(url.origin + p)); const r = respond(new Response(a.body, { status: a.status, headers: a.headers }), node); r.headers.set('cache-control', p === '/issuer.css' ? 'public, max-age=300' : 'public, max-age=86400'); return r; }
  if (p === '/robots.txt') return respond(new Response(ROBOTS(host), { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=86400' } }), node);
  if (p === '/.well-known/security.txt') return respond(new Response(SECURITY(host), { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=86400' } }), node);
  const [live, iw, hk] = await Promise.all([liveNodes(), iwFacts(), c.kind === 'sov' && c.cc === 'hk' ? hkUp() : Promise.resolve(true)]);
  const j = (o, ct) => respond(new Response(JSON.stringify(o, null, 1), { headers: { 'content-type': ct || 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*' } }), node);
  const t = (s, ct) => respond(new Response(s, { headers: { 'content-type': ct || 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=300' } }), node);
  const label = c.kind === 'sov' ? nodeTitle(c.cc) : STD_COPY[c.which].title; const desc = c.kind === 'sov' ? nodeDesc(c.cc, nodeView(c.cc, live, iw, hk)) : STD_COPY[c.which].desc;
  const LINK = AEO.linkHeader(host, TGT);
  if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return j(c.kind === 'sov' ? nodeCard(host, c.cc, live, iw, hk) : { name: label, description: desc, url: c.which === 'iw' ? IW_MCP : GI_MCP, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: c.which === 'iw' ? IW_MCP : GI_MCP, transport: 'JSONRPC' }], version: SURFACES_VERSION, protocolVersion: '0.3.0', provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], securitySchemes: {}, security: [], skills: [{ id: 'standard', name: 'Read the standard', description: desc, tags: ['standard', 'capital-markets'] }] });
  if (p === '/.well-known/api-catalog') return j(AEO.apiCatalog(host, TGT), 'application/linkset+json');
  if (p === '/.well-known/oauth-authorization-server' || p === '/.well-known/openid-configuration') return j(OAUTH.metadata());
  if (p === '/.well-known/oauth-protected-resource') return j(AEO.protectedResource(host, TGT));
  if (p === '/auth.md') return t(AEO.authMd(host, TGT), 'text/markdown; charset=utf-8');
  if (p === '/.well-known/mcp/server-card.json' || p === '/.well-known/mcp/server-cards.json' || p === '/.well-known/mcp.json') return j(AEO.mcpServerCard(host, TGT, live, label));
  if (p === '/.well-known/agent-skills/index.json' || p === '/.well-known/skills.json') return j(AEO.skillsIndex(host, TGT));
  const sk = p.match(/^\/\.well-known\/agent-skills\/([a-z-]+)\/SKILL\.md$/); if (sk) { const md = AEO.skillMd(host, TGT, sk[1]); return md ? t(md, 'text/markdown; charset=utf-8') : j({ error: 'not_found', status: 404 }); }
  if (p === '/.well-known/ai-catalog.json' || p === '/.well-known/ard.json') { const a = AEO.aiCatalog(host, TGT, label, desc); a.entries = a.entries.filter(e => !/:api:paid-call$/.test(e.identifier)); a.capabilities = (a.capabilities || []).filter(x => x.type !== 'x402'); return j(a, 'application/ard+json; charset=utf-8'); }
  const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/robots.txt', '/sitemap.xml'].concat(c.kind === 'sov' ? ['/mcp'] : []);
  if (p === '/sitemap.xml') return t(sitemap(host, ['/', '/llms.txt', '/facts.json']), 'application/xml; charset=utf-8');
  if (p === '/llms.txt') return t(c.kind === 'sov' ? nodeLlms(host, c.cc, live, iw, hk) : stdLlms(c.which, host, iw));
  if (p === '/facts.json') return j(c.kind === 'sov' ? nodeFacts(host, c.cc, live, iw, hk) : { domain: host, kind: 'standard', standard: STD_COPY[c.which].title, door: c.which === 'iw' ? IW_MCP : GI_MCP, clauses_at: `https://${host}/`, markets: c.which === 'iw' ? iw.markets || [] : NODES.map(x => NODE_DATA[x].country), operator: OPERATOR, contact: CONTACT, surface_version: SURFACES_VERSION, as_of: today() });
  if (p === '/') {
    let page;
    const sp = speller();   // one speller per page: the H1 is the first use
    if (c.kind === 'sov') { const h1 = sp(nodeH1(c.cc)); const b = nodeBody(host, c.cc, live, iw, hk, sp); page = shell({ kyp: 'https://getissuer.ai/#issuers', host, title: label, desc, h1, state: b.v.arming ? 'node arming' : (b.v.isLive ? 'live' : 'not live'), asOf: b.v.asOf, body: b.html, sp }); }
    else { const h1 = sp(STD_COPY[c.which].h1); page = shell({ host, title: label, desc, h1, state: 'standard', asOf: today(), body: stdBody(c.which, live, iw, sp), sp }); }
    const md = AEO.wantsMarkdown(request);
    // no-transform: the edge must not rewrite the page (it would inject the Web Analytics beacon — the page carries zero scripts)
    const r = respond(new Response(md ? AEO.toMarkdown(page, host) : page, { headers: { 'content-type': md ? 'text/markdown; charset=utf-8' : 'text/html; charset=utf-8', 'cache-control': 'public, max-age=60, must-revalidate, no-transform', Vary: 'Accept', Link: LINK } }), node);
    return r;
  }
  return respond(new Response(JSON.stringify({ error: 'not_found', status: 404, paths }), { status: 404, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } }), node);
}
