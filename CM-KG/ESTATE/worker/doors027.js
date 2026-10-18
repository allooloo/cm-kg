// ORDER-027 (CEO GO 2026-10-17) — the product doors on the estate Worker: six duty doors (agent-<duty>.ai), getissuer.ai, and the cite-fact / cite-dd quiet zones.
// Zones of record: START_ME_UP\Allooloo_New_Zones_2026-10-16.xlsx (ZONES tab). One canonical .ai per family; every other zone of the family 301s to it, path kept.
// Counts and dates are live from list_nodes on every render; nothing typed. Known gaps are carried verbatim from the node surfaces (nodes.js). Captures in duty-captures.js.
// Copy fence: each duty spelled out once before its short form; the line is "the record an agent cites under <duty>"; UK, never GB; no pricing; no Singapore duty page by ruling.
import { OPERATOR, CORPORATE, CONTACT, APEX, APEX_AGENT, SURFACES_VERSION, REGION_FULL, esc, int, today, num, table, scale, contactSection } from './chrome.js';
import { nodesTable, totals } from './products.js';
import CAP from './duty-captures.js';

const WORDS = ['none', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'];
const GI = 'https://getissuer.ai';
const SWAP = 'https://agent-swap.ai';
const GI_MCP = 'https://mcp.getissuer.ai/mcp';
const GI_AGENT = 'https://agent.getissuer.ai/.well-known/agent-card.json';

// ---------- the six duty families (memo §2; ZONES tab column D/E)
export const DUTIES = {
  kyp: { nodes: ['ca'], market: 'Canada', short: 'KYP', long: 'Know Your Product',
    title: 'Agentic KYP — the record an agent cites under Know Your Product (KYP) in Canada',
    h1: 'The record an agent cites under Know Your Product, for every issuer listed in Canada.',
    lead: v => `Know Your Product (KYP) asks a registered firm in Canada to understand each security it makes available before a client is offered it — the structure, the features, the risks, and the company behind the paper — and to keep that understanding current while the security stays on the shelf. agent-kyp.ai is where a dealer's agent finds the issuer half of that file: ${v.records} issuers across the Toronto Stock Exchange, TSX Venture, the Canadian Securities Exchange and Cboe Canada, each field carrying its source and its read date, stored and served in Toronto.`,
    duty: ['Instrument: National Instrument 31-103, section 13.2.1 (know your product), in force since 31 December 2021 under the Client Focused Reforms.', 'Who carries it: registered dealers and advisers in every province and territory, including the investment dealers that CIRO oversees.', 'What it asks: reasonable steps to assess and understand each security made available, a watch for significant changes to it, and a file that shows what the firm relied on.', 'What stays with the firm: the shelf decision, the suitability determination for each client, and the client file itself. The record is an input to KYP; it is not the KYP decision.'],
    answers: ['Is this the issuer the shelf thinks it is: legal name as filed, ticker on its own venue, ISIN, LEI and the LEI registration status.', 'Who stands behind the paper: jurisdiction of incorporation from the GLEIF legal-jurisdiction field, the auditor where it is reported, the newswire the issuer uses.', 'What moved since the shelf last looked: material change reports, results, AGM record dates, halts and bulletins over the trailing twelve months, each dated and linked to the wire or the exchange page.', 'What could not be read: a blank field carries its reason in place, so a reviewer sees the gap rather than a fill.'],
    regulator: 'the Canadian Securities Administrators and CIRO' },
  prod: { nodes: ['uk'], market: 'UK', short: 'PROD / Consumer Duty', long: 'the Product Intervention and Product Governance Sourcebook (PROD) and the Consumer Duty',
    title: 'Agentic PROD — the record an agent cites under PROD and the Consumer Duty in the UK',
    h1: 'The record an agent cites under the FCA product governance rules and the Consumer Duty, for every issuer listed in the UK.',
    lead: v => `In the UK a firm that distributes a financial instrument works under two sets of FCA rules at once: the Product Intervention and Product Governance Sourcebook (PROD), which wants the distributor to understand the instrument and its target market, and the Consumer Duty, which wants retail customers to get products that meet their needs and information they can understand. agent-prod.ai hands an agent the issuer facts both rules lean on — ${v.records} companies on the London Stock Exchange Main Market, AIM and Aquis, sourced from Companies House, the RNS trail and the LEI register, stored and served in London.`,
    duty: ['PROD 3: the product governance requirements for firms that manufacture or distribute MiFID financial instruments; a distributor obtains the information it needs to understand each instrument and identifies the target market for it.', 'Consumer Duty: Principle 12 and PRIN 2A of the FCA Handbook, in force for open products since 31 July 2023; the products and services outcome and the consumer understanding outcome apply to retail business.', 'Who carries them: brokers, wealth managers and platforms authorised by the FCA, and the firms that manufacture what those platforms list.', 'What stays with the firm: the target market assessment, the fair value judgement and the customer communications. PROD / Consumer Duty decisions are the firm\'s; the record is what the agent reads first.'],
    answers: ['Which venue and segment the issuer sits on: Main Market, AIM or Aquis, with the LSE trading segment code where the issuer profile gives one.', 'Who the issuer is at Companies House: company number, filing history, previous names, and the LEI that binds them.', 'What the issuer has told the market: the RNS and wire trail for twelve months, typed — results, director dealings, major holdings, AGM notices — each with its announcement URL.', 'Where a source refused the machine: the gap line names the source and the refusal, so the file says what was not read.'],
    regulator: 'the Financial Conduct Authority (FCA)' },
  mifid: { nodes: ['de', 'fr', 'nl'], market: 'Germany · France · Netherlands', short: 'MiFID II product governance', long: 'the product governance rules of the second Markets in Financial Instruments Directive (MiFID II)',
    title: 'Agentic MiFID — the record an agent cites under MiFID II product governance in Germany, France and the Netherlands',
    h1: 'The record an agent cites under MiFID II product governance, for issuers listed in Frankfurt, Paris and Amsterdam.',
    lead: v => `The product governance rules of the second Markets in Financial Instruments Directive (MiFID II) reach every investment firm in the European Union that offers an instrument to a client: the distributor holds adequate information on the instrument and understands it before distribution, and reviews it while it is distributed. One directive, three supervisors, three registers. agent-mifid.ai sends an agent to three sovereign nodes — Xetra and Eurex in Frankfurt, Euronext Paris, Growth and Access in Paris, Euronext Amsterdam in Amsterdam — ${v.records} records in all, each served only from its own country.`,
    duty: ['Directive 2014/65/EU, Articles 16(3) and 24(2), with Commission Delegated Directive (EU) 2017/593, Articles 9 and 10; ESMA\'s guidelines on MiFID II product governance requirements set out the method.', 'Germany: Wertpapierhandelsgesetz section 80(9) to (13) and BaFin\'s MaComp, module BT 5 (Produktüberwachung).', 'France: the Code monétaire et financier and the AMF General Regulation, supervised by the Autorité des marchés financiers.', 'Netherlands: the Wet op het financieel toezicht, supervised by the Autoriteit Financiële Markten.', 'What stays with the firm: the target market, the distribution strategy and the periodic review. MiFID II product governance is the distributor\'s file; the record fills the issuer column of it.'],
    answers: ['The issuer behind each ISIN: legal name, LEI and status, the venue and segment, and in Germany the Eurex reference link where the share has a listed derivative.', 'The national register line: Handelsregister court and number in Germany, the SIREN in France, the KVK number in the Netherlands, each only where a source of record carries it.', 'The regulatory trail: AMF BDIF filings in France, AFM notifications in the Netherlands, EQS ad hoc and directors\' dealings in Germany, twelve months, dated and linked.', 'One identifier, one country: a dual listing resolves to two records, each in its own jurisdiction, never merged across a border.'],
    regulator: 'BaFin, the AMF and the AFM under ESMA' },
  finsa: { nodes: ['ch'], market: 'Switzerland', short: 'FinSA', long: 'the Financial Services Act',
    title: 'Agentic FinSA — the record an agent cites under the Financial Services Act (FinSA) in Switzerland',
    h1: 'The record an agent cites under the Financial Services Act, for every issuer listed on SIX and BX Swiss.',
    lead: v => `Switzerland wrote its own rule book for the point of sale: the Financial Services Act (FinSA, in German FIDLEG) tells a financial service provider what it must know and say about an instrument before it recommends or sells it — the risks, the costs, and for retail clients the key information document. agent-finsa.ai is the issuer side of that: ${v.records} Swiss listings, joined to the Zefix federal register for the company UID and to GLEIF for the LEI, kept in Zurich and answered from Zurich.`,
    duty: ['Act: Federal Act on Financial Services of 15 June 2018, in force since 1 January 2020; FINMA supervises the providers, the review bodies check prospectuses.', 'Article 8: the provider informs the client about the financial instrument, including its risks and costs.', 'Articles 10 to 14: the appropriateness and suitability checks, and when they may be skipped.', 'Articles 58 to 63: the key information document for instruments offered to retail clients; shares are outside it, the issuer facts under Article 8 are not.', 'What stays with the provider: the client classification, the check itself and the documentation of advice. FinSA duties sit with the provider; the record supplies what the provider reads about the issuer.'],
    answers: ['Which company issued the listing: legal name, SIX or BX Swiss symbol, ISIN, LEI, and the Zefix UID of the legal entity.', 'What the commercial register published: SHAB notices of the register rubric — board changes, capital changes, seat moves — dated and linked.', 'What the issuer announced: ad hoc and wire releases over twelve months, dated, with the publication URL.', 'Where the name rule held back a match: ambiguous hits are counted in the gap line rather than attached to the wrong company.'],
    regulator: 'the Swiss Financial Market Supervisory Authority (FINMA)' },
  ddo: { nodes: ['au'], market: 'Australia', short: 'DDO', long: 'the Design and Distribution Obligations',
    title: 'Agentic DDO — the record an agent cites under the Design and Distribution Obligations (DDO) in Australia',
    h1: 'The record an agent cites under the Design and Distribution Obligations, for every issuer listed in Australia.',
    lead: v => `The Design and Distribution Obligations (DDO) make an Australian issuer decide who a product is for and make every distributor stay inside that decision. An agent working the distribution side reads the issuer before it reads the target market determination. agent-ddo.ai gives it that issuer: ${v.records} companies on ASX, NSX and the Australian listings of TMX, joined to the ASIC company register for the ACN, ABN, type and status, stored and served in Sydney.`,
    duty: ['Statute: Part 7.8A of the Corporations Act 2001, in force since 5 October 2021; ASIC Regulatory Guide 274 sets out how ASIC reads it.', 'Issuers: make a target market determination for each product in scope and review it (sections 994B and 994C).', 'Distributors: take reasonable steps so that retail distribution is consistent with the determination (section 994E), and report significant dealings outside it.', 'Scope: fully paid ordinary shares are outside DDO; hybrids, notes, listed options and exchange-traded products are inside, and the company that issues them is the same company the record carries.', 'What stays with the firm: the determination, the distribution conditions and the dealing reports. DDO judgements are the issuer\'s and the distributor\'s; the record is the common ground both read.'],
    answers: ['The listed entity: ASX code, legal name, ACN and ABN from the ASIC dataset, company type and registration status.', 'The announcement trail: ASX company announcements over twelve months — results, appendix filings, capital raisings, director interests — each with its ASX announcement URL.', 'The register trail: ASIC status changes where the company carries an ACN.', 'The missing pieces, counted: address fields the bulk register does not carry, and venues with no machine-readable list, are written into the gap line.'],
    regulator: 'the Australian Securities and Investments Commission (ASIC)' },
  regbi: { nodes: ['us'], market: 'United States', short: 'Reg BI', long: 'Regulation Best Interest',
    title: 'Agentic Reg BI — the record an agent cites under Regulation Best Interest (Reg BI) in the United States',
    h1: 'The record an agent cites under Regulation Best Interest, for every issuer listed on NYSE, Nasdaq and Cboe.',
    lead: v => `Regulation Best Interest (Reg BI) asks a broker-dealer that recommends a security to a retail customer to act in that customer's best interest, and its care obligation starts before any customer is in view: the firm understands the security's risks, rewards and costs. agent-regbi.ai points an agent at the issuer half of that understanding — ${v.records} exchange-listed filers, built from EDGAR alone, stored and served in Virginia.`,
    duty: ['Rule: 17 CFR 240.15l-1 under the Securities Exchange Act of 1934, adopted by the SEC in 2019, binding on broker-dealers since 30 June 2020; FINRA examines member firms against it.', 'Care obligation: reasonable diligence, care and skill to understand the potential risks, rewards and costs of a recommendation, then a reasonable basis to believe it is in this customer\'s best interest.', 'The other three obligations — disclosure, conflict of interest, and the written policies — sit beside care and are the firm\'s own.', 'What stays with the broker-dealer: the recommendation, the customer profile and the record of both. Reg BI is the firm\'s obligation; the record supplies what an agent reads about the issuer.'],
    answers: ['The filer behind the ticker: legal name, CIK, exchange and ticker from the SEC list of exchange-listed companies, LEI where a GLEIF record in a US jurisdiction matches exactly.', 'What the issuer filed: the EDGAR filings index for twelve months — 8-K items, 10-K, 10-Q, proxy, insider and ownership forms — each dated with its accession link.', 'Who audits it: the auditor name and location from the cover-page tags of the latest annual report, where the filing carries them.', 'Several classes, one filer: each share class resolves to its own ticker on the same CIK, and the record says so.'],
    regulator: 'the Securities and Exchange Commission and FINRA' }
};

export function classify27(h) {
  let m;
  if ((m = h.match(/^agent-?(kyp|prod|mifid|finsa|ddo|regbi)\.(ai|com|co\.uk)$/)) && DUTIES[m[1]]) { const canon = `agent-${m[1]}.ai`; return h === canon ? { kind: 'duty', fam: m[1] } : { kind: 'redirect', canonical: `https://${canon}`, status: 301 }; }
  if (/^get-?issuer\.(ai|com|io|org|co\.uk)$/.test(h)) return h === 'getissuer.ai' ? { kind: 'getissuer' } : { kind: 'redirect', canonical: GI, status: 301 };
  if ((m = h.match(/^cite-(fact|dd)\.(ai|com)$/))) return m[2] === 'ai' ? { kind: 'cite', which: m[1] } : { kind: 'redirect', canonical: `https://cite-${m[1]}.ai`, status: 301 };
  if (/^agent-swap\.(ai|com|io|org|co\.uk)$/.test(h)) return h === 'agent-swap.ai' ? { kind: 'swap' } : { kind: 'redirect', canonical: SWAP, status: 301 };   // ORDER-032 C.4
  return null;
}
export const isNew = c => c && (c.kind === 'duty' || c.kind === 'getissuer' || c.kind === 'cite' || c.kind === 'swap');

const nv = (live, cc) => { const n = live[`${cc}-cm-kg`] || {}; return { live: !!n.live, records: n.live ? int(n.records) : '', events: n.live ? int(n.events) : '', as_of: n.live ? (n.as_of || '') : '' }; };
function famVals(live, fam) {
  const ns = DUTIES[fam].nodes.map(cc => nv(live, cc));
  return { records: int(ns.reduce((a, x) => a + (Number(x.records) || 0), 0)), events: int(ns.reduce((a, x) => a + (Number(x.events) || 0), 0)), as_of: ns.map(x => x.as_of).sort().slice(-1)[0] || '', live: ns.every(x => x.live) };
}

// ---------- AEO target, label and description for the shared kit paths in surfaces.js
export function target27(c) {
  if (c.kind === 'duty') {
    const d = DUTIES[c.fam];
    if (d.nodes.length === 1) { const cc = d.nodes[0]; return { kind: 'node', mcp: `https://mcp.${cc}-cm-kg.ai/mcp`, agent: `https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json`, openapi: `https://mcp.${cc}-cm-kg.ai/openapi.json`, mcpjson: `https://mcp.${cc}-cm-kg.ai/mcp.json`, name: `${cc}-cm-kg door` }; }
    return { kind: 'apex', mcp: `${APEX}/mcp`, agent: `${APEX_AGENT}/.well-known/agent-card.json`, openapi: `${APEX}/openapi.json`, mcpjson: `${APEX}/mcp.json`, name: 'Capital Markets Knowledge Graph — apex router' };
  }
  if (c.kind === 'getissuer') return { kind: 'apex', mcp: GI_MCP, agent: GI_AGENT, openapi: 'https://mcp.getissuer.ai/openapi.json', mcpjson: 'https://mcp.getissuer.ai/mcp.json', name: 'getissuer' };
  return { kind: 'apex', mcp: `${APEX}/mcp`, agent: `${APEX_AGENT}/.well-known/agent-card.json`, openapi: `${APEX}/openapi.json`, mcpjson: `${APEX}/mcp.json`, name: 'Capital Markets Knowledge Graph — apex router' };
}
const CITE = {
  fact: { title: 'Agentic cite-fact — the receipt for an answer an agent was served', h1: 'cite-fact — the receipt for a served answer.', what: 'A receipt is a permanent address on cite-fact.ai that resolves to exactly what an Allooloo door served: the record or event payload, the node, the as-of, the serving time, the signing key and the source page of each field. A second call never changes the first receipt.', state: 'Receipts are not issued yet and none is stubbed. This host serves its machine kit only.' },
  dd: { title: 'Agentic cite-DD — the due-diligence file, every fact receipted', h1: 'cite-DD — the due-diligence file, every fact receipted.', what: 'cite-DD is the due diligence (DD) file for one issuer: a bundle of cite-fact receipts, gathered through the duty doors, each fact traceable to the answer that served it.', state: 'No file is issued yet and none is stubbed. This host serves its machine kit only.' }
};
export function label27(c) { if (c.kind === 'swap') return SWAP_COPY.title; return c.kind === 'duty' ? DUTIES[c.fam].title : c.kind === 'getissuer' ? 'Agentic getissuer — the issuer record, for AI agents' : CITE[c.which].title; }
export function desc27(c, live) {
  if (c.kind === 'swap') return SWAP_COPY.desc;
  if (c.kind === 'duty') { const d = DUTIES[c.fam]; const v = famVals(live, c.fam); return `The record an agent cites under ${d.long} (${d.short}), ${d.market}: ${v.records} issuer records and ${v.events} dated disclosure events, live from list_nodes, served in-country.`; }
  if (c.kind === 'getissuer') { const t = totals({ live }); return `getissuer — the issuer record, for AI agents: ${int(t.records)} issuers, ${int(t.events)} events, ${WORDS[t.nodes] || t.nodes} markets, one MCP door at ${GI_MCP}.`; }
  return `${CITE[c.which].h1} ${CITE[c.which].state}`;
}

// ---------- duty door page (node-surface template: numbered sections, live counts, verbatim gaps, kit, contact)
function captureBlock(fam) {
  const k = CAP[fam]; if (!k) return '<p>No capture.</p>';
  const req1 = { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'resolve_issuer', arguments: { identifier: k.identifier } } };
  const req2 = { jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name: 'list_events_since', arguments: { identifier: k.resolve.cmr, since: k.events.since, limit: 3 } } };
  return `<p>Captured from <code>https://mcp.${esc(k.node)}.ai/mcp</code> on ${esc(k.captured)}, verbatim.</p><pre>${esc(JSON.stringify(req1))}</pre><pre>${esc(JSON.stringify(k.resolve, null, 1))}</pre><pre>${esc(JSON.stringify(req2))}</pre><pre>${esc(JSON.stringify(k.events, null, 1))}</pre>`;
}
export function dutyBody(ctx, host, fam) {
  const d = DUTIES[fam]; const v = famVals(ctx.live, fam); const N = ctx.nodes;
  const doors = d.nodes.map(cc => { const x = nv(ctx.live, cc); return [`<code class="nw">${cc}-cm-kg</code>`, esc(N[cc].country), esc(REGION_FULL[cc]), `<code>https://mcp.${cc}-cm-kg.ai/mcp</code>`, `<a href="https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json">agent.${cc}-cm-kg.ai</a>`, `<span class="n">${esc(x.records || '—')}</span>`, `<span class="n">${esc(x.events || '—')}</span>`, `<span class="nw">${esc(x.as_of)}</span>`]; });
  const gaps = d.nodes.map(cc => `<p><strong>${esc(N[cc].country)} (${cc}-cm-kg).</strong> ${esc(N[cc].gaps)} <span class="muted">(carried from: ${esc(N[cc].gapsFrom)})</span></p>`).join('');
  const tiles = scale([[esc(v.records), 'issuer records', 'list_nodes', 'issuer'], [esc(v.events), 'dated disclosure events', 'list_nodes', 'record'], [esc(v.as_of || ''), 'sweep market date', 'list_nodes', 'pulse']]);
  return `${tiles}<p class="lead">${esc(d.lead(v))}</p>
<h2>1 The duty, in ${esc(d.market)}</h2>${num(1, d.duty.map(esc))}
<h2>2 What the record answers under ${esc(d.short)}</h2>${num(2, d.answers.map(esc).concat([`Supervised by ${esc(d.regulator)}; the record is public-record only — no prices, quotes or licensed market data, nothing inferred, blank stays blank.`]))}
<h2>3 The door it calls</h2><div class="wrap">${table(['node', 'market', 'region', 'MCP door', 'Agent Card', 'records', 'events', 'as of'], doors)}</div><p class="src">source: list_nodes at ${esc(APEX)}/mcp, read at render</p>${num(3, ['Transport: MCP Streamable HTTP, JSON-RPC 2.0, stateless, no authentication.', 'Tools: <code>resolve_issuer</code> · <code>get_record</code> · <code>list_aliases</code> · <code>list_events_since</code> · <code>list_nodes</code>.', `Every identifier is answered by its own node; the apex <code>${esc(APEX)}/mcp</code> and <a href="${GI}/">getissuer.ai</a> route any identifier there. No record body leaves its country; no fallback.`])}
<h2>4 A real wire capture from ${esc(d.market)}</h2>${captureBlock(fam)}
<h2>5 Known gaps</h2>${gaps}
<h2>6 Machine kit</h2>${num(6, ['<a href="/llms.txt"><code>/llms.txt</code></a> · <a href="/facts.json"><code>/facts.json</code></a> · <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a> · <a href="/.well-known/security.txt"><code>/.well-known/security.txt</code></a> · <a href="/sitemap.xml"><code>/sitemap.xml</code></a> · <a href="/robots.txt"><code>/robots.txt</code></a> · <a href="/mcp.json"><code>/mcp.json</code></a> · <a href="/openapi.json"><code>/openapi.json</code></a>', 'Zone family: ' + esc(familyZones(fam)) + ' forward here, path kept.'])}${contactSection(host)}`;
}
const FAMZ = { kyp: ['agent-kyp.com', 'agentkyp.ai', 'agentkyp.com'], prod: ['agent-prod.com', 'agentprod.ai', 'agent-prod.co.uk', 'agentprod.co.uk'], mifid: ['agent-mifid.com', 'agentmifid.ai', 'agentmifid.com'], finsa: ['agent-finsa.com', 'agentfinsa.ai', 'agentfinsa.com'], ddo: ['agent-ddo.com', 'agentddo.ai', 'agentddo.com'], regbi: ['agent-regbi.com', 'agentregbi.ai', 'agentregbi.com'] };
const familyZones = fam => FAMZ[fam].join(', ');
export function dutyFacts(host, fam, live) {
  const d = DUTIES[fam]; const v = famVals(live, fam);
  return { domain: host, kind: 'duty door', duty: `${d.long} (${d.short})`, market: d.market, line: `the record an agent cites under ${d.long}`, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: v.as_of || today(), surface_version: SURFACES_VERSION, source: 'public-record',
    nodes: d.nodes.map(cc => { const x = nv(live, cc); return { node: `${cc}-cm-kg`, live: x.live, records: x.live ? Number(x.records) : null, events: x.live ? Number(x.events) : null, as_of: x.as_of || null, mcp_url: `https://mcp.${cc}-cm-kg.ai/mcp`, agent_card: `https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json`, region: REGION_FULL[cc] }; }),
    issuer_records: Number(v.records) || null, disclosure_events: Number(v.events) || null, apex: `${APEX}/mcp`, getissuer: `${GI}/`, forwards_here: FAMZ[fam], counts_from: 'list_nodes (live on each render)',
    machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/mcp.json', '/openapi.json'] };
}
export function dutyLlms(host, fam, live) {
  const d = DUTIES[fam]; const v = famVals(live, fam);
  return [`# ${host} — ${d.title}`, `1. What this host is: the duty door for ${d.long} (${d.short}) in ${d.market} — the record an agent cites under ${d.long}. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`,
    `2. Counts at render (list_nodes): ${v.records} issuer records, ${v.events} dated disclosure events, sweep market date ${v.as_of || 'none'}.`,
    `3. Door(s): ${d.nodes.map(cc => `https://mcp.${cc}-cm-kg.ai/mcp (Agent Card https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json)`).join('; ')}. MCP Streamable HTTP, no auth. Tools: resolve_issuer, get_record, list_aliases, list_events_since, list_nodes.`,
    `4. Any identifier from any market: ${APEX}/mcp or ${GI_MCP} (same router).`, `5. Residency: ${d.nodes.map(cc => REGION_FULL[cc]).join('; ')}; no record body leaves its country; no fallback.`,
    `6. Known gaps: ${d.nodes.map(cc => `${cc}-cm-kg — see https://${cc}-cm-kg.ai/ section 5`).join('; ')}.`, `7. Forwards here (301, path kept): ${FAMZ[fam].join(', ')}.`,
    '8. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt /mcp.json /openapi.json', '9. Rules: public-record only; no prices; blank stays blank; counts are live, never typed; the duty decision stays with the firm.', `10. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
}

// ---------- getissuer.ai (company template, head block of record)
export function getissuerBody(ctx, host) {
  const t = totals(ctx); const markets = WORDS[t.nodes] || String(t.nodes);
  const install = JSON.stringify({ mcpServers: { getissuer: { type: 'http', url: GI_MCP } } }, null, 2);
  const duty = Object.keys(DUTIES).map(k => `<a href="https://agent-${k}.ai/">agent-${k}.ai</a> (${esc(DUTIES[k].short)}, ${esc(DUTIES[k].market)})`).join(' · ');
  return `<p class="lead"><strong>${esc(int(t.records))} issuers · ${esc(int(t.events))} events · ${esc(markets)} markets</strong> <span class="muted">— live from list_nodes, sweep market date ${esc(t.last)}</span></p>
<h2>1 Four verbs, one record</h2>${num(1, [`<strong>getissuer</strong> gets the record: one call with a ticker, ISIN, LEI or legal name returns the issuer and the node that holds it.`, `<strong>The duty doors</strong> say which record for which market: ${duty}.`, '<strong>cite-fact</strong> is the proof: <a href="https://cite-fact.ai/">cite-fact.ai</a>.', '<strong>cite-DD</strong> is the diligence file: <a href="https://cite-dd.ai/">cite-dd.ai</a>.'])}
<h2>2 Install</h2><p>Any MCP client that speaks Streamable HTTP:</p><pre>${esc(install)}</pre><p>Claude Code:</p><pre>claude mcp add --transport http getissuer ${esc(GI_MCP)}</pre>${num(2, [`Door: <code>${esc(GI_MCP)}</code> — the same router as <code>${esc(APEX)}/mcp</code>: same five tools, same index, no second store.`, `Agent Card (A2A): <a href="${GI_AGENT}"><code>${esc(GI_AGENT)}</code></a>.`, 'Tools: <code>resolve_issuer</code> · <code>get_record</code> · <code>list_aliases</code> · <code>list_events_since</code> · <code>list_nodes</code>. Read-only, no authentication.', 'Registry entry: <code>registry.modelcontextprotocol.io · io.github.allooloo/cm-kg</code>.'])}
<h2>3 Where each record lives</h2>${nodesTable(ctx)}${num(3, ['The router holds an index only and forwards each call to the node of the listing; the record is stored and served in its own country; no fallback across borders.', 'Public-record only: no prices, quotes or licensed market data; every field carries its source and read date; blank stays blank.'])}
<h2>4 Machine kit</h2>${num(4, ['<a href="/llms.txt"><code>/llms.txt</code></a> · <a href="/facts.json"><code>/facts.json</code></a> · <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a> · <a href="/.well-known/security.txt"><code>/.well-known/security.txt</code></a> · <a href="/sitemap.xml"><code>/sitemap.xml</code></a> · <a href="/robots.txt"><code>/robots.txt</code></a> · <a href="/mcp.json"><code>/mcp.json</code></a> · <a href="/openapi.json"><code>/openapi.json</code></a>', 'Forwards here (301, path kept): getissuer.com, getissuer.io, getissuer.co.uk, get-issuer.ai, get-issuer.com, get-issuer.io, get-issuer.org, get-issuer.co.uk.'])}${contactSection(host)}`;
}
export function getissuerFacts(host, live) {
  const t = totals({ live });
  return { domain: host, kind: 'product root', product: 'getissuer', head: 'getissuer — the issuer record, for AI agents', operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: t.last || today(), surface_version: SURFACES_VERSION, source: 'public-record', issuers: t.records, events: t.events, markets: t.nodes, counts_from: 'list_nodes (live on each render)', mcp_url: GI_MCP, alias_of: `${APEX}/mcp`, agent_card: GI_AGENT,
    verbs: ['getissuer gets the record', 'duty doors say which record for which market', 'cite-fact is the proof', 'cite-DD the diligence file'], duty_doors: Object.keys(DUTIES).map(k => `https://agent-${k}.ai/`), cite: ['https://cite-fact.ai/', 'https://cite-dd.ai/'], machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/mcp.json', '/openapi.json'] };
}
export function getissuerLlms(host, live) {
  const t = totals({ live });
  return [`# ${host} — getissuer, the issuer record for AI agents`, `1. Scope at render (list_nodes): ${t.records} issuers, ${t.events} dated disclosure events, ${t.nodes} markets live; sweep market date ${t.last}.`, `2. Door: ${GI_MCP} (MCP Streamable HTTP, no auth) — alias of ${APEX}/mcp: same router, same five tools, same index. Agent Card: ${GI_AGENT}.`, '3. Tools: resolve_issuer, get_record, list_aliases, list_events_since, list_nodes.', `4. Install: {"mcpServers":{"getissuer":{"type":"http","url":"${GI_MCP}"}}} · claude mcp add --transport http getissuer ${GI_MCP}`, '5. Four verbs: getissuer gets the record · duty doors say which record for which market (' + Object.keys(DUTIES).map(k => `agent-${k}.ai`).join(', ') + ') · cite-fact is the proof (cite-fact.ai) · cite-DD the diligence file (cite-dd.ai).', `6. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`, '7. Rules: public-record only; no prices; blank stays blank; records served in their own country; counts live, never typed.', '8. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt /mcp.json /openapi.json', `9. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
}

// ---------- cite-fact.ai / cite-dd.ai: quiet-zone kit (ORDER-019 shape); pages and the receipt itself are ORDER-028
export function citeBody(host, which) { const q = CITE[which]; return `<p class="lead">${esc(q.what)}</p><p><strong>${esc(q.state)}</strong> Operator: ${esc(OPERATOR)}. Records today are served by the doors of the Capital Markets Knowledge Graph — <a href="${GI}/">getissuer.ai</a> and <code>${esc(APEX)}/mcp</code>.</p>${contactSection(host)}`; }
export function citeFacts(host, which, live) { const t = totals({ live }); return { domain: host, kind: 'quiet zone', product: which === 'fact' ? 'cite-fact' : 'cite-DD', what: CITE[which].what, state: CITE[which].state, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: today(), surface_version: SURFACES_VERSION, estate: { issuers: t.records, events: t.events, markets: t.nodes, counts_from: 'list_nodes (live on each render)' }, records_served_by: [`${GI_MCP}`, `${APEX}/mcp`], forwards_here: [`cite-${which}.com`], machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'] }; }
export function citeLlms(host, which) { const q = CITE[which]; return [`# ${host} — ${q.title}`, `1. ${q.what}`, `2. State: ${q.state}`, `3. Records are served today by ${GI_MCP} and ${APEX}/mcp.`, `4. Operator: ${OPERATOR}. Contact: ${CONTACT}. cite-${which}.com forwards here.`, '5. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt', `6. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n'; }

// ---------- page metadata for surfaces.js
export function pageArgs27(c, ctx, host) {
  if (c.kind === 'swap') { const d = ctx.swap || { rows: [], swap_log: [], at: new Date().toISOString() }; return { title: SWAP_COPY.title, h1: SWAP_COPY.h1, state: 'live', asOf: d.at.slice(0, 10), body: swapBody(d, host), meta: { node: 'estate', as_of: d.at.slice(0, 10) } }; }
  if (c.kind === 'duty') { const d = DUTIES[c.fam]; const v = famVals(ctx.live, c.fam); return { title: d.title, h1: d.h1, state: v.live ? 'live' : 'not live', asOf: v.as_of || today(), body: dutyBody(ctx, host, c.fam), meta: { node: d.nodes.length === 1 ? `${d.nodes[0]}-cm-kg` : d.nodes.map(x => `${x}-cm-kg`).join(','), as_of: v.as_of || today() } }; }
  if (c.kind === 'getissuer') { const t = totals(ctx); return { title: label27(c), h1: 'getissuer — the issuer record, for AI agents', state: 'live', asOf: t.last || today(), body: getissuerBody(ctx, host), meta: { node: 'apex', as_of: t.last || today() } }; }
  const q = CITE[c.which]; return { title: q.title, h1: q.h1, state: 'record', asOf: today(), body: citeBody(host, c.which), meta: { node: 'estate', as_of: today() } };
}
export function facts27(c, host, live, ctx) { if (c.kind === 'swap') return swapFacts((ctx && ctx.swap) || { rows: [], swap_log: [], at: new Date().toISOString() }, host); return c.kind === 'duty' ? dutyFacts(host, c.fam, live) : c.kind === 'getissuer' ? getissuerFacts(host, live) : citeFacts(host, c.which, live); }
export function llms27(c, host, live, ctx) { if (c.kind === 'swap') return swapLlms((ctx && ctx.swap) || { rows: [], swap_log: [], at: new Date().toISOString() }, host); return c.kind === 'duty' ? dutyLlms(host, c.fam, live) : c.kind === 'getissuer' ? getissuerLlms(host, live) : citeLlms(host, c.which); }
export function paths27(c) { if (c.kind === 'swap') return ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt']; return (c.kind === 'getissuer' ? ['/', '/docs'] : ['/']).concat(['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt']).concat(c.kind === 'cite' ? [] : ['/mcp.json', '/openapi.json']); }
export function pointer27(c, kind) { const t = target27(c); return { pointer: true, [kind]: kind === 'mcp' ? t.mcpjson : t.openapi, door: t.mcp, note: 'this host is a product surface; the door descriptor is served by the door' }; }

// ---------- ORDER-032 C.4 — agent-swap.ai: which cloud serves each market's record now, its last swap, and when the record last reached the second cloud.
// Live at render: the serving cloud is the X-Allooloo-Origin header each node door returns; swaps and ark writes come from the published logs
// /swap/swaps.json (written by the swap rail) and /swap/ark.json (written at the sweep close). Sourced or blank: a door that does not answer reads "did not answer".
const SWAP_NODES = [['nl', 'Netherlands'], ['ch', 'Switzerland'], ['fr', 'France'], ['de', 'Germany'], ['sg', 'Singapore'], ['au', 'Australia'], ['uk', 'United Kingdom'], ['ca', 'Canada'], ['jp', 'Japan'], ['kr', 'South Korea'], ['us', 'United States']];
const CLOUD = { azure: 'Azure', aws: 'AWS' };
export const SWAP_COPY = {
  title: 'agent-swap — the record keeps answering',
  h1: 'agent-swap — the record keeps answering',
  desc: 'For each of eleven markets: the cloud serving the issuer record now, the last swap, and the last night the record reached its second cloud. Live at render.',
  lead: "Every market's issuer record is served from its own country and reaches a second cloud the same night. When the serving cloud stops answering, the same record answers from the other one: same address, same tools, same record."
};
async function assetJson(env, url, path) { try { const r = await env.ASSETS.fetch(new URL(path, url)); return r.ok ? await r.json() : null; } catch (e) { return null; } }
export async function swapData(env, url) {
  const [swaps, ark] = await Promise.all([assetJson(env, url, '/swap/swaps.json'), assetJson(env, url, '/swap/ark.json')]);
  const log = ((swaps && swaps.swaps) || []).slice().sort((a, b) => (a.at < b.at ? -1 : 1));
  const rows = await Promise.all(SWAP_NODES.map(async ([cc, country]) => {
    const node = `${cc}-cm-kg`; let origin = null, asOf = null;
    try {
      const ac = new AbortController(); const t = setTimeout(() => ac.abort(), 4000);
      const r = await fetch(`https://mcp.${node}.ai/facts.json`, { signal: ac.signal, cf: { cacheTtl: 0 } }); clearTimeout(t);
      if (r.ok) { origin = (r.headers.get('x-allooloo-origin') || '').toLowerCase() || null; asOf = r.headers.get('x-cmr-as-of') || null; }
    } catch (e) { }
    const sw = log.filter(x => x.node === node); const a = ((ark && ark.nodes) || {})[node] || null;
    return { node, country, serving: origin, as_of: asOf, swaps: sw.length, last_swap: sw.length ? sw[sw.length - 1] : null, last_ark_write: a ? a.last_write : null };
  }));
  return { at: new Date().toISOString(), rows, swap_log: log };
}
function swapBody(d, host) {
  const rows = d.rows.map(r => [`<code class="nw">${esc(r.node)}</code>`, esc(r.country), r.serving ? esc(CLOUD[r.serving] || r.serving) : 'did not answer', r.as_of ? esc(r.as_of) : '',
    r.last_swap ? `${esc(r.last_swap.at.slice(0, 10))} (to ${esc(CLOUD[r.last_swap.to] || r.last_swap.to)})` : 'none yet', r.swaps ? int(r.swaps) : 'none yet', r.last_ark_write ? esc(r.last_ark_write) : 'not yet']);
  const log = d.swap_log.length ? table(['When (UTC)', 'Market', 'From', 'To', 'Proof'], d.swap_log.slice().reverse().map(x => [esc(x.at.replace('T', ' ').slice(0, 16)), `<code class="nw">${esc(x.node)}</code>`, esc(CLOUD[x.from] || x.from), esc(CLOUD[x.to] || x.to), esc(x.proof || '')])) : '<p>No swap yet.</p>';
  return `<p class="lead">${esc(SWAP_COPY.lead)}</p>
<h2>1 Serving now</h2>${table(['Market', 'Country', 'Serving cloud', 'Record as of', 'Last swap', 'Swaps', 'Last copy to the second cloud'], rows)}
<p>Read at ${esc(d.at.replace('T', ' ').slice(0, 16))} UTC from each market's door.</p>
<h2>2 Swaps</h2>${log}
<h2>3 Machine kit</h2>${num(3, ['<a href="/llms.txt"><code>/llms.txt</code></a> · <a href="/facts.json"><code>/facts.json</code></a> · <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a>', `Doors: <code>https://mcp.&lt;market&gt;-cm-kg.ai/mcp</code> · apex <code>${esc(GI_MCP)}</code>`, `Operator: ${esc(OPERATOR)}`])}
${contactSection(host)}`;
}
function swapFacts(d, host) {
  return { domain: host, kind: 'record', product: 'agent-swap', what: SWAP_COPY.lead, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: d.at.slice(0, 10), read_at: d.at, surface_version: SURFACES_VERSION,
    nodes: d.rows.map(r => ({ node: r.node, country: r.country, serving: r.serving, record_as_of: r.as_of, swaps: r.swaps, last_swap: r.last_swap, last_ark_write: r.last_ark_write })), swaps: d.swap_log,
    machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'], source: 'X-Allooloo-Origin header of each node door at render; /swap/swaps.json; /swap/ark.json' };
}
function swapLlms(d, host) {
  return [`# ${host} — agent-swap, the record keeps answering`, `1. ${SWAP_COPY.lead}`, `2. Read at ${d.at} from each market's door:`,
    ...d.rows.map(r => `   - ${r.node} (${r.country}): serving ${r.serving ? (CLOUD[r.serving] || r.serving) : 'did not answer'}; record as of ${r.as_of || 'not read'}; swaps ${r.swaps || 'none yet'}${r.last_swap ? `; last ${r.last_swap.at.slice(0, 10)} to ${r.last_swap.to}` : ''}; last copy to the second cloud ${r.last_ark_write || 'not yet'}`),
    `3. Doors: https://mcp.<market>-cm-kg.ai/mcp; apex ${GI_MCP}. Operator: ${OPERATOR}. Contact: ${CONTACT}. agent-swap.com, .io, .org and .co.uk forward here.`,
    '4. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt'].join('\n') + '\n';
}
// record-grade pages carry no script (Site Book): the shared footer's /webmcp.js and the light/dark toggle (which needs it) are taken out for this family
export function stripScripts(htmlText) { return htmlText.replace('<script src="/webmcp.js"></script>', '').replace(/<button class="tint"[\s\S]*?<\/button>/, ''); }
