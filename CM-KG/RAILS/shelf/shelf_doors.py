r"""SHELF-01 step 3 — the two shelf doors on the shared door image (cmkg-door:0.17.0), the house method of the EU doors (zones-do5):
  1 one Cloudflare Origin CA certificate per zone (origin_ca_do5.py <zone>; key and PFX under AZURE\certs\<zone>, never printed)
  2 the Container App in East US (cmkg-env-eastus-2): cmkg-door-bench (DOOR_MODE=bench) · cmkg-door-review (DOOR_MODE=review); store = the apex store's
    'shelf' container (key as an app secret); the bench door also holds the CMR signing key (app secret) to sign scorecards
  3 the zone records: mcp.<zone> CNAME → the app FQDN (proxied) + TXT asuid.mcp.<zone> = the app's customDomainVerificationId
  4 the hostname added and bound with the zone's certificate (TXT validation)
  5 the gate through mcp.<zone>: initialize version 0.17.0, its tools (bench 3 · review 2), list_* answers
Secrets are read in-process (AGENT KEYS, az) and passed to az only. Usage: python -X utf8 -I shelf_doors.py bench|review|both"""
import sys, os, json, subprocess, time, urllib.request
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\zones-do5')
from cf import cf, zones
HERE = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1')
AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
RG, ENV = 'allooloo-cmkg-eastus', 'cmkg-env-eastus-2'; IMG = 'allooloocmkg.azurecr.io/cmkg-door:0.17.0'
def az(*a):
    r = subprocess.run([AZ, *a, '-o', 'json'], capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
    if r.returncode: return {'error': (r.stderr or '').strip().splitlines()[-2:]}
    try: return json.loads(r.stdout or 'null')
    except Exception: return r.stdout
def tsv(*a): return subprocess.run([AZ, *a, '-o', 'tsv'], capture_output=True, text=True, env=env).stdout.strip()
DOORS = {'bench': ('cmkg-door-bench', 'data-bench.ai', 3), 'review': ('cmkg-door-review', 'data-review.ai', 2)}
want = list(DOORS) if sys.argv[1] == 'both' else [sys.argv[1]]
log = {}
for mode in want:
    app, zone, ntools = DOORS[mode]; host = f'mcp.{zone}'; out = log[mode] = {}
    # 1 the zone's Origin CA certificate
    p = subprocess.run([sys.executable, '-X', 'utf8', '-I', r'C:\ALLOOLOO\CM-KG\RAILS\zones-do5\origin_ca_do5.py', zone], capture_output=True, text=True); out['origin_ca'] = p.stdout.strip()[-200:] or p.stderr[-200:]
    # 2 the app
    ex = az('containerapp', 'show', '-n', app, '-g', RG, '--query', 'name')
    if isinstance(ex, dict) and ex.get('error'):
        akey = tsv('storage', 'account', 'keys', 'list', '-n', 'allooloocmkgapex', '-g', 'allooloo-cmkg-shared', '--query', '[0].value')
        acr_u = tsv('acr', 'credential', 'show', '-n', 'allooloocmkg', '--query', 'username'); acr_p = tsv('acr', 'credential', 'show', '-n', 'allooloocmkg', '--query', 'passwords[0].value')
        secrets = [f'storage-key={akey}']
        if mode == 'bench': secrets.append('cmr-signing-jwk=' + json.dumps(json.loads(open(r'C:\ALLOOLOO\AGENT KEYS\cmr-signing-jwk.txt', encoding='utf-8-sig').read()), separators=(',', ':')))
        envs = [f'NODE={mode}-shelf', 'REGION=eastus', 'STORAGE_ACCOUNT=allooloocmkgapex', 'STORAGE_CONTAINER=shelf', 'STORAGE_KEY=secretref:storage-key', f'PUBLIC_HOST={host}', f'DOOR_MODE={mode}']
        if mode == 'bench': envs.append('CMR_SIGNING_JWK=secretref:cmr-signing-jwk')
        r = az('containerapp', 'create', '-n', app, '-g', RG, '--environment', ENV, '--image', IMG, '--registry-server', 'allooloocmkg.azurecr.io', '--registry-username', acr_u, '--registry-password', acr_p,
               '--target-port', '8080', '--ingress', 'external', '--min-replicas', '1', '--max-replicas', '3', '--cpu', '0.5', '--memory', '1Gi', '--secrets', *secrets, '--env-vars', *envs,
               '--revision-suffix', 'v0170-1027', '--query', '{fqdn:properties.configuration.ingress.fqdn,state:properties.provisioningState}')
        out['create'] = r if not (isinstance(r, dict) and r.get('error')) else r['error']; print(mode, 'create', out['create'])
        if isinstance(r, dict) and r.get('error'): continue
    info = az('containerapp', 'show', '-n', app, '-g', RG, '--query', '{fqdn:properties.configuration.ingress.fqdn,asuid:properties.customDomainVerificationId}')
    out['fqdn'] = info['fqdn']; print(mode, 'app', info['fqdn'])
    # 3 the zone records
    Z = zones(zone)[0]['id']
    for name, typ, content, prox in ((host, 'CNAME', info['fqdn'], True), (f'asuid.{host}', 'TXT', info['asuid'], False)):
        exr = cf('GET', f'/zones/{Z}/dns_records?name={name}&type={typ}').get('result') or []
        body = {'type': typ, 'name': name, 'content': content if typ != 'TXT' else '"%s"' % content, 'ttl': 1, 'proxied': prox, 'comment': 'SHELF-01 2026-10-27'}
        r = cf('PUT', f"/zones/{Z}/dns_records/{exr[0]['id']}", body) if exr else cf('POST', f'/zones/{Z}/dns_records', body)
        out[f'dns {name}'] = r.get('success'); print(mode, 'dns', name, r.get('success'), (r.get('errors') or [''])[0])
    # 4 the hostname, bound with the zone's certificate
    cname = 'origin-' + zone.replace('.', '-'); certs = az('containerapp', 'env', 'certificate', 'list', '-g', RG, '-n', ENV)
    cid = next((c['id'] for c in (certs if isinstance(certs, list) else []) if c.get('name') == cname), None)
    if not cid:
        d = os.path.join(r'C:\ALLOOLOO\AZURE\certs', zone); pw = open(os.path.join(d, 'pfx-pass.txt')).read().strip()
        r = az('containerapp', 'env', 'certificate', 'upload', '-g', RG, '-n', ENV, '--certificate-file', os.path.join(d, 'origin.pfx'), '--password', pw, '--certificate-name', cname); cid = r.get('id') if isinstance(r, dict) else None
    time.sleep(30)   # the asuid record propagates before the binding validates it
    bound = {h['name']: h.get('bindingType') for h in (az('containerapp', 'hostname', 'list', '-n', app, '-g', RG) or [])} if True else {}
    if host not in bound: az('containerapp', 'hostname', 'add', '-n', app, '-g', RG, '--hostname', host)
    r = az('containerapp', 'hostname', 'bind', '-n', app, '-g', RG, '--hostname', host, '--certificate', cid, '--validation-method', 'TXT')
    out['bind'] = 'bound' if not (isinstance(r, dict) and r.get('error')) else r['error']; print(mode, 'bind', out['bind'])
    # 5 the gate through the public door
    g = {}
    for _ in range(10):
        try:
            def rpc(m, p):
                rr = urllib.request.urlopen(urllib.request.Request(f'https://{host}/mcp', data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'accept': 'application/json, text/event-stream', 'user-agent': 'Allooloo SHELF-01 gate'}), timeout=60)
                t = rr.read().decode(); return json.loads(t[t.index('{'):])
            g['version'] = rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'shelf-gate', 'version': '1'}})['result']['serverInfo'].get('version')
            g['tools'] = [t['name'] for t in rpc('tools/list', {})['result']['tools']]
            g['list'] = rpc('tools/call', {'name': 'list_benches' if mode == 'bench' else 'list_reviews', 'arguments': {}})['result'].get('structuredContent')
            break
        except Exception as e: g['error'] = repr(e)[:160]; time.sleep(20)
    g['PASS'] = g.get('version') == '0.17.0' and len(g.get('tools') or []) == ntools and isinstance(g.get('list'), dict)
    out['gate'] = g; print(mode, 'gate', json.dumps(g)[:400])
json.dump(log, open(os.path.join(HERE, f'shelf-doors-{time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())}.json'), 'w'), indent=1, default=str)
