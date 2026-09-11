// Estate machine surface — one Worker, one template, every Allooloo zone that has no page of its own.
// Per host: an honest one-page HTML (what this domain is; live or not), /llms.txt, /facts.json, /robots.txt, /sitemap.xml, CMR headers v1, favicon set.
// Brand surfaces 301 to canonical (.com -> .ai for nodes and roots; cm-record.com -> .org; cm-kg.ai short brand -> the long-form root). Machine surfaces never sit behind a forward.
const OPERATOR = 'Allooloo Technologies Corp.';
const GLOBAL_DOOR = 'https://mcp.capitalmarketsknowledgegraph.ai';
const NODES = { ca: 'Canada', uk: 'United Kingdom', au: 'Australia', sg: 'Singapore', ch: 'Switzerland', de: 'Germany', fr: 'France', nl: 'Netherlands', hk: 'Hong Kong', jp: 'Japan', kr: 'South Korea', us: 'United States' };
const ORDER = ['ca', 'uk', 'au', 'sg', 'ch', 'de', 'fr', 'nl', 'hk', 'jp', 'kr', 'us'];
let LIVE = null, LIVE_AT = 0;
async function liveNodes() {
  if (LIVE && Date.now() - LIVE_AT < 300000) return LIVE;
  try {
    const r = await fetch(GLOBAL_DOOR + '/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'list_nodes', arguments: {} } }) });
    const j = await r.json(); LIVE = {}; for (const n of j.result.structuredContent.nodes) LIVE[n.node] = n; LIVE_AT = Date.now();
  } catch (e) { LIVE = LIVE || {}; }
  return LIVE;
}
function classify(host) {
  const h = host.replace(/^www\./, '');
  let m;
  if ((m = h.match(/^([a-z]{2})-cm-kg\.(org|ai|com)$/)) && NODES[m[1]]) return { kind: 'node', cc: m[1], tld: m[2], canonical: m[2] === 'com' ? `https://${m[1]}-cm-kg.ai/` : null };
  if (h === 'capitalmarketsknowledgegraph.ai') return { kind: 'root', role: 'graph' };
  if (h === 'capitalmarketsknowledgegraph.org') return { kind: 'root', role: 'standard' };
  if (h === 'capitalmarketsknowledgegraph.com') return { kind: 'redirect', canonical: 'https://capitalmarketsknowledgegraph.ai/' };
  if (h === 'cm-kg.org') return { kind: 'root', role: 'cmkg-standard' };
  if (h === 'cm-kg.io') return { kind: 'root', role: 'cmkg-twin' };
  if (h === 'cm-kg.ai') return { kind: 'redirect', canonical: 'https://capitalmarketsknowledgegraph.ai/' };
  if (h === 'cm-kg.com') return { kind: 'redirect', canonical: 'https://cm-kg.ai/' };
  if (h === 'cm-record.org') return { kind: 'record', role: 'standard' };
  if (h === 'cm-record.ai') return { kind: 'record', role: 'resolver' };
  if (h === 'cm-record.io') return { kind: 'record', role: 'twin' };
  if (h === 'cm-record.com') return { kind: 'redirect', canonical: 'https://cm-record.org/' };
  return { kind: 'unknown' };
}
function facts(host, c, live) {
  const base = { domain: host, operator: OPERATOR, as_of: new Date().toISOString().slice(0, 10), source: 'public-record', estate: 'Capital Markets Knowledge Graph (CM-KG)', corporate: 'https://allooloo.io', machine_paths: ['/llms.txt', '/facts.json', '/robots.txt', '/sitemap.xml'] };
  if (c.kind === 'node') {
    const n = live[`${c.cc}-cm-kg`] || {}; const isLive = !!n.live;
    return { ...base, kind: c.tld === 'org' ? 'node registry' : 'node door', node: `${c.cc}-cm-kg`, country: NODES[c.cc], live: isLive, records: isLive ? n.records : 0, node_as_of: isLive ? n.as_of : null,
      registry: `https://${c.cc}-cm-kg.org/`, door_host: `mcp.${c.cc}-cm-kg.ai`, door_url: isLive ? `https://mcp.${c.cc}-cm-kg.ai/mcp` : null, note: isLive ? 'the node door answers' : 'named; the door is not published until it answers' };
  }
  if (c.kind === 'root') return { ...base, kind: { graph: 'root of the graph', standard: 'standard mirror of the long-form root', 'cmkg-standard': 'CM-KG standard and beacon', 'cmkg-twin': 'CM-KG machine twin' }[c.role], live_nodes: Object.values(live).filter(n => n.live).map(n => n.node), global_door: `${GLOBAL_DOOR}/mcp`, nodes: ORDER.map(cc => ({ node: `${cc}-cm-kg`, country: NODES[cc], live: !!(live[`${cc}-cm-kg`] || {}).live })) };
  if (c.kind === 'record') return { ...base, kind: { standard: 'Capital Markets Record — the object standard (schema, signing, versions)', resolver: 'CMR resolver door', twin: 'CMR machine twin' }[c.role], spec: 'CMR v0 (draft)', signing: 'not yet live; no signature is stubbed', resolver_live: false, records_served_by: `${GLOBAL_DOOR}/mcp` };
  return base;
}
function page(host, c, f) {
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
  let title, body;
  if (c.kind === 'node') {
    title = `${f.node} — ${f.country} node ${c.tld === 'org' ? 'registry' : 'door'}`;
    body = `<p>${esc(f.country)} node of the Capital Markets Knowledge Graph. This host is the node's ${c.tld === 'org' ? 'public registry' : 'operating door'}.</p>
<p><strong>Status: ${f.live ? 'live' : 'not live'}.</strong> ${f.live ? `${f.records.toLocaleString()} records as of ${esc(f.node_as_of)}. The door answers at <code>${esc(f.door_url)}</code> (Streamable HTTP MCP, no auth).` : 'The node is named in the twelve-node build order; its door is not published until it answers.'}</p>
<p>Read live from the global door's <code>list_nodes</code>. ${f.live ? `<a href="https://mcp.${c.cc}-cm-kg.ai/">Node door</a> · ` : ''}<a href="${GLOBAL_DOOR}/">Global door</a></p>`;
  } else if (c.kind === 'root') {
    title = { graph: 'Capital Markets Knowledge Graph', standard: 'Capital Markets Knowledge Graph — standard', 'cmkg-standard': 'CM-KG — standard and beacon', 'cmkg-twin': 'CM-KG — machine twin' }[c.role];
    body = `<p>${esc(f.kind)}. Issuers as nodes; insiders, holders, auditors, transfer agents, parents and subsidiaries, dual listings and newswires as edges. Twelve sovereign market nodes, one global door. Public-record only.</p>
<p><strong>Live nodes: ${f.live_nodes.length ? esc(f.live_nodes.join(', ')) : 'none'}.</strong> The global door answers at <code>${esc(f.global_door)}</code> (Streamable HTTP MCP, no auth) and routes by identifier to the node that holds the name.</p>
<ul>${f.nodes.map(n => `<li>${esc(n.country)} — ${esc(n.node)} — ${n.live ? 'live' : 'not live'}</li>`).join('')}</ul>
<p><a href="${GLOBAL_DOOR}/">Global door</a> · <a href="https://allooloo.io/">Allooloo Technologies Corp.</a></p>`;
  } else if (c.kind === 'record') {
    title = { standard: 'Capital Markets Record — the standard', resolver: 'Capital Markets Record — resolver', twin: 'Capital Markets Record — machine twin' }[c.role];
    body = `<p>${esc(f.kind)}. One record per listed company, keyed on ISIN, ticker and LEI. Versioned, sourced, never deleted; every field names the registry it came from or the engine that read it and carries a state.</p>
<p><strong>Status: ${c.role === 'resolver' ? 'resolver not live' : 'draft standard (CMR v0)'}.</strong> Signing is not yet live and no signature is stubbed. Records are served today by the global door at <code>${esc(f.records_served_by)}</code>.</p>
<p><a href="${GLOBAL_DOOR}/">Global door</a> · <a href="https://allooloo.io/">Allooloo Technologies Corp.</a></p>`;
  } else { title = host; body = '<p>An Allooloo Technologies Corp. domain.</p>'; }
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><meta name="description" content="${esc(title)}. Operator: Allooloo Technologies Corp. Public-record only.">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest"><meta name="theme-color" content="#14213D"><link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt">
<style>body{font-family:'IBM Plex Sans',system-ui,sans-serif;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.55;background:#fff}h1{font-size:1.35rem}code{background:#f3f4f6;padding:.1em .3em}a{color:#0B6E4F}footer{margin-top:2rem;padding-top:.75rem;border-top:1px solid #E5E7EB;color:#6B7280;font-size:.85rem}</style></head>
<body><h1>${esc(title)}</h1>${body}<footer>${esc(host)} · ${OPERATOR} · public-record only · <a href="/llms.txt">llms.txt</a> · <a href="/facts.json">facts.json</a></footer></body></html>`;
}
function llms(host, c, f) {
  const lines = [`# ${host}`, `Operator: ${OPERATOR} (Vancouver, Canada). Corporate: https://allooloo.io`, `What this domain is: ${f.kind}.`];
  if (c.kind === 'node') lines.push(`Node: ${f.node} (${f.country}). Live: ${f.live ? 'yes' : 'no'}.${f.live ? ` Records: ${f.records} as of ${f.node_as_of}. Door: ${f.door_url}` : ' The door is not published until it answers.'}`);
  if (c.kind === 'root') lines.push(`Live nodes: ${f.live_nodes.join(', ') || 'none'}. Global door (Streamable HTTP MCP, no auth): ${f.global_door}. Tools: resolve_issuer, get_record, list_events_since, list_aliases, list_nodes.`);
  if (c.kind === 'record') lines.push(`Spec: ${f.spec}. Signing: ${f.signing}. Records served by ${f.records_served_by}.`);
  lines.push('Rules: public-record only; no prices, quotes or licensed market data; blank stays blank; nothing published before it answers.', 'Machine paths: /llms.txt, /facts.json, /robots.txt, /sitemap.xml');
  return lines.join('\n') + '\n';
}
function headers(extra) { return { 'X-CMR-Node': extra.node || 'estate', 'X-CMR-As-Of': extra.as_of || '', 'X-CMR-Version': String(extra.version || ''), 'X-CMR-Source': 'public-record', 'X-CMR-Operator': OPERATOR, 'Strict-Transport-Security': 'max-age=31536000', 'X-Content-Type-Options': 'nosniff', ...(extra.h || {}) }; }
export default {
  async fetch(request, env) {
    const url = new URL(request.url); const host = url.hostname; const c = classify(host);
    const apex = host.replace(/^www\./, '');
    if (c.kind === 'redirect' || c.canonical) return Response.redirect(c.canonical + url.pathname.replace(/^\//, '') + url.search, 301);   // brand hosts: .com -> canonical .ai/.org; cm-kg.ai -> long-form root
    if (host !== apex) return Response.redirect(`https://${apex}${url.pathname}${url.search}`, 301);
    const live = await liveNodes(); const f = facts(host, c, live);
    const meta = { node: c.kind === 'node' ? `${c.cc}-cm-kg` : (c.kind === 'root' ? 'global' : 'cm-record'), as_of: f.node_as_of || f.as_of, version: c.kind === 'node' && f.live ? 1 : '' };
    const p = url.pathname.replace(/\/+$/, '') || '/';
    if (p === '/') return new Response(page(host, c, f), { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300', ...headers(meta) } });
    if (p === '/llms.txt') return new Response(llms(host, c, f), { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=300', ...headers(meta) } });
    if (p === '/facts.json') return new Response(JSON.stringify(f, null, 1), { headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', ...headers(meta) } });
    if (p === '/robots.txt') return new Response(`User-agent: *\nAllow: /\nUser-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: Claude-User\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\nUser-agent: Bingbot\nAllow: /\nUser-agent: Applebot\nAllow: /\nUser-agent: Grok\nAllow: /\nSitemap: https://${host}/sitemap.xml\n`, { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=3600', ...headers(meta) } });
    if (p === '/sitemap.xml') return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://${host}/</loc></url><url><loc>https://${host}/llms.txt</loc></url><url><loc>https://${host}/facts.json</loc></url></urlset>\n`, { headers: { 'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=3600', ...headers(meta) } });
    if (['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest'].includes(p)) { const a = await env.ASSETS.fetch(new Request(url.origin + p)); const h = new Headers(a.headers); for (const [k, v] of Object.entries(headers(meta))) h.set(k, v); h.set('cache-control', 'public, max-age=86400'); return new Response(a.body, { status: a.status, headers: h }); }
    return new Response(JSON.stringify({ error: 'not_found', paths: ['/', '/llms.txt', '/facts.json', '/robots.txt', '/sitemap.xml'] }), { status: 404, headers: { 'content-type': 'application/json', ...headers(meta) } });
  }
};
