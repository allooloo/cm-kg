"""ORDER-019 item 1 — Cloudflare Origin CA on every regional door and Agent Card hostname.
Per hostname (CEO: one certificate per door and Agent Card hostname): private key + CSR (openssl) -> Origin CA certificate over the CF API (15 years)
-> PFX -> uploaded to the Container Apps environment as a certificate -> hostname added if missing and bound to that certificate
-> CNAME turned proxied (SSL Full (strict) on the zone). No managed certificates, no re-bind loops, no polling: one pass, states read once.
Usage: python origin_ca.py <cc> [cc ...]   Keys read in-process from AGENT KEYS (never printed). Private keys stay under the AZURE certs folder (git-ignored)."""
import json, os, secrets, subprocess, sys
import requests

TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
R = {'ca': 'canadacentral', 'uk': 'uksouth', 'au': 'australiaeast', 'sg': 'southeastasia', 'ch': 'switzerlandnorth', 'de': 'germanywestcentral',
     'fr': 'francecentral', 'nl': 'westeurope', 'jp': 'japaneast', 'kr': 'koreacentral', 'us': 'eastus'}
ZONES = {'ca': '4d2c6dc2f534dd8c013f6e66544eed4c', 'uk': '999f8cab6ae570a878379f0e37cd87b0', 'au': '8732370fd5742f40dba657be3eab5d37', 'sg': '0d4ae29fdde22945ffd2858bc2922576',
         'ch': '0ea4358fbd0c1dc5ccf069448ccefe48', 'de': '0e7b54741212fb036c2cf18b9392ed25', 'fr': '645c30886df97804e3b793399e303c2b', 'nl': 'e5a042d3df88b7e170d5225ecfacb008',
         'jp': 'f1c120f9d544c4af28bd6029ce071b96', 'kr': 'cd87134802ca140f4767253f39453ce1', 'us': '64516e94b82d13781980dff99c20c8b0'}
B = 'https://api.cloudflare.com/client/v4'
HERE = os.path.dirname(os.path.abspath(__file__)); LOGF = os.path.join(HERE, 'origin-ca.log')
def key(f): return open(rf'C:\ALLOOLOO\AGENT KEYS\{f}.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
CF = {'Authorization': 'Bearer ' + key('cloudflare')}       # DNS records + zone settings
CFD = {'Authorization': 'Bearer ' + key('cloudflare-origin-ca')}   # Origin CA token (Zone · SSL and Certificates · Edit), CEO Sept 12

def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True)
    open(LOGF, 'a', encoding='utf-8').write(__import__('time').strftime('%Y-%m-%d %H:%M ') + s + '\n')
def az(*a, check=True):
    r = subprocess.run(['az', *a, '-o', 'json'], capture_output=True, text=True, shell=True)
    if r.returncode and check: log('az error', ' '.join(a[:4]), (r.stderr or '')[-300:].replace('\n', ' ')); return None
    try: return json.loads(r.stdout or 'null')
    except Exception: return None
def cf(method, path, h, **kw):
    r = requests.request(method, B + path, headers=h, timeout=90, **kw)
    try: j = r.json()
    except Exception: j = {'success': r.ok, 'result': None, 'errors': [{'message': r.text[:200]}]}
    return j

acct = az('account', 'show')
if not acct or acct.get('tenantId') != TENANT or acct.get('id') != SUB: sys.exit('STOP: not the Allooloo tenant/subscription of record')

def region(cc):
    rg = f'allooloo-cmkg-{R[cc]}'; app = f'cmkg-door-{cc}'; zone = ZONES[cc]
    envf = os.path.join(HERE, f'env-{cc}.txt'); envn = open(envf).read().strip() if os.path.exists(envf) else f'cmkg-env-{R[cc]}'
    hosts = [f'mcp.{cc}-cm-kg.ai', f'agent.{cc}-cm-kg.ai']
    existing = az('containerapp', 'env', 'certificate', 'list', '-n', envn, '-g', rg, check=False) or []
    hn = {h.get('name'): h for h in (az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or [])}
    for h in hosts:
        tag = h.split('.')[0]; d = os.path.join(HERE, 'certs', cc, tag); os.makedirs(d, exist_ok=True)
        keyf, csrf, crtf, pfxf = [os.path.join(d, f'origin.{x}') for x in ('key', 'csr', 'pem', 'pfx')]
        certname = f'origin-{tag}-{cc}-2026-09-12'
        if not os.path.exists(keyf):
            subprocess.run(['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes', '-keyout', keyf, '-out', csrf, '-subj', f'/CN={h}/O=Allooloo Technologies Corp.'], capture_output=True, text=True)
        csr = open(csrf, encoding='utf-8').read()
        if not os.path.exists(crtf):
            j = cf('POST', '/certificates', CFD, json={'hostnames': [h], 'requested_validity': 5475, 'request_type': 'origin-rsa', 'csr': csr})
            if not j.get('success'): log(f'[{cc}] Origin CA refused for {h}:', (j.get('errors') or [{}])[0].get('message', '')[:200]); continue
            open(crtf, 'w', encoding='utf-8').write(j['result']['certificate']); log(f'[{cc}] Origin CA certificate issued for {h} (id {j["result"]["id"][:8]}…, expires {str(j["result"].get("expires_on", ""))[:10]})')
        pw = secrets.token_urlsafe(16)
        subprocess.run(['openssl', 'pkcs12', '-export', '-inkey', keyf, '-in', crtf, '-out', pfxf, '-passout', 'pass:' + pw], capture_output=True, text=True)
        if not [c for c in existing if c.get('name') == certname]:
            up = az('containerapp', 'env', 'certificate', 'upload', '-n', envn, '-g', rg, '--certificate-file', pfxf, '--password', pw, '--certificate-name', certname)
            if not up: log(f'[{cc}] certificate upload failed for {h}'); continue
            log(f'[{cc}] certificate {certname} uploaded to {envn}')
        else: log(f'[{cc}] certificate {certname} already on {envn}')
        if h not in hn:
            a = az('containerapp', 'hostname', 'add', '--hostname', h, '-n', app, '-g', rg, check=False); log(f'[{cc}] hostname {h} add attempted: {"ok" if a is not None else "refused"}')
        b = az('containerapp', 'hostname', 'bind', '--hostname', h, '-n', app, '-g', rg, '--environment', envn, '--certificate', certname, check=False)
        log(f'[{cc}] bind {h} -> {certname}: {"ok" if b is not None else "refused"}')
    hn2 = {h.get('name'): h.get('bindingType') for h in (az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or [])}
    # 5. flip orange where SniEnabled; SSL strict on the zone
    for h in hosts:
        state = hn2.get(h)
        recs = cf('GET', f'/zones/{zone}/dns_records?name={h}', CF).get('result') or []
        for rec in recs:
            if rec['type'] == 'CNAME' and state == 'SniEnabled' and not rec.get('proxied'):
                u = cf('PATCH', f'/zones/{zone}/dns_records/{rec["id"]}', CF, json={'proxied': True}); log(f'[{cc}] {h}: binding {state}; CNAME proxied: {u.get("success")}')
            elif rec['type'] == 'CNAME': log(f'[{cc}] {h}: binding {state}; CNAME proxied already {rec.get("proxied")}' if state == 'SniEnabled' else f'[{cc}] {h}: binding {state} — left grey (reported, not retried)')
    s = cf('PATCH', f'/zones/{zone}/settings/ssl', CF, json={'value': 'strict'}); log(f'[{cc}] zone SSL strict: {s.get("success")}')

for cc in sys.argv[1:] or list(R): region(cc)
