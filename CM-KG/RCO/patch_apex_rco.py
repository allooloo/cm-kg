r"""patch_apex_rco.py — RCO-A-01 (DAY ORDER 3, 2026-10-24): the resolver writes receipts. cm-kg-apex 0.13.0 -> 0.14.0: every tools/call of resolve_issuer
(an ISIN resolved) and get_signal (a signal returned) from an outside caller is given a decision_id, answers with a `receipt` block {decision_id,
get_receipt, page} and the header X-RCO-Decision-Id, and its receipt is written to mcp.rco-a2a.ai after the answer (ctx.waitUntil). Allooloo's own
renders (User-Agent "Allooloo …": eco-pages, acm-signals) leave no receipt — they write their own or render a test. The keyring of record
(kid allooloo-rco-2026-10) is served at /.well-known/jwks.json. index.js.pre-rcoa01-20261024 beside. Usage: python -X utf8 -I patch_apex_rco.py"""
import io, json, shutil, os
P = r"C:\ALLOOLOO\CM-KG\DOOR\apex\index.js"
if not os.path.exists(P + ".pre-rcoa01-20261024"): shutil.copy2(P, P + ".pre-rcoa01-20261024")
t = io.open(P, encoding="utf-8", newline="").read()
def sub(old, new, n=1):
    global t; assert t.count(old) == n, (old[:90], t.count(old)); t = t.replace(old, new)
PUB = json.load(open(r"C:\ALLOOLOO\CM-KG\RCO\rco-signing.pub.jwk.json", encoding="utf-8"))
sub("const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.13.0';   // 0.13.0 = ACM-SIGNALS-01",
    "import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';\nconst RCO_JWKS = { keys: [" + json.dumps(PUB) + "] };   // RCO-A-01: the receipt-signing key of record (public half)\n"
    "const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.14.0';   // 0.14.0 = RCO-A-01 (2026-10-24): receipts on resolve_issuer and get_signal. 0.13.0 = ACM-SIGNALS-01")
sub("async function handleRpc(msg) {", "async function handleRpc(msg, cx) {")
sub("  if (method === 'tools/call') { const name = params && params.name; if (!TOOLS.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`); const out = await callTool(name, (params && params.arguments) || {});",
    "  if (method === 'tools/call') { const name = params && params.name; if (!TOOLS.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`); const args = (params && params.arguments) || {}; const out = await callTool(name, args);\n"
    "    if (cx && !cx.internal && (name === 'resolve_issuer' || name === 'get_signal') && out && typeof out === 'object') { const did = decisionId(); out.receipt = receiptLinks(did); cx.decisions.push({ id: did, name, args, out, at: new Date().toISOString() }); }")
RECEIPT = r'''
// ---- RCO-A-01 (2026-10-24): the receipt of a decision the resolver cleared (plan v1.1 §2.6)
async function receiptFor(d, host) {
  const { id, name, args, out } = d; const ident = String(args.identifier || '').trim(); const w = whichNode(ident);
  const type = /^\d{8}$|^\d{12,14}$/.test(ident) ? 'gtin' : ({ isin: 'isin', lei: 'lei', cmr: 'cmr', ticker: 'ticker' }[w.kind] || 'identifier');
  let signal, rule; const records = [];
  if (name === 'get_signal') {
    signal = out.signal; rule = { id: 'ACM-68000 issuer states — getissuer get_signal', version: SERVER_VERSION };
    if (out.record) records.push({ url: out.record, as_of: out.as_of || null, sha256: await sha256({ cmr: out.cmr, node: out.node, as_of: out.as_of, isin: out.isin, issuer: out.issuer }), signature: null });
    if (out.filing) records.push({ url: out.filing.url || ('https://mcp.issuerwire.ai/mcp#get_row:' + out.filing.issuerwire_row), as_of: out.filing.date || null, sha256: await sha256(out.filing),
      signature: out.filing.from === 'Issuerwire' ? { alg: 'EdDSA', kid: 'amn-2026-10', keyring: 'https://issuerwire.ai/.well-known/jwks.json', note: 'the row is signed by Issuerwire; the full signed row is served on x402' } : null });
  } else {
    const m = out.matches || []; signal = m.length ? 'ACM-200' : (out.unavailable && out.unavailable.length ? 'ACM-500' : 'ACM-404');
    rule = { id: 'getissuer resolve_issuer — the twelve registers (index only)', version: SERVER_VERSION + ' · index as_of ' + indexAsOf() };
    for (const x of m.slice(0, 6)) records.push({ url: x.record_url, as_of: x.as_of || null, sha256: await sha256(x), signature: null });
  }
  if (!records.length) records.push({ url: `https://${host}/nodes.json`, as_of: indexAsOf() || null, sha256: null, signature: null });
  return { decision_id: id, object: { type, id: ident.slice(0, 80) }, actor_class: 'ai-agent (MCP client)', rule, records_read: records.filter(r => r.url), signal, decided_at: d.at, issuing_door: `https://${host}/mcp` };
}
'''
sub("function rpcResult(id, result) {", RECEIPT.lstrip("\n") + "function rpcResult(id, result) {")
sub("  async fetch(request, env) {", "  async fetch(request, env, ctx) {")
sub("      const batch = Array.isArray(body); const outs = []; for (const m of (batch ? body : [body])) { const r = await handleRpc(m); if (r) outs.push(r); }",
    "      const cx = { internal: /^Allooloo /.test(request.headers.get('user-agent') || ''), decisions: [] };\n"
    "      const batch = Array.isArray(body); const outs = []; for (const m of (batch ? body : [body])) { const r = await handleRpc(m, cx); if (r) outs.push(r); }\n"
    "      if (cx.decisions.length && ctx) ctx.waitUntil(Promise.all(cx.decisions.map(async d => writeReceipt(env, await receiptFor(d, host)))));")
sub("      return json(batch ? outs : outs[0], 200, 'no-store', servedAsOf);",
    "      const resp = json(batch ? outs : outs[0], 200, 'no-store', servedAsOf); if (cx.decisions.length) { resp.headers.set('X-RCO-Decision-Id', cx.decisions.map(d => d.id).join(', ')); resp.headers.set('Access-Control-Expose-Headers', 'X-CMR-Node, X-CMR-As-Of, X-CMR-Source, X-CMR-Operator, X-CMR-Version, Mcp-Session-Id, X-RCO-Decision-Id'); }\n      return resp;")
sub("    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json'", "    if (p === '/.well-known/jwks.json') return json(RCO_JWKS, 200, 'public, max-age=3600');\n    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json'")
io.open(P, "w", encoding="utf-8", newline="").write(t); print("apex patched 0.14.0")
