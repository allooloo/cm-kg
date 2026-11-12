r"""iw_stop_old.py — IW-MOVE-01 step 8: the old side stopped, nothing deleted. In rg-amn-frc (the other directory):
  jobs   each of the eight amn-*-rail jobs: its clock is set to the never-fires form (0 0 31 2 *) — the job, its image, its settings and its history stay.
         The clock it had is saved first (old-stopped.json) so it can be put back with `restore`.
  door   amn-door is stopped (the Container Apps stop action: no replica runs, the app, its revisions, host names and certificates stay).
Then the stopped state is read back. Usage: python -X utf8 -I iw_stop_old.py stop|state|restore"""
import json, os, subprocess, sys, pathlib
AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']; H = pathlib.Path(__file__).parent
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\A2AAMN\.azure', MSYS_NO_PATHCONV='1'); SUB = '9e406344-81a4-4624-98de-a9c642a75d69'; RG = 'rg-amn-frc'; PARKED = '0 0 31 2 *'
JOBS = ['standing', 'filings', 'coverage', 'claims', 'receipts', 'ark', 'stores', 'close']
def az(*a, check=True):
    r = subprocess.run([*AZ, *a, '--subscription', SUB, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode:
        if check: sys.exit(f'STOP az {" ".join(a[:4])}: {r.stderr[-500:]}')
        return {'_error': r.stderr[-400:]}
    return json.loads(r.stdout) if r.stdout.strip() else None
cron = lambda x: (az('containerapp', 'job', 'show', '-n', f'amn-{x}-rail', '-g', RG)['properties']['configuration'].get('scheduleTriggerConfig') or {}).get('cronExpression')
APP = f'/subscriptions/{SUB}/resourceGroups/{RG}/providers/Microsoft.App/containerApps/amn-door'
def state():
    d = az('containerapp', 'show', '-n', 'amn-door', '-g', RG); reps = az('containerapp', 'replica', 'list', '-n', 'amn-door', '-g', RG, check=False)
    s = {'jobs': {f'amn-{x}-rail': cron(x) for x in JOBS}, 'door': {'runningStatus': d['properties'].get('runningStatus'), 'replicas': len(reps) if isinstance(reps, list) else 'not listed', 'latest_revision': d['properties'].get('latestRevisionName'), 'host_names_kept': len(d['properties']['configuration']['ingress'].get('customDomains') or [])}}
    print(json.dumps(s, indent=1)); return s
what = sys.argv[1]
if what == 'state': state()
if what == 'stop':
    f = H / 'old-stopped.json'
    if not f.exists(): json.dump({'crons_before': {x: cron(x) for x in JOBS}}, open(f, 'w'), indent=1)
    for x in JOBS:
        if cron(x) != PARKED: az('containerapp', 'job', 'update', '-n', f'amn-{x}-rail', '-g', RG, '--cron-expression', PARKED)
        print(f'amn-{x}-rail', cron(x), flush=True)
    r = subprocess.run([*AZ, 'rest', '--method', 'post', '--url', f'https://management.azure.com{APP}/stop?api-version=2024-03-01'], capture_output=True, text=True, env=ENV); print('door stop exit', r.returncode, r.stderr[-300:])
    import time; time.sleep(60); json.dump({**json.load(open(f)), 'state_after': state()}, open(f, 'w'), indent=1)
if what == 'restore':
    b = json.load(open(H / 'old-stopped.json'))['crons_before']
    for x in JOBS: az('containerapp', 'job', 'update', '-n', f'amn-{x}-rail', '-g', RG, '--cron-expression', b[x]); print(x, cron(x))
    r = subprocess.run([*AZ, 'rest', '--method', 'post', '--url', f'https://management.azure.com{APP}/start?api-version=2024-03-01'], capture_output=True, text=True, env=ENV); print('door start exit', r.returncode)
