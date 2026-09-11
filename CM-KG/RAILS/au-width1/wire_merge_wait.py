"""Build-day helper (2026-09-11): wait until the three wire_search shards cover every issuer (or all report DONE), stop the shards, merge b and c into
raw/wire_search.jsonl by key (first write wins), and append the DONE line the assembly waiter looks for."""
import json, os, time, subprocess
from common import load_issuers, key
n_iss = len(load_issuers()); files = ['raw/wire_search.jsonl', 'raw/wire_search_b.jsonl', 'raw/wire_search_c.jsonl']; logs = ['raw/wire_search.log', 'raw/wire_search_b.log', 'raw/wire_search_c.log']
def keys(fn):
    ks = set()
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try: ks.add(json.loads(line)['key'])
            except Exception: pass
    return ks
while True:
    u = set().union(*[keys(f) for f in files]); done = all(os.path.exists(l) and 'DONE' in open(l).read() for l in logs)
    print('covered', len(u), '/', n_iss, 'all done', done, flush=True)
    if len(u) >= n_iss or done: break
    time.sleep(60)
subprocess.call(['powershell', '-NoProfile', '-Command', "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*wire_search*.py*' -and $_.CommandLine -notlike '*wire_merge_wait*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"])
time.sleep(3)
have = keys('raw/wire_search.jsonl'); added = 0
with open('raw/wire_search.jsonl', 'a', encoding='utf-8') as out:
    for fn in files[1:]:
        if not os.path.exists(fn): continue
        for line in open(fn, encoding='utf-8'):
            try: d = json.loads(line)
            except Exception: continue
            if d['key'] in have: continue
            have.add(d['key']); out.write(json.dumps(d, ensure_ascii=False) + '\n'); added += 1
print('merged', added, 'total keys', len(have), flush=True)
open('raw/wire_search.log', 'a').write('wire_search DONE (merged shards)\n')
