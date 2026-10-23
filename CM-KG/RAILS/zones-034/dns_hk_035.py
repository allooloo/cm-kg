"""ORDER-035 — DNS for the Hong Kong door hostnames on hk-cm-kg.ai: asuid.<host> TXT (the Container Apps environment's domain verification id) and a DNS-only
CNAME <host> → the app's FQDN, for mcp.hk-cm-kg.ai and agent.hk-cm-kg.ai. Existing records at a name are reported and left (nothing overwritten).
origin_ca.py hk then binds the Origin CA certificate and turns the CNAMEs orange. Token cloudflare.txt in-process; Azure read under the Allooloo tenant."""
import json, os, subprocess, urllib.request, urllib.error
ZONE = 'eccfebad4729da2b3ab6411bf739acb4'; RG = 'allooloo-cmkg-eastasia'; APP = 'cmkg-door-hk'
TOK = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip()
env = {**os.environ, 'AZURE_CONFIG_DIR': r'C:\ALLOOLOO\.azure'}
def az(*a): return json.loads(subprocess.run(['az', *a, '-o', 'json'], capture_output=True, text=True, env=env, shell=True).stdout or 'null')
acct = az('account', 'show')
if acct['tenantId'] != '04a24e43-dc13-4578-950a-910db076a799': raise SystemExit('STOP: tenant')
fqdn = az('containerapp', 'show', '-n', APP, '-g', RG)['properties']['configuration']['ingress']['fqdn']
envn = open(r'C:\ALLOOLOO\AZURE\env-hk.txt').read().strip()
vid = az('containerapp', 'env', 'show', '-n', envn, '-g', RG)['properties']['customDomainConfiguration']['customDomainVerificationId']
def cf(m, p, b=None):
    r = urllib.request.Request('https://api.cloudflare.com/client/v4' + p, data=json.dumps(b).encode() if b else None, method=m, headers={'Authorization': 'Bearer ' + TOK, 'content-type': 'application/json'})
    try: return json.load(urllib.request.urlopen(r, timeout=60))
    except urllib.error.HTTPError as e: return json.load(e)
for h in ('mcp.hk-cm-kg.ai', 'agent.hk-cm-kg.ai'):
    have = cf('GET', f'/zones/{ZONE}/dns_records?name={h}').get('result') or []
    if have: print(h, 'present:', [(x['type'], x['content'], x['proxied']) for x in have], '— left as is')
    else: r = cf('POST', f'/zones/{ZONE}/dns_records', {'type': 'CNAME', 'name': h, 'content': fqdn, 'proxied': False, 'ttl': 300, 'comment': 'ORDER-035 hk door (DNS-only until the Origin CA bind)'}); print(h, 'CNAME', fqdn, 'created' if r.get('success') else r.get('errors'))
    t = f'asuid.{h}'; have = cf('GET', f'/zones/{ZONE}/dns_records?name={t}&type=TXT').get('result') or []
    if any(x['content'].strip('"') == vid for x in have): print(t, 'TXT present')
    else: r = cf('POST', f'/zones/{ZONE}/dns_records', {'type': 'TXT', 'name': t, 'content': vid, 'ttl': 300, 'comment': 'ORDER-035 Container Apps domain verification'}); print(t, 'TXT created' if r.get('success') else r.get('errors'))
