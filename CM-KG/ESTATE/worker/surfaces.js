// Estate surfaces Worker — ORDER-020 (Sept 12 2026), on top of ORDER-019. One Worker, every Allooloo surface, one chrome (chrome.js).
// Hosts: allooloo.io (§4, record pages §3, status §6) · twelve node surfaces (<cc>-cm-kg.ai; .org/.com 301) · eight product roots (agentic-*.ai; .com/.org/.io 301; RADAR §7)
// · the estate roots and cm-record hosts. Every host: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt.
// Scheduled: the §6 probe every five minutes → KV. Counts and dates are live from list_nodes on every render; nothing typed. Previous Workers kept beside (index.js, index-v1-*.js).
import NODE_DATA from './nodes.js';
import EXAMPLES from './examples.js';
import { OPERATOR, CORPORATE, CONTACT, CONTACT2, APEX, APEX_AGENT, SURFACES_VERSION, COMPANY_TITLE, REGION_FULL, ROBOTS, SECURITY, ICONS, esc, int, today, dl, num, table, form, contactSection, headers, html, markdown, notFound, text, json, sitemap, page, scale } from './chrome.js';
import * as AEO from './aeo.js';
import { PRODUCTS, ORDER, DUTY, nodesTable, totals } from './products.js';
import { heroRecord, homeBody, homeMeta, recordPageBody, PAGES, readStatus, statusBody, statusJson, probe } from './site.js';
const HOME_H1 = 'Every listed company in eleven markets, as a record an agent can call.';
// §12.3 — Toronto and London above the fold on their node pages
const FOCUS = { ca: { buyer: 'investment dealers and wealth platforms under CIRO; the fund managers who feed them', duty: 'KYP — every product on the shelf, known continuously, and the file that proves it', pain: 'a 15-to-30-person data floor doing it by hand across TSX, TSXV, CSE and Cboe Canada', first: 'Dealer MCP access to the Canada node + Coverage on their shelf', proof: 'served from Canada Central (Toronto, Canada); public-record only; source and read date on every field' },
  uk: { buyer: 'brokers, wealth managers and platforms under the FCA product governance rules (PROD); the compliance consultancies that serve them', duty: 'know the product and its target market, and show your work', pain: 'the same data floor across Main Market, AIM and Aquis, with RNS as the firehose', first: 'Dealer MCP access to the UK node + Disclosure as the feed', proof: 'served from UK South (London, United Kingdom); FCA NSM and Companies House as sources; nothing licensed on the wire' } };
import { radarData, radarBody, radarCsv } from './radar.js';
import { KYP_COPY, kypBody, kypFacts, kypLlms, kypVals } from './kyp.js';
import { handlePaid, paidStats, handleApi, receiptJwks, receiptLookup, openapi as x402Openapi } from './x402.js';
import * as OAUTH from './oauth.js';
import { docsBody, supportBody } from './docs.js';

const REGISTRY = 'registry.modelcontextprotocol.io · io.github.allooloo/cm-kg';
let LIVE = null, LIVE_AT = 0;
async function liveNodes() {
  if (LIVE && Date.now() - LIVE_AT < 300000) return LIVE;
  try {
    const r = await fetch(APEX + '/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'list_nodes', arguments: {} } }) });
    const j = await r.json(); const m = {}; for (const n of j.result.structuredContent.nodes) m[n.node] = n; LIVE = m; LIVE_AT = Date.now();
  } catch (e) { LIVE = LIVE || {}; }
  return LIVE;
}
let ASK_UP = null, ASK_AT = 0;
async function askUp() { if (ASK_UP !== null && Date.now() - ASK_AT < 600000) return ASK_UP; try { const r = await fetch('https://ask.allooloo.io/', { method: 'HEAD', signal: AbortSignal.timeout(8000) }); ASK_UP = r.ok; } catch (e) { ASK_UP = false; } ASK_AT = Date.now(); return ASK_UP; }

function classify(host) {
  const h = host.replace(/^www\./, ''); let m;
  if (h === 'allooloo.io') return { kind: 'site' };
  if (h === 'allooloo.ai') return { kind: 'redirect', canonical: 'https://allooloo.io', status: 308 };
  if (h === 'kyp-model.ai') return { kind: 'kyp' };
  if (/^(kyp-model|kypmodel)\.(com|org|io)$/.test(h)) return { kind: 'redirect', canonical: 'https://kyp-model.ai', status: 301 };   // six kyp zones → 301 → kyp-model.ai, path preserved, one hop (CEO, Sept 12 2026)   // CEO forward, Sept 12 2026: allooloo.ai + www → 308 → allooloo.io, path + query kept
  if ((m = h.match(/^([a-z]{2})-cm-kg\.(ai|org|com)$/)) && NODE_DATA[m[1]]) return { kind: 'node', cc: m[1], tld: m[2], canonical: m[2] === 'ai' ? null : `https://${m[1]}-cm-kg.ai` };
  if ((m = h.match(/^agentic-([a-z0-9]+)\.(ai|com|org|io)$/)) && PRODUCTS[m[1]]) return { kind: 'product', product: m[1], tld: m[2], canonical: m[2] === 'ai' ? null : `https://agentic-${m[1]}.ai` };
  if (h === 'capitalmarketsknowledgegraph.ai') return { kind: 'root', role: 'graph' };
  if (h === 'capitalmarketsknowledgegraph.org') return { kind: 'root', role: 'standard' };
  if (h === 'capitalmarketsknowledgegraph.com') return { kind: 'redirect', canonical: 'https://capitalmarketsknowledgegraph.ai' };
  if (h === 'cm-kg.org') return { kind: 'root', role: 'cmkg-standard' };
  if (h === 'cm-kg.io') return { kind: 'root', role: 'cmkg-twin' };
  if (h === 'cm-kg.ai') return { kind: 'redirect', canonical: 'https://capitalmarketsknowledgegraph.ai' };
  if (h === 'cm-kg.com') return { kind: 'redirect', canonical: 'https://cm-kg.ai' };
  if (h === 'cm-record.org') return { kind: 'record', role: 'standard' };
  if (h === 'cm-record.ai') return { kind: 'record', role: 'resolver' };
  if (h === 'cm-record.io') return { kind: 'record', role: 'twin' };
  if (h === 'cm-record.com') return { kind: 'redirect', canonical: 'https://cm-record.org' };
  return { kind: 'unknown' };
}
const ctxOf = (live, extra) => { let n = 0; return { live, nodes: NODE_DATA, sec: () => ++n, h: t => t, form, ...(extra || {}) }; };

// ---------- node surfaces (ORDER-019, re-chromed)
function fill(s, v) { return String(s).replace(/\{\{issuers\}\}/g, v.issuers).replace(/\{\{events\}\}/g, v.events).replace(/\{\{drop\}\}/g, v.drop); }
function nodeVals(cc, live) {
  const n = live[`${cc}-cm-kg`] || {}; const isLive = !!n.live;
  return { live: isLive, issuers: isLive ? int(n.records) : (cc === 'hk' ? 'not served (Width 0)' : ''), events: isLive ? int(n.events) : (cc === 'hk' ? 'none (Width 0)' : ''), drop: isLive ? (n.as_of || '') : '', exchanges: n.exchanges || [], version: isLive ? 1 : '' };
}
function nodeBody(host, cc, live) {
  const d = NODE_DATA[cc]; const v = nodeVals(cc, live); const node = `${cc}-cm-kg`; const ex = EXAMPLES[cc]; const partner = !!d.partner; const codes = d.idForms.map(x => `<code>${esc(x)}</code>`).join(' · ');
  const s1 = num(1, [`Jurisdiction: ${esc(d.country)}`, `Node ID: <code>${node}</code>`, `Coverage: ${esc(d.coverage)}`, `Issuer records: <code>${esc(v.issuers)}</code>`, `Dated disclosure events: <code>${esc(v.events)}</code>`, 'Disclosure period: trailing twelve months', `Drop date: <code>${esc(v.drop || 'none')}</code>`, `Operator: ${OPERATOR}`, 'Counts and drop date are populated from the node on each render. Counts render as integers. Dates render as <code>YYYY-MM-DD</code>.', esc(d.sweep)]);
  const s2 = partner
    ? num(2, ['MCP endpoint: none. This node has no door at Width 0.', 'Agent Card: none.', 'Answer scope: nothing is answered on this node; the roster is held, not served.', 'Tools: none.', 'Accepted identifiers: none.', `The other eleven nodes answer through the apex router <code>${APEX}/mcp</code>; Hong Kong identifiers return not found there.`])
    : num(2, [`MCP endpoint: <code>https://mcp.${cc}-cm-kg.ai/mcp</code>`, 'Transport: <code>streamable-http</code>', `Agent Card: <code>https://agent.${cc}-cm-kg.ai</code>`, 'Agent protocol: A2A', `Answer scope: <code>${node}</code> only`, 'Tools: <code>resolve_issuer</code>; <code>get_record</code>; <code>list_aliases</code>; <code>list_events_since</code>; <code>list_nodes</code>', `Accepted identifiers: ${codes}`,
      `Request:<pre>${esc(JSON.stringify({ tool: 'resolve_issuer', arguments: { identifier: d.example } }, null, 2))}</pre>`, `Response (captured from the wire ${esc(ex ? ex.captured : '')}):<pre>${esc(JSON.stringify(ex ? ex.response : { note: 'no capture' }, null, 2))}</pre>`]);
  const s3 = num(3, [`Storage region: Azure ${esc(REGION_FULL[cc])}${partner ? ' — no store; the roster is held in the build pond only' : ''}`, `Serving region: ${partner ? 'none' : `Azure ${esc(REGION_FULL[cc])}`}`, 'Apex router: <code>mcp.capitalmarketsknowledgegraph.ai</code>', 'Apex content: index only', 'The apex router forwards requests to the jurisdictional node.', 'No record body leaves the jurisdiction.', 'No-fallback rule: records are not served from another jurisdiction when this node is unavailable.', esc(d.residency)]);
  const s4 = num(4, [`Sources of record: ${esc(d.sources)}.`, `Field-class source mapping: ${esc(d.mapping)}.`, 'Source URL: carried on every field.', 'Read date: carried on every field.', 'Read-date format: <code>YYYY-MM-DD</code>.', 'Record <code>as_of</code> and field read dates remain separate fields.', 'Every field carries source URL and read date; none is served without both.', 'Confirmed: the field as read from its source of record.', 'Signed: reserved for CMR signing; not yet in service. Not used on this node.', esc(d.engines)]);
  const s5 = num(5, [`${esc(d.gaps)} <span class="muted">(carried from: ${esc(d.gapsFrom)})</span>`]);
  const s6 = num(6, [`Exchange tiers: ${esc(d.tiers)}`, `Filing language: ${esc(d.language)}`, `Regulator: ${esc(d.regulator)}`, `Corporate register: ${esc(d.register)}`, `Disclosure channel: ${esc(d.channel)}`, `Fiscal-year convention: ${esc(d.fiscal)}`, `Identifier forms accepted by the door: ${codes}`, esc(d.auditorLine), `Duty served by the record in this market: ${esc(d.duty)}`]);
  const s7 = num(7, ORDER.filter(x => x !== cc).map(x => { const ov = nodeVals(x, live); return x === 'hk' ? `<code>hk-cm-kg</code> · ${esc(REGION_FULL.hk)} · Width 0 · no endpoint · <a href="https://hk-cm-kg.ai/">hk-cm-kg.ai</a>` : `<code>${x}-cm-kg</code> · ${esc(REGION_FULL[x])} · <code>https://mcp.${x}-cm-kg.ai/mcp</code> · ${ov.live ? `${ov.issuers} records · ${ov.events} events` : 'door not live'} · <a href="https://${x}-cm-kg.ai/">${x}-cm-kg.ai</a>`; }));
  const focus = FOCUS[cc] ? `${scale([[esc(v.issuers), 'issuer records', 'list_nodes'], [esc(v.events), 'dated disclosure events', 'list_nodes'], [esc(v.drop || 'none'), 'drop date', 'list_nodes']])}<div class="duty">${dl([['buyer', esc(FOCUS[cc].buyer)], ['duty', esc(FOCUS[cc].duty)], ['pain', esc(FOCUS[cc].pain)], ['first product', esc(FOCUS[cc].first)], ['proof they check first', esc(FOCUS[cc].proof)]])}</div>` : '';
  const s8 = num(8, ['Machine instructions: <a href="/llms.txt"><code>/llms.txt</code></a>', 'Facts: <a href="/facts.json"><code>/facts.json</code></a>', partner ? 'Agent Card: none (no door). <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a> on this host states that.' : `Agent Card: <a href="https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json"><code>https://agent.${cc}-cm-kg.ai</code></a> (pointer at <code>/.well-known/agent-card.json</code> on this host)`, `Registry: <code>${REGISTRY}</code>`, partner ? 'Door descriptors: none.' : `Door descriptors: <a href="https://mcp.${cc}-cm-kg.ai/mcp.json"><code>mcp.json</code></a> · <a href="https://mcp.${cc}-cm-kg.ai/openapi.json"><code>openapi.json</code></a> (pointers at <code>/mcp.json</code> and <code>/openapi.json</code> here)`, 'Also on this host: <a href="/.well-known/security.txt"><code>/.well-known/security.txt</code></a> · <a href="/sitemap.xml"><code>/sitemap.xml</code></a> · <a href="/robots.txt"><code>/robots.txt</code></a>']);
  const s9 = contactSection(host);
  return `${focus}<p class="lead">${esc(fill(d.reason, v))}</p><h2>1 Scope</h2>${s1}<h2>2 Access</h2>${s2}<h2>3 Residency</h2>${s3}<h2>4 Provenance</h2>${s4}<h2>5 Known gaps</h2>${s5}<h2>6 Market particulars</h2>${s6}<h2>7 Estate</h2>${s7}<h2>8 Machine kit</h2>${s8}${s9}`;
}
function nodeFacts(host, cc, live) {
  const d = NODE_DATA[cc]; const v = nodeVals(cc, live); const node = `${cc}-cm-kg`;
  return { domain: host, kind: 'node surface', node, country: d.country, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: today(), surface_version: SURFACES_VERSION, source: 'public-record', live: v.live, issuer_records: v.live ? Number(v.issuers) : null, disclosure_events: v.live ? Number(v.events) : null, drop_date: v.drop || null, width: d.partner ? 0 : null,
    coverage: d.coverage, exchanges: v.exchanges, storage_region: d.region, serving_region: d.partner ? null : d.region, mcp_url: d.partner ? null : `https://mcp.${cc}-cm-kg.ai/mcp`, agent_card: d.partner ? null : `https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json`, apex: `${APEX}/mcp`, apex_content: 'index only', no_fallback: true,
    sources_of_record: d.sources, field_source_mapping: d.mapping, known_gaps: d.gaps, gaps_carried_from: d.gapsFrom, duty: d.duty, local_partner: d.partner ? 'wanted' : undefined, identifier_forms: d.idForms, registry: REGISTRY,
    machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'].concat(d.partner ? [] : ['/mcp.json', '/openapi.json']), counts_from: 'list_nodes (live on each render)' };
}
function nodeLlms(host, cc, live) {
  const d = NODE_DATA[cc]; const v = nodeVals(cc, live); const node = `${cc}-cm-kg`;
  return [`# ${host} — ${d.title}`, `1. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`, `2. What this host is: the surface of the ${d.country} node (${node}) of the Capital Markets Knowledge Graph. The surface tells a human or a crawler the node exists and hands them to it; it answers nothing itself.`,
    `3. Node: ${node}. Live: ${v.live ? 'yes' : 'no'}. Issuer records: ${v.issuers}. Dated disclosure events: ${v.events}. Drop date: ${v.drop || 'none'}. Coverage: ${d.coverage}.`,
    d.partner ? '4. Door: none (Width 0 by order; local partner wanted). Agent Card: none.' : `4. Door (MCP, streamable-http, no auth): https://mcp.${cc}-cm-kg.ai/mcp. Agent Card (A2A): https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json. Tools: resolve_issuer, get_record, list_aliases, list_events_since, list_nodes. Answer scope: ${node} only.`,
    `5. Identifiers accepted: ${d.idForms.join('; ')}.`, `6. Residency: stored and served from Azure ${d.region}; the apex router ${APEX}/mcp holds an index and forwards; no record body leaves the jurisdiction; no fallback.`,
    `7. Sources of record: ${d.sources}.`, `8. Known gaps: ${d.gaps}`, `9. Registry: ${REGISTRY}.`, `10. Machine paths on this host: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt${d.partner ? '' : ' /mcp.json /openapi.json'}.`,
    '11. Rules: public-record only; no prices, quotes or licensed market data; blank stays blank; nothing published before it answers; counts and dates are live from list_nodes, never typed.', `12. Surface version: ${SURFACES_VERSION}; prior renders are kept in the pond.`].join('\n') + '\n';
}
function nodeCard(host, cc, live) {
  const d = NODE_DATA[cc]; const v = nodeVals(cc, live); const node = `${cc}-cm-kg`;
  if (d.partner) return { name: `${d.country} node — Capital Markets Knowledge Graph (surface)`, description: `Surface of ${node}. No door and no agent at Width 0; local partner wanted. This host answers nothing itself.`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, capabilities: {}, skills: [], version: '0', contact: CONTACT };
  return { name: `${d.country} node — Capital Markets Knowledge Graph (surface pointer)`, description: `Surface of ${node}: ${v.issuers} issuer records, ${v.events} dated disclosure events as of ${v.drop}. The node's agent is at https://agent.${cc}-cm-kg.ai; its MCP door is https://mcp.${cc}-cm-kg.ai/mcp. This host is documentation only.`,
    url: `https://mcp.${cc}-cm-kg.ai/mcp`, agentCard: `https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, version: String(v.version || 1), protocolVersion: '0.3', capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'],
    skills: [{ id: 'pointer', name: 'Where the node answers', description: `Resolve, read, alias, event and node listing calls for ${d.country} go to the node door; see agentCard.`, tags: ['capital-markets', cc] }], contact: CONTACT };
}
const nodePointer = (kind, cc) => ({ pointer: true, node: `${cc}-cm-kg`, [kind]: `https://mcp.${cc}-cm-kg.ai/${kind}.json`, note: 'this host is the node surface; the door descriptor is served by the door' });

// ---------- product roots
function productFacts(host, key, live) {
  const p = PRODUCTS[key]; const t = totals(ctxOf(live)); return { domain: host, kind: 'product surface', product: p.title, h1: p.h1, description: p.reason, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, canonical: `https://agentic-${key}.ai/`, as_of: today(), surface_version: SURFACES_VERSION, source: 'public-record', estate: 'Capital Markets Knowledge Graph (CM-KG)', apex: `${APEX}/mcp`, live_nodes: Object.values(live).filter(n => n.live).map(n => n.node), issuer_records_live: t.records, disclosure_events_live: t.events, last_drop: t.last, counts_from: 'list_nodes (live on each render)', machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'].concat(key === 'radar' ? ['/radar.json', '/radar.csv'] : []) };
}
const productCard = (host, key) => { const p = PRODUCTS[key]; return { name: `${p.title.split(' — ')[0]} — Allooloo`, description: `${p.reason} No agent endpoint on this host; the estate agent is at ${APEX_AGENT}.`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, capabilities: {}, skills: [], version: '0', contact: CONTACT, estate_agent_card: `${APEX_AGENT}/.well-known/agent-card.json` }; };
const productLlms = (host, key, live) => { const p = PRODUCTS[key]; const t = totals(ctxOf(live)); return [`# ${host} — ${p.title}`, `1. ${p.reason}`, `2. Operator: ${OPERATOR}. Contact: ${CONTACT}. Canonical: https://agentic-${key}.ai/ (.com .org .io forward here).`, `3. Estate: ${t.nodes} live nodes, ${t.records} issuer records, ${t.events} dated disclosure events at render (list_nodes); apex door ${APEX}/mcp; apex Agent Card ${APEX_AGENT}/.well-known/agent-card.json.`, '4. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt' + (key === 'radar' ? ' /radar.json /radar.csv' : ''), '5. Rules: public-record only; no prices; nothing published before it answers; every number on the page is a door, a log or a ledger.', `6. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n'; };

// ---------- allooloo.io
function siteFacts(live) { const t = totals(ctxOf(live)); return { record: 'allooloo-facts', as_of: today(), surface_version: SURFACES_VERSION, legal_name: OPERATOR, jurisdiction: 'Canada', city: 'Vancouver', url: CORPORATE, contact: CONTACT, positioning: 'Agentic Capital Markets Global Desk', estate: { issuer_records: t.records, disclosure_events: t.events, nodes_live: t.nodes, last_drop: t.last, counts_from: 'list_nodes (live on each render)', apex: `${APEX}/mcp`, nodes: ORDER.map(cc => { const n = live[`${cc}-cm-kg`] || {}; return { node: `${cc}-cm-kg`, country: NODE_DATA[cc].country, live: !!n.live, records: n.live ? n.records : null, events: n.live ? n.events : null, surface: `https://${cc}-cm-kg.ai/` }; }) }, products: Object.keys(PRODUCTS).map(k => ({ product: PRODUCTS[k].title, url: `https://agentic-${k}.ai/` })), licence_shapes: ['Dealer MCP access', 'Issuer record', 'Knowledge Graph API', 'Node operator'], rules: ['licence only, no services', 'public-record only: no prices, no quotes, no licensed market data', 'blank is blank; every field carries a source and a reader', 'nothing deleted; records versioned'], status: 'https://allooloo.io/status', radar: 'https://agentic-radar.ai/radar.json', machine_paths: ['/llms.txt', '/facts.json', '/.well-known/allooloo.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/status.json'] }; }
const siteLlms = (live) => { const t = totals(ctxOf(live)); return [`# allooloo.io — ${OPERATOR}`, '1. Agentic Capital Markets Global Desk. Vancouver, Canada. Contact: ' + CONTACT + '. Builder of the Capital Markets Knowledge Graph and the Capital Markets Record, served to AI agents over MCP and A2A.', `2. Estate at render: ${t.nodes} live nodes, ${t.records} issuer records, ${t.events} dated disclosure events (list_nodes); apex door ${APEX}/mcp; eleven regional doors mcp.<cc>-cm-kg.ai/mcp; Hong Kong a beacon.`, '3. Products: ' + Object.keys(PRODUCTS).map(k => `${PRODUCTS[k].title} — https://agentic-${k}.ai/`).join('; ') + '.', '4. Licence shapes: Dealer MCP access; Issuer record; Knowledge Graph API; Node operator. Licence only, no services.', '5. Rules: public-record only; no prices, quotes or licensed market data; blank stays blank; every field carries a source and a reader; records versioned, never deleted.', '6. Record pages: /status /terms /privacy /security /no-cookies. Machine: /facts.json /.well-known/allooloo.json /.well-known/agent-card.json /.well-known/security.txt /status.json /sitemap.xml /robots.txt.', `7. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n'; };
const siteCard = () => ({ name: 'Allooloo Technologies Corp. — corporate surface', description: `Corporate surface of the operator of the Capital Markets Knowledge Graph. The estate agent is at ${APEX_AGENT}; the apex MCP door at ${APEX}/mcp.`, url: `${APEX}/mcp`, agentCard: `${APEX_AGENT}/.well-known/agent-card.json`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `${CORPORATE}/`, capabilities: {}, skills: [], version: '0', contact: CONTACT });

// ---------- roots and record hosts
function rootFacts(host, c, live) {
  const base = { domain: host, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: today(), surface_version: SURFACES_VERSION, source: 'public-record', estate: 'Capital Markets Knowledge Graph (CM-KG)', machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'], counts_from: 'list_nodes (live on each render)' };
  const ln = Object.values(live);
  if (c.kind === 'root') return { ...base, kind: { graph: 'root of the graph', standard: 'standard mirror of the long-form root', 'cmkg-standard': 'CM-KG standard and beacon', 'cmkg-twin': 'CM-KG machine twin' }[c.role], live_nodes: ln.filter(n => n.live).map(n => n.node), global_door: `${APEX}/mcp`, apex_agent_card: `${APEX_AGENT}/.well-known/agent-card.json`, nodes: ORDER.map(cc => { const n = live[`${cc}-cm-kg`] || {}; return { node: `${cc}-cm-kg`, country: NODE_DATA[cc].country, live: !!n.live, records: n.live ? n.records : 0, events: n.live ? n.events : 0, as_of: n.live ? n.as_of : null, surface: `https://${cc}-cm-kg.ai/` }; }) };
  return { ...base, kind: { standard: 'Capital Markets Record — the object standard (schema, signing, versions)', resolver: 'CMR resolver door', twin: 'CMR machine twin' }[c.role], spec: 'CMR v0 (draft)', signing: 'not yet live; no signature is stubbed', resolver_live: false, records_served_by: `${APEX}/mcp` };
}
function rootBody(host, c, f, live) {
  if (c.kind === 'root') return `<p class="lead">${esc(f.kind)}. Issuers as nodes; insiders, holders, auditors, transfer agents, parents and subsidiaries, dual listings and newswires as edges. Twelve sovereign market nodes, one apex router that holds an index and forwards. Public-record only.</p><p><strong>Live nodes: ${f.live_nodes.length ? esc(f.live_nodes.join(', ')) : 'none'}.</strong> The apex answers at <code>${esc(f.global_door)}</code> (Streamable HTTP MCP, no auth) and forwards by identifier to the node that holds the name.</p>${nodesTable(ctxOf(live))}<p>${c.role === 'graph' ? '<a href="/docs">Documentation — connect, tools, record shape, residency</a> · ' : ''}<a href="${APEX}/">Apex door</a> · <a href="${APEX_AGENT}/.well-known/agent-card.json">Apex Agent Card</a> · <a href="${APEX}/openapi.json">openapi.json</a> · <a href="${APEX}/mcp.json">mcp.json</a></p>${contactSection(host)}`;
  return `<p class="lead">${esc(f.kind)}. One record per listed company, keyed on ISIN, ticker and LEI. Versioned, sourced, never deleted; every field names the registry it came from or the engine that read it and carries a state.</p><p><strong>Status: ${c.role === 'resolver' ? 'resolver not live' : 'draft standard (CMR v0)'}.</strong> Signing is not yet live and no signature is stubbed. Records are served today by the apex at <code>${esc(f.records_served_by)}</code>.</p>${contactSection(host)}`;
}
const rootTitle = c => c.kind === 'root' ? { graph: 'Capital Markets Knowledge Graph', standard: 'Capital Markets Knowledge Graph — standard', 'cmkg-standard': 'CM-KG — standard and beacon', 'cmkg-twin': 'CM-KG — machine twin' }[c.role] : { standard: 'Capital Markets Record — the standard', resolver: 'Capital Markets Record — resolver', twin: 'Capital Markets Record — machine twin' }[c.role];
const rootLlms = (host, c, f) => [`# ${host}`, `Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`, `What this domain is: ${f.kind}.`, c.kind === 'root' ? `Live nodes: ${f.live_nodes.join(', ') || 'none'}. Apex door (Streamable HTTP MCP, no auth): ${f.global_door}. Tools: resolve_issuer, get_record, list_events_since, list_aliases, list_nodes. Documentation: https://${host}/docs (connect, tools with wire examples, identifiers, record shape, residency, data handling, limits, support). Node surfaces: ${ORDER.map(cc => `https://${cc}-cm-kg.ai/`).join(' ')}` : `Spec: ${f.spec}. Signing: ${f.signing}. Records served by ${f.records_served_by}.`, 'Rules: public-record only; no prices, quotes or licensed market data; blank stays blank; nothing published before it answers.', 'Machine paths: /llms.txt, /facts.json, /.well-known/agent-card.json, /.well-known/security.txt, /sitemap.xml, /robots.txt', `Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
const rootCard = (host, c, f) => ({ name: `${host} — Allooloo`, description: `${f.kind}. This host is documentation; the estate agent is at ${APEX_AGENT}.`, url: c.kind === 'root' ? `${APEX}/mcp` : undefined, agentCard: `${APEX_AGENT}/.well-known/agent-card.json`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, capabilities: {}, skills: [], version: '0', contact: CONTACT });

export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(probe(env)); },
  async fetch(request, env) {
    const url = new URL(request.url); const host = url.hostname; const c = classify(host); const apex = host.replace(/^www\./, '');
    if (c.kind === 'redirect' || c.canonical) return Response.redirect(c.canonical + url.pathname + url.search, c.status || 301);
    if (host !== apex) return Response.redirect(`https://${apex}${url.pathname}${url.search}`, 301);
    const p = url.pathname.replace(/\/+$/, '') || '/';
    // x402 paid route (agentic-trades.ai only): the same record as the free apex route, $0.01 USDC on Base; free routes untouched
    const paid = c.kind === 'product' && c.product === 'trades' && p.match(/^\/x402\/record\/([a-z]{2}-cm-kg)\/([A-Za-z\-]+)\/(.+)$/i);
    if (paid) { if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: headers({}, { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'PAYMENT-SIGNATURE, X-PAYMENT, content-type', 'access-control-allow-methods': 'GET, OPTIONS' }) }); return handlePaid(request, env, url, paid); }
    // REGISTRIES GATE (TO 100): the authorization server on agentic-registries.ai; licensed routes gated by a bearer token, public routes untouched
    if (c.kind === 'product' && c.product === 'registries') {
      if (p === '/oauth/register' && request.method === 'POST') return OAUTH.register(request, env);
      if (p === '/oauth/token' && request.method === 'POST') return OAUTH.token(request, env);
      if (p === '/oauth/introspect' && request.method === 'POST') return OAUTH.introspect(request, env);
      if (p === '/oauth/revoke' && request.method === 'POST') return OAUTH.revoke(request, env);
      if (p === '/agent/identity' && request.method === 'POST') return OAUTH.identity(request, env);
      if (p === '/agent/identity/claim' && request.method === 'POST') return OAUTH.claim(request, env);
      if (p === '/agent/event/notify' && request.method === 'POST') return OAUTH.events(request, env);
      if ((p.startsWith('/oauth/') || p.startsWith('/agent/')) && request.method === 'OPTIONS') return new Response(null, { status: 204, headers: headers({}, { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'authorization, content-type', 'access-control-allow-methods': 'GET, POST, OPTIONS' }) });
      if (p === '/oauth/jwks.json') return json(await OAUTH.jwks(env), { node: 'registry' }, 'public, max-age=300');
      if (p.startsWith('/oauth/register/') && request.method === 'GET') { const v = await OAUTH.verify(request, env); const id = p.split('/').pop(); if (!v.ok || v.claims.sub !== id) return OAUTH.challenge(host, v.error); const ci = await OAUTH.clientInfo(env, id); return ci ? json(ci, { node: 'registry' }, 'no-store') : notFound([], { node: 'registry' }); }
      if (p === '/registry/whoami') { const v = await OAUTH.verify(request, env); if (!v.ok) return OAUTH.challenge(host, v.error); return json({ licensed: true, ...v.claims, note: 'a licensed call; receipted in the region of the call' }, { node: 'registry' }, 'no-store'); }
    }
    // AGENTIC-X402.AI (23rd surface): the paid endpoint, the receipt key and the receipt resolver
    if (c.kind === 'product' && c.product === 'x402') {
      if (p === '/api') { if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: headers({}, { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'PAYMENT-SIGNATURE, X-PAYMENT, content-type', 'access-control-allow-methods': 'GET, POST, OPTIONS' }) }); return handleApi(request, env, url); }
      if (p === '/x402/jwks.json') return json(await receiptJwks(env), { node: 'x402' }, 'public, max-age=300');
      if (p === '/openapi.json') return json(x402Openapi(), { node: 'x402' }, 'public, max-age=3600');
      const rc = p.match(/^\/x402\/receipt\/([a-f0-9]{32})$/); if (rc) { const r = await receiptLookup(env, rc[1]); return r ? json(r, { node: 'x402' }, 'public, max-age=31536000, immutable') : notFound(['/x402/receipt/{nonce}'], { node: 'x402' }); }
    }
    const lic = c.kind === 'product' && c.product === 'trades' && p.match(/^\/licensed\/record\/([a-z]{2}-cm-kg)\/([A-Za-z\-]+)\/(.+)$/i);
    if (lic) { const v = await OAUTH.verify(request, env); if (!v.ok) return OAUTH.challenge(host, v.error); const r = await fetch(`${APEX}/record/${lic[1]}/${lic[2]}/${lic[3]}`, { headers: { accept: 'application/json' } }); return new Response(await r.text(), { status: r.status, headers: headers({ node: 'registry' }, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'X-Licensed-Client': v.claims.sub }) }); }
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405, headers: headers({}, { 'content-type': 'text/plain' }) });
    if (ICONS.includes(p)) { const a = await env.ASSETS.fetch(new Request(url.origin + p)); const h = new Headers(a.headers); for (const [k, v] of Object.entries(headers({}))) h.set(k, v); h.set('cache-control', p === '/estate.css' ? 'public, max-age=300' : 'public, max-age=86400'); return new Response(a.body, { status: a.status, headers: h }); }
    if (p === '/robots.txt') return text(ROBOTS(host), {}, 'text/plain; charset=utf-8', 'public, max-age=86400');
    if (p === '/.well-known/security.txt') return text(SECURITY(host), {}, 'text/plain; charset=utf-8', 'public, max-age=86400');
    const live = await liveNodes(); const ctx = ctxOf(live);
    // ---- agent readiness kit (aeo.js): the same paths on every surface, pointing at the node door, the apex, or the beacon
    const cc0 = c.kind === 'node' ? c.cc : null; const T = AEO.target(c, cc0); const kmeta = { node: c.kind === 'node' ? `${c.cc}-cm-kg` : (c.kind === 'site' ? 'allooloo' : 'estate'), as_of: today() };
    const LINK = AEO.linkHeader(host, T);
    const label = c.kind === 'node' ? `${NODE_DATA[c.cc].country} node — Capital Markets Knowledge Graph` : c.kind === 'product' ? PRODUCTS[c.product].title : c.kind === 'site' ? 'Allooloo Technologies Corp. — Capital Markets Knowledge Graph' : c.kind === 'kyp' ? KYP_COPY.title : `${host} — Capital Markets Knowledge Graph`;
    const desc0 = c.kind === 'node' ? fill(NODE_DATA[c.cc].meta, nodeVals(c.cc, live)) : c.kind === 'product' ? PRODUCTS[c.product].reason : c.kind === 'site' ? homeMeta(ctx) : c.kind === 'kyp' ? KYP_COPY.meta.replace(/\{records\}/g, kypVals(ctx).records).replace(/\{events\}/g, kypVals(ctx).events).replace(/\{live_nodes\}/g, kypVals(ctx).live_nodes) : 'Estate host of the Capital Markets Knowledge Graph; the apex router answers for every market.';
    const HTML = (body, m) => AEO.wantsMarkdown(request) ? markdown(AEO.toMarkdown(body, host), m, LINK) : html(body, m, LINK);
    if (p === '/.well-known/oauth-authorization-server' || p === '/.well-known/openid-configuration') return json(OAUTH.metadata(), kmeta, 'public, max-age=3600');
    if (p === '/.well-known/api-catalog') return json(AEO.apiCatalog(host, T), kmeta, 'public, max-age=3600', 200, 'application/linkset+json');
    if (p === '/.well-known/oauth-protected-resource') return json(AEO.protectedResource(host, T), kmeta, 'public, max-age=3600');
    if (p === '/auth.md') return markdown(AEO.authMd(host, T), kmeta, LINK);
    if (p === '/.well-known/mcp/server-card.json' || p === '/.well-known/mcp/server-cards.json' || p === '/.well-known/mcp.json') return json(AEO.mcpServerCard(host, T, live), kmeta);
    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(AEO.agentCard(host, T, label, desc0, live, cc0), kmeta);
    if (p === '/.well-known/agent-skills/index.json') return json(AEO.skillsIndex(host, T), kmeta);
    const sk = p.match(/^\/\.well-known\/agent-skills\/([a-z-]+)\/SKILL\.md$/); if (sk) { const md = AEO.skillMd(host, T, sk[1]); return md ? markdown(md, kmeta, LINK) : notFound([], kmeta); }
    if (p === '/.well-known/ai-catalog.json') return json(AEO.aiCatalog(host, T, label, desc0), kmeta);
    if (p.startsWith('/.well-known/') && p !== '/.well-known/allooloo.json') return notFound(['/.well-known/agent-card.json', '/.well-known/mcp/server-card.json', '/.well-known/api-catalog', '/.well-known/oauth-protected-resource', '/.well-known/agent-skills/index.json', '/.well-known/ai-catalog.json', '/.well-known/security.txt'], kmeta);
    if (c.kind === 'kyp') {
      const v = kypVals(ctx); const meta = { node: 'kyp-model', as_of: v.last || today() }; const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
      if (p === '/') return HTML(page({ host, title: KYP_COPY.title, desc: desc0, h1: KYP_COPY.h1, state: 'live', asOf: v.last || today(), body: kypBody(ctx, host), jsonld: [{ '@context': 'https://schema.org', '@type': 'Article', headline: KYP_COPY.h1, name: KYP_COPY.title, description: desc0, url: `https://${host}/`, datePublished: '2026-09-12', author: { '@type': 'Person', name: 'Matthew Keddy', jobTitle: 'CEO', worksFor: { '@type': 'Organization', name: OPERATOR, url: CORPORATE } }, publisher: { '@type': 'Organization', name: OPERATOR, url: CORPORATE } }] }), meta);
      if (p === '/llms.txt') return text(kypLlms(host, ctx), meta);
      if (p === '/facts.json') return json(kypFacts(host, ctx), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      return notFound(paths, meta);
    }
    if (c.kind === 'site') {
      const meta = { node: 'allooloo', as_of: today() }; const t = totals(ctx);
      const paths = ['/', '/support', '/status', '/terms', '/privacy', '/security', '/no-cookies', '/llms.txt', '/facts.json', '/status.json', '/.well-known/allooloo.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
      if (p === '/radar') return Response.redirect('https://agentic-radar.ai/' + url.search, 308);
      if (p === '/contact') return Response.redirect(CORPORATE + '/#contact', 302);
      if (p === '/support') return HTML(page({ host, title: 'Support — Allooloo', desc: 'Support for the Allooloo estate doors: what to bring, the contact form of record, status, security and documentation links.', h1: 'Support', state: 'live', asOf: today(), path: '/support', nocurrent: true, body: supportBody(host) }), meta);
      if (p === '/') return HTML(page({ host, title: COMPANY_TITLE, desc: homeMeta(ctx), h1: HOME_H1, state: 'live', asOf: t.last || today(), body: homeBody(ctx, host), jsonld: [{ '@context': 'https://schema.org', '@type': 'Organization', name: OPERATOR, url: CORPORATE, logo: `${CORPORATE}/icon-512.png`, address: { '@type': 'PostalAddress', addressLocality: 'Vancouver', addressRegion: 'BC', addressCountry: 'CA' }, contactPoint: { '@type': 'ContactPoint', url: CONTACT, contactType: 'support' } }] }), meta);
      if (p === '/record') { const rec = await heroRecord(); return HTML(page({ host, title: 'What a record looks like — a live Capital Markets Record for AI agents — Allooloo', desc: 'One live Capital Markets Record from the Canada door, every field with its value, source, reader and state — the shape AI agents read on every node.', h1: 'What a record looks like: one live Capital Markets Record from the Canada door.', state: rec ? 'live' : 'record', asOf: rec ? rec.as_of : today(), version: rec ? `${SURFACES_VERSION} · record v${rec.version}` : SURFACES_VERSION, path: '/record', body: recordPageBody(rec) }), { node: 'ca-cm-kg', as_of: rec ? rec.as_of : today(), version: rec ? rec.version : '' }); }
      if (p === '/status') { const st = await readStatus(env); return HTML(page({ host, title: 'Status — Allooloo estate doors', desc: 'Eleven doors probed every five minutes with one real resolve_issuer; response times, 24h median, last drop. Hong Kong a beacon.', h1: 'Status — the eleven doors', state: 'live', asOf: today(), body: statusBody(ctx, st) }), meta); }
      if (p === '/status.json') { const st = await readStatus(env); return json(statusJson(ctx, st), meta, 'public, max-age=60'); }
      const pg = PAGES[p.slice(1)]; if (pg) return HTML(page({ host, title: pg.title, desc: `${pg.h1}. ${OPERATOR}, record-grade page, as of 2026-09-12.`, h1: pg.h1, state: pg.state, asOf: '2026-09-12', version: '0.1', body: pg.body() }), meta);
      if (p === '/llms.txt') return text(siteLlms(live), meta);
      if (p === '/facts.json') return json(siteFacts(live), meta);
      if (p === '/.well-known/allooloo.json') { const a = await env.ASSETS.fetch(new Request(url.origin + '/site/.well-known/allooloo.json')); return json(a.ok ? await a.json() : { error: 'not_found' }, meta, 'public, max-age=3600'); }
      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(siteCard(), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths.filter(x => !x.endsWith('.json') && !x.endsWith('.txt'))), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      return notFound(paths, meta);
    }
    if (c.kind === 'node') {
      const cc = c.cc; const v = nodeVals(cc, live); const d = NODE_DATA[cc]; const meta = { node: `${cc}-cm-kg`, as_of: v.drop || today(), version: v.version };
      const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt'].concat(d.partner ? [] : ['/mcp.json', '/openapi.json']);
      if (p === '/') return HTML(page({ host, title: d.title, desc: fill(d.meta, v), h1: d.h1, state: v.live ? 'live' : (d.partner ? 'width 0' : 'not live'), asOf: v.drop || today(), version: v.live ? `${SURFACES_VERSION} · record v${v.version}` : SURFACES_VERSION, body: nodeBody(host, cc, live), jsonld: [{ '@context': 'https://schema.org', '@type': 'Dataset', name: d.title, description: fill(d.meta, v), url: `https://${host}/`, creator: { '@type': 'Organization', name: OPERATOR, url: CORPORATE }, license: 'public-record only', spatialCoverage: d.country, ...(v.live ? { distribution: [{ '@type': 'DataDownload', encodingFormat: 'application/json', contentUrl: `https://mcp.${cc}-cm-kg.ai/mcp` }] } : {}) }] }), meta);
      if (p === '/llms.txt') return text(nodeLlms(host, cc, live), meta);
      if (p === '/facts.json') return json(nodeFacts(host, cc, live), meta);
      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(nodeCard(host, cc, live), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      if ((p === '/mcp.json' || p === '/openapi.json') && !d.partner) return json(nodePointer(p.slice(1, -5), cc), meta);
      return notFound(paths, meta);
    }
    if (c.kind === 'product') {
      const key = c.product; const pr = PRODUCTS[key]; const meta = { node: 'estate', as_of: today() }; const t = totals(ctx);
      const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt'].concat(key === 'radar' ? ['/radar.json', '/radar.csv'] : key === 'x402' ? ['/api', '/openapi.json', '/x402/jwks.json', '/x402/receipt/{nonce}'] : []);
      if (key === 'radar' && (p === '/' || p === '/radar.json' || p === '/radar.csv')) {
        const st = await readStatus(env); const d = await radarData(ctx, env, url.origin, st); d.paid_calls = await paidStats(env);
        if (p === '/radar.json') return json(d, meta, 'public, max-age=60');
        if (p === '/radar.csv') return text(radarCsv(d), meta, 'text/csv; charset=utf-8', 'public, max-age=60');
        const body = page({ host, title: pr.title, desc: pr.reason, h1: pr.h1, state: 'live', asOf: d.as_of.slice(0, 10), version: 'v1.0 · ' + SURFACES_VERSION, body: `<p class="lead">${esc(pr.reason)}</p>${radarBody(ctx, host, d)}`, mono: true });
        if (AEO.wantsMarkdown(request)) return markdown(AEO.toMarkdown(body, host), meta, LINK);
        return new Response(body, { headers: headers(meta, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=60', 'Vary': 'Accept', 'Link': LINK, 'Content-Security-Policy': "default-src 'none'; img-src 'self' data:; style-src 'self'; base-uri 'none'; form-action https://formspree.io https://allooloo.io; frame-ancestors *; upgrade-insecure-requests", 'X-Frame-Options': 'ALLOWALL' }) });
      }
      if (p === '/') { const ask = key === 'ask' ? await askUp() : false; return HTML(page({ host, title: pr.title, desc: pr.reason, h1: pr.h1, state: 'live', asOf: t.last || today(), body: `<p class="lead">${esc(pr.reason)}</p>${pr.body(ctxOf(live, { askUp: ask }), host)}` }), meta); }
      if (p === '/facts.json') return json(productFacts(host, key, live), meta);
      if (p === '/llms.txt') return text(productLlms(host, key, live), meta);
      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(productCard(host, key), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      return notFound(paths, meta);
    }
    if (c.kind === 'root' || c.kind === 'record') {
      const f = rootFacts(host, c, live); const meta = { node: c.kind === 'root' ? 'global' : 'cm-record', as_of: f.as_of }; const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
      const isGraph = c.kind === 'root' && c.role === 'graph'; const helpLink = isGraph ? '<link rel="help" href="/docs" title="Connector documentation">' : '';
      if (p === '/') return HTML(page({ host, title: rootTitle(c), desc: `${rootTitle(c)}. Operator: ${OPERATOR}. Public-record only.`, h1: rootTitle(c), state: c.kind === 'root' ? 'live' : 'draft', asOf: today(), head: helpLink, body: rootBody(host, c, f, live) }), meta);
      if (p === '/docs' && isGraph) return HTML(page({ host, title: 'Documentation — Capital Markets Knowledge Graph apex door for AI agents', desc: 'Connector documentation for the apex door: connect, five read-only tools with wire examples, identifiers, the record shape, residency by node, data handling, limits and versioning, support.', h1: 'Documentation — the apex door', state: 'live', asOf: today(), path: '/docs', head: helpLink, nocurrent: true, body: docsBody(live) }), meta);
      if (p === '/llms.txt') return text(rootLlms(host, c, f), meta);
      if (p === '/facts.json') return json(f, meta);
      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(rootCard(host, c, f), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      return notFound(paths, meta);
    }
    return json({ error: 'not_found', note: 'an Allooloo Technologies Corp. domain with no page of its own', corporate: CORPORATE }, {}, 'no-store', 404);
  }
};
