r"""fix_envhost.py — NODE-EU (DAY ORDER 4, 2026-10-24): the subscription holds its maximum of Container Apps environments (16; Azure answered
MaxNumberOfGlobalEnvironmentsInSubExceeded on Belgium Central). Until the quota is raised (CEO's hand), a European node whose region has no environment
keeps its store in its own region and resource group, and runs its door and its job in the nearest existing environment (same nearest-region rule as
dk/fi in Sweden Central, pt in Spain Central, gr in Italy North). The app and the job stay in the node's own resource group; only the environment
(and so the compute location) is the host's. Flagged per node in the report.
  ENV_HOST = {be, lu, ie: westeurope · at, pl, cz: germanywestcentral}
provision_region.py.pre-envhost-20261024 and provision_jobs.py.pre-envhost-20261024 beside."""
import io, os, shutil
HOST = "ENV_HOST = {'be': 'westeurope', 'lu': 'westeurope', 'ie': 'westeurope', 'at': 'germanywestcentral', 'pl': 'germanywestcentral', 'cz': 'germanywestcentral'}   # NODE-EU 2026-10-24: environment quota reached; door + job in the nearest existing environment, store in the node's region"
def patch(p, subs):
    if not os.path.exists(p + '.pre-envhost-20261024'): shutil.copy2(p, p + '.pre-envhost-20261024')
    t = io.open(p, encoding='utf-8', newline='').read()
    for o, n in subs:
        assert t.count(o) == 1, (p, o[:70]); t = t.replace(o, n)
    io.open(p, 'w', encoding='utf-8', newline='').write(t); print('patched', p)
if False: patch(r'C:\ALLOOLOO\AZURE\provision_region.py', [
    ("env_name = open(rf'C:\\ALLOOLOO\\AZURE\\env-{cc}.txt').read().strip()", HOST + "\nenv_name = open(rf'C:\\ALLOOLOO\\AZURE\\env-{cc}.txt').read().strip()"),
    ("    for suffix in ('', '-2', '-3'):\n",
     "    if cc in ENV_HOST:   # NODE-EU (2026-10-24): the host region's environment, by resource id; the app stays in the node's group\n"
     "        hrg = f'allooloo-cmkg-{ENV_HOST[cc]}'; env_name = az('containerapp', 'env', 'list', '-g', hrg, '--query', \"[?properties.provisioningState=='Succeeded'].id | [0]\", '-o', 'tsv', raw=True)\n"
     "        if not env_name: raise SystemExit(f'no environment in {hrg}')\n"
     "        log(f'environment: host {env_name.split(\"/\")[-1]} ({ENV_HOST[cc]}); the store stays in {region}')\n"
     "    for suffix in (() if cc in ENV_HOST else ('', '-2', '-3')):\n"),
    ("    else: raise SystemExit('no usable environment')\n",
     "    else:\n        if cc not in ENV_HOST: raise SystemExit('no usable environment')\n"),
])
patch(r'C:\ALLOOLOO\CM-KG\RAILS\job\provision_jobs.py', [
    ("LAB = ['tavily',", HOST + "\nLAB = ['tavily',"),
    ("az('containerapp', 'job', 'create', '-n', job, '-g', rg, '--environment', env_name(rg), '--trigger-type', 'Schedule', '--cron-expression', PARKED, '--replica-timeout', '36000',",
     "az('containerapp', 'job', 'create', '-n', job, '-g', rg, '--environment', (az('containerapp', 'env', 'list', '-g', f'allooloo-cmkg-{ENV_HOST[cc]}', '--query', \"[?properties.provisioningState=='Succeeded'].id | [0]\", '-o', 'tsv', raw=True) if cc in ENV_HOST else env_name(rg)), '--trigger-type', 'Schedule', '--cron-expression', PARKED, '--replica-timeout', '36000',"),
])
