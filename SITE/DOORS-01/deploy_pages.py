r"""deploy_pages.py — DOORS-01: wrangler deploy of getdoors-pages (new: the three door pages), getasof-pages and gettargetmarket-pages (the three-band footer) from
the estate source on disk. The Cloudflare token is read in-process, never printed. A failed deploy stops the run. Usage: python -X utf8 -I deploy_pages.py"""
import os, sys, subprocess
env = dict(os.environ, CLOUDFLARE_API_TOKEN=open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0], CLOUDFLARE_ACCOUNT_ID='dd2832b36f171b815f84c8487aada36b')
for d in (r'C:\ALLOOLOO\CM-KG\DOOR\getdoors', r'C:\ALLOOLOO\CM-KG\DOOR\getasof', r'C:\ALLOOLOO\CM-KG\DOOR\gettargetmarket'):
    r = subprocess.run('npx -y wrangler@4 deploy', cwd=d, shell=True, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(os.path.basename(d), 'exit', r.returncode, [l.strip() for l in (r.stdout + r.stderr).splitlines() if 'Version ID' in l or 'ERROR' in l][:3])
    if r.returncode: sys.exit('STOP: deploy failed in ' + d)
