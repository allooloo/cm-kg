r"""ORDER-031 part 3 — one Azure Monitor rule per job (twelve): the job failed, or no run started by 23:30 UTC Friday (apex: by 05:00 UTC Saturday)
-> one email to the address in ROOT-CONFIG.json (developers@allooloo.ai, confirmed by the CEO 2026-10-17). No polling: a scheduled-query rule on the
region's Log Analytics workspace (the environment already streams ContainerAppSystemLogs_CL there), evaluated every 15 minutes over a 4-hour window.
  python alerts.py create [cc ...|apex]     python alerts.py status
Create-only; an existing rule is left as it is (Rule One)."""
import os, sys, json, subprocess
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
NODES = {'nl': 'westeurope', 'ch': 'switzerlandnorth', 'fr': 'francecentral', 'de': 'germanywestcentral', 'sg': 'southeastasia', 'au': 'australiaeast', 'uk': 'uksouth', 'ca': 'canadacentral', 'jp': 'japaneast', 'kr': 'koreacentral', 'us': 'eastus'}
CFG = json.load(open(r'C:\ALLOOLOO\ROOT-CONFIG.json', encoding='utf-8')); EMAIL = CFG['alert_email']
def az(*a, raw=False, check=True):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=(os.name == 'nt'))
    if p.returncode != 0:
        if check: raise SystemExit(f"az {' '.join(str(x) for x in a[:5])} failed: {(p.stderr or p.stdout)[-500:]}")
        return None
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az('account', 'show')
if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
def kql(job, apex=False):
    late = "dayofweek(now()) == 6d and hourofday(now()) >= 5 and hourofday(now()) < 7" if apex else "dayofweek(now()) == 5d and ((hourofday(now()) == 23 and datetime_part('minute', now()) >= 30))"
    deadline = '05:00 UTC Saturday' if apex else '23:30 UTC Friday'
    return (f"let job = '{job}';\n"
            "let failed = ContainerAppSystemLogs_CL | where JobName_s == job and TimeGenerated > ago(4h)\n"
            "  | where Reason_s in ('Failed', 'BackoffLimitExceeded', 'Timeout', 'DeadlineExceeded', 'ErrImagePull', 'ImagePullBackOff') or (Reason_s == 'ContainerTerminated' and Log_s !has \"exit code '0'\")\n"
            "  | project TimeGenerated, Reason_s, Log_s;\n"
            "let late = ContainerAppSystemLogs_CL | where JobName_s == job and TimeGenerated > ago(4h) and Reason_s == 'ContainerStarted'\n"
            f"  | summarize started = count() | where started == 0 and {late}\n"
            f"  | project TimeGenerated = now(), Reason_s = 'NoRunByDeadline', Log_s = strcat('no execution of ', job, ' started by {deadline}');\n"
            "failed | union late")
cmd = sys.argv[1]
if cmd == 'create':
    ag = az('monitor', 'action-group', 'show', '-n', 'allooloo-cmkg-alerts', '-g', 'allooloo-cmkg-shared', check=False)
    if not ag: ag = az('monitor', 'action-group', 'create', '-n', 'allooloo-cmkg-alerts', '-g', 'allooloo-cmkg-shared', '--short-name', 'cmkgsweep', '--action', 'email', 'developers', EMAIL, '--tags', 'order=ORDER-031'); print('action group created ->', EMAIL)
    else: print('action group present ->', [e['emailAddress'] for e in ag.get('emailReceivers', [])])
    for cc in (sys.argv[2:] or list(NODES) + ['apex']):
        reg = 'eastus' if cc == 'apex' else NODES[cc]; rg = f'allooloo-cmkg-{reg}'; job = 'cmkg-apex-rail' if cc == 'apex' else f'cmkg-{cc}-rail'; name = f'alert-{job}'
        if az('monitor', 'scheduled-query', 'show', '-n', name, '-g', rg, check=False): print(name, 'present'); continue
        ws = [w for w in az('monitor', 'log-analytics', 'workspace', 'list', '-g', rg)][0]['id']
        # the CLI's --condition-query parser rejects this KQL ("no tabular expression"); the rule is PUT directly (same resource, any KQL)
        body = {'location': reg, 'tags': {'order': 'ORDER-031', 'job': job}, 'properties': {
            'displayName': name, 'description': f'ORDER-031: {job} failed, or no run by {"05:00 UTC Saturday" if cc == "apex" else "23:30 UTC Friday"} -> email {EMAIL}',
            'severity': 1, 'enabled': True, 'evaluationFrequency': 'PT15M', 'windowSize': 'PT4H', 'scopes': [ws], 'targetResourceTypes': ['Microsoft.OperationalInsights/workspaces'],
            'criteria': {'allOf': [{'query': kql(job, cc == 'apex'), 'timeAggregation': 'Count', 'operator': 'GreaterThan', 'threshold': 0, 'failingPeriods': {'numberOfEvaluationPeriods': 1, 'minFailingPeriodsToAlert': 1}}]},
            'autoMitigate': True, 'actions': {'actionGroups': [ag['id']]}}}
        bp = os.path.join(os.environ.get('TEMP', '/tmp'), f'alert-{job}.json'); json.dump(body, open(bp, 'w', encoding='utf-8'))
        url = f"/subscriptions/{SUB}/resourceGroups/{rg}/providers/Microsoft.Insights/scheduledQueryRules/{name}?api-version=2023-03-15-preview"
        az('rest', '--method', 'put', '--url', url, '--body', '@' + bp); os.remove(bp)
        print(name, 'created in', reg)
elif cmd == 'status':
    for r in az('monitor', 'scheduled-query', 'list'): print(r['name'], r['location'], 'enabled' if r.get('enabled', True) else 'disabled', r.get('evaluationFrequency'))
