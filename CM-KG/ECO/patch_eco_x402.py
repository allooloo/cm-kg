r"""patch_eco_x402.py — X402-A-01 (DAY ORDER 3, 2026-10-24) on eco-pages: the ECO records (/eco.json, /isin/, /ticker/) are free inside the per-agent
daily free tier and answer the x402 v2 offer past it; a paid read is verified, served, settled, and its RCO receipt names the settlement. The ECO
/.well-known/mcp.json carries the payment door and the routing block. allooloo.ai/x402 (page), /x402/settled.json and /x402/pricing.json publish the
settlement counts of every Allooloo door — counts only, never amounts. index.js.pre-x402a01-20261024 beside. Usage: python -X utf8 -I patch_eco_x402.py"""
import io, os, shutil
P = r"C:\ALLOOLOO\CM-KG\ECO\worker\index.js"; W = r"C:\ALLOOLOO\CM-KG\ECO\wrangler.toml"
for f in (P, W):
    if not os.path.exists(f + ".pre-x402a01-20261024"): shutil.copy2(f, f + ".pre-x402a01-20261024")
t = io.open(P, encoding="utf-8", newline="").read()
def sub(old, new, n=1):
    global t; assert t.count(old) == n, (old[:90], t.count(old)); t = t.replace(old, new)
sub("import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';",
    "import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';\nimport { decide, settle, paymentDoor, counts, PRICING } from './x402gate.js';   // X402-A-01\nconst INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer)/;\nconst ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: 'https://mcp.getissuer.ai/mcp' }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-a2a.ai/mcp' }];")
sub("const VERSION = '2026-10-24.2';", "const VERSION = '2026-10-24.3';")
X402PAGE = r'''
// ---- X402-A-01: allooloo.ai/x402 — settlement counts of the Allooloo doors (counts only, never amounts)
async function x402(url, env) {
  const c = await counts(env, 14);
  if (url.pathname === '/x402/settled.json') return J(c, 200, 'no-store');
  if (url.pathname === '/x402/pricing.json') return J({ ...PRICING, payment: paymentDoor(env), doors: ['https://mcp.getissuer.ai/mcp', 'https://mcp.<cc>-cm-kg.ai/mcp (twelve)', 'https://<cc>-eco.ai/eco.json · /isin/ · /ticker/', 'https://mcp.rco-a2a.ai/mcp (write_receipt without a key)'] }, 200, 'public, max-age=300');
  const today = new Date().toISOString().slice(0, 10), days = Object.keys({ ...c.by_day, ...c.free_by_day, ...c.offers_by_day }).sort().reverse();
  const body = `<div class="topbar">${OPERATOR} · x402 on the Allooloo doors</div><p class="eyebrow">allooloo.ai/x402</p>
<h1>Settled reads<span class="host">allooloo.ai/x402</span></h1><div class="badge">${int(c.settled)} SETTLED · ${int(c.by_day[today] || 0)} TODAY</div>
<p class="subtitle">An agent pays an agent for a record — no procurement desk. Every record read on the resolver, the twelve node doors and the Electronic Compliance Objects is free for the first ${paymentDoor(env).free_reads_per_agent_per_day} reads an agent makes in a day, then settles over x402 on Base. A paid read carries its RCO receipt.</p>
<p class="meta">Counts only, read live from the register at render. Machine form: <a href="/x402/settled.json">/x402/settled.json</a> · terms: <a href="/x402/pricing.json">/x402/pricing.json</a>.</p>
<table><thead><tr><th>Day (UTC)</th><th>Settled</th><th>Free-tier reads</th><th>Offers (402)</th></tr></thead><tbody>
${days.map(d => `<tr><td>${d}</td><td>${int(c.by_day[d] || 0)}</td><td>${int(c.free_by_day[d] || 0)}</td><td>${int(c.offers_by_day[d] || 0)}</td></tr>`).join('') || '<tr><td colspan="4">no reads on the register yet</td></tr>'}
</tbody></table>
<h2>By door</h2><table><thead><tr><th>Door</th><th>Settled</th></tr></thead><tbody>${Object.entries(c.by_door).map(([d, n]) => `<tr><td>${esc(d)}</td><td>${int(n)}</td></tr>`).join('') || '<tr><td colspan="2">none yet</td></tr>'}</tbody></table>`;
  return HT(shell('x402 · settled reads', `${c.settled} settled reads on the Allooloo doors (counts only).`, body, 'allooloo.ai'));
}
'''
sub("export default {", X402PAGE.lstrip("\n") + "export default {")
sub("    if (host === 'allooloo.ai') return (url.pathname === '/markets' || url.pathname === '/markets/' || url.pathname === '/markets.json') ? markets(url) : R301('https://allooloo.io' + url.pathname + url.search);",
    "    if (host === 'allooloo.ai' && (url.pathname === '/x402' || url.pathname === '/x402/' || url.pathname.startsWith('/x402/'))) return x402(url, env);\n"
    "    if (host === 'allooloo.ai') return (url.pathname === '/markets' || url.pathname === '/markets/' || url.pathname === '/markets.json') ? markets(url) : R301('https://allooloo.io' + url.pathname + url.search);")
# meter the ECO record reads
sub("    const p = url.pathname, m = MARKETS[cc].record, live = LIVE.includes(cc);",
    "    const p = url.pathname, m = MARKETS[cc].record, live = LIVE.includes(cc);\n"
    "    const metered = p === '/eco.json' || /^\\/(isin|ticker)\\//.test(p); const internal = INTERNAL.test(request.headers.get('user-agent') || '');\n"
    "    const g = metered && !internal ? await decide(request, env, { door: 'eco', resource: `https://${host}${p}`, description: `One Electronic Compliance Object read on ${host} (Allooloo Technologies Corp.)` }) : { pass: true };\n"
    "    if (g.response) return g.response;\n"
    "    const pay = g.paid ? await settle(env, g.paid, 'eco') : null; if (pay && !pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } });\n"
    "    const paid = r => { if (!pay) return r; const h = new Headers(r.headers); h.set('PAYMENT-RESPONSE', pay.header); h.set('X-PAYMENT-RESPONSE', pay.header); h.set('cache-control', 'no-store'); h.set('access-control-expose-headers', 'PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, PAYMENT-REQUIRED'); return new Response(r.body, { status: r.status, headers: h }); };")
sub("    if (p === '/eco.json') { const st = status(cc, (await nodes())[cc]); return J({ ...MARKETS[cc], node_status: st, build: BUILT }); }",
    "    if (p === '/eco.json') { const st = status(cc, (await nodes())[cc]); return paid(J({ ...MARKETS[cc], node_status: st, build: BUILT, ...(pay ? { settlement: { network: pay.pr.network, transaction: pay.tx } } : {}) }, 200, pay ? 'no-store' : undefined)); }")
sub("ctx.waitUntil(writeReceipt(env, { decision_id: did, object:", "ctx.waitUntil(writeReceipt(env, { ...(pay ? { settlement: { network: pay.pr.network, transaction: pay.tx } } : {}), decision_id: did, object:")
sub("      return J(o, st, 'no-store');\n    }", "      if (pay) o.settlement = { network: pay.pr.network, transaction: pay.tx, payer: pay.payer };\n      return paid(J(o, st, 'no-store'));\n    }")
sub("    if (p === '/.well-known/mcp.json') return J({ mcp_server: live ? `https://mcp.${cc}-cm-kg.ai/mcp` : APEX, apex: APEX, transport: 'streamable-http', auth: 'none for reads', tools_of_note: ['resolve_issuer', 'list_nodes'], operator: OPERATOR });",
    "    if (p === '/.well-known/mcp.json') return J({ mcp_server: live ? `https://mcp.${cc}-cm-kg.ai/mcp` : APEX, apex: APEX, resolver: 'https://mcp.getissuer.ai/mcp', transport: 'streamable-http', auth: 'none for reads', tools_of_note: ['resolve_issuer', 'get_signal', 'list_nodes'], operator: OPERATOR, routing: ROUTING, payment: paymentDoor(env), receipts: { door: 'https://mcp.rco-a2a.ai/mcp', note: 'an ECO lookup that returns a signal leaves an RCO receipt; the answer carries its decision_id' } });")
io.open(P, "w", encoding="utf-8", newline="").write(t)
w = io.open(W, encoding="utf-8", newline="").read()
if "X402" not in w: w = w.rstrip("\n") + '\n\n# X402-A-01 (2026-10-24): the shared x402 register\n[[kv_namespaces]]\nbinding = "X402"\nid = "dd183811c9b34c4db1a91029f5343fde"\n\n[vars]\nX402_FREE_PER_DAY = "100"\n'
io.open(W, "w", encoding="utf-8", newline="").write(w); print("eco x402")
