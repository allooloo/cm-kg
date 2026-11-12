r"""iw_apps.py — IW-MOVE-01 step 1: Issuerwire's door and its eight Ops Agents jobs on the Allooloo side (allooloo-iw-francecentral, iw-env-francecentral).
Every app runs as the one identity iw-identity; every secret is a Key Vault reference into allooloo-iw-kv-frc (no value passes through here).
  door   iw-door       image iw-door:iwmove01 by digest, port 8000, 0.5 CPU / 1 Gi, 1..3 replicas — as the old door, with the new key ids and issuer
  jobs   iw-<x>-rail   the research fleet image by digest; each runs the Ops Agents build its twin runs on the old side (/job/iw/<build>/ops/job_amn.py);
                       trigger Manual — Issuerwire's schedule is the one weekly job, nothing here has a clock
`mode` staging -> STORAGE_CONTAINER=staging (the Ops Agents' own dry-run: staging container, schema ops_staging, no ledger event, ark off) and the three
door hosts pointed at the twin's own door; `mode` live -> pond, hosts as published. Needs (CEO's hand, once): iw-identity may read secrets in the vault and
pull from the registry. Usage: python -X utf8 -I iw_apps.py door | jobs staging|live | show"""
import json, os, subprocess, sys, pathlib
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
H = pathlib.Path(__file__).parent; RG = 'allooloo-iw-francecentral'; ENVN = 'iw-env-francecentral'; KV = 'https://allooloo-iw-kv-frc.vault.azure.net/secrets/'; ACR = 'allooloocmkg.azurecr.io'
ID = json.load(open(H / 'iw-identity.json'))['id']; DOOR_IMG = json.load(open(H / 'door-image.json'))['image']; FLEET = json.load(open(H / 'fleet-image.json'))['image']
OLDJ = {j['name']: j for j in json.load(open(H / 'old-jobs.json'))}; OLDD = json.load(open(H / 'old-door.json'))
PG = 'allooloo-iw-pg-frc.postgres.database.azure.com'; SA = 'allooloostgiwfrc'; KID = 'iw-2026-11'; XKID = 'iw-x402-receipts-2026-11'
def az(*a, check=True):
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode:
        if check: sys.exit(f'STOP az {" ".join(a[:4])}: {r.stderr[-900:]}')
        return None
    return json.loads(r.stdout) if r.stdout.strip() else None
sec = lambda *names: [f'{n}=keyvaultref:{KV}{n},identityref:{ID}' for n in names]
BUILD = {'iw01-10262245': 'iw01', 'nightly02-11011600': 'nightly02', 'fix-20261103': 'fix'}
what = sys.argv[1]
if what == 'door':
    fq = None
    old = {e['name']: e.get('value') for e in OLDD['properties']['template']['containers'][0]['env'] if not e.get('secretRef')}
    env = [f'PGHOST={PG}', 'PGDATABASE=amn', 'PGUSER=amnadmin', f'STORAGE_ACCOUNT={SA}', f"ACCESS_TEAM={old['ACCESS_TEAM']}", f"X402_FACILITATOR_URL={old['X402_FACILITATOR_URL']}", f"X402_AMOUNT={old['X402_AMOUNT']}", 'PORT=8000',
           'IMAGE_TAG=iwmove01', f"ACCESS_AUD={old['ACCESS_AUD']}", f'AMN_KID={KID}', f'AMN_X402_KID={XKID}', 'AMN_RECEIPT_ISSUER=allooloo',
           'PGPASSWORD=secretref:pg-admin', 'AMN_SIGN_KEY_PEM=secretref:iw-sign-key', 'AMN_X402_KEY_PEM=secretref:iw-x402-key', 'AZURE_STORAGE_KEY=secretref:storage-key', 'X402_FACILITATOR_AUTH=secretref:x402-facilitator-auth',
           'X402_FACILITATOR_KEY_ID=secretref:x402-facilitator-key-id', 'X402_PAY_TO=secretref:x402-pay-to', 'X402_PAY_TO_OUSD=secretref:x402-pay-to-ousd']
    if az('containerapp', 'show', '-n', 'iw-door', '-g', RG, check=False): print('iw-door exists (kept)')
    else:
        az('containerapp', 'create', '-n', 'iw-door', '-g', RG, '--environment', ENVN, '--image', DOOR_IMG, '--user-assigned', ID, '--registry-server', ACR, '--registry-identity', ID,
           '--ingress', 'external', '--target-port', '8000', '--transport', 'auto', '--cpu', '0.5', '--memory', '1Gi', '--min-replicas', '1', '--max-replicas', '3',
           '--secrets', *sec('pg-admin', 'iw-sign-key', 'iw-x402-key', 'storage-key', 'x402-facilitator-auth', 'x402-facilitator-key-id', 'x402-pay-to', 'x402-pay-to-ousd'), '--env-vars', *env)
    d = az('containerapp', 'show', '-n', 'iw-door', '-g', RG); fq = d['properties']['configuration']['ingress']['fqdn']; json.dump({'fqdn': fq, 'image': DOOR_IMG}, open(H / 'new-door.json', 'w')); print('iw-door', fq, d['properties']['runningStatus'])
if what == 'jobs':
    mode = sys.argv[2]; fq = json.load(open(H / 'new-door.json'))['fqdn']; out = {}
    for oname, j in OLDJ.items():
        x = oname[len('amn-'):-len('-rail')]; name = f'iw-{x}-rail'; k = j['properties']['template']['containers'][0]; c = j['properties']['configuration']; old = {e['name']: e.get('value') for e in k['env'] if not e.get('secretRef')}; build = BUILD[old['IMAGE_TAG']]
        env = {q: v for q, v in old.items() if q not in ('PGHOST', 'STORAGE_ACCOUNT', 'STORAGE_CONTAINER', 'IMAGE_TAG')}
        env.update({'PGHOST': PG, 'STORAGE_ACCOUNT': SA, 'STORAGE_CONTAINER': 'pond' if mode == 'live' else 'staging', 'IMAGE_TAG': f"iwmove01-{old['IMAGE_TAG']}", 'AMN_KID': KID, 'AMN_X402_KID': XKID})
        if mode != 'live': env.update({'AMN_DOOR': f'https://{fq}', 'AMN_HUB': f'https://{fq}', 'AMN_BRAND': f'https://{fq}'})
        sr = {'PGPASSWORD': 'pg-admin', 'AMN_SIGN_KEY_PEM': 'iw-sign-key', 'AZURE_STORAGE_KEY': 'storage-key', 'AWS_ACCESS_KEY_ID': 'ark-aws-key-id', 'AWS_SECRET_ACCESS_KEY': 'ark-aws-secret'}
        if any(e['name'] == 'COMPANIES_HOUSE_KEY' for e in k['env']): sr['COMPANIES_HOUSE_KEY'] = 'companieshouse-key'
        envs = [f'{q}={v}' for q, v in env.items()] + [f'{q}=secretref:{v}' for q, v in sr.items()]
        if az('containerapp', 'job', 'show', '-n', name, '-g', RG, check=False):
            az('containerapp', 'job', 'update', '-n', name, '-g', RG, '--set-env-vars', *envs, *([] if mode != 'live' else []))
            if mode == 'live': az('containerapp', 'job', 'update', '-n', name, '-g', RG, '--remove-env-vars', 'AMN_DOOR', 'AMN_HUB', 'AMN_BRAND', check=False)
            state = 'updated'
        else:
            az('containerapp', 'job', 'create', '-n', name, '-g', RG, '--environment', ENVN, '--trigger-type', 'Manual', '--replica-timeout', str(c['replicaTimeout']), '--replica-retry-limit', '0', '--parallelism', '1', '--replica-completion-count', '1',
               '--image', FLEET, '--user-assigned', ID, '--registry-server', ACR, '--registry-identity', ID, '--cpu', str(k['resources']['cpu']), '--memory', k['resources']['memory'],
               '--command', '/usr/local/bin/python3', f'/job/iw/{build}/ops/job_amn.py', '--secrets', *sec(*sorted(set(sr.values()))), '--env-vars', *envs)
            state = 'created'
        out[name] = {'twin_of': oname, 'build': build, 'mode': mode, 'old_cron': (c.get('scheduleTriggerConfig') or {}).get('cronExpression'), 'timeout': c['replicaTimeout']}; print(name, state, build, mode, flush=True)
    json.dump(out, open(H / 'new-jobs.json', 'w'), indent=1)
if what == 'show':
    for j in az('containerapp', 'job', 'list', '-g', RG) or []:
        k = j['properties']['template']['containers'][0]; print(j['name'], j['properties']['configuration']['triggerType'], k['image'][-20:], k.get('command'), [e.get('value') for e in k['env'] if e['name'] == 'STORAGE_CONTAINER'])
