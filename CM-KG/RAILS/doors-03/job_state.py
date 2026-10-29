r"""DOORS-03 — print the latest execution status of the named node rail jobs, one line: cc=status ... Usage: python -X utf8 -I job_state.py ca us"""
import sys, json, subprocess, os
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
def az(*a): p = subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8'); return json.loads(p.stdout) if p.stdout.strip() else None
rg = {r.split('\t')[0]: r.split('\t')[1] for r in open(os.path.join(os.environ.get('TEMP', '.'), 'claude', 'cmkg-jobs.tsv'), encoding='utf-8').read().splitlines() if '\t' in r}
out = []
for cc in sys.argv[1:]:
    j = f'cmkg-{cc}-rail'; e = az('containerapp', 'job', 'execution', 'list', '-n', j, '-g', rg[j], '--query', 'sort_by([], &properties.startTime)[-1].{n:name,s:properties.status,e:properties.endTime}')
    out.append(f"{cc}={e['s'] if e else '?'}")
print(' '.join(out), flush=True)
