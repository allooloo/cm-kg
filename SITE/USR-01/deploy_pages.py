r"""deploy_pages.py — USR-03: wrangler deploy of page Workers from the estate source on disk. The Cloudflare token is read in-process, never printed.
A failed deploy stops the run. Usage: python -X utf8 -I deploy_pages.py getresearch [getdoors getasof gettargetmarket]"""
import os, sys, subprocess
env = dict(os.environ, CLOUDFLARE_API_TOKEN=open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0], CLOUDFLARE_ACCOUNT_ID='dd2832b36f171b815f84c8487aada36b')
for n in sys.argv[1:]:
    d = os.path.join(r'C:\ALLOOLOO\CM-KG\DOOR', n)
    r = subprocess.run('npx -y wrangler@4 deploy', cwd=d, shell=True, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(n, 'exit', r.returncode, [l.strip() for l in (r.stdout + r.stderr).splitlines() if 'Version ID' in l or 'ERROR' in l or 'error' in l.lower()][:4])
    if r.returncode: sys.exit('STOP: deploy failed in ' + d)
