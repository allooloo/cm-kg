r"""iw_domains.py — IW-MOVE-01 step 7 (before the flip, nothing public changes): the nine host names on the new door, each with its own managed certificate
validated by a TXT record (the names stay proxied at Cloudflare and keep pointing at the old door until the flip).
  add     each host name is added to iw-door (needs asuid.<host> to carry the new environment's id: iw_dns.py txt)
  certs   a managed certificate is requested per host (TXT validation); the validation tokens are written to cert-tokens.json for iw_dns.py dnsauth
  bind    each host whose certificate has been issued is bound (SNI); prints what is still pending
Usage: python -X utf8 -I iw_domains.py add|certs|bind"""
import json, os, subprocess, sys, time, pathlib
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
H = pathlib.Path(__file__).parent; RG = 'allooloo-iw-francecentral'; EN = 'iw-env-francecentral'; APP = 'iw-door'
HOSTS = ['issuerwire.ai', 'www.issuerwire.ai', 'mcp.issuerwire.ai', 'a2a-amn.ai', 'www.a2a-amn.ai', 'mcp.a2a-amn.ai', 'x402.a2a-amn.ai', 'agentmarketnews.ai', 'www.agentmarketnews.ai']
cname = lambda h: 'mc-iw-' + h.replace('.', '-')
def az(*a, check=True, wait=True):
    if not wait: return subprocess.Popen([*AZ, *a, '-o', 'json'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=ENV)
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode:
        if check: sys.exit(f'STOP az {" ".join(a[:5])}: {r.stderr[-600:]}')
        return {'_error': r.stderr[-300:]}
    return json.loads(r.stdout) if r.stdout.strip() else None
def certs(): return {c['properties']['subjectName']: c for c in az('containerapp', 'env', 'certificate', 'list', '-g', RG, '-n', EN, '--managed-certificates-only') or []}
what = sys.argv[1]
if what == 'add':
    have = {d['name'] for d in (az('containerapp', 'hostname', 'list', '-n', APP, '-g', RG) or [])}
    for h in HOSTS:
        if h in have: print(h, 'already on the door'); continue
        r = az('containerapp', 'hostname', 'add', '-n', APP, '-g', RG, '--hostname', h, check=False); print(h, 'added' if '_error' not in (r or {}) else 'FAILED ' + r['_error'][-200:], flush=True)
if what == 'certs':
    have = certs(); ps = []
    for h in HOSTS:
        if h not in have: ps.append(az('containerapp', 'env', 'certificate', 'create', '-g', RG, '-n', EN, '--hostname', h, '--validation-method', 'TXT', '--certificate-name', cname(h), wait=False)); time.sleep(3)
    for _ in range(20):
        time.sleep(15); have = certs()
        if all(h in have and (have[h]['properties'].get('validationToken') or have[h]['properties'].get('provisioningState') == 'Succeeded') for h in HOSTS): break
    tok = {h: have[h]['properties'].get('validationToken') for h in HOSTS if h in have and have[h]['properties'].get('validationToken')}; json.dump(tok, open(H / 'cert-tokens.json', 'w'), indent=1)
    for h in HOSTS: print(h, (have.get(h) or {}).get('properties', {}).get('provisioningState', 'NOT REQUESTED'), 'token' if h in tok else 'no token')
if what == 'bind':
    have = certs(); bound = {d['name']: d.get('bindingType') for d in (az('containerapp', 'hostname', 'list', '-n', APP, '-g', RG) or [])}; pend = []
    for h in HOSTS:
        st = (have.get(h) or {}).get('properties', {}).get('provisioningState')
        if bound.get(h) == 'SniEnabled': print(h, 'bound'); continue
        if st != 'Succeeded': print(h, 'certificate', st); pend.append(h); continue
        r = az('containerapp', 'hostname', 'bind', '-n', APP, '-g', RG, '--environment', EN, '--hostname', h, '--certificate', have[h]['name'], check=False); print(h, 'bound now' if '_error' not in (r or {}) else 'FAILED ' + r['_error'][-200:], flush=True)
    print('pending:', pend); sys.exit(1 if pend else 0)
