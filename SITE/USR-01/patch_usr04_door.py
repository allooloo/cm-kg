import pathlib
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker\research.js'); s = p.read_text(encoding='utf-8')
if 'LIST_NODES' in s: raise SystemExit('already patched')
def rep(o, n, k=1):
    global s
    assert s.count(o) == k, (s.count(o), o[:70]); s = s.replace(o, n)
rep("const HOST = 'getresearch.ai'; const GI_MCP = 'https://mcp.getissuer.ai/mcp'; const RCO = 'https://mcp.rco-records.ai/mcp'; const AGENT = 'https://agent.getissuer.ai/.well-known/agent-card.json';",
    "const HOST = 'getresearch.ai'; const GI_MCP = 'https://mcp.getresearch.ai/mcp'; const RCO = 'https://mcp.rco-records.ai/mcp'; const AGENT = 'https://agent.getresearch.ai/.well-known/agent-card.json';   // USR-04: the door's own host (the same router as mcp.getissuer.ai)\nconst LIST_NODES = 'https://mcp.getissuer.ai/mcp';   // the roster read: another zone's host of the same router (a Worker cannot fetch its own zone's other route)")
rep("  try { const r = await fetch(GI_MCP, { method: 'POST',", "  try { const r = await fetch(LIST_NODES, { method: 'POST',")
rep("mcpServers: { getissuer: { type: 'http', url: GI_MCP } }", "mcpServers: { getresearch: { type: 'http', url: GI_MCP } }")
rep("claude mcp add --transport http getissuer ${esc(GI_MCP)}", "claude mcp add --transport http getresearch ${esc(GI_MCP)}")
rep("— the apex router; read-only, no authentication, no account. get_research is on its tool list beside resolve_issuer and the rest.", "— the same router as <code>https://mcp.getissuer.ai/mcp</code> ; read-only, no authentication, no account. Tools: get_research · resolve_issuer · list_nodes. get_research is on mcp.getissuer.ai's own tool list too.")
rep("the page store's ledger, list_nodes at <code>${esc(GI_MCP)}</code>", "the page store's ledger, list_nodes at <code>${esc(LIST_NODES)}</code>")
rep("'https://mcp.getissuer.ai/x402/pricing.json'", "'https://mcp.getresearch.ai/x402/pricing.json'", 2)
rep("kind: 'pointer (the door is the apex router)', url: GI_MCP, mcp_json: 'https://mcp.getissuer.ai/mcp.json'", "kind: 'pointer (the door is the router)', url: GI_MCP, mcp_json: 'https://mcp.getresearch.ai/mcp.json'")
rep("(MCP Streamable HTTP, no auth) — the apex router; tool get_research.", "(MCP Streamable HTTP, no auth) — the same router as https://mcp.getissuer.ai/mcp; tools get_research, resolve_issuer, list_nodes.")
rep("tools: ['get_research'], errors:", "tools: ['get_research', 'resolve_issuer', 'list_nodes'], registry: 'io.github.allooloo/getresearch', errors:")
p.write_text(s, encoding='utf-8'); print('ok')
