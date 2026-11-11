import { acmFirstResponse, acmFirst } from './acm_first.js';   // TEXTS-01 (ACM-68000 v1.1)
// stack-pages — STACK-01 (2026-10-30). Serves the generated bundle (stack_pages.py): the trunk pages eco-10060.org, rco-10060.org, acm-68000.org (+ .ai, the
// identical body at its own host), the office pages a2a-auditor.ai, a2a-schema.ai, acm-registry.org (their twins 301 to them), and the six later SM-ECO-10060
// members (hk ky bm je tw lu × .org/.ai/.com, identical bodies at their own hostnames, no 301). Nothing typed here: every body is the bundle's.
// {{LIVE_RECEIPT}} is the chain's latest anchored tip (META.tip), verified at render through verify_receipt at mcp.rco-records.ai (five-minute cache).
import { BUNDLE, META } from './bundle.js';
const VERSION = '2026-11-01.2';   // .2 = TWINS-01a: cpg-68000.org/ is the page; a machine caller of / is sent 301 → /cpg.json (META.machine)
const V_PREV1 = '2026-11-01.1';   // .1 = TWINS-01: eco/rco .ai/.com serve the .org bytes (META.alias); Link rel=canonical (META.link)
const V_PREV = '2026-10-31.2';   // .2 = TEXTS-02: a superseded page renders its successor's full page beneath the pointer; READ-01 first-use rule
const DOOR = 'https://mcp.rco-records.ai/mcp';
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let LIVE = null, LIVE_AT = 0;
async function liveReceipt() {
  if (LIVE && Date.now() - LIVE_AT < 300000) return LIVE;
  const id = META.tip.id; let html;
  try {
    const r = await fetch(DOOR, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'Allooloo stack-pages (STACK-01)' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'verify_receipt', arguments: { id } } }), signal: AbortSignal.timeout(10000) });
    const t = await r.text(); const j = JSON.parse(t.slice(t.indexOf('{'))); const s = j.result.structuredContent || JSON.parse(j.result.content[0].text);
    const v = s.verification || {}, rc = s.receipt || {};
    const mark = b => b ? '<span class="ok">ok</span>' : '<span class="bad">FAIL</span>';
    html = `<p class="meta">verify_receipt at <a href="${DOOR}">mcp.rco-records.ai/mcp</a>, read ${esc(new Date().toISOString())} — the result is the door's, shown as answered.</p>
<table><tbody><tr><th scope="row">id</th><td class="mono"><a href="https://rco-records.ai/receipts/${esc(id)}">${esc(id)}</a></td></tr>
<tr><th scope="row">seq</th><td>${esc(rc.seq)} (anchored tip of night ${esc(META.tip.night)})</td></tr>
<tr><th scope="row">subject · market</th><td>${esc(rc.subject)} (${esc(rc.subject_type)}) · ${esc(rc.market)}</td></tr>
<tr><th scope="row">rule_version</th><td>${esc(rc.rule_version)}</td></tr><tr><th scope="row">cleared_at</th><td>${esc(rc.cleared_at)}</td></tr>
<tr><th scope="row">answer_hash</th><td class="mono">${esc(rc.answer_hash)}</td></tr><tr><th scope="row">prev_hash</th><td class="mono">${esc(rc.prev_hash)}</td></tr>
<tr><th scope="row">hash · id · signature</th><td>${mark(v.hash_ok)} · ${mark(v.id_ok)} · ${mark(v.sig_ok)} under kid ${esc(v.kid)} — <b>${v.valid ? 'VALID' : 'NOT VALID'}</b></td></tr></tbody></table>`;
  } catch (e) { html = `<p class="bad">verify_receipt did not answer at render (${esc(String(e).slice(0, 120))}). The receipt is ${esc(id)}; read it at <a href="https://rco-records.ai/receipts/${esc(id)}">rco-records.ai/receipts/${esc(id)}</a>.</p>`; }
  LIVE = html; LIVE_AT = Date.now(); return LIVE;
}
// STACK-01 addendum (CEO ruling 2026-10-31): the four CPG pages keep their bodies as their own origins serve them; at request time only the holder line
// becomes Allooloo's and the typed counts are struck. Every other byte passes through untouched.
const LIVE_ORIGIN = {};   // CPG-02 (2026-10-31): the umbrella's page and the former sister families are generated now (bundle); the proxies of STACK-01 are kept below, unused
const LIVE_ORIGIN_PRE_CPG02 = {
  'cpg-68000.ai': { origin: 'https://cull-cpg-68000-door.pages.dev', verify: 'cpg-68000.ai' },
  'sm-aio-cpg.org': { origin: 'https://cull-gp-aio-1.pages.dev', verify: 'sm-aio-cpg.org' },
  'sm-esg-cpg.org': { origin: 'https://cull-gp-esg-1.pages.dev', verify: 'sm-esg-cpg.org' },
  'sm-amp-cpg.org': { origin: 'https://sm-amp-cpg.jollyflower-416db105.francecentral.azurecontainerapps.io' },
};
const STRIKE = [
  [/© 202[67] GreenCore Solutions Corp\. \(GSC\) · Protocol operator: GSC/g, '© 2027 Allooloo Technologies Corp. · Standard held by Allooloo Technologies Corp. · Open standard, MIT licence.'],
  [/The family is 50 nodes — this apex/g, 'The family is this apex'],
  [/The 50 nodes — the doors/g, 'The nodes — the doors'],
  [/1 Sovereign Manifest apex \+ 49 jurisdiction nodes = 50 nodes\./g, 'the Sovereign Manifest apex and its jurisdiction nodes.'],
  [/all 49 jurisdiction nodes/g, 'all its jurisdiction nodes'],
  [/one apex and 49 jurisdiction doors/g, 'one apex and its jurisdiction doors'],
  [/49 jurisdictional resolvers \+ apex/g, 'the jurisdictional resolvers and the apex'],
];
async function liveStruck(request, host, url) {
  const o = LIVE_ORIGIN[host]; const h = new Headers(request.headers); h.delete('host'); if (o.verify) h.set('x-verify-host', o.verify);
  const r = await fetch(o.origin + url.pathname + url.search, { method: request.method === 'HEAD' ? 'HEAD' : 'GET', headers: h, redirect: 'manual' });
  const ct = r.headers.get('content-type') || '';
  if (!/text\/|json|xml|markdown/.test(ct) || request.method === 'HEAD') return new Response(r.body, { status: r.status, headers: r.headers });
  let t = await r.text(); for (const [a, b] of STRIKE) t = t.replace(a, b);
  const hh = new Headers(r.headers); hh.delete('content-length'); hh.set('X-Stack-Version', VERSION);
  return new Response(t, { status: r.status, headers: hh });
}
// TEXTS-02 (CEO 2026-10-31): a superseded page keeps its SUPERSEDED eyebrow and pointer, and the successor's full page renders beneath it — taken at request
// time from the successor's own page (this bundle's, or the page book-pages serves), from its eyebrow to its footer, its title set as a section heading.
// The expansion of ACM-68000 is taken out of the spliced part and the whole page is then read once by the first-use rule (once per page).
const unwriteAcm = z => z.replace(/ACM-68000(\s*)\(Agent Clearance Manifest — /g, 'ACM-68000$1(').replace(/ACM-68000 \(Agent Clearance Manifest\)/g, 'ACM-68000');
async function withSuccessor(body) {
  const m = /<!--SUCCESSOR:(https:\/\/[^>]+?)-->/.exec(body); if (!m) return body;
  const u = new URL(m[1]); const own = BUNDLE[u.hostname] && BUNDLE[u.hostname][u.pathname]; let src = own ? own[1] : null;
  if (!src) { try { const r = await fetch(u.href, { headers: { 'user-agent': 'Allooloo stack-pages (TEXTS-02 successor)' }, cf: { cacheTtl: 300 } }); if (r.ok) src = await r.text(); } catch (e) { src = null; } }
  const a = src ? src.indexOf('<p class="eyebrow"') : -1, b = src ? src.indexOf('<footer') : -1;
  if (a < 0 || b < a) return body.replace(m[0], '');
  const part = src.slice(a, b).replace('<h1>', '<h2 class="successor">').replace('</h1>', '</h2>');
  return body.replace(m[0], `<section class="successor">${unwriteAcm(part)}</section>`);
}
const SEC = { 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Strict-Transport-Security': 'max-age=31536000', 'X-Stack-Version': VERSION, 'access-control-allow-origin': '*' };
export default {
  async fetch(request) {
    const url = new URL(request.url); let host = url.hostname.toLowerCase(); if (host.startsWith('www.')) host = host.slice(4);
    if (LIVE_ORIGIN[host]) return acmFirstResponse(await liveStruck(request, host, url));   // TEXTS-01: the proxied pages get the ACM first use too
    if (META.twins[host]) return new Response(null, { status: 301, headers: { location: `https://${META.twins[host]}${url.pathname}${url.search}`, 'cache-control': 'public, max-age=3600', ...SEC } });
    if (META.alias && META.alias[host]) host = META.alias[host];   // TWINS-01: a live twin serves its .org site as is
    const site = BUNDLE[host]; if (!site) return new Response(JSON.stringify({ error: 'not_found', host }), { status: 404, headers: { 'content-type': 'application/json', ...SEC } });
    const p = url.pathname === '/index.html' ? '/' : url.pathname;
    const mto = META.machine && META.machine[host] && META.machine[host][url.pathname];   // TWINS-01a: the old descriptor root, for machine callers
    if (mto && !/text\/html/i.test(request.headers.get('accept') || '')) return new Response(null, { status: 301, headers: { location: `https://${host}${mto}`, vary: 'Accept', 'cache-control': 'public, max-age=300', ...SEC } });
    const f = site[p] || (p.endsWith('/') && site[p + 'index.html']);
    if (!f) return new Response(JSON.stringify({ error: 'not_found', host, paths: Object.keys(site).sort() }, null, 1), { status: 404, headers: { 'content-type': 'application/json', ...SEC } });
    let [ct, body] = f;
    if (body.includes('{{LIVE_RECEIPT}}')) body = body.replace('{{LIVE_RECEIPT}}', await liveReceipt());
    if (body.includes('<!--SUCCESSOR:')) body = acmFirst(unwriteAcm(await withSuccessor(body)), 'html');   // TEXTS-02: the whole page read once (pointer, successor, footer)
    const link = META.link && META.link[host] && META.link[host][p];
    return new Response(body, { headers: { 'content-type': ct, 'cache-control': ct.startsWith('text/html') ? 'public, max-age=60, must-revalidate' : 'public, max-age=300', ...SEC, ...(link ? { link } : {}), ...(mto ? { vary: 'Accept' } : {}) } });
  }
};
