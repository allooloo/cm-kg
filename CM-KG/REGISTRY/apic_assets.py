r"""apic_assets.py — PROTOCOLS-A-01 (DAY ORDER 3, 2026-10-24): Azure API Center assets for ECO and the signals in allooloo-apic (Allooloo tenant): api, version
v1-0-0, definition mcp, deployment prod on the production environment — the same shape as cm-kg-apex. Create-or-update; nothing deleted. Tenant guarded.
Usage: python -X utf8 -I apic_assets.py"""
import json, os, subprocess, tempfile
ENV = {**os.environ, "AZURE_CONFIG_DIR": r"C:\ALLOOLOO\.azure", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
AZ = [r"C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe", "-IX", "utf8", "-m", "azure.cli"]
def az(*a):
    r = subprocess.run(AZ + list(a), capture_output=True, text=True, encoding="utf-8", env=ENV); return r.returncode, (r.stdout or r.stderr)[-400:]
rc, out = az("account", "show", "--query", "tenantId", "-o", "tsv"); assert out.strip() == "04a24e43-dc13-4578-950a-910db076a799", out
B = "https://management.azure.com/subscriptions/038b49c0-5a0c-46f7-bd34-41ee6d087b41/resourceGroups/allooloo-cmkg-shared/providers/Microsoft.ApiCenter/services/allooloo-apic/workspaces/default"
V = "?api-version=2024-03-01"
C = [{"email": "mk@allooloo.ai", "name": "Allooloo Technologies Corp.", "url": "https://allooloo.io"}]
APIS = {
  "eco": {"title": "Electronic Compliance Objects (index: allooloo.ai/markets)", "summary": "Each market's disclosure regime as one sourced, signed object, with the issuer's ACM-68000 signal.",
          "description": "What: one Electronic Compliance Object per market (index: allooloo.ai/markets): regulator, exchanges and listings page, regulated-information store, periodic and ad hoc disclosure, filing format, ISIN prefix, LEI, calendar, languages, halts page — each field with its source page, signed (kid allooloo-eco-2026-10). Doors: MCP https://mcp.getissuer.ai/eco/mcp (get_eco, get_signal, resolve_issuer, list_nodes); pages https://<cc>-eco.ai/ with /eco.json and /isin/{ISIN}. Every lookup that returns a signal leaves an RCO receipt. Every read free for every agent (no rationing); x402 on Base (USDC) for agents that choose to pay. Standard ECO-10060 (Agentic KG Holdings, MIT).",
          "docs": [("website", "https://allooloo.ai/markets"), ("mcp descriptor", "https://fr-eco.ai/.well-known/mcp.json"), ("registry", "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.allooloo/eco")], "uri": "https://mcp.getissuer.ai/eco/mcp"},
  "acm-signals": {"title": "ACM-68000 signals for listed issuers", "summary": "The ACM-68000 signal of a listed security in its home market, live through the resolver.",
          "description": "What: the seven ACM-68000 signals for listed issuers — ACM-200 TRADING, ACM-404 NOT ON THE REGISTER, ACM-451 READ THE FILING (named), ACM-300 CONDITIONAL, ACM-000 NOT APPLICABLE, ACM-500 SYSTEM ERROR; ACM-403 HALTED advisory until the nodes carry a halt flag. Doors: MCP https://mcp.getissuer.ai/signals/mcp (get_signal, list_signals); pages https://acm-<code>.ai/. Every get_signal leaves an RCO receipt. Every read free for every agent (no rationing); x402 on Base (USDC) for agents that choose to pay. Standard ACM-68000 (Agentic KG Holdings, MIT).",
          "docs": [("website", "https://acm-200.ai/"), ("signals", "https://acm-200.ai/signals.json"), ("registry", "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.allooloo/acm-signals")], "uri": "https://mcp.getissuer.ai/signals/mcp"}}
def put(url, body):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f: json.dump(body, f); fn = f.name
    rc, out = az("rest", "--method", "put", "--url", url, "--body", "@" + fn, "--headers", "Content-Type=application/json"); os.unlink(fn); return rc, out
log = {}
for n, a in APIS.items():
    steps = []
    steps.append(put(f"{B}/apis/{n}{V}", {"properties": {"title": a["title"], "summary": a["summary"], "description": a["description"][:1000], "kind": "mcp", "lifecycleStage": "production", "contacts": C,
        "externalDocumentation": [{"title": t, "url": u} for t, u in a["docs"]], "license": {"name": "Standard MIT; operated by Allooloo"}}}))
    steps.append(put(f"{B}/apis/{n}/versions/v1-0-0{V}", {"properties": {"title": "1.0.0", "lifecycleStage": "production"}}))
    steps.append(put(f"{B}/apis/{n}/versions/v1-0-0/definitions/mcp{V}", {"properties": {"title": "MCP", "description": "Streamable HTTP, JSON-RPC 2.0, no auth for reads"}}))
    steps.append(put(f"{B}/apis/{n}/deployments/prod{V}", {"properties": {"title": "production", "environmentId": "/workspaces/default/environments/production", "definitionId": f"/workspaces/default/apis/{n}/versions/v1-0-0/definitions/mcp", "server": {"runtimeUri": [a["uri"]]}, "isDefault": True}}))
    log[n] = [s[0] for s in steps]; print(n, log[n], "" if all(s[0] == 0 for s in steps) else [s[1] for s in steps if s[0]])
json.dump(log, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "apic-2026-10-24.json"), "w"), indent=1)
