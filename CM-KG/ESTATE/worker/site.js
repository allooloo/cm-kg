// ORDER-020 §4 (as amended Sept 12 2026: §4.0 page order, §5.0 title rule, §12 Toronto and London) + §3 record pages + §6 Status.
// allooloo.io: head → H1 → scale block (five live numbers) → reason-for-being → products → twelve-node table → licence shapes → engines and duties → Proof → contact.
// The sample record is one link in Proof → /record (a live get_record from the Canada door on its own page). Regions are never abbreviated.
import { APEX, APEX_AGENT, CONTACT, CONTACT2, LEGAL, OPERATOR, KICKER, REGION_FULL, REGIONS_LIST, esc, int, num, table, form, scale } from './chrome.js';
import { ORDER, DUTY, LICENCES, nodesTable, totals, PRODUCTS } from './products.js';

const HERO_ID = 'TSX:SHOP';   // the Canada node's section-2 example issuer; fetched from the Canada door at render (§4.1)
let HERO = null, HERO_AT = 0;
export async function heroRecord() {
  if (HERO && Date.now() - HERO_AT < 300000) return HERO;
  try {
    const r = await fetch('https://mcp.ca-cm-kg.ai/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'get_record', arguments: { identifier: HERO_ID } } }) });
    const j = await r.json(); const s = j.result && j.result.structuredContent; if (s && s.cmr) { HERO = s; HERO_AT = Date.now(); }
  } catch (e) { /* the block states the miss */ }
  return HERO;
}
function srcCell(u) { if (!u) return ''; const show = u.replace(/^https?:\/\//, ''); return `<a class="src" href="${esc(u)}" rel="noopener">${esc(show.length > 64 ? show.slice(0, 61) + '…' : show)}</a>`; }
export function recordBlock(rec) {
  if (!rec) return `<div class="record"><div class="head"><span>Capital Markets Record</span><span>Canada door did not answer at render — no record shown (a block that cannot show a source does not go on the page)</span></div></div>`;
  const idn = rec.identity || {}; const rows = Object.keys(idn).map(k => { const f = idn[k] || {}; return [`<code>${esc(k)}</code>`, esc(f.value || '') + (f.note && !f.value ? `<span class="muted"> — ${esc(f.note)}</span>` : ''), srcCell(f.source_url), esc(f.read_by || ''), `<code>${esc(f.state || '')}</code>`]; });
  return `<div class="record" id="cmr"><div class="head"><span>Capital Markets Record · <code>${esc(rec.cmr)}</code></span><span>version ${esc(rec.version)} · as of ${esc(rec.as_of)} · served by <code>mcp.ca-cm-kg.ai</code> from ${esc(REGION_FULL.ca)} at render</span></div>
<div class="issuer">${esc((idn.name || {}).value || '')}</div><div class="wrap">${table(['field', 'value', 'source', 'read by', 'state'], rows)}</div>
<p class="muted">Aliases: ${(rec.aliases || []).length} · events on the record: ${int(rec.event_count)} (<a href="${esc(rec.events_url || '')}">events</a>) · gaps: ${(rec.gaps || []).map(g => `${esc(g.field)} — ${esc(g.reason)}`).join('; ') || 'none'}. Call of record: <code>get_record · ${esc(HERO_ID)}</code> at <code>https://mcp.ca-cm-kg.ai/mcp</code>.</p></div>`;
}
export const REASON = 'Allooloo builds the Capital Markets Knowledge Graph for the dealers, brokers and wealth platforms of Toronto and London, and serves it from eleven markets: one record per listed company on the exchanges of Canada, the United States, the United Kingdom, France, the Netherlands, Switzerland, Germany, Australia, Singapore, Japan and Korea, with Hong Kong as a beacon. Every field carries the registry or filing it came from and the date it was read. Records are stored and served in the issuer\'s own jurisdiction; an apex router holds an index and forwards, nothing more. Agents call it over MCP and A2A; a desk, a watchlist, an ESG slice, an issuer record, the disclosure trail, a registry of agents and a live numbers page are built on it. Public record only. No prices, no quotes, no licensed data.';
export function scaleBlock(ctx) { const t = totals(ctx); return scale([[int(t.records), 'listed companies', 'list_nodes'], [int(t.events), 'dated disclosures, trailing twelve months', 'list_nodes'], [`${t.nodes}`, 'markets · 11 Azure regions · served in-country', 'list_nodes'], ['100%', 'fields carrying source URL and read date', 'the record shape'], [esc(t.last), 'last drop', 'list_nodes']]); }
export function homeMeta(ctx) { const t = totals(ctx); return `${int(t.records)} listed companies, ${int(t.events)} dated disclosures, eleven markets served in-country. Every field sourced and read-dated. MCP and A2A for AI agents.`; }

export function homeBody(ctx, host) {
  return `${scaleBlock(ctx)}
<p class="lead">${esc(REASON)}</p>
<h2>1 Products</h2>${num(1, Object.keys(PRODUCTS).map(k => `<a href="https://agentic-${k}.ai/"><code>${esc(PRODUCTS[k].title)}</code></a>`))}
<h2>2 The twelve nodes</h2>${nodesTable(ctx)}
<h2>3 Licence</h2><p>Four things a dealer, bank or broker can sign. No services. Ever.</p>${num(3, LICENCES.map(([n, l]) => `<code>${esc(n)}</code>: ${esc(l)}.`))}<p>You license. You operate. We do not consult, integrate, or run your motion.</p>
<h2>4 Engines and duties</h2><p>Eight engines. Named duties. Human cut. Claude reads and adjudicates. ChatGPT extracts at scale. Gemini reads whole filings. Perplexity grounds the cold read. Grok carries the live signal. Mistral reads the European nodes in their own languages. Tavily is the net. Cloudflare is the network. No engine is trusted alone. Every field carries who read it. A person cuts the record before it is confirmed.</p>
<p>The duty the record serves, by market: ${ORDER.map(cc => `${esc(ctx.nodes[cc].country)} — ${esc(DUTY[cc])}`).join('; ')}.</p>
<h2>5 Proof</h2><p class="kicker">${esc(KICKER)}</p>${num(5, [`Served in-country from ${esc(REGIONS_LIST)}.`, 'Public-record only: exchange lists, corporate registers, GLEIF, EDGAR, EDINET, DART, RNS, AMF, AFM, SIX, Xetra, ASX, SGX and their peers; source URL and read date on every field; blank stays blank.', 'What a record looks like: <a href="/record">a live record from the Canada door</a>, rendered on its own page.', 'Every door probed every five minutes: <a href="/status">allooloo.io/status</a>. The estate numbers: <a href="https://agentic-radar.ai/">agentic-radar.ai</a> · <a href="https://agentic-radar.ai/radar.json">radar.json</a>.', `Registry entry: <code>registry.modelcontextprotocol.io · io.github.allooloo/cm-kg</code>; apex Agent Card <code>${APEX_AGENT}/.well-known/agent-card.json</code>.`])}
<h2>6 Contact</h2><p>Tell us what you trade.</p>${form(host)}<p class="muted">The agents that built this read their own mail: ${CONTACT2}. Support: ${CONTACT}. ${OPERATOR} · Vancouver, Canada.</p>`;
}
export function recordPageBody(rec) { return `<p class="lead">One Capital Markets Record, as the Canada door serves it at render: every field with its value, the source it was read from, the reader and its state. This is the shape of every record on the estate.</p>${recordBlock(rec)}<p><a href="/">Back to allooloo.io</a> · <a href="https://ca-cm-kg.ai/">the Canada node</a> · <a href="https://mcp.ca-cm-kg.ai/openapi.json">openapi.json</a></p>`; }

// ---------- the record pages (§3)
export const PAGES = {
  terms: { title: 'Terms of Use — Allooloo', h1: 'Terms of Use', state: 'draft', body: () => `<p class="muted">Draft as of 2026-09-12 · version 0.1 · to be signed by ${LEGAL}. Until signed, these terms are the operator\'s stated practice, not a signed instrument.</p>
${num(1, ['Operator: ' + OPERATOR + ', Vancouver, Canada. Contact: ' + CONTACT + '.', 'Surfaces covered: allooloo.io, the twelve node surfaces (<code>&lt;cc&gt;-cm-kg.ai</code>), the eight product surfaces (<code>agentic-*.ai</code>), the doors (<code>mcp.*</code>, <code>agent.*</code>) and the apex.', 'What is served: public-record data — records and dated disclosure events read from exchanges, regulators, registers and filings — with the source and read date on every field. No prices, quotes or licensed market data.', 'Reading: the public doors may be read by any person or agent, without registration, for any lawful purpose, under the rate the door states (Streamable HTTP, no auth).', 'Redistribution: a field may be redistributed with its source URL and read date attached; a field stripped of its source is not a Capital Markets Record.', 'Licences: Dealer MCP access, Issuer record, Knowledge Graph API and Node operator are licence shapes signed separately; nothing on these surfaces grants one. Licence only, no services.', 'No warranty beyond the source: the operator serves what the source of record said on the read date; the source, not the operator, is the authority for the fact. Gaps are stated on the record.', 'Nothing deleted: records are versioned and superseded; prior renders and drops are kept.', 'Changes: these terms carry an <code>as of</code> date and a version; prior versions stay in the pond and can be read on request.', 'Law: British Columbia, Canada.'])}` },
  privacy: { title: 'Privacy — Allooloo', h1: 'Privacy', state: 'draft', body: () => `<p class="muted">Draft as of 2026-09-12 · version 0.1 · to be signed by ${LEGAL}.</p>
${num(1, ['No cookies are set by any Allooloo surface. No third-party scripts, analytics tags, fonts from a CDN, chat widgets or trackers are loaded.', 'Cloudflare edge logs are the only analytics: request counts by hostname and region, retained by Cloudflare under its terms; no personal profile is built from them.', 'The contact form posts to Formspree (the form processor of record); the fields sent are the email address and message typed, plus the hostname the form was on. Formspree holds them under its terms and forwards them to ' + CONTACT + '.', 'Door calls: the apex and the regional doors log the request path, the identifier asked and the region; when the Registries layer is in service, a registered agent\'s calls are receipted in the region of the call and readable by the firm that made them.', 'Records served are public-record data about listed companies, not about persons; where a filing names a director or officer, the record carries the filing\'s reference, not a profile.', 'Requests about personal data: ' + CONTACT + '.'])}` },
  security: { title: 'Report a Security Issue — Allooloo', h1: 'Report a Security Issue', state: 'record', body: () => `${num(1, ['Report to <a href="mailto:' + CONTACT + '">' + CONTACT + '</a>. Machine-readable: <a href="/.well-known/security.txt"><code>/.well-known/security.txt</code></a> on every zone.', 'Scope: allooloo.io, <code>*-cm-kg.ai</code> (surfaces, <code>mcp.</code> and <code>agent.</code> hosts), <code>agentic-*.ai</code>, <code>capitalmarketsknowledgegraph.ai</code>, <code>cm-record.org</code> and the Azure origins behind the doors.', 'What to send: the host, the path, the request that shows the issue, the date and time (UTC), and how to reach you.', 'What happens: the report is read within one business day; a fix is confirmed to the reporter; the surface version carries the date.', 'Headers as content: strict Content-Security-Policy, Strict-Transport-Security, X-Content-Type-Options, Referrer-Policy, X-Frame-Options, Permissions-Policy on every response; no inline scripts anywhere.', 'Preferred languages: English.'])}` },
  'no-cookies': { title: 'No cookies — Allooloo', h1: 'No cookies', state: 'record', body: () => `<p>No Allooloo surface sets a cookie. No third-party scripts, no analytics tags, no fonts from a CDN, no chat widget, no cookie banner — there is nothing to consent to. Cloudflare edge logs are the analytics: request counts by hostname and region, nothing about a person. The contact form posts to Formspree and sends only what is typed into it. Every page is under 50 KB, one CSS file, no JavaScript except the form honeypot field.</p>` }
};

// ---------- status (§6): probe results from KV
export const PROBE = { ca: 'TSX:SHOP', us: 'NASDAQ:AAPL', uk: 'LSE:SHEL', fr: 'XPAR:FR0000120271', nl: 'AMS:NL0000009165', ch: 'NESN.SW', de: 'SAP.DE', au: 'ASX:BHP', sg: 'D05.SI', jp: 'TSE-PRIME:7203', kr: 'KOSPI:005930' };
export async function readStatus(env) {
  const out = {};
  for (const cc of Object.keys(PROBE)) { try { const v = await env.STATUS.get(`node:${cc}`, 'json'); if (v) out[cc] = v; } catch (e) { /* no entry yet */ } }
  return out;
}
const median = a => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y); const m = Math.floor(s.length / 2); return s.length % 2 ? s[m] : Math.round((s[m - 1] + s[m]) / 2); };
export function statusRows(ctx, st) {
  return ORDER.map(cc => { const n = ctx.live[`${cc}-cm-kg`] || {}; const s = st[cc];
    if (cc === 'hk') return { node: `${cc}-cm-kg`, region: REGION_FULL.hk, state: 'beacon · partner wanted', last_call: null, ms: null, median_24h: null, last_drop: null, samples: 0 };
    const hist = (s && s.hist) || []; const day = hist.filter(([t]) => Date.now() - t < 86400000);
    return { node: `${cc}-cm-kg`, region: REGION_FULL[cc], state: s ? (s.ok ? 'up' : 'down') : 'no probe yet', last_call: s ? new Date(s.ts).toISOString() : null, ms: s ? s.ms : null, median_24h: median(day.map(x => x[1])), last_drop: n.as_of || null, samples: day.length, bars: day.slice(-48).map(x => x[1]) }; });
}
export function statusBody(ctx, st) {
  const rows = statusRows(ctx, st);
  const bars = r => r.bars && r.bars.length ? `<div class="bars">${r.bars.map(ms => `<i style="height:${Math.max(2, Math.min(40, Math.round(ms / 50)))}px" title="${ms} ms"></i>`).join('')}</div>` : '';
  return `<p class="lead">Every five minutes one real <code>resolve_issuer</code> (the node\'s section-2 example issuer) is sent to each of the eleven doors through its public hostname; the round trip in milliseconds is written to the edge store. One call per node per five minutes; no other polling anywhere. Machine twin: <a href="/status.json"><code>/status.json</code></a>.</p>
<div class="wrap">${table(['node', 'region', 'state', 'last call (UTC)', 'response ms', '24h median ms', 'samples 24h', 'last drop', '24h line'], rows.map(r => [`<code>${r.node}</code>`, esc(r.region), r.state === 'up' ? '<span class="pill live">up</span>' : `<span class="pill">${esc(r.state)}</span>`, esc(r.last_call ? r.last_call.slice(0, 19).replace('T', ' ') : '—'), `<span class="n">${r.ms == null ? '—' : r.ms}</span>`, `<span class="n">${r.median_24h == null ? '—' : r.median_24h}</span>`, `<span class="n">${r.samples}</span>`, esc(r.last_drop || '—'), bars(r)]))}</div>
<p class="src">source: the §6 probe (Worker cron, every five minutes) writing to KV; drop dates from list_nodes. The 24h line is the proof of warming (minimum one replica per door).</p>`;
}
export function statusJson(ctx, st) { return { as_of: new Date().toISOString(), probe: 'resolve_issuer per node every five minutes via the public hostname', source: 'estate Worker cron → KV', nodes: statusRows(ctx, st).map(r => { const { bars, ...rest } = r; return rest; }) }; }

// ---------- the scheduled probe (§6)
export async function probe(env) {
  for (const [cc, id] of Object.entries(PROBE)) {
    const t0 = Date.now(); let ok = false;
    try {
      const r = await fetch(`https://mcp.${cc}-cm-kg.ai/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json', 'user-agent': 'Allooloo status probe' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'resolve_issuer', arguments: { identifier: id } } }), signal: AbortSignal.timeout(20000) });
      const j = await r.json(); ok = !!(j.result && j.result.structuredContent && j.result.structuredContent.matches && j.result.structuredContent.matches.length);
    } catch (e) { ok = false; }
    const ms = Date.now() - t0; let prev = null;
    try { prev = await env.STATUS.get(`node:${cc}`, 'json'); } catch (e) { prev = null; }
    const hist = ((prev && prev.hist) || []).filter(([t]) => Date.now() - t < 86400000 * 2).concat([[t0, ms]]).slice(-600);
    await env.STATUS.put(`node:${cc}`, JSON.stringify({ ts: t0, ms, ok, identifier: id, hist }));
  }
}
