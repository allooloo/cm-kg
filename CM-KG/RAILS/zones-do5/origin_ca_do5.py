r"""origin_ca_do5.py — DAY ORDER 5 ZONES-01 (2026-10-24): one Cloudflare Origin CA certificate per cm-kg zone that has (or will have) a Container App behind it.
Hostnames: <zone> and *.<zone> (one subdomain level: mcp./agent. on own zones; <cc>. on eu-cm-kg.ai). Key + CSR made here with openssl, kept under
C:\ALLOOLOO\AZURE\certs\<zone>\ (git-ignored, never printed); the PFX for Container Apps is written beside with a random password kept in pfx-pass.txt there.
Origin CA key read in-process from AGENT KEYS\cloudflare-origin-ca.txt. A zone already holding origin.pem is skipped. Usage: python -X utf8 -I origin_ca_do5.py <zone> ...|all"""
import sys, os, json, subprocess, secrets, requests
ZONES = 'eu-cm-kg.ai lu-cm-kg.ai ky-cm-kg.ai bm-cm-kg.ai je-cm-kg.ai in-cm-kg.ai tw-cm-kg.ai sa-cm-kg.ai ae-cm-kg.ai br-cm-kg.ai mx-cm-kg.ai'.split()
SEL = ZONES if sys.argv[1:] == ['all'] else sys.argv[1:]
T = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-origin-ca.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
log = {}
for z in SEL:
    d = os.path.join(r'C:\ALLOOLOO\AZURE\certs', z); os.makedirs(d, exist_ok=True)
    kf, csrf, pf, xf, pw = (os.path.join(d, x) for x in ('origin.key', 'origin.csr', 'origin.pem', 'origin.pfx', 'pfx-pass.txt'))
    if not os.path.exists(pf):
        subprocess.run(['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes', '-keyout', kf, '-out', csrf, '-subj', f'/CN={z}'], check=True, capture_output=True)
        r = requests.post('https://api.cloudflare.com/client/v4/certificates', headers={'Authorization': 'Bearer ' + T},
                          json={'hostnames': [z, '*.' + z], 'requested_validity': 5475, 'request_type': 'origin-rsa', 'csr': open(csrf, encoding='utf-8').read()}, timeout=60).json()
        if not r.get('success'): print(z, 'REFUSED', r.get('errors')); log[z] = {'refused': r.get('errors')}; continue
        open(pf, 'w', encoding='utf-8').write(r['result']['certificate'])
        json.dump({'id': r['result']['id'], 'expires_on': r['result']['expires_on'], 'hostnames': r['result']['hostnames']}, open(os.path.join(d, 'origin-ca.json'), 'w'), indent=1)
    if not os.path.exists(xf):
        open(pw, 'w').write(secrets.token_urlsafe(24))
        subprocess.run(['openssl', 'pkcs12', '-export', '-out', xf, '-inkey', kf, '-in', pf, '-passout', 'file:' + pw], check=True, capture_output=True)
    log[z] = json.load(open(os.path.join(d, 'origin-ca.json')))
    print(z, log[z]['hostnames'], log[z]['expires_on'])
json.dump(log, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'origin-ca-2026-10-24.json'), 'w'), indent=1)
