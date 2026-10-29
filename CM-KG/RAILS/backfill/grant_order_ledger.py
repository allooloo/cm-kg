r"""Backfill gate fix (2026-10-26) — the CEO's click. Gives each backfill job's managed identity Storage Blob Data Contributor on the one order-ledger
container (allooloocmkgapex/backfill-order), nothing wider: the gate reads the earlier markets' entries there, and each job writes its own entry.
Idempotent (an existing assignment is reported, not duplicated). Usage: python -X utf8 -I C:\ALLOOLOO\CM-KG\RAILS\backfill\grant_order_ledger.py"""
import json, os, subprocess, time
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
def az(*a):
    p = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8'); return (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr[-300:]
SA = az('storage', 'account', 'show', '-n', 'allooloocmkgapex', '-g', 'allooloo-cmkg-shared', '--query', 'id')[0]
SCOPE = f'{SA}/blobServices/default/containers/backfill-order'
jobs = az('containerapp', 'job', 'list', '--query', "[?ends_with(name,'-backfill')].{n:name,pid:identity.principalId}")[0]
ok = 0
for j in sorted(jobs, key=lambda x: x['n']):
    for i in range(4):
        r, err = az('role', 'assignment', 'create', '--role', 'Storage Blob Data Contributor', '--assignee-object-id', j['pid'], '--assignee-principal-type', 'ServicePrincipal', '--scope', SCOPE)
        if r: break
        time.sleep(10)
    ok += bool(r); print(j['n'], 'ok' if r else 'FAILED ' + err)
print(f'{ok}/{len(jobs)} granted on backfill-order')
