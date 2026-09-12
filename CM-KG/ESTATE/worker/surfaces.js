// Estate surfaces Worker — ORDER-019 (Sept 12 2026). One Worker, every Allooloo zone that has no page of its own. Beside the previous index.js (kept).
// Node surfaces: <cc>-cm-kg.ai renders the nine-section node page (NODE-SURFACES.md); .org and .com 301 to the .ai, path and query kept.
// Agentic zones: agentic-<product>.ai serves the quiet-zone kit; .com .org .io 301 to the .ai. Roots and cm-record hosts keep their pages.
// Every host: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt (+ /mcp.json /openapi.json pointers where a door exists),
// self-canonical, <title> + meta, WebSite JSON-LD "Allooloo", og:site_name, favicon set, CMR headers, strict CSP, HSTS, zero third-party scripts.
// Counts and dates are live from list_nodes on every render; nothing typed.
import NODE_DATA from './nodes.js';
import EXAMPLES from './examples.js';

const OPERATOR = 'Allooloo Technologies Corp.';
const CORPORATE = 'https://allooloo.io';
const CONTACT = 'developers@allooloo.ai';
const CONTACT2 = 'allooloo@hey.com';
const APEX = 'https://mcp.capitalmarketsknowledgegraph.ai';
const APEX_AGENT = 'https://agent.capitalmarketsknowledgegraph.ai';
const REGISTRY = 'registry.modelcontextprotocol.io · io.github.allooloo/cm-kg';
const ORDER = ['ca', 'us', 'uk', 'fr', 'nl', 'ch', 'de', 'au', 'sg', 'jp', 'kr', 'hk'];
const FORM = 'https://formspree.io/f/moeqzgll';
const AGENTIC = {
  trades: { name: 'Agentic Trades', line: 'Agentic Trades is an Allooloo Technologies Corp. product surface: trade-side agents on the Capital Markets Knowledge Graph. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' },
  ask: { name: 'Agentic Ask', line: 'Agentic Ask is an Allooloo Technologies Corp. product surface: question-and-answer agents over sourced capital-markets records. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' },
  coverage: { name: 'Agentic Coverage', line: 'Agentic Coverage is an Allooloo Technologies Corp. product surface: coverage of every listed issuer per market, held as records agents can call. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' },
  esg: { name: 'Agentic ESG', line: 'Agentic ESG is an Allooloo Technologies Corp. product surface: sustainability disclosures per issuer, sourced and read-dated, for agents. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' },
  issuers: { name: 'Agentic Issuers', line: 'Agentic Issuers is an Allooloo Technologies Corp. product surface: the issuer record — identity, registers, auditors, agents — served in-country. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' },
  registries: { name: 'Agentic Registries', line: 'Agentic Registries is an Allooloo Technologies Corp. product surface: public registers (LEI, company registers, securities lists) joined into one callable record. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' },
  disclosure: { name: 'Agentic Disclosure', line: 'Agentic Disclosure is an Allooloo Technologies Corp. product surface: dated disclosure events per issuer from the filing systems and wires of each market. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' },
  radar: { name: 'Agentic Radar', line: 'Agentic Radar is an Allooloo Technologies Corp. product surface: what moved since a date across the twelve market nodes, for agents that watch. The product page follows under its own order; this zone is live, open to crawlers and carries the machine kit. Corporate: https://allooloo.io' }
};
const CSP = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; base-uri 'none'; form-action https://formspree.io; frame-ancestors 'none'; upgrade-insecure-requests";
const BOTS = ['GPTBot', 'ClaudeBot', 'Claude-User', 'Claude-SearchBot', 'Google-Extended', 'PerplexityBot', 'Perplexity-User', 'OAI-SearchBot', 'ChatGPT-User', 'Bingbot', 'Applebot', 'Applebot-Extended', 'Amazonbot', 'CCBot', 'DuckAssistBot', 'meta-externalagent', 'Bytespider', 'cohere-ai', 'Diffbot', 'YouBot', 'MistralAI-User', 'xAI-Grok'];
const ROBOTS = host => ['User-agent: *\nAllow: /'].concat(BOTS.map(u => `User-agent: ${u}\nAllow: /`)).join('\n\n') + `\n\nSitemap: https://${host}/sitemap.xml\n`;
const SECURITY = host => `Contact: mailto:${CONTACT}\nContact: ${CORPORATE}\nExpires: 2027-09-12T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: ${CORPORATE}\n`;
const ICONS = ['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-48.png', '/icon-96.png', '/icon-144.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest'];
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
const int = n => (typeof n === 'number' && isFinite(n)) ? String(Math.trunc(n)) : '';
const today = () => new Date().toISOString().slice(0, 10);

let LIVE = null, LIVE_AT = 0;
async function liveNodes() {
  if (LIVE && Date.now() - LIVE_AT < 300000) return LIVE;
  try {
    const r = await fetch(APEX + '/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'list_nodes', arguments: {} } }) });
    const j = await r.json(); const m = {}; for (const n of j.result.structuredContent.nodes) m[n.node] = n; LIVE = m; LIVE_AT = Date.now();
  } catch (e) { LIVE = LIVE || {}; }
  return LIVE;
}

function classify(host) {
  const h = host.replace(/^www\./, ''); let m;
  if ((m = h.match(/^([a-z]{2})-cm-kg\.(ai|org|com)$/)) && NODE_DATA[m[1]]) return { kind: 'node', cc: m[1], tld: m[2], canonical: m[2] === 'ai' ? null : `https://${m[1]}-cm-kg.ai` };
  if ((m = h.match(/^agentic-([a-z]+)\.(ai|com|org|io)$/)) && AGENTIC[m[1]]) return { kind: 'agentic', product: m[1], tld: m[2], canonical: m[2] === 'ai' ? null : `https://agentic-${m[1]}.ai` };
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

// ---------- shared chrome
function head(host, title, desc, extraJsonLd) {
  const ld = [{ '@context': 'https://schema.org', '@type': 'WebSite', name: 'Allooloo', url: `https://${host}/`, publisher: { '@type': 'Organization', name: OPERATOR, url: CORPORATE } }].concat(extraJsonLd || []);
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="https://${host}/">
<meta property="og:site_name" content="Allooloo"><meta property="og:type" content="website"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="https://${host}/"><meta property="og:image" content="https://${host}/icon-512.png">
<meta name="robots" content="index,follow"><meta name="theme-color" content="#14213D">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="48x48" href="/icon-48.png"><link rel="icon" type="image/png" sizes="96x96" href="/icon-96.png"><link rel="icon" type="image/png" sizes="144x144" href="/icon-144.png"><link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png"><link rel="icon" type="image/png" sizes="512x512" href="/icon-512.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt"><link rel="alternate" type="application/json" href="/facts.json" title="facts.json">
<script type="application/ld+json">${JSON.stringify(ld)}</script>
<style>body{font-family:'IBM Plex Sans',system-ui,sans-serif;max-width:78ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.55;background:#fff}h1{font-size:1.4rem;line-height:1.3}h2{font-size:1.05rem;margin-top:1.8rem;border-top:1px solid #E5E7EB;padding-top:.8rem}code,pre{background:#f3f4f6}code{padding:.1em .3em}pre{padding:.7rem;overflow:auto;font-size:.85rem}a{color:#0B6E4F}dl{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1rem}dt{font-family:ui-monospace,monospace;color:#6B7280}dd{margin:0}form{margin:.8rem 0}label{display:block;margin:.4rem 0}input,textarea{width:100%;max-width:40ch;padding:.35rem;border:1px solid #9CA3AF;font:inherit}button{padding:.4rem .9rem;border:1px solid #14213D;background:#14213D;color:#fff;font:inherit}footer{margin-top:2rem;padding-top:.75rem;border-top:1px solid #E5E7EB;color:#6B7280;font-size:.9rem}.lead{font-size:1.02rem}</style></head><body>`;
}
function footer(host) { return `<footer>${esc(host)} · ${OPERATOR} · public-record only · <a href="/llms.txt">llms.txt</a> · <a href="/facts.json">facts.json</a> · <a href="/.well-known/agent-card.json">agent-card.json</a> · <a href="/sitemap.xml">sitemap</a> · <a href="${CORPORATE}">allooloo.io</a></footer></body></html>`; }
function form(host) {
  return `<form action="${FORM}" method="POST"><input type="hidden" name="_subject" value="${esc(host)} contact"><input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off"><input type="hidden" name="_next" value="${CORPORATE}">
<label>email <input type="email" name="email" required></label><label>message <textarea name="message" rows="4" required></textarea></label><button type="submit">send</button></form>`;
}
function headers(meta, extra) {
  return { 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
    'X-CMR-Node': meta.node || 'estate', 'X-CMR-As-Of': meta.as_of || '', 'X-CMR-Version': String(meta.version || ''), 'X-CMR-Source': 'public-record', 'X-CMR-Operator': OPERATOR, ...(extra || {}) };
}
const html = (body, meta) => new Response(body, { headers: headers(meta, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' }) });
const text = (body, meta, ct, cache) => new Response(body, { headers: headers(meta, { 'content-type': ct || 'text/plain; charset=utf-8', 'cache-control': cache || 'public, max-age=300' }) });
const json = (obj, meta, cache) => new Response(JSON.stringify(obj, null, 1), { headers: headers(meta, { 'content-type': 'application/json; charset=utf-8', 'cache-control': cache || 'public, max-age=300', 'access-control-allow-origin': '*' }) });
function sitemap(host, paths) { return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${paths.map(p => `<url><loc>https://${host}${p}</loc></url>`).join('')}</urlset>\n`; }
const dl = rows => `<dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`;
const num = (n, items) => dl(items.map((v, i) => [`${n}.${i + 1}`, v]));

// ---------- node surfaces
function fill(s, v) { return String(s).replace(/\{\{issuers\}\}/g, v.issuers).replace(/\{\{events\}\}/g, v.events).replace(/\{\{drop\}\}/g, v.drop); }
function nodeVals(cc, live) {
  const n = live[`${cc}-cm-kg`] || {}; const isLive = !!n.live;
  return { live: isLive, issuers: isLive ? int(n.records) : (cc === 'hk' ? 'not served (Width 0)' : ''), events: isLive ? int(n.events) : (cc === 'hk' ? 'none (Width 0)' : ''), drop: isLive ? (n.as_of || '') : '', exchanges: n.exchanges || [], version: isLive ? 1 : '' };
}
function nodePage(host, cc, live) {
  const d = NODE_DATA[cc]; const v = nodeVals(cc, live); const node = `${cc}-cm-kg`; const ex = EXAMPLES[cc]; const partner = !!d.partner;
  const title = d.title; const desc = fill(d.meta, v); const codes = d.idForms.map(x => `<code>${esc(x)}</code>`).join(' · ');
  const s1 = num(1, [`Jurisdiction: ${esc(d.country)}`, `Node ID: <code>${node}</code>`, `Coverage: ${esc(d.coverage)}`, `Issuer records: <code>${esc(v.issuers)}</code>`, `Dated disclosure events: <code>${esc(v.events)}</code>`, 'Disclosure period: trailing twelve months', `Drop date: <code>${esc(v.drop || 'none')}</code>`, `Operator: ${OPERATOR}`, 'Counts and drop date are populated from the node on each render. Counts render as integers. Dates render as <code>YYYY-MM-DD</code>.']);
  const s2 = partner
    ? num(2, ['MCP endpoint: none. This node has no door at Width 0.', 'Agent Card: none.', 'Answer scope: nothing is answered on this node; the roster is held, not served.', 'Tools: none.', 'Accepted identifiers: none.', `The other eleven nodes answer through the apex router <code>${APEX}/mcp</code>; Hong Kong identifiers return not found there.`])
    : num(2, [`MCP endpoint: <code>https://mcp.${cc}-cm-kg.ai/mcp</code>`, 'Transport: <code>streamable-http</code>', `Agent Card: <code>https://agent.${cc}-cm-kg.ai</code>`, 'Agent protocol: A2A', `Answer scope: <code>${node}</code> only`, 'Tools: <code>resolve_issuer</code>; <code>get_record</code>; <code>list_aliases</code>; <code>list_events_since</code>; <code>list_nodes</code>', `Accepted identifiers: ${codes}`,
      `Request:<pre>${esc(JSON.stringify({ tool: 'resolve_issuer', arguments: { identifier: d.example } }, null, 2))}</pre>`, `Response (captured from the wire ${esc(ex ? ex.captured : '')}):<pre>${esc(JSON.stringify(ex ? ex.response : { note: 'no capture' }, null, 2))}</pre>`]);
  const s3 = num(3, [`Storage region: Azure ${esc(d.region)}${partner ? ' — no store; the roster is held in the build pond only' : ` (${esc(d.city)})`}`, `Serving region: ${partner ? 'none' : `Azure ${esc(d.region)} (${esc(d.city)})`}`, 'Apex router: <code>mcp.capitalmarketsknowledgegraph.ai</code>', 'Apex content: index only', 'The apex router forwards requests to the jurisdictional node.', 'No record body leaves the jurisdiction.', 'No-fallback rule: records are not served from another jurisdiction when this node is unavailable.']);
  const s4 = num(4, [`Sources of record: ${esc(d.sources)}.`, `Field-class source mapping: ${esc(d.mapping)}.`, 'Source URL: carried on every field.', 'Read date: carried on every field.', 'Read-date format: <code>YYYY-MM-DD</code>.', 'Record <code>as_of</code> and field read dates remain separate fields.', 'Every field carries source URL and read date; none is served without both.', 'Confirmed: the field as read from its source of record.', 'Signed: reserved for CMR signing; not yet in service. Not used on this node.']);
  const s5 = num(5, [`${esc(d.gaps)} <span style="color:#6B7280">(carried from: ${esc(d.gapsFrom)})</span>`]);
  const s6 = num(6, [`Exchange tiers: ${esc(d.tiers)}`, `Filing language: ${esc(d.language)}`, `Regulator: ${esc(d.regulator)}`, `Corporate register: ${esc(d.register)}`, `Disclosure channel: ${esc(d.channel)}`, `Fiscal-year convention: ${esc(d.fiscal)}`, `Identifier forms accepted by the door: ${codes}`, esc(d.auditorLine), `Duty served by the record in this market: ${esc(d.duty)}`]);
  const s7 = num(7, ORDER.filter(x => x !== cc).map(x => { const o = NODE_DATA[x]; const ov = nodeVals(x, live); return x === 'hk' ? `<code>hk-cm-kg</code> · Width 0 · no endpoint · local partner wanted · <a href="https://hk-cm-kg.ai/">hk-cm-kg.ai</a>` : `<code>${x}-cm-kg</code> · ${esc(o.region)} · <code>https://mcp.${x}-cm-kg.ai/mcp</code> · ${ov.live ? `${ov.issuers} records · ${ov.events} events` : 'door not live'} · <a href="https://${x}-cm-kg.ai/">${x}-cm-kg.ai</a>`; }));
  const s8 = num(8, ['Machine instructions: <a href="/llms.txt"><code>/llms.txt</code></a>', 'Facts: <a href="/facts.json"><code>/facts.json</code></a>', partner ? 'Agent Card: none (no door). <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a> on this host states that.' : `Agent Card: <a href="https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json"><code>https://agent.${cc}-cm-kg.ai</code></a> (pointer at <code>/.well-known/agent-card.json</code> on this host)`, `Registry: <code>${REGISTRY}</code>`, partner ? 'Door descriptors: none.' : `Door descriptors: <a href="https://mcp.${cc}-cm-kg.ai/mcp.json"><code>mcp.json</code></a> · <a href="https://mcp.${cc}-cm-kg.ai/openapi.json"><code>openapi.json</code></a> (pointers at <code>/mcp.json</code> and <code>/openapi.json</code> here)`, 'Also on this host: <a href="/.well-known/security.txt"><code>/.well-known/security.txt</code></a> · <a href="/sitemap.xml"><code>/sitemap.xml</code></a> · <a href="/robots.txt"><code>/robots.txt</code></a>']);
  const s9 = num(9, [`<a href="mailto:${CONTACT}">${CONTACT}</a> — contact of record`, `<a href="mailto:${CONTACT2}">${CONTACT2}</a> — the agents that built this read their own mail`, `Form: ${form(host)}`]);
  const body = `<h1>${esc(d.h1)}</h1><p class="lead">${esc(fill(d.reason, v))}</p>
<h2>1 Scope</h2>${s1}<h2>2 Access</h2>${s2}<h2>3 Residency</h2>${s3}<h2>4 Provenance</h2>${s4}<h2>5 Known gaps</h2>${s5}<h2>6 Market particulars</h2>${s6}<h2>7 Estate</h2>${s7}<h2>8 Machine kit</h2>${s8}<h2>9 Contact</h2>${s9}`;
  const ld = [{ '@context': 'https://schema.org', '@type': 'Dataset', name: title, description: desc, url: `https://${host}/`, creator: { '@type': 'Organization', name: OPERATOR, url: CORPORATE }, license: 'public-record only', spatialCoverage: d.country, ...(v.live ? { distribution: [{ '@type': 'DataDownload', encodingFormat: 'application/json', contentUrl: `https://mcp.${cc}-cm-kg.ai/mcp` }] } : {}) }];
  return head(host, title, desc, ld) + body + footer(host);
}
function nodeFacts(host, cc, live) {
  const d = NODE_DATA[cc]; const v = nodeVals(cc, live); const node = `${cc}-cm-kg`;
  return { domain: host, kind: 'node surface', node, country: d.country, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: today(), source: 'public-record', live: v.live, issuer_records: v.live ? Number(v.issuers) : null, disclosure_events: v.live ? Number(v.events) : null, drop_date: v.drop || null, width: d.partner ? 0 : null,
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
    '11. Rules: public-record only; no prices, quotes or licensed market data; blank stays blank; nothing published before it answers; counts and dates are live from list_nodes, never typed.'].join('\n') + '\n';
}
function nodeCard(host, cc, live) {
  const d = NODE_DATA[cc]; const v = nodeVals(cc, live); const node = `${cc}-cm-kg`;
  if (d.partner) return { name: `${d.country} node — Capital Markets Knowledge Graph (surface)`, description: `Surface of ${node}. No door and no agent at Width 0; local partner wanted. This host answers nothing itself.`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, capabilities: {}, skills: [], version: '0', contact: CONTACT };
  return { name: `${d.country} node — Capital Markets Knowledge Graph (surface pointer)`, description: `Surface of ${node}: ${v.issuers} issuer records, ${v.events} dated disclosure events as of ${v.drop}. The node's agent is at https://agent.${cc}-cm-kg.ai; its MCP door is https://mcp.${cc}-cm-kg.ai/mcp. This host is documentation only.`,
    url: `https://mcp.${cc}-cm-kg.ai/mcp`, agentCard: `https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, version: String(v.version || 1), protocolVersion: '0.3', capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'],
    skills: [{ id: 'pointer', name: 'Where the node answers', description: `Resolve, read, alias, event and node listing calls for ${d.country} go to the node door; see agentCard.`, tags: ['capital-markets', cc] }], contact: CONTACT };
}
function nodePointer(kind, cc) { return { pointer: true, node: `${cc}-cm-kg`, [kind]: `https://mcp.${cc}-cm-kg.ai/${kind}.json`, note: 'this host is the node surface; the door descriptor is served by the door' }; }

// ---------- agentic quiet zones
function agenticPage(host, p) {
  const a = AGENTIC[p]; const title = `${a.name} — Allooloo`; const desc = a.line;
  return head(host, title, desc) + `<h1>${esc(a.name)}</h1><p class="lead">${esc(a.line.replace(' Corporate: https://allooloo.io', ''))}</p>
${num(1, [`Operator: ${OPERATOR}`, `Corporate: <a href="${CORPORATE}">${CORPORATE.replace('https://', '')}</a>`, `Canonical host: <code>https://agentic-${p}.ai/</code> (.com, .org and .io forward here)`, 'State: live, open to crawlers, kitted; product page follows under its own order.', `Estate: Capital Markets Knowledge Graph — apex <code>${APEX}/mcp</code>, twelve market nodes.`, 'Machine kit: <a href="/llms.txt"><code>/llms.txt</code></a> · <a href="/facts.json"><code>/facts.json</code></a> · <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a> · <a href="/.well-known/security.txt"><code>/.well-known/security.txt</code></a> · <a href="/sitemap.xml"><code>/sitemap.xml</code></a> · <a href="/robots.txt"><code>/robots.txt</code></a>', `Contact: <a href="mailto:${CONTACT}">${CONTACT}</a>`])}
<h2>Contact</h2>${form(host)}` + footer(host);
}
function agenticFacts(host, p, live) {
  const a = AGENTIC[p]; const ln = Object.values(live).filter(n => n.live);
  return { domain: host, kind: 'product surface (quiet zone)', product: a.name, description: a.line, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, canonical: `https://agentic-${p}.ai/`, as_of: today(), source: 'public-record', estate: 'Capital Markets Knowledge Graph (CM-KG)', apex: `${APEX}/mcp`, live_nodes: ln.map(n => n.node), issuer_records_live: ln.reduce((s, n) => s + (n.records || 0), 0), disclosure_events_live: ln.reduce((s, n) => s + (n.events || 0), 0), counts_from: 'list_nodes (live on each render)', machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'] };
}
function agenticCard(host, p) { const a = AGENTIC[p]; return { name: `${a.name} — Allooloo`, description: `${a.line} No agent endpoint on this host yet; the Capital Markets Knowledge Graph apex agent is at ${APEX_AGENT}.`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, capabilities: {}, skills: [], version: '0', contact: CONTACT, estate_agent_card: `${APEX_AGENT}/.well-known/agent-card.json` }; }
function agenticLlms(host, p, live) { const a = AGENTIC[p]; return [`# ${host} — ${a.name}`, `1. ${a.line}`, `2. Operator: ${OPERATOR}. Contact: ${CONTACT}. Canonical: https://agentic-${p}.ai/ (.com .org .io forward here).`, `3. Estate: Capital Markets Knowledge Graph; apex door ${APEX}/mcp; apex Agent Card ${APEX_AGENT}/.well-known/agent-card.json; live nodes: ${Object.values(live).filter(n => n.live).map(n => n.node).join(', ') || 'none'}.`, '4. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt', '5. Rules: public-record only; no prices; nothing published before it answers.'].join('\n') + '\n'; }

// ---------- roots and record hosts (carried from the previous Worker, kit added)
function rootFacts(host, c, live) {
  const base = { domain: host, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: today(), source: 'public-record', estate: 'Capital Markets Knowledge Graph (CM-KG)', machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'], counts_from: 'list_nodes (live on each render)' };
  const ln = Object.values(live);
  if (c.kind === 'root') return { ...base, kind: { graph: 'root of the graph', standard: 'standard mirror of the long-form root', 'cmkg-standard': 'CM-KG standard and beacon', 'cmkg-twin': 'CM-KG machine twin' }[c.role], live_nodes: ln.filter(n => n.live).map(n => n.node), global_door: `${APEX}/mcp`, apex_agent_card: `${APEX_AGENT}/.well-known/agent-card.json`, nodes: ORDER.map(cc => { const n = live[`${cc}-cm-kg`] || {}; return { node: `${cc}-cm-kg`, country: NODE_DATA[cc].country, live: !!n.live, records: n.live ? n.records : 0, events: n.live ? n.events : 0, as_of: n.live ? n.as_of : null, surface: `https://${cc}-cm-kg.ai/` }; }) };
  return { ...base, kind: { standard: 'Capital Markets Record — the object standard (schema, signing, versions)', resolver: 'CMR resolver door', twin: 'CMR machine twin' }[c.role], spec: 'CMR v0 (draft)', signing: 'not yet live; no signature is stubbed', resolver_live: false, records_served_by: `${APEX}/mcp` };
}
function rootPage(host, c, f) {
  let title, body;
  if (c.kind === 'root') {
    title = { graph: 'Capital Markets Knowledge Graph', standard: 'Capital Markets Knowledge Graph — standard', 'cmkg-standard': 'CM-KG — standard and beacon', 'cmkg-twin': 'CM-KG — machine twin' }[c.role];
    body = `<h1>${esc(title)}</h1><p class="lead">${esc(f.kind)}. Issuers as nodes; insiders, holders, auditors, transfer agents, parents and subsidiaries, dual listings and newswires as edges. Twelve sovereign market nodes, one apex router that holds an index and forwards. Public-record only.</p>
<p><strong>Live nodes: ${f.live_nodes.length ? esc(f.live_nodes.join(', ')) : 'none'}.</strong> The apex answers at <code>${esc(f.global_door)}</code> (Streamable HTTP MCP, no auth) and forwards by identifier to the node that holds the name.</p>
${dl(f.nodes.map((n, i) => [String(i + 1), `${esc(n.country)} — <code>${esc(n.node)}</code> — ${n.live ? `live · ${int(n.records)} records · ${int(n.events)} events · as of ${esc(n.as_of)}` : 'not live'} · <a href="${n.surface}">${esc(n.surface.replace('https://', '').replace(/\/$/, ''))}</a>`]))}
<p><a href="${APEX}/">Apex door</a> · <a href="${APEX_AGENT}/.well-known/agent-card.json">Apex Agent Card</a> · <a href="${CORPORATE}/">${OPERATOR}</a></p><h2>Contact</h2>${form(host)}`;
  } else {
    title = { standard: 'Capital Markets Record — the standard', resolver: 'Capital Markets Record — resolver', twin: 'Capital Markets Record — machine twin' }[c.role];
    body = `<h1>${esc(title)}</h1><p class="lead">${esc(f.kind)}. One record per listed company, keyed on ISIN, ticker and LEI. Versioned, sourced, never deleted; every field names the registry it came from or the engine that read it and carries a state.</p>
<p><strong>Status: ${c.role === 'resolver' ? 'resolver not live' : 'draft standard (CMR v0)'}.</strong> Signing is not yet live and no signature is stubbed. Records are served today by the apex at <code>${esc(f.records_served_by)}</code>.</p><p><a href="${APEX}/">Apex door</a> · <a href="${CORPORATE}/">${OPERATOR}</a></p><h2>Contact</h2>${form(host)}`;
  }
  return head(host, title, `${title}. Operator: ${OPERATOR}. Public-record only.`) + body + footer(host);
}
function rootLlms(host, c, f) {
  const lines = [`# ${host}`, `Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`, `What this domain is: ${f.kind}.`];
  if (c.kind === 'root') lines.push(`Live nodes: ${f.live_nodes.join(', ') || 'none'}. Apex door (Streamable HTTP MCP, no auth): ${f.global_door}. Tools: resolve_issuer, get_record, list_events_since, list_aliases, list_nodes. Node surfaces: ${ORDER.map(cc => `https://${cc}-cm-kg.ai/`).join(' ')}`);
  if (c.kind === 'record') lines.push(`Spec: ${f.spec}. Signing: ${f.signing}. Records served by ${f.records_served_by}.`);
  lines.push('Rules: public-record only; no prices, quotes or licensed market data; blank stays blank; nothing published before it answers.', 'Machine paths: /llms.txt, /facts.json, /.well-known/agent-card.json, /.well-known/security.txt, /sitemap.xml, /robots.txt');
  return lines.join('\n') + '\n';
}
function rootCard(host, c, f) { return { name: `${host} — Allooloo`, description: `${f.kind}. This host is documentation; the estate agent is at ${APEX_AGENT}.`, url: c.kind === 'root' ? `${APEX}/mcp` : undefined, agentCard: `${APEX_AGENT}/.well-known/agent-card.json`, provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, capabilities: {}, skills: [], version: '0', contact: CONTACT }; }

export default {
  async fetch(request, env) {
    const url = new URL(request.url); const host = url.hostname; const c = classify(host); const apex = host.replace(/^www\./, '');
    if (c.kind === 'redirect' || c.canonical) return Response.redirect(c.canonical + url.pathname + url.search, 301);
    if (host !== apex) return Response.redirect(`https://${apex}${url.pathname}${url.search}`, 301);
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405, headers: headers({}, { 'content-type': 'text/plain' }) });
    const p = url.pathname.replace(/\/+$/, '') || '/';
    if (ICONS.includes(p)) { const a = await env.ASSETS.fetch(new Request(url.origin + p)); const h = new Headers(a.headers); for (const [k, v] of Object.entries(headers({}))) h.set(k, v); h.set('cache-control', 'public, max-age=86400'); return new Response(a.body, { status: a.status, headers: h }); }
    if (p === '/robots.txt') return text(ROBOTS(host), {}, 'text/plain; charset=utf-8', 'public, max-age=86400');
    if (p === '/.well-known/security.txt') return text(SECURITY(host), {}, 'text/plain; charset=utf-8', 'public, max-age=86400');
    const live = await liveNodes();
    if (c.kind === 'node') {
      const cc = c.cc; const v = nodeVals(cc, live); const meta = { node: `${cc}-cm-kg`, as_of: v.drop || today(), version: v.version };
      const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt'].concat(NODE_DATA[cc].partner ? [] : ['/mcp.json', '/openapi.json']);
      if (p === '/') return html(nodePage(host, cc, live), meta);
      if (p === '/llms.txt') return text(nodeLlms(host, cc, live), meta);
      if (p === '/facts.json') return json(nodeFacts(host, cc, live), meta);
      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(nodeCard(host, cc, live), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      if ((p === '/mcp.json' || p === '/openapi.json') && !NODE_DATA[cc].partner) return json(nodePointer(p.slice(1, -5), cc), meta);
      return json({ error: 'not_found', paths }, meta, 'no-store');
    }
    if (c.kind === 'agentic') {
      const meta = { node: 'estate', as_of: today() }; const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
      if (p === '/') return html(agenticPage(host, c.product), meta);
      if (p === '/facts.json') return json(agenticFacts(host, c.product, live), meta);
      if (p === '/llms.txt') return text(agenticLlms(host, c.product, live), meta);
      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(agenticCard(host, c.product), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      return json({ error: 'not_found', paths }, meta, 'no-store');
    }
    if (c.kind === 'root' || c.kind === 'record') {
      const f = rootFacts(host, c, live); const meta = { node: c.kind === 'root' ? 'global' : 'cm-record', as_of: f.as_of }; const paths = ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
      if (p === '/') return html(rootPage(host, c, f), meta);
      if (p === '/llms.txt') return text(rootLlms(host, c, f), meta);
      if (p === '/facts.json') return json(f, meta);
      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(rootCard(host, c, f), meta);
      if (p === '/sitemap.xml') return text(sitemap(host, paths), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
      return json({ error: 'not_found', paths }, meta, 'no-store');
    }
    return json({ error: 'not_found', note: 'an Allooloo Technologies Corp. domain with no page of its own', corporate: CORPORATE }, {}, 'no-store');
  }
};
