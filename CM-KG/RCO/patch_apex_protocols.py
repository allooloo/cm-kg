r"""patch_apex_protocols.py — PROTOCOLS-A-01 (DAY ORDER 3, 2026-10-24): the resolver's two named paths for the MCP Registry. cm-kg-apex 0.15.0 -> 0.16.0.
  /eco/mcp      — io.github.allooloo/eco: get_eco(market) (the Electronic Compliance Object of a market, read from <cc>-eco.ai/eco.json), get_signal,
                  resolve_issuer, list_nodes — the ECO pages' resolver path.
  /signals/mcp  — io.github.allooloo/acm-signals: get_signal, list_signals (the seven ACM-68000 signals and their pages).
Same JSON-RPC handler, same meter (get_eco is a record read), same receipts. /mcp is unchanged. index.js.pre-protocols01-20261024 beside."""
import io, os, shutil
P = r"C:\ALLOOLOO\CM-KG\DOOR\apex\index.js"
if not os.path.exists(P + ".pre-protocols01-20261024"): shutil.copy2(P, P + ".pre-protocols01-20261024")
t = io.open(P, encoding="utf-8", newline="").read()
def sub(old, new, n=1):
    global t; assert t.count(old) == n, (old[:90], t.count(old)); t = t.replace(old, new)
sub("const SERVER_VERSION = '0.15.0';", "const SERVER_VERSION = '0.16.0';   // 0.16.0 = PROTOCOLS-A-01 (2026-10-24): /eco/mcp and /signals/mcp.")
sub("const PAID_TOOLS = ['resolve_issuer', 'get_signal', 'get_record', 'list_events_since', 'list_aliases'];", "const PAID_TOOLS = ['resolve_issuer', 'get_signal', 'get_record', 'list_events_since', 'list_aliases', 'get_eco'];")
sub("let INDEX = null, NODES = null;", r'''const ECO_MARKETS = ['ae','ar','at','au','be','br','ca','ch','cl','co','cr','cz','de','dk','do','ec','es','fi','fr','gr','gt','hk','id','ie','il','in','it','jp','kr','ma','mx','my','nl','no','pa','pe','ph','pl','pt','sa','se','sg','th','tr','uk','us','uy','vn','za'];
const EXTRA_TOOLS = [
  { name: 'get_eco', title: 'Get Electronic Compliance Object', annotations: { title: 'Get Electronic Compliance Object', readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true }, description: 'The Electronic Compliance Object of one market (49): regulator, exchanges and listings page, regulated-information store, disclosure deadlines, ad hoc regime, filing format, ISIN prefix, LEI, calendar, languages, halts page — each field with its source page, signed (kid allooloo-eco-2026-10) — and the node status.', inputSchema: { type: 'object', properties: { market: { type: 'string', description: 'two-letter market code (fr, uk, us, de, jp, …)' } }, required: ['market'] } },
  { name: 'list_signals', title: 'List ACM-68000 signals', annotations: { title: 'List ACM-68000 signals', readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true }, description: 'The seven ACM-68000 signals, what each means for a listed issuer, and the page of each (acm-<code>.ai).', inputSchema: { type: 'object', properties: {} } }];
const PROFILES = { '/eco/mcp': { name: 'allooloo-eco', tools: ['get_eco', 'get_signal', 'resolve_issuer', 'list_nodes'], instructions: 'Electronic Compliance Objects (Allooloo): get_eco(market) for the disclosure regime of one of 49 markets, each field sourced and signed; get_signal for the ACM-68000 state of a listed security; receipts on mcp.rco-a2a.ai.' },
  '/signals/mcp': { name: 'acm-signals', tools: ['get_signal', 'list_signals'], instructions: 'ACM-68000 signals for listed issuers (Allooloo): get_signal(identifier) answers ACM-200 TRADING, ACM-404 NOT ON THE REGISTER, ACM-451 READ THE FILING (named), ACM-300, ACM-000, ACM-500; ACM-403 HALTED is advisory. list_signals names the seven and their pages.' } };
let INDEX = null, NODES = null;''')
sub("async function callTool(name, args) {\n  args = args || {};", r'''async function callTool(name, args) {
  args = args || {};
  if (name === 'list_signals') return { protocol: 'ACM-68000', standard: 'https://acm-68000.org/', signals: [['000', 'NOT_APPLICABLE', 'NOT APPLICABLE'], ['200', 'ALLOW', 'TRADING'], ['300', 'CONDITIONAL', 'CONDITIONAL'], ['403', 'RESTRICT', 'HALTED (advisory)'], ['404', 'NOT_FOUND', 'NOT ON THE REGISTER'], ['451', 'ESCALATE', 'READ THE FILING'], ['500', 'SYSTEM_ERROR', 'SYSTEM ERROR']].map(([c, s, i]) => ({ code: 'ACM-' + c, state: s, listed_issuers: i, page: `https://acm-${c}.ai/` })), tool: 'get_signal' };
  if (name === 'get_eco') { const cc = String(args.market || '').toLowerCase().trim(); if (!ECO_MARKETS.includes(cc)) return { error: 'not_found', market: args.market, markets: ECO_MARKETS };
    try { const r = await fetch(`https://${cc}-eco.ai/eco.json`, { headers: { 'user-agent': 'Allooloo getissuer (get_eco)', accept: 'application/json' }, signal: AbortSignal.timeout(12000) }); const j = await r.json(); return { market: cc, page: `https://${cc}-eco.ai/`, ...j }; } catch (e) { return { error: 'unavailable', market: cc, page: `https://${cc}-eco.ai/` }; } }''')
sub("async function handleRpc(msg, cx) {", "async function handleRpc(msg, cx) {\n  const prof = cx && cx.profile ? PROFILES[cx.profile] : null; const ALL = TOOLS.concat(EXTRA_TOOLS); const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : TOOLS;")
sub("  if (method === 'tools/list') return rpcResult(id, { tools: TOOLS });", "  if (method === 'tools/list') return rpcResult(id, { tools: LIST });")
sub("if (!TOOLS.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`);", "if (!LIST.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`);")
sub("serverInfo: { name: 'capitalmarketsknowledgegraph', version: SERVER_VERSION }, instructions: 'Capital Markets Knowledge Graph apex",
    "serverInfo: { name: prof ? prof.name : 'capitalmarketsknowledgegraph', version: SERVER_VERSION }, instructions: prof ? prof.instructions : 'Capital Markets Knowledge Graph apex")
sub("    if (p === '/mcp') {", "    if (p === '/mcp' || PROFILES[p]) {")
sub("      const cx = { internal: INTERNAL.test(request.headers.get('user-agent') || ''), decisions: [] };", "      const cx = { internal: INTERNAL.test(request.headers.get('user-agent') || ''), decisions: [], profile: PROFILES[p] ? p : null };")
io.open(P, "w", encoding="utf-8", newline="").write(t); print("apex 0.16.0")
