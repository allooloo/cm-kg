r"""patch_estate.py — DOORS-01: the estate source (CM-KG\ESTATE\worker). A .pre-doors01-2026-11-05 copy beside every file touched. Idempotent per file.
  chrome.js   the footer, three bands on every surface (allooloo.io included): FOR AGENTS (as now) · FOR DESKS (every live get_ door, FOR DESKS order, from the door
              check; a door not answering is not listed) · FOR HUMANS (as now, the trailing "· ·" before the two icons removed); SURFACES_VERSION 2026-11-05.2
  nav02.js    the door check also reads each get_ door's /mcp.json (200 = live) and hands the live list to the footer; the About page's door list in the doors order
  doors027.js the kind 'desk' (getfilings.ai · getticker.ai · getauditor.ai): classify, serveAs, target, label, desc, page args, facts, llms, paths, read at render
  surfaces.js the desk pages' own card, descriptor and x402 file; /index.md; the read at render
  asof.js     getasof.ai's llms.txt, facts and card carry the doors list in the same order
  paygo.js    data-paygo.ai's machine door list in the doors order
Usage: python -X utf8 -I patch_estate.py"""
import pathlib, shutil
W = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker')
def edit(name, pairs, mark):
    p = W / name; pre = W / name.replace('.js', '.pre-doors01-2026-11-05.js'); s = p.read_text(encoding='utf-8')
    if mark in s: print(name, 'already patched'); return
    if not pre.exists(): shutil.copy2(p, pre)
    for o, n in pairs:
        assert s.count(o) == 1, (name, s.count(o), o[:90]); s = s.replace(o, n)
    p.write_text(s, encoding='utf-8'); print(name, 'patched')
FH_OLD = "<a href=\"https://allooloo.io/security\">Security</a> · <a href=\"https://www.linkedin.com/company/allooloo-technologies-corp/\" aria-label=\"LinkedIn\">${icon('linkedin')}</a> · <a href=\"https://x.com/allooloo_ai\" aria-label=\"X\">${icon('x')}</a></p>`;"
FH_NEW = "<a href=\"https://allooloo.io/security\">Security</a> <a href=\"https://www.linkedin.com/company/allooloo-technologies-corp/\" aria-label=\"LinkedIn\">${icon('linkedin')}</a> <a href=\"https://x.com/allooloo_ai\" aria-label=\"X\">${icon('x')}</a></p>`;   // DOORS-01: the trailing \"· ·\" before the two icons removed"
edit('chrome.js', [
  ("export const SURFACES_VERSION = '2026-11-05.1';", "export const SURFACES_VERSION = '2026-11-05.2';   // .2 = DOORS-01: getfilings.ai · getticker.ai · getauditor.ai; the three-band footer (FOR AGENTS · FOR DESKS · FOR HUMANS) on every surface, allooloo.io included; was 2026-11-05.1\nconst SV_PREV_DOORS01 = '2026-11-05.1';"),
  (FH_OLD, FH_NEW),
  ("const COMPANY_LINE = `", "// DOORS-01: FOR DESKS — every live get_ door as its verb, in the doors order (nav order first, then the rest), each to its door; read from the door check (a door\n// that does not answer, or a held name, is never listed); omitted only while the first check has not answered\nexport const DESK_ORDER = ['get_issuer', 'get_orderability', 'get_target_market', 'get_as_of', 'get_filings', 'get_ticker', 'get_auditor'];\nconst FOR_DESKS = () => { const l = (DOORS && DOORS.desks) || []; const live = DESK_ORDER.map(t => l.find(x => x[0] === t)).filter(Boolean); return live.length ? `<p class=\"row\"><span class=\"kicker\">FOR DESKS</span> ${live.map(([t, u]) => `<a href=\"${u}\"><code>${t}</code></a>`).join(' · ')}</p>` : ''; };\nconst COMPANY_LINE = `"),
  ("  return `<footer><section class=\"band\" aria-label=\"Allooloo\"><p class=\"tag\">${esc(tg)}</p><p>${esc(bd)}</p></section>${company ? `<p class=\"line\">${OPERATOR} · 260-4611 Viking Way, Richmond, BC V6V 2K9, Canada</p>` : ''}${FOR_AGENTS}${company ? `<p class=\"row\">${FOOTER_ROW_COMPANY}</p>` : FOR_HUMANS() + COMPANY_LINE}</footer>`;",
   "  return `<footer><section class=\"band\" aria-label=\"Allooloo\"><p class=\"tag\">${esc(tg)}</p><p>${esc(bd)}</p></section>${FOR_AGENTS}${FOR_DESKS()}${FOR_HUMANS()}${COMPANY_LINE}</footer>`;   // DOORS-01: three bands on every surface; allooloo.io takes the roll it missed (its company row, FOOTER_ROW_COMPANY, is kept in this file, unused)"),
], "DOORS-01: three bands")
edit('nav02.js', [
  ("  DOORS = { live: nl.length, answering: up.filter(Boolean).length, read_at: new Date().toISOString(), method: 'list_nodes, then each live door /mcp.json (the digest\\'s door check)' }; DOORS_AT = Date.now(); setDoors(DOORS);",
   "  const desks = (await Promise.all(DESKS.map(async ([t, u, mj]) => { try { const r = await fetch(mj, { headers: UA, redirect: 'manual', cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(8000) }); return r.status === 200 ? [t, u] : null; } catch (e) { return null; } }))).filter(Boolean);   // DOORS-01: the get_ doors that answer\n"
   "  DOORS = { live: nl.length, answering: up.filter(Boolean).length, desks, read_at: new Date().toISOString(), method: 'list_nodes, then each live door /mcp.json (the digest\\'s door check); each get_ door /mcp.json for FOR DESKS' }; DOORS_AT = Date.now(); setDoors(DOORS);"),
  ("import COPY from './about-copy.js';", "import COPY from './about-copy.js';\nimport { DESKS } from './desks.js';   // DOORS-01"),
  ("'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.issuerwire.ai/mcp'], operator: OPERATOR }, meta);", "'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.getfilings.ai/mcp', 'https://mcp.getticker.ai/mcp', 'https://mcp.getauditor.ai/mcp', 'https://mcp.issuerwire.ai/mcp'], operator: OPERATOR }, meta);   // DOORS-01: the doors order"),
], "import { DESKS } from './desks.js'")
edit('doors027.js', [
  ("import * as A from './asof.js';", "import * as A from './asof.js';\nimport * as DK from './desks.js';   // DOORS-01 (2026-11-05): getfilings.ai · getticker.ai · getauditor.ai (kind 'desk')"),
  ("  let m; const as = A.classifyA(h); if (as) return as;   // ASOF-01", "  let m; const dk = DK.classifyD(h); if (dk) return dk;   // DOORS-01\n  const as = A.classifyA(h); if (as) return as;   // ASOF-01"),
  ("export const serveAs = h => A.serveAs(h) ||", "export const serveAs = h => DK.serveAs(h) || A.serveAs(h) ||"),
  ("export const asofData = A.asofData;", "export const deskData = DK.deskData; export const agentCardD = DK.agentCardD; export const descriptorD = DK.descriptorD; export const x402D = DK.x402D;   // DOORS-01\nexport const asofData = A.asofData;"),
  ("export const isNew = c => c && (c.kind === 'asof' ||", "export const isNew = c => c && (c.kind === 'desk' || c.kind === 'asof' ||"),
  ("  if (c.kind === 'asof') return A.targetA();   // ASOF-01", "  if (c.kind === 'asof') return A.targetA();   // ASOF-01\n  if (c.kind === 'desk') return DK.targetD(c);   // DOORS-01"),
  ("export function label27(c) { if (c.kind === 'asof') return A.TITLE;", "export function label27(c) { if (c.kind === 'desk') return DK.titleD(c); if (c.kind === 'asof') return A.TITLE;"),
  ("  if (c.kind === 'asof') return A.descA();   // ASOF-01", "  if (c.kind === 'asof') return A.descA();   // ASOF-01\n  if (c.kind === 'desk') return DK.descD(c);   // DOORS-01"),
  ("  if (c.kind === 'asof') { const d = A.sweep(ctx.live);", "  if (c.kind === 'desk') { const d = DK.sweepD(ctx.live); return { title: DK.titleD(c), h1: DK.h1D(c), state: 'live', asOf: d, body: DK.deskBody(c, ctx, host), meta: { node: 'apex', as_of: d } }; }   // DOORS-01\n  if (c.kind === 'asof') { const d = A.sweep(ctx.live);"),
  ("export function facts27(c, host, live, ctx) { if (c.kind === 'asof')", "export function facts27(c, host, live, ctx) { if (c.kind === 'desk') return DK.factsD(c, host, live, ctx); if (c.kind === 'asof')"),
  ("export function llms27(c, host, live, ctx) { if (c.kind === 'asof')", "export function llms27(c, host, live, ctx) { if (c.kind === 'desk') return DK.llmsD(c, host, live, ctx); if (c.kind === 'asof')"),
  ("export function paths27(c) { if (c.kind === 'asof')", "export function paths27(c) { if (c.kind === 'desk') return DK.pathsD(); if (c.kind === 'asof')"),
], "import * as DK from './desks.js'")
edit('surfaces.js', [
  ("    if (c.kind === 'asof') {   // ASOF-01: the As Of door's own card",
   "    if (c.kind === 'desk') {   // DOORS-01: each door page's own card, descriptor and x402 file (the door is the router); no generic CM-KG card, skills or OpenAPI here\n"
   "      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(D27.agentCardD(c, host), kmeta);\n"
   "      if (p === '/mcp.json' || p === '/.well-known/mcp.json' || p === '/.well-known/mcp/server-card.json' || p === '/.well-known/mcp/server-cards.json') return json(D27.descriptorD(c), kmeta);\n"
   "      if (p === '/.well-known/x402.json' || p === '/.well-known/x402') return json(D27.x402D(c), kmeta);\n"
   "      if (p === '/openapi.json' || p === '/.well-known/skills.json' || p.startsWith('/.well-known/agent-skills')) return notFound(D27.paths27(c), kmeta);\n"
   "    }\n"
   "    if (c.kind === 'asof') {   // ASOF-01: the As Of door's own card"),
  ("      if (c.kind === 'asof') ctx.asof = await D27.asofData(env, url);", "      if (c.kind === 'desk') ctx.desk = await D27.deskData(env, c.key);   // DOORS-01: the gate's receipt counter, read at render\n      if (c.kind === 'asof') ctx.asof = await D27.asofData(env, url);"),
  ("      if (p === '/index.md' && c.kind === 'asof')", "      if (p === '/index.md' && (c.kind === 'asof' || c.kind === 'desk'))"),
], "c.kind === 'desk'")
DL = "Doors: get_issuer https://getissuer.ai/ · get_orderability https://getorderability.ai/ · get_target_market https://gettargetmarket.ai/ · get_as_of https://getasof.ai/ · get_filings https://getfilings.ai/ · get_ticker https://getticker.ai/ · get_auditor https://getauditor.ai/"
DA = "['get_issuer https://getissuer.ai/', 'get_orderability https://getorderability.ai/', 'get_target_market https://gettargetmarket.ai/', 'get_as_of https://getasof.ai/', 'get_filings https://getfilings.ai/', 'get_ticker https://getticker.ai/', 'get_auditor https://getauditor.ai/']"
edit('asof.js', [
  ("    licence: 'https://data-licence.ai/', products: [", f"    licence: 'https://data-licence.ai/', doors: {DA}, products: ["),
  ("'10. Products: Issuer https://getissuer.ai/ · Orderability https://getorderability.ai/ · Target Market https://gettargetmarket.ai/ · As Of https://getasof.ai/ · Issuerwire https://issuerwire.ai/',", f"'10. Products: Issuer https://getissuer.ai/ · Orderability https://getorderability.ai/ · Target Market https://gettargetmarket.ai/ · As Of https://getasof.ai/ · Issuerwire https://issuerwire.ai/ · {DL}',   // DOORS-01: the doors order"),
  ("    'x-allooloo': { page: `https://${host}/`, router_card: AGENT, receipts: RCO, products: [", f"    'x-allooloo': {{ page: `https://${{host}}/`, router_card: AGENT, receipts: RCO, doors: {DA}, products: ["),
], "'get_auditor https://getauditor.ai/'")
edit('paygo.js', [("'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.issuerwire.ai/mcp',", "'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.getfilings.ai/mcp', 'https://mcp.getticker.ai/mcp', 'https://mcp.getauditor.ai/mcp', 'https://mcp.issuerwire.ai/mcp',")], "https://mcp.getfilings.ai/mcp")
