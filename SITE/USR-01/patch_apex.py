r"""patch_apex.py — USR-03: get_research, the eighth door, on the apex router (CM-KG\DOOR\apex\index.js; index.pre-usr01-2026-11-11.js beside; wrangler.toml
.pre copy beside). The tool is on the router's own tool list and card (mcp.getissuer.ai); the router resolves the issuer on its node, reads the page from the
page store (KV allooloo-research, binding RESEARCH), signs, receipts (writer allooloo) and answers. On the till at the standing per-read rate: free, the x402
offer only when asked; a paid read settles before the answer so the receipt names the settlement. The doors list carries the eighth door. 0.25.0 -> 0.26.0.
Idempotent: refuses on a second run. Usage: python -X utf8 -I patch_apex.py"""
import pathlib, shutil
D = pathlib.Path(r'C:\ALLOOLOO\CM-KG\DOOR\apex'); p = D / 'index.js'; pre = D / 'index.pre-usr01-2026-11-11.js'
s = p.read_text(encoding='utf-8')
if "from './research.js'" in s: raise SystemExit('already patched')
if not pre.exists(): shutil.copy2(p, pre)
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:80]); s = s.replace(o, n)
rep("import { DOORS as D01, DOOR_NAMES, DOOR_TOOLS } from './doors.js';", "import { RESEARCH_NAME, RESEARCH_TOOL, RESEARCH_LEAD, RESEARCH_PAGE, researchCall } from './research.js';   // USR-03: get_research, the eighth door (answered here from the page store)\nimport { DOORS as D01, DOOR_NAMES, DOOR_TOOLS } from './doors.js';")
rep("'get_filings', 'get_ticker', 'get_auditor'];   // DOORS-01 · ASOF-01", "'get_filings', 'get_ticker', 'get_auditor', 'get_research'];   // USR-03 · DOORS-01 · ASOF-01")
rep("const SERVER_VERSION = '0.25.0';", "const SERVER_VERSION = '0.26.0';   // 0.26.0 = USR-03 (2026-11-11): get_research on this router (Data Research: the research page of an issuer, from the page store, signed and receipted) · ")
rep("['get_auditor', 'https://getauditor.ai/']];", "['get_auditor', 'https://getauditor.ai/'], ['get_research', 'https://getresearch.ai/']];   // USR-03: the eighth door")
rep("let INDEX = null, NODES = null;", "TOOLS.push(RESEARCH_TOOL);   // USR-03: the router's own tool list and card carry the eighth door\nconst RESEARCH_LLMS = `\\nget_research (Data Research, ${RESEARCH_PAGE}): ${RESEARCH_LEAD} Input: ticker with exchange, or ISIN, or LEI. The router resolves the issuer on its node, reads the page, signs it (EdDSA, kid allooloo-cmr-2026-10, keyring https://allooloo.ai/.well-known/jwks.json) and receipts it at https://mcp.rco-records.ai/mcp (writer: allooloo). Reads are free; the x402 offer answers only when asked (x402-pay: 1). Licensed research: none loaded.\\n${DESKS_LINE}\\n`;\nlet INDEX = null, NODES = null;")
rep("    if (DOOR_NAMES.includes(name)) { const r = await d01Route(name, args, cx || {});", "    if (name === RESEARCH_NAME) { const r = await researchCall((cx || {}).env, cx || {}, args, { whichNode, forward }); if (r.receipt_id && cx) cx.decisions.push({ id: r.receipt_id, out: { receipt: { id: r.receipt_id } } }); return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: r.isError }); }   // USR-03\n    if (DOOR_NAMES.includes(name)) { const r = await d01Route(name, args, cx || {});")
rep("decisions: [], profile: PROFILES[p] ? p : null, env, host,", "decisions: [], ctx, profile: PROFILES[p] ? p : null, env, host,")
rep("      const batch = Array.isArray(body); const outs = [];", "      if (g.paid && !pay && (Array.isArray(body) ? body : [body]).some(m => m && m.method === 'tools/call' && m.params && m.params.name === RESEARCH_NAME)) { pay = await settle(env, g.paid, 'getresearch'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } }); cx.settlement = { network: pay.pr.network, transaction: pay.tx, payer: pay.payer }; }   // USR-03: a paid research read settles first, so its receipt names the settlement\n      const batch = Array.isArray(body); const outs = [];")
rep("    if (p === '/llms.txt') return new Response(llms(host), {", "    if (p === '/llms.txt') return new Response(llms(host) + (D01_HOST(host) || ASOF_HOST(host) || TM_HOST(host) || ORD_HOST(host) ? '' : RESEARCH_LLMS), {")
p.write_text(s, encoding='utf-8')
w = D / 'wrangler.toml'; t = w.read_text(encoding='utf-8')
if 'binding = "RESEARCH"' not in t:
    shutil.copy2(w, D / 'wrangler.toml.pre-usr01-2026-11-11')
    t = t.replace('# X402-A-01: the free tier', '# USR-03 (2026-11-11): the research page store (one page per issuer, key p:<cmr>; written by CM-KG\\RAILS\\research\\publish.py)\n[[kv_namespaces]]\nbinding = "RESEARCH"\nid = "7d0e0e4a059e444982b5eb1cc500efc1"\n\n# X402-A-01: the free tier'); assert 'RESEARCH' in t; w.write_text(t, encoding='utf-8')
print('patched', p)
