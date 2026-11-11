// foragents.js — R-043 (CEO 2026-11-01; queued into TMKT-04, 2026-11-02): every Allooloo surface carries the FOR AGENTS row — llms.txt · llms-full.txt ·
// MCP server card · Agent card · Keys · security.txt — each the surface's own file. One module, copied into each Worker that serves a surface outside the
// estate (rco-door, eco-pages, stack-pages, book-pages), wrapping that Worker's own fetch:
//   · an HTML page (200) gains the row inside its footer (before </footer>; a page without a footer gets one footer holding only the row)
//   · a file of the six the Worker does not serve for a host (its own answer 404) is served here, generated from the host's own surfaces — never typed:
//       /llms-full.txt                the host's own page as text, plus the door's tool list where the host's descriptor names a door
//       /llms.txt                     the page's title, its first paragraph and the six paths
//       /.well-known/mcp.json         the host's descriptor of record where it has one at another path (a standard's own descriptor), else a page descriptor
//       /.well-known/agent-card.json  a card naming the page, its descriptor and its operator
//       /.well-known/jwks.json        the Allooloo keyring of record (https://allooloo.ai/.well-known/jwks.json, read and cached five minutes)
//       /.well-known/security.txt     the house security.txt for the host
//   · AUDIT-01 F5 (2026-11-11): /robots.txt and /sitemap.xml, when the Worker answers 404 for them (User-agent: *, Allow: /, Sitemap; the sitemap lists the
//     host's page) — no Content-Signal line here (that is a policy statement; only hosts that already state it in the header carry it)
//   · a file the Worker already serves is never replaced; nothing else is touched.
const ROW = '<p class="row foragents"><span class="kicker">FOR AGENTS</span> <a href="/llms.txt">llms.txt</a> · <a href="/llms-full.txt">llms-full.txt</a> · <a href="/.well-known/mcp.json">MCP server card</a> · <a href="/.well-known/agent-card.json">Agent card</a> · <a href="/.well-known/jwks.json">Keys</a> · <a href="/.well-known/security.txt">security.txt</a></p>';
const SIX = ['/llms.txt', '/llms-full.txt', '/.well-known/mcp.json', '/.well-known/agent-card.json', '/.well-known/jwks.json', '/.well-known/security.txt'];
const OPERATOR = 'Allooloo Technologies Corp.', CORPORATE = 'https://allooloo.io';
const H = (ct, extra) => ({ 'content-type': ct, 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', 'X-For-Agents': 'R-043', ...(extra || {}) });
const text = html => String(html || '').replace(/<(script|style|noscript|svg|template)\b[\s\S]*?<\/\1>/gi, ' ').replace(/<br\s*\/?>/gi, '\n').replace(/<\/(p|h\d|li|dt|dd|tr|div|section|table|header|footer)>/gi, '\n').replace(/<[^>]+>/g, ' ')
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;|&#x27;/g, "'").replace(/&middot;/g, '·').replace(/&rarr;/g, '→').replace(/&mdash;/g, '—')
  .split('\n').map(l => l.replace(/[ \t]+/g, ' ').trim()).filter(Boolean).join('\n');
let KEYS = null, KEYS_AT = 0;
async function keyring() {
  if (!KEYS || Date.now() - KEYS_AT > 300000) { try { const r = await fetch('https://allooloo.ai/.well-known/jwks.json', { headers: { 'user-agent': 'Allooloo for-agents (R-043)' }, cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(8000) }); if (r.ok) { KEYS = await r.text(); KEYS_AT = Date.now(); } } catch (e) { /* the last read */ } }
  return KEYS;
}
async function own(inner, request, env, ctx, path, accept) {
  const u = new URL(request.url); u.pathname = path; u.search = '';
  try { const r = await inner.fetch(new Request(u.toString(), { headers: { accept: accept || 'text/html', 'user-agent': 'Allooloo for-agents (R-043)' } }), env, ctx); return r.status === 200 ? r : null; } catch (e) { return null; }
}
async function descriptorOf(inner, request, env, ctx, host) {   // the host's descriptor of record: /.well-known/mcp.json, /mcp.json, or a standard's own (<std>.json)
  const std = (/^([a-z]+(?:-[a-z]+)?-\d{5})\.(org|ai|com|io)$/.exec(host) || [])[1];
  for (const p of ['/mcp.json', '/protocol.json', ...(std ? [`/${std}.json`, `/.well-known/${std}.json`] : [])]) { const r = await own(inner, request, env, ctx, p, 'application/json'); if (r) { try { return { path: p, json: await r.json() }; } catch (e) { /* next */ } } }
  return null;
}
async function gen(inner, request, env, ctx, host, p) {
  const page = await own(inner, request, env, ctx, '/'); const html = page ? await page.text() : ''; const t = text((/<main\b[\s\S]*?<\/main>/i.exec(html) || [html])[0]);
  const title = text((/<title>([\s\S]*?)<\/title>/i.exec(html) || [])[1] || host); const first = t.split('\n').find(l => l.length > 60) || t.split('\n')[0] || '';
  if (p === '/.well-known/jwks.json') { const k = await keyring(); return k ? new Response(k, { headers: H('application/jwk-set+json; charset=utf-8', { 'X-Keyring-Of-Record': 'https://allooloo.ai/.well-known/jwks.json' }) }) : null; }
  if (p === '/.well-known/security.txt') return new Response(`Contact: ${CORPORATE}/#contact\nContact: ${CORPORATE}/security\nExpires: 2027-09-12T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: ${CORPORATE}/security\n`, { headers: H('text/plain; charset=utf-8') });
  const d = await descriptorOf(inner, request, env, ctx, host);
  if (p === '/.well-known/mcp.json') {
    if (d) return new Response(JSON.stringify({ ...d.json, descriptor_of_record: `https://${host}${d.path}` }, null, 1), { headers: H('application/json; charset=utf-8') });
    return new Response(JSON.stringify({ name: host, kind: 'page (no MCP door on this host)', page: `https://${host}/`, title, operator: OPERATOR, corporate: CORPORATE, resolver: 'https://mcp.getissuer.ai/mcp', note: 'a page of the Allooloo estate; the doors are named on https://data-paygo.ai/' }, null, 1), { headers: H('application/json; charset=utf-8') });
  }
  if (p === '/.well-known/agent-card.json') {   // AUDIT-01 F1: supportedInterfaces (the page; the MCP door its descriptor names, if any) and one skill (read the page)
    const dj = d && d.json; const dr = dj && [dj.door, dj.url, dj.endpoints && dj.endpoints[0] && dj.endpoints[0].url].find(x => typeof x === 'string' && /\/mcp\b/.test(x));
    const si = [{ url: `https://${host}/`, protocolBinding: 'HTTP+JSON', protocolVersion: '1.0' }, ...(dr ? [{ url: dr, protocolBinding: 'HTTP+JSON', transport: 'streamable-http', description: 'the MCP door this host\'s descriptor names' }] : [])];
    const sk = [{ id: 'read', name: `Read ${title}`, description: `${first.slice(0, 300)}${first ? ' ' : ''}The page is https://${host}/; its text for agents is https://${host}/llms.txt${dr ? `; the door its descriptor names: ${dr}` : ''}.`, tags: ['reference', 'read'], examples: [`https://${host}/llms.txt`] }];
    return new Response(JSON.stringify({ name: title, description: first.slice(0, 500), url: `https://${host}/`, provider: { organization: OPERATOR, url: CORPORATE }, version: new Date().toISOString().slice(0, 10), capabilities: {}, skills: sk, supportedInterfaces: si, defaultInputModes: ['text/plain'], defaultOutputModes: ['text/html'], descriptor: `https://${host}/.well-known/mcp.json` }, null, 1), { headers: H('application/json; charset=utf-8') });
  }
  if (p === '/llms.txt') return new Response(`# ${host} — ${title}\n\n${first}\n\nFor agents: ${SIX.map(x => `https://${host}${x}`).join(' · ')}\nOperator: ${OPERATOR}. Corporate: ${CORPORATE}.\n`, { headers: H('text/plain; charset=utf-8') });
  if (p === '/llms-full.txt') {
    const L = [`# ${host} — llms-full.txt`, '', `The page's full text and the door's tool list, generated from the page's own source at ${new Date().toISOString().slice(0, 16)}Z. The short index is /llms.txt.`, '', '## The page', '', t || '(this host serves no page of its own)', '', '## The door'];
    const dj = d && d.json; const door = dj && (dj.url || dj.door || (dj.endpoints && dj.endpoints[0] && dj.endpoints[0].url)); const tools = dj && Array.isArray(dj.tools) ? dj.tools : null;
    if (door && typeof door === 'string') L.push('', `Door: ${door}`);
    if (tools && tools.length) { L.push('', 'Tools:'); for (const x of tools) L.push(`- ${typeof x === 'string' ? x : `${x.name}${x.title ? ' — ' + x.title : ''}${x.description ? ': ' + x.description : ''}`}`); }
    else if (!door) L.push('', 'No MCP door on this host; the resolver for every listed issuer is https://mcp.getissuer.ai/mcp.');
    L.push('', `Operator: ${OPERATOR}. Corporate: ${CORPORATE}.`);
    return new Response(L.join('\n') + '\n', { headers: H('text/plain; charset=utf-8') });
  }
  return null;
}
// CLEAN-01 item 5 (2026-11-11): Markdown for Agents in code (the zone setting is not editable on Free) — estate-pages' own converter (ESTATE\worker\aeo.js
// toMarkdown + wantsMarkdown, copied); only a request whose Accept prefers text/markdown gets it, a browser's HTML is unchanged
function toMarkdown(html, host) {
  let s = html.replace(/<head>[\s\S]*?<\/head>/, '').replace(/<header>[\s\S]*?<\/header>/, '').replace(/<footer>[\s\S]*?<\/footer>/, '').replace(/<form[\s\S]*?<\/form>/g, '(contact form: https://allooloo.io/#contact)');
  s = s.replace(/<div class="tile"><div class="v">([\s\S]*?)<\/div><div class="k">([\s\S]*?)<\/div>(?:<div class="s">([\s\S]*?)<\/div>)?<\/div>/g, (m, v, k, src) => `\n- ${v.replace(/<[^>]+>/g, '')} ${k.replace(/<[^>]+>/g, '')}${src ? ' (' + src.replace(/<[^>]+>/g, '') + ')' : ''}`).replace(/<\/div>/g, '\n');
  s = s.replace(/<pre>([\s\S]*?)<\/pre>/g, (m, a) => '\n```\n' + a + '\n```\n');
  s = s.replace(/<table[^>]*>([\s\S]*?)<\/table>/g, (m, a) => { const rows = [...a.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(r => [...r[1].matchAll(/<t[hd][^>]*>([\s\S]*?)<\/t[hd]>/g)].map(c => c[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim())); if (!rows.length) return ''; return '\n| ' + rows[0].join(' | ') + ' |\n|' + rows[0].map(() => ' --- ').join('|') + '|\n' + rows.slice(1).map(r => '| ' + r.join(' | ') + ' |').join('\n') + '\n'; });
  s = s.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/g, '\n# $1\n').replace(/<h2[^>]*>([\s\S]*?)<\/h2>/g, '\n## $1\n').replace(/<dt>([\s\S]*?)<\/dt>\s*<dd>([\s\S]*?)<\/dd>/g, '\n- **$1** $2').replace(/<p[^>]*>([\s\S]*?)<\/p>/g, '\n$1\n').replace(/<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g, '[$2]($1)').replace(/<code>([\s\S]*?)<\/code>/g, '`$1`').replace(/<br\s*\/?>/g, '\n');
  s = s.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/\n{3,}/g, '\n\n').trim();
  return s + `\n\n---\n${OPERATOR} · https://${host}/\n`;
}
const wantsMarkdown = req => { const a = (req.headers.get('accept') || '').toLowerCase(); return a.includes('text/markdown') && (a.indexOf('text/markdown') < (a.indexOf('text/html') === -1 ? 1e9 : a.indexOf('text/html'))); };
export function withForAgents(inner) {
  return { ...inner, async fetch(request, env, ctx) {
    const u = new URL(request.url); const p = u.pathname.replace(/\/+$/, '') || '/'; const host = u.hostname.replace(/^www\./, '');
    const ua = request.headers.get('user-agent') || ''; const self = /^Allooloo for-agents/.test(ua);
    const r = await inner.fetch(request, env, ctx);
    if (self || !(request.method === 'GET' || request.method === 'HEAD')) return r;
    if (r.status === 200 && (r.headers.get('content-type') || '').includes('text/html') && wantsMarkdown(request)) {   // CLEAN-01: Markdown for Agents
      const hm = new Headers(r.headers); hm.set('content-type', 'text/markdown; charset=utf-8'); hm.set('vary', 'Accept'); hm.delete('content-length');
      return new Response(request.method === 'HEAD' ? null : toMarkdown(await r.text(), host), { status: 200, headers: hm });
    }
    if (SIX.includes(p) && r.status === 404) { const g = await gen(inner, request, env, ctx, host, p); return g || r; }
    if (p === '/robots.txt' && r.status === 404) return new Response(`User-agent: *\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\nAllow: /\n\nSitemap: https://${host}/sitemap.xml\n`, { headers: H('text/plain; charset=utf-8') });   // AUDIT-01 F5
    if (p === '/sitemap.xml' && r.status === 404) return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n<url><loc>https://${host}/</loc></url>\n</urlset>\n`, { headers: H('application/xml; charset=utf-8') });   // AUDIT-01 F5
    const ct = r.headers.get('content-type') || '';
    if (r.status !== 200 || !ct.includes('text/html')) return r;
    let b = await r.text(); if (b.includes('FOR AGENTS</span>')) { const hv = new Headers(r.headers); hv.append('vary', 'Accept'); return new Response(b, { status: r.status, headers: hv }); }   // CLEAN-01: Vary (the body is unchanged)
    b = b.includes('</footer>') ? b.replace(/<\/footer>(?![\s\S]*<\/footer>)/, ROW + '</footer>') : b.replace(/<\/body>/i, `<footer>${ROW}</footer></body>`);
    const h = new Headers(r.headers); h.delete('content-length'); h.append('vary', 'Accept'); return new Response(b, { status: r.status, headers: h });   // CLEAN-01: Vary
  } };
}
