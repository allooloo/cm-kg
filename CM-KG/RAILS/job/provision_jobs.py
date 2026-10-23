r"""ORDER-031 — the twelve Container Apps Jobs (eleven nodes + apex), create-only, idempotent, nothing deleted.
  python provision_jobs.py create <image tag> [cc ...]   create (or bring to the image) the node jobs; the US job is updated in place (same image, same schedule, nothing else)
  python provision_jobs.py apex <image tag>              the apex job in East US
  python provision_jobs.py arm [cc ...|apex]             set the real cron (30 20 * * 5 UTC; apex 30 3 * * 6 UTC = Friday 23:30 Toronto); until then the jobs carry the parked cron 0 0 31 2 * (never fires)
  python provision_jobs.py ark-on <cc|apex> <bucket> <aws region>   enable the ark write on a job after the CEO attaches the policy
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
    tag = sys.argv[2]; ccs = sys.argv[3:] or list(NODES); image = f'{ACR_SERVER}/cmkg-sweep:{tag}'
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
            az('containerapp', 'job', 'create', '-n', job, '-g', rg, '--environment', env_name(rg), '--trigger-type', 'Schedule', '--cron-expression', PARKED, '--replica-timeout', '36000', '--replica-retry-limit', '1', '--replica-completion-count', '1', '--parallelism', '1',
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
elif cmd == 'arm':
    for cc in (sys.argv[2:] or list(NODES) + ['apex']):
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
    for cc in (sys.argv[3:] or list(NODES) + ['apex']):
        job = 'cmkg-apex-rail' if cc == 'apex' else f'cmkg-{cc}-rail'; rg = 'allooloo-cmkg-eastus' if cc == 'apex' else f'allooloo-cmkg-{NODES[cc]}'
        before = az('containerapp', 'job', 'show', '-n', job, '-g', rg); env0 = {e['name']: e.get('value') for e in before['properties']['template']['containers'][0].get('env', [])}
        az('containerapp', 'job', 'update', '-n', job, '-g', rg, '--image', image, '--set-env-vars', f'IMAGE_TAG={tag}')
        after = az('containerapp', 'job', 'show', '-n', job, '-g', rg); env1 = {e['name']: e.get('value') for e in after['properties']['template']['containers'][0].get('env', [])}
        moved = sorted(k for k in set(env0) | set(env1) if env0.get(k) != env1.get(k))
        log(f"{job}: {before['properties']['template']['containers'][0]['image'].split(':')[-1]} -> {tag} · env changed: {moved} · ARK_ENABLED {env1.get('ARK_ENABLED')}")
elif cmd == 'nightly':
    for cc in (sys.argv[2:] or list(NODES) + ['apex']):
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
