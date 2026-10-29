r"""patch_eco_protocols.py — PROTOCOLS-A-01 (DAY ORDER 3, 2026-10-24) on eco-pages: the consolidated allooloo.ai/.well-known set and allooloo.ai/llms.txt —
every Allooloo door in one place, typed by what it resolves: the resolver (getissuer, with its /eco/mcp and /signals/mcp paths), the twelve node doors,
Issuerwire, the ECO pages, the seven signal pages, the receipt door; the routing block; the x402 payment door; the keyring (receipts kid allooloo-rco-2026-10,
ECO records kid allooloo-eco-2026-10). The ECO agent cards point at the resolver. The resolver's get_eco read passes unmetered (it meters itself).
index.js.pre-protocols01-20261024 beside. Usage: python -X utf8 -I patch_eco_protocols.py"""
import io, os, shutil, json
P = r"C:\ALLOOLOO\CM-KG\ECO\worker\index.js"
if not os.path.exists(P + ".pre-protocols01-20261024"): shutil.copy2(P, P + ".pre-protocols01-20261024")
t = io.open(P, encoding="utf-8", newline="").read()
def sub(old, new, n=1):
    global t; assert t.count(old) == n, (old[:90], t.count(old)); t = t.replace(old, new)
PUB = json.load(open(r"C:\ALLOOLOO\CM-KG\RCO\rco-signing.pub.jwk.json", encoding="utf-8"))
sub("const INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer)/;", "const INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer|getissuer)/;")
sub("const VERSION = '2026-10-24.3';", "const VERSION = '2026-10-24.4';")
WK = r'''
// ---- PROTOCOLS-A-01: allooloo.ai/.well-known — the doors of Allooloo Technologies Corp., one set
const RCO_PUB = __PUB__;
const NODE_CC = ['ca', 'uk', 'us', 'de', 'fr', 'nl', 'ch', 'au', 'sg', 'jp', 'kr', 'hk'];
const DOORS = () => [
  { id: 'getissuer', resolves: 'listed issuers (ticker, ISIN, LEI) and the ACM-68000 signal', mcp: 'https://mcp.getissuer.ai/mcp', card: 'https://agent.getissuer.ai/.well-known/agent-card.json', registry: 'io.github.allooloo/cm-kg' },
  { id: 'eco', resolves: 'the Electronic Compliance Object of a market (49)', mcp: 'https://mcp.getissuer.ai/eco/mcp', pages: INDEX, registry: 'io.github.allooloo/eco' },
  { id: 'acm-signals', resolves: 'the seven ACM-68000 signals for listed issuers', mcp: 'https://mcp.getissuer.ai/signals/mcp', pages: ['000', '200', '300', '403', '404', '451', '500'].map(c => `https://acm-${c}.ai/`), registry: 'io.github.allooloo/acm-signals' },
  ...NODE_CC.map(c => ({ id: `${c}-cm-kg`, resolves: `listed issuers of one market, served in-country (${c})`, mcp: `https://mcp.${c}-cm-kg.ai/mcp`, card: `https://agent.${c}-cm-kg.ai/.well-known/agent-card.json` })),
  { id: 'issuerwire', resolves: 'filings and releases since your last read (twelve markets)', mcp: 'https://mcp.issuerwire.ai/mcp', card: 'https://issuerwire.ai/.well-known/agent-card.json', registry: 'io.github.allooloo/issuerwire' },
  { id: 'receipts', resolves: 'receipts — the Record of Cleared Orders (Allooloo doors write; anyone reads)', mcp: 'https://mcp.rco-a2a.ai/mcp', operator: 'Agentic KG Holdings (the standard); Allooloo writes' }];
async function wellKnown(url, env) {
  const p = url.pathname, me = 'https://allooloo.ai';
  const routing = ROUTING, payment = paymentDoor(env), doors = DOORS();
  if (p === '/llms.txt') return T(`# allooloo.ai — Allooloo Technologies Corp.\n\nDoors by what they resolve:\n${routing.map(r => `- ${r.what} → ${r.door}`).join('\n')}\n\nWhere agents read the market: one sourced, read-dated record for every listed company, served in the issuer's own jurisdiction, over MCP and A2A.\n\n## The doors\n${doors.map(d => `- ${d.id}: ${d.resolves} — ${d.mcp}`).join('\n')}\n\n## Pages\n- Electronic Compliance Objects, 49 markets: ${INDEX}\n- The seven signal pages: https://acm-000.ai/ … https://acm-500.ai/\n- Settled reads (counts only): ${me}/x402\n\n## Terms\n- Reads are free for the first ${payment.free_reads_per_agent_per_day} per agent per day, then x402 on Base (USDC): ${me}/x402/pricing.json\n- Every resolve and signal leaves an RCO receipt (decision_id in the answer), readable by anyone at https://mcp.rco-a2a.ai/mcp\n- Keyring: ${me}/.well-known/jwks.json\n\nMachine set: ${me}/.well-known/mcp.json · agent-card.json · api-catalog · ai-catalog.json · jwks.json · security.txt\nOperator: Allooloo Technologies Corp. · mk@allooloo.ai · https://allooloo.io\n`);
  if (p === '/.well-known/mcp.json') return J({ name: 'allooloo', title: 'Allooloo Technologies Corp. — the doors', description: 'Every Allooloo MCP door, typed by what it resolves, with the routing block, the x402 payment door and the receipt door.', websiteUrl: 'https://allooloo.io/', remotes: doors.map(d => ({ type: 'streamable-http', url: d.mcp })), doors, routing, payment, receipts: { door: 'https://mcp.rco-a2a.ai/mcp', keyring: `${me}/.well-known/jwks.json` }, operator: OPERATOR });
  if (p === '/.well-known/agent-card.json') return J({ protocolVersion: '0.3.0', name: 'Allooloo Technologies Corp. — getissuer and the market doors', description: 'Where agents read the market. Start at the resolver: getissuer names the home market of any listed issuer (ticker, ISIN, LEI) and answers its ACM-68000 signal; the record is served by that market\'s own node.', url: 'https://mcp.getissuer.ai/mcp', preferredTransport: 'JSONRPC',
    supportedInterfaces: [{ url: 'https://mcp.getissuer.ai/mcp', transport: 'JSONRPC', protocolBinding: 'JSONRPC' }], provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: VERSION, capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'],
    skills: [{ id: 'resolve-issuer', name: 'Resolve a listed issuer', description: 'resolve_issuer at https://mcp.getissuer.ai/mcp', tags: ['capital-markets', 'resolver'] }, { id: 'get-signal', name: 'Get the ACM-68000 signal', description: 'get_signal at https://mcp.getissuer.ai/mcp', tags: ['acm-68000'] }, { id: 'get-eco', name: 'Read a market\'s Electronic Compliance Object', description: 'get_eco at https://mcp.getissuer.ai/eco/mcp', tags: ['eco'] }]
      .concat(routing.map(r => ({ id: 'route-' + r.resolves, name: 'Route: ' + r.what, description: `${r.what} resolve at ${r.door}`, tags: ['routing'] }))), doors, payment });
  if (p === '/.well-known/api-catalog') return new Response(JSON.stringify({ linkset: [{ anchor: me, 'service-doc': [{ href: me + '/llms.txt', type: 'text/plain' }], service: doors.map(d => ({ href: d.mcp, title: `${d.id} — ${d.resolves}` })).concat(routing.filter(r => r.resolves === 'gtin').map(r => ({ href: r.door, title: 'GTINs → gtinfetch.ai (GreenCore Solutions Corp.)' }))) }] }, null, 1), { headers: H('application/linkset+json', { 'cache-control': 'public, max-age=300' }) });
  if (p === '/.well-known/ai-catalog.json') return J({ specVersion: '1.0', host: { displayName: 'Allooloo Technologies Corp.', identifier: 'did:web:allooloo.ai' }, entries: doors.map(d => ({ identifier: `urn:air:allooloo.ai:door:${d.id}`, displayName: d.id, type: 'application/json', url: d.mcp, description: d.resolves, ...(d.card ? { agentCard: d.card } : {}) })) });
  if (p === '/.well-known/jwks.json') return J({ keys: [RCO_PUB, ...((JWKS && JWKS.keys) || [])] });
  if (p === '/.well-known/security.txt') return T(`Contact: mailto:allooloo@hey.com\nContact: https://allooloo.io/security\nExpires: 2027-10-24T00:00:00Z\nPreferred-Languages: en\nCanonical: https://allooloo.ai/.well-known/security.txt\n`);
  return J({ error: 'not_found', paths: ['/llms.txt', '/.well-known/mcp.json', '/.well-known/agent-card.json', '/.well-known/api-catalog', '/.well-known/ai-catalog.json', '/.well-known/jwks.json', '/.well-known/security.txt'] }, 404, 'no-store');
}
'''.replace("__PUB__", json.dumps(PUB))
sub("export default {", WK.lstrip("\n") + "export default {")
sub("    if (host === 'allooloo.ai' && (url.pathname === '/x402'", "    if (host === 'allooloo.ai' && (url.pathname === '/llms.txt' || url.pathname.startsWith('/.well-known/'))) return wellKnown(url, env);\n    if (host === 'allooloo.ai' && (url.pathname === '/x402'")
io.open(P, "w", encoding="utf-8", newline="").write(t); print("eco protocols")
