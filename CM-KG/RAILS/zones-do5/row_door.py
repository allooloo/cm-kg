r"""row_door.py — NODE-ROW (DAY ORDER 5, 2026-10-24): a ROW node's door answers on its own zone, by the door name rule of record:
mcp.<cc>-cm-kg.ai (door, /mcp) and agent.<cc>-cm-kg.ai (card). Proxied CNAMEs → the door's Container Apps FQDN + asuid TXT; the zone's Origin CA certificate
(AZURE\certs\<cc>-cm-kg.ai) uploaded once to the environment that holds the door; both hostnames bound with it; the route mcp.<cc>-cm-kg.ai/* → cmkg-node-gate.
Run after provision_region.py <cc> <region> app. Usage: python -X utf8 -I row_door.py <cc>"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import cf, zones
cc = sys.argv[1]; zone = f'{cc}-cm-kg.ai'; app = f'cmkg-door-{cc}'
env = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
def az(*a):
    r = subprocess.run([AZ, *a, '-o', 'json'], capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
    if r.returncode: return {'error': (r.stderr or '').strip().splitlines()[-1:]}
    try: return json.loads(r.stdout or 'null')
    except Exception: return r.stdout
apps = az('containerapp', 'list', '--query', f"[?name=='{app}'].{{g:resourceGroup,e:properties.managedEnvironmentId,f:properties.configuration.ingress.fqdn,v:properties.customDomainVerificationId}}")
a = apps[0]; rg, envid, fqdn, asuid = a['g'], a['e'], a['f'], a['v']; env_rg, env_name = envid.split('/')[4], envid.split('/')[-1]
Z = zones(zone)[0]['id']; log = {'door': app, 'fqdn': fqdn, 'env': env_name}
for h in ('mcp', 'agent'):
    for name, typ, content, prox in ((f'{h}.{zone}', 'CNAME', fqdn, True), (f'asuid.{h}.{zone}', 'TXT', asuid, False)):
        ex = cf('GET', f'/zones/{Z}/dns_records?name={name}&type={typ}').get('result') or []
        body = {'type': typ, 'name': name, 'content': content if typ != 'TXT' else f'"{content}"', 'ttl': 1, 'proxied': prox, 'comment': 'NODE-ROW DAY ORDER 5 2026-10-24'}
        r = cf('PUT', f"/zones/{Z}/dns_records/{ex[0]['id']}", body) if ex else cf('POST', f'/zones/{Z}/dns_records', body); log[name] = r.get('success')
cname = 'origin-' + zone.replace('.', '-'); have = az('containerapp', 'env', 'certificate', 'list', '-g', env_rg, '-n', env_name)
cid = next((c['id'] for c in (have if isinstance(have, list) else []) if c.get('name') == cname), None)
if not cid:
    d = os.path.join(r'C:\ALLOOLOO\AZURE\certs', zone); pw = open(os.path.join(d, 'pfx-pass.txt')).read().strip()
    r = az('containerapp', 'env', 'certificate', 'upload', '-g', env_rg, '-n', env_name, '--certificate-file', os.path.join(d, 'origin.pfx'), '--password', pw, '--certificate-name', cname); cid = r.get('id') if isinstance(r, dict) else None
log['certificate'] = bool(cid)
bound = {x['name']: x.get('bindingType') for x in (az('containerapp', 'hostname', 'list', '-n', app, '-g', rg) or []) if isinstance(x, dict)}
for h in (f'mcp.{zone}', f'agent.{zone}'):
    if bound.get(h) == 'SniEnabled': log[h] = 'bound (already)'; continue
    if h not in bound: az('containerapp', 'hostname', 'add', '-n', app, '-g', rg, '--hostname', h)
    r = az('containerapp', 'hostname', 'bind', '-n', app, '-g', rg, '--hostname', h, '--certificate', cid, '--validation-method', 'TXT')
    log[h] = 'bound' if not (isinstance(r, dict) and r.get('error')) else r['error']
pat = f'mcp.{zone}/*'; ex = [r for r in cf('GET', f'/zones/{Z}/workers/routes').get('result', []) if r['pattern'] == pat]
log['gate route'] = 'present' if ex else cf('POST', f'/zones/{Z}/workers/routes', {'pattern': pat, 'script': 'cmkg-node-gate'}).get('success')
print(json.dumps(log)); json.dump(log, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'row-door-{cc}-2026-10-24.json'), 'w'), indent=1)
