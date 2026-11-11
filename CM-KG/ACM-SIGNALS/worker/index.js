// acm-signals — TEXTS-01 (2026-10-31): the ACM-68000 signal pages re-cut from ACM-68000 canonical text v1.1. One page per signal of the clearance
// vocabulary (§6) on acm-200 / acm-403 / acm-404 / acm-451 .ai (the .org and .com twins answer 301 to the .ai, path and query kept): its Reading and
// Boundary, its column of the §6.1 family binding table, the §6 and §6.1 paragraphs and the canonical mission (§9), from signals-canon.json
// (signals_canon.py, read from canon-texts.json) — nothing typed. The look is the standard's own page (acm-68000.org as stack-pages serves it).
// Reserved codes (v1.1 ruling): ACM-000, ACM-300 and ACM-500 are listed in the register as reserved, never served, never reused — every request on
// their zones forwards (301) to the standard's page, https://acm-68000.org/. Agent Clearance Manifest is written out once on first use (acm_first.js).
// The prior worker (seven signals, live tests, the office line) is kept beside as index.js.pre-texts01-2026-10-31.
import C from './signals-canon.json';
import { acmFirst } from './acm_first.js';
const VERSION = '2026-10-31.1';
const STANDARD = 'https://acm-68000.org/'; const REGISTER = 'https://acm-68000.org/register.json'; const RESOLVER = 'https://mcp.getissuer.ai/mcp';
const LIVE = Object.keys(C.signals).map(c => c.slice(4)); const RESERVED = C.reserved.map(r => r.code.slice(4));
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const SEC = { 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'strict-transport-security': 'max-age=31536000; includeSubDomains', 'X-ACM-Version': VERSION };
const J = (o, status = 200) => new Response(JSON.stringify(o, null, 1) + '\n', { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', ...SEC } });
const T = (t, ct = 'text/plain; charset=utf-8') => new Response(acmFirst(t, 'text'), { headers: { 'content-type': ct, 'cache-control': 'public, max-age=300', ...SEC } });
const R301 = to => new Response(null, { status: 301, headers: { location: to, 'cache-control': 'public, max-age=3600', ...SEC } });
const table = (head, rows) => `<table><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
const VER = (/Version (\d+\.\d+)/.exec(C.head[2]) || [])[1];
function sig(code) { const s = C.signals['ACM-' + code]; return { standard: 'ACM-68000', expansion: 'Agent Clearance Manifest', standard_version: VER, signal: s.code, reading: s.reading, boundary: s.boundary, bindings: s.bindings, standard_page: STANDARD, register: REGISTER, resolver: RESOLVER, reserved: C.reserved }; }
function page(code, host) {
  const s = C.signals['ACM-' + code];
  const body = `<p class="eyebrow">ACM-68000 · ${esc(C.section)}</p><h1>${esc(s.code)} · ${esc(s.reading)}<span class="host">${esc(host)}</span></h1>`
    + `<p class="mission"><b>${esc(C.mission)}</b></p>`
    + `<h2>${esc(C.section)}</h2>` + table(C.table_head, [[s.code, s.reading, s.boundary]]) + C.paragraphs.map(t => `<p>${esc(t)}</p>`).join('')
    + `<h2>${esc(C.binding_heading)}</h2>` + table(['Family', s.code], s.bindings.map(b => [b.family, b.outcome])) + C.binding_paragraphs.map(t => `<p>${esc(t)}</p>`).join('')
    + `<h2>Machine surfaces</h2><p class="meta"><a href="/signal.json">/signal.json</a> · <a href="/signals.json">/signals.json</a> · <a href="/llms.txt">/llms.txt</a> · <a href="/.well-known/agent-card.json">/.well-known/agent-card.json</a> · <a href="${STANDARD}">acm-68000.org</a> · <a href="${REGISTER}">register.json</a> · get_signal at <a href="${RESOLVER}">${RESOLVER.replace('https://', '')}</a></p>`;
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(s.code)} · ${esc(s.reading)} — ACM-68000</title>`
    + `<meta name="description" content="${esc(s.code)} · ${esc(s.reading)}: ${esc(s.boundary)}"><link rel="canonical" href="https://${esc(host)}/"><style>${C.shell.style}</style></head><body><div class="container">`
    + `<div class="topbar">${C.shell.topbar}</div>${body}${C.shell.footer}</div></body></html>`;
  return acmFirst(html, 'html');
}
function llms(code, host) {
  const s = C.signals['ACM-' + code];
  return `# ${host} — ${s.code} · ${s.reading}\n\n${C.mission}\n\n${C.section}\n${s.code} · ${s.reading} — ${s.boundary}\n\n${C.paragraphs.join('\n\n')}\n\n${C.binding_heading}\n${s.bindings.map(b => `- ${b.family}: ${b.outcome}`).join('\n')}\n\n${C.binding_paragraphs.join('\n\n')}\n\nStandard: ${STANDARD} · register: ${REGISTER} · get_signal: ${RESOLVER}\n\n${C.shell.topbar.replace(/<[^>]+>/g, '')}\n`;
}
export default {
  async fetch(request) {
    const WMD = r => { const a = (r.headers.get('accept') || '').toLowerCase(); return a.includes('text/markdown') && (a.indexOf('text/markdown') < (a.indexOf('text/html') === -1 ? 1e9 : a.indexOf('text/html'))); };   // CLEAN-01: estate-pages' wantsMarkdown
    const url = new URL(request.url); let host = url.hostname.toLowerCase(); if (host.startsWith('www.')) host = host.slice(4);
    const m = host.match(/^acm-(\d{3})\.(ai|org|com|io)$/); if (!m) return J({ error: 'not_found' }, 404);
    const [, code, tld] = m;
    if (RESERVED.includes(code)) return R301(STANDARD);   // reserved: never served, its zone forwards to the standard's page
    if (!LIVE.includes(code)) return J({ error: 'not_found', host }, 404);
    if (tld !== 'ai') return R301(`https://acm-${code}.ai${url.pathname}${url.search}`);
    const p = url.pathname; const me = `https://${host}/`;
    if ((p === '/' || p === '/index.html') && WMD(request)) { const m = T(llms(code, host), 'text/markdown; charset=utf-8'); m.headers.set('vary', 'Accept'); return m; }   // CLEAN-01: Markdown for Agents (the page's own /index.md)
    if (p === '/' || p === '/index.html') return new Response(page(code, host), { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300', vary: 'Accept', ...SEC } });
    if (p === '/signal.json') return J(sig(code));
    if (p === '/signals.json') return J({ standard: 'ACM-68000', expansion: 'Agent Clearance Manifest', standard_version: VER, source: `ACM-68000 canonical text v${VER} §6`, signals: Object.values(C.signals).map(s => ({ code: s.code, reading: s.reading, boundary: s.boundary, page: `https://acm-${s.code.slice(4)}.ai/` })), reserved: C.reserved, standard_page: STANDARD });
    if (p === '/llms.txt' || p === '/index.md') return T(llms(code, host), p === '/index.md' ? 'text/markdown; charset=utf-8' : 'text/plain; charset=utf-8');
    if (p === '/.well-known/agent-card.json') { const s = C.signals['ACM-' + code]; return J({ protocolVersion: '0.3.0', name: `${s.code} · ${s.reading}`, description: `${s.code} · ${s.reading}: ${s.boundary}`, url: me, provider: { organization: 'Allooloo Technologies Corp.', url: 'https://allooloo.io' }, holder: 'Allooloo Technologies Corp.', licence: 'MIT', standard: 'ACM-68000', expansion: 'Agent Clearance Manifest', documentationUrl: me + 'llms.txt', kind: 'reference surface (serves no tools)', capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json'], defaultOutputModes: ['application/json', 'text/plain'], version: VERSION, supportedInterfaces: [{ url: me, protocolBinding: 'HTTP+JSON', protocolVersion: '1.0' }, { url: RESOLVER, protocolBinding: 'HTTP+JSON', transport: 'streamable-http', description: 'get_signal — the resolver this page names' }], skills: [{ id: 'get-signal', name: `${s.code} · ${s.reading}`, description: `${s.code} · ${s.reading}: ${s.boundary} The page is ${me}; get_signal at ${RESOLVER} returns the signal for a security.`, tags: ['acm-68000', 'signal'], examples: [me + 'signal.json'] }] }); }   // AUDIT-01 F1
    if (p === '/health.json') return J({ status: 'ok', host, version: VERSION, signal: 'ACM-' + code });
    if (p === '/robots.txt') return T(`User-agent: *\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\nAllow: /\nSitemap: ${me}sitemap.xml\n`);
    if (p === '/sitemap.xml') return T(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${['', 'signal.json', 'signals.json', 'llms.txt'].map(x => `<url><loc>${me}${x}</loc></url>`).join('')}</urlset>\n`, 'application/xml');
    if (p === '/.well-known/security.txt') return T(`Contact: https://allooloo.io/#contact\nContact: https://allooloo.io/security\nExpires: 2027-10-31T00:00:00Z\nPreferred-Languages: en\nCanonical: ${me}.well-known/security.txt\n`);
    return J({ error: 'not_found', host, paths: ['/', '/signal.json', '/signals.json', '/llms.txt', '/index.md', '/health.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/robots.txt', '/sitemap.xml'] }, 404);
  }
};
