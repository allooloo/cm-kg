r"""patch_gate.py — ASOF-01: get_as_of on the node gate (CM-KG\NODE-GATE\worker\index.js; index.pre-asof01-2026-11-05.js beside). Idempotent: refuses on a
second run (the import is already there). Usage: python -X utf8 -I patch_gate.py"""
import pathlib, shutil
D = pathlib.Path(r'C:\ALLOOLOO\CM-KG\NODE-GATE\worker'); p = D / 'index.js'; pre = D / 'index.pre-asof01-2026-11-05.js'
if not pre.exists(): shutil.copy2(p, pre)
s = p.read_text(encoding='utf-8')
if "from './asof.js'" in s: raise SystemExit('already patched')
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:80]); s = s.replace(o, n)
rep("import { TM_NAMES, TM_READS, TM_TOOLS, TM_JWK_PUBLIC, tmCall, tmSkills } from './tm.js';   // TMKT-02: the Target Market door (read and file) on every node door",
    "import { TM_NAMES, TM_READS, TM_TOOLS, TM_JWK_PUBLIC, tmCall, tmSkills } from './tm.js';   // TMKT-02: the Target Market door (read and file) on every node door\n"
    "import { ASOF_NAME, ASOF_TOOL, getAsOf, asofLine, asofLlms, asofSkill, ASOF_PAGE, ASOF_MCP } from './asof.js';   // ASOF-01: get_as_of, the point-in-time door, on every node door")
rep("const VERSION = '2026-11-02.4';",
    "const VERSION = '2026-11-05.1';   // .1 = ASOF-01: get_as_of answered here (the sealed vintage via the door's own get_record as_of; signed kid allooloo-cmr-2026-10; receipted with the node as writer); on tools/list, the card, the page, llms.txt, facts.json, mcp.json; was 2026-11-02.4\n"
    "const VERSION_PRIOR_ASOF01 = '2026-11-02.4';")
rep("  return new Response(JSON.stringify({ ...c, skills, target_market: { door: `${door}/mcp`, tools: TM_NAMES, page: 'https://gettargetmarket.ai/', router: 'https://mcp.gettargetmarket.ai/mcp (routes by subject to the home node)' } }), { status: resp.status, headers: h });",
    "  const sk2 = skills.filter(s => s && s.id !== ASOF_NAME).concat([asofSkill(door)]);   // ASOF-01\n"
    "  return new Response(JSON.stringify({ ...c, skills: sk2, target_market: { door: `${door}/mcp`, tools: TM_NAMES, page: 'https://gettargetmarket.ai/', router: 'https://mcp.gettargetmarket.ai/mcp (routes by subject to the home node)' }, as_of: { door: `${door}/mcp`, tool: ASOF_NAME, page: ASOF_PAGE, router: `${ASOF_MCP} (routes by issuer to the owning node)` } }), { status: resp.status, headers: h });")
rep("j.target_market = { door: `${door}/mcp`, tools: TM_NAMES, page: 'https://gettargetmarket.ai/', store: \"this node's own pond, container target-market (tm/<subject>/v<N>.json)\" }; t = JSON.stringify(j); } catch (e) {} }",
    "j.target_market = { door: `${door}/mcp`, tools: TM_NAMES, page: 'https://gettargetmarket.ai/', store: \"this node's own pond, container target-market (tm/<subject>/v<N>.json)\" }; if (Array.isArray(j.tools) && !j.tools.includes(ASOF_NAME)) j.tools.push(ASOF_NAME); j.as_of = { door: `${door}/mcp`, tool: ASOF_NAME, page: ASOF_PAGE, store: \"the node's sealed vintage (backfill/replay/<year>/), read through get_record as_of\" }; t = JSON.stringify(j); } catch (e) {} }   // ASOF-01")
rep("signed by the node and receipted at mcp.rco-records.ai (<a href=\"https://gettargetmarket.ai/\">gettargetmarket.ai</a>).</p>`);",
    "signed by the node and receipted at mcp.rco-records.ai (<a href=\"https://gettargetmarket.ai/\">gettargetmarket.ai</a>).</p>${asofLine(door)}`);   // ASOF-01: the As Of line after the Target Market line")
rep("(the manufacturer's target market statement for a product listed on this node: read, list, verify, file — https://gettargetmarket.ai/)`);",
    "(the manufacturer's target market statement for a product listed on this node: read, list, verify, file — https://gettargetmarket.ai/), ${asofLlms()}`);   // ASOF-01")
rep("const tmDescTools = tools => Array.isArray(tools) ? tools.concat(TM_TOOLS.filter(t => !tools.find(x => x && x.name === t.name)).map(t => ({ name: t.name, description: t.description }))) : tools;",
    "const tmDescTools = tools => Array.isArray(tools) ? tools.concat(TM_TOOLS.concat([ASOF_TOOL]).filter(t => !tools.find(x => x && x.name === t.name)).map(t => ({ name: t.name, description: t.description }))) : tools;   // ASOF-01: + get_as_of")
BLOCK = r"""    // ASOF-01: get_as_of is answered by the gate (the door's own get_record as_of, the node's record key, the receipt writer); free for every agent, the signed
    // HTTP 402 offer only when asked (x402-pay: 1) or paid (R-039, as get_orderability); a call routed by the router was metered there and names its settlement
    const asofCalls = list.filter(x => x && x.method === 'tools/call' && x.params && x.params.name === ASOF_NAME);
    if (asofCalls.length) {
      let asPay = null, asSettle = null; const asRouted = /^getissuer apex \(get_as_of route\)/.test(request.headers.get('user-agent') || '');
      if (asRouted) { try { asSettle = JSON.parse(request.headers.get('x-asof-settlement') || 'null'); } catch (e) { asSettle = null; } }
      if (!internal && !asRouted && (request.headers.get('x402-pay') === '1' || request.headers.get('payment-signature') || request.headers.get('x-payment'))) {
        const g = await decide(request, env, { door: node, resource: `https://${url.hostname}/mcp`, description: `One as-of record read on the ${node} node door (Allooloo Technologies Corp.)`, units: asofCalls.length });
        if (g.response) return signOffer(env, node, g.response);
        if (g.paid) { asPay = await settle(env, g.paid, node); if (!asPay.settled) return settleFail(asPay); asSettle = { network: asPay.pr.network, transaction: asPay.tx, payer: asPay.payer }; }
      }
      const rest = list.filter(x => !asofCalls.includes(x));
      const mine = await Promise.all(asofCalls.map(async x => { const r = await getAsOf(env, ctx, { node, host: url.hostname, door: RDOOR, callerKey: request.headers.get('rco-key') || undefined, payer: asSettle ? asSettle.payer : undefined, settlement: asSettle ? { network: asSettle.network, transaction: asSettle.transaction } : undefined }, (x.params && x.params.arguments) || {}); return { m: { jsonrpc: '2.0', id: x.id, result: { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: !!r.err } }, rid: r.receipt_id }; }));
      let others = [];
      if (rest.length) { const r2 = await fetch(new Request(request, { body: JSON.stringify(Array.isArray(msg) ? rest : rest[0]) })); try { const j2 = await r2.json(); others = Array.isArray(j2) ? j2 : [j2]; } catch (e) { others = []; } }
      const all = mine.map(x => x.m).concat(others);
      return withPay(new Response(JSON.stringify(Array.isArray(msg) ? all : all[0]), { status: 200, headers: { 'content-type': 'application/json', 'cache-control': 'no-store', 'access-control-allow-origin': '*', 'X-Node-Gate': VERSION,
        'X-RCO-Receipt-Id': mine.map(x => x.rid).filter(Boolean).join(', '), 'access-control-expose-headers': 'X-RCO-Receipt-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' } }), asPay);
    }
    // AIO-01: get_orderability is answered by the gate"""
rep("    // AIO-01: get_orderability is answered by the gate", BLOCK)
rep("      if (j0 && j0.result && Array.isArray(j0.result.tools)) for (const tt of TM_TOOLS) if (!j0.result.tools.find(t => t.name === tt.name)) j0.result.tools.push(tt);   // TMKT-02",
    "      if (j0 && j0.result && Array.isArray(j0.result.tools)) for (const tt of TM_TOOLS) if (!j0.result.tools.find(t => t.name === tt.name)) j0.result.tools.push(tt);   // TMKT-02\n"
    "      if (j0 && j0.result && Array.isArray(j0.result.tools) && !j0.result.tools.find(t => t.name === ASOF_NAME)) j0.result.tools.push(ASOF_TOOL);   // ASOF-01")
p.write_text(s, encoding='utf-8'); print('patched', p)
