"""ORDER-018 Step 0 — read-only inventory of the Allooloo subscription (tenant of record 04a24e43-dc13-4578-950a-910db076a799, subscription
038b49c0-5a0c-46f7-bd34-41ee6d087b41). Nothing is created or changed. Writes AZURE\\step0-inventory-<date>.json and prints the report lines.
Regions inventoried: the twelve market nodes' home regions (the CEO's "eleven target regions" plus the Hong Kong candidate, marked).
Refuses to run unless `az account show` returns the tenant and subscription of record."""
import json, subprocess, datetime, sys, os
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
REGIONS = [('canadacentral', 'ca'), ('uksouth', 'uk'), ('australiaeast', 'au'), ('southeastasia', 'sg'), ('switzerlandnorth', 'ch'), ('germanywestcentral', 'de'), ('francecentral', 'fr'), ('westeurope', 'nl'), ('japaneast', 'jp'), ('koreacentral', 'kr'), ('eastus', 'us'), ('eastasia', 'hk (Width 0 only, candidate)')]
def az(*args, check=True):
    p = subprocess.run(['az', *args, '--output', 'json'], capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
    if p.returncode != 0:
        if check: raise SystemExit('az ' + ' '.join(args[:3]) + ' failed: ' + (p.stderr or p.stdout)[-400:])
        return None
    try: return json.loads(p.stdout) if p.stdout.strip() else None
    except Exception: return {'raw': p.stdout[:2000]}
acct = az('account', 'show')
if not acct or acct.get('tenantId') != TENANT or acct.get('id') != SUB:
    raise SystemExit(f"STOP: az account show is tenant {acct.get('tenantId') if acct else None} / subscription {acct.get('id') if acct else None}, not the tenant of record. Run: az login --tenant {TENANT} ; az account set --subscription {SUB}")
out = {'as_of': datetime.datetime.now().isoformat(timespec='minutes'), 'tenant': TENANT, 'subscription': SUB, 'signed_in_as': (acct.get('user') or {}).get('name')}
subs = az('account', 'list'); out['subscriptions_visible'] = [{'name': s['name'], 'id': s['id'], 'tenant': s['tenantId'], 'state': s.get('state')} for s in subs]
groups = az('group', 'list') or []
out['resource_groups'] = [{'name': g['name'], 'location': g['location'], 'state': (g.get('properties') or {}).get('provisioningState'), 'tags': g.get('tags')} for g in groups]
res = az('resource', 'list', check=False) or []
out['resources_by_group'] = {}
for r in res: out['resources_by_group'].setdefault(r.get('resourceGroup'), []).append({'name': r['name'], 'type': r['type'], 'location': r.get('location')})
out['container_app_environments'] = [{'name': e['name'], 'group': e['resourceGroup'], 'location': e['location'], 'state': (e.get('properties') or {}).get('provisioningState')} for e in (az('containerapp', 'env', 'list', check=False) or [])]
out['storage_accounts'] = [{'name': s['name'], 'group': s['resourceGroup'], 'location': s['location'], 'state': s.get('provisioningState')} for s in (az('storage', 'account', 'list', check=False) or [])]
out['providers'] = {ns: (az('provider', 'show', '--namespace', ns, check=False) or {}).get('registrationState') for ns in ('Microsoft.App', 'Microsoft.Storage', 'Microsoft.OperationalInsights', 'Microsoft.ContainerRegistry')}
out['quotas'] = {}
for loc, node in REGIONS:
    q = {'node': node}
    u = az('rest', '--method', 'get', '--url', f'https://management.azure.com/subscriptions/{SUB}/providers/Microsoft.App/locations/{loc}/usages?api-version=2024-03-01', check=False)
    q['container_apps'] = [{'name': (x.get('name') or {}).get('value'), 'current': x.get('currentValue'), 'limit': x.get('limit')} for x in ((u or {}).get('value') or [])] if u else 'not readable'
    s = az('storage', 'account', 'show-usage', '--location', loc, check=False)
    q['storage_accounts'] = {'current': s.get('currentValue'), 'limit': s.get('limit')} if isinstance(s, dict) and 'limit' in s else 'not readable'
    out['quotas'][loc] = q
fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"step0-inventory-{datetime.date.today().isoformat()}.json"); json.dump(out, open(fn, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('signed in as', out['signed_in_as'], '| tenant', TENANT, '| subscription', SUB)
print('subscriptions visible:', len(out['subscriptions_visible']), [s['name'] + ' (' + s['state'] + ')' for s in out['subscriptions_visible']])
print('resource groups:', len(groups)); [print(f"  {g['name']:40s} {g['location']:20s} {g['state']}") for g in out['resource_groups']]
print('container app environments:', len(out['container_app_environments']), '| storage accounts:', len(out['storage_accounts']), '| providers:', out['providers'])
for loc, q in out['quotas'].items():
    ca = q['container_apps']; env = next((x for x in ca if isinstance(ca, list) and 'Environment' in str(x.get('name'))), None) if isinstance(ca, list) else None
    print(f"  {loc:20s} {q['node']:28s} container apps: {('env ' + str(env['current']) + '/' + str(env['limit'])) if env else (ca if isinstance(ca, str) else str(len(ca)) + ' usage rows')} | storage accounts: {q['storage_accounts']}")
print('saved', fn)
