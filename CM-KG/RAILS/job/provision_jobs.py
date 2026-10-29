r"""ORDER-031 — the twelve Container Apps Jobs (eleven nodes + apex), create-only, idempotent, nothing deleted.
  python provision_jobs.py create <image tag> [cc ...]   create (or bring to the image) the node jobs; the US job is updated in place (same image, same schedule, nothing else)
  python provision_jobs.py apex <image tag>              the apex job in East US
  python provision_jobs.py arm [cc ...|apex]             set the real cron (30 20 * * 5 UTC; apex 30 3 * * 6 UTC = Friday 23:30 Toronto); until then the jobs carry the parked cron 0 0 31 2 * (never fires)
  python provision_jobs.py ark-on <cc|apex> <bucket> <aws region>   enable the ark write on a job after the CEO attaches the policy
  python provision_jobs.py digest <image tag>            ORDER-037: cmkg-apex-digest (20 14 * * * UTC) + cmkg-apex-week (0 13,14 * * 6 UTC) on the apex image, job_digest.py
  python provision_jobs.py digest-sas                    ORDER-037: wire issuerwire-pond-sas (the CEO places it in allooloo-cmkg-kv-apex) into cmkg-apex-digest
  python provision_jobs.py status
Identity: each job has a system-assigned managed identity. It pulls the image from the registry (AcrPull), reads its vault (Key Vault Secrets User)
and its node's resource group (Contributor: storage key, door restart). The apex identity gets Contributor on every node group + the shared group.
Secrets are Key Vault references; nothing baked, nothing in env files, no registry password handled here. Tenant guard as the rails."""
import os, sys, json, subprocess, time
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'; ACR = 'allooloocmkg'; ACR_SERVER = 'allooloocmkg.azurecr.io'
NODES = {'nl': 'westeurope', 'ch': 'switzerlandnorth', 'fr': 'francecentral', 'de': 'germanywestcentral', 'sg': 'southeastasia', 'au': 'australiaeast', 'uk': 'uksouth', 'ca': 'canadacentral', 'jp': 'japaneast', 'kr': 'koreacentral', 'us': 'eastus', 'hk': 'eastasia'}   # hk: ORDER-035 (2026-10-22)
ARK = {'hk': 'ap-east-1', 'nl': 'eu-central-1', 'ch': 'eu-central-2', 'fr': 'eu-west-3', 'de': 'eu-central-1', 'sg': 'ap-southeast-1', 'au': 'ap-southeast-2', 'uk': 'eu-west-2', 'ca': 'ca-central-1', 'jp': 'ap-northeast-1', 'kr': 'ap-northeast-2', 'us': 'us-east-1', 'apex': 'us-east-1'}
PARKED = '0 0 31 2 *'; CRON = '30 20 * * 5'; CRON_APEX = '30 3 * * 6'   # the weekly clock of record until ORDER-036
# ORDER-036 NIGHTLY (2026-10-22): 02:00 in each region's local STANDARD time as a fixed UTC cron, pinned across clock changes (never moved for daylight time);
# the apex after the last region (Canada and the United States fire 07:00 UTC; the apex 12:30 UTC); seven nights a week
NIGHTLY = {'au': '0 16 * * *', 'jp': '0 17 * * *', 'kr': '0 17 * * *', 'sg': '0 18 * * *', 'hk': '0 18 * * *', 'nl': '0 1 * * *', 'ch': '0 1 * * *', 'fr': '0 1 * * *', 'de': '0 1 * * *', 'uk': '0 2 * * *', 'ca': '0 7 * * *', 'us': '0 7 * * *', 'apex': '30 12 * * *'}
KV = {'hk': 'allooloo-cmkg-kv-sg'}   # hk reads the Singapore vault's lab keys by reference (no key value copied to a new vault); every other node its own
# NODE-EU-01…14 (DAY ORDER 4, 2026-10-24): the European nodes. Region = the Container Apps region in the country, else the nearest (flagged in the report);
# nightly 02:00 local standard time as a fixed UTC cron; ark region in or nearest the country; lab keys by reference from the nearest existing vault (no key copied)
EU_NODES = {'it': 'italynorth', 'es': 'spaincentral', 'se': 'swedencentral', 'dk': 'swedencentral', 'no': 'norwayeast', 'fi': 'swedencentral', 'be': 'belgiumcentral', 'ie': 'northeurope',
            'at': 'austriaeast', 'pl': 'polandcentral', 'pt': 'spaincentral', 'lu': 'belgiumcentral', 'gr': 'italynorth', 'cz': 'austriaeast'}
EU_ARK = {'it': 'eu-south-1', 'es': 'eu-south-2', 'se': 'eu-north-1', 'dk': 'eu-north-1', 'no': 'eu-north-1', 'fi': 'eu-north-1', 'be': 'eu-west-3', 'ie': 'eu-west-1', 'at': 'eu-central-2', 'pl': 'eu-central-1', 'pt': 'eu-south-2', 'lu': 'eu-west-3', 'gr': 'eu-south-1', 'cz': 'eu-central-1'}
EU_STD = {'it': 1, 'es': 1, 'se': 1, 'dk': 1, 'no': 1, 'fi': 2, 'be': 1, 'ie': 0, 'at': 1, 'pl': 1, 'pt': 0, 'lu': 1, 'gr': 2, 'cz': 1}
EU_KV = {'it': 'allooloo-cmkg-kv-fr', 'es': 'allooloo-cmkg-kv-fr', 'se': 'allooloo-cmkg-kv-nl', 'dk': 'allooloo-cmkg-kv-nl', 'no': 'allooloo-cmkg-kv-nl', 'fi': 'allooloo-cmkg-kv-nl', 'be': 'allooloo-cmkg-kv-nl', 'ie': 'allooloo-cmkg-kv-uk',
         'at': 'allooloo-cmkg-kv-de', 'pl': 'allooloo-cmkg-kv-de', 'pt': 'allooloo-cmkg-kv-fr', 'lu': 'allooloo-cmkg-kv-nl', 'gr': 'allooloo-cmkg-kv-fr', 'cz': 'allooloo-cmkg-kv-de'}
for _cc, _r in EU_NODES.items():
    NODES[_cc] = _r; ARK[_cc] = EU_ARK[_cc]; NIGHTLY[_cc] = f"0 {(2 - EU_STD[_cc]) % 24} * * *"; KV[_cc] = EU_KV[_cc]
ROW_NODES = {'ky': 'eastus', 'bm': 'eastus', 'je': 'uksouth', 'in': 'centralindia', 'tw': 'eastasia', 'sa': 'qatarcentral', 'ae': 'uaenorth', 'br': 'brazilsouth', 'mx': 'mexicocentral'}   # NODE-ROW (DAY ORDER 5, 2026-10-24)
ROW_ARK = {'ky': 'us-east-1', 'bm': 'us-east-1', 'je': 'eu-west-2', 'in': 'ap-south-1', 'tw': 'ap-east-2', 'sa': 'me-central-1', 'ae': 'me-central-1', 'br': 'sa-east-1', 'mx': 'mx-central-1'}
ROW_STD = {'ky': -5, 'bm': -4, 'je': 0, 'in': 5.5, 'tw': 8, 'sa': 3, 'ae': 4, 'br': -3, 'mx': -6}
ROW_KV = {'ky': 'allooloo-cmkg-kv-us', 'bm': 'allooloo-cmkg-kv-us', 'je': 'allooloo-cmkg-kv-uk', 'in': 'allooloo-cmkg-kv-sg', 'tw': 'allooloo-cmkg-kv-sg', 'sa': 'allooloo-cmkg-kv-fr', 'ae': 'allooloo-cmkg-kv-fr', 'br': 'allooloo-cmkg-kv-us', 'mx': 'allooloo-cmkg-kv-us'}
for _cc, _r in ROW_NODES.items():
    _m = int(round((2 - ROW_STD[_cc]) * 60)) % 1440; NODES[_cc] = _r; ARK[_cc] = ROW_ARK[_cc]; NIGHTLY[_cc] = f"{_m % 60} {_m // 60} * * *"; KV[_cc] = ROW_KV[_cc]
ENV_HOST = {'be': 'westeurope', 'lu': 'westeurope', 'ie': 'westeurope', 'at': 'germanywestcentral', 'pl': 'germanywestcentral', 'cz': 'germanywestcentral', 'ky': 'eastus', 'bm': 'eastus', 'je': 'uksouth', 'in': 'southeastasia', 'tw': 'eastasia', 'sa': 'italynorth', 'ae': 'italynorth', 'br': 'eastus', 'mx': 'eastus'}   # NODE-EU 2026-10-24: environment quota reached; door + job in the nearest existing environment, store in the node's region
# ENUM-01 (DAY ORDER 6, 2026-10-25): region / ark / nightly / vault stay explicit per market (policy and infrastructure lines), but the jobs a run touches by
# default are the roster's live entries (never a market that is only in a map — sa is a policy line, not a node), and the rail refuses when a roster entry has no
# line in a map (the gap is named). The roster's store region must match the map's.
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import roster   # ENUM-01 (DAY ORDER 6): the roster of record
ROSTER_CC = roster.codes()
for _name, _m in (('region (NODES)', NODES), ('ark region (ARK)', ARK), ('nightly cron (NIGHTLY)', NIGHTLY)): roster.require(_name, _m, ROSTER_CC)
_bad = [c for c in ROSTER_CC if roster.region(c) and roster.region(c) != NODES[c]]
if _bad: raise SystemExit('ROSTER POLICY GAP · store region differs from the roster for: ' + ', '.join(_bad) + ' — rail refused')
LAB = ['tavily', 'grok', 'perplexity', 'mistral', 'gemini', 'chatgpt', 'claude', 'companieshouse', 'dart', 'edinet']
ENVKEY = {'tavily': 'TAVILY_API_KEY', 'grok': 'XAI_API_KEY', 'perplexity': 'PERPLEXITY_API_KEY', 'mistral': 'MISTRAL_API_KEY', 'gemini': 'GEMINI_API_KEY', 'chatgpt': 'OPENAI_API_KEY', 'claude': 'ANTHROPIC_API_KEY', 'companieshouse': 'COMPANIESHOUSE_API_KEY', 'dart': 'DART_API_KEY', 'edinet': 'EDINET_API_KEY'}
def az(*a, raw=False, check=True):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=(os.name == 'nt'))
    if p.returncode != 0:
        if check: raise SystemExit(f"az {' '.join(str(x) for x in a[:5])} failed: {(p.stderr or p.stdout)[-500:]}")
        return None
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
def log(*a): print(*a, flush=True)
acct = az('account', 'show')
if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
cmd = sys.argv[1]
ACR_ID = az('acr', 'show', '-n', ACR, '--query', 'id', '-o', 'tsv', raw=True)
def env_name(rg):
    for e in az('containerapp', 'env', 'list', '-g', rg):
        if e['properties']['provisioningState'] == 'Succeeded': return e['name']
    raise SystemExit(f'no environment in {rg}')
def assign(role, pid, scope):
    for i in range(8):
        r = az('role', 'assignment', 'create', '--role', role, '--assignee-object-id', pid, '--assignee-principal-type', 'ServicePrincipal', '--scope', scope, check=False)
        if r is not None: return True
        time.sleep(15)   # a new identity takes a moment to be visible to RBAC
    return False
def ensure_identity_roles(job, rg, kv, extra_rgs=()):
    pid = az('containerapp', 'job', 'show', '-n', job, '-g', rg, '--query', 'identity.principalId', '-o', 'tsv', raw=True)
    if not pid or pid == 'None':
        az('containerapp', 'job', 'identity', 'assign', '-n', job, '-g', rg, '--system-assigned'); time.sleep(10)
        pid = az('containerapp', 'job', 'show', '-n', job, '-g', rg, '--query', 'identity.principalId', '-o', 'tsv', raw=True)
    kvid = az('keyvault', 'show', '-n', kv, '--query', 'id', '-o', 'tsv', raw=True)   # (hk: the Singapore vault, by reference)
    roles = [('AcrPull', ACR_ID), ('Key Vault Secrets User', kvid)] + [('Contributor', az('group', 'show', '-n', g, '--query', 'id', '-o', 'tsv', raw=True)) for g in [rg, *extra_rgs]]
    for role, scope in roles: log(f"  {job}: {role} on {scope.split('/')[-1]} {'ok' if assign(role, pid, scope) else 'FAILED'}")
    return pid
def kv_secrets(job, rg, kv, names):
    az('containerapp', 'job', 'secret', 'set', '-n', job, '-g', rg, '--secrets', *[f'{n}=keyvaultref:https://{kv}.vault.azure.net/secrets/{n},identityref:system' for n in names])
def set_env(job, rg, pairs): az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--set-env-vars', *pairs)
if cmd == 'create':
    tag = sys.argv[2]; ccs = sys.argv[3:] or list(ROSTER_CC); image = f'{ACR_SERVER}/cmkg-sweep:{tag}'
    for cc in ccs:
        reg = NODES[cc]; rg = f'allooloo-cmkg-{reg}'; job = f'cmkg-{cc}-rail'; kv = KV.get(cc, f'allooloo-cmkg-kv-{cc}'); sa = f'allooloocmkg{cc}pond'
        base_env = [f'NODE_CC={cc}', f'REGION={reg}', f'STORAGE_ACCOUNT={sa}', 'STORAGE_CONTAINER=pond', 'DOOR_RESTART=1', 'ARK_ENABLED=0', f'ARK_BUCKET=allooloo-ark-{cc}-cm-kg', f'ARK_REGION={ARK[cc]}', f'IMAGE_TAG={tag}', 'CONTACT=developers@allooloo.ai', 'PPLX_MAX=6000']
        ex = az('containerapp', 'job', 'show', '-n', job, '-g', rg, check=False)
        if ex:
            log(f"{job}: present ({ex['properties']['configuration']['triggerType']}, {ex['properties']['template']['containers'][0]['image']}) -> image {image}")
            if cc == 'us': az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--set-env-vars', *base_env)   # its registry credential already stands
            else: az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--set-env-vars', *base_env)   # the image follows once the registry is bound to the identity (below)
            if cc == 'us' and ex['properties']['configuration']['triggerType'] != 'Schedule':   # the US job comes to the same image and schedule, nothing else
                r = az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--trigger-type', 'Schedule', '--cron-expression', PARKED, check=False)
                log(f'  {job}: trigger -> Schedule (parked)' if r is not None else f'  {job}: trigger type not changeable on update (left Manual; flagged for the report)')
        else:
            # the pull by identity cannot be validated before the identity holds AcrPull: create on the CLI's default image, then roles, then registry + image
            az('containerapp', 'job', 'create', '-n', job, '-g', rg, '--environment', (az('containerapp', 'env', 'list', '-g', f'allooloo-cmkg-{ENV_HOST[cc]}', '--query', "[?properties.provisioningState=='Succeeded'].id | [0]", '-o', 'tsv', raw=True) if cc in ENV_HOST else env_name(rg)), '--trigger-type', 'Schedule', '--cron-expression', PARKED, '--replica-timeout', '36000', '--replica-retry-limit', '1', '--replica-completion-count', '1', '--parallelism', '1',
               '--cpu', '2.0', '--memory', '4Gi', '--mi-system-assigned', '--env-vars', *base_env, '--tags', 'order=ORDER-031', f'node={cc}-cm-kg', 'clock=20:30-UTC-Friday')
            log(f'{job}: created in {reg} (parked cron {PARKED}, timeout 36000 s, retry 1)')
        ensure_identity_roles(job, rg, kv)
        if not ex or cc != 'us' and ex['properties']['template']['containers'][0]['image'] != image:
            az('containerapp', 'job', 'registry', 'set', '-n', job, '-g', rg, '--server', ACR_SERVER, '--identity', 'system')
            az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--container-name', job, '--set-env-vars', *base_env); log(f'  {job}: image {image} (pull by identity)')
        names = [f'{n}-key' for n in LAB] + ['ark-aws-key-id', 'ark-aws-secret']
        kv_secrets(job, rg, kv, names)
        set_env(job, rg, [f'{ENVKEY[n]}=secretref:{n}-key' for n in LAB] + ['AWS_ACCESS_KEY_ID=secretref:ark-aws-key-id', 'AWS_SECRET_ACCESS_KEY=secretref:ark-aws-secret'])
        log(f'  {job}: {len(names)} vault references wired as env')
elif cmd == 'backfill':
    # BACKFILL-01 B-6 (DAY ORDER 7, 2026-10-25): one backfill job per roster node with an armed backfill policy line (RAILS\backfill\policy.json), the node job's
    # pattern (same image, environment, identity roles, vault references) with JOB_MODE=backfill, 30 14 * * * UTC (after the live window — the digest closes the
    # night at 14:20 — and after rco-ark 05:45), one six-hour replica, one retry. Signing key by vault reference (cmr-signing-jwk); a vault without it: no job, named.
    tag = sys.argv[2]; image = f'{ACR_SERVER}/cmkg-sweep:{tag}'
    BP = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backfill', 'policy.json'), encoding='utf-8'))['markets']
    roster.require('backfill policy (RAILS\\backfill\\policy.json)', BP, ROSTER_CC)
    for cc in (sys.argv[3:] or [c for c in ROSTER_CC if BP[c]['adapter'] != 'none']):
        reg = NODES[cc]; rg = f'allooloo-cmkg-{reg}'; job = f'cmkg-{cc}-backfill'; kv = KV.get(cc, f'allooloo-cmkg-kv-{cc}'); sa = f'allooloocmkg{cc}pond'
        if 'cmr-signing-jwk' not in (az('keyvault', 'secret', 'list', '--vault-name', kv, '--query', '[].name', check=False) or []):
            log(f'{job}: not created — vault {kv} holds no cmr-signing-jwk (CEO hand: az keyvault secret set --vault-name {kv} -n cmr-signing-jwk --file "C:\\ALLOOLOO\\AGENT KEYS\\cmr-signing-jwk.txt")'); continue
        base_env = [f'NODE_CC={cc}', f'REGION={reg}', f'STORAGE_ACCOUNT={sa}', 'STORAGE_CONTAINER=pond', 'JOB_MODE=backfill', 'DOOR_RESTART=0', 'ARK_ENABLED=1', f'ARK_BUCKET=allooloo-ark-{cc}-cm-kg', f'ARK_REGION={ARK[cc]}', f'IMAGE_TAG={tag}', 'CONTACT=developers@allooloo.ai']
        ex = az('containerapp', 'job', 'show', '-n', job, '-g', rg, check=False)
        if not ex:
            az('containerapp', 'job', 'create', '-n', job, '-g', rg, '--environment', (az('containerapp', 'env', 'list', '-g', f'allooloo-cmkg-{ENV_HOST[cc]}', '--query', "[?properties.provisioningState=='Succeeded'].id | [0]", '-o', 'tsv', raw=True) if cc in ENV_HOST else env_name(rg)),
               '--trigger-type', 'Schedule', '--cron-expression', '30 14 * * *', '--replica-timeout', '21600', '--replica-retry-limit', '1', '--replica-completion-count', '1', '--parallelism', '1',
               '--cpu', '2.0', '--memory', '4Gi', '--mi-system-assigned', '--env-vars', *base_env, '--tags', 'order=BACKFILL-01', f'node={cc}-cm-kg', 'clock=14:30-UTC-nightly')
            log(f'{job}: created in {reg} (30 14 * * * UTC, timeout 21600 s, retry 1)')
        ensure_identity_roles(job, rg, kv)
        if not ex or ex['properties']['template']['containers'][0]['image'] != image:
            az('containerapp', 'job', 'registry', 'set', '-n', job, '-g', rg, '--server', ACR_SERVER, '--identity', 'system')
            az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--container-name', job, '--set-env-vars', *base_env); log(f'  {job}: image {image} (pull by identity)')
        names = [f'{n}-key' for n in LAB] + ['ark-aws-key-id', 'ark-aws-secret', 'cmr-signing-jwk']
        kv_secrets(job, rg, kv, names)
        set_env(job, rg, [f'{ENVKEY[n]}=secretref:{n}-key' for n in LAB] + ['AWS_ACCESS_KEY_ID=secretref:ark-aws-key-id', 'AWS_SECRET_ACCESS_KEY=secretref:ark-aws-secret', 'CMR_SIGNING_JWK=secretref:cmr-signing-jwk'])
        log(f'  {job}: armed, {len(names)} vault references wired as env')
elif cmd == 'apex':
    tag = sys.argv[2]; rg = 'allooloo-cmkg-eastus'; job = 'cmkg-apex-rail'; kv = 'allooloo-cmkg-kv-apex'; image = f'{ACR_SERVER}/cmkg-sweep:{tag}'
    base_env = ['STORAGE_CONTAINER=pond', 'APEX_DRY=0', 'APEX_STORAGE_ACCOUNT=allooloocmkgapex', 'APEX_CONTAINER=sweeps', 'ARK_ENABLED=0', 'ARK_BUCKET=allooloo-ark-apex', f'ARK_REGION={ARK["apex"]}', f'IMAGE_TAG={tag}']
    ex = az('containerapp', 'job', 'show', '-n', job, '-g', rg, check=False)
    if ex: az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--set-env-vars', *base_env); log(f'{job}: image -> {image}')
    else:
        az('containerapp', 'job', 'create', '-n', job, '-g', rg, '--environment', env_name(rg), '--trigger-type', 'Schedule', '--cron-expression', PARKED, '--replica-timeout', '7200', '--replica-retry-limit', '0', '--replica-completion-count', '1', '--parallelism', '1',
           '--cpu', '1.0', '--memory', '2Gi', '--mi-system-assigned', '--env-vars', *base_env, '--tags', 'order=ORDER-031', 'role=apex', 'clock=03:30-UTC-Saturday')
        log(f'{job}: created in eastus (parked cron {PARKED})')
    ensure_identity_roles(job, rg, kv, extra_rgs=[f'allooloo-cmkg-{r}' for r in NODES.values() if r != 'eastus'] + ['allooloo-cmkg-shared'])
    if not ex or ex['properties']['template']['containers'][0]['image'] != image:
        az('containerapp', 'job', 'registry', 'set', '-n', job, '-g', rg, '--server', ACR_SERVER, '--identity', 'system')
        az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--container-name', job, '--command', '/usr/local/bin/python3', '/job/ALLOOLOO/CM-KG/RAILS/job/job_apex.py', '--set-env-vars', *base_env); log(f'  {job}: image {image} (pull by identity)')
    kv_secrets(job, rg, kv, ['cloudflare-d1-token', 'tavily-key', 'ark-aws-key-id', 'ark-aws-secret'])
    set_env(job, rg, ['CLOUDFLARE_API_TOKEN=secretref:cloudflare-d1-token', 'TAVILY_API_KEY=secretref:tavily-key', 'AWS_ACCESS_KEY_ID=secretref:ark-aws-key-id', 'AWS_SECRET_ACCESS_KEY=secretref:ark-aws-secret'])
    log(f'  {job}: vault references wired')
elif cmd == 'digest':
    # ORDER-037 (2026-10-23): two more triggers of the apex image run job_digest.py — cmkg-apex-digest (daily, after the 14:00 UTC Issuerwire close) and
    # cmkg-apex-week (Saturday; the rail itself keeps only the hour that is 06:00 in Los Angeles). Least privilege: storage keys on the thirteen stores
    # (Reader and Data Access), AcrPull, the apex vault for the Tavily key. The private ops store is allooloocmkgapex/ops (public blob access is off on the account).
    tag = sys.argv[2]; rg = 'allooloo-cmkg-eastus'; kv = 'allooloo-cmkg-kv-apex'; image = f'{ACR_SERVER}/cmkg-sweep:{tag}'
    akey = az('storage', 'account', 'keys', 'list', '-n', 'allooloocmkgapex', '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv', raw=True)
    az('storage', 'container', 'create', '-n', 'ops', '--account-name', 'allooloocmkgapex', '--account-key', akey, raw=True); log('allooloocmkgapex/ops: present (private)')
    stores = [('allooloocmkgapex', 'allooloo-cmkg-shared')] + [(f'allooloocmkg{cc}pond', f'allooloo-cmkg-{NODES[cc]}') for cc in ROSTER_CC]   # ENUM-01 (DAY ORDER 6): every roster node's store (was the twelve + live.json)
    for job, cron, mode in (('cmkg-apex-digest', '20 14 * * *', 'daily'), ('cmkg-apex-week', '0 13,14 * * 6', 'week')):
        base_env = [f'MODE={mode}', 'APEX_STORAGE_ACCOUNT=allooloocmkgapex', 'APEX_CONTAINER=sweeps', 'OPS_CONTAINER=ops', f'IMAGE_TAG={tag}']
        ex = az('containerapp', 'job', 'show', '-n', job, '-g', rg, check=False)
        if not ex:
            az('containerapp', 'job', 'create', '-n', job, '-g', rg, '--environment', env_name(rg), '--trigger-type', 'Schedule', '--cron-expression', cron, '--replica-timeout', '1800', '--replica-retry-limit', '0', '--replica-completion-count', '1', '--parallelism', '1',
               '--cpu', '0.5', '--memory', '1Gi', '--mi-system-assigned', '--env-vars', *base_env, '--tags', 'order=ORDER-037', 'role=apex-digest', f'clock={cron.replace(" ", "_")}')
            log(f'{job}: created ({cron} UTC, timeout 1800 s, retry 0)')
        pid = az('containerapp', 'job', 'show', '-n', job, '-g', rg, '--query', 'identity.principalId', '-o', 'tsv', raw=True)
        roles = [('AcrPull', ACR_ID), ('Key Vault Secrets User', az('keyvault', 'show', '-n', kv, '--query', 'id', '-o', 'tsv', raw=True))] + [('Reader and Data Access', az('storage', 'account', 'show', '-n', sa, '-g', g, '--query', 'id', '-o', 'tsv', raw=True)) for sa, g in stores]
        for role, scope in roles: log(f"  {job}: {role} on {scope.split('/')[-1]} {'ok' if assign(role, pid, scope) else 'FAILED'}")
        if not ex or ex['properties']['template']['containers'][0]['image'] != image:
            az('containerapp', 'job', 'registry', 'set', '-n', job, '-g', rg, '--server', ACR_SERVER, '--identity', 'system')
            az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--container-name', job, '--command', '/usr/local/bin/python3', '/job/ALLOOLOO/CM-KG/RAILS/job/job_digest.py', '--set-env-vars', *base_env); log(f'  {job}: image {image} (pull by identity)')
        kv_secrets(job, rg, kv, ['tavily-key']); set_env(job, rg, ['TAVILY_API_KEY=secretref:tavily-key'])
elif cmd == 'digest-sas':
    # ORDER-037: once the CEO has placed the Issuerwire pond read SAS (read + list, container pond of stgamnfrc, GSC tenant) in allooloo-cmkg-kv-apex as
    # issuerwire-pond-sas, wire it into the daily digest; until then the digest writes the eight Issuerwire rows as NOT LANDED with the flag
    rg = 'allooloo-cmkg-eastus'; kv = 'allooloo-cmkg-kv-apex'
    kv_secrets('cmkg-apex-digest', rg, kv, ['issuerwire-pond-sas']); set_env('cmkg-apex-digest', rg, ['ISSUERWIRE_POND_SAS=secretref:issuerwire-pond-sas']); log('cmkg-apex-digest: ISSUERWIRE_POND_SAS wired')
elif cmd == 'arm':
    for cc in (sys.argv[2:] or list(ROSTER_CC) + ['apex']):
        job = 'cmkg-apex-rail' if cc == 'apex' else f'cmkg-{cc}-rail'; rg = 'allooloo-cmkg-eastus' if cc == 'apex' else f'allooloo-cmkg-{NODES[cc]}'
        az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--cron-expression', CRON_APEX if cc == 'apex' else CRON); log(f"{job}: ARMED {CRON_APEX if cc == 'apex' else CRON} UTC")
elif cmd == 'ark-on':
    cc, bucket, region = sys.argv[2], sys.argv[3], sys.argv[4]; job = 'cmkg-apex-rail' if cc == 'apex' else f'cmkg-{cc}-rail'; rg = 'allooloo-cmkg-eastus' if cc == 'apex' else f'allooloo-cmkg-{NODES[cc]}'
    set_env(job, rg, ['ARK_ENABLED=1', f'ARK_BUCKET={bucket}', f'ARK_REGION={region}']); log(f'{job}: ark ON -> s3://{bucket} ({region})')
elif cmd in ('dryrun', 'live'):
    # dryrun <cc>: point the job at the staging container (no door restart) and start one execution; live <cc>: back to the pond container.
    # (create resets these to pond/1 — lesson of 2026-10-18 02:52: a re-trigger right after create ran against the live store and was stopped at once)
    cc = sys.argv[2]; job = 'cmkg-apex-rail' if cc == 'apex' else f'cmkg-{cc}-rail'; rg = 'allooloo-cmkg-eastus' if cc == 'apex' else f'allooloo-cmkg-{NODES[cc]}'
    if cc == 'apex': pairs = ['STORAGE_CONTAINER=staging', 'APEX_DRY=1'] if cmd == 'dryrun' else ['STORAGE_CONTAINER=pond', 'APEX_DRY=0']
    else: pairs = ['STORAGE_CONTAINER=staging', 'DOOR_RESTART=0'] if cmd == 'dryrun' else ['STORAGE_CONTAINER=pond', 'DOOR_RESTART=1']
    set_env(job, rg, pairs)
    env = {e['name']: e.get('value') for e in az('containerapp', 'job', 'show', '-n', job, '-g', rg)['properties']['template']['containers'][0]['env']}
    if env.get('STORAGE_CONTAINER') != ('staging' if cmd == 'dryrun' else 'pond'): raise SystemExit(f'{job}: container env not set as asked — not started')
    log(f"{job}: STORAGE_CONTAINER={env.get('STORAGE_CONTAINER')} DOOR_RESTART={env.get('DOOR_RESTART')}")
    if cmd == 'dryrun': log(f"{job}: execution {az('containerapp', 'job', 'start', '-n', job, '-g', rg, '--query', 'name', '-o', 'tsv', raw=True)} started against staging")
elif cmd == 'upgrade':
    # ORDER-036: the tag move of the upgrade (UPGRADE.md) — image and IMAGE_TAG only; every other env value (ARK_ENABLED among them) is kept as the job carries it
    tag = sys.argv[2]; image = f'{ACR_SERVER}/cmkg-sweep:{tag}'
    for cc in (sys.argv[3:] or list(ROSTER_CC) + ['apex']):
        job = 'cmkg-apex-rail' if cc == 'apex' else f'cmkg-{cc}-rail'; rg = 'allooloo-cmkg-eastus' if cc == 'apex' else f'allooloo-cmkg-{NODES[cc]}'
        before = az('containerapp', 'job', 'show', '-n', job, '-g', rg); env0 = {e['name']: e.get('value') for e in before['properties']['template']['containers'][0].get('env', [])}
        # DAY ORDER 5 (2026-10-25): one transient Azure error no longer stops the fleet move — retry once, then name the job and carry on
        if az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--set-env-vars', f'IMAGE_TAG={tag}', check=False) is None:
            time.sleep(20)
            if az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--set-env-vars', f'IMAGE_TAG={tag}', check=False) is None: log(f'{job}: UPGRADE FAILED twice (flagged; left on its tag)'); continue
        after = az('containerapp', 'job', 'show', '-n', job, '-g', rg); env1 = {e['name']: e.get('value') for e in after['properties']['template']['containers'][0].get('env', [])}
        moved = sorted(k for k in set(env0) | set(env1) if env0.get(k) != env1.get(k))
        log(f"{job}: {before['properties']['template']['containers'][0]['image'].split(':')[-1]} -> {tag} · env changed: {moved} · ARK_ENABLED {env1.get('ARK_ENABLED')}")
elif cmd == 'nightly':
    for cc in (sys.argv[2:] or list(ROSTER_CC) + ['apex']):
        job = 'cmkg-apex-rail' if cc == 'apex' else f'cmkg-{cc}-rail'; rg = 'allooloo-cmkg-eastus' if cc == 'apex' else f'allooloo-cmkg-{NODES[cc]}'
        az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--cron-expression', NIGHTLY[cc]); log(f'{job}: NIGHTLY {NIGHTLY[cc]} UTC (02:00 local standard time; apex after the last region)')
elif cmd == 'export':
    # the schedule of every job as it stands, written beside before a clock change (Rule One: the Friday clock is disabled, never deleted — this file is its record)
    out = {j['name']: {'resource_group': j['resourceGroup'], 'trigger': j['properties']['configuration']['triggerType'], 'cron': (j['properties']['configuration'].get('scheduleTriggerConfig') or {}).get('cronExpression'), 'image': j['properties']['template']['containers'][0]['image']} for j in az('containerapp', 'job', 'list')}
    fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"schedules-{sys.argv[2] if len(sys.argv) > 2 else 'export'}.json")
    with open(fn, 'x', encoding='utf-8') as f: json.dump(out, f, indent=1)
    log(f'schedules exported: {fn} ({len(out)} jobs)')
elif cmd == 'status':
    for j in az('containerapp', 'job', 'list'):
        c = j['properties']['configuration']; t = j['properties']['template']['containers'][0]
        log(f"{j['name']:16s} {j['location']:20s} {c['triggerType']:8s} cron={(c.get('scheduleTriggerConfig') or {}).get('cronExpression', '-'):12s} timeout={c['replicaTimeout']} retry={c['replicaRetryLimit']} {t['image'].split('/')[-1]} mi={'yes' if (j.get('identity') or {}).get('principalId') else 'no'}")
