// acm-signals — ACM-SIGNALS-01 (DAY ORDER 3, CEO 2026-10-24). The seven ACM-68000 signal pages on acm-000/200/300/403/404/451/500.ai, operated by
import { signalBlock } from './prompt.js';   // PROMPT-01 (DAY ORDER 6, 2026-10-25)
// Allooloo Technologies Corp. (records line 2026-10-24); the .org and .com twins 301 to the .ai with path and query kept. Page pattern: cpg-200.ai
// (GSC's CPG application profile). The office kicker and the standard's definition come first (Agentic KG Holdings, reference operator, MIT); the
// Allooloo issuer state, the live ISIN test through the resolver (getissuer get_signal, read at render, five-minute cache) and "Connect your AI"
// follow; GSC's CPG row is linked in the table. Machine files carry the doors by what they resolve. Worker-rendered, no job.
import { HALTS } from './halts.js';
import { paymentDoor } from './x402gate.js';   // PROTOCOLS-A-01: the payment door in mcp.json
const VERSION = '2026-10-24.2';
const RESOLVER = 'https://mcp.getissuer.ai/mcp';
const IW = 'https://mcp.issuerwire.ai/mcp';
const FORM = 'https://formspree.io/f/moeqzgll';
const OPERATOR = 'Allooloo Technologies Corp.';
const OFFICE = 'Agentic KG Holdings · the Agentic Private Office · ACM-68000 reference operator · MIT licence';
const UA = 'Allooloo acm-signals (ACM-SIGNALS-01)';
const RECORDS = 'Allooloo Technologies Corp. operates this page from 2026-10-24 (company records line ACM-SIGNALS-01).';
const ROUTES = [['gtin', 'GTINs', 'https://gtinfetch.ai/mcp', 'gtinfetch.ai — GreenCore Solutions Corp.'], ['issuer', 'Listed issuers (ticker, ISIN, LEI)', 'https://mcp.getissuer.ai/mcp', 'getissuer — Allooloo Technologies Corp.'], ['receipt', 'Receipts — the Record of Cleared Orders', 'https://mcp.rco-a2a.ai/mcp', 'RCO-A2A — Agentic KG Holdings']];
const ROUTE_TXT = 'Doors by what they resolve:\n' + ROUTES.map(([, w, d]) => `- ${w} → ${d}`).join('\n');
// the standard (acm-68000.org/signals.json, the office's definitions) · the Allooloo issuer state · GSC's CPG application profile
const S = {
  '000': { std: 'NOT_APPLICABLE', action: 'No action required.', issuer: 'NOT APPLICABLE', kind: 'definition', when: 'The identifier is not a listed-security identifier — a GTIN is answered ACM-000 and routed to gtinfetch.ai.', example: '03017620422003' },
  '200': { std: 'ALLOW', action: 'Execute the transaction.', issuer: 'TRADING', kind: 'state', when: 'The security is on its home market\'s register (the node\'s current roster).', candidates: ['FR0000120271', 'CA82509L1076', 'CH0038863350', 'DE0007164600', 'AU000000BHP4', 'JP3633400001', 'SG1L01001701'] },
  '300': { std: 'CONDITIONAL', action: 'Evaluate before proceeding.', issuer: 'CONDITIONAL', kind: 'definition', when: 'A bare ticker names more than one issuer: the resolver answers ACM-300 with the candidates; name the exchange or give the ISIN.', example: 'BHP' },
  '403': { std: 'RESTRICT', action: 'Halt transaction.', issuer: 'HALTED', kind: 'state', when: 'Trading in the line is halted or suspended by the exchange or regulator: the home node\'s record carries a halt flag read nightly from the market\'s halts page, and the resolver answers ACM-403 with the halt (since, reason, the page it was read from).', candidates: ['8366.T'] },
  '404': { std: 'NOT_FOUND', action: 'Abort transaction.', issuer: 'NOT ON THE REGISTER', kind: 'state', when: 'The security is not on the register of any market on the roster (not listed there, delisted, or never admitted).', example: 'ZAE000015889' }   /* ENUM-01 (DAY ORDER 6): the example must sit on a market off the roster — Petrobras (BRPETRACNPR6) answers ACM-200 since Brazil joined (DAY ORDER 5); Naspers (Johannesburg) is off the roster and answers ACM-404 (read 2026-10-25) */,
  '451': { std: 'ESCALATE', action: 'Human-in-the-loop required.', issuer: 'READ THE FILING', kind: 'state', when: 'A regulatory filing for the issuer is dated in the last three days: a person reads it before the agent acts. The answer names the filing.', fallback: ['GB00BP6MXD84', 'US0378331005', 'CA82509L1076'] },
  '500': { std: 'SYSTEM_ERROR', action: 'Retry or fallback.', issuer: 'SYSTEM ERROR', kind: 'definition', when: 'The home market\'s node did not answer: retry. No record is served from another store, so there is no fallback record.' },
};
const CODES = ['000', '200', '300', '403', '404', '451', '500'];
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const link = (u, t) => /^https?:\/\//.test(u || '') ? `<a href="${esc(u)}">${esc(t || u.replace(/^https?:\/\//, '').replace(/\/$/, ''))}</a>` : esc(u);
const CSP = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; script-src 'self'; base-uri 'none'; form-action https://formspree.io https://allooloo.io; frame-ancestors 'none'; upgrade-insecure-requests";

async function rpc(url, name, args, ms) {
  const r = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': UA }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(ms || 15000) });
  const raw = await r.text(); const line = raw.split('\n').map(l => l.replace(/^data: /, '')).find(l => l.trim().startsWith('{'));
  const j = JSON.parse(line); return j.result.structuredContent || JSON.parse(j.result.content[0].text);
}
const signal = id => rpc(RESOLVER, 'get_signal', { identifier: id }, 25000);

// ---- the live test, read at render (five-minute cache per code)
const CACHE = {};
async function liveTest(code) {
  const c = CACHE[code]; if (c && Date.now() - c.at < 300000) return c.v;
  const s = S[code]; let v = null;
  try {
    if (code === '200') { for (const id of s.candidates) { const a = await signal(id); if (a.signal === 'ACM-200') { v = { identifier: id, answer: a }; break; } } }
    else if (code === '451') {
      const cut = new Date(Date.now() - 3 * 86400000).toISOString().slice(0, 10);
      // Issuerwire's delta per market (ISIN-keyed markets first, then the LSE tickers); a row is a candidate when it is a filing dated inside the window
      for (const mk of ['NL', 'FR', 'UK']) {
        if (v) break;
        const d = await rpc(IW, 'get_delta', { market: mk, since: cut }, 12000).catch(() => null); let tried = 0;
        for (const rid of ((d && d.ids) || []).slice(0, 15)) {
          const row = await rpc(IW, 'get_row', { id: rid }, 8000).catch(() => null); const r = row && row.row;
          if (!r || r.type !== 'filing' || String(r.date) < cut) continue;
          const parts = String(r.issuer_key || '').split(':'), code = (parts[2] || '').toUpperCase();
          const id = /^[A-Z]{2}[A-Z0-9]{9}\d$/.test(code) ? code : (/^(LSE|AIM)$/i.test(parts[1] || '') ? `${parts[1].toUpperCase()}:${code}` : null);
          if (!id || ++tried > 4) continue;
          const a = await signal(id); if (a.signal === 'ACM-451') { v = { identifier: id, picked_from: { source: 'Issuerwire', market: mk, row: r.id, date: r.date, title: r.title }, answer: a }; break; }
        }
      }
      if (!v) for (const id of s.fallback) { const a = await signal(id); if (a.signal === 'ACM-451') { v = { identifier: id, picked_from: { source: 'the node\'s events (no FR Issuerwire filing in the window answered 451 at render)' }, answer: a }; break; } }
    }
    else if (code === '403') { for (const id of s.candidates) { const a = await signal(id); if (a.signal === 'ACM-403') { v = { identifier: id, answer: a }; break; } } if (!v) v = { identifier: s.candidates[0], answer: await signal(s.candidates[0]), note: 'no halt among the page\'s candidates answered ACM-403 at render (the halt has lifted); every node reads its halts page every night' }; }
    else if (code === '500') { const a = await rpc(RESOLVER, 'list_nodes', {}, 15000); v = { identifier: null, nodes_live: (a.live_nodes || []).length, answer: { signal: null, note: `ACM-500 is answered only when the home node does not answer; ${(a.live_nodes || []).length} of ${((a.nodes || []).filter(n => n.live)).length || (a.live_nodes || []).length} nodes answered at render` } }; }
    else { const a = await signal(s.example); v = { identifier: s.example, answer: a }; }
  } catch (e) { v = { error: 'the resolver did not answer at render', resolver: RESOLVER }; }
  CACHE[code] = { at: Date.now(), v }; return v;
}

const CSS = `*{margin:0;padding:0;box-sizing:border-box}
body{background:#faf8f3;color:#1a1a1a;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;-webkit-font-smoothing:antialiased}
.container{max-width:900px;margin:0 auto;padding:32px 24px 96px}
.topbar{font-size:12px;color:#6b6b6b;letter-spacing:.04em;margin-bottom:14px}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;color:#6b6b6b;font-size:11px;font-weight:600;margin:0 0 10px}
h1{font:700 28px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;margin:0 0 4px}
h1 .host{display:block;font-size:14px;color:#c84a1e;font-weight:600;margin-top:6px}
.badge{display:inline-block;font:700 11px/1 ui-monospace,monospace;letter-spacing:.08em;color:#f3eee0;background:#c84a1e;padding:5px 10px;border-radius:3px;margin:10px 6px 4px 0}
.badge.grey{background:#6b6b6b}
.subtitle{font-size:18px;color:#6b6b6b;font-style:italic;margin:8px 0 20px}
h2{font-size:18px;font-weight:700;margin:34px 0 12px;padding-bottom:8px;border-bottom:2px solid #c84a1e}
.meta{font-size:13px;color:#6b6b6b;margin:0 0 6px}
p{margin:0 0 10px}
table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0 24px}
th,td{text-align:left;padding:10px 14px;border-bottom:1px solid #d4cfc1;vertical-align:top;overflow-wrap:anywhere}
th{background:#f3eee0;font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
td.mono{font-family:ui-monospace,monospace;color:#c84a1e;font-weight:600}
tr.self td{background:#f3eee0}
a{color:#2455a3;text-decoration:none}
.surfaces{font-family:ui-monospace,monospace;font-size:12px;background:#1a1a1a;color:#f3eee0;padding:16px 20px;border-radius:4px;margin:12px 0 24px;white-space:pre-wrap;overflow-x:auto;line-height:1.7}
.connect{display:inline-block;font:600 14px/1 inherit;padding:11px 18px;border:0;border-radius:3px;background:#c84a1e;color:#f3eee0;cursor:pointer;margin:6px 0 10px}
form{display:grid;gap:6px;max-width:520px}form input,form textarea{font:inherit;padding:8px;border:1px solid #d4cfc1;border-radius:3px;background:#fff}form button{justify-self:start;font:600 13px/1 inherit;padding:9px 16px;border:0;border-radius:3px;background:#c84a1e;color:#f3eee0}.hp{display:none}
footer{margin-top:64px;padding-top:28px;border-top:1px solid #d4cfc1;font-size:12px;color:#6b6b6b;line-height:1.7}
.footer-brand{font-size:15px;font-weight:700;color:#1a1a1a;margin-bottom:8px}
@media (max-width:600px){.container{padding:24px 16px 72px}th,td{padding:8px}}`;

function connectBlock(code, id) {
  const cfg = { mcpServers: { getissuer: { type: 'http', url: RESOLVER } } };
  const first = id ? { method: 'tools/call', params: { name: 'get_signal', arguments: { identifier: id } } } : { method: 'tools/call', params: { name: 'list_nodes', arguments: {} } };
  return `<h2>Connect your AI</h2>
<p>One door for listed issuers: <b>${esc(RESOLVER)}</b> (MCP, Streamable HTTP, no account). Hand your agent the door and the first call; ${id ? `the first call returns <b>ACM-${code}</b>.` : 'ACM-500 is the answer only when a node does not answer, so the first call reads the live nodes.'}</p>
<button class="connect" type="button" data-copy="connect-text" id="connect-btn">Connect your AI</button> <span class="meta" id="connect-done"></span>
<div class="surfaces" id="connect-text">Add this MCP server to your agent:
${esc(JSON.stringify(cfg, null, 1))}

First call:
${esc(JSON.stringify(first))}
${id ? `→ "signal": "ACM-${code}"` : '→ the nodes on the roster, live'}

Machine form: https://acm-${code}.ai/connect.json</div>`;
}
function testBlock(code, v) {
  if (!v || v.error) return `<p class="meta">The resolver did not answer at render (${esc(RESOLVER)}). Read it yourself with the call below.</p>`;
  const a = v.answer || {};
  const lines = [`# Live test — read at render through the resolver (getissuer get_signal). No API key. No account.`];
  if (v.picked_from) lines.push(`# Test picked at render from ${v.picked_from.source}${v.picked_from.title ? `: "${v.picked_from.title}" (${v.picked_from.date}, row ${v.picked_from.row})` : ''}`);
  if (v.identifier) lines.push(`$ curl -s ${RESOLVER} -H "content-type: application/json" \\\n    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_signal","arguments":{"identifier":"${v.identifier}"}}}'`);
  else lines.push(`$ curl -s ${RESOLVER} -H "content-type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_nodes","arguments":{}}}'`);
  const show = {}; for (const k of ['signal', 'state', 'identifier', 'issuer', 'exchange', 'node', 'isin', 'as_of', 'filing', 'candidates', 'route', 'note', 'record', 'eco', 'read_at']) if (a[k] != null) show[k] = a[k];
  if (show.candidates) show.candidates = show.candidates.slice(0, 3);
  lines.push(JSON.stringify(show, null, 1));
  return `<div class="surfaces">${esc(lines.join('\n'))}</div>`;
}
function haltsBlock() {
  return `<table><thead><tr><th>Market</th><th>Halts page</th><th>ECO page</th></tr></thead><tbody>${Object.entries(HALTS).map(([cc, h]) => `<tr><td>${esc(h.country)}</td><td>${h.halts ? link(h.halts) : 'not found on the official pages — ' + (h.halts_checked || []).map(u => link(u)).join(' · ')}</td><td>${link(h.eco)}</td></tr>`).join('')}</tbody></table>`;
}
function table(code) {
  return `<table><thead><tr><th>Signal</th><th>Standard state</th><th>Action</th><th>Listed issuers (Allooloo)</th><th>CPG (GreenCore)</th></tr></thead><tbody>
${CODES.map(c => `<tr${c === code ? ' class="self"' : ''}><td class="mono">${link(`https://acm-${c}.ai/`, 'ACM-' + c)}</td><td>${S[c].std}</td><td>${esc(S[c].action)}</td><td>${S[c].kind === 'state' ? S[c].issuer : S[c].kind === 'advisory' ? S[c].issuer + ' (advisory)' : 'definition'}</td><td>${link(`https://cpg-${c}.ai/`, 'CPG-' + c)}</td></tr>`).join('\n')}
</tbody></table>`;
}
function footer() {
  return `<footer><p class="footer-brand">${OPERATOR}</p><p>Where agents read the market. One sourced, read-dated record for every listed company, served in the issuer’s own jurisdiction, callable by any agent over MCP and A2A.</p>
<p style="margin-top:8px">${esc(RECORDS)}</p>
<p style="margin-top:8px">Standard: <a href="https://acm-68000.org/">ACM-68000</a> (Agentic KG Holdings, reference operator, MIT) · <a href="https://allooloo.ai/markets">Electronic Compliance Objects</a> · <a href="https://getissuer.ai/">getissuer</a> · <a href="https://issuerwire.ai/">Issuerwire</a></p>
<p style="margin-top:8px"><a href="mailto:allooloo@hey.com">Support</a> · <a href="https://allooloo.io/status">Status</a> · <a href="https://allooloo.io/terms">Terms of Use</a> · <a href="https://allooloo.io/privacy">Privacy</a> · <a href="https://allooloo.io/security">Report a Security Issue</a> · <a href="/llms.txt">llms.txt</a></p>
<p style="margin-top:8px">This site sets no cookies. Artificial intelligence makes mistakes; a signal is the resolver’s reading of the public record at the time shown, not investment advice — read the filing.</p>
<p style="margin-top:10px">© 2026 ${OPERATOR}</p></footer>`;
}
function contact(host, code) {
  return `<h2>Contact Us</h2><form action="${FORM}" method="POST" accept-charset="UTF-8"><input type="hidden" name="site" value="${esc(host)}"><input type="hidden" name="source" value="acm-${code}"><input type="hidden" name="_subject" value="${esc(host)} contact"><input type="hidden" name="_next" value="https://allooloo.io/"><input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off">
<label for="f-email">email</label><input id="f-email" type="email" name="email" required autocomplete="email"><label for="f-message">message</label><textarea id="f-message" name="message" rows="5" required></textarea><button type="submit">send</button></form>`;
}
async function page(code, host) {
  const s = S[code], v = await liveTest(code);
  const firstId = code === '500' ? null : (v && v.identifier) || s.example || (s.candidates && s.candidates[0]);
  const body = `<div class="topbar">${esc(OFFICE)}</div>
<p class="eyebrow">ACM-68000 · Seven Canonical Signals</p>
<h1>ACM-${code} · ${s.std}<span class="host">${esc(host)}</span></h1>
<div class="badge">STANDARD: ${s.std}</div><div class="badge grey">LISTED ISSUERS: ${s.kind === 'definition' ? 'DEFINITION' : s.issuer + (s.kind === 'advisory' ? ' · ADVISORY' : '')}</div>
<p class="subtitle">ACM-${code} · ${s.std} · ${esc(s.action)}</p>
<h2>Definition — the standard</h2>
<p>ACM-${code} is one of the seven canonical signals of ACM-68000. State: <b>${s.std}</b>. Action: <b>${esc(s.action)}</b> The standard is held by Agentic KG Holdings (the Agentic Private Office) as reference operator under the MIT licence, and implemented by any company's doors: ${link('https://acm-68000.org/')}.</p>
<h2>Listed issuers — ${OPERATOR}, operator and implementer</h2>
<p class="meta">${esc(RECORDS)}</p>
<p><b>${s.kind === 'definition' ? 'On the resolver' : 'Issuer state: ' + s.issuer + (s.kind === 'advisory' ? ' (advisory)' : '')}.</b> ${esc(s.when)}</p>
${code === '403' ? `<p>The halts pages of the live markets, read from each market's Electronic Compliance Object:</p>${haltsBlock()}` : ''}
${testBlock(code, v)}
${connectBlock(code, firstId)}
<h2>The Seven Signals</h2>
${table(code)}
<h2>Doors by what they resolve</h2>
<p class="meta">${ROUTES.map(([, w, d, o]) => `${esc(w)} → ${link(d)} (${esc(o)})`).join('<br>')}</p>
<h2>Machine Surfaces</h2>
<p class="meta">/signal.json · /signals.json · /connect.json · /nodes.json · /health.json · /dataset.jsonld · /llms.txt · /index.md · /sitemap.xml<br>/.well-known/agent-card.json · /.well-known/mcp.json · /.well-known/api-catalog · /.well-known/ai-catalog.json · /.well-known/security.txt</p>
${signalBlock(code, s, firstId)}
${contact(host, code)}`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ACM-${code} · ${s.std}</title><meta name="description" content="ACM-${code} · ${s.std} · ${esc(s.action)} Listed issuers: ${esc(s.kind === 'definition' ? 'definition' : s.issuer)}. Live test through the resolver mcp.getissuer.ai."><link rel="canonical" href="https://${esc(host)}/"><style>${CSS}</style></head><body><div class="container">${body}${footer()}</div><script src="/connect.js" defer></script></body></html>`;
}

const CONNECT_JS = `(function(){var b=document.getElementById('connect-btn');if(!b)return;b.addEventListener('click',function(){var t=document.getElementById('connect-text').innerText;var d=document.getElementById('connect-done');(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){d.textContent='copied — paste it to your agent';},function(){d.textContent='select the block below and copy it';});});})();\n`;
const H = (ct, extra) => ({ 'content-type': ct, 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY', 'X-ACM-Version': VERSION, 'X-CMR-Operator': OPERATOR, 'access-control-allow-origin': '*', ...(extra || {}) });
const J = (o, st, cache) => new Response(JSON.stringify(o, null, 1), { status: st || 200, headers: H('application/json; charset=utf-8', { 'cache-control': cache || 'public, max-age=300' }) });
const T = (s, ct) => new Response(s, { headers: H(ct || 'text/plain; charset=utf-8', { 'cache-control': 'public, max-age=300' }) });
const R301 = u => new Response(null, { status: 301, headers: { location: u, 'cache-control': 'public, max-age=3600', 'X-ACM-Version': VERSION } });
const sigJson = c => ({ code: 'ACM-' + c, state: S[c].std, action: S[c].action, page: `https://acm-${c}.ai/`, listed_issuers: { state: S[c].kind === 'definition' ? null : S[c].issuer, kind: S[c].kind, when: S[c].when, resolver: RESOLVER, tool: 'get_signal' }, cpg: `https://cpg-${c}.ai/`, standard: 'https://acm-68000.org/' });

async function machine(code, host, p, env) {   // ENUM-01 (DAY ORDER 6): async — /nodes.json reads the roster
  const s = S[code], me = `https://${host}/`;
  if (p === '/signals.json') return J({ protocol: 'ACM-68000', standard: 'https://acm-68000.org/', operator_of_reference: 'Agentic KG Holdings (MIT)', this_page_operator: OPERATOR, signals: CODES.map(sigJson), routing: ROUTES.map(([k, w, d, o]) => ({ resolves: k, what: w, door: d, operator: o })) });
  if (p === '/connect.json') return J({ door: RESOLVER, transport: 'streamable-http', auth: 'none for reads', mcpServers: { getissuer: { type: 'http', url: RESOLVER } }, first_call: code === '500' ? { name: 'list_nodes', arguments: {} } : { name: 'get_signal', arguments: { identifier: (CACHE[code] && CACHE[code].v && CACHE[code].v.identifier) || s.example || (s.candidates || [])[0] } }, returns: code === '500' ? 'the live nodes (ACM-500 is answered only when a node does not answer)' : 'ACM-' + code });
  if (p === '/.well-known/mcp.json') return J({ $schema: 'https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json', title: `ACM-${code} — the signal, answered by the resolver`, description: `The ACM-68000 signal ACM-${code} for listed issuers is answered by getissuer (get_signal). Doors by what they resolve: GTINs → gtinfetch.ai/mcp · listed issuers → mcp.getissuer.ai/mcp · receipts → mcp.rco-a2a.ai/mcp.`, websiteUrl: me,
    remotes: ROUTES.map(([, , d]) => ({ type: 'streamable-http', url: d })), routing: ROUTES.map(([k, w, d, o]) => ({ resolves: k, what: w, door: d, transport: 'streamable-http', operator: o })), payment: paymentDoor(env || {}), mcp_paths: { signals: 'https://mcp.getissuer.ai/signals/mcp', resolver: RESOLVER }, receipts: { door: 'https://mcp.rco-a2a.ai/mcp', note: 'every get_signal leaves an RCO receipt' }, _meta: { 'ai.allooloo/acm-signals': { signal: 'ACM-' + code, tool: 'get_signal', operator: OPERATOR, version: VERSION } } });
  if (p === '/.well-known/agent-card.json') return J({ protocolVersion: '0.3.0', name: `ACM-${code} · ${s.std}`, description: `The ACM-68000 signal ACM-${code} (${s.std}: ${s.action}) for listed issuers, answered live by getissuer's get_signal. ${s.when}`, url: me, version: VERSION,
    provider: { organization: OPERATOR, url: 'https://allooloo.io' }, supportedInterfaces: [{ url: RESOLVER, protocolBinding: 'JSONRPC', transport: 'streamable-http', description: 'getissuer — the listed-issuer resolver' }], defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'], capabilities: { streaming: false, pushNotifications: false },
    skills: [{ id: 'get-signal', name: 'Get the ACM-68000 signal', description: `get_signal(identifier) at ${RESOLVER}: ACM-200 TRADING · ACM-404 NOT ON THE REGISTER · ACM-451 READ THE FILING (named) · ACM-300 CONDITIONAL · ACM-000 NOT APPLICABLE · ACM-500 SYSTEM ERROR · ACM-403 HALTED (from the home node\'s halt flag).`, tags: ['acm-68000', 'signal', 'listed-issuers'], examples: ['FR0000120271'] }]
      .concat(ROUTES.map(([k, w, d, o]) => ({ id: 'route-' + k, name: 'Route: ' + w, description: `${w} resolve at ${d} (${o}).`, tags: ['routing', k, 'mcp'] }))), routing: ROUTES.map(([k, , d]) => ({ resolves: k, door: d })) });
  if (p === '/.well-known/api-catalog') return new Response(JSON.stringify({ linkset: [{ anchor: me, 'service-doc': [{ href: me + 'llms.txt', type: 'text/plain' }], status: [{ href: me + 'health.json' }], service: ROUTES.map(([, w, d, o]) => ({ href: d, title: `${w} → ${d.replace('https://', '')} (${o})`, type: 'application/json' })).concat([{ href: me + 'signal.json', title: `ACM-${code} — this signal, live` }]) }] }, null, 1), { headers: H('application/linkset+json', { 'cache-control': 'public, max-age=300' }) });
  if (p === '/.well-known/ai-catalog.json') return J({ specVersion: '1.0', host: { displayName: `ACM-${code}`, identifier: `did:web:${host}` }, entries: ROUTES.map(([k, w, d, o]) => ({ identifier: `urn:air:${host}:route:${k}`, displayName: `Route: ${w} → ${d.replace('https://', '')}`, type: 'application/json', url: d, capabilities: ['routing.' + k], description: `${w} resolve at ${d}, operated by ${o.split(' — ').pop()}.` }))
    .concat([{ identifier: `urn:air:${host}:signal:acm-${code}`, displayName: `ACM-${code} · ${s.std}`, type: 'application/json', url: me + 'signal.json', capabilities: ['acm-68000.signal', 'get_signal'], description: `The ACM-68000 signal ACM-${code} for listed issuers; answered live by ${RESOLVER} get_signal.`, representativeQueries: ['what does ACM-' + code + ' mean', 'what signal does this ISIN carry', 'is this security halted'] }]) });
  if (p === '/nodes.json') return J({ this_host: host, doors: ROUTES.map(([k, w, d, o]) => ({ resolves: k, what: w, door: d, operator: o })), allooloo_nodes: { holds: 'listed issuers — one sourced, signed record per listed company, served in its own jurisdiction', resolver: RESOLVER, nodes: (((await rpc(RESOLVER, 'list_nodes', {}).catch(() => null)) || {}).nodes || []).filter(n => n.live).map(n => { const cc = n.node.split('-')[0]; const h = HALTS[cc] || {}; return { node: n.node, market: n.country, holds: 'listed issuers', door: n.regional_door || null, eco: h.eco || `https://${cc}-eco.ai/`, halts_page: h.halts || null, ...(h.halts ? {} : { halts_page_gap: 'no halts page line in the halt-source policy (ENUM-01 gap, named)' }) }; }) }   /* ENUM-01: the roster (list_nodes), HALTS is the halt-source policy */, cpg_profile: { holds: 'GTIN product records — the CPG application profile of ACM-68000 (GreenCore Solutions Corp.)', signal_pages: CODES.map(c => `https://cpg-${c}.ai/`) } });
  if (p === '/dataset.jsonld') return new Response(JSON.stringify({ '@context': 'https://schema.org', '@type': 'Dataset', name: `ACM-${code} · ${s.std} — signal page`, url: me, description: `The ACM-68000 signal ACM-${code} for listed issuers. ${s.when}`, publisher: { '@type': 'Organization', name: OPERATOR, url: 'https://allooloo.io/' }, isBasedOn: 'https://acm-68000.org/', license: 'https://opensource.org/licenses/MIT',
    distribution: ROUTES.map(([, w, d, o]) => ({ '@type': 'DataDownload', name: `${w} — MCP door`, description: `${w} resolve at this door (${o}).`, contentUrl: d, encodingFormat: 'application/json' })).concat([{ '@type': 'DataDownload', name: `ACM-${code} — this signal`, contentUrl: me + 'signal.json', encodingFormat: 'application/json' }]) }, null, 1), { headers: H('application/ld+json', { 'cache-control': 'public, max-age=300' }) });
  if (p === '/llms.txt' || p === '/index.md') return T(`# ${host} — ACM-${code} · ${s.std}\n\n${ROUTE_TXT}\n\n${p === '/index.md' ? '> ' + host + '\n\n' : ''}ACM-${code} · ${s.std} · ${s.action} — one of the seven canonical signals of ACM-68000 (https://acm-68000.org/; Agentic KG Holdings, reference operator, MIT).\nListed issuers (${OPERATOR}, operator of this page): ${s.kind === 'definition' ? 'definition' : s.issuer + (s.kind === 'advisory' ? ' (advisory)' : '')} — ${s.when}\nResolver: ${RESOLVER} — get_signal(identifier) returns the signal live.\nCPG application profile (GreenCore Solutions Corp.): https://cpg-${code}.ai/\nThe seven: ${CODES.map(c => `https://acm-${c}.ai/`).join(' · ')}\nMachine surfaces: /signal.json · /signals.json · /connect.json · /nodes.json · /health.json · /dataset.jsonld · /.well-known/agent-card.json · /.well-known/mcp.json · /.well-known/api-catalog · /.well-known/ai-catalog.json\n${RECORDS}\n`, p === '/index.md' ? 'text/markdown; charset=utf-8' : 'text/plain; charset=utf-8');
  if (p === '/health.json') return J({ status: 'ok', host, version: VERSION, signal: 'ACM-' + code, resolver: RESOLVER }, 200, 'no-store');
  if (p === '/robots.txt') return T(`User-agent: *\nAllow: /\nSitemap: https://${host}/sitemap.xml\n`);
  if (p === '/sitemap.xml') return T(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${['/', '/signal.json', '/signals.json', '/llms.txt'].map(x => `<url><loc>https://${host}${x}</loc></url>`).join('')}</urlset>\n`, 'application/xml');
  if (p === '/.well-known/security.txt') return T(`Contact: mailto:allooloo@hey.com\nContact: https://allooloo.io/security\nExpires: 2027-10-24T00:00:00Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\n`);
  if (p === '/connect.js') return new Response(CONNECT_JS, { headers: H('application/javascript; charset=utf-8', { 'cache-control': 'public, max-age=3600' }) });
  return null;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url); let host = url.hostname.toLowerCase(); if (host.startsWith('www.')) host = host.slice(4);
    const m = host.match(/^acm-(000|200|300|403|404|451|500)\.(ai|org|com)$/); if (!m) return J({ error: 'not_found' }, 404, 'no-store');
    const [, code, tld] = m;
    if (tld !== 'ai') return R301(`https://acm-${code}.ai${url.pathname}${url.search}`);
    const p = url.pathname;
    if (p === '/' || p === '/index.html') return new Response(await page(code, host), { headers: H('text/html; charset=utf-8', { 'cache-control': 'public, max-age=60, must-revalidate' }) });
    if (p === '/signal.json') { const v = await liveTest(code); return J({ ...sigJson(code), live_test: v }, 200, 'public, max-age=60'); }
    const r = await machine(code, host, p, env); if (r) return r;
    return J({ error: 'not_found', host, paths: ['/', '/signal.json', '/signals.json', '/connect.json', '/nodes.json', '/health.json', '/dataset.jsonld', '/llms.txt', '/index.md', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/api-catalog', '/.well-known/ai-catalog.json'] }, 404, 'no-store');
  }
};
