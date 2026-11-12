r"""capacity_snapshot.py — DIGEST-CAP-01 (DAY ORDER 5, 2026-10-24): the subscription's capacity as provisioned, for the nightly digest's capacity block.
What only Azure Resource Manager can see (the digest job holds data-plane roles only, never a subscription Reader): Container Apps environments against the
subscription limit, the regions they sit in, door apps, jobs (with image tags), node stores and their regions. Written to the private ops store as
ops/capacity/latest.json and ops/capacity/<date>.json (beside, never over a dated copy). Run by CC after any provisioning change (row_close / eu_job) and at
every order close. Tenant guarded. Usage: python -X utf8 -I capacity_snapshot.py"""
import os, sys, json, subprocess, datetime, tempfile
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']   # not az.cmd: cmd.exe mangles JMESPath braces
ENV_LIMIT = 16   # MaxNumberOfGlobalEnvironmentsInSubExceeded, read 2026-10-24 (DAY ORDER 4); raised only by the CEO's quota request
def az(*a):
    r = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: raise SystemExit('az failed: ' + (r.stderr or '')[-300:])
    return json.loads(r.stdout or 'null')
acct = az('account', 'show'); assert acct['tenantId'] == '04a24e43-dc13-4578-950a-910db076a799' and acct['id'] == '038b49c0-5a0c-46f7-bd34-41ee6d087b41', 'STOP: not the Allooloo tenant/subscription'
envs = az('containerapp', 'env', 'list', '--query', '[].{n:name,l:location}')
apps = az('containerapp', 'list', '--query', "[?starts_with(name,'cmkg-door')].{n:name,l:location,img:properties.template.containers[0].image}")
jobs = az('containerapp', 'job', 'list', '--query', '[].{n:name,l:location,img:properties.template.containers[0].image,cron:properties.configuration.scheduleTriggerConfig.cronExpression,mod:systemData.lastModifiedAt,env:properties.template.containers[0].env}')   # Line 0 (DAY ORDER 6): + when each job definition last changed
stores = az('storage', 'account', 'list', '--query', "[?starts_with(name,'allooloocmkg')].{n:name,l:location}")
now = datetime.datetime.now(datetime.timezone.utc)
# FIX-01 (2026-11-12): from what runs. A job names its image by tag (repo:tag) or by digest (repo@sha256:…); by digest there is no tag in the name, so the
# tag is the version the job stamps on its own run (IMAGE_TAG — the string its marker carries). Issuerwire's jobs ride the fleet image but run their own code.
import re, collections
def job_tag(j):
    img = j['img']; name = img.split('/')[-1]; repo = re.split(r'[:@]', name)[0]; env = {e.get('name'): e.get('value') for e in (j.get('env') or [])}
    by_digest = '@sha256:' in name; tag = (env.get('IMAGE_TAG') or 'unstamped') if by_digest else name.split(':')[-1]
    if repo == 'cmkg-sweep' and j['n'].startswith('iw-'): repo = 'cmkg-sweep (Issuerwire Ops Agents)'
    return {'repo': repo, 'tag': tag, 'digest': name.split('@')[-1] if by_digest else None, 'cron': j.get('cron'), 'modified': j.get('mod')}
TAGS = {j['n']: job_tag(j) for j in jobs}; rails = collections.Counter(v['tag'] for k, v in TAGS.items() if re.fullmatch(r'cmkg-[a-z]{2}-rail', k))
FLEET_TAG = rails.most_common(1)[0][0] if rails else None
snap = {'read_utc': now.isoformat(), 'read_by': 'capacity_snapshot.py (laptop, az, Allooloo tenant)',
        'environments': {'used': len(envs), 'limit': ENV_LIMIT, 'free': ENV_LIMIT - len(envs), 'regions': sorted({e['l'] for e in envs})},
        'doors': {'apps': len(apps), 'regions': sorted({a['l'] for a in apps}), 'images': sorted({a['img'].split(':')[-1] for a in apps})},
        'jobs': {'count': len(jobs), 'scheduled': sum(1 for j in jobs if j.get('cron')), 'images': sorted({v['tag'] for v in TAGS.values()}),
                 'tags': TAGS, 'fleet_tag': FLEET_TAG, 'fleet_tags_on_rails': dict(rails)},   # DIGEST-CAP-01 addendum: per job, read from the job definitions
        'stores': {'node_stores': sum(1 for s in stores if s['n'].endswith('pond')), 'regions': sorted({s['l'] for s in stores})}}
k = az('storage', 'account', 'keys', 'list', '-g', 'allooloo-cmkg-shared', '-n', 'allooloocmkgapex', '--query', '[0].value')
with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f: json.dump(snap, f, indent=1); fn = f.name
# BOOKOPS-02 (2026-11-01): the key goes in by environment (AZURE_STORAGE_KEY), never on the command line, and a failed upload prints the blob name and exit
# status only — never the command. latest.json is the copy of record (a failure stops the run); the dated copy is beside, never over one, so a second
# run in the same minute finds it written and that is not a failure.
rc_latest = 0
for name in ('capacity/latest.json', f'capacity/{now.date().isoformat()}-{now.strftime("%H%M")}.json'):
    r = subprocess.run([*AZ, 'storage', 'blob', 'upload', '--account-name', 'allooloocmkgapex', '-c', 'ops', '-n', name, '-f', fn, '--overwrite', 'true' if name.endswith('latest.json') else 'false', '--no-progress', '-o', 'none'],
                       env={**ENV, 'AZURE_STORAGE_KEY': k}, capture_output=True)
    if r.returncode:
        print(f'upload {name}: exit {r.returncode}' + ('' if name.endswith('latest.json') else ' (the dated copy is already written this minute; latest.json is the copy of record)'), file=sys.stderr, flush=True)
        if name.endswith('latest.json'): rc_latest = r.returncode
os.unlink(fn); print(json.dumps(snap, indent=1))
if rc_latest: sys.exit(rc_latest)
