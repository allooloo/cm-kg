r"""proof_enum01.py — ENUM-01 proof one (DAY ORDER 6, 2026-10-25): a synthetic market on a COPY of the roster, every rail's market list read through it with no
code change, then removed. Nothing is written to the wire: each rail's roster line is evaluated as written in its own file (the statements that call roster.*),
and the rails that carry policy keyed by market are run in their refuse path (they must name the synthetic market as a gap). Writes proof-enum01-<date>.json.
With --backfill (DAY ORDER 7, 2.1) the synthetic market also carries a backfill policy line and the backfill rail must generate its job.
Usage: python -X utf8 -I proof_enum01.py [--backfill]"""
import os, sys, json, re, subprocess, datetime, tempfile, shutil
R = r'C:\ALLOOLOO\CM-KG'; HERE = os.path.dirname(os.path.abspath(__file__)); DAY = datetime.date.today().isoformat()
NJ = os.path.join(R, 'DOOR', 'apex', 'static', 'nodes.json')
tmp = tempfile.mkdtemp(prefix='enum01-'); COPY = os.path.join(tmp, 'nodes.json')
roster = json.load(open(NJ, encoding='utf-8'))
ZZ = {'node': 'zz-cm-kg', 'country': 'Synthetica (ENUM-01 proof)', 'registry': None, 'door': 'https://mcp.zz-cm-kg.ai', 'live': True, 'as_of': DAY, 'records': 1, 'exchanges': ['XZZZ'], 'events': 1,
      'region': {'azure': 'East US', 'city': 'Virginia', 'store': 'eastus', 'door': 'eastus', 'door_azure': None, 'read_from': 'synthetic'}, 'duty': None, 'example': {'ticker': 'XZZZ:TEST', 'isin': 'ZZ0000000001', 'name': 'Synthetic Issuer'}}
json.dump(roster + [ZZ], open(COPY, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
ENV = dict(os.environ, ROSTER_FILE=COPY, ROSTER_OFFLINE='1', AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', PYTHONIOENCODING='utf-8')
out = {'proof': 'ENUM-01 proof one', 'date': DAY, 'roster_copy': COPY, 'roster_of_record_untouched': None, 'rails': []}
before = open(NJ, 'rb').read()

# (a) enumerations: each rail's own roster statement, evaluated as written in its file, through the copy
A = [(r'RAILS\job\job_digest.py', 'NODES', 'nightly digest rows (cmkg-apex-digest)'),
     (r'RAILS\job\job_apex.py', 'NODES', 'apex job: markers read, landed/close line (cmkg-apex-rail)'),
     (r'DOOR\apex\build_index.py', 'NODES', 'apex index builder: stores indexed'),
     (r'RAILS\snapshot_surfaces.py', 'NODES', 'surfaces snapshot (apex job nightly)'),
     (r'RAILS\door\load_nodes.py', 'NODES', 'door loader: nodes.json on every door'),
     (r'RAILS\job\alerts.py', 'NODES', 'Azure Monitor rules, one per job'),
     (r'ECO\build_eco.py', 'LIVE', 'eco-refresh: NODE LIVE on the ECO pages'),
     (r'ECO\build_specs.py', 'MARKETS', 'MARKET-SPECS (eco-refresh monthly)')]
code = r'''
import sys, os, re, json
f, var = sys.argv[1], sys.argv[2]; src = open(f, encoding="utf-8").read()
sys.path.insert(0, os.path.dirname(f)); import roster
ns = {"roster": roster, "os": os, "sys": sys, "json": json, "__file__": f}
for line in src.splitlines():
    s = line.strip()
    if re.match(r"^(NODES|LIVE|MARKETS|ROSTER_CC|DOORS|_door)\s*=.*roster\.", s) or s.startswith("roster.require("): exec(s, ns)
v = ns.get(var); print(json.dumps(sorted(v.keys()) if isinstance(v, dict) else sorted(x[0] if isinstance(x, (list, tuple)) else x for x in v)))
'''
for rel, var, what in A:
    p = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', code, os.path.join(R, rel), var], capture_output=True, text=True, env=ENV, encoding='utf-8')
    got = json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 and p.stdout.strip() else None
    out['rails'].append({'rail': rel, 'class': '(a)', 'what': what, 'reads': var, 'markets': len(got) if got else None, 'synthetic_picked_up': bool(got and 'zz' in got), 'error': None if got else (p.stderr or '')[-300:]})

# (b) policy keyed by market: the rail must refuse and name zz (no line for it)
B = [('provision_jobs.py status (region / ark / nightly maps)', [sys.executable, '-X', 'utf8', '-I', os.path.join(R, r'RAILS\job\provision_jobs.py'), 'status']),
     ('build_halts.py (halt-source policy from the ECO record)', [sys.executable, '-X', 'utf8', '-I', os.path.join(R, r'ACM-SIGNALS\build_halts.py')]),
     ('job_node.py market clock (STD_OFFSET)', [sys.executable, '-X', 'utf8', '-I', '-c', "import os,sys; sys.path.insert(0, r'" + os.path.join(R, r'RAILS\job') + "'); import roster; CC='zz'; src=open(r'" + os.path.join(R, r'RAILS\job\job_node.py') + "',encoding='utf-8').read(); i=src.index('STD_OFFSET = {'); j=src.index('def last_trading'); ns={}; exec(src[i:j], ns); STD_OFFSET=ns['STD_OFFSET']; exec([l for l in src.splitlines() if l.startswith(\"if CC != 'apex' and CC not in STD_OFFSET\")][0])"])]
for what, cmd in B:
    p = subprocess.run(cmd, capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    msg = ((p.stderr or '') + (p.stdout or '')).strip().splitlines()
    gap = next((l for l in msg if 'ROSTER POLICY GAP' in l), None)
    out['rails'].append({'rail': what, 'class': '(b)', 'refused': p.returncode != 0, 'gap_line': gap, 'synthetic_named': bool(gap and 'zz' in gap)})

# (c) infrastructure: refuses without an ark-region line for zz (named); with the synthetic policy overlay it generates zz's bucket, IAM, certificate and standby lines
p = subprocess.run([sys.executable, '-X', 'utf8', '-I', os.path.join(HERE, 'infra_from_roster.py'), '--out', os.path.join(tmp, 'infra')], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
gap = next((l for l in ((p.stderr or '') + (p.stdout or '')).splitlines() if 'ROSTER POLICY GAP' in l), None)
out['rails'].append({'rail': 'infra_from_roster.py (ark bucket · IAM · Origin CA · standby)', 'class': '(c)', 'refused': p.returncode != 0, 'gap_line': gap, 'synthetic_named': bool(gap and 'zz' in gap)})
pj = os.path.join(R, r'RAILS\job\provision_jobs.py'); pj_text = open(pj, encoding='utf-8').read()
ov = os.path.join(tmp, 'enum'); shutil.copytree(HERE, ov, ignore=shutil.ignore_patterns('infra-*', '__pycache__')); os.makedirs(os.path.join(tmp, 'job'), exist_ok=True)
open(os.path.join(tmp, 'job', 'provision_jobs.py'), 'w', encoding='utf-8').write(pj_text.replace("ARK = {'hk': 'ap-east-1',", "ARK = {'zz': 'us-east-1', 'hk': 'ap-east-1',", 1))   # the policy line a new market brings (in the copy only)
p = subprocess.run([sys.executable, '-X', 'utf8', '-I', os.path.join(ov, 'infra_from_roster.py'), '--out', os.path.join(tmp, 'infra2')], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
gen = json.load(open(os.path.join(tmp, 'infra2', 'infra.json'), encoding='utf-8')) if p.returncode == 0 else {'nodes': []}
zz = next((l for l in gen['nodes'] if l['node'] == 'zz-cm-kg'), None)
out['rails'].append({'rail': 'infra_from_roster.py with the synthetic policy line (copy of provision_jobs ARK + zz)', 'class': '(c)', 'nodes_generated': len(gen['nodes']), 'synthetic_generated': zz})

if '--backfill' in sys.argv:   # DAY ORDER 7 §2.1: the backfill rail generates the synthetic market's job from a policy line, no code change
    pol = json.load(open(os.path.join(R, r'RAILS\backfill\policy.json'), encoding='utf-8'))
    pol['markets']['zz'] = {'archive': 'Synthetic Archive', 'base_url': 'https://archive.example.invalid/', 'earliest': '2021-01-01', 'licence_note': 'synthetic (ENUM-01 proof)', 'reader': 'keyless', 'adapter': 'synthetic', 'rate': {'rps': 1}, 'wave': 9}
    pcopy = os.path.join(tmp, 'backfill-policy.json'); json.dump(pol, open(pcopy, 'w', encoding='utf-8'), indent=1)
    for label, env in (('without a backfill line', ENV), ('with a backfill line', dict(ENV, BACKFILL_POLICY=pcopy))):
        p = subprocess.run([sys.executable, '-X', 'utf8', '-I', os.path.join(R, r'RAILS\backfill\backfill_jobs.py'), 'plan'], capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
        txt = (p.stdout or '') + (p.stderr or '')
        out['rails'].append({'rail': f'backfill_jobs.py plan ({label})', 'class': 'BACKFILL', 'exit': p.returncode, 'zz_line': next((l for l in txt.splitlines() if 'zz' in l), None)})

shutil.rmtree(tmp, ignore_errors=True)
out['synthetic_removed'] = not os.path.exists(COPY)
out['roster_of_record_untouched'] = open(NJ, 'rb').read() == before and 'zz-cm-kg' not in open(NJ, encoding='utf-8').read()
fn = os.path.join(HERE, f'proof-enum01-{DAY}' + ('-backfill' if '--backfill' in sys.argv else '') + '.json'); json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in out['rails']: print(json.dumps(r, ensure_ascii=False)[:260])
print('synthetic removed:', out['synthetic_removed'], '· roster of record untouched:', out['roster_of_record_untouched'], '->', fn)
