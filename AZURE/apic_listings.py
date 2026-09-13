"""LISTINGS (CEO, Sept 13 2026) — Azure API Center allooloo-apic: OpenAPI definition per door imported from each door's own spec (eleven node doors + apex),
externalDocumentation openapi links corrected, apex title corrected, and the agentic-x402.ai/api REST API registered with its OpenAPI. Nothing deleted.
az rest with @file bodies (Windows). Tenant check first."""
import json, subprocess, sys, os, tempfile
API = '2024-06-01-preview'
B = 'https://management.azure.com/subscriptions/038b49c0-5a0c-46f7-bd34-41ee6d087b41/resourceGroups/allooloo-cmkg-shared/providers/Microsoft.ApiCenter/services/allooloo-apic/workspaces/default'
def az(method, path, body=None):
    cmd = ['az', 'rest', '--method', method, '--url', f'{B}{path}?api-version={API}', '-o', 'json']
    f = None
    if body is not None:
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8'); json.dump(body, f); f.close(); cmd += ['--body', '@' + f.name]
    r = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if f: os.unlink(f.name)
    if r.returncode != 0: return {'error': (r.stderr or r.stdout).strip()[:300]}
    try: return json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception: return {'raw': r.stdout[:200]}
sys.path.insert(0, r'C:\ALLOOLOO\AZURE'); from az_guard import require_allooloo; require_allooloo()   # STANDING RULE Sept 13 2026: tenant + subscription + user, stop on mismatch
NODES = {'ca': 'Canada', 'uk': 'United Kingdom', 'us': 'United States', 'de': 'Germany', 'fr': 'France', 'nl': 'Netherlands', 'ch': 'Switzerland', 'au': 'Australia', 'sg': 'Singapore', 'jp': 'Japan', 'kr': 'South Korea'}
doors = {f'cm-kg-{cc}': (f'https://mcp.{cc}-cm-kg.ai', f'https://{cc}-cm-kg.ai', f'Capital Markets Agents: MCP+A2A {n}') for cc, n in NODES.items()}
doors['cm-kg-apex'] = ('https://mcp.capitalmarketsknowledgegraph.ai', 'https://capitalmarketsknowledgegraph.ai', 'Capital Markets Agents: MCP+A2A apex router')
lines = []
for api, (mcp, site, title) in doors.items():
    cur = az('GET', f'/apis/{api}')
    if 'error' in cur: lines.append(f'{api}: GET failed {cur["error"]}'); continue
    props = cur['properties']
    props['title'] = title
    props['externalDocumentation'] = [{'title': 'website', 'url': site}, {'title': 'openapi', 'url': f'{mcp}/openapi.json'}, {'title': 'mcp descriptor', 'url': f'{mcp}/mcp.json'}]
    up = az('PUT', f'/apis/{api}', {'properties': {k: v for k, v in props.items() if k in ('title', 'kind', 'summary', 'description', 'lifecycleStage', 'externalDocumentation', 'contacts', 'license', 'termsOfService', 'customProperties')}})
    d = az('PUT', f'/apis/{api}/versions/v0-11-0/definitions/openapi', {'properties': {'title': 'OpenAPI 3.1 (the door\'s own spec)', 'description': f'{mcp}/openapi.json — the REST twin of the MCP door; same records, same events'}})
    imp = az('POST', f'/apis/{api}/versions/v0-11-0/definitions/openapi/importSpecification', {'format': 'link', 'value': f'{mcp}/openapi.json', 'specification': {'name': 'openapi', 'version': '3.1.0'}})
    lines.append(f"{api}: title/docs {'ok' if 'error' not in up else up['error'][:80]} · definition {'ok' if 'error' not in d else d['error'][:80]} · import {'accepted' if 'error' not in imp else imp['error'][:120]}")
# agentic-x402.ai/api — REST API with its own OpenAPI
api = 'agentic-x402-api'
up = az('PUT', f'/apis/{api}', {'properties': {'title': 'Agentic x402 — a paid call with a signed receipt', 'kind': 'rest', 'summary': 'x402 v2 paid endpoint: $0.01 USDC on Base (eip155:8453), EIP-3009, 60 s window; EdDSA-signed receipts that resolve forever', 'description': 'GET https://agentic-x402.ai/api answers 402 Payment Required with the offer; a signed authorization buys the estate index or one Capital Markets Record (?record=node/exchange/code) and a receipt (kid allooloo-x402-receipts-2026-09, public key /x402/jwks.json, resolver /x402/receipt/{nonce}). Public-record only. Operator: Allooloo Technologies Corp.', 'lifecycleStage': 'production', 'externalDocumentation': [{'title': 'website', 'url': 'https://agentic-x402.ai/'}, {'title': 'openapi', 'url': 'https://agentic-x402.ai/openapi.json'}, {'title': 'receipt key', 'url': 'https://agentic-x402.ai/x402/jwks.json'}], 'contacts': [{'email': 'developers@allooloo.ai', 'name': 'Allooloo Technologies Corp.', 'url': 'https://allooloo.io'}], 'termsOfService': {'url': 'https://allooloo.io/terms'}}})
v = az('PUT', f'/apis/{api}/versions/v1', {'properties': {'title': 'v1', 'lifecycleStage': 'production'}})
d = az('PUT', f'/apis/{api}/versions/v1/definitions/openapi', {'properties': {'title': 'OpenAPI 3.1', 'description': 'https://agentic-x402.ai/openapi.json'}})
imp = az('POST', f'/apis/{api}/versions/v1/definitions/openapi/importSpecification', {'format': 'link', 'value': 'https://agentic-x402.ai/openapi.json', 'specification': {'name': 'openapi', 'version': '3.1.0'}})
dep = az('PUT', f'/apis/{api}/deployments/prod', {'properties': {'title': 'production', 'definitionId': f'/workspaces/default/apis/{api}/versions/v1/definitions/openapi', 'environmentId': '/workspaces/default/environments/production', 'server': {'runtimeUri': ['https://agentic-x402.ai/api']}, 'isDefault': True, 'state': 'active'}})
lines.append(f"{api}: api {'ok' if 'error' not in up else up['error'][:100]} · version {'ok' if 'error' not in v else v['error'][:80]} · definition {'ok' if 'error' not in d else d['error'][:80]} · import {'accepted' if 'error' not in imp else imp['error'][:120]} · deployment {'ok' if 'error' not in dep else dep['error'][:120]}")
print('\n'.join(lines))
json.dump({'lines': lines}, open(r'C:\ALLOOLOO\AZURE\apic-listings-2026-09-13.json', 'w'), indent=1)
