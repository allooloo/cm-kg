r"""LIST-02 — read only: every cmkg-door Container App, its image tag and env (names; values only where not secret)."""
import json, subprocess, os, collections
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
apps = json.loads(subprocess.run([*AZ, 'containerapp', 'list', '--query', "[?starts_with(name,'cmkg-door-')].{n:name,g:resourceGroup,i:properties.template.containers[0].image,env:properties.template.containers[0].env}", '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8').stdout)
print(collections.Counter(a['i'].split(':')[-1] for a in apps))
for a in sorted(apps, key=lambda x: x['n']): print(a['n'], a['g'], a['i'].split(':')[-1], [(e['name'], (e.get('value') or 'secretref')[:36]) for e in a['env']])
json.dump(apps, open(os.path.join(os.environ['TEMP'], 'claude', 'door-apps.json'), 'w'), indent=1)
