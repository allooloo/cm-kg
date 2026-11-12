r"""iw_infra.py — IW-MOVE-01 step 1: Issuerwire's twin in the Allooloo subscription, France Central. Run by the agent under C:\ALLOOLOO\.azure. Idempotent:
each resource is read first and created only when absent. A step that fails stops the run. Nothing on the old side is touched.
  resource group   allooloo-iw-francecentral
  storage          allooloostgiwfrc (Standard_LRS, StorageV2, no public blob access) + the seven containers of the old account
  Key Vault        allooloo-iw-kv-frc (access policies; the signed-in operator sets, the apps read)
  PostgreSQL       allooloo-iw-pg-frc (flexible server, Burstable B1ms, v16, 32 GB — the old server's shape), admin amnadmin, database amn.
                   The admin password is MADE HERE (48 random bytes, url-safe), written straight into the new vault as pg-admin and handed to the
                   server's create call in the same process. It is never printed, logged or written to disk, and it is not the old password.
  environment      iw-env-francecentral (Container Apps, consumption)
Usage: python -X utf8 -I iw_infra.py"""
import json, os, subprocess, sys, time, secrets, urllib.request
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'; TENANT = '04a24e43-dc13-4578-950a-910db076a799'; LOC = 'francecentral'
RG = 'allooloo-iw-francecentral'; SA = 'allooloostgiwfrc'; KV = 'allooloo-iw-kv-frc'; PG = 'allooloo-iw-pg-frc'; CAE = 'iw-env-francecentral'
CONTAINERS = ['audit-log', 'ledger', 'pond', 'record', 'staging', 'statements', 'x402-receipts']
def say(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def az(*a, check=True, secret=False):
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode:
        if check: say('STOP: az', ' '.join(a[:4]), '' if secret else r.stderr[-300:]); sys.exit(1)
        return None
    return json.loads(r.stdout) if r.stdout.strip() else None
acct = az('account', 'show'); assert acct['tenantId'] == TENANT and acct['id'] == SUB, 'not the Allooloo tenant/subscription'
TAGS = ['estate=allooloo', 'product=issuerwire', 'order=IW-MOVE-01']
if not az('group', 'show', '-n', RG, check=False): az('group', 'create', '-n', RG, '-l', LOC, '--tags', *TAGS); say('resource group created', RG)
else: say('resource group present', RG)
if not az('storage', 'account', 'show', '-n', SA, '-g', RG, check=False):
    az('storage', 'account', 'create', '-n', SA, '-g', RG, '-l', LOC, '--sku', 'Standard_LRS', '--kind', 'StorageV2', '--access-tier', 'Hot', '--allow-blob-public-access', 'false', '--min-tls-version', 'TLS1_2', '--tags', *TAGS); say('storage account created', SA)
else: say('storage account present', SA)
key = az('storage', 'account', 'keys', 'list', '-n', SA, '-g', RG, secret=True)[0]['value']
for c in CONTAINERS: az('storage', 'container', 'create', '-n', c, '--account-name', SA, '--account-key', key, secret=True)
say('containers present', len(CONTAINERS))
if not az('keyvault', 'show', '-n', KV, '-g', RG, check=False):
    az('keyvault', 'create', '-n', KV, '-g', RG, '-l', LOC, '--enable-rbac-authorization', 'false', '--tags', *TAGS); say('key vault created', KV)
else: say('key vault present', KV)
if not az('postgres', 'flexible-server', 'show', '-n', PG, '-g', RG, check=False):
    have = az('keyvault', 'secret', 'show', '--vault-name', KV, '-n', 'pg-admin', check=False, secret=True)
    pw = have['value'] if have else 'Iw' + secrets.token_urlsafe(48)
    if not have: az('keyvault', 'secret', 'set', '--vault-name', KV, '-n', 'pg-admin', '--value', pw, '--query', 'id', secret=True); say('pg-admin made and placed in the new vault (never printed)')
    az('postgres', 'flexible-server', 'create', '-n', PG, '-g', RG, '-l', LOC, '--tier', 'Burstable', '--sku-name', 'Standard_B1ms', '--version', '16', '--storage-size', '32', '--admin-user', 'amnadmin', '--admin-password', pw, '--public-access', '0.0.0.0', '--yes', '--tags', *TAGS, secret=True); del pw
    say('postgres server created', PG)
else: say('postgres server present', PG)
ip = urllib.request.urlopen('https://api.ipify.org', timeout=20).read().decode().strip()
az('postgres', 'flexible-server', 'firewall-rule', 'create', '-g', RG, '-n', PG, '--rule-name', 'iw-move-01-operator', '--start-ip-address', ip, '--end-ip-address', ip, check=False); say('firewall: Azure services, and the operator address for the restore')
if not az('containerapp', 'env', 'show', '-n', CAE, '-g', RG, check=False): az('containerapp', 'env', 'create', '-n', CAE, '-g', RG, '-l', LOC, '--tags', *TAGS); say('environment created', CAE)
else: say('environment present', CAE)
e = az('containerapp', 'env', 'show', '-n', CAE, '-g', RG); say('environment', e['properties']['provisioningState'], 'default domain', e['properties']['defaultDomain'], 'verification id present', bool(e['properties'].get('customDomainConfiguration', {}).get('customDomainVerificationId')))
say('INFRA DONE')
