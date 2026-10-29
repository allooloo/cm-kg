"""ORDER-035 follow-on (CEO, 2026-10-23): the Hong Kong door in Azure API Center allooloo-apic — the fifteenth asset, cm-kg-hk, the same shape as the other
twelve door assets (asset · version v0-11-0 · definitions mcp + openapi (imported from the door's own spec) · deployment prod in environment production).
Description of record and contact as apic_descriptions.py sets them. Create-only: stops if cm-kg-hk already exists. az rest with @file bodies (Windows). Tenant check first."""
import json, subprocess, os, sys, tempfile, datetime
API = '2024-06-01-preview'
B = 'https://management.azure.com/subscriptions/038b49c0-5a0c-46f7-bd34-41ee6d087b41/resourceGroups/allooloo-cmkg-shared/providers/Microsoft.ApiCenter/services/allooloo-apic/workspaces/default'
def az(method, path, body=None):
    cmd = ['az', 'rest', '--method', method, '--url', f'{B}{path}?api-version={API}', '-o', 'json']; f = None
    if body is not None:
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8'); json.dump(body, f, ensure_ascii=False); f.close(); cmd += ['--body', '@' + f.name]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
    if f: os.unlink(f.name)
    if r.returncode != 0: return {'error': (r.stderr or r.stdout).strip()[-300:]}
    try: return json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception: return {'raw': r.stdout[:200]}
sys.path.insert(0, r'C:\ALLOOLOO\AZURE'); from az_guard import require_allooloo; require_allooloo()   # STANDING RULE Sept 13 2026: tenant + subscription + user, stop on mismatch
src = open(r'C:\ALLOOLOO\AZURE\apic_descriptions.py', encoding='utf-8').read()
ns = {}; exec(src[src.index('DESC = ('):src.index('NODES = ')], ns)   # the description of record and the contact, as the twelve carry them
DESC, CONTACT = ns['DESC'], ns['CONTACT']
API_NAME = 'cm-kg-hk'; MCP = 'https://mcp.hk-cm-kg.ai'; SITE = 'https://hk-cm-kg.ai'; V = 'v0-11-0'
if 'error' not in az('GET', f'/apis/{API_NAME}'): raise SystemExit(f'STOP: {API_NAME} already exists — create-only')
steps = []
def step(name, res):
    steps.append(f"{name}: {'FAILED ' + res['error'] if 'error' in res else 'ok'}")
    if 'error' in res: print('\n'.join(steps)); raise SystemExit(1)
    return res
a = step('api', az('PUT', f'/apis/{API_NAME}', {'properties': {'title': 'Capital Markets Agents: MCP+A2A Hong Kong door', 'kind': 'mcp', 'summary': 'Capital Markets Knowledge Graph — MCP (streamable-http) + A2A',
    'description': DESC, 'lifecycleStage': 'production', 'contacts': CONTACT, 'customProperties': {},
    'externalDocumentation': [{'title': 'website', 'url': SITE}, {'title': 'openapi', 'url': f'{MCP}/openapi.json'}, {'title': 'mcp descriptor', 'url': f'{MCP}/mcp.json'}]}}))
step('version', az('PUT', f'/apis/{API_NAME}/versions/{V}', {'properties': {'title': 'v0.11.0', 'lifecycleStage': 'production'}}))
step('definition mcp', az('PUT', f'/apis/{API_NAME}/versions/{V}/definitions/mcp', {'properties': {'title': 'MCP streamable-http', 'description': f'remote {MCP}/mcp — descriptor {MCP}/mcp.json'}}))
step('definition openapi', az('PUT', f'/apis/{API_NAME}/versions/{V}/definitions/openapi', {'properties': {'title': "OpenAPI 3.1 (the door's own spec)", 'description': f'{MCP}/openapi.json — the REST twin of the MCP door; same records, same events'}}))
step('openapi import', az('POST', f'/apis/{API_NAME}/versions/{V}/definitions/openapi/importSpecification', {'format': 'link', 'value': f'{MCP}/openapi.json', 'specification': {'name': 'openapi', 'version': '3.1.0'}}))
step('deployment prod', az('PUT', f'/apis/{API_NAME}/deployments/prod', {'properties': {'title': 'production', 'definitionId': f'/workspaces/default/apis/{API_NAME}/versions/{V}/definitions/mcp', 'environmentId': '/workspaces/default/environments/production',
    'server': {'runtimeUri': [f'{MCP}/mcp']}, 'customProperties': {}}}))
n = len(az('GET', '/apis').get('value', []))
out = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'asset_id': a.get('id'), 'steps': steps, 'assets_in_workspace': n}
json.dump(out, open(r'C:\ALLOOLOO\AZURE\apic-hk-035-20261023.json', 'x', encoding='utf-8'), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False, indent=1))
