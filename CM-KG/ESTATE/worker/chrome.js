// ORDER-020 §0–§3 + CEO corrections (Sept 12 2026) — the record-grade chrome: title line first, mark, nine-tab nav, state pill; one form; one footer.
// Regions are never abbreviated: REGION_FULL is the list of record and is written out wherever residency appears. The kicker is never the opening line.
export const OPERATOR = 'Allooloo Technologies Corp.';
export const CORPORATE = 'https://allooloo.io';
export const CONTACT = 'https://allooloo.io/#contact';   // the contact form is the only support door (CEO, Sept 12 2026)
export const CONTACT2 = 'allooloo@hey.com';
export const LEGAL = 'legal@allooloo.ai';
export const APEX = 'https://mcp.capitalmarketsknowledgegraph.ai';
export const APEX_AGENT = 'https://agent.capitalmarketsknowledgegraph.ai';
export const FORM = 'https://formspree.io/f/moeqzgll';
export const SURFACES_VERSION = '2026-09-13.8';   // bumped on every estate deploy; prior renders go to the pond (snapshot_surfaces.py)
export const KICKER = 'Microsoft AI Cloud Partner · Microsoft Azure · eleven regions, in-country';   // Proof section first line and footer line only
export const COMPANY_TITLE = 'AI Agents · MCP + A2A · Capital Markets Knowledge Graph — Allooloo';
export const REGION_FULL = { ca: 'Canada Central (Toronto, Canada)', us: 'East US (Virginia, United States)', uk: 'UK South (London, United Kingdom)', fr: 'France Central (Paris, France)', nl: 'West Europe (Amsterdam, Netherlands)', ch: 'Switzerland North (Zurich, Switzerland)', de: 'Germany West Central (Frankfurt, Germany)', au: 'Australia East (Sydney, Australia)', sg: 'Southeast Asia (Singapore)', jp: 'Japan East (Tokyo, Japan)', kr: 'Korea Central (Seoul, South Korea)', hk: 'East Asia (Hong Kong — beacon, partner wanted)' };
export const REGIONS_LIST = ['ca', 'us', 'uk', 'fr', 'nl', 'ch', 'de', 'au', 'sg', 'jp', 'kr', 'hk'].map(cc => REGION_FULL[cc]).join(' · ');
export const NAV = [['HOME', 'https://allooloo.io/'], ['Trades', 'https://agentic-trades.ai/'], ['ASK', 'https://agentic-ask.ai/'], ['Coverage', 'https://agentic-coverage.ai/'], ['ESG', 'https://agentic-esg.ai/'], ['Issuers', 'https://agentic-issuers.ai/'], ['Disclosure', 'https://agentic-disclosure.ai/'], ['Registries', 'https://agentic-registries.ai/'], ['RADAR', 'https://agentic-radar.ai/']];
export const CSP = "default-src 'none'; img-src 'self' data:; style-src 'self'; base-uri 'none'; form-action https://formspree.io https://allooloo.io; frame-ancestors 'none'; upgrade-insecure-requests";   // the redirect target of the form POST must be allowed too (browsers apply form-action to the 302)
export const BOTS = ['GPTBot', 'ClaudeBot', 'Claude-User', 'Claude-SearchBot', 'Google-Extended', 'PerplexityBot', 'Perplexity-User', 'OAI-SearchBot', 'ChatGPT-User', 'Bingbot', 'Applebot', 'Applebot-Extended', 'Amazonbot', 'CCBot', 'DuckAssistBot', 'meta-externalagent', 'Bytespider', 'cohere-ai', 'Diffbot', 'YouBot', 'MistralAI-User', 'xAI-Grok'];
export const ROBOTS = host => ['User-agent: *\nAllow: /\nContent-Signal: search=yes, ai-input=yes, ai-train=yes'].concat(BOTS.map(u => `User-agent: ${u}\nAllow: /`)).join('\n\n') + `\n\nSitemap: https://${host}/sitemap.xml\n`;
export const SECURITY = host => `Contact: ${CONTACT}\nContact: https://allooloo.io/security\nExpires: 2027-09-12T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: https://allooloo.io/security\n`;
export const ICONS = ['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-48.png', '/icon-96.png', '/icon-144.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest', '/mark.svg', '/allooloo-logo.svg', '/allooloo-logo-dark.svg', '/allooloo-logo-1200.png', '/estate.css'];
export const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
export const int = n => (typeof n === 'number' && isFinite(n)) ? String(Math.trunc(n)) : '';
export const today = () => new Date().toISOString().slice(0, 10);
export const dl = rows => `<dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`;
export const num = (n, items) => dl(items.map((v, i) => [`${n}.${i + 1}`, v]));
export const table = (cols, rows, cls) => `<table${cls ? ` class="${cls}"` : ''}><thead><tr>${cols.map(c => `<th scope="col">${c}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;

export function form(host) {
  // Contact Us — the one form on every surface (CEO, Sept 12 2026): endpoint of record https://formspree.io/f/moeqzgll, POST, hidden site = hostname; labels above, full column width; the honeypot stays.
  return `<form action="${FORM}" method="POST" accept-charset="UTF-8"><input type="hidden" name="site" value="${esc(host)}"><input type="hidden" name="_subject" value="${esc(host)} contact"><input type="hidden" name="_next" value="${CORPORATE}/"><input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<label for="f-email">email</label><input id="f-email" type="email" name="email" required autocomplete="email"><label for="f-message">message</label><textarea id="f-message" name="message" rows="5" required></textarea><button type="submit">send</button></form>
<p class="muted">The agents that built this read their own mail: ${CONTACT2}</p>`;
}
export const contactSection = host => `<h2>Contact Us</h2>${form(host)}`;
export function headers(meta, extra) {
  return { 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY', 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'X-CMR-Node': meta.node || 'estate', 'X-CMR-As-Of': meta.as_of || '', 'X-CMR-Version': String(meta.version || SURFACES_VERSION), 'X-CMR-Source': 'public-record', 'X-CMR-X402': 'ready', 'X-CMR-Operator': OPERATOR, 'X-CMR-Contact': 'CEO mk@allooloo.ai', 'X-Surface-Version': SURFACES_VERSION, ...(extra || {}) };
}
export const html = (body, meta, link) => new Response(body, { headers: headers(meta, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=60, must-revalidate', 'Vary': 'Accept', ...(link ? { 'Link': link } : {}) }) });
export const markdown = (body, meta, link) => new Response(body, { headers: headers(meta, { 'content-type': 'text/markdown; charset=utf-8', 'cache-control': 'public, max-age=60, must-revalidate', 'Vary': 'Accept', ...(link ? { 'Link': link } : {}) }) });
export const text = (body, meta, ct, cache) => new Response(body, { headers: headers(meta, { 'content-type': ct || 'text/plain; charset=utf-8', 'cache-control': cache || 'public, max-age=300' }) });
export const json = (obj, meta, cache, status, ct) => new Response(JSON.stringify(obj, null, 1), { status: status || 200, headers: headers(meta, { 'content-type': ct || 'application/json; charset=utf-8', 'cache-control': cache || 'public, max-age=300', 'access-control-allow-origin': '*' }) });
export const notFound = (paths, meta) => json({ error: 'not_found', status: 404, paths }, meta, 'no-store', 404);
export function sitemap(host, paths) { return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${paths.map(p => `<url><loc>https://${host}${p}</loc></url>`).join('')}</urlset>\n`; }
export const scale = items => `<div class="grid">${items.map(([v, k, s]) => `<div class="tile"><div class="v">${v}</div><div class="k">${k}</div>${s ? `<div class="s">${s}</div>` : ''}</div>`).join('')}</div>`;

// The page: title line (the <title>, first text on the page) → mark → nav → state pill line → H1 (mono) → body → footer (kicker line, then the full regions list, then the row with © last).
export function page({ host, title, desc, h1, body, asOf, version, state, jsonld, path }) {
  const ld = [{ '@context': 'https://schema.org', '@type': 'WebSite', name: 'Allooloo', url: `https://${host}/`, publisher: { '@type': 'Organization', name: OPERATOR, url: CORPORATE } }].concat(jsonld || []);
  const live = state === 'live'; const canonical = `https://${host}${path || '/'}`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="${canonical}">
<meta property="og:site_name" content="Allooloo"><meta property="og:type" content="website"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${canonical}"><meta property="og:image" content="https://${host}/icon-512.png">
<meta name="robots" content="index,follow"><meta name="theme-color" content="#14213D">
<link rel="stylesheet" href="/estate.css?v=${SURFACES_VERSION}">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="48x48" href="/icon-48.png"><link rel="icon" type="image/png" sizes="96x96" href="/icon-96.png"><link rel="icon" type="image/png" sizes="144x144" href="/icon-144.png"><link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png"><link rel="icon" type="image/png" sizes="512x512" href="/icon-512.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt"><link rel="alternate" type="application/json" href="/facts.json" title="facts.json">
<script type="application/ld+json">${JSON.stringify(ld)}</script></head><body${host === 'allooloo.io' ? ' class="site"' : ''}>
<header><a class="logo" href="${CORPORATE}/" aria-label="Allooloo"><img src="/allooloo-logo.svg" width="200" height="50" alt="Allooloo"></a>
<nav aria-label="Estate"><ul>${NAV.map(([t, u]) => `<li><a href="${u}"${u.startsWith(`https://${host}/`) ? ' aria-current="page"' : ''}>${t}</a></li>`).join('')}</ul></nav>
<p class="state"><span class="pill${live ? ' live' : ''}">${esc(state || 'record')}</span> as of ${esc(asOf || today())} · version ${esc(version || SURFACES_VERSION)} · ${esc(host)}</p></header>
<main><h1>${esc(h1)}</h1>${body}</main>
<footer><p>${host === 'allooloo.io' ? `The agents that built this read their own mail: ${CONTACT2} · ${OPERATOR} · Vancouver &amp; Toronto, Canada · <a href="https://kyp-model.ai/">CEO Letter</a> · <a href="https://agentic-x402.ai/">x402</a>` : `<a href="${CONTACT}">Support</a> · <a href="https://allooloo.io/status">Status</a> · <a href="https://allooloo.io/terms">Terms of Use</a> · <a href="https://allooloo.io/privacy">Privacy</a> · <a href="https://allooloo.io/security">Report a Security Issue</a> · <a href="https://allooloo.io/no-cookies">No cookies</a> · <a href="/llms.txt">llms.txt</a> · <a href="https://x.com/allooloo_io">X @allooloo_io</a> · <a href="https://kyp-model.ai/">CEO Letter</a> · <a href="https://agentic-x402.ai/">x402</a> · Microsoft AI Cloud Partner · © 2026 ${OPERATOR}`}</p></footer></body></html>`;
}
