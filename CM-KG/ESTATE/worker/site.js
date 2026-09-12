// ORDER-020 §4 + §3 + §6 — allooloo.io as the thirteenth surface: live hero record from the Canada door, live numbers block, the record pages
// (Terms, Privacy, Security, No cookies), Status (/status, /status.json) from the §6 probe in KV. Record-grade register; nothing typed that a door can give.
import { APEX, APEX_AGENT, CONTACT, CONTACT2, LEGAL, OPERATOR, REGIONS, esc, int, num, table, form } from './chrome.js';
import { ORDER, DUTY, LICENCES, nodesTable, tiles, totals } from './products.js';

const HERO_ID = 'TSX:SHOP';   // the Canada node's §2 example issuer; the record is fetched from the Canada door at render (§4.1)
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
export function heroBlock(rec) {
  if (!rec) return `<div class="record"><div class="head"><span>Capital Markets Record</span><span>Canada door did not answer at render — no record shown (a block that cannot show a source does not go on the page)</span></div></div>`;
  const idn = rec.identity || {}; const rows = Object.keys(idn).map(k => { const f = idn[k] || {}; return [`<code>${esc(k)}</code>`, esc(f.value || '') + (f.note && !f.value ? `<span class="muted"> — ${esc(f.note)}</span>` : ''), srcCell(f.source_url), esc(f.read_by || ''), `<code>${esc(f.state || '')}</code>`]; });
  return `<div class="record" id="cmr"><div class="head"><span>Capital Markets Record · <code>${esc(rec.cmr)}</code></span><span>version ${esc(rec.version)} · as of ${esc(rec.as_of)} · served by <code>mcp.ca-cm-kg.ai</code> at render</span></div>
<div class="issuer">${esc((idn.name || {}).value || '')}</div><div class="wrap">${table(['field', 'value', 'source', 'read by', 'state'], rows)}</div>
<p class="muted">Aliases: ${(rec.aliases || []).length} · events on the record: ${int(rec.event_count)} (<a href="${esc(rec.events_url || '')}">events</a>) · gaps: ${(rec.gaps || []).map(g => `${esc(g.field)} — ${esc(g.reason)}`).join('; ') || 'none'}. Record as data: <code>get_record · ${esc(HERO_ID)}</code> at <code>https://mcp.ca-cm-kg.ai/mcp</code>.</p></div>`;
}

export function homeBody(ctx, host, rec) {
  const t = totals(ctx);
  return `<p class="lead">Allooloo builds the Capital Markets Knowledge Graph and serves Capital Markets Records to AI agents over MCP and A2A: one record per listed company, source and read date on every field, stored and served in the issuer's jurisdiction. Eleven doors live; Hong Kong a beacon with a partner wanted. Licence only, no services.</p>
<h2>1 The record</h2><p>One record per listed company. Keyed on ISIN, ticker and LEI. Versioned, sourced, never deleted. Every field names the registry it came from or the engine that read it, and the day it was read.</p>${heroBlock(rec)}
<h2>2 The numbers</h2>${tiles(ctx)}<p class="src">issuers, events, nodes live and last drop are read from <code>list_nodes</code> at ${esc(APEX)}/mcp on every render</p>
<h2>3 The desk</h2><p>Ask about any listed company in the markets you trade. <a href="https://ask.allooloo.io/">ask.allooloo.io</a> is one door over the nodes: the identifier does the routing — a TSX name opens the Canada node, a Xetra name opens the German node, in German if you asked in German. Default scope is the market the name belongs to. Cross-border — dual listings, foreign parents, the holder who is in three of your markets — is there when it's the question.</p>
<p>Built for the duty a dealer cannot decline: know every product on the shelf, continuously. KYP in Canada, product governance in London and Frankfurt, reasonable-basis suitability in New York, DDO in Sydney, product due diligence in Singapore. Same record, twelve names.</p>
<h2>4 The graph</h2><p>Issuers as nodes. Insiders across boards, holders across names, auditors and transfer agents shared, parents and subsidiaries, dual listings across markets, the newswire each issuer actually uses. Served live to AI agents over MCP.</p>
<p>Twelve nodes: eleven doors, each a public registry served in its own jurisdiction; Hong Kong a beacon at Width 0 with a local partner wanted.</p>${nodesTable(ctx)}
<p>Public-record only: SEDAR+, SEDI, Companies House, RNS, ASX, SGX, SIX, Xetra, EDGAR, EDINET, DART and their peers. No prices. No quotes. No licensed market data. Nothing on the wire a data licence could pull back.</p>
<h2>5 The orchestra</h2><p>Eight engines. Named duties. Human cut. Claude reads and adjudicates. ChatGPT extracts at scale. Gemini reads whole filings. Perplexity grounds the cold read. Grok carries the live signal. Mistral reads the European nodes in their own languages. Tavily is the net. Cloudflare is the network.</p><p>No engine is trusted alone. Every field carries who read it. A person cuts the record before it is confirmed.</p>
<h2>6 Licence</h2><p>Four things a dealer, bank or broker can sign. No services. Ever.</p>${num(6, LICENCES.map(([n, l]) => `<code>${esc(n)}</code>: ${esc(l)}.`))}<p>You license. You operate. We do not consult, integrate, or run your motion.</p>
<h2>7 In production</h2>${num(7, [`${int(t.records)} issuer records and ${int(t.events)} dated disclosure events served from ${t.nodes} doors at render (list_nodes); last drop ${esc(t.last)}.`, 'Eight engines orchestrated, gated, adjudicated; every enriched field carries a source and a reader.', 'Estate on Microsoft Azure Container Apps in eleven regions, in-country; the apex router on Cloudflare, index only. MCP and A2A end to end.', 'Status of every door, five-minute probe: <a href="/status">allooloo.io/status</a>. The estate numbers: <a href="https://agentic-radar.ai/">agentic-radar.ai</a>.'])}
<h2>8 Products</h2>${num(8, [['Agentic Trades', 'https://agentic-trades.ai/', 'the product line, mapped'], ['ASK', 'https://agentic-ask.ai/', 'the desk'], ['Coverage', 'https://agentic-coverage.ai/', 'a watchlist that reads the record'], ['ESG', 'https://agentic-esg.ai/', 'the sustainability slice of the trail'], ['Issuers', 'https://agentic-issuers.ai/', 'the issuer\'s own record'], ['Disclosure', 'https://agentic-disclosure.ai/', 'the trail as a product'], ['Registries', 'https://agentic-registries.ai/', 'who may call, and what they did'], ['RADAR', 'https://agentic-radar.ai/', 'the estate numbers']].map(([n, u, l]) => `<a href="${u}"><code>${n}</code></a> — ${l}`))}
<h2>9 Contact</h2><p>Tell us what you trade.</p>${form(host)}<p class="muted">The agents that built this read their own mail: ${CONTACT2}. Support: ${CONTACT}. ${OPERATOR} · Vancouver, Canada.</p>`;
}

// ---------- the record pages (§3)
export const PAGES = {
  terms: { title: 'Terms of Use — Allooloo', h1: 'Terms of Use', state: 'draft', body: () => `<p class="muted">Draft as of 2026-09-12 · version 0.1 · to be signed by ${LEGAL}. Until signed, these terms are the operator's stated practice, not a signed instrument.</p>
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
  return ORDER.map(cc => { const d = ctx.nodes[cc]; const n = ctx.live[`${cc}-cm-kg`] || {}; const s = st[cc];
    if (cc === 'hk') return { node: `${cc}-cm-kg`, region: 'East Asia (beacon)', state: 'beacon · partner wanted', last_call: null, ms: null, median_24h: null, last_drop: null, samples: 0 };
    const hist = (s && s.hist) || []; const day = hist.filter(([t]) => Date.now() - t < 86400000);
    return { node: `${cc}-cm-kg`, region: d.region, state: s ? (s.ok ? 'up' : 'down') : 'no probe yet', last_call: s ? new Date(s.ts).toISOString() : null, ms: s ? s.ms : null, median_24h: median(day.map(x => x[1])), last_drop: n.as_of || null, samples: day.length, bars: day.slice(-48).map(x => x[1]) }; });
}
export function statusBody(ctx, st) {
  const rows = statusRows(ctx, st);
  const bars = r => r.bars && r.bars.length ? `<div class="bars">${r.bars.map(ms => `<i style="height:${Math.max(2, Math.min(40, Math.round(ms / 50)))}px" title="${ms} ms"></i>`).join('')}</div>` : '';
  return `<p class="lead">Every five minutes one real <code>resolve_issuer</code> (the node's section-2 example issuer) is sent to each of the eleven doors through its public hostname; the round trip in milliseconds is written to the edge store. One call per node per five minutes; no other polling anywhere. Machine twin: <a href="/status.json"><code>/status.json</code></a>.</p>
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
