r"""reslate_local.py — RESLATE-01, the run of 2026-11-12: the one job (cmkg-apex-rail) holds Contributor on thirteen resource groups only, so it could start
sixteen markets; the other eighteen are started from the agent's shell by the same job_reslate.py (RESLATE_ONLY), under the same night and the SAME Tavily
meter the cloud run set (its account ceiling, argv[1]). The Tavily key is read in-process for the free /usage read only; never printed.
Usage: python -X utf8 reslate_local.py <account ceiling of the run> <cc,cc,...>"""
import os, sys, json, runpy, urllib.request
ceiling = int(sys.argv[1]); os.environ['RESLATE_ONLY'] = sys.argv[2]; os.environ['RESLATE_SKIP'] = 'apex,others,publish,digest'; os.environ['RESLATE_WAIT_HOURS'] = '11'
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'; os.environ['CMKG_ROOT'] = r'C:\ALLOOLOO'; os.environ['NIGHT'] = '2026-11-12'
os.environ['TAVILY_API_KEY'] = open(r'C:\ALLOOLOO\AGENT KEYS\tavily.txt', encoding='utf-8').read().strip().splitlines()[0]
a = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.tavily.com/usage', headers={'Authorization': 'Bearer ' + os.environ['TAVILY_API_KEY']}), timeout=30).read()).get('account') or {}
used = (a.get('plan_usage') or 0) + (a.get('paygo_usage') or 0); left = max(ceiling - used, 0); os.environ['RESLATE_TAVILY_USD'] = str(left * 0.008)
print('account counter', used, '· the run stops at', ceiling, '· credits left on the meter', left, flush=True)
sys.argv = ['job_reslate.py']; sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\job'); os.chdir(r'C:\ALLOOLOO\CM-KG\RAILS\job'); runpy.run_path('job_reslate.py', run_name='__main__')
