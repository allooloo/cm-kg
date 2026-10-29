r"""patch_apex_x402.py — X402-A-01 (DAY ORDER 3, 2026-10-24): x402 on the resolver. cm-kg-apex 0.14.0 -> 0.15.0. Paid-eligible reads (tools/call
resolve_issuer · get_signal · get_record · list_events_since · list_aliases; GET /record · /events · /signal/{identifier}) pass free inside the
per-agent daily free tier; past it (or when the caller asks for the offer) the door answers HTTP 402 with the x402 v2 offer; a valid PAYMENT-SIGNATURE is
verified, the read is served, then settled; the answer carries PAYMENT-RESPONSE and its RCO receipt, and the receipt names the settlement transaction.
GET /signal/{identifier} is the REST twin of get_signal. mcp.json and /.well-known/mcp.json carry the payment door and the routing block. The internal
skip narrows to Allooloo's own renderers. KV X402 bound in wrangler.toml. index.js.pre-x402a01-20261024 beside. Usage: python -X utf8 -I patch_apex_x402.py"""
import io, os, shutil
P = r"C:\ALLOOLOO\CM-KG\DOOR\apex\index.js"; W = r"C:\ALLOOLOO\CM-KG\DOOR\apex\wrangler.toml"
for f in (P, W):
    if not os.path.exists(f + ".pre-x402a01-20261024"): shutil.copy2(f, f + ".pre-x402a01-20261024")
t = io.open(P, encoding="utf-8", newline="").read()
def sub(old, new, n=1):
    global t; assert t.count(old) == n, (old[:90], t.count(old)); t = t.replace(old, new)
sub("import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';",
    "import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';\nimport { decide, settle, paymentDoor, PRICING } from './x402gate.js';\nconst INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer)/;   // Allooloo's own renderers: no receipt, no meter\nconst PAID_TOOLS = ['resolve_issuer', 'get_signal', 'get_record', 'list_events_since', 'list_aliases'];\nconst ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: 'https://mcp.getissuer.ai/mcp' }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-a2a.ai/mcp' }];")
sub("const SERVER_VERSION = '0.14.0';   // 0.14.0 = RCO-A-01", "const SERVER_VERSION = '0.15.0';   // 0.15.0 = X402-A-01 (2026-10-24): x402 v2, free tier per agent per day, paid reads carry their receipt. 0.14.0 = RCO-A-01")
# receipts carry the settlement
sub("  return { decision_id: id, object: { type, id: ident.slice(0, 80) }, actor_class: 'ai-agent (MCP client)', rule, records_read: records.filter(r => r.url), signal, decided_at: d.at, issuing_door: `https://${host}/mcp` };",
    "  const body = { decision_id: id, object: { type, id: ident.slice(0, 80) }, actor_class: d.actor || 'ai-agent (MCP client)', rule, records_read: records.filter(r => r.url), signal, decided_at: d.at, issuing_door: `https://${host}/mcp` };\n  if (d.settlement) body.settlement = d.settlement;   // X402-A-01: a paid read's receipt names its settlement (network and transaction, never an amount)\n  return body;")
sub("      const cx = { internal: /^Allooloo /.test(request.headers.get('user-agent') || ''), decisions: [] };",
    "      const cx = { internal: INTERNAL.test(request.headers.get('user-agent') || ''), decisions: [] };\n"
    "      const units = cx.internal ? 0 : (Array.isArray(body) ? body : [body]).filter(m => m && m.method === 'tools/call' && m.params && PAID_TOOLS.includes(m.params.name)).length;\n"
    "      const g = units ? await decide(request, env, { door: 'getissuer', resource: `https://${host}/mcp`, description: 'One record read on getissuer, the listed-issuer resolver (Allooloo Technologies Corp.)', units }) : { pass: true, free: true };\n"
    "      if (g.response) return g.response;")
sub("      if (cx.decisions.length && ctx) ctx.waitUntil(Promise.all(cx.decisions.map(async d => writeReceipt(env, await receiptFor(d, host)))));",
    "      let pay = null; if (g.paid) { pay = await settle(env, g.paid, 'getissuer'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } }); for (const d of cx.decisions) d.settlement = { network: pay.pr.network, transaction: pay.tx }; }\n"
    "      if (cx.decisions.length && ctx) ctx.waitUntil(Promise.all(cx.decisions.map(async d => writeReceipt(env, await receiptFor(d, host)))));")
sub("      const resp = json(batch ? outs : outs[0], 200, 'no-store', servedAsOf); if (cx.decisions.length) {",
    "      const resp = json(batch ? outs : outs[0], 200, 'no-store', servedAsOf); if (pay) { resp.headers.set('PAYMENT-RESPONSE', pay.header); resp.headers.set('X-PAYMENT-RESPONSE', pay.header); } if (cx.decisions.length) {")
sub("Mcp-Session-Id, X-RCO-Decision-Id'); }", "Mcp-Session-Id, X-RCO-Decision-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, PAYMENT-REQUIRED'); }")
# GET paid reads: /record, /events, /signal/{id}
sub("    let m = p.match(/^\\/(record|events)\\/([a-z]{2}-cm-kg)\\/([A-Z\\-]+)\\/(.+)$/i);",
    """    const sg = p.match(/^\\/signal\\/([^/]+)$/);
    if (sg || /^\\/(record|events)\\//.test(p)) {
      const internal = INTERNAL.test(request.headers.get('user-agent') || '');
      const g = internal ? { pass: true, free: true } : await decide(request, env, { door: 'getissuer', resource: `https://${host}${p}`, description: 'One record read on getissuer, the listed-issuer resolver (Allooloo Technologies Corp.)' });
      if (g.response) return g.response;
      if (sg) {
        const ident = decodeURIComponent(sg[1]); const out = await getSignal(ident); let pay = null;
        if (g.paid) { pay = await settle(env, g.paid, 'getissuer'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } }); }
        let did = null; if (!internal) { did = decisionId(); out.receipt = receiptLinks(did); const d = { id: did, name: 'get_signal', args: { identifier: ident }, out, at: new Date().toISOString(), actor: 'api-client (HTTP GET)', settlement: pay ? { network: pay.pr.network, transaction: pay.tx } : undefined }; if (ctx) ctx.waitUntil((async () => writeReceipt(env, await receiptFor(d, host)))()); }
        if (pay) out.settlement = { network: pay.pr.network, transaction: pay.tx, payer: pay.payer };
        const resp = json(out, 200, 'no-store', out.as_of || ''); if (did) resp.headers.set('X-RCO-Decision-Id', did); if (pay) { resp.headers.set('PAYMENT-RESPONSE', pay.header); resp.headers.set('X-PAYMENT-RESPONSE', pay.header); }
        resp.headers.set('Access-Control-Expose-Headers', 'X-RCO-Decision-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, PAYMENT-REQUIRED'); return resp;
      }
      if (g.paid) { const pay = await settle(env, g.paid, 'getissuer'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed' }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header } }); request.__pay = pay; }
    }
    let m = p.match(/^\\/(record|events)\\/([a-z]{2}-cm-kg)\\/([A-Z\\-]+)\\/(.+)$/i);""")
sub("    if (p === '/mcp.json') return json(mcpJson(host), 200, 'public, max-age=300');",
    "    if (p === '/mcp.json' || p === '/.well-known/mcp.json') return json({ ...mcpJson(host), payment: paymentDoor(env), routing: ROUTING, receipts: { door: 'https://mcp.rco-a2a.ai/mcp', keyring: 'https://mcp.getissuer.ai/.well-known/jwks.json', note: 'every resolve_issuer and get_signal leaves an RCO receipt; the answer carries its decision_id' } }, 200, 'public, max-age=300');\n"
    "    if (p === '/x402/pricing.json') return json({ ...PRICING, door: `https://${host}/mcp`, payment: paymentDoor(env) }, 200, 'public, max-age=300');")
io.open(P, "w", encoding="utf-8", newline="").write(t)
w = io.open(W, encoding="utf-8", newline="").read()
if "X402" not in w: w = w.rstrip("\n") + '\n\n# X402-A-01 (2026-10-24): the shared x402 register (free-tier meters, counts of settlements and offers)\n[[kv_namespaces]]\nbinding = "X402"\nid = "dd183811c9b34c4db1a91029f5343fde"\n'
io.open(W, "w", encoding="utf-8", newline="").write(w); print("apex 0.15.0")
