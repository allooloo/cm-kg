r"""bind_eu_doors.py — DAY ORDER 5 ZONES-01 (2026-10-24): the European doors answer on the EU regime zone (door name rule of record).
Per environment that holds a European door: the Origin CA certificate for eu-cm-kg.ai (and lu-cm-kg.ai in West Europe) uploaded once (name origin-<zone>).
Per door: hostname <cc>.eu-cm-kg.ai added and bound with that certificate (Luxembourg also mcp./agent.lu-cm-kg.ai with its own zone's certificate);
then the door moves to cmkg-door 0.15.0 with PUBLIC_HOST and AGENT_CARD_URL naming the zone door. The Container Apps hostname keeps answering.
Requires dns_eu_doors.py applied first (CNAME + asuid TXT). Usage: python -X utf8 -I bind_eu_doors.py <cc> ... | all"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); D = json.load(open(os.path.join(HERE, 'doors-2026-10-24.json')))
SEL = list(D) if sys.argv[1:] == ['all'] else sys.argv[1:]
env = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1')
AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
def az(*a):
    r = subprocess.run([AZ, *a, '-o', 'json'], capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
    if r.returncode: return {'error': (r.stderr or '').strip().splitlines()[-1:]}
    try: return json.loads(r.stdout or 'null')
    except Exception: return r.stdout
def cert(env_rg, env_name, zone):
    name = 'origin-' + zone.replace('.', '-')
    have = az('containerapp', 'env', 'certificate', 'list', '-g', env_rg, '-n', env_name)
    for c in (have if isinstance(have, list) else []):
        if c.get('name') == name: return c['id']
    d = os.path.join(r'C:\ALLOOLOO\AZURE\certs', zone); pw = open(os.path.join(d, 'pfx-pass.txt')).read().strip()
    r = az('containerapp', 'env', 'certificate', 'upload', '-g', env_rg, '-n', env_name, '--certificate-file', os.path.join(d, 'origin.pfx'), '--password', pw, '--certificate-name', name)
    return r.get('id') if isinstance(r, dict) else None
log = {}
for cc in SEL:
    d = D[cc]; out = log[cc] = {}
    binds = [(f'{cc}.eu-cm-kg.ai', 'eu-cm-kg.ai')] + ([('mcp.lu-cm-kg.ai', 'lu-cm-kg.ai'), ('agent.lu-cm-kg.ai', 'lu-cm-kg.ai')] if cc == 'lu' else [])
    have = az('containerapp', 'hostname', 'list', '-n', d['app'], '-g', d['rg'])
    bound = {h['name']: h.get('bindingType') for h in (have if isinstance(have, list) else [])}
    for host, zone in binds:
        cid = cert(d['env_rg'], d['env'], zone)
        if not cid: out[host] = 'certificate upload failed'; print(cc, host, out[host]); continue
        if bound.get(host) == 'SniEnabled': out[host] = 'bound (already)'; print(cc, host, out[host]); continue
        if host not in bound: az('containerapp', 'hostname', 'add', '-n', d['app'], '-g', d['rg'], '--hostname', host)
        r = az('containerapp', 'hostname', 'bind', '-n', d['app'], '-g', d['rg'], '--hostname', host, '--certificate', cid, '--validation-method', 'TXT')
        out[host] = 'bound' if not (isinstance(r, dict) and r.get('error')) else r['error']; print(cc, host, out[host])
    ph = 'mcp.lu-cm-kg.ai' if cc == 'lu' else f'{cc}.eu-cm-kg.ai'
    card = 'https://agent.lu-cm-kg.ai/.well-known/agent-card.json' if cc == 'lu' else f'https://{cc}.eu-cm-kg.ai/.well-known/agent-card.json'
    vars_ = ['PUBLIC_HOST=' + ph, 'AGENT_CARD_URL=' + card] + (['AGENT_HOST=agent.lu-cm-kg.ai'] if cc == 'lu' else [f'AGENT_HOST={cc}.eu-cm-kg.ai'])
    r = az('containerapp', 'update', '-n', d['app'], '-g', d['rg'], '--image', 'allooloocmkg.azurecr.io/cmkg-door:0.15.0', '--set-env-vars', *vars_, '--query', 'properties.latestRevisionName')
    out['revision'] = r; print(cc, 'door 0.15.0', r)
json.dump(log, open(os.path.join(HERE, f'bind-eu-doors-{"_".join(SEL) if len(SEL) < 4 else "all"}-2026-10-24.json'), 'w'), indent=1)
