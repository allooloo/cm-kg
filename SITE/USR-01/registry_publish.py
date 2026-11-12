import os, subprocess, json, urllib.request, shutil
PUB = r'C:\ALLOOLOO\CM-KG\DOOR\.tools\mcp-publisher.exe'; D = r'C:\ALLOOLOO\CM-KG\DOOR\getresearch\registry'; shutil.copy2(os.path.join(D, 'getresearch.server.json'), os.path.join(D, 'server.json'))
tok = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, env=dict(os.environ, GH_CONFIG_DIR=r'C:\ALLOOLOO\.gh')).stdout.strip(); assert tok, 'no gh token'
r = subprocess.run([PUB, 'login', 'github', '--token', tok], capture_output=True, text=True, cwd=D); print('login', r.returncode, (r.stdout + r.stderr).replace(tok, '***')[-200:].strip())
r = subprocess.run([PUB, 'publish', 'server.json'], capture_output=True, text=True, cwd=D); print('publish', r.returncode, (r.stdout + r.stderr).replace(tok, '***')[-300:].strip())
j = json.load(urllib.request.urlopen(urllib.request.Request('https://registry.modelcontextprotocol.io/v0/servers?search=io.github.allooloo/getresearch', headers={'User-Agent': 'Allooloo USR-04'}), timeout=30))
print([(s['server']['name'], s['server']['version'], (s.get('_meta') or {}).get('io.modelcontextprotocol.registry/official', {}).get('status')) for s in j.get('servers', [])])
