r"""ORDER-031 — bring the US job to the same schedule as the other ten (nothing else changes on it). `az containerapp job update` cannot change a
job's trigger type (Manual -> Schedule), so this is a direct ARM PATCH of configuration.triggerType + scheduleTriggerConfig, parked cron until the arm.
Usage: python us_trigger.py [cron]   (default the parked cron 0 0 31 2 *). Tenant guard as the rails. Prints the trigger before and after."""
import os, sys, json, subprocess, tempfile
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
cron = sys.argv[1] if len(sys.argv) > 1 else '0 0 31 2 *'
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=(os.name == 'nt'))
    if p.returncode != 0: raise SystemExit(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-500:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az('account', 'show')
if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
url = f'/subscriptions/{SUB}/resourceGroups/allooloo-cmkg-eastus/providers/Microsoft.App/jobs/cmkg-us-rail?api-version=2024-03-01'
before = az('rest', '--method', 'get', '--url', url)['properties']['configuration']
print('before:', before['triggerType'], before.get('scheduleTriggerConfig'), 'timeout', before['replicaTimeout'], 'retry', before['replicaRetryLimit'])
body = {'properties': {'configuration': {'triggerType': 'Schedule', 'scheduleTriggerConfig': {'cronExpression': cron, 'parallelism': 1, 'replicaCompletionCount': 1}, 'manualTriggerConfig': None,
        'replicaTimeout': before['replicaTimeout'], 'replicaRetryLimit': before['replicaRetryLimit']}}}
fd, bp = tempfile.mkstemp(suffix='.json'); os.write(fd, json.dumps(body).encode()); os.close(fd)
az('rest', '--method', 'patch', '--url', url, '--body', '@' + bp); os.remove(bp)
after = az('rest', '--method', 'get', '--url', url)['properties']['configuration']
print('after: ', after['triggerType'], after.get('scheduleTriggerConfig'), 'timeout', after['replicaTimeout'], 'retry', after['replicaRetryLimit'])
