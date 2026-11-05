r"""registry_publish.py — ASOF-01: io.github.allooloo/getasof 0.1.0 to registry.modelcontextprotocol.io with the GitHub sign-in already on this machine
(C:\ALLOOLOO\.gh, account allooloo), passed in-process; never printed. Usage: python -X utf8 -I registry_publish.py"""
import os, subprocess, json, urllib.request
PUB = r'C:\ALLOOLOO\CM-KG\DOOR\.tools\mcp-publisher.exe'; D = r'C:\ALLOOLOO\CM-KG\DOOR\getasof\registry'
tok = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, env=dict(os.environ, GH_CONFIG_DIR=r'C:\ALLOOLOO\.gh')).stdout.strip()
assert tok, 'no gh token'
r = subprocess.run([PUB, 'login', 'github', '--token', tok], capture_output=True, text=True, cwd=D); print('login', r.returncode, (r.stdout + r.stderr).replace(tok, '***')[-200:].strip())
r = subprocess.run([PUB, 'publish', 'server.json'], capture_output=True, text=True, cwd=D); print('publish', r.returncode, (r.stdout + r.stderr).replace(tok, '***')[-300:].strip())
j = json.load(urllib.request.urlopen(urllib.request.Request('https://registry.modelcontextprotocol.io/v0/servers?search=io.github.allooloo/getasof', headers={'User-Agent': 'Allooloo ASOF-01'}), timeout=30))
print([(s['server']['name'], s['server']['version'], (s.get('_meta') or {}).get('io.modelcontextprotocol.registry/official', {}).get('status')) for s in j.get('servers', [])])
