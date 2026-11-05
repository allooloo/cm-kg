r"""patch_gate.py — DOORS-01: get_filings · get_ticker · get_auditor on the node gate (CM-KG\NODE-GATE\worker\index.js; index.pre-doors01-2026-11-05.js beside).
Idempotent: refuses on a second run. Usage: python -X utf8 -I patch_gate.py"""
import pathlib, shutil
D = pathlib.Path(r'C:\ALLOOLOO\CM-KG\NODE-GATE\worker'); p = D / 'index.js'; pre = D / 'index.pre-doors01-2026-11-05.js'
if not pre.exists(): shutil.copy2(p, pre)
s = p.read_text(encoding='utf-8')
if "from './doors.js'" in s: raise SystemExit('already patched')
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:80]); s = s.replace(o, n)
rep("import { ASOF_NAME, ASOF_TOOL, getAsOf, asofLine, asofLlms, asofSkill, ASOF_PAGE, ASOF_MCP } from './asof.js';",
    "import { ASOF_NAME, ASOF_TOOL, getAsOf, asofLine, asofLlms, asofSkill, ASOF_PAGE, ASOF_MCP } from './asof.js';\n"
    "import { DOORS, DOOR_NAMES, DOOR_TOOLS, doorCall, doorsLine, doorsLlms, doorsSkills } from './doors.js';   // DOORS-01: get_filings · get_ticker · get_auditor on every node door")
rep("const VERSION = '2026-11-05.1';", "const VERSION = '2026-11-05.2';   // .2 = DOORS-01: get_filings · get_ticker · get_auditor answered here (fields already on the record; signed; receipted with the node as writer); was 2026-11-05.1\nconst VERSION_PRIOR_DOORS01 = '2026-11-05.1';")
rep("  const sk2 = skills.filter(s => s && s.id !== ASOF_NAME).concat([asofSkill(door)]);   // ASOF-01",
    "  const sk2 = skills.filter(s => s && s.id !== ASOF_NAME && !DOOR_NAMES.includes(s.id)).concat([asofSkill(door)], doorsSkills(door));   // ASOF-01 · DOORS-01")
rep("if (Array.isArray(j.tools) && !j.tools.includes(ASOF_NAME)) j.tools.push(ASOF_NAME);",
    "if (Array.isArray(j.tools) && !j.tools.includes(ASOF_NAME)) j.tools.push(ASOF_NAME); if (Array.isArray(j.tools)) for (const n of DOOR_NAMES) if (!j.tools.includes(n)) j.tools.push(n);")
rep("</p>${asofLine(door)}`);   // ASOF-01: the As Of line after the Target Market line", "</p>${asofLine(door)}${doorsLine(door)}`);   // ASOF-01: the As Of line after the Target Market line · DOORS-01: the three door lines")
rep(", ${asofLlms()}`);   // ASOF-01", ", ${asofLlms()}, ${doorsLlms()}`);   // ASOF-01 · DOORS-01")
rep("tools.concat(TM_TOOLS.concat([ASOF_TOOL]).filter(", "tools.concat(TM_TOOLS.concat([ASOF_TOOL], DOOR_TOOLS).filter(")
BLOCK = r"""    // DOORS-01: get_filings · get_ticker · get_auditor are answered by the gate (the door's own reads of the record, the node's record key, the receipt writer); free for
    // every agent, the signed HTTP 402 offer only when asked (x402-pay: 1) or paid; a call routed by the router was metered there and names its settlement
    const dCalls = list.filter(x => x && x.method === 'tools/call' && x.params && DOOR_NAMES.includes(x.params.name));
    if (dCalls.length) {
      let dPay = null, dSettle = null; const dRouted = /^getissuer apex \(doors route\)/.test(request.headers.get('user-agent') || '');
      if (dRouted) { try { dSettle = JSON.parse(request.headers.get('x-door-settlement') || 'null'); } catch (e) { dSettle = null; } }
      if (!internal && !dRouted && (request.headers.get('x402-pay') === '1' || request.headers.get('payment-signature') || request.headers.get('x-payment'))) {
        const g = await decide(request, env, { door: node, resource: `https://${url.hostname}/mcp`, description: `One record read on the ${node} node door (Allooloo Technologies Corp.)`, units: dCalls.length });
        if (g.response) return signOffer(env, node, g.response);
        if (g.paid) { dPay = await settle(env, g.paid, node); if (!dPay.settled) return settleFail(dPay); dSettle = { network: dPay.pr.network, transaction: dPay.tx, payer: dPay.payer }; }
      }
      const rest = list.filter(x => !dCalls.includes(x));
      const mine = await Promise.all(dCalls.map(async x => { const r = await doorCall(env, ctx, { node, host: url.hostname, door: RDOOR, callerKey: request.headers.get('rco-key') || undefined, payer: dSettle ? dSettle.payer : undefined, settlement: dSettle ? { network: dSettle.network, transaction: dSettle.transaction } : undefined }, x.params.name, (x.params && x.params.arguments) || {}); return { m: { jsonrpc: '2.0', id: x.id, result: { content: [{ type: 'text', text: JSON.stringify(r.o) }], structuredContent: r.o, isError: !!r.err } }, rid: r.receipt_id }; }));
      let others = [];
      if (rest.length) { const r2 = await fetch(new Request(request, { body: JSON.stringify(Array.isArray(msg) ? rest : rest[0]) })); try { const j2 = await r2.json(); others = Array.isArray(j2) ? j2 : [j2]; } catch (e) { others = []; } }
      const all = mine.map(x => x.m).concat(others);
      return withPay(new Response(JSON.stringify(Array.isArray(msg) ? all : all[0]), { status: 200, headers: { 'content-type': 'application/json', 'cache-control': 'no-store', 'access-control-allow-origin': '*', 'X-Node-Gate': VERSION,
        'X-RCO-Receipt-Id': mine.map(x => x.rid).filter(Boolean).join(', '), 'access-control-expose-headers': 'X-RCO-Receipt-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE' } }), dPay);
    }
    // ASOF-01: get_as_of is answered by the gate"""
rep("    // ASOF-01: get_as_of is answered by the gate", BLOCK)
rep("      if (j0 && j0.result && Array.isArray(j0.result.tools) && !j0.result.tools.find(t => t.name === ASOF_NAME)) j0.result.tools.push(ASOF_TOOL);   // ASOF-01",
    "      if (j0 && j0.result && Array.isArray(j0.result.tools) && !j0.result.tools.find(t => t.name === ASOF_NAME)) j0.result.tools.push(ASOF_TOOL);   // ASOF-01\n"
    "      if (j0 && j0.result && Array.isArray(j0.result.tools)) for (const tt of DOOR_TOOLS) if (!j0.result.tools.find(t => t.name === tt.name)) j0.result.tools.push(tt);   // DOORS-01")
p.write_text(s, encoding='utf-8'); print('patched', p)
