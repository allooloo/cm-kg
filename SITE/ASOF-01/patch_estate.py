r"""patch_estate.py — ASOF-01: the estate source (CM-KG\ESTATE\worker). A .pre-asof01-2026-11-05 copy beside every file touched. Idempotent per file.
  chrome.js   NAV: "As Of" → https://getasof.ai/ to the right of Target Market, before Issuerwire (every surface on the shared template); the closing card of
              getasof.ai; SURFACES_VERSION 2026-11-05.1
  doors027.js the kind 'asof' (getasof.ai): classify, serveAs (www), target, label, desc, page args, facts, llms, paths, read at render
  surfaces.js getasof.ai's own card, descriptor and x402 file; /index.md (the Markdown twin by path, beside Accept negotiation); the read at render
  paygo.js    data-paygo.ai's machine door list: mcp.getasof.ai after mcp.gettargetmarket.ai, before Issuerwire
  nav02.js    the About page's machine door list: the same order
Usage: python -X utf8 -I patch_estate.py"""
import pathlib, shutil
W = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker')
def edit(name, pairs, mark):
    p = W / name; pre = W / name.replace('.js', '.pre-asof01-2026-11-05.js')
    s = p.read_text(encoding='utf-8')
    if mark in s: print(name, 'already patched'); return
    if not pre.exists(): shutil.copy2(p, pre)
    for o, n in pairs:
        assert s.count(o) == 1, (name, s.count(o), o[:90]); s = s.replace(o, n)
    p.write_text(s, encoding='utf-8'); print(name, 'patched')
edit('chrome.js', [
  ("export const SURFACES_VERSION = '2026-11-02.15';", "export const SURFACES_VERSION = '2026-11-05.1';   // .1 = ASOF-01: getasof.ai (the As Of door's page) and \"As Of\" on the nav of record, to the right of Target Market; was 2026-11-02.15\nconst SV_PREV_ASOF01 = '2026-11-02.15';"),
  ("['Target Market', 'https://gettargetmarket.ai/'], ['Issuerwire', 'https://issuerwire.ai/']];   // NAV-01", "['Target Market', 'https://gettargetmarket.ai/'], ['As Of', 'https://getasof.ai/'], ['Issuerwire', 'https://issuerwire.ai/']];   // ASOF-01 (2026-11-05): As Of to the right of Target Market, before Issuerwire · NAV-01"),
  ("const BANDS = { 'getorderability.ai': [", "const BANDS = { 'getasof.ai': ['Point-in-time proof.', 'Others sell point-in-time data; Allooloo sells point-in-time proof. The issuer record as it stood on any date, signed by the node of its market and receipted on the Record of Cleared Orders, callable by any agent over MCP and A2A.'],   // ASOF-01: the closing card (the book's line of record)\n  'getorderability.ai': ["),
], "ASOF-01 (2026-11-05): As Of to the right")
edit('doors027.js', [
  ("import * as G from './getord.js';", "import * as G from './getord.js';\nimport * as A from './asof.js';   // ASOF-01 (2026-11-05): getasof.ai, the point-in-time door's page (kind 'asof')"),
  ("  let m; const pg = PG.classifyP(h); if (pg) return pg;", "  let m; const as = A.classifyA(h); if (as) return as;   // ASOF-01\n  const pg = PG.classifyP(h); if (pg) return pg;"),
  ("export const serveAs = h => G.serveAs(h) || T.serveAs(h) || PG.serveAs(h);", "export const serveAs = h => A.serveAs(h) || G.serveAs(h) || T.serveAs(h) || PG.serveAs(h);   // ASOF-01: www.getasof.ai answers as getasof.ai"),
  ("export const bookDataG = G.bookData; export const docsBodyG = G.docsBodyG;", "export const bookDataG = G.bookData; export const docsBodyG = G.docsBodyG;\nexport const asofData = A.asofData; export const agentCardA = A.agentCardA; export const descriptorA = A.descriptorA; export const x402A = A.x402A;   // ASOF-01"),
  ("export const isNew = c => c && (c.kind === 'paygo' ||", "export const isNew = c => c && (c.kind === 'asof' || c.kind === 'paygo' ||"),
  ("  if (c.kind === 'getord') return G.targetG();", "  if (c.kind === 'getord') return G.targetG();\n  if (c.kind === 'asof') return A.targetA();   // ASOF-01"),
  ("export function label27(c) { if (c.kind === 'paygo'", "export function label27(c) { if (c.kind === 'asof') return A.TITLE; if (c.kind === 'paygo'"),
  ("  if (c.kind === 'getord') return G.descG();", "  if (c.kind === 'getord') return G.descG();\n  if (c.kind === 'asof') return A.descA();   // ASOF-01"),
  ("  if (c.kind === 'getord') { const d = G.sweep(ctx.live);", "  if (c.kind === 'asof') { const d = A.sweep(ctx.live); return { title: A.TITLE, h1: A.H1, state: 'live', asOf: d, body: A.asofBody(ctx, host), meta: { node: 'apex', as_of: d } }; }   // ASOF-01\n  if (c.kind === 'getord') { const d = G.sweep(ctx.live);"),
  ("export function facts27(c, host, live, ctx) { if (c.kind === 'paygo'", "export function facts27(c, host, live, ctx) { if (c.kind === 'asof') return A.factsA(host, live, ctx && ctx.asof); if (c.kind === 'paygo'"),
  ("export function llms27(c, host, live, ctx) { if (c.kind === 'paygo'", "export function llms27(c, host, live, ctx) { if (c.kind === 'asof') return A.llmsA(host, live, ctx && ctx.asof); if (c.kind === 'paygo'"),
  ("export function paths27(c) { if (c.kind === 'paygo'", "export function paths27(c) { if (c.kind === 'asof') return A.pathsA(); if (c.kind === 'paygo'"),
], "import * as A from './asof.js'")
edit('surfaces.js', [
  ("    if (c.kind === 'tm') {   // TMKT-01: the Target Market door's own card and descriptor",
   "    if (c.kind === 'asof') {   // ASOF-01: the As Of door's own card, descriptor and x402 file (the door is the router: mcp.getasof.ai); no generic CM-KG card, skills or OpenAPI here\n"
   "      if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json') return json(D27.agentCardA(host), kmeta);\n"
   "      if (p === '/mcp.json' || p === '/.well-known/mcp.json' || p === '/.well-known/mcp/server-card.json' || p === '/.well-known/mcp/server-cards.json') return json(D27.descriptorA(), kmeta);\n"
   "      if (p === '/.well-known/x402.json' || p === '/.well-known/x402') return json(D27.x402A(), kmeta);\n"
   "      if (p === '/openapi.json' || p === '/.well-known/skills.json' || p.startsWith('/.well-known/agent-skills')) return notFound(D27.paths27(c), kmeta);\n"
   "    }\n"
   "    if (c.kind === 'tm') {   // TMKT-01: the Target Market door's own card and descriptor"),
  ("      if (c.kind === 'getord') ctx.book = await D27.bookDataG(live);",
   "      if (c.kind === 'asof') ctx.asof = await D27.asofData(env, url);   // ASOF-01: the shelf ledger and the receipt counter, read at render\n"
   "      if (c.kind === 'getord') ctx.book = await D27.bookDataG(live);"),
  ("      if (p === '/llms.txt') return text(D27.llms27(c, host, live, ctx), meta,",
   "      if (p === '/index.md' && c.kind === 'asof') return markdown(AEO.toMarkdown(page({ host, title: a.title, desc: desc0, h1: a.h1, state: a.state, asOf: a.asOf, body: a.body }), host), meta, LINK);   // ASOF-01: the Markdown twin by path\n"
   "      if (p === '/llms.txt') return text(D27.llms27(c, host, live, ctx), meta,"),
], "c.kind === 'asof'")
edit('paygo.js', [("'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.issuerwire.ai/mcp',", "'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.issuerwire.ai/mcp',")], "https://mcp.getasof.ai/mcp")
edit('nav02.js', [("'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.issuerwire.ai/mcp'], operator: OPERATOR }, meta);", "'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.issuerwire.ai/mcp'], operator: OPERATOR }, meta);")], "https://mcp.getasof.ai/mcp")
