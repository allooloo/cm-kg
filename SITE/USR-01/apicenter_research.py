r"""apicenter_asof.py — DOORS-01 item 6: the Azure API Center entry for one door (argv: getfilings | getticker | getauditor) (allooloo-apic, workspace default), the way STACK-01's apicenter.py
made rco-records': API <door> (kind mcp, production) · version (the router's version) · MCP definition (the tools, read from the door's own
tools/list) · deployment live (https://mcp.<door>.ai/mcp). Values read from the door's own surfaces. Signed-in az, Allooloo tenant; an existing
entry is read and saved beside first (apicenter-' + K + '-pre-<stamp>.json). Usage: python -X utf8 -I apicenter_asof.py"""
import os, sys, json, subprocess, datetime, urllib.request
K = 'getresearch'
SUM = "The record's research page on a listed company, written from the signed record: no analyst, no rating, no view. Signed and receipted on RCO-10060."
HERE = os.path.dirname(os.path.abspath(__file__)); ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1')
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
def az(*a, body=None, ok404=False):
    args = [*AZ, *a, '-o', 'json']
    if body is not None:
        fp = os.path.join(HERE, '_apic_body.json'); json.dump(body, open(fp, 'w', encoding='utf-8'), ensure_ascii=False); args += ['--body', '@' + fp]
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', env=ENV)
    if r.returncode:
        if ok404 and ('NotFound' in r.stderr or '404' in r.stderr): return None
        raise SystemExit('az failed: ' + r.stderr[-400:])
    return json.loads(r.stdout or 'null')
acct = az('account', 'show'); assert acct['tenantId'] == '04a24e43-dc13-4578-950a-910db076a799' and acct['id'] == '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
S = az('resource', 'list', '--resource-type', 'Microsoft.ApiCenter/services')[0]['id']
U = lambda p: f'https://management.azure.com{S}/workspaces/default/{p}?api-version=2024-03-01'
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
old = az('rest', '--method', 'get', '--url', U(f'apis/{K}'), ok404=True)
if old: json.dump(old, open(os.path.join(HERE, f'apicenter-' + K + '-pre-{stamp}.json'), 'x', encoding='utf-8'), indent=1, ensure_ascii=False)
G = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Allooloo USR-04 API Center'}), timeout=30).read())
mcpj = G(f'https://mcp.{K}.ai/mcp.json'); card = G(f'https://agent.{K}.ai/.well-known/agent-card.json')
init = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://mcp.{K}.ai/mcp', method='POST', data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}}).encode(), headers={'User-Agent': 'Allooloo USR-04 API Center', 'content-type': 'application/json', 'accept': 'application/json'}), timeout=30).read())
ver = init['result']['serverInfo']['version']; vname = ver.replace('.', '-'); tools = [t['name'] for t in mcpj.get('tools', []) if not t.get('note')]
api = {'properties': {'title': 'getresearch — the Data Research door', 'kind': 'mcp', 'lifecycleStage': 'production',
       'summary': SUM,
       'description': (card.get('description') or '')[:1000], 'contacts': [{'name': 'Allooloo Technologies Corp.', 'email': 'mk@allooloo.ai', 'url': f'https://{K}.ai'}],
       'license': {'name': 'Allooloo door; RCO-10060 is MIT'},
       'externalDocumentation': [{'title': 'page', 'url': f'https://{K}.ai/'}, {'title': 'Agent Card', 'url': f'https://agent.{K}.ai/.well-known/agent-card.json'},
                                 {'title': 'RCO-10060', 'url': 'https://rco-10060.org/'}, {'title': 'registry', 'url': f'https://registry.modelcontextprotocol.io/v0/servers?search=io.github.allooloo/{K}'}],
       'customProperties': {}}}
az('rest', '--method', 'put', '--url', U(f'apis/{K}'), body=api)
az('rest', '--method', 'put', '--url', U(f'apis/{K}/versions/{vname}'), body={'properties': {'title': ver, 'lifecycleStage': 'production'}})
az('rest', '--method', 'put', '--url', U(f'apis/{K}/versions/{vname}/definitions/mcp'), body={'properties': {'title': 'MCP', 'description': 'Streamable HTTP, JSON-RPC 2.0 · tools: ' + ', '.join(tools) + ' · reads free (the x402 offer only when asked) · typed errors unknown_issuer, ambiguous, no_page, invalid_request'}})
az('rest', '--method', 'put', '--url', U(f'apis/{K}/deployments/live'), body={'properties': {'title': 'live', 'environmentId': '/workspaces/default/environments/live', 'definitionId': f'/workspaces/default/apis/{K}/versions/{vname}/definitions/mcp', 'server': {'runtimeUri': [f'https://mcp.{K}.ai/mcp']}, 'state': 'active'}})
rb = az('rest', '--method', 'get', '--url', U(f'apis/{K}')); dp = az('rest', '--method', 'get', '--url', U(f'apis/{K}/deployments/live'))
print(K + ':', rb['properties']['title'], '| kind', rb['properties']['kind'], '| version', vname, '| tools', tools, '| deployment', dp['properties']['server']['runtimeUri'])
