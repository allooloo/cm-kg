r"""patch_drift.py — FIX-01 item 5: the capacity snapshot written from what runs, and the digest reading the fleet tag from it.
Cause of the 33 DRIFT: every fleet job now names its image BY DIGEST (cmkg-sweep@sha256:…), so the snapshot's "repo:tag" split found no cmkg-sweep tag at
all; and the digest took the fleet tag of record from a setting typed on the one job (FLEET_TAG=0.35.54) while every market ran 0.35.61.
  capacity_snapshot.py   per job: repo = the image name without tag or digest; tag = the image tag, or — when the image is named by digest — the version
                         the job itself stamps on its run (its IMAGE_TAG, the same string its marker carries); the digest is kept beside. A job on the
                         fleet image that runs another product's code (Issuerwire's Ops Agents) is recorded under its own repo name, not as a sweep.
                         fleet_tag = the tag the market rails (cmkg-<cc>-rail) run — read, never typed; if they do not all agree, every tag is listed.
  job_digest.py          the fleet tag of record = the snapshot's fleet_tag when it has one; the typed setting only as the fallback.
No job definition is changed. Every replacement must match once. .pre copies are kept. Usage: python -X utf8 -I patch_drift.py"""
import ast, pathlib, shutil, sys
J = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\job')
def patch(name, pairs):
    p = J / name; pre = J / name.replace('.py', '.pre-fix01-2026-11-12.py'); s = p.read_text(encoding='utf-8')
    if 'FIX-01' in s: print(name, 'already patched'); return
    if not pre.exists(): shutil.copy2(p, pre)
    for o, n in pairs:
        if s.count(o) != 1: sys.exit(f'STOP {name}: {s.count(o)} of 1 for {o[:90]!r}')
        s = s.replace(o, n)
    ast.parse(s); p.write_text(s, encoding='utf-8', newline='\n'); print('patched', name)
patch('capacity_snapshot.py', [
    ("'[].{n:name,l:location,img:properties.template.containers[0].image,cron:properties.configuration.scheduleTriggerConfig.cronExpression,mod:systemData.lastModifiedAt}')",
     "'[].{n:name,l:location,img:properties.template.containers[0].image,cron:properties.configuration.scheduleTriggerConfig.cronExpression,mod:systemData.lastModifiedAt,env:properties.template.containers[0].env}')"),
    ("now = datetime.datetime.now(datetime.timezone.utc)\n",
     "now = datetime.datetime.now(datetime.timezone.utc)\n"
     "# FIX-01 (2026-11-12): from what runs. A job names its image by tag (repo:tag) or by digest (repo@sha256:…); by digest there is no tag in the name, so the\n"
     "# tag is the version the job stamps on its own run (IMAGE_TAG — the string its marker carries). Issuerwire's jobs ride the fleet image but run their own code.\n"
     "import re, collections\n"
     "def job_tag(j):\n"
     "    img = j['img']; name = img.split('/')[-1]; repo = re.split(r'[:@]', name)[0]; env = {e.get('name'): e.get('value') for e in (j.get('env') or [])}\n"
     "    by_digest = '@sha256:' in name; tag = (env.get('IMAGE_TAG') or 'unstamped') if by_digest else name.split(':')[-1]\n"
     "    if repo == 'cmkg-sweep' and j['n'].startswith('iw-'): repo = 'cmkg-sweep (Issuerwire Ops Agents)'\n"
     "    return {'repo': repo, 'tag': tag, 'digest': name.split('@')[-1] if by_digest else None, 'cron': j.get('cron'), 'modified': j.get('mod')}\n"
     "TAGS = {j['n']: job_tag(j) for j in jobs}; rails = collections.Counter(v['tag'] for k, v in TAGS.items() if re.fullmatch(r'cmkg-[a-z]{2}-rail', k))\n"
     "FLEET_TAG = rails.most_common(1)[0][0] if rails else None\n"),
    ("'images': sorted({j['img'].split(':')[-1] for j in jobs}),\n                 'tags': {j['n']: {'repo': j['img'].split('/')[-1].split(':')[0], 'tag': j['img'].split(':')[-1], 'cron': j.get('cron'), 'modified': j.get('mod')} for j in jobs}},",
     "'images': sorted({v['tag'] for v in TAGS.values()}),\n                 'tags': TAGS, 'fleet_tag': FLEET_TAG, 'fleet_tags_on_rails': dict(rails)},"),
])
patch('job_digest.py', [
    ("    FLEET = os.environ.get('FLEET_TAG') or IMAGE_TAG;",
     "    FLEET = ((cap.get('provisioned') or {}).get('jobs') or {}).get('fleet_tag') or os.environ.get('FLEET_TAG') or IMAGE_TAG;   # FIX-01 (2026-11-12): the fleet tag is read from what runs (the capacity snapshot), the typed setting is the fallback\n    #"),
])
