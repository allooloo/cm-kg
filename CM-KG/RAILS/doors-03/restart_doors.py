r"""DOORS-03 — restart the named node doors (cmkg-door-<cc>, latest revision) so they drop their record cache after the live fold; the index reloads on its own
every ten minutes, records are cached until restart. Usage: python -X utf8 -I restart_doors.py <cc> [cc ...]"""
import sys, json, subprocess, os
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
def az(*a): p = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8'); return json.loads(p.stdout) if p.stdout.strip() else ({'error': p.stderr.strip()[-200:]} if p.returncode else None)
apps = {a['name']: a['resourceGroup'] for a in az('containerapp', 'list', '--query', "[?starts_with(name,'cmkg-door-')].{name:name,resourceGroup:resourceGroup}")}
for cc in sys.argv[1:]:
    n = f'cmkg-door-{cc}'; g = apps.get(n)
    if not g: print(cc, 'no door app'); continue
    rev = az('containerapp', 'show', '-g', g, '-n', n, '--query', 'properties.latestRevisionName')
    r = az('containerapp', 'revision', 'restart', '-g', g, '-n', n, '--revision', rev)
    print(cc, 'restarted', rev, g, '' if not (isinstance(r, dict) and r.get('error')) else r['error'])
