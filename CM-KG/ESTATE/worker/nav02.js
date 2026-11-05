// nav02.js — NAV-02 (CEO, 2026-11-01): the footer of record's live parts, the machine files every surface carries, the Organization schema, and the
// About/Investor page. Wired in protocols.js (the entry of estate-pages), so every host the estate serves has them, whatever module renders its page.
//   doorCheck   the door check the digest uses (job_digest.py, DIGEST-CAP-01): list_nodes on the resolver, then each live node's public door /mcp.json → 200;
//               cached five minutes in the isolate (refreshed in the background once stale); the footer's "All doors answering" readout (chrome.js setDoors)
//   jwks        /.well-known/jwks.json on every surface: the Allooloo keyring of record (https://allooloo.ai/.well-known/jwks.json), served as the surface's own file
//   llmsFull    /llms-full.txt on every surface: the page's full text (the page itself, as markdown, by the same converter the Accept: text/markdown answer
//               uses) plus the door's tool list (the surface's own descriptor; else the door it names, tools/list) — generated from the page's source, never typed
//   withOrg     the Organization schema on every HTML page: sameAs LinkedIn, X, Crunchbase; the Richmond address
//   about       about.allooloo.ai and investor.allooloo.ai: one page, the same body on both hosts (served as about.allooloo.ai); investor lands at Investor
//               Relations (/about.js scrolls there on that host); the eight live tiles read from the record at render; no form (the CEO footer line is the contact)
import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ICONS, ROBOTS, SECURITY, esc, int, today, page, scale, text, json, headers, sitemap, setDoors } from './chrome.js';
import * as AEO from './aeo.js';
import { NEWS } from './docs.js';
import COPY from './about-copy.js';
import { DESKS } from './desks.js';   // DOORS-01
const UA = { 'user-agent': 'Allooloo estate (NAV-02)' };
const APEX = 'https://mcp.getissuer.ai/mcp';
export const SAME_AS = ['https://www.linkedin.com/company/allooloo-technologies-corp/', 'https://x.com/allooloo_ai', 'https://www.crunchbase.com/organization/allooloo'];
export const ADDRESS = { '@type': 'PostalAddress', streetAddress: '260-4611 Viking Way', addressLocality: 'Richmond', addressRegion: 'BC', postalCode: 'V6V 2K9', addressCountry: 'CA' };
export const ORG = { '@context': 'https://schema.org', '@type': 'Organization', name: OPERATOR, url: CORPORATE, logo: `${CORPORATE}/icon-512.png`, address: ADDRESS, sameAs: SAME_AS };
const rpc = (url, method, params) => fetch(url, { method: 'POST', headers: { ...UA, 'content-type': 'application/json', accept: 'application/json, text/event-stream' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params: params || {} }), signal: AbortSignal.timeout(9000) })
  .then(async r => { const t = await r.text(); return JSON.parse(t.slice(t.indexOf('{'))); });
// ---------- the door check (the digest's own method, read at render)
let NODES = null, NODES_AT = 0;
async function nodes() {
  if (NODES && Date.now() - NODES_AT < 300000) return NODES;
  try { const j = await rpc(APEX, 'tools/call', { name: 'list_nodes', arguments: {} }); NODES = j.result.structuredContent.nodes; NODES_AT = Date.now(); } catch (e) { NODES = NODES || []; }
  return NODES;
}
let DOORS = null, DOORS_AT = 0, DOORS_RUN = null;
async function runCheck() {
  const nl = (await nodes()).filter(n => n.live); if (!nl.length) return DOORS;
  const up = await Promise.all(nl.map(async n => {
    let d = String(n.regional_door || n.door || '').replace(/\/+$/, ''); if (d.endsWith('/mcp')) d = d.slice(0, -4);
    try {   // the digest follows a redirect from outside; a <cc>.eu-cm-kg.ai /mcp.json is the zone's 301 to eu-issuer.ai (this Worker), which a subrequest cannot follow
      const r = await fetch(d + '/mcp.json', { headers: UA, redirect: 'manual', cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(8000) }); if (r.status === 200) return true;
      if (r.status >= 300 && r.status < 400) { const w = await fetch(d + '/mcp', { method: 'POST', headers: { ...UA, 'content-type': 'application/json', accept: 'application/json, text/event-stream' }, body: '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}', redirect: 'manual', signal: AbortSignal.timeout(8000) }); return w.status === 200; }   // the door itself at its gate (tools/list), never a path this Worker serves (.11 read /.well-known/mcp.json, which the estate serves: a loop)
      return false; } catch (e) { return false; }
  }));
  const desks = (await Promise.all(DESKS.map(async ([t, u, mj]) => { try { const r = await fetch(mj, { headers: UA, redirect: 'manual', cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(8000) }); return r.status === 200 ? [t, u] : null; } catch (e) { return null; } }))).filter(Boolean);   // DOORS-01: the get_ doors that answer
  DOORS = { live: nl.length, answering: up.filter(Boolean).length, desks, read_at: new Date().toISOString(), method: 'list_nodes, then each live door /mcp.json (the digest\'s door check); each get_ door /mcp.json for FOR DESKS' }; DOORS_AT = Date.now(); setDoors(DOORS);
  return DOORS;
}
export async function doorCheck(ctx) {
  if (DOORS && Date.now() - DOORS_AT < 300000) return DOORS;
  if (DOORS && ctx && ctx.waitUntil) { if (!DOORS_RUN) { DOORS_RUN = runCheck().finally(() => { DOORS_RUN = null; }); ctx.waitUntil(DOORS_RUN); } return DOORS; }   // stale: answer with the last check, refresh behind
  if (!DOORS_RUN) { DOORS_RUN = runCheck().finally(() => { DOORS_RUN = null; }); if (ctx && ctx.waitUntil) ctx.waitUntil(DOORS_RUN.catch(() => null)); }
  try { return await Promise.race([DOORS_RUN, new Promise(r => setTimeout(() => r(DOORS), 5000))]); } catch (e) { return DOORS; }   // a first check waits five seconds at most, then finishes behind
}
// ---------- the keyring
let KEYS = null, KEYS_AT = 0;
export async function jwks() {
  if (!KEYS || Date.now() - KEYS_AT > 300000) { try { const r = await fetch('https://allooloo.ai/.well-known/jwks.json', { headers: UA, cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(8000) }); if (r.ok) { KEYS = await r.json(); KEYS_AT = Date.now(); } } catch (e) { /* the last one read */ } }
  return KEYS;
}
// ---------- llms-full.txt
const TOOLS = new Map();
async function doorTools(url) {
  const c = TOOLS.get(url); if (c && Date.now() - c.at < 300000) return c.tools;
  try { const j = await rpc(url, 'tools/list'); const t = ((j.result || {}).tools || []).map(x => ({ name: x.name, title: x.title, description: x.description })); TOOLS.set(url, { at: Date.now(), tools: t }); return t; } catch (e) { return c ? c.tools : null; }
}
export async function llmsFull(request, env, ctx, handler, host) {
  const base = new URL(request.url); const sub = p => handler(new Request(new URL(p, base), { headers: { accept: p === '/' ? 'text/html' : 'application/json', 'user-agent': 'Allooloo llms-full (NAV-02)' } }), env, ctx);
  const pr = await sub('/'); const html = pr.status === 200 ? await pr.text() : '';
  const md = html ? AEO.toMarkdown(html, host).trim() : '(this host serves no page of its own)';
  let d = null; try { const r = await sub('/.well-known/mcp.json'); if (r.status === 200) d = await r.json(); } catch (e) { d = null; }
  let tools = d && Array.isArray(d.tools) ? d.tools.filter(t => t && t.name) : null; const door = d && (d.url || (d.endpoints && d.endpoints[0] && d.endpoints[0].url)) || null;
  if ((!tools || !tools.length) && door) tools = await doorTools(door);
  const L = [`# ${host} — llms-full.txt`, '', `The page's full text and the door's tool list, generated from the page's own source at ${new Date().toISOString().slice(0, 16)}Z (surface ${SURFACES_VERSION}). The short index is /llms.txt.`, '', '## The page', '', md, '', '## The door'];
  if (door) L.push('', `Door (Streamable HTTP MCP): ${door}`);
  if (tools && tools.length) { L.push('', 'Tools:'); for (const t of tools) L.push(`- ${t.name}${t.title ? ' — ' + t.title : ''}${t.description ? ': ' + t.description : ''}${t.note ? ' (' + t.note + ')' : ''}`); }
  else if (d && Array.isArray(d.doors)) L.push('', 'No MCP door on this host. The doors it names:', ...d.doors.map(x => `- ${x}`));
  else if (!door) L.push('', 'No MCP door on this host; the resolver for every listed issuer is ' + APEX + '.');
  L.push('', `Operator: ${OPERATOR}. Corporate: ${CORPORATE}.`);
  return text(L.join('\n') + '\n', { node: 'estate', as_of: today() }, 'text/plain; charset=utf-8', 'public, max-age=300');
}
// ---------- the Organization schema on every HTML page
export async function withOrg(r) {
  const ct = r.headers.get('content-type') || ''; if (r.status !== 200 || !ct.includes('text/html')) return r;
  let b = await r.text(); const h = new Headers(r.headers); h.delete('content-length');
  if (!b.includes('"sameAs"') && b.includes('</head>')) b = b.replace('</head>', `<script type="application/ld+json">${JSON.stringify(ORG)}</script></head>`);
  return new Response(b, { status: r.status, headers: h });
}
// ---------- the About/Investor page
export const ABOUT_HOSTS = ['about.allooloo.ai', 'investor.allooloo.ai'];
export const isAbout = h => ABOUT_HOSTS.includes(String(h || '').replace(/^www\./, ''));
const ABOUT = 'about.allooloo.ai';
async function getJson(u) { try { const r = await fetch(u, { headers: { ...UA, accept: 'application/json' }, cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(9000) }); return r.ok ? await r.json() : null; } catch (e) { return null; } }
const LAST = {}; let LAST_AT = 0;
const keep = v => { const now = Date.now(); for (const k of Object.keys(v)) { if (k === 'sources') continue; if (v[k] != null) LAST[k] = v[k]; else if (now - LAST_AT < 300000 && LAST[k] != null) v[k] = LAST[k]; } if (Object.entries(v).every(([k, x]) => k === 'sources' || x != null)) LAST_AT = now; return v; };
async function tileData(env, url) { return keep(await tileRead(env, url)); }
async function tileRead(env, url) {
  const [nl, radar, iw, ark, ops] = await Promise.all([nodes(), env.ASSETS.fetch(new Request(new URL('/estate-traffic.json', url))).then(r => r.ok ? r.json().then(et => ({ estate_traffic: et })) : null).catch(() => null), getJson('https://issuerwire.ai/facts.json'),   // radar's own source for the calls (agentic-radar.ai is this Worker: a subrequest cannot reach it)
    env.ASSETS.fetch(new Request(new URL('/swap/ark.json', url))).then(r => r.ok ? r.json() : null).catch(() => null),
    env.ASSETS.fetch(new Request(new URL('/ops/agents.json', url))).then(r => r.ok ? r.json() : null).catch(() => null)]);
  const live = nl.filter(n => n.live); const sum = k => live.reduce((a, n) => a + (Number(n[k]) || 0), 0);   // HOME-02: each tile keeps its last good reading (LAST), five minutes
  const regions = new Set(live.map(n => n.region && n.region.azure).filter(Boolean));
  return {
    countries: live.length ? new Set(live.map(n => n.country)).size : null, issuers: live.length ? sum('records') : null, events: live.length ? sum('events') : null,
    iw_rows: iw && iw.signed_rows != null ? iw.signed_rows : (radar && radar.issuerwire && radar.issuerwire.signed_rows), calls30: radar && radar.estate_traffic ? radar.estate_traffic.estate_requests_30d : null,
    opsagents: ops && ops.scheduled_jobs != null ? ops.scheduled_jobs : null, regions: regions.size || null, arks: ark && ark.nodes ? Object.keys(ark.nodes).length : null,
    sources: { countries: 'list_nodes (live nodes, by country)', issuers: 'list_nodes', events: 'list_nodes', iw_rows: 'issuerwire.ai/facts.json', calls30: 'estate-traffic.json (the source agentic-radar.ai/radar.json reads)', opsagents: 'ops/agents.json (the scheduled jobs of the fleet, from the capacity snapshot of the job definitions)', regions: 'list_nodes (region.azure of the live nodes)', arks: 'swap/ark.json (the ark bucket per node)' } };
}
const n = v => v == null ? '' : int(Number(v));
function tiles(v) {
  return scale([[n(v.countries), 'Countries live', '', 'ring'], [n(v.issuers), 'Issuers on the record', '', 'issuer'], [n(v.events), 'Dated disclosures', '', 'record'], [n(v.iw_rows), 'Issuerwire signed rows', '', 'pulse']])
    + scale([[n(v.calls30), 'AI-agent calls, 30 days', '', 'desk'], [n(v.opsagents), 'OpsAgents on the fleet, nightly', '', 'key'], [n(v.regions), 'Azure regions, in-country', '', 'ring'], [n(v.arks), 'AWS arks, 60-minute standby', '', 'receipt']]);
}
function blocks(list, v) {
  return list.map(b => b[0] === 'tiles' ? tiles(v) : b[0] === 'lead' ? `<p><strong>${esc(b[1])}</strong> ${esc(b[2])}</p>` : b[0] === 'news' ? `<p><strong>${esc(b[1])}</strong> ${NEWS[0] ? `<a href="${esc(NEWS[0].url)}">${esc(NEWS[0].title)}</a> · ${esc(NEWS[0].date)}` : ''}</p>` : `<p>${esc(b[1])}</p>`).join('\n');
}
export const aboutBody = v => `${blocks(COPY.about.blocks, v)}
<p class="kicker" id="investor-relations">${esc(COPY.investor.label)}</p><h2>${esc(COPY.investor.head)}</h2>
${blocks(COPY.investor.blocks, v)}`;
const ABOUT_JS = "(function(){if(/^investor\\./.test(location.hostname)&&!location.hash){var e=document.getElementById('investor-relations');if(e)e.scrollIntoView();}})();\n";
const TITLE = 'About Us · Investor Relations — Allooloo Technologies Corp.';
export async function about(request, env, ctx, inner) {
  const url = new URL(request.url); const p = url.pathname.replace(/\/+$/, '') || '/'; const host = ABOUT; const meta = { node: 'allooloo', as_of: today() };
  if (ICONS.includes(p) || p === '/estate.css' || p === '/webmcp.js' || p.startsWith('/swap/') || p.startsWith('/ops/')) return inner.fetch(new Request(`https://allooloo.io${p}${url.search}`, request), env, ctx);
  if (p === '/about.js') return text(ABOUT_JS, meta, 'text/javascript; charset=utf-8', 'public, max-age=300');
  if (p === '/robots.txt') return text(ROBOTS(host), meta, 'text/plain; charset=utf-8', 'public, max-age=86400');
  if (p === '/.well-known/security.txt') return text(SECURITY(host), meta, 'text/plain; charset=utf-8', 'public, max-age=86400');
  const desc = COPY.about.head + ' ' + COPY.investor.head;
  if (p === '/') { const v = await tileData(env, url); return new Response(page({ host, title: TITLE, desc, h1: COPY.about.head, state: 'record', eyebrow: COPY.about.label, asOf: today(), body: aboutBody(v), head: '<script src="/about.js" defer></script>', nocurrent: true }), { headers: headers(meta, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=60, must-revalidate', 'Vary': 'Accept' }) }); }
  if (p === '/llms.txt') return text([`# ${host} — About Us · Investor Relations`, `1. ${COPY.about.head}`, `2. ${COPY.investor.head}`, `3. One page on two hosts: https://about.allooloo.ai (About Us) and https://investor.allooloo.ai (Investor Relations), the same body. Contact: the CEO footer line. Copy of record v${COPY.version}.`, `4. Operator: ${OPERATOR}. Surface version: ${SURFACES_VERSION}. Full text: /llms-full.txt.`].join('\n') + '\n', meta);
  if (p === '/facts.json') { const v = await tileData(env, url); return json({ domain: host, hosts: ABOUT_HOSTS, kind: 'the About/Investor page', operator: OPERATOR, corporate: CORPORATE, copy_of_record: 'v' + COPY.version, tiles: v, surface_version: SURFACES_VERSION, as_of: today() }, meta); }
  if (p === '/.well-known/mcp.json' || p === '/mcp.json' || p === '/.well-known/mcp/server-card.json') return json({ name: 'about-allooloo', kind: 'page (no MCP door on this host)', page: 'https://about.allooloo.ai/', doors: ['https://mcp.getissuer.ai/mcp', 'https://mcp.getorderability.ai/mcp', 'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.getfilings.ai/mcp', 'https://mcp.getticker.ai/mcp', 'https://mcp.getauditor.ai/mcp', 'https://mcp.issuerwire.ai/mcp'], operator: OPERATOR }, meta);   // DOORS-01: the doors order
  if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json({ name: 'Allooloo — About Us · Investor Relations', description: desc, url: 'https://about.allooloo.ai/', provider: { organization: OPERATOR, url: CORPORATE }, version: SURFACES_VERSION, capabilities: {}, skills: [], defaultInputModes: ['text/plain'], defaultOutputModes: ['text/html'], supportedInterfaces: [] }, meta);
  if (p === '/sitemap.xml') return text(sitemap(host, ['/', '/llms.txt', '/llms-full.txt']), meta, 'application/xml; charset=utf-8', 'public, max-age=3600');
  return json({ error: 'not_found', status: 404, paths: ['/', '/llms.txt', '/llms-full.txt', '/facts.json', '/.well-known/mcp.json', '/.well-known/agent-card.json', '/.well-known/jwks.json', '/.well-known/security.txt'] }, meta, 'no-store', 404);
}
