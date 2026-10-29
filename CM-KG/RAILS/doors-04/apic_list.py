r"""LIST-02 — read only: the API assets in allooloo-apic (name, kind, title, contacts, deployment runtime) against the roster of record."""
import json, subprocess, os
ENV = {**os.environ, 'AZURE_CONFIG_DIR': r'C:\ALLOOLOO\.azure'}; AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
B = 'https://management.azure.com/subscriptions/038b49c0-5a0c-46f7-bd34-41ee6d087b41/resourceGroups/allooloo-cmkg-shared/providers/Microsoft.ApiCenter/services/allooloo-apic/workspaces/default'
def get(p): r = subprocess.run(AZ + ['rest', '--method', 'get', '--url', f'{B}{p}?api-version=2024-06-01-preview', '-o', 'json'], capture_output=True, text=True, encoding='utf-8', env=ENV); return json.loads(r.stdout) if r.stdout.strip() else {'error': r.stderr[-200:]}
apis = get('/apis').get('value', [])
nodes = json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))
have = {a['name'] for a in apis}
for a in sorted(apis, key=lambda x: x['name']):
    p = a['properties']; print(a['name'], '|', p.get('kind'), '|', p.get('title'), '|', [c.get('email') for c in p.get('contacts') or []])
want = [f"cm-kg-{n['node'].split('-')[0]}" for n in nodes]
print('assets', len(apis), '| node assets present', sum(1 for w in want if w in have), 'of', len(want), '| apex', 'cm-kg-apex' in have)
print('missing', [w for w in want if w not in have])
dep = get('/apis/cm-kg-fr/deployments/prod'); print('fr runtime', ((dep.get('properties') or {}).get('server') or {}).get('runtimeUri'))
