// eco-pages — ECO-01 (CEO day order 2, 2026-10-23). The Electronic Compliance Object page per market on <cc>-eco.ai (49 at ECO-01; 54 + the EU regime at ECO-02), the twins
// (<cc>-eco.io/.org/.com/.net) 301 to it, eu/sm/xx-eco.* 301 to the index, and allooloo.ai/markets (the index of all 49 with live status).
// Page pattern: the fr-eco-10060.ai chrome and sections, Allooloo footer and form. Fields come from the signed build (data.js, build_eco.py);
// the live numbers (issuers, as_of, door) are read from the apex list_nodes at render (five-minute cache), never typed.
import { BUILT, LIVE, JWKS, MARKETS, REGIME } from './data.js';   // ECO-02 (DAY ORDER 5): + lu ky bm je tw and the EU regime object (eu-eco.ai)
import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';
import { decide, settle, paymentDoor, counts, PRICING } from './x402gate.js';   // X402-A-01
const INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer|getissuer)/;
const ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: 'https://mcp.getissuer.ai/mcp' }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-a2a.ai/mcp' }];   // RCO-A-01: an ECO lookup that returns a signal leaves a receipt
const VERSION = '2026-10-28.2';   // REF-01 (2026-10-28): the member line at the top of the duty block, the receipts line at its foot, every market page + the EU regime page   // SITE-02 (a) (2026-10-28): the issuer-records door line under the record table on every market with a live Allooloo node; was 2026-10-24.5   // ECO-02: 54 markets + the EU regime page; the European doors under eu-cm-kg.ai
const NM = Object.keys(MARKETS).length;
// REF-01 (2026-10-28): the SM-ECO-10060 registry order (apex sm-eco-10060.org; 49 members, EU = 1 … ZA = 49), from C:\GREENCORE\PROTOCOLS\_canon\registry\estate.json at patch time
const REF01 = {"eu": 1, "fr": 2, "de": 3, "es": 4, "it": 5, "nl": 6, "pl": 7, "ch": 8, "uk": 9, "be": 10, "pt": 11, "at": 12, "ie": 13, "cz": 14, "dk": 15, "se": 16, "fi": 17, "no": 18, "gr": 19, "us": 20, "ca": 21, "mx": 22, "br": 23, "ar": 24, "cl": 25, "co": 26, "cr": 27, "do": 28, "ec": 29, "gt": 30, "pa": 31, "pe": 32, "uy": 33, "au": 34, "jp": 35, "kr": 36, "sg": 37, "in": 38, "id": 39, "my": 40, "ph": 41, "th": 42, "vn": 43, "ae": 44, "sa": 45, "il": 46, "tr": 47, "ma": 48, "za": 49};
const memberLine = cc => REF01[cc] ? `<p class="meta">Member ${REF01[cc]} of 49 under SM-ECO-10060 · <a href="https://${cc}-eco-10060.org/">${cc}-eco-10060.org</a></p>` : '<p class="meta">Served by Allooloo; not yet a registry member</p>';
const RECEIPTS_LINE = '<p class="meta">Receipts for decisions cleared in this market: <a href="https://rco-a2a.ai/">rco-a2a.ai</a></p>';
const EU_DOOR = new Set(['it', 'es', 'se', 'dk', 'no', 'fi', 'be', 'ie', 'at', 'pl', 'pt', 'gr', 'cz']);
const doorOf = cc => (NODES && NODES[cc] && (NODES[cc].regional_door || (NODES[cc].door && NODES[cc].door.replace(/\/$/, '') + '/mcp'))) || (EU_DOOR.has(cc) ? `https://${cc}.eu-cm-kg.ai/mcp` : `https://mcp.${cc}-cm-kg.ai/mcp`);   // ENUM-01 (DAY ORDER 6): the roster entry's door first (list_nodes); the DAY ORDER 5 name rule only before the first roster read   // ACM-SIGNALS-01: the signal table links the seven signal pages (acm-<code>.ai)
const APEX = 'https://mcp.capitalmarketsknowledgegraph.ai/mcp';
const FORM = 'https://formspree.io/f/moeqzgll';
const OPERATOR = 'Allooloo Technologies Corp.';
const UA = 'Allooloo eco-pages (ECO-01)';
const INDEX = 'https://allooloo.ai/markets';
const CSP = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; base-uri 'none'; form-action https://formspree.io https://allooloo.io; frame-ancestors 'none'; upgrade-insecure-requests";
const SIG = [
  ['ACM-200', 'TRADING', 'The ISIN is on this market\'s register (the node\'s current roster for the exchange list).'],
  ['ACM-403', 'HALTED', 'Trading in the line is suspended or halted by the exchange or regulator. The node\'s record carries the halt flag, read nightly from the market\'s halts page named in the fields.'],
  ['ACM-404', 'NOT ON THE REGISTER', 'The ISIN is not on this market\'s register (not listed here, delisted, or never admitted).'],
  ['ACM-451', 'READ THE FILING', 'A regulatory filing for the issuer is dated in the last three days: read it before acting. The answer names it.'],
];
const FIELDS = [
  ['regulator', 'Regulator'], ['exchanges', 'Exchange(s) and listings page'], ['regulated_information_store', 'Regulated-information store'],
  ['periodic_disclosure', 'Periodic disclosure obligations and deadlines'], ['ad_hoc_regime', 'Ad hoc / inside-information regime'], ['filing_format', 'Filing format'],
  ['isin_prefix', 'ISIN prefix'], ['lei', 'LEI'], ['market_calendar', 'Market calendar'], ['filing_languages', 'Filing language(s)'],
  ['trading_halts_page', 'Trading halts page'], ['store_lookup_url', 'Store lookup'],
];
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const link = u => /^https?:\/\//.test(u || '') ? `<a href="${esc(u)}">${esc(u.replace(/^https?:\/\//, '').replace(/\/$/, ''))}</a>` : esc(u);
const int = n => n == null ? '' : Number(n).toLocaleString('en-US');

// ---- live numbers from the apex (list_nodes), five-minute cache
let NODES = null, NODES_AT = 0;
async function nodes() {
  if (NODES && Date.now() - NODES_AT < 300000) return NODES;
  try {
    const r = await fetch(APEX, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': UA }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'list_nodes', arguments: {} } }), signal: AbortSignal.timeout(8000) });
    const j = await r.json(); const sc = j.result.structuredContent || JSON.parse(j.result.content[0].text);
    NODES = Object.fromEntries(sc.nodes.map(n => [n.node.split('-')[0], n])); NODES_AT = Date.now();
  } catch (e) { if (!NODES) NODES = {}; }
  return NODES;
}
async function apexCall(name, args) {
  const r = await fetch(APEX, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': UA }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(12000) });
  const j = await r.json(); return j.result.structuredContent || JSON.parse(j.result.content[0].text);
}

function status(cc, n) {
  const m = MARKETS[cc].record, live = LIVE.includes(cc), s = m.fields.regulated_information_store || {};
  if (live && n && n.live) return { live: true, line: `NODE LIVE · as_of ${n.as_of} · ${int(n.records)} issuers · door ${n.regional_door}`, history: n.backfill && n.backfill.history_from ? `History from ${n.backfill.history_from} · ${int(n.backfill.rows)} rows · ${int(n.backfill.documents)} documents` : null, as_of: n.as_of, issuers: n.records, door: n.regional_door, agent_card: n.agent_card };   // BACKFILL-01 B-7: the history line, from the roster entry (store backfill/facts.json), never typed
  if (live) return { live: true, line: 'NODE LIVE · the apex did not answer at render; door ' + doorOf(cc), door: doorOf(cc) };
  return { live: false, line: `NODE OPENING · store: ${s.state === 'sourced' ? s.value : 'not found'}`, store: s.state === 'sourced' ? s.value : null, store_url: s.url || null };
}

function val(v) {
  if (v == null) return '';
  if (Array.isArray(v)) return v.map(x => typeof x === 'object' ? Object.entries(x).filter(([, y]) => y != null).map(([k, y]) => /^https?:/.test(String(y)) ? link(String(y)) : `${k === 'name' || k === 'report' ? '' : esc(k) + ': '}${esc(y)}`).join(' — ') : esc(x)).join('<br>');
  if (typeof v === 'object') return Object.entries(v).map(([k, y]) => `${esc(k)}: ${/^https?:/.test(String(y)) ? link(String(y)) : esc(y)}`).join('<br>');
  return esc(v);
}
function fieldRow(key, label, f) {
  if (!f || f.state !== 'sourced') {
    const ch = (f && (f.checked || [])) || [];
    return `<tr><td>${esc(label)}</td><td class="nf">not found</td><td>${ch.length ? 'pages checked: ' + ch.map(link).join(' · ') : 'no official page answered'}</td></tr>`;
  }
  const src = String(f.source || '').split(/\s;\s|\s\|\s/).filter(Boolean);
  return `<tr><td>${esc(label)}</td><td>${val(f.value)}${f.url ? '<br>' + link(f.url) : ''}</td><td>${src.map(link).join('<br>')}</td></tr>`;
}

const CSS = `*{margin:0;padding:0;box-sizing:border-box}
body{background:#faf8f3;color:#1a1a1a;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;-webkit-font-smoothing:antialiased}
.container{max-width:900px;margin:0 auto;padding:32px 24px 96px}
.topbar{font-size:12px;color:#6b6b6b;letter-spacing:.04em;margin-bottom:14px}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;color:#6b6b6b;font-size:11px;font-weight:600;margin:0 0 10px}
h1{font:700 28px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;margin:0 0 4px}
h1 .host{display:block;font-size:14px;color:#c84a1e;font-weight:600;margin-top:6px}
.badge{display:inline-block;font:700 11px/1 ui-monospace,monospace;letter-spacing:.08em;color:#f3eee0;background:#c84a1e;padding:5px 10px;border-radius:3px;margin:10px 0 4px}
.badge.open{background:#6b6b6b}
.subtitle{font-size:18px;color:#6b6b6b;font-style:italic;margin:8px 0 20px}
h2{font-size:18px;font-weight:700;margin:34px 0 12px;padding-bottom:8px;border-bottom:2px solid #c84a1e}
.meta{font-size:13px;color:#6b6b6b;margin:0 0 6px}
table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0 24px}
th,td{text-align:left;padding:10px 14px;border-bottom:1px solid #d4cfc1;vertical-align:top;overflow-wrap:anywhere}
th{background:#f3eee0;font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
td.mono{font-family:ui-monospace,monospace;color:#c84a1e;font-weight:600}
td.nf{color:#6b6b6b;font-style:italic}
a{color:#2455a3;text-decoration:none}
.surfaces{font-family:ui-monospace,monospace;font-size:12px;background:#1a1a1a;color:#f3eee0;padding:16px 20px;border-radius:4px;margin:12px 0 24px;white-space:pre;overflow-x:auto;line-height:1.8}
form{display:grid;gap:6px;max-width:520px}form input,form textarea{font:inherit;padding:8px;border:1px solid #d4cfc1;border-radius:3px;background:#fff}form button{justify-self:start;font:600 13px/1 inherit;padding:9px 16px;border:0;border-radius:3px;background:#c84a1e;color:#f3eee0}.hp{display:none}
footer{margin-top:64px;padding-top:28px;border-top:1px solid #d4cfc1;font-size:12px;color:#6b6b6b;line-height:1.7}
.footer-brand{font-size:15px;font-weight:700;color:#1a1a1a;margin-bottom:8px}
@media (max-width:600px){.container{padding:24px 16px 72px}th,td{padding:8px}}`;

function footer(host) {
  return `<footer><p class="footer-brand">${OPERATOR}</p><p>Where agents read the market. One sourced, read-dated record for every listed company, served in the issuer’s own jurisdiction, callable by any agent over MCP and A2A.</p>
<p style="margin-top:8px"><a href="mailto:allooloo@hey.com">Support</a> · <a href="https://allooloo.io/status">Status</a> · <a href="https://allooloo.io/terms">Terms of Use</a> · <a href="https://allooloo.io/privacy">Privacy</a> · <a href="https://allooloo.io/security">Report a Security Issue</a> · <a href="https://allooloo.io/no-cookies">No cookies</a> · <a href="/llms.txt">llms.txt</a> · <a href="https://x.com/allooloo_ai">X @allooloo_ai</a> · <a href="${INDEX}">All ${NM} markets</a></p>
<p style="margin-top:8px">Standard: <a href="https://eco-10060.org/">ECO-10060</a> · signals <a href="https://acm-68000.org/">ACM-68000</a> (Agentic KG Holdings, reference operator, MIT). This site sets no cookies. Artificial intelligence makes mistakes; every field links the page it was read on — read the regulator.</p>
<p style="margin-top:10px">© 2026 ${OPERATOR}</p></footer>`;
}
function contact(host, cc) {
  return `<h2>Contact Us</h2><form action="${FORM}" method="POST" accept-charset="UTF-8"><input type="hidden" name="site" value="${esc(host)}"><input type="hidden" name="source" value="${esc(cc)}-eco"><input type="hidden" name="_subject" value="${esc(host)} contact"><input type="hidden" name="_next" value="https://allooloo.io/"><input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<label for="f-email">email</label><input id="f-email" type="email" name="email" required autocomplete="email"><label for="f-message">message</label><textarea id="f-message" name="message" rows="5" required></textarea><button type="submit">send</button></form>`;
}
const shell = (title, desc, body, host) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="https://${esc(host)}/"><style>${CSS}</style></head><body><div class="container">${body}${footer(host)}</div></body></html>`;

function page(cc, host, n) {
  const R = MARKETS[cc], m = R.record, st = status(cc, n), ex = m.node.example;
  const test = st.live && ex ? `# Connection test — the ISIN path on the ${esc(m.country)} node. No API key. No account. No setup.
$ curl "https://${cc}-eco.ai/isin/${esc(ex.isin)}"${ex.isin_on_node ? '' : `
# ${esc(ex.note)} — the ticker path answers from the node:
$ curl "https://${cc}-eco.ai/ticker/${esc(ex.ticker)}"`}
{ "isin": "${esc(ex.isin)}", "market": "${cc}", "signal": "ACM-200", "state": "TRADING",
  "issuer": "${esc(ex.name)}", "record": "${esc(ex.record_url)}", ... }` : null;
  const lk = m.fields.store_lookup_url || {};
  const body = `<div class="topbar">${esc(OPERATOR)} · Microsoft Azure · in-country nodes · ${esc(m.region || '')}</div>
<p class="eyebrow">Electronic Compliance Object · ${esc(m.country)}</p>
<h1>Electronic Compliance Object · ${esc(m.country)}<span class="host">${esc(host)}</span></h1>
<div class="badge${st.live ? '' : ' open'}">${esc(st.line)}</div>
<p class="subtitle">What an agent must know before it acts on a security listed in ${esc(m.country)}: who regulates, where the filings are stored, what is due when, and which state the issuer is in.</p>
<p class="meta">${OPERATOR} · fields read ${esc(m.hunted)} from the regulator's and exchange's own pages · ${m.sourced} of 12 sourced · ${m.not_found.length} not found · record sha256 ${R.sha256.slice(0, 16)}… · ${R.signature ? 'signed ' + esc(R.signature.kid) : 'not yet signed (key not placed)'}</p>
<h2>The record</h2>
${memberLine(cc)}
<table><thead><tr><th>Field</th><th>Value</th><th>Source</th></tr></thead><tbody>
${FIELDS.map(([k, l]) => fieldRow(k, l, m.fields[k])).join('\n')}
<tr><td>Node status and door</td><td>${esc(st.line)}${st.history ? '<br>' + esc(st.history) : ''}${st.door ? '<br>' + link(st.door) : ''}</td><td>${st.live ? link(APEX) + ' (list_nodes, at render)' : 'the node opens on order; until then the store is the record'}</td></tr>
</tbody></table>
${st.live && n && n.regional_door ? `<p class="meta">Issuer records for this market: ${link(n.regional_door)}</p>` : ''}
${RECEIPTS_LINE}
<h2>ACM-68000 signals — issuer states</h2>
<table><thead><tr><th>Signal</th><th>State</th><th>When</th></tr></thead><tbody>
${SIG.map(([s, t, w]) => `<tr><td class="mono"><a href="https://acm-${s.slice(4)}.ai/">${s}</a></td><td>${t}</td><td>${esc(w)}${s === 'ACM-403' && m.fields.trading_halts_page && m.fields.trading_halts_page.url ? ' ' + link(m.fields.trading_halts_page.url) : ''}</td></tr>`).join('\n')}
</tbody></table>
<h2>Connection Test</h2>
${test ? `<div class="surfaces">${test}</div>` : `<p class="meta">No node in ${esc(m.country)} yet, so no ISIN path here. Look an issuer up in the store itself: ${lk.state === 'sourced' && lk.url ? link(lk.url) : 'store lookup page not found'}.</p>`}
<h2>Machine Surfaces</h2>
<p class="meta">/eco.json · /signals.json · /nodes.json · /health.json · /llms.txt · /sitemap.xml${st.live ? ' · /isin/{ISIN} · /ticker/{EXCHANGE:SYMBOL}' : ''}<br>/.well-known/agent-card.json · /.well-known/mcp.json · /.well-known/acm-68000.json · /.well-known/security.txt · /.well-known/jwks.json</p>
${contact(host, cc)}`;
  return shell(`Electronic Compliance Object · ${m.country}`, `${m.country}: regulator, exchanges, regulated-information store, disclosure deadlines, ad hoc regime, filing format, ISIN, LEI, calendar, languages — each with its source page. ${st.line}.`, body, host);
}

async function lookup(cc, kind, id) {
  const m = MARKETS[cc].record; const node = cc + '-cm-kg';
  const ident = kind === 'isin' ? id.toUpperCase() : id;
  if (kind === 'isin' && !/^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(ident)) return [{ error: 'bad_isin', hint: 'twelve characters: two-letter prefix, nine alphanumerics, one check digit' }, 400];
  let sc; try { sc = await apexCall('resolve_issuer', { identifier: ident }); } catch (e) { return [{ error: 'apex_unreachable', apex: APEX }, 502]; }
  const mine = (sc.matches || []).filter(x => x.node === node), elsewhere = (sc.matches || []).filter(x => x.node !== node).map(x => ({ node: x.node, name: x.name, exchange: x.exchange, record: x.record_url }));
  const base = { [kind]: ident, market: cc, country: m.country, node, read_at: new Date().toISOString(), apex: APEX };
  if (!mine.length) return [{ ...base, signal: 'ACM-404', state: 'NOT ON THE REGISTER', note: kind === 'isin' && !MARKETS[cc].record.node.example.isin_on_node ? MARKETS[cc].record.node.example.note : `not on the ${node} register`, elsewhere }, 200];
  const h = mine[0]; let recent = null;
  try { const e = await (await fetch(h.events_url, { headers: { 'user-agent': UA }, signal: AbortSignal.timeout(8000) })).json(); const cut = new Date(Date.now() - 3 * 86400000).toISOString().slice(0, 10); recent = (e.events || []).find(x => x.event_type !== 'newswire_release' && x.date >= cut) || null; } catch (e) { }
  const out = { ...base, signal: recent ? 'ACM-451' : 'ACM-200', state: recent ? 'READ THE FILING' : 'TRADING', issuer: h.name, exchange: h.exchange, isin: h.isin || null, lei: h.lei || null, as_of: h.as_of, record: h.record_url, events: h.events_url, halts: (m.fields.trading_halts_page || {}).url || null, elsewhere };
  if (recent) out.filing = { date: recent.date, title: recent.title, url: recent.url };
  return [out, 200];
}

const H = (ct, extra) => ({ 'content-type': ct, 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY', 'X-ECO-Version': VERSION, 'X-ECO-Build': BUILT.file, 'X-CMR-Operator': OPERATOR, 'access-control-allow-origin': '*', ...(extra || {}) });
const J = (o, st, cache) => new Response(JSON.stringify(o, null, 1), { status: st || 200, headers: H('application/json; charset=utf-8', { 'cache-control': cache || 'public, max-age=300' }) });
const T = (s, ct) => new Response(s, { headers: H(ct || 'text/plain; charset=utf-8', { 'cache-control': 'public, max-age=300' }) });
const HT = s => new Response(s, { headers: H('text/html; charset=utf-8', { 'cache-control': 'public, max-age=60, must-revalidate' }) });
const R301 = u => new Response(null, { status: 301, headers: { location: u, 'cache-control': 'public, max-age=3600', 'X-ECO-Version': VERSION } });

async function markets(url) {
  const ns = await nodes(); const cs = Object.keys(MARKETS).sort((a, b) => MARKETS[a].record.country.localeCompare(MARKETS[b].record.country));
  const rows = cs.map(cc => { const m = MARKETS[cc].record, st = status(cc, ns[cc]); return { market: cc, country: m.country, region: m.region, host: `https://${cc}-eco.ai/`, status: st.live ? 'NODE LIVE' : 'NODE OPENING', as_of: st.as_of || null, issuers: st.issuers || null, door: st.door || null, store: st.store || null, fields_sourced: m.sourced, fields_not_found: m.not_found.length }; });
  const liveN = rows.filter(r => r.status === 'NODE LIVE' && r.as_of).length;
  if (url.pathname === '/markets.json') return J({ object: 'Electronic Compliance Object index', operator: OPERATOR, markets: rows.length, live_nodes: liveN, live_from: APEX + ' list_nodes (at render)', build: BUILT, rows });
  const body = `<div class="topbar">${OPERATOR} · Electronic Compliance Objects · ${rows.length} markets</div><p class="eyebrow">allooloo.ai/markets</p>
<h1>Electronic Compliance Objects<span class="host">allooloo.ai/markets</span></h1><div class="badge">${liveN} NODES LIVE · ${rows.length - liveN} OPENING</div>
<p class="subtitle">One page per market: regulator, exchanges, regulated-information store, deadlines, ad hoc regime, filing format, ISIN, LEI, calendar, languages — each read from the official page, or marked not found.</p>
<p class="meta">Live count read from the apex at render (${esc(APEX)}, list_nodes). Fields from the hunt of ${esc(BUILT.hunt)}. Machine form: <a href="/markets.json">/markets.json</a>.</p>
<table><thead><tr><th>Market</th><th>Status</th><th>Issuers · as of</th><th>Fields sourced / not found</th></tr></thead><tbody>
${rows.map(r => `<tr><td><a href="${r.host}">${esc(r.country)}</a><br><span class="meta">${r.market}-eco.ai</span></td><td>${r.status === 'NODE LIVE' ? '<b>NODE LIVE</b>' : 'NODE OPENING'}${r.door ? '<br>' + link(r.door) : r.store ? '<br><span class="meta">store: ' + esc(r.store).slice(0, 90) + '</span>' : ''}</td><td>${r.issuers ? int(r.issuers) + ' · ' + esc(r.as_of) : '—'}</td><td>${r.fields_sourced} / ${r.fields_not_found}</td></tr>`).join('\n')}
</tbody></table>`;
  return HT(shell(`Electronic Compliance Objects · ${NM} markets`, `${rows.length} markets, ${liveN} nodes live (read at render).`, body, 'allooloo.ai'));
}

// ---- X402-A-01: allooloo.ai/x402 — settlement counts of the Allooloo doors (counts only, never amounts)
async function x402(url, env) {
  const c = await counts(env, 14);
  if (url.pathname === '/x402/settled.json') return J(c, 200, 'no-store');
  if (url.pathname === '/x402/pricing.json') return J({ ...PRICING, payment: paymentDoor(env), doors: ['https://mcp.getissuer.ai/mcp', 'https://mcp.<cc>-cm-kg.ai/mcp and https://<cc>.eu-cm-kg.ai/mcp (every node door)', 'https://<cc>-eco.ai/eco.json · /isin/ · /ticker/', 'https://mcp.rco-a2a.ai/mcp (write_receipt without a key)'] }, 200, 'public, max-age=300');
  const today = new Date().toISOString().slice(0, 10), days = Object.keys({ ...c.by_day, ...c.free_by_day, ...c.offers_by_day }).sort().reverse();
  const body = `<div class="topbar">${OPERATOR} · x402 on the Allooloo doors</div><p class="eyebrow">allooloo.ai/x402</p>
<h1>Settled reads<span class="host">allooloo.ai/x402</span></h1><div class="badge">${int(c.settled)} SETTLED · ${int(c.by_day[today] || 0)} TODAY</div>
<p class="subtitle">An agent pays an agent for a record — no procurement desk. Every record read on the resolver, every node door and the Electronic Compliance Objects is free for every agent, with no count and no 402 after N reads. An agent that chooses to pay asks for the offer (header <code>x402-pay: 1</code>) and settles over x402 on Base; a paid read carries its settlement on its RCO receipt. Settlement counts are published below.</p><p class="meta"><b>No rationing (CEO ruling 2026-10-24): every read is free for every agent, house or outside — no 402 after N reads on any Allooloo door.</b></p>
<p class="meta">Counts only, read live from the register at render. Machine form: <a href="/x402/settled.json">/x402/settled.json</a> · terms: <a href="/x402/pricing.json">/x402/pricing.json</a>.</p>
<table><thead><tr><th>Day (UTC)</th><th>Settled</th><th>Free-tier reads</th><th>Offers (402)</th></tr></thead><tbody>
${days.map(d => `<tr><td>${d}</td><td>${int(c.by_day[d] || 0)}</td><td>${int(c.free_by_day[d] || 0)}</td><td>${int(c.offers_by_day[d] || 0)}</td></tr>`).join('') || '<tr><td colspan="4">no reads on the register yet</td></tr>'}
</tbody></table>
<h2>By door</h2><table><thead><tr><th>Door</th><th>Settled</th></tr></thead><tbody>${Object.entries(c.by_door).map(([d, n]) => `<tr><td>${esc(d)}</td><td>${int(n)}</td></tr>`).join('') || '<tr><td colspan="2">none yet</td></tr>'}</tbody></table>`;
  return HT(shell('x402 · settled reads', `${c.settled} settled reads on the Allooloo doors (counts only).`, body, 'allooloo.ai'));
}
// ---- PROTOCOLS-A-01: allooloo.ai/.well-known — the doors of Allooloo Technologies Corp., one set
const RCO_PUB = {"kty": "OKP", "crv": "Ed25519", "x": "N-knqz1-H9xwNGvOS0Eu7CDrmdPgzFjCgvExLJt2lQw", "kid": "allooloo-rco-2026-10", "alg": "EdDSA", "use": "sig"};
const NODE_CC = ['ca', 'uk', 'us', 'de', 'fr', 'nl', 'ch', 'au', 'sg', 'jp', 'kr', 'hk'];
const DOORS = (ns) => [   // ENUM-01 (DAY ORDER 6): the node doors are every live node on the roster (list_nodes), not a typed twelve
  { id: 'getissuer', resolves: 'listed issuers (ticker, ISIN, LEI) and the ACM-68000 signal', mcp: 'https://mcp.getissuer.ai/mcp', card: 'https://agent.getissuer.ai/.well-known/agent-card.json', registry: 'io.github.allooloo/cm-kg' },
  { id: 'eco', resolves: `the Electronic Compliance Object of a market (${NM}) and the EU regime`, mcp: 'https://mcp.getissuer.ai/eco/mcp', pages: INDEX, registry: 'io.github.allooloo/eco' },
  { id: 'acm-signals', resolves: 'the seven ACM-68000 signals for listed issuers', mcp: 'https://mcp.getissuer.ai/signals/mcp', pages: ['000', '200', '300', '403', '404', '451', '500'].map(c => `https://acm-${c}.ai/`), registry: 'io.github.allooloo/acm-signals' },
  ...Object.values(ns || {}).filter(n => n.live).map(n => ({ id: n.node, resolves: `listed issuers of one market, served in-country (${n.node.split('-')[0]})`, mcp: n.regional_door || (String(n.door).replace(/\/$/, '') + '/mcp'), card: n.agent_card || null })),
  { id: 'issuerwire', resolves: 'filings and releases since your last read (markets: issuerwire.ai/facts.json)', mcp: 'https://mcp.issuerwire.ai/mcp', card: 'https://issuerwire.ai/.well-known/agent-card.json', registry: 'io.github.allooloo/issuerwire' },
  { id: 'receipts', resolves: 'receipts — the Record of Cleared Orders (Allooloo doors write; anyone reads)', mcp: 'https://mcp.rco-a2a.ai/mcp', operator: 'Agentic KG Holdings (the standard); Allooloo writes' }];
async function wellKnown(url, env) {
  const p = url.pathname, me = 'https://allooloo.ai';
  const routing = ROUTING, payment = paymentDoor(env), doors = DOORS(await nodes());
  if (p === '/llms.txt') return T(`# allooloo.ai — Allooloo Technologies Corp.\n\nDoors by what they resolve:\n${routing.map(r => `- ${r.what} → ${r.door}`).join('\n')}\n\nWhere agents read the market: one sourced, read-dated record for every listed company, served in the issuer's own jurisdiction, over MCP and A2A.\n\n## The doors\n${doors.map(d => `- ${d.id}: ${d.resolves} — ${d.mcp}`).join('\n')}\n\n## Pages\n- Electronic Compliance Objects, ${NM} markets: ${INDEX}\n- The seven signal pages: https://acm-000.ai/ … https://acm-500.ai/\n- Settled reads (counts only): ${me}/x402\n\n## Terms\n- Every read is free for every agent — no rationing (CEO ruling 2026-10-24). To pay by choice: ask for the offer (x402-pay: 1), then pay on Base (USDC, OUSD): ${me}/x402/pricing.json\n- Every resolve and signal leaves an RCO receipt (decision_id in the answer), readable by anyone at https://mcp.rco-a2a.ai/mcp\n- Keyring: ${me}/.well-known/jwks.json\n\nMachine set: ${me}/.well-known/mcp.json · agent-card.json · api-catalog · ai-catalog.json · jwks.json · security.txt\nOperator: Allooloo Technologies Corp. · mk@allooloo.ai · https://allooloo.io\n`);
  if (p === '/.well-known/mcp.json') return J({ name: 'allooloo', title: 'Allooloo Technologies Corp. — the doors', description: 'Every Allooloo MCP door, typed by what it resolves, with the routing block, the x402 payment door and the receipt door.', websiteUrl: 'https://allooloo.io/', remotes: doors.map(d => ({ type: 'streamable-http', url: d.mcp })), doors, routing, payment, receipts: { door: 'https://mcp.rco-a2a.ai/mcp', keyring: `${me}/.well-known/jwks.json` }, operator: OPERATOR });
  if (p === '/.well-known/agent-card.json') return J({ protocolVersion: '0.3.0', name: 'Allooloo Technologies Corp. — getissuer and the market doors', description: 'Where agents read the market. Start at the resolver: getissuer names the home market of any listed issuer (ticker, ISIN, LEI) and answers its ACM-68000 signal; the record is served by that market\'s own node.', url: 'https://mcp.getissuer.ai/mcp', preferredTransport: 'JSONRPC',
    supportedInterfaces: [{ url: 'https://mcp.getissuer.ai/mcp', transport: 'JSONRPC', protocolBinding: 'JSONRPC' }], provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: VERSION, capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'],
    skills: [{ id: 'resolve-issuer', name: 'Resolve a listed issuer', description: 'resolve_issuer at https://mcp.getissuer.ai/mcp', tags: ['capital-markets', 'resolver'] }, { id: 'get-signal', name: 'Get the ACM-68000 signal', description: 'get_signal at https://mcp.getissuer.ai/mcp', tags: ['acm-68000'] }, { id: 'get-eco', name: 'Read a market\'s Electronic Compliance Object', description: 'get_eco at https://mcp.getissuer.ai/eco/mcp', tags: ['eco'] }]
      .concat(routing.map(r => ({ id: 'route-' + r.resolves, name: 'Route: ' + r.what, description: `${r.what} resolve at ${r.door}`, tags: ['routing'] }))), doors, payment });
  if (p === '/.well-known/api-catalog') return new Response(JSON.stringify({ linkset: [{ anchor: me, 'service-doc': [{ href: me + '/llms.txt', type: 'text/plain' }], service: doors.map(d => ({ href: d.mcp, title: `${d.id} — ${d.resolves}` })).concat(routing.filter(r => r.resolves === 'gtin').map(r => ({ href: r.door, title: 'GTINs → gtinfetch.ai (GreenCore Solutions Corp.)' }))) }] }, null, 1), { headers: H('application/linkset+json', { 'cache-control': 'public, max-age=300' }) });
  if (p === '/.well-known/ai-catalog.json') return J({ specVersion: '1.0', host: { displayName: 'Allooloo Technologies Corp.', identifier: 'did:web:allooloo.ai' }, entries: doors.map(d => ({ identifier: `urn:air:allooloo.ai:door:${d.id}`, displayName: d.id, type: 'application/json', url: d.mcp, description: d.resolves, ...(d.card ? { agentCard: d.card } : {}) })) });
  if (p === '/.well-known/jwks.json') return J({ keys: [RCO_PUB, {"kty": "OKP", "crv": "Ed25519", "x": "cqa-iPbl2AD_Yw3bIxQCPAmzSiBemxU6ajL2nI1w9QA", "kid": "allooloo-cmr-2026-10", "alg": "EdDSA", "use": "sig"}, ...((JWKS && JWKS.keys) || [])] });   // NODE-SIGN-01: + the node-record key
  if (p === '/.well-known/security.txt') return T(`Contact: mailto:allooloo@hey.com\nContact: https://allooloo.io/security\nExpires: 2027-10-24T00:00:00Z\nPreferred-Languages: en\nCanonical: https://allooloo.ai/.well-known/security.txt\n`);
  return J({ error: 'not_found', paths: ['/llms.txt', '/.well-known/mcp.json', '/.well-known/agent-card.json', '/.well-known/api-catalog', '/.well-known/ai-catalog.json', '/.well-known/jwks.json', '/.well-known/security.txt'] }, 404, 'no-store');
}
// ---- ECO-02 (DAY ORDER 5, 2026-10-24): eu-eco.ai — the EU regime object (ESMA, MiFID II product governance, Prospectus Regulation, MAR, Transparency, ESEF,
// FIRDS, OAM / ESAP, LEI) with one row per EU/EEA market linking to its own ECO page. Signed like the market records (kid allooloo-eco-2026-10).
const RFIELDS = [['regulator', 'Regulator and the competent-authority model'], ['mifid_ii_product_governance', 'MiFID II product governance'], ['prospectus_regulation', 'Prospectus Regulation'], ['mar', 'Market Abuse Regulation (MAR)'],
  ['transparency_directive', 'Transparency Directive — periodic reports'], ['esef', 'ESEF — the reporting format'], ['firds', 'FIRDS — instrument reference data'], ['oam_network', 'Officially appointed mechanisms / ESAP'], ['isin_lei', 'ISIN and LEI']];
async function regime(url, host, request, env) {
  const p = url.pathname, R = REGIME, m = R.record, ns = await nodes();
  const rows = (m.markets || []).map(r => ({ cc: r.cc, country: r.country, nca: (r.nca && r.nca.name) || r.nca || null, nca_url: (r.nca && r.nca.url) || null, eco_page: r.eco_page || null, node_live: !!(ns[r.cc] && ns[r.cc].live), door: ns[r.cc] && ns[r.cc].live ? doorOf(r.cc) : null, records: ns[r.cc] && ns[r.cc].live ? ns[r.cc].records : null }));
  const liveN = rows.filter(r => r.node_live).length;
  if (p === '/eco.json') return J({ ...R, rows, build: BUILT });
  if (p === '/nodes.json') return J({ regime: 'eu', live_nodes: liveN, rows: rows.map(r => ({ cc: r.cc, live: r.node_live, door: r.door, records: r.records })), apex: APEX, index: INDEX });
  if (p === '/health.json') return J({ status: 'ok', host, version: VERSION, build: BUILT.file, apex_read: Object.keys(ns).length > 0 }, 200, 'no-store');
  if (p === '/signals.json') return J({ protocol: 'ACM-68000', reference: 'https://acm-68000.org/', signals: SIG.map(([code, state, when]) => ({ code, state, when, page: `https://acm-${code.slice(4)}.ai/` })), resolver: 'https://mcp.getissuer.ai/mcp', regime: 'eu' });
  if (p === '/.well-known/jwks.json') return J(JWKS);
  if (p === '/.well-known/security.txt') return T(`Contact: mailto:allooloo@hey.com\nContact: https://allooloo.io/security\nExpires: 2027-10-23T00:00:00Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\n`);
  if (p === '/.well-known/mcp.json') return J({ mcp_server: 'https://mcp.getissuer.ai/eco/mcp', resolver: 'https://mcp.getissuer.ai/mcp', transport: 'streamable-http', auth: 'none for reads', regime: 'eu', doors: rows.filter(r => r.door).map(r => ({ market: r.cc, door: r.door })), routing: ROUTING, payment: paymentDoor(env), receipts: { door: 'https://mcp.rco-a2a.ai/mcp', keyring: 'https://allooloo.ai/.well-known/jwks.json' } });
  if (p === '/.well-known/agent-card.json') return J({ name: 'Electronic Compliance Object · European Union regime', description: 'The EU disclosure and product-governance regime as one sourced, signed object, with one row per EU/EEA market and its own ECO page.', url: 'https://mcp.getissuer.ai/eco/mcp', preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: 'https://mcp.getissuer.ai/eco/mcp', transport: 'JSONRPC' }, { url: 'https://mcp.getissuer.ai/mcp', transport: 'JSONRPC' }], provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: VERSION, protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'], skills: [{ id: 'get-eco', name: 'Read the EU regime object', description: 'get_eco at https://mcp.getissuer.ai/eco/mcp', tags: ['eco', 'eu', 'mifid-ii'] }], routing: ROUTING });
  if (p === '/llms.txt') return T(`# ${host} — Electronic Compliance Object · European Union regime\n\nDoors by what they resolve:\n${ROUTING.map(r => `- ${r.what} → ${r.door}`).join('\n')}\n\n${RFIELDS.map(([k, l]) => { const f = m.fields[k] || {}; return `- ${l}: ${f.state === 'sourced' ? String(typeof f.value === 'string' ? f.value : JSON.stringify(f.value)).slice(0, 400) + ' (source ' + (f.source || f.url) + ')' : 'not found'}`; }).join('\n')}\n\n## Markets\n${rows.map(r => `- ${r.country}: ${r.eco_page || 'no ECO page'}${r.node_live ? ' · node live · ' + r.door : ''}`).join('\n')}\n\nMachine set: /eco.json · /nodes.json · /signals.json · /.well-known/agent-card.json · /.well-known/mcp.json · /.well-known/jwks.json · /.well-known/security.txt · /sitemap.xml\n`);
  if (p === '/sitemap.xml') return T(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${['/', '/eco.json', '/llms.txt'].map(x => `<url><loc>https://${host}${x}</loc></url>`).join('')}</urlset>\n`, 'application/xml; charset=utf-8');
  if (p === '/robots.txt') return T(`User-agent: *\nAllow: /\nSitemap: https://${host}/sitemap.xml\n`);
  if (p !== '/' && p !== '/index.html') return J({ error: 'not_found', host, paths: ['/', '/eco.json', '/nodes.json', '/signals.json', '/health.json', '/llms.txt', '/sitemap.xml', '/robots.txt', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/jwks.json', '/.well-known/security.txt'] }, 404, 'no-store');
  const body = `<div class="topbar">${esc(OPERATOR)} · Electronic Compliance Objects · the EU regime</div>
<p class="eyebrow">Electronic Compliance Object · European Union</p>
<h1>Electronic Compliance Object · European Union<span class="host">${esc(host)}</span></h1>
<div class="badge">REGIME · ${liveN} NODES LIVE · ${rows.length} EU/EEA MARKETS</div>
<p class="subtitle">The rules every EU/EEA market shares — product governance, prospectus, market abuse, periodic reporting and its format — and where each market's own object is.</p>
<p class="meta">${OPERATOR} · fields read ${esc(m.hunted)} from ESMA's own pages · ${m.sourced} of ${RFIELDS.length} sourced · record sha256 ${R.sha256.slice(0, 16)}… · ${R.signature ? 'signed ' + esc(R.signature.kid) : 'not signed'}</p>
<h2>The regime</h2>
${memberLine('eu')}
<table><thead><tr><th>Field</th><th>Value</th><th>Source</th></tr></thead><tbody>
${RFIELDS.map(([k, l]) => fieldRow(k, l, m.fields[k])).join('\n')}
</tbody></table>
${RECEIPTS_LINE}
<h2>Markets</h2>
<table><thead><tr><th>Market</th><th>Competent authority</th><th>ECO page</th><th>Node</th></tr></thead><tbody>
${rows.map(r => `<tr><td>${esc(r.country)}</td><td>${r.nca_url ? `<a href="${esc(r.nca_url)}">${esc(r.nca)}</a>` : esc(r.nca || '')}</td><td>${r.eco_page ? link(r.eco_page) : '—'}</td><td>${r.node_live ? `NODE LIVE · ${int(r.records)} · ${link(r.door)}` : 'NODE OPENING'}</td></tr>`).join('\n')}
</tbody></table>
<h2>Machine Surfaces</h2>
<p class="meta">/eco.json · /nodes.json · /signals.json · /health.json · /llms.txt · /sitemap.xml<br>/.well-known/agent-card.json · /.well-known/mcp.json · /.well-known/security.txt · /.well-known/jwks.json</p>
${contact(host, 'eu')}`;
  return HT(shell('Electronic Compliance Object · European Union regime', `The EU regime: ESMA, MiFID II product governance, Prospectus Regulation, MAR, ESEF — each with its source page — and ${rows.length} EU/EEA markets.`, body, host));
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url); let host = url.hostname.toLowerCase(); if (host.startsWith('www.')) host = host.slice(4);
    if (host.endsWith('.workers.dev')) host = (url.searchParams.get('host') || '').toLowerCase();   // verification only: ?host=<cc>-eco.ai selects the surface on workers.dev
    if (host === 'allooloo.ai' && (url.pathname === '/llms.txt' || url.pathname.startsWith('/.well-known/'))) return wellKnown(url, env);
    if (host === 'allooloo.ai' && (url.pathname === '/x402' || url.pathname === '/x402/' || url.pathname.startsWith('/x402/'))) return x402(url, env);
    if (host === 'allooloo.ai') return (url.pathname === '/markets' || url.pathname === '/markets/' || url.pathname === '/markets.json') ? markets(url) : R301('https://allooloo.io' + url.pathname + url.search);
    const mt = host.match(/^([a-z]{2})-eco\.(ai|io|org|com|net)$/); if (!mt) return J({ error: 'not_found' }, 404, 'no-store');
    const [, cc, tld] = mt;
    if (cc === 'eu' && tld === 'ai' && REGIME) return regime(url, host, request, env);   // ECO-02: the EU regime object
    if (!MARKETS[cc]) return R301(url.pathname === '/llms.txt' || url.pathname.startsWith('/.well-known/') ? 'https://allooloo.ai' + url.pathname : INDEX);   // PROTOCOLS-A-01: eu/sm/xx machine files land on the allooloo.ai set                                   // eu, sm, xx: the family index
    if (tld !== 'ai') return R301(`https://${cc}-eco.ai${url.pathname}${url.search}`);   // house redirect: path and query kept
    const p = url.pathname, m = MARKETS[cc].record, live = LIVE.includes(cc);
    const metered = p === '/eco.json' || /^\/(isin|ticker)\//.test(p); const internal = INTERNAL.test(request.headers.get('user-agent') || '');
    const g = metered && !internal ? await decide(request, env, { door: 'eco', resource: `https://${host}${p}`, description: `One Electronic Compliance Object read on ${host} (Allooloo Technologies Corp.)` }) : { pass: true };
    if (g.response) return g.response;
    const pay = g.paid ? await settle(env, g.paid, 'eco') : null; if (pay && !pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } });
    const paid = r => { if (!pay) return r; const h = new Headers(r.headers); h.set('PAYMENT-RESPONSE', pay.header); h.set('X-PAYMENT-RESPONSE', pay.header); h.set('cache-control', 'no-store'); h.set('access-control-expose-headers', 'PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, PAYMENT-REQUIRED'); return new Response(r.body, { status: r.status, headers: h }); };
    if (p === '/' || p === '/index.html') return HT(page(cc, host, (await nodes())[cc]));
    if (p === '/eco.json') { const st = status(cc, (await nodes())[cc]); return paid(J({ ...MARKETS[cc], node_status: st, build: BUILT, ...(pay ? { settlement: { network: pay.pr.network, transaction: pay.tx } } : {}) }, 200, pay ? 'no-store' : undefined)); }
    if (p === '/signals.json') return J({ protocol: 'ACM-68000', reference: 'https://acm-68000.org/', mapping: 'issuer states', signals: SIG.map(([code, state, when]) => ({ code, state, when, page: `https://acm-${code.slice(4)}.ai/` })), resolver: 'https://mcp.getissuer.ai/mcp', tool: 'get_signal', market: cc });
    if (p === '/nodes.json') { const ns = await nodes(); return J({ market: cc, live: live, node: live ? ns[cc] || { node: cc + '-cm-kg', door: doorOf(cc) } : null, apex: APEX, index: INDEX, live_markets: LIVE }); }
    if (p === '/health.json') { const ns = await nodes(); return J({ status: 'ok', host, version: VERSION, build: BUILT.file, apex_read: Object.keys(ns).length > 0, node_live: live && !!(ns[cc] && ns[cc].live) }, 200, 'no-store'); }
    if (p === '/.well-known/jwks.json') return J(JWKS);
    if (p === '/.well-known/security.txt') return T(`Contact: mailto:allooloo@hey.com\nContact: https://allooloo.io/security\nExpires: 2027-10-23T00:00:00Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\n`);
    if (p === '/.well-known/acm-68000.json') return J({ protocol: 'ACM-68000', reference: 'https://acm-68000.org/', operator_of_reference: 'Agentic KG Holdings (MIT)', implemented_by: OPERATOR, signals: SIG.map(([code, state]) => ({ code, state, page: `https://acm-${code.slice(4)}.ai/` })), lookup: live ? `https://${host}/isin/{ISIN}` : null });
    if (p === '/.well-known/mcp.json') return J({ mcp_server: live ? doorOf(cc) : APEX, apex: APEX, resolver: 'https://mcp.getissuer.ai/mcp', transport: 'streamable-http', auth: 'none for reads', tools_of_note: ['resolve_issuer', 'get_signal', 'list_nodes'], operator: OPERATOR, routing: ROUTING, payment: paymentDoor(env), receipts: { door: 'https://mcp.rco-a2a.ai/mcp', note: 'an ECO lookup that returns a signal leaves an RCO receipt; the answer carries its decision_id' } });
    if (p === '/.well-known/agent-card.json') return J({ name: `Electronic Compliance Object · ${m.country}`, description: `${m.country}: the regulator, exchanges, regulated-information store, disclosure deadlines and issuer states (ACM-68000), each field with its source page.${live ? ' ISIN lookup on the ' + cc + '-cm-kg node.' : ''}`, url: `https://${host}/`, provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: VERSION, supportedInterfaces: [{ url: 'https://mcp.getissuer.ai/eco/mcp', protocolBinding: 'MCP', description: 'the resolver: get_eco, get_signal, resolve_issuer' }, { url: 'https://mcp.getissuer.ai/mcp', protocolBinding: 'MCP' }].concat(live ? [{ url: `https://mcp.${cc}-cm-kg.ai/mcp`, protocolBinding: 'MCP', description: 'this market node' }] : []), resolver: 'https://mcp.getissuer.ai/mcp', routing: ROUTING, payment: paymentDoor(env), skills: [{ id: 'get-eco', name: 'Get this ECO through the resolver', description: `get_eco {"market": "${cc}"} at https://mcp.getissuer.ai/eco/mcp`, tags: ['eco', 'mcp'] }, { id: 'eco-record', name: 'Electronic Compliance Object', description: 'GET /eco.json — the sourced record', tags: ['disclosure', 'regulator', 'isin'] }].concat(live ? [{ id: 'isin-state', name: 'Issuer state by ISIN', description: 'GET /isin/{ISIN} — ACM-200 / ACM-404 / ACM-451 on this market\'s node', tags: ['isin', 'acm-68000'] }] : []), defaultInputModes: ['application/json'], defaultOutputModes: ['application/json'] });
    if (p === '/llms.txt') { const st = status(cc, (await nodes())[cc]); return T(`# ${host} — Electronic Compliance Object · ${m.country}\n\n${st.line}\n\n${FIELDS.map(([k, l]) => { const f = m.fields[k] || {}; return `- ${l}: ${f.state === 'sourced' ? (typeof f.value === 'string' ? f.value : JSON.stringify(f.value)) + ' (source: ' + f.source + ')' : 'not found'}`; }).join('\n')}\n\nSignals (ACM-68000): ACM-200 trading · ACM-403 halted · ACM-404 not on the register · ACM-451 read the filing\nMachine: /eco.json /signals.json /nodes.json /health.json${live ? ' /isin/{ISIN} /ticker/{EXCHANGE:SYMBOL}' : ''}\nIndex: ${INDEX}\nOperator: ${OPERATOR}\n`); }
    if (p === '/sitemap.xml') return T(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${['/', '/eco.json', '/llms.txt'].map(x => `<url><loc>https://${host}${x}</loc></url>`).join('')}</urlset>\n`, 'application/xml');
    if (p === '/robots.txt') return T(`User-agent: *\nAllow: /\nSitemap: https://${host}/sitemap.xml\n`);
    const lk = p.match(/^\/(isin|ticker)\/([^/]+)$/);
    if (lk && live) {
      const [o, st] = await lookup(cc, lk[1], decodeURIComponent(lk[2]));
      if (st === 200 && o.signal && !/^Allooloo /.test(request.headers.get('user-agent') || '')) {   // RCO-A-01: the ECO rule read that cleared a signal
        const did = decisionId(), R = MARKETS[cc]; o.receipt = receiptLinks(did);
        const recs = [{ url: `https://${cc}-eco.ai/eco.json`, as_of: m.hunted || null, sha256: 'sha256:' + R.sha256, signature: R.signature ? { alg: R.signature.alg || 'EdDSA', kid: R.signature.kid, keyring: `https://${cc}-eco.ai/.well-known/jwks.json` } : null }];
        if (o.record) recs.push({ url: o.record, as_of: o.as_of || null, sha256: await sha256({ record: o.record, as_of: o.as_of, issuer: o.issuer }), signature: null });
        if (o.filing && o.filing.url) recs.push({ url: o.filing.url, as_of: o.filing.date || null, sha256: await sha256(o.filing), signature: null });
        ctx.waitUntil(writeReceipt(env, { ...(pay ? { settlement: { network: pay.pr.network, transaction: pay.tx } } : {}), decision_id: did, object: { type: lk[1] === 'isin' ? 'isin' : 'ticker', id: String(o[lk[1]] || decodeURIComponent(lk[2])).slice(0, 80) }, actor_class: 'api-client (HTTP GET)',
          rule: { id: `ECO-${cc.toUpperCase()} — Electronic Compliance Object, ${m.country}`, version: BUILT.file }, records_read: recs, signal: o.signal, decided_at: new Date().toISOString(), issuing_door: `https://${cc}-eco.ai` }));
      }
      if (pay) o.settlement = { network: pay.pr.network, transaction: pay.tx, payer: pay.payer };
      return paid(J(o, st, 'no-store'));
    }
    return J({ error: 'not_found', host, paths: ['/', '/eco.json', '/signals.json', '/nodes.json', '/health.json', '/llms.txt', '/sitemap.xml', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/acm-68000.json', '/.well-known/security.txt', '/.well-known/jwks.json'].concat(live ? ['/isin/{ISIN}', '/ticker/{EXCHANGE:SYMBOL}'] : []) }, 404, 'no-store');
  }
};
