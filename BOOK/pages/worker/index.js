// book-pages — BOOK-04 (2026-10-31): the Book of Markets on the human pages. Values come from the Book only (read from the mirror allooloocmkgapex/book at
// request time, SAS under container policy book-wire-read, edge-cached BOOK_TTL seconds); prose comes from the canonical texts only (pages-canon.json,
// read verbatim from SM-ECO-10060 v1.0 and ACM-68000 v1.0 by pages_canon.py). Nothing typed.
//   the member hosts (market code + -eco-10060.org / .ai / .com) at "/"   the member page as it stands, its Book rows replaced by the full ECO catalogue (Appendix A) of the market
//   sm-eco-10060.org / .ai / .com at /market/ + market code               the whole chapter: the five sections, each under its own version line
//   acm-68000.org / .ai / .com at /market/ + market code                  the rule register of the market: its ACM section and the register revisions it names
// AIO, AMP and ESG render inside the sm-eco chapter only. Rendering rules: every rendered value carries its source_url and source_date; not_found renders
// "not found"; inferred rows and conflict rows never render (they stay in the Book for the readers); no counts in text.
// Every other request passes to the host's own origin (Pages) or, for the hosts stack-pages serves, to stack-pages (service binding STACK), unchanged.
import CANON from '../pages-canon.json';
import { acmFirstResponse } from './acm_first.js';   // TEXTS-01
const BLOB = 'https://allooloocmkgapex.blob.core.windows.net/book/';
const STACK_MEMBERS = ['hk', 'ky', 'bm', 'je', 'tw', 'lu'];   // STACK-01 MEMBERS-02: these member hosts are served by stack-pages
const VERSION = 'book-pages 2026-11-02.3';   // .3 = TMKT-04: AIO-10060 v1.2 at aio-10060.org, v1.1 kept at aio-10060.org/v1.1/; was 2026-11-02.2 —   // .2 = TMKT-01: manufacturer_evidence_accepted renders not found where the review held objects; was 2026-11-02.1   // .1 = GETORD-01: the AIO pages name the orderability door (getorderability.ai, mcp.getorderability.ai/mcp); every market page's ask line links to it   // 2026-11-01.1 =   // .1 = DEFECTS-01: the market page names, at its head, the client categories get_orderability takes — the signed AIO client_categories, in the regime's own words   // 2026-10-31.10 =   // .10 = AIO-01: the AIO pages name the orderability door and get_orderability; member pages carry the Orderability door line   //   // .9 = CEO confirmations: esg-10060.org ESG-10060's own zone; sm-eco-10060 one subtitle line   // .8 = TEXTS-02: ESG-10060's page at sm-eco-10060.org/esg/; sm-eco-10060.ai/.com twins of the apex body   // .7 = READ-01: the arrow is the mono arrow (class="arrow"); AIO/AMP one subtitle line, host line without trailing slash; chapter path written out, no placeholder; first use once per page   // .6 = CPG-02: member pages and the SM-ECO apex regenerated from the canonical texts; the family's shell and stack row; stack_version on descriptors   // .5 = the AIO-10060 / AMP-10060 zones are the pages (.org canonical, .ai/.com twins, same body); sm-eco /aio/ /amp/ the second door   // .4 = TEXTS-01: AIO-10060 / AMP-10060 standard pages + descriptors, their names on the chapter sections, ACM first use   // .3 = a seed kept against a recorded conflict renders (the seed is the value of record)   // .2 = a seed's missing source_date renders "not found" beside its value
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const NF = 'not_found';
async function blob(env, name, list) {
  const u = BLOB + (list ? `?restype=container&comp=list&prefix=${encodeURIComponent(name)}` : name.split('/').map(encodeURIComponent).join('/'));
  const r = await fetch(u + (list ? '&' : '?') + String(env.BOOK_SAS).trim().replace(/^\?/, ''), { cf: { cacheTtl: Number(env.BOOK_TTL || 300), cacheEverything: true } });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`book mirror ${r.status}`);
  return list ? r.text() : r.json();
}
async function chapter(env, cc) {
  const xml = await blob(env, `${cc}/chapters/`, true); if (!xml) return null;
  const vs = [...xml.matchAll(/<Name>([^<]+)<\/Name>/g)].map(m => m[1]).map(n => [Number((/\.chapter\.v(\d+)\.json$/.exec(n) || [])[1] || 0), n]).filter(x => x[0]).sort((a, b) => b[0] - a[0]);
  if (!vs.length) return null;
  const man = await blob(env, vs[0][1]); const secs = {};
  await Promise.all(man.sections.map(async ref => { secs[ref.family] = await blob(env, ref.path); }));
  return { man, secs };
}
// ---- values ------------------------------------------------------------------------------------------------------------------------------------------
const isEl = v => v && typeof v === 'object' && !Array.isArray(v) && 'name' in v && 'value' in v;
const hidden = f => !!(f && (f.inferred || (f.conflict && f.value === NF && f.name !== 'manufacturer_evidence_accepted')));   // TMKT-01: the field renders not found even where the review held objects (the conflict stays in the Book)   // BOOK-02 addendum: a seed kept against a differing reading renders the seed; its conflict stays in the Book
function val(v) {
  if (v === NF) return '<span class="nf">not found</span>';
  if (v === null || v === undefined) return '<span class="nf">not found</span>';
  if (Array.isArray(v)) return v.length ? `<ul>${v.map(x => `<li>${val(x)}</li>`).join('')}</ul>` : '<span class="nf">not found</span>';
  if (typeof v === 'object') {
    if (isEl(v)) return el(v);
    const ks = Object.keys(v); if (!ks.length) return '<span class="nf">not found</span>';
    return `<dl class="kv">${ks.map(k => `<dt>${esc(k)}</dt><dd>${val(v[k])}</dd>`).join('')}</dl>`;
  }
  if (typeof v === 'string' && /^https?:\/\//.test(v)) return `<a href="${esc(v)}">${esc(v)}</a>`;
  return esc(v);
}
const src = f => f.source_url ? `<p class="src">source <a href="${esc(f.source_url)}">${esc(f.source_url)}</a> · dated ${f.source_date ? esc(f.source_date) : '<span class="nf">not found</span>'}</p>` : '';   // a seed read before source_date was kept shows its date as the Book holds it: not found
// a field element: not_found → "not found"; a value always with its source_url and source_date (a date the Book does not hold reads "not found"); no source_url → not rendered as a value
function el(f) {
  if (hidden(f)) return '';
  if (f.value === NF || !f.source_url) return '<span class="nf">not found</span>';
  return `${val(f.value)}${src(f)}`;
}
function rows(fields, meanings) {
  const M = Object.fromEntries((meanings || []).map(m => [m.name, m.meaning]));
  return `<table class="book"><tbody>${fields.filter(f => !hidden(f)).map(f => `<tr><th scope="row"><code>${esc(f.name)}</code>${M[f.name] ? `<span class="mean">${esc(M[f.name])}</span>` : ''}</th><td>${el(f)}</td></tr>`).join('')}</tbody></table>`;
}
const vline = (s, ref) => `<p class="ver">${esc(s.family)} · <code>${esc(s.version)}</code>${s.supersedes ? ` · supersedes <code>${esc(s.supersedes)}</code>` : ''} · produced ${esc(s.produced_at || '')}${ref ? ` · <a href="${esc(ref)}">signed on the node door</a>` : ''}</p>`;
const apx = fam => CANON.sm_eco.appendices[fam] || { heading: fam, text: [] };
function section(fam, s, door) {
  const A = apx(fam); const cat = CANON.catalogue[fam];
  let body;
  if (fam === 'AMP') {   // one block of the Appendix D fields per venue, keyed by venue_mic
    const blocks = []; let cur = null;
    for (const f of s.fields || []) { if (f.name === 'venue_mic') { cur = []; blocks.push(cur); } if (cur) cur.push(f); }
    body = blocks.map(b => `<h4>venue_mic · ${el(b[0]) || '<span class="nf">not found</span>'}</h4>${rows(b.slice(1), cat)}`).join('');
  } else body = rows(s.fields || [], cat);
  const S = CANON.standards && CANON.standards[fam];   // TEXTS-01: the AIO and AMP sections carry their standard's name and link
  const std = S ? `<p class="ver">standard <a href="${esc(S.page)}">${esc(S.id)} · ${esc(S.name)}</a></p>` : '';
  return `<h2>${esc(A.heading)}</h2>${std}${vline(s, door ? `${door}/book/${fam.toLowerCase()}.json` : null)}${A.text.map(t => `<p>${esc(t)}</p>`).join('')}${body}`;
}
// ---- a standard's own page (TEXTS-01: AIO-10060, AMP-10060) — from its canonical text only: head, mission verbatim, contract, what it owns, schema v0.1 ----
function blocksHtml(blocks) {
  return (blocks || []).map(b => b.sub ? `<h3>${esc(b.sub)}</h3>` : b.table ? `<table class="book"><thead><tr>${b.table[0].map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${b.table.slice(1).map(r => `<tr>${r.map((c, i) => i === 0 ? `<th scope="row"><code>${esc(c)}</code></th>` : `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>` : b.t ? (/\s→\s/.test(b.t) ? `<p class="arrow">${esc(b.t)}</p>` : `<p>${esc(b.t)}</p>`) : '').join('');   // READ-01: a line of the arrow is the mono arrow, as the family's other pages set it
}
function descriptor(S, host) {   // the standard's machine descriptor, beside its page on every host that serves it (the zone .org/.ai/.com and the second door)
  const here = host.startsWith('sm-eco-10060.') ? `https://${host}/${S.id.split('-')[0].toLowerCase()}/` : `https://${host}/`;
  return { standard: S.id, name: S.name, title: S.head[1], version: S.head[2], mission: S.mission, page: S.page, this_page: here, twins: S.twins, second_door: S.second_door,
    canonical_text: CANON.source[S.id] ? CANON.source[S.id].split('\\').pop() : null, contract: S.contract.map(x => `${x.n}. ${x.title}`), owns: S.owns.map(x => `${x.n}. ${x.title}`),
    schema: S.schema_fields.map(x => ({ section: x.section, fields: x.fields, state: 'proposed v0.1 (unratified)' })), holder: 'Allooloo Technologies Corp.', licence: 'MIT',
    ...(S.id === 'AIO-10060' ? { door: AIO_DOOR } : {}),   // AIO-01
    chapter_section: `SM-ECO-10060 chapter, ${S.id.split('-')[0]} section — https://sm-eco-10060.org/market/ followed by the market code (e.g. https://sm-eco-10060.org/market/ca/)`, stack_version: S.stack_version || CANON.stack };   // CPG-02: each member's descriptor references the stack version
}
// READ-01 / CEO confirmation: one subtitle line, as the family's other pages carry it — the text's head line with its version written in ("canonical text
// v1.0"); the head line is not repeated below the title and the version line is not printed apart
function oneLine(head) {
  const ver = (/Version\s+([\d.]+)/.exec(head[2] || '') || [])[1]; if (!ver) return head[1];
  return /Canonical text/i.test(head[1]) ? head[1].replace(/Canonical text/i, `canonical text v${ver}`) : `${head[1]} · canonical text v${ver}`;
}
// AIO-01 (CEO 2026-10-31): the orderability door — where the outcome is produced, by whom, signed and receipted how
const AIO_DOOR = { door_page: 'https://getorderability.ai/', door: 'https://mcp.getorderability.ai/mcp', tool: 'get_orderability', arguments: ['subject', 'client_category'],   // GETORD-01: the orderability door
   node_door_example: 'https://mcp.ca-cm-kg.ai/mcp', roster: 'https://mcp.getissuer.ai/nodes.json', apex: 'https://mcp.getissuer.ai/mcp', signed: 'allooloo-eco-2026-10 (the producing node)', receipts: 'https://mcp.rco-records.ai/mcp (writer: the node)' };
const AIO_DOOR_HTML = `<h2>The door</h2><p>The orderability door: <a href="https://getorderability.ai/">getorderability.ai</a> — <code>https://mcp.getorderability.ai/mcp</code>, the same router as mcp.getissuer.ai, routing <code>get_orderability</code> by subject to the node that holds it.</p><p>Outcomes are produced on each market node's own door by the tool <code>get_orderability(subject, client_category)</code> — for Canada <a href="https://mcp.ca-cm-kg.ai/mcp">https://mcp.ca-cm-kg.ai/mcp</a>; the roster <a href="https://mcp.getissuer.ai/nodes.json">mcp.getissuer.ai/nodes.json</a> names every node's door. The apex <a href="https://mcp.getissuer.ai/mcp">mcp.getissuer.ai/mcp</a> routes the same call by subject to the node that holds it.</p><p>The market is the door's own; the client category is one the market's chapter names in client_categories[]; the rule is the market's current ACM-68000 register revision. Each outcome is signed by the producing node (kid allooloo-eco-2026-10) and each read is receipted at <a href="https://mcp.rco-records.ai/mcp">mcp.rco-records.ai</a>, the node as writer.</p>`;
async function standardPage(env, fam, host, prior) {   // TMKT-04: prior = an earlier version kept at its own URL (CANON.prior)
  const S = prior || CANON.standards[fam]; const root = await rootOf(env, 'sm-eco-10060');
  const path = prior ? new URL(prior.page).pathname : host.startsWith('sm-eco-10060.') ? `/${fam.toLowerCase()}/` : '/';
  const dpath = `${path}${S.id.toLowerCase()}.json`;
  const eyebrow = oneLine(S.head);
  let content = `<p class="mission"><b>${esc(S.mission)}</b></p>`;
  for (const part of S.contract) content += `<h2>${esc(part.title)}</h2>${blocksHtml(part.blocks)}`;
  for (const part of S.owns) content += `<h2>${esc(part.title)}</h2>${blocksHtml(part.blocks)}`;
  for (const part of S.schema) content += `<h2>${esc(part.title)}</h2>${blocksHtml(part.blocks)}`;
  if (fam === 'AIO') content += AIO_DOOR_HTML;   // AIO-01: the door and the tool
  if (prior) content = `<p class="meta">This is ${esc(S.id)} as published at ${esc(S.head[2])}. The version in force: <a href="${esc(prior.superseded_by)}">${esc(prior.superseded_by)}</a>.</p>` + content;   // TMKT-04
  else if (fam === 'AIO' && CANON.prior && CANON.prior['AIO@1.1']) content += `<p class="meta">Earlier version, kept at its own URL: <a href="/v1.1/">AIO-10060 v1.1</a>.</p>`;   // TMKT-04
  content += `<h2>Machine surfaces</h2><p class="meta"><a href="${esc(dpath)}">${esc(dpath)}</a> · chapter sections: <code>sm-eco-10060.org/market/</code> followed by the market code (<a href="https://sm-eco-10060.org/market/ca/">sm-eco-10060.org/market/ca/</a>)</p>`;
  let html = shell(root, { eyebrow, h1: S.id, title: `${S.id} — ${S.name} — Canonical`, canonical: S.page, h1host: `${host}${path}`.replace(/\/$/, ''), content });
  html = html.replace(/<h1>SM-ECO-10060/, `<h1>${esc(S.id)}`).replace(/<p class="meta">SM-ECO-10060 — the jurisdiction layer[^<]*<\/p>/, '').replace(/<p class="subtitle">Sovereign Manifest[^<]*<\/p>/, '').replace(/<p class="mission">[\s\S]*?<\/p>\s*(?=<p class="subtitle">)/, '').replace(/<div class="badge">[^<]*<\/div>/, '');
  return html;
}
// ---- the register ------------------------------------------------------------------------------------------------------------------------------------
async function revisions(env, acm) {
  const out = []; const seen = new Set();
  const refs = (acm.fields || []).filter(f => !hidden(f) && f.value && f.value !== NF && /_revision_ref$/.test(f.name)).map(f => f.value);
  const want = [];
  for (const r of refs) for (const x of (Array.isArray(r) ? r : [r])) if (x && x.path) want.push(x.path);
  while (want.length) {
    const p = want.shift(); if (seen.has(p)) continue; seen.add(p);
    const r = await blob(env, p); if (!r) continue; out.push({ path: p, rev: r });
    for (const d of [].concat(r.dependencies || [], r.components || [])) if (d && d.path) want.push(d.path);
  }
  return out;
}
const IDENT = ['rule_version', 'rule_family', 'revision', 'schema_version', 'duty', 'published_at', 'content_hash'];
function revisionBlock(r, path) {
  const M = Object.fromEntries(CANON.revision_fields.map(m => [m.name, m.meaning]));
  const ident = IDENT.filter(k => r[k] !== undefined).map(k => `<tr><th scope="row"><code>${esc(k)}</code>${M[k] ? `<span class="mean">${esc(M[k])}</span>` : ''}</th><td>${val(r[k])}</td></tr>`).join('');
  const rest = Object.keys(r).filter(k => !IDENT.includes(k) && !['note', 'proof'].includes(k)).map(k => {
    const v = r[k]; if (isEl(v) && hidden(v)) return '';
    return `<tr><th scope="row"><code>${esc(k)}</code>${M[k] ? `<span class="mean">${esc(M[k])}</span>` : ''}</th><td>${isEl(v) ? el(v) : val(v)}</td></tr>`;
  }).join('');
  return `<h3><code>${esc(r.rule_version)}</code></h3><p class="ver">register <code>${esc(path)}</code></p><table class="book"><tbody>${ident}${rest}</tbody></table>`;
}
// ---- shells ------------------------------------------------------------------------------------------------------------------------------------------
const CSS = '<style>.book{width:100%;border-collapse:collapse;margin:8px 0 18px}.book th{text-align:left;vertical-align:top;width:34%;padding:6px 8px;border-top:1px solid #e3e3e3}.book td{padding:6px 8px;border-top:1px solid #e3e3e3;vertical-align:top}.mean{display:block;font-weight:400;color:#6b6b6b;font-size:12px;margin-top:2px}.src{font-size:12px;color:#6b6b6b;margin-top:4px;word-break:break-all}.nf{color:#6b6b6b}.ver{font-size:13px;color:#444;margin:4px 0 8px}.kv dt{font-weight:600;font-size:13px}.kv dd{margin:0 0 6px 12px}.book ul{margin:0 0 0 16px}h4{margin:14px 0 4px;font-size:14px}</style>';
// CPG-02 (2026-10-31): one shell for every page this Worker serves — the family's look as stack-pages serves it (pages-canon.json shell: style, holder
// line, footer with the stack row of record, CPG-68000 v1.0 §5). No page borrows another page's body any more.
function shell(_unused, { title, canonical, h1host, content, eyebrow, h1 }) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><link rel="canonical" href="${esc(canonical)}"><style>${CANON.shell.style}</style>${CSS}</head>`
    + `<body><div class="container"><div class="topbar">${CANON.shell.topbar}</div><p class="eyebrow">${esc(eyebrow || '')}</p><h1>${esc(h1 || '')}<span class="host">${esc(h1host)}</span></h1>${content}${CANON.shell.footer}</div></body></html>`;
}
const HTML = (s, extra) => new Response(s, { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300', 'X-Book-Pages': VERSION, ...(extra || {}) } });
async function rootOf() { return ''; }   // CPG-02: the shell is the family's own (above); no root page is fetched
// DEFECTS-01 (2026-11-01): a desk copies the category from the page; the one the door takes is the AIO section's client_categories identifier
function askLine(aio, door) {
  const f = aio && (aio.fields || []).find(x => x.name === 'client_categories'); const v = f && Array.isArray(f.value) ? f.value : [];
  const ids = v.map(o => o && (o.identifier || o.category || o.name)).filter(Boolean); const src = door ? ` · <a href="${esc(door)}/book/aio.json">${esc(door)}/book/aio.json</a>` : '';
  if (!ids.length) return `<p class="meta"><b>Ask <a href="https://getorderability.ai/">get_orderability</a> with:</b> the chapter names no client category yet (AIO <code>client_categories</code> not found), so no outcome can be concluded here${src}</p>`;
  return `<p class="meta"><b>Ask <a href="https://getorderability.ai/">get_orderability</a> with:</b> ${ids.map(x => `<code>${esc(x)}</code>`).join(' · ')} — the client categories the chapter names, in the regime's own words (AIO <code>client_categories</code>, <code>${esc(aio.version)}</code>)${src}. The other category lists below are the chapter's ECO and ACM fields, not the identifiers the door takes.</p>`;
}
async function marketPage(env, std, cc, host) {
  const ch = await chapter(env, cc); if (!ch) return null;
  const m = ch.man;
  const doorUrl = await doorOf(env, m.node);
  const root = await rootOf(env, std);
  const juris = (m.scope && m.scope.jurisdiction) || cc;
  let content = `<p class="ver">chapter <code>${esc(m.version)}</code>${m.supersedes ? ` · supersedes <code>${esc(m.supersedes)}</code>` : ''} · as of ${esc(m.as_of)} · node <code>${esc(m.node)}</code>${doorUrl ? ` · <a href="${esc(doorUrl)}/book/manifest.json">${esc(doorUrl)}/book/</a>` : ''}</p>`;
  if (std === 'sm-eco-10060') {
    content += CANON.sm_eco.field_element ? `<p class="meta">${esc(CANON.sm_eco.field_element)}</p>` : '';
    content += askLine(ch.secs.AIO, doorUrl);   // DEFECTS-01: the categories to ask with, before the other category lists of the chapter
    for (const fam of ['ECO', 'ACM', 'AIO', 'AMP', 'ESG']) if (ch.secs[fam]) content += section(fam, ch.secs[fam], doorUrl);
  } else {
    const A = CANON.acm; const acm = ch.secs.ACM;
    content += `<h2>${esc(A.register_heading)}</h2>${A.register_text.map(t => `<p>${esc(t)}</p>`).join('')}`;
    if (acm) { content += `<h3>${esc(apx('ACM').heading)}</h3>${vline(acm, doorUrl ? `${doorUrl}/book/acm.json` : null)}${rows(acm.fields || [], CANON.catalogue.ACM)}`;
      content += `<h2>${esc(A.revision_heading)}</h2>`; for (const x of await revisions(env, acm)) content += revisionBlock(x.rev, x.path); }
  }
  const canonical = `https://${std}.org/market/${cc}/`;
  return shell(root, { eyebrow: `${std.toUpperCase()} · ${juris}`, h1: std.toUpperCase(), title: `${std.toUpperCase()} — ${juris} — ${m.version}`, canonical, h1host: `${host}/market/${cc}/`, content: `<p class="subtitle">${esc(juris)} · <code>${esc(m.jurisdiction_namespace || '')}</code></p>` + content });
}
let NODES = null;
async function doorOf(env, node) {
  try {
    if (!NODES) { const r = await fetch('https://mcp.getissuer.ai/nodes.json', { cf: { cacheTtl: 3600 } }); const j = await r.json(); NODES = Object.fromEntries((j.nodes || j).map(n => [n.node, n.door])); }
    return NODES[node] || null;
  } catch (e) { return null; }
}
let SMN = null;
async function registry() {   // the SM-ECO-10060 registry of members as sm-eco-10060.org serves it (nodes.json) — values, not prose
  if (!SMN) { const r = await fetch('https://sm-eco-10060.org/nodes.json', { cf: { cacheTtl: 3600 } }); SMN = await r.json(); }
  return SMN;
}
let ROSTER = null;
async function roster() { if (!ROSTER) { const r = await fetch('https://mcp.getissuer.ai/nodes.json', { cf: { cacheTtl: 3600 } }); const j = await r.json(); ROSTER = Object.fromEntries((j.nodes || j).map(n => [n.node.split('-')[0], n])); } return ROSTER; }
const a = (u, t) => u ? `<a href="${esc(u)}">${esc(t || u)}</a>` : '<span class="nf">not found</span>';
const SURF = ['/protocol.json', '/signals.json', '/nodes.json', '/health.json', '/dataset.jsonld', '/llms.txt', '/index.md', '/auth.md', '/.well-known/agent-card.json', '/.well-known/ai-catalog.json', '/.well-known/api-catalog', '/.well-known/acm-68000.json', '/.well-known/security.txt'];
function signalsTable() { const t = CANON.acm_signals; return `<table><thead><tr>${t[0].map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${t.slice(1).map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`; }
async function memberPage(env, request, cc) {
  const reg = await registry(); const m = (reg.members || []).find(x => String(x.code).toLowerCase() === cc);
  const ch = await chapter(env, cc); const host = new URL(request.url).hostname;
  if (!m) return new Response('not found', { status: 404 });
  const n = (await roster())[cc] || {}; const rg = n.region || {}; const doorUrl = n.door || (await doorOf(env, ch && ch.man.node));
  const NS = m.namespace || `${cc.toUpperCase()}-ECO-10060`;
  const facts = [['Allooloo node', n.node ? `<code>${esc(n.node)}</code>${rg.azure ? ` · Azure region ${esc(rg.azure)}` : ''}${rg.city ? ` · records served from ${esc(rg.city)}` : ''}` : esc(m.allooloo_node || '')],
    ['Record door', doorUrl ? `${a(doorUrl + '/mcp')}&nbsp;&nbsp;&nbsp;&nbsp;Agent Card: ${a(n.agent_card || m.agent_card)}` : a(m.record_door)],
    ['Exchanges on the record', esc((n.exchanges || []).join(' · ')) || '<span class="nf">not found</span>'],
    ['Orderability door', doorUrl ? `${a(doorUrl + '/mcp')}&nbsp;&nbsp;&nbsp;&nbsp;get_orderability (AIO-10060)` : '<span class="nf">not found</span>'],   // AIO-01: beside the record door
    ['Receipts door', `${a('https://mcp.rco-records.ai/mcp', 'mcp.rco-records.ai/mcp')} (RCO-10060 · Record of Cleared Orders)`],
    ['Example record', a(m.example_record)], ['Market duty page', a(m.market_duty_page, (m.market_duty_page || '').replace(/^https:\/\/|\/$/g, ''))], ['Market issuer page', a(m.market_issuer_page)]];
  let content = `<p class="mission"><b>${esc(CANON.sm_eco_text.mission)}</b></p><p class="subtitle">${esc(m.jurisdiction)} · ${esc(NS)} · Member · ${esc(m.jurisdiction)} under SM-ECO-10060</p>`
    + `<table><tbody>${facts.map(([k, v]) => `<tr><th scope="row">${esc(k)}</th><td>${v}</td></tr>`).join('')}</tbody></table>`;
  if (ch && ch.secs.ECO) content += `${section('ECO', ch.secs.ECO, doorUrl)}<p class="ver">chapter <code>${esc(ch.man.version)}</code> · <a href="https://sm-eco-10060.org/market/${cc}/">sm-eco-10060.org/market/${cc}/</a></p>`;
  content += `<h2>ACM-68000 signals</h2>${signalsTable()}<h2>Machine surfaces</h2><p class="meta">${SURF.map(x => `<a href="${x}">${x}</a>`).join(' · ')}</p>`;
  return HTML(shell(null, { eyebrow: 'SM-ECO-10060 · Member', h1: NS, title: `${NS} — ${m.jurisdiction} — Member`, canonical: `https://${cc}-eco-10060.org/`, h1host: host, content }));
}
// the SM-ECO-10060 apex, regenerated (CPG-02): head and mission verbatim, the six parts of its canonical text, the members of the registry one line each
function blocksH(blocks) { return blocksHtml(blocks); }
async function smEcoRoot(host) {
  const T = CANON.sm_eco_text; const reg = await registry(); const by = {};
  for (const m of reg.members || []) (by[m.region || ''] = by[m.region || ''] || []).push(m);
  let content = `<p class="mission"><b>${esc(T.mission)}</b></p>`;   // CEO confirmation: one subtitle line (the eyebrow), as on AIO/AMP
  for (const part of T.parts) content += `<h2>${esc(part.title)}</h2>${blocksH(part.blocks)}`;
  content += `<h2>Members</h2>` + Object.keys(by).sort().map(r => `<h3>${esc(r)}</h3><p class="meta">${by[r].map(m => `${a(m.canonical, m.namespace)} · ${esc(m.jurisdiction)}`).join('<br>')}</p>`).join('');
  content += `<h2>Machine surfaces</h2><p class="meta">${['/protocol.json', '/nodes.json', '/signals.json', '/llms.txt', '/.well-known/agent-card.json'].map(x => `<a href="${x}">${x}</a>`).join(' · ')} · chapters: <code>/market/</code> followed by the market code (<a href="/market/ca/">/market/ca/</a>)</p>`;   // READ-01: the path written out, no placeholder
  return HTML(shell(null, { eyebrow: oneLine(T.head), h1: 'SM-ECO-10060', title: `SM-ECO-10060 — ${T.head[1]}`, canonical: 'https://sm-eco-10060.org/', h1host: host, content }));
}
async function withStack(env, request) {   // a descriptor served from its own origin gains the stack version reference (CPG-02 item 3)
  const r = await fetch(request); if (!r.ok) return r; let j; try { j = await r.json(); } catch (e) { return r; }
  if (j && typeof j === 'object' && !Array.isArray(j) && !j.stack_version) j.stack_version = CANON.stack;
  return new Response(JSON.stringify(j, null, 1), { headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', 'X-Book-Pages': VERSION } });
}
export default {
  async fetch(request, env, ctx) {
    // READ-01: www answers with the apex's own body — the request is read as the apex's (same page, same host line; other paths reach the apex's origin)
    if (new URL(request.url).hostname.startsWith('www.')) { const u = new URL(request.url); u.hostname = u.hostname.slice(4); request = new Request(u, request); }
    const url = new URL(request.url); const host = url.hostname; const p = url.pathname;
    const pass = () => (env.STACK && /^(acm-68000\.|([a-z]{2})-eco-10060\.)/.test(host) && (host.startsWith('acm-68000.') || STACK_MEMBERS.includes(host.slice(0, 2)))) ? env.STACK.fetch(request) : fetch(request);
    if (request.method !== 'GET' && request.method !== 'HEAD') return pass();
    return acmFirstResponse(await route(request, env, url, host, p, pass));   // TEXTS-01: Agent Clearance Manifest written out once on first use
  }
};
async function route(request, env, url, host, p, pass) {
  try {
    const mm = /^([a-z]{2})-eco-10060\.(org|ai|com)$/.exec(host);
    if (host === 'sm-eco-10060.org' && (p === '/' || p === '/index.html')) return await smEcoRoot(host);   // CPG-02 (before the member branch: 'sm' is the apex, not a market)
    const twin = /^sm-eco-10060\.(ai|com)$/.test(host);   // TEXTS-02 (CEO 2026-10-31): sm-eco-10060.ai and .com serve the apex body as twins, no 301
    if (twin && (p === '/' || p === '/index.html')) return await smEcoRoot(host);
    if (mm && mm[1] !== 'sm' && (p === '/' || p === '/index.html')) return await memberPage(env, request, mm[1]);
    if (host === 'sm-eco-10060.org' && p === '/protocol.json') return await withStack(env, request);   // CPG-02 item 3
    const sm = /^(sm-eco-10060|acm-68000)\.(org|ai|com)$/.exec(host); const mk = /^\/market\/([a-z]{2})\/?$/.exec(p);
    if (sm && mk) { const html = await marketPage(env, sm[1], mk[1], host); return html ? HTML(html) : new Response('not found', { status: 404 }); }
    // TEXTS-01: the AIO-10060 and AMP-10060 standards' pages — at sm-eco-10060.org/aio/ and /amp/, and at the root of their own zones where they exist
    const sp = /^sm-eco-10060\.(org|ai|com)$/.test(host) ? /^\/(aio|amp|esg)(\/|\/index\.html|\/(aio|amp|esg)-10060\.json)?$/.exec(p) : null;   // TEXTS-02: /esg/ — ESG-10060's page
    const zm = /^(aio|amp|esg)-10060\.(org|ai|com|io)$/.exec(host);   // CEO confirmation: esg-10060.org, ESG-10060's own zone
    const fam = sp ? sp[1].toUpperCase() : zm ? zm[1].toUpperCase() : null;
    if (fam && CANON.standards && CANON.standards[fam]) {
      const S = CANON.standards[fam]; const dname = `${S.id.toLowerCase()}.json`;
      if (sp && !sp[2]) return Response.redirect(`https://${host}/${sp[1]}/`, 301);
      if ((sp && sp[3]) || (zm && (p === '/' + dname || p === '/.well-known/' + dname))) return new Response(JSON.stringify(descriptor(S, host), null, 1), { headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', 'X-Book-Pages': VERSION } });
      const pv = zm && fam === 'AIO' && CANON.prior && CANON.prior['AIO@1.1'] && /^\/v1\.1(\/|\/index\.html|\/aio-10060\.json)?$/.exec(p);   // TMKT-04: v1.1 at its own URL
      if (pv) { const P = CANON.prior['AIO@1.1']; if (!pv[1]) return Response.redirect(`https://${host}/v1.1/`, 301); if (pv[1] === '/aio-10060.json') return new Response(JSON.stringify({ ...descriptor(P, host), version: P.head[2], this_page: P.page, canonical_text: P.canonical_text, stack_version: P.stack_version, superseded_by: P.superseded_by }, null, 1), { headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', 'X-Book-Pages': VERSION } }); return HTML(await standardPage(env, fam, host, P)); }
      if (sp || p === '/' || p === '/index.html') return HTML(await standardPage(env, fam, host));
      if (zm && p === '/robots.txt') return new Response('User-agent: *\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\nAllow: /\n', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
      if (zm) return new Response('not found', { status: 404, headers: { 'X-Book-Pages': VERSION } });
    }
    if (twin) return await fetch(new Request(`https://sm-eco-10060.org${p}${url.search}`, request));   // TEXTS-02: every other path of a twin is the apex's own (descriptor, llms.txt, …)
  } catch (e) { return new Response(`book-pages: ${String(e.message || e)}`, { status: 502, headers: { 'X-Book-Pages': VERSION } }); }
  return pass();
}
