r"""reslate_move.py — RESLATE-01: the fleet onto the re-slate image, and the one job armed. The agent runs it under C:\ALLOOLOO\.azure. A step that fails stops the run.
  rails    every cmkg-<cc>-rail (the roster): image -> the re-slate image by digest; RESEARCH_THREADS=4 (34 markets write at once: the engines' rate);
           tag retired=RESLATE-01-nightly-clock (its own clock is gone: the one job starts it). Its cron stays the house's never-fires form (0 0 31 2 *).
  one      cmkg-apex-rail = the one job: image, command job_reslate.py, replica timeout 14 h, the meters, cron 0 6 * * 6 (Saturday 06:00 UTC: after every
           market's Friday close in its own time zone)
  retire   cmkg-apex-digest, cmkg-apex-week (the one job writes the one digest), every cmkg-<cc>-backfill, cmkg-eco-ops, eco-refresh, book-of-markets,
           bookops-weekly (started by the one job): cron -> 0 0 31 2 *, tag retired=RESLATE-01. Nothing is deleted.
  Not touched: cmkg-rco-chain (the receipt chain's own daily check, not a re-slate) and the four trader-* jobs (Trader Class reads the record as a desk
  would; not a re-slate) — named in the report.
Before the first write the estate's jobs are saved as they stand (jobs-before-reslate.json). Usage: python -X utf8 -I reslate_move.py rails|one|retire"""
import json, os, subprocess, sys, time, pathlib
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
H = pathlib.Path(__file__).parent; IMG = json.load(open(H / 'reslate-image.json'))['image']; PARKED = '0 0 31 2 *'; phase = sys.argv[1]
def say(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def az(*a, check=True):
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode:
        if check: say('STOP: az', ' '.join(a[:5]), r.stderr[-300:]); sys.exit(1)
        return None
    return json.loads(r.stdout) if r.stdout.strip() else None
jobs = az('containerapp', 'job', 'list')
sv = H / 'jobs-before-reslate.json'
if not sv.exists(): json.dump([{'name': j['name'], 'rg': j['resourceGroup'], 'trigger': j['properties']['configuration'].get('triggerType'), 'cron': (j['properties']['configuration'].get('scheduleTriggerConfig') or {}).get('cronExpression'), 'timeout': j['properties']['configuration'].get('replicaTimeout'), 'image': j['properties']['template']['containers'][0]['image'], 'command': j['properties']['template']['containers'][0].get('command'), 'tags': j.get('tags')} for j in jobs], open(sv, 'w'), indent=1)
J = {j['name']: j for j in jobs}; cron = lambda j: (j['properties']['configuration'].get('scheduleTriggerConfig') or {}).get('cronExpression')
if phase == 'rails':
    n = 0
    for name in sorted(J):
        if not (name.startswith('cmkg-') and name.endswith('-rail')) or name == 'cmkg-apex-rail': continue
        j = J[name]; rg = j['resourceGroup']
        az('containerapp', 'job', 'update', '-n', name, '-g', rg, '--image', IMG, '--set-env-vars', 'RESEARCH_THREADS=4', '--tags', *[f'{k}={v}' for k, v in {**(j.get('tags') or {}), 'retired': 'RESLATE-01-nightly-clock', 'started-by': 'cmkg-apex-rail'}.items()])
        n += 1; say(name, 'image moved; own clock', cron(j))
    say('rails moved', n)
elif phase == 'one':
    name, rg = 'cmkg-apex-rail', 'allooloo-cmkg-eastus'; j = J[name]
    az('containerapp', 'job', 'update', '-n', name, '-g', rg, '--image', IMG, '--container-name', j['properties']['template']['containers'][0]['name'], '--command', '/usr/local/bin/python3', '/job/ALLOOLOO/CM-KG/RAILS/job/job_reslate.py',
       '--replica-timeout', '50400', '--cron-expression', '0 6 * * 6', '--set-env-vars', 'RESLATE_TAVILY_USD=500', 'RESLATE_PPLX_USD=500', 'RESLATE_WAIT_HOURS=11', 'OPS_CONTAINER=ops', 'MODE=daily',
       '--tags', *[f'{k}={v}' for k, v in {**(j.get('tags') or {}), 'role': 'reslate', 'order': 'RESLATE-01', 'clock': 'Saturday-06:00-UTC'}.items()])
    x = az('containerapp', 'job', 'show', '-n', name, '-g', rg); c = x['properties']['template']['containers'][0]
    say(name, 'cron', cron(x), 'timeout', x['properties']['configuration'].get('replicaTimeout'), 'command', c.get('command'), 'image', c['image'][-20:])
elif phase == 'retire':
    names = ['cmkg-apex-digest', 'cmkg-apex-week', 'cmkg-eco-ops', 'eco-refresh', 'book-of-markets', 'bookops-weekly'] + sorted(n for n in J if n.startswith('cmkg-') and n.endswith('-backfill')); out = []
    for name in names:
        j = J.get(name)
        if not j: say(name, 'not found'); continue
        was = cron(j)
        if was != PARKED: az('containerapp', 'job', 'update', '-n', name, '-g', j['resourceGroup'], '--cron-expression', PARKED, '--tags', *[f'{k}={v}' for k, v in {**(j.get('tags') or {}), 'retired': 'RESLATE-01', 'clock-was': str(was).replace(' ', '_').replace('*', 'x').replace(',', '+'), 'started-by': 'cmkg-apex-rail'}.items()])
        out.append({'job': name, 'rg': j['resourceGroup'], 'cron_was': was, 'cron_now': PARKED}); say(name, 'retired; clock was', was)
    json.dump(out, open(H / 'jobs-retired.json', 'w'), indent=1); say('retired', len(out))
