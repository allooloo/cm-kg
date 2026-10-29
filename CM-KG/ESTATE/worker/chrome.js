// ORDER-020 §0–§3 + CEO corrections (Sept 12 2026) — the record-grade chrome: title line first, mark, nine-tab nav, state pill; one form; one footer.
// SURFACE REFURB (Site Book + Brand Book + Addendum A, CEO Sept 28 2026; staging only): sticky header (logo · four-item nav · tint button · "Gain the edge" pill), LIVE line of record, big sans H1,
// one inline icon sprite (eight icons of record + the header's sun/moon), brand band above the one-row footer. Legacy bodies are wrapped, never reworded.
// Regions are never abbreviated: REGION_FULL is the list of record and is written out wherever residency appears. The kicker is never the opening line.
export const OPERATOR = 'Allooloo Technologies Corp.';
export const CORPORATE = 'https://allooloo.io';
export const CONTACT = 'https://allooloo.io/#contact';   // the contact form is the only support door (CEO, Sept 12 2026)
export const CONTACT2 = 'allooloo@hey.com';
export const LEGAL = 'legal@allooloo.ai';
export const APEX = 'https://mcp.getissuer.ai';   // RADAR-02 (2026-10-23): the apex door prints as mcp.getissuer.ai (same Worker, same paths); the long hostname is printed nowhere; was https://mcp.capitalmarketsknowledgegraph.ai
export const APEX_AGENT = 'https://agent.getissuer.ai';   // RADAR-02: was https://agent.capitalmarketsknowledgegraph.ai
export const FORM = 'https://formspree.io/f/moeqzgll';
export const SURFACES_VERSION = '2026-10-28.4';   // SITE-02 (Site Build Plan v2.2, 2026-10-28): nav of record KYP · Issuerwire · Data Now · Data Vintage · RADAR; §3 corrections (signed, six tools, Hong Kong, OpsAgents, four lines); home re-cut; getissuer.ai as the KYP page; shelf pages; was 2026-10-28.1     // SITE-01 (Site Build Plan v2.2, 2026-10-28): /news 'As covered in' — 20 outlet links; was 2026-10-27.7     // RADAR-MAIL (2026-10-27): broadcast.mail off radar.json; was 2026-10-27.6     // NEWS-LINE (2026-10-27): the Oct 22 release line on /news reads the two-products line; was 2026-10-27.5     // HEY-CUT (2026-10-27): the 'agents read their own mail' line off the contact block, the allooloo.io footer line, /docs, the auth markdown and RADAR §12; was 2026-10-27.4     // LOCATION-ALIGN + NEWS-01 (2026-10-27): every company-location line reads Richmond, BC; allooloo.io/news; News on every footer row; was 2026-10-27.3     // LOCATION-CUT (2026-10-27): '· Vancouver & Toronto' off the allooloo.io footer line; was 2026-10-27.2     // CRUNCHBASE (2026-10-27): Crunchbase link on every footer row, after Microsoft AI Cloud Partner; was 2026-10-27.1     // FOOTER-ADDR (2026-10-27): allooloo.io footer line carries the Richmond, BC street address; was 2026-10-26.2     // ZONES-02 (2026-10-26): nine pages on the zones paid 2026-10-25 (zones02.js), eight forwards; was 2026-10-26.1     // RADAR-01 (2026-10-26): RADAR §12 Spend removed (page, radar.json, radar.csv), one paid-calls line kept; was 2026-10-25.1     // DAY ORDER 5 (2026-10-25): allooloo.io reads the roster (nodes.json via list_nodes) for counts, regions, duty and the jurisdiction paragraph; was 2026-10-23.2     // RADAR-02 (2026-10-23): RADAR sovereign zones + Issuerwire sections, registry/spend read, apex prints as mcp.getissuer.ai, logo on the ORDER-034 pages; was 2026-10-23.1   // HANDLE (2026-10-23): X @allooloo_ai on every footer row; was 2026-10-22.2   // ORDER-035 (2026-10-22): Hong Kong a full node, twelve markets; was 2026-10-22.1   // ORDER-034 (2026-10-22): sovereign node pages + two standards pages; was 2026-10-18.1   // ORDER-032 C.4 (2026-10-18): agent-swap.ai; was 2026-10-17.1   // ORDER-027 (2026-10-17): product doors; was 2026-09-28.1   // bumped on every estate deploy; prior renders go to the pond (snapshot_surfaces.py)
export const KICKER = 'allooloo.ai · Microsoft AI Cloud Partner · Microsoft Azure · in-country, region by region';   // ORDER-027 D4: the kicker prints allooloo.ai (printed name; allooloo.io stays the serving canonical)   // Proof section first line and footer line only
export const COMPANY_TITLE = 'AI agents for capital markets — Allooloo';   // HOME TITLE (CEO, 2026-10-28)
export const REGION_FULL = { ca: 'Canada Central (Toronto, Canada)', us: 'East US (Virginia, United States)', uk: 'UK South (London, United Kingdom)', fr: 'France Central (Paris, France)', nl: 'West Europe (Amsterdam, Netherlands)', ch: 'Switzerland North (Zurich, Switzerland)', de: 'Germany West Central (Frankfurt, Germany)', au: 'Australia East (Sydney, Australia)', sg: 'Southeast Asia (Singapore)', jp: 'Japan East (Tokyo, Japan)', kr: 'Korea Central (Seoul, South Korea)', hk: 'East Asia (Hong Kong)' }   // ORDER-035: a full node;
export const REGIONS_LIST = ['ca', 'us', 'uk', 'fr', 'nl', 'ch', 'de', 'au', 'sg', 'jp', 'kr', 'hk'].map(cc => REGION_FULL[cc]).join(' · ');
export const NAV = [['KYP', 'https://getissuer.ai/'], ['Issuerwire', 'https://issuerwire.ai/'], ['Data Now', 'https://data-now.ai/'], ['Data Vintage', 'https://data-vintage.ai/'], ['RADAR', 'https://agentic-radar.ai/']];   // SITE-02 (Site Build Plan v2.2 §2, 2026-10-28): the nav of record — five product names; Trades, ASK and Issuers leave the bar   // Brand Book ruling 4: the nine capitalised tabs are retired
export const CTA = ['Connect an agent', 'https://allooloo.io/connect'];   // SITE-02 §2: the pill
export const TAGLINE = 'Where agents read the market.';
export const BAND = 'Allooloo is the intelligence layer under the trade, not the trade. One sourced, read-dated record for every listed company in every market it serves, served in the issuer’s own jurisdiction, callable by any agent over MCP and A2A.';
// The eight icons of record (Addendum A §7), hand-drawn, 24-unit line icons in currentColor; sun and moon are the header tint button's own (Site Book, header).
const ICON_PATHS = {
  ring: '<circle cx="12" cy="12" r="8.5" stroke-dasharray="15 3.6"/><circle cx="12" cy="12" r="4.5" stroke-dasharray="8 2.8" stroke-dashoffset="4"/>',
  record: '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h5M10 16h5"/>',
  desk: '<path d="M4 5h16v11H10l-4 4v-4H4z"/><path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01"/>',
  issuer: '<path d="M4 20h16M6 20V9l6-4 6 4v11M10 20v-5h4v5"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="M11 12l8-8M16 7l3 3M14 9l2 2"/>',
  receipt: '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
  pulse: '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>'
};
export const SPRITE = `<svg class="sprite" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">${Object.entries(ICON_PATHS).map(([k, d]) => `<symbol id="i-${k}" viewBox="0 0 24 24">${d}</symbol>`).join('')}</svg>`;
export const icon = (name, cls) => `<svg class="ic${cls ? ' ' + cls : ''}" aria-hidden="true" focusable="false"><use href="#i-${name}"/></svg>`;
// A button of the new look: pill, arrow icon in place of the written "→" (Site Book: an icon on every button). kind: 'primary' (solid navy) | 'secondary' (navy outline).
export const btn = (label, href, kind) => `<a class="btn ${kind || 'secondary'}" href="${href}">${label}${icon('arrow')}</a>`;
// Market-tile region line (Addendum A §4): "<Region> Azure (<City>, <Country>)" in the new market tiles only; existing pages keep REGION_FULL as written.
export const regionAzure = cc => cc === 'hk' ? 'East Asia Azure (Hong Kong)' : REGION_FULL[cc].replace(' (', ' Azure (');
export const CSP = "default-src 'none'; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'none'; form-action https://formspree.io https://allooloo.io; frame-ancestors 'none'; upgrade-insecure-requests";   // the redirect target of the form POST must be allowed too (browsers apply form-action to the 302)
export const BOTS = ['GPTBot', 'ClaudeBot', 'Claude-User', 'Claude-SearchBot', 'Google-Extended', 'PerplexityBot', 'Perplexity-User', 'OAI-SearchBot', 'ChatGPT-User', 'Bingbot', 'Applebot', 'Applebot-Extended', 'Amazonbot', 'CCBot', 'DuckAssistBot', 'meta-externalagent', 'Bytespider', 'cohere-ai', 'Diffbot', 'YouBot', 'MistralAI-User', 'xAI-Grok'];
export const ROBOTS = host => ['User-agent: *\nAllow: /\nContent-Signal: search=yes, ai-input=yes, ai-train=yes'].concat(BOTS.map(u => `User-agent: ${u}\nAllow: /`)).join('\n\n') + `\n\nSitemap: https://${host}/sitemap.xml\nAgentmap: https://${host}/.well-known/ard.json\n# llms.txt: https://${host}/llms.txt\n`;   // Agentmap = ARD §6.1 discovery directive; the llms.txt pointer is a comment (no robots directive exists for it)
export const SECURITY = host => `Contact: ${CONTACT}\nContact: https://allooloo.io/security\nExpires: 2027-09-12T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: https://allooloo.io/security\n`;
export const ICONS = ['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-48.png', '/icon-96.png', '/icon-144.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest', '/mark.svg', '/allooloo-logo.svg', '/allooloo-logo-dark.svg', '/allooloo-logo-1200.png', '/estate.css', '/webmcp.js'];
export const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
export const int = n => (typeof n === 'number' && isFinite(n)) ? String(Math.trunc(n)) : '';
export const today = () => new Date().toISOString().slice(0, 10);
export const dl = rows => `<dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`;
export const num = (n, items) => dl(items.map((v, i) => [`${n}.${i + 1}`, v]));
export const table = (cols, rows, cls) => `<table${cls ? ` class="${cls}"` : ''}><thead><tr>${cols.map(c => `<th scope="col">${c}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;

export function form(host) {
  // Contact Us — the one form on every surface (CEO, Sept 12 2026): endpoint of record https://formspree.io/f/moeqzgll, POST, hidden site = hostname; labels above, full column width; the honeypot stays.
  return `<form id="contact" action="${FORM}" method="POST" accept-charset="UTF-8" toolname="contact_us" tooldescription="Send a message to Allooloo Technologies Corp. through the contact form of record on ${esc(host)}"><input type="hidden" name="site" value="${esc(host)}"><input type="hidden" name="_subject" value="${esc(host)} contact"><input type="hidden" name="_next" value="${CORPORATE}/"><input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<label for="f-email">email</label><input id="f-email" type="email" name="email" required autocomplete="email"><label for="f-message">message</label><textarea id="f-message" name="message" rows="5" required></textarea><button type="submit">send</button></form>`;
}
export const contactSection = host => `<h2>Contact Us</h2>${form(host)}`;
export function headers(meta, extra) {
  return { 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Content-Signal': 'search=yes, ai-input=yes, ai-train=yes', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY', 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'X-CMR-Node': meta.node || 'estate', 'X-CMR-As-Of': meta.as_of || '', 'X-CMR-Version': String(meta.version || SURFACES_VERSION), 'X-CMR-Source': 'public-record', 'X-CMR-X402': 'ready', 'X-CMR-Operator': OPERATOR, 'X-CMR-Contact': 'CEO mk@allooloo.ai', 'X-Surface-Version': SURFACES_VERSION, ...(extra || {}) };
}
export const html = (body, meta, link) => new Response(body, { headers: headers(meta, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=60, must-revalidate', 'Vary': 'Accept', ...(link ? { 'Link': link } : {}) }) });
export const markdown = (body, meta, link) => new Response(body, { headers: headers(meta, { 'content-type': 'text/markdown; charset=utf-8', 'cache-control': 'public, max-age=60, must-revalidate', 'Vary': 'Accept', ...(link ? { 'Link': link } : {}) }) });
export const text = (body, meta, ct, cache) => new Response(body, { headers: headers(meta, { 'content-type': ct || 'text/plain; charset=utf-8', 'cache-control': cache || 'public, max-age=300' }) });
export const json = (obj, meta, cache, status, ct) => new Response(JSON.stringify(obj, null, 1), { status: status || 200, headers: headers(meta, { 'content-type': ct || 'application/json; charset=utf-8', 'cache-control': cache || 'public, max-age=300', 'access-control-allow-origin': '*' }) });
export const notFound = (paths, meta) => json({ error: 'not_found', status: 404, paths }, meta, 'no-store', 404);
export function sitemap(host, paths) { return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${paths.map(p => `<url><loc>https://${host}${p}</loc></url>`).join('')}</urlset>\n`; }
// Tiles (Site Book "Tiles"): navy line icon, big figure, label, one line under it, optional "View →". A tile shows only when its figure answers; a missing tile closes the row up; no live tile, no row.
export const scale = items => { const live = items.filter(([v]) => v !== '' && v != null && v !== '0'); return live.length ? `<div class="grid${live.length === 4 ? ' four' : ''}">${live.map(([v, k, s, ic, href]) => `<div class="tile"><div class="v">${ic ? icon(ic) : ''}${v}</div><div class="k">${k}</div>${s ? `<div class="s">${s}</div>` : ''}${href ? `<a class="view" href="${href}">View${icon('arrow')}</a>` : ''}</div>`).join('')}</div>` : ''; };

// The page (refurb): sticky bar (logo · nav · tint · pill) → LIVE line of record → big sans H1 (+ sub-line and buttons on a hero) → body → brand band → footer line (allooloo.io only) → one-row footer.
// The LIVE line keeps each page's state word (Addendum A §5); the green dot shows only where that word is "live". It sits in <header> so the markdown twin (aeo.js toMarkdown) is unchanged;
// on a hero page (sub given) it moves under the sub-line, as the home spec orders it. The brand band sits inside <footer> for the same reason.
const FOOTER_ROW = `<a href="${CONTACT}">Support</a> · <a href="https://allooloo.io/status">Status</a> · <a href="https://allooloo.io/news">News</a> · <a href="https://allooloo.io/terms">Terms of Use</a> · <a href="https://allooloo.io/privacy">Privacy</a> · <a href="https://allooloo.io/security">Report a Security Issue</a> · <a href="https://allooloo.io/no-cookies">No cookies</a> · <a href="/llms.txt">llms.txt</a> · <a href="https://x.com/allooloo_ai">X @allooloo_ai</a> · <a href="https://kyp-model.ai/">CEO Letter</a> · <a href="https://agentic-x402.ai/">x402</a> · Microsoft AI Cloud Partner · <a href="https://www.crunchbase.com/organization/allooloo">Crunchbase</a> · © 2026 ${OPERATOR}`;
const liveLine = (state, asOf, version, host) => `<p class="state">${state === 'live' ? '<span class="dot" aria-hidden="true"></span>' : ''}${esc(state || 'record')} · as of ${esc(asOf || today())} · version ${esc(version || SURFACES_VERSION)} · ${esc(host)}</p>`;
// SITE-04A (2026-10-28): the nav of record and the estate footer as one kit, so the own-shell hosts (ORDER-034, DAY ORDER 5) render them byte-for-byte as the shared template does.
// navHeader opens <header> and closes the .bar; the caller closes </header>. kyp: the KYP link's href on a country issuer page (getissuer.ai/#issuers by the order).
export function navHeader(host, { nocurrent, kyp } = {}) {
  return `<header><div class="bar"><div class="in"><a class="logo" href="${CORPORATE}/" aria-label="Allooloo"><img src="/allooloo-logo.svg" width="160" height="40" alt="Allooloo"></a>
<nav aria-label="Estate"><ul>${NAV.map(([t, u]) => `<li><a href="${t === 'KYP' && kyp ? kyp : u}"${!nocurrent && u.startsWith(`https://${host}/`) ? ' aria-current="page"' : ''}>${t}</a></li>`).join('')}</ul></nav>
<button class="tint" type="button" data-tint aria-label="Light or dark">${icon('moon', 'moon')}${icon('sun', 'sun')}</button><a class="btn primary cta" href="${CTA[1]}">${CTA[0]}${icon('arrow')}</a></div></div>
`;
}
export function estateFooter(host) {
  return `<footer><section class="band" aria-label="Allooloo"><p class="tag">${esc(TAGLINE)}</p><p>${esc(BAND)}</p></section>${host === 'allooloo.io' ? `<p class="line">${OPERATOR} · 260-4611 Viking Way, Richmond, BC V6V 2K9, Canada</p>` : ''}<p class="row">${FOOTER_ROW}</p></footer>`;
}
export function page({ host, title, desc, h1, body, asOf, version, state, jsonld, path, head, nocurrent, sub, actions }) {
  const ld = [{ '@context': 'https://schema.org', '@type': 'WebSite', name: 'Allooloo', url: `https://${host}/`, publisher: { '@type': 'Organization', name: OPERATOR, url: CORPORATE } }].concat(jsonld || []);
  const canonical = `https://${host}${path || '/'}`; const ll = liveLine(state, asOf, version, host); const hero = !!sub;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="${canonical}">
<meta property="og:site_name" content="Allooloo"><meta property="og:type" content="website"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${canonical}"><meta property="og:image" content="https://${host}/icon-512.png">
<meta name="robots" content="index,follow"><meta name="theme-color" content="#14213D"><meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="/estate.css?v=${SURFACES_VERSION}">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="48x48" href="/icon-48.png"><link rel="icon" type="image/png" sizes="96x96" href="/icon-96.png"><link rel="icon" type="image/png" sizes="144x144" href="/icon-144.png"><link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png"><link rel="icon" type="image/png" sizes="512x512" href="/icon-512.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt"><link rel="alternate" type="application/json" href="/facts.json" title="facts.json"><link rel="ai-catalog" href="/.well-known/ai-catalog.json"><link rel="ard" href="/.well-known/ard.json">
${head || ''}<script type="application/ld+json">${JSON.stringify(ld)}</script></head><body${host === 'allooloo.io' ? ' class="site"' : ''}>${SPRITE}
${navHeader(host, { nocurrent })}${hero ? '' : `<div class="in">${ll}</div>`}</header>
<main><div class="hero"><h1>${esc(h1)}</h1>${hero ? `<p class="sub">${esc(sub)}</p>${ll}${actions ? `<p class="actions">${actions}</p>` : ''}` : ''}</div>${body}</main>
${estateFooter(host)}<script src="/webmcp.js"></script></body></html>`;
}
