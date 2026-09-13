"""API CENTER (CEO, Sept 13 2026): description of record on the twelve MCP assets; contact mk@allooloo.ai on all thirteen; titles carry the node
("… apex router", "… Canada door" …). PUT by az rest with @file bodies; every other property carried forward unchanged. Tenant check first."""
import json, subprocess, os, tempfile, sys
API = '2024-06-01-preview'
B = 'https://management.azure.com/subscriptions/038b49c0-5a0c-46f7-bd34-41ee6d087b41/resourceGroups/allooloo-cmkg-shared/providers/Microsoft.ApiCenter/services/allooloo-apic/workspaces/default'
def az(method, path, body=None):
    cmd = ['az', 'rest', '--method', method, '--url', f'{B}{path}?api-version={API}', '-o', 'json']; f = None
    if body is not None:
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8'); json.dump(body, f, ensure_ascii=False); f.close(); cmd += ['--body', '@' + f.name]
    r = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if f: os.unlink(f.name)
    if r.returncode != 0: return {'error': (r.stderr or r.stdout).strip()[:300]}
    try: return json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception: return {'raw': r.stdout[:200]}
sys.path.insert(0, r'C:\ALLOOLOO\AZURE'); from az_guard import require_allooloo; require_allooloo()   # STANDING RULE Sept 13 2026: tenant + subscription + user, stop on mismatch
DESC = ("What: KYP Agentic Trading with the Capital Markets Knowledge Graph — one public-record file per listed company across eleven national markets, "
        "identity through disclosure trail, each field carrying its source and the date it was read, served from the issuer's own jurisdiction over the "
        "Model Context Protocol and the Agent-to-Agent protocol. Why: So an agent acting for a licensed capital markets participant with a Know Your Product (KYP) "
        "obligation hands back a fact that can be defended. The KYP model runs on this record. No prices, no quotes, no licensed data.")
CONTACT = [{'email': 'mk@allooloo.ai', 'name': 'Allooloo Technologies Corp.', 'url': 'https://allooloo.io'}]
NODES = {'ca': 'Canada', 'uk': 'United Kingdom', 'us': 'United States', 'de': 'Germany', 'fr': 'France', 'nl': 'Netherlands', 'ch': 'Switzerland', 'au': 'Australia', 'sg': 'Singapore', 'jp': 'Japan', 'kr': 'South Korea'}
titles = {f'cm-kg-{cc}': f'Capital Markets Agents: MCP+A2A {n} door' for cc, n in NODES.items()}
titles['cm-kg-uk'] = 'Capital Markets Agents: MCP+A2A UK door'   # API Center caps title at 50 chars; 'United Kingdom door' makes 51
titles['cm-kg-apex'] = 'Capital Markets Agents: MCP+A2A apex router'
KEEP = ('title', 'kind', 'summary', 'description', 'lifecycleStage', 'externalDocumentation', 'contacts', 'license', 'termsOfService', 'customProperties')
lines = []
for api in list(titles) + ['agentic-x402-api']:
    cur = az('GET', f'/apis/{api}')
    if 'error' in cur: lines.append(f'{api}: GET failed {cur["error"]}'); continue
    props = {k: v for k, v in cur['properties'].items() if k in KEEP}
    props['contacts'] = CONTACT
    if api in titles: props['title'] = titles[api]; props['description'] = DESC
    up = az('PUT', f'/apis/{api}', {'properties': props})
    back = az('GET', f'/apis/{api}').get('properties', {})
    ok = back.get('contacts', [{}])[0].get('email') == 'mk@allooloo.ai' and (api not in titles or (back.get('description') == DESC and back.get('title') == titles[api]))
    lines.append(f"{api}: {'ok' if ok and 'error' not in up else 'FAILED ' + str(up.get('error', ''))[:600].replace(chr(10),' ')} · title \"{back.get('title')}\" · contact {back.get('contacts', [{}])[0].get('email')} · description {len(back.get('description') or '')} chars")
print('\n'.join(lines))
json.dump({'lines': lines}, open(r'C:\ALLOOLOO\AZURE\apic-descriptions-2026-09-13.json', 'w'), indent=1)
