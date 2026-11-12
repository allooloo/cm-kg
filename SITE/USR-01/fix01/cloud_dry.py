r"""cloud_dry.py — FIX-01 item 2 proof: one PLAN-ONLY execution of the one job (cmkg-apex-rail, RESLATE_DRY=1: nothing is started, no Tavily read is
made, only the free /usage counter and the job definitions are read). Prints the job's own log: the yield order and the Tavily meter as shared out.
Usage: python -X utf8 -I cloud_dry.py"""
import json, os, subprocess, sys, time, pathlib
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
JOB, RG = 'cmkg-apex-rail', 'allooloo-cmkg-eastus'; H = pathlib.Path(__file__).parent
def az(*a, js=True):
    r = subprocess.run([*AZ, *a, '-o', 'json' if js else 'tsv'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace')
    if r.returncode: sys.exit(f'STOP az {" ".join(a[:4])}: {r.stderr[-500:]}')
    return (json.loads(r.stdout) if r.stdout.strip() else None) if js else r.stdout.strip()
img = az('containerapp', 'job', 'show', '-n', JOB, '-g', RG, '--query', 'properties.template.containers[0].image', js=False); y = H / 'cloud-dry.yaml'
y.write_text(json.dumps({'containers': [{'name': JOB, 'image': img, 'command': ['/usr/local/bin/python3', '/job/ALLOOLOO/CM-KG/RAILS/job/job_reslate.py'], 'resources': {'cpu': 1.0, 'memory': '2Gi'},
    'env': [{'name': 'RESLATE_DRY', 'value': '1'}, {'name': 'RESLATE_TAVILY_USD', 'value': '500'}, {'name': 'RESLATE_PPLX_USD', 'value': '500'}, {'name': 'TAVILY_API_KEY', 'secretRef': 'tavily-key'}]}]}, indent=1), encoding='utf-8')
x = az('containerapp', 'job', 'start', '-n', JOB, '-g', RG, '--yaml', str(y)); ex = x.get('name') or x['id'].split('/')[-1]; print('execution', ex, 'image', img[-30:], flush=True)
while True:
    time.sleep(30); st = az('containerapp', 'job', 'execution', 'show', '-n', JOB, '-g', RG, '--job-execution-name', ex, '--query', 'properties.status', js=False)
    if st not in ('Running', 'Processing', 'Unknown', ''): break
print('status', st); time.sleep(20)
r = subprocess.run([*AZ, 'containerapp', 'job', 'logs', 'show', '-n', JOB, '-g', RG, '--execution', ex, '--container', JOB, '--tail', '300'], capture_output=True, text=True, env=ENV, encoding='utf-8', errors='replace'); lines = []
for l in r.stdout.splitlines():
    try: lines.append(json.loads(l).get('Log', ''))
    except Exception: pass
open(H / 'cloud-dry.log', 'w', encoding='utf-8').write('\n'.join(lines))
for l in lines:
    if any(w in l for w in ('RESLATE-01', 'Tavily', 'yield order', 'STOP', 'FAILED', '"run_meter"', 'meter_credits')): print(l[:400])
