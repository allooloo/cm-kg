r"""backfill_jobs.py — BACKFILL-01 B-6 (DAY ORDER 7, 2026-10-25): one backfill job per node, generated from the roster and the backfill policy — no market typed.
Each job is the node's own live job pattern (same image, same environment, same identity roles, same vault references) with JOB_MODE=backfill, a nightly slot
after the live window (the digest closes the night at 14:20 UTC) and after rco-ark (05:45 UTC): 30 14 * * * UTC, one six-hour replica, one retry (the fleet's
per-job retry). The job paces to the archive (the policy line's pace), never on a schedule tighter than the archive's. Markets wait their turn in the B-3
order inside the job (backfill.py), so every node is armed and only the market whose turn it is pulls.
  python backfill_jobs.py plan                 the job of every roster node (from roster + policy), or the gap that stops the rail
  python backfill_jobs.py create <tag> [cc..]  writes the jobs (az, Allooloo tenant guard) by copying each node's live job definition; vault secret cmr-signing-jwk
                                               must exist in the node's vault (the CEO's hand when it does not: a key value is never written by CC)"""
import os, sys, json, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import roster
POL = json.load(open(os.environ.get('BACKFILL_POLICY') or os.path.join(HERE, 'policy.json'), encoding='utf-8'))
CRON = '30 14 * * *'; TIMEOUT = 21600; RETRY = 1
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
def plan():
    roster.require('backfill policy (RAILS\\backfill\\policy.json)', POL['markets'])
    out = []
    for n in roster.load():
        cc = roster.cc_of(n); l = POL['markets'][cc]
        out.append({'job': f'cmkg-{cc}-backfill', 'node': n['node'], 'store': f"allooloocmkg{cc}pond ({(n.get('region') or {}).get('store')})", 'adapter': l['adapter'], 'archive': l['archive'],
                    'cron_utc': CRON if l['adapter'] != 'none' else None, 'armed': l['adapter'] != 'none', 'order_position': (POL['order'].index(cc) + 1) if cc in POL['order'] else None,
                    'pace_rps': (l.get('pace') or {}).get('rps'), 'env': {'NODE_CC': cc, 'JOB_MODE': 'backfill', 'ARK_ENABLED': '1'}, 'secrets': ['cmr-signing-jwk', 'ark-aws-key-id', 'ark-aws-secret']})
    return out
def az(*a, check=True):
    p = subprocess.run(['az', *a, '-o', 'json'], capture_output=True, text=True, encoding='utf-8', errors='replace', shell=(os.name == 'nt'))
    if p.returncode and check: raise SystemExit(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-400:]}")
    return json.loads(p.stdout) if p.stdout.strip() else None
def create(tag, ccs):
    acct = az('account', 'show'); assert acct['tenantId'] == TENANT and acct['id'] == SUB, 'STOP: not the Allooloo tenant/subscription'
    jobs = {j['job']: j for j in plan()}
    for cc in (ccs or [j['node'].split('-')[0] for j in jobs.values() if j['armed']]):
        j = jobs[f'cmkg-{cc}-backfill']; live = f'cmkg-{cc}-rail'
        src = next((x for x in az('containerapp', 'job', 'list') if x['name'] == live), None)
        if not src: print(f'{cc}: no live job {live} to copy — skipped (named)'); continue
        rg = src['resourceGroup']; kv = next((s.get('keyVaultUrl', '').split('/')[2].split('.')[0] for s in (src['properties']['configuration'].get('secrets') or []) if s.get('keyVaultUrl')), None)
        have = az('keyvault', 'secret', 'list', '--vault-name', kv, '--query', '[].name', check=False) or []
        if 'cmr-signing-jwk' not in have: print(f'{cc}: vault {kv} has no cmr-signing-jwk — job not created (CEO hand: az keyvault secret set --vault-name {kv} -n cmr-signing-jwk --file "AGENT KEYS\\cmr-signing-jwk.txt")'); continue
        if az('containerapp', 'job', 'show', '-n', j['job'], '-g', rg, check=False): print(f"{j['job']}: exists (left as it is)"); continue
        c = src['properties']['template']['containers'][0]; env = [e for e in c.get('env') or [] if e['name'] not in ('JOB_MODE', 'NOT_BEFORE', 'DOOR_RESTART')]
        env += [{'name': 'JOB_MODE', 'value': 'backfill'}, {'name': 'IMAGE_TAG', 'value': tag}]
        secrets = list(src['properties']['configuration'].get('secrets') or []) + [{'name': 'cmr-signing-jwk', 'keyVaultUrl': f'https://{kv}.vault.azure.net/secrets/cmr-signing-jwk', 'identity': 'system'}]
        env.append({'name': 'CMR_SIGNING_JWK', 'secretRef': 'cmr-signing-jwk'})
        spec = {'location': src['location'], 'identity': {'type': 'SystemAssigned'}, 'properties': {'environmentId': src['properties']['environmentId'], 'configuration': {
            'triggerType': 'Schedule', 'replicaTimeout': TIMEOUT, 'replicaRetryLimit': RETRY, 'scheduleTriggerConfig': {'cronExpression': CRON, 'parallelism': 1, 'replicaCompletionCount': 1},
            'registries': src['properties']['configuration'].get('registries'), 'secrets': secrets}, 'template': {'containers': [{**c, 'image': c['image'].rsplit(':', 1)[0] + ':' + tag, 'env': env}]}}}
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False); json.dump(spec, f); f.close()
        az('rest', '--method', 'put', '--url', f"https://management.azure.com/subscriptions/{SUB}/resourceGroups/{rg}/providers/Microsoft.App/jobs/{j['job']}?api-version=2024-03-01", '--body', '@' + f.name)
        print(f"{j['job']}: created in {rg} ({src['location']}), cron {CRON} UTC, image :{tag} — identity roles: run provision_jobs.py roles {cc}-backfill")
if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == 'plan':
        for j in plan(): print(json.dumps(j, ensure_ascii=False))
    elif a[0] == 'create': create(a[1], a[2:])
