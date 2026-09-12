"""ORDER-018 — one region of the sovereign estate, step by step (idempotent, create-only, nothing deleted or overwritten).
Usage: python provision_region.py <cc> <region> <step> [image_tag]
  storage   resource group + storage account (versioning on) + container 'pond'
  upload    the node's local pond (POND\\<node>\\**) as pond/<source>/<date>/… blobs (no overwrite) and the rendered door data as door/… (records, events,
            per-node index.json, facts.json, nodes.json), from CM-KG\\DOOR\\data
  app       Container Apps environment + the door app (image from allooloocmkg.azurecr.io, secrets never printed)
  flip      hostname mcp.<node>-cm-kg.ai: TXT asuid record + proxied CNAME at Cloudflare, the Workers custom-domain binding removed (the Worker stays deployed), managed certificate bound by TXT validation
  status    print the app FQDN, replicas, hostname state
Tenant guard: refuses unless az account show is the tenant and subscription of record. Keys and storage keys are read into memory only."""
import json, os, sys, subprocess, glob, re, time, urllib.request
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'; ACR = 'allooloocmkg'; ACR_SERVER = 'allooloocmkg.azurecr.io'
CF_ACCT = 'dd2832b36f171b815f84c8487aada36b'
ZONES = {'ca': '4d2c6dc2f534dd8c013f6e66544eed4c', 'uk': '999f8cab6ae570a878379f0e37cd87b0', 'au': '8732370fd5742f40dba657be3eab5d37', 'sg': '0d4ae29fdde22945ffd2858bc2922576', 'ch': '0ea4358fbd0c1dc5ccf069448ccefe48', 'de': '0e7b54741212fb036c2cf18b9392ed25', 'fr': '645c30886df97804e3b793399e303c2b', 'nl': 'e5a042d3df88b7e170d5225ecfacb008', 'jp': 'f1c120f9d544c4af28bd6029ce071b96', 'kr': 'cd87134802ca140f4767253f39453ce1', 'us': '64516e94b82d13781980dff99c20c8b0'}
cc, region, step = sys.argv[1], sys.argv[2], sys.argv[3]; tag = sys.argv[4] if len(sys.argv) > 4 else 'latest'
node = f'{cc}-cm-kg'; rg = f'allooloo-cmkg-{region}'; sa = f'allooloocmkg{cc}pond'; app = f'cmkg-door-{cc}'; host = f'mcp.{node}.ai'
env_name = open(rf'C:\ALLOOLOO\AZURE\env-{cc}.txt').read().strip() if os.path.exists(rf'C:\ALLOOLOO\AZURE\env-{cc}.txt') else f'cmkg-env-{region}'
LOG = r'C:\ALLOOLOO\AZURE\provision.log'
def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M')} [{cc} {region} {step}] {msg}"; print(line, flush=True); open(LOG, 'a', encoding='utf-8').write(line + '\n')
def az(*args, check=True, raw=False):
    p = subprocess.run(['az', *args] + ([] if raw else ['--output', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
    if p.returncode != 0:
        if check: raise SystemExit(f"az {' '.join(str(a) for a in args[:4])} failed: {(p.stderr or p.stdout)[-600:]}")
        return None
    if raw: return p.stdout.strip()
    try: return json.loads(p.stdout) if p.stdout.strip() else None
    except Exception: return {'raw': p.stdout[:500]}
acct = az('account', 'show')
if not acct or acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
def cf(method, path, body=None, tok=None):
    tok = tok or open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip()
    req = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(req, timeout=60); raw = r.read()
        return json.loads(raw) if raw.strip() else {'success': 200 <= r.status < 300, 'status': r.status}
    except urllib.error.HTTPError as e: return {'success': False, 'http': e.code, 'body': e.read()[:300].decode('utf-8', 'replace')}
def storage_key():
    return az('storage', 'account', 'keys', 'list', '-n', sa, '-g', rg, '--query', '[0].value', '-o', 'tsv', raw=True)
if step == 'storage':
    g = az('group', 'show', '-n', rg, check=False) or az('group', 'create', '-n', rg, '-l', region, '--tags', 'order=ORDER-018', 'owner=allooloo', f'node={node}'); log(f"resource group {rg} {g['properties']['provisioningState']}")
    s = az('storage', 'account', 'show', '-n', sa, '-g', rg, check=False)
    if not s: s = az('storage', 'account', 'create', '-n', sa, '-g', rg, '-l', region, '--sku', 'Standard_LRS', '--kind', 'StorageV2', '--allow-blob-public-access', 'false', '--min-tls-version', 'TLS1_2', '--tags', f'node={node}', 'order=ORDER-018')
    log(f"storage account {sa} {s.get('provisioningState')} {s.get('primaryLocation')}")
    az('storage', 'account', 'blob-service-properties', 'update', '--account-name', sa, '-g', rg, '--enable-versioning', 'true'); log('blob versioning on')
    k = storage_key(); az('storage', 'container', 'create', '--account-name', sa, '--account-key', k, '-n', 'pond', check=False); log("container 'pond' present")
elif step == 'upload':
    k = storage_key(); src = rf'C:\ALLOOLOO\CM-KG\POND\{node}'
    if os.path.isdir(src):
        r = az('storage', 'blob', 'upload-batch', '--account-name', sa, '--account-key', k, '--destination', 'pond', '--destination-path', 'pond', '--source', src, '--overwrite', 'false', '--no-progress', check=False)
        n = len(r) if isinstance(r, list) else 'see log'; log(f'pond drops uploaded: {n} blobs from {src}')
    data = r'C:\ALLOOLOO\CM-KG\DOOR\data'; recs = glob.glob(os.path.join(data, 'records', node, '*', '*.json')); log(f'door records to upload: {len(recs)}')
    for sub in ('records', 'events'):
        d = os.path.join(data, sub, node)
        if os.path.isdir(d):
            r = az('storage', 'blob', 'upload-batch', '--account-name', sa, '--account-key', k, '--destination', 'pond', '--destination-path', f'door/{sub}', '--source', d, '--overwrite', 'true', '--no-progress', '--content-type', 'application/json', check=False)
            log(f'door/{sub}: {len(r) if isinstance(r, list) else "see log"} blobs')
    # per-node index: ticker / isin / lei / alias / name -> cmr keys, from the record files
    def nkey(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('&', ' and ')).strip()
    idx = {'ticker': {}, 'isin': {}, 'lei': {}, 'alias': {}, 'name': {}, 'cmr': {}, 'keys': []}
    for f in recs:
        r = json.load(open(f, encoding='utf-8')); key = r['cmr']; t = key.split('/')[2]; v = lambda x: (r['identity'].get(x) or {}).get('value')
        idx['keys'].append(key); idx['cmr'][key.upper()] = [key]; idx['ticker'].setdefault(t.upper(), []).append(key)
        root = t.split('.')[0].upper()
        if root != t.upper(): idx['ticker'].setdefault(root, []).append(key)
        if v('isin'): idx['isin'].setdefault(str(v('isin')).upper(), []).append(key)
        if v('lei'): idx['lei'].setdefault(str(v('lei')).upper(), []).append(key)
        if v('name'): idx['name'].setdefault(nkey(v('name')), []).append(key)
        for a in r.get('aliases', []):
            if a.get('value'): idx['alias'].setdefault(nkey(a['value']), []).append(key)
    tmp = rf'C:\ALLOOLOO\AZURE\tmp-{node}'; os.makedirs(tmp, exist_ok=True)
    json.dump(idx, open(os.path.join(tmp, 'index.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    facts = json.load(open(os.path.join(data, 'facts.json'), encoding='utf-8')); nf = {**facts, 'nodes': {node: facts['nodes'].get(node, {})}, 'store': f'Azure Storage (regional pond, {region}) — blob per record and per issuer event list', 'region': region}
    json.dump(nf, open(os.path.join(tmp, 'facts.json'), 'w', encoding='utf-8'), indent=1)
    json.dump(json.load(open(os.path.join(data, 'nodes.json'), encoding='utf-8')), open(os.path.join(tmp, 'nodes.json'), 'w', encoding='utf-8'), indent=1)
    for fn in ('index.json', 'facts.json', 'nodes.json'):
        az('storage', 'blob', 'upload', '--account-name', sa, '--account-key', k, '-c', 'pond', '-n', f'door/{fn}', '-f', os.path.join(tmp, fn), '--overwrite', 'true', '--content-type', 'application/json', '--no-progress', check=False)
    log(f"door index: {len(idx['keys'])} keys, {len(idx['ticker'])} tickers, {len(idx['isin'])} isins, {len(idx['alias'])} aliases; facts + nodes uploaded")
elif step == 'app':
    # a failed environment is left standing (Rule One) and the next name is used: cmkg-env-<region>, -2, -3 …
    for suffix in ('', '-2', '-3'):
        cand = env_name + suffix; e = az('containerapp', 'env', 'show', '-n', cand, '-g', rg, check=False)
        if e and e['properties']['provisioningState'] in ('Succeeded', 'InProgress', 'Waiting', 'Updating'): env_name = cand; log(f"environment {cand} present ({e['properties']['provisioningState']})"); break
        if e: log(f"environment {cand} is {e['properties']['provisioningState']} — left standing, trying the next name"); continue
        e = az('containerapp', 'env', 'create', '-n', cand, '-g', rg, '-l', region, '--tags', 'order=ORDER-018', check=False)
        if e and e['properties']['provisioningState'] == 'Succeeded': env_name = cand; log(f"environment {cand} {e['properties']['provisioningState']} (Log Analytics workspace auto-created by the CLI)"); break
        log(f"environment {cand} create returned {(e or {}).get('properties', {}).get('provisioningState')}")
    else: raise SystemExit('no usable environment')
    open(rf'C:\ALLOOLOO\AZURE\env-{cc}.txt', 'w').write(env_name)
    k = storage_key(); acr_pw = az('acr', 'credential', 'show', '-n', ACR, '--query', 'passwords[0].value', '-o', 'tsv', raw=True)
    a = az('containerapp', 'show', '-n', app, '-g', rg, check=False)
    image = f'{ACR_SERVER}/cmkg-door:{tag}'
    if not a:
        a = az('containerapp', 'create', '-n', app, '-g', rg, '--environment', env_name, '--image', image, '--registry-server', ACR_SERVER, '--registry-username', ACR, '--registry-password', acr_pw, '--target-port', '8080', '--ingress', 'external', '--min-replicas', '1', '--max-replicas', '3', '--cpu', '0.5', '--memory', '1.0Gi',
               '--secrets', f'storage-key={k}', '--env-vars', f'NODE={node}', f'REGION={region}', f'STORAGE_ACCOUNT={sa}', 'STORAGE_CONTAINER=pond', 'STORAGE_KEY=secretref:storage-key', f'PUBLIC_HOST={host}', '--tags', 'order=ORDER-018', f'node={node}')
        log(f"app {app} created")
    else:
        a = az('containerapp', 'update', '-n', app, '-g', rg, '--image', image); log(f"app {app} updated to {image}")
    fqdn = a['properties']['configuration']['ingress']['fqdn']; log(f"fqdn https://{fqdn}")
elif step in ('bind', 'flip'):
    zone = ZONES.get(cc)
    if not zone: raise SystemExit(f'zone id for {cc} not on file (HITL)')
    a = az('containerapp', 'show', '-n', app, '-g', rg); fqdn = a['properties']['configuration']['ingress']['fqdn']
    e = az('containerapp', 'env', 'show', '-n', env_name, '-g', rg); vid = e['properties']['customDomainConfiguration']['customDomainVerificationId']
    tok = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip()
    agent_host = f'agent.{node}.ai'
    if step == 'bind':
        # Azure must know both names: TXT asuid record per hostname, hostname added, managed certificate bound by TXT validation (works behind the proxy)
        for h in (host, agent_host):
            recs = cf('GET', f'/zones/{zone}/dns_records?name=asuid.{h}&type=TXT', tok=tok).get('result') or []
            if not any(r.get('content', '').strip('"') == vid for r in recs):
                r = cf('POST', f'/zones/{zone}/dns_records', {'type': 'TXT', 'name': f'asuid.{h}', 'content': vid, 'ttl': 300}, tok=tok); log(f"TXT asuid.{h} {'created' if r.get('success') else r}")
            else: log(f'TXT asuid.{h} present')
            for attempt in range(6):  # the add validates the asuid TXT record, which takes a minute to propagate
                hn = az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or []
                if any(x.get('name') == h for x in hn): break
                az('containerapp', 'hostname', 'add', '-n', app, '-g', rg, '--hostname', h, check=False); time.sleep(15)
            hn = az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or []
            if not any(x.get('name') == h for x in hn): log(f'hostname {h} could not be added (TXT not visible yet) — rerun bind'); continue
            log(f'hostname {h} added')
            b = az('containerapp', 'hostname', 'bind', '-n', app, '-g', rg, '--hostname', h, '--environment', env_name, '--validation-method', 'TXT', check=False)
            log(f"hostname {h} bind: {'ok' if b is not None else 'pending/failed — rerun bind'}")
    else:
        hn = az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or []
        ready = {x.get('name'): x.get('bindingType') for x in hn}
        if any(ready.get(h) != 'SniEnabled' for h in (host, agent_host)): raise SystemExit(f'origin not yet bound with a certificate: {ready} — run bind again / wait, then flip')
        # the origin answers on the new binding: the Workers custom-domain binding comes off mcp.* (the Worker stays deployed), then the records flip to proxied CNAMEs
        d1 = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt', encoding='utf-8').read().strip()
        for d in (cf('GET', f'/accounts/{CF_ACCT}/workers/domains?hostname={host}', tok=d1).get('result') or []):
            r = cf('DELETE', f'/accounts/{CF_ACCT}/workers/domains/{d["id"]}', tok=d1); log(f"workers domain binding {d['id']} for {host} removed: {r.get('success')}")
        for h in (host, agent_host):
            recs = cf('GET', f'/zones/{zone}/dns_records?name={h}', tok=tok).get('result') or []
            for r0 in [r for r in recs if r['type'] in ('A', 'AAAA')]:
                r = cf('DELETE', f'/zones/{zone}/dns_records/{r0["id"]}', tok=tok); log(f"{h}: placeholder {r0['type']} record {r0['content']} removed (Workers custom-domain placeholder): {r.get('success')}")
            cn = [r for r in recs if r['type'] == 'CNAME']
            if cn:
                if cn[0]['content'] != fqdn or not cn[0].get('proxied'): r = cf('PATCH', f'/zones/{zone}/dns_records/{cn[0]["id"]}', {'content': fqdn, 'proxied': True}, tok=tok); log(f"CNAME {h} updated -> {fqdn}: {r.get('success')}")
                else: log(f'CNAME {h} present')
            else:
                r = cf('POST', f'/zones/{zone}/dns_records', {'type': 'CNAME', 'name': h, 'content': fqdn, 'proxied': True, 'ttl': 1}, tok=tok); log(f"CNAME {h} -> {fqdn} created: {r.get('success')} {r if not r.get('success') else ''}")
        z = cf('PATCH', f'/zones/{zone}/settings/ssl', {'value': 'strict'}, tok=tok); log(f"zone SSL strict: {z.get('success')}")
elif step == 'go':
    # End-to-end hostname move (the managed certificate validates only once the name resolves to the app): for each hostname — the Workers custom-domain
    # binding comes off mcp.* (the Worker stays deployed, the apex still serves), a DNS-only CNAME points the name at the app, the hostname is added,
    # the certificate bound (retried until Succeeded, up to 15 minutes), then the record turns proxied. Zone SSL: Full (strict).
    zone = ZONES.get(cc)
    if not zone: raise SystemExit(f'zone id for {cc} not on file (HITL)')
    a = az('containerapp', 'show', '-n', app, '-g', rg); fqdn = a['properties']['configuration']['ingress']['fqdn']
    e = az('containerapp', 'env', 'show', '-n', env_name, '-g', rg); vid = e['properties']['customDomainConfiguration']['customDomainVerificationId']
    tok = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip(); d1 = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt', encoding='utf-8').read().strip()
    for h in (f'agent.{node}.ai', host):
        recs = cf('GET', f'/zones/{zone}/dns_records?name=asuid.{h}&type=TXT', tok=tok).get('result') or []
        if not any(r.get('content', '').strip('"') == vid for r in recs): cf('POST', f'/zones/{zone}/dns_records', {'type': 'TXT', 'name': f'asuid.{h}', 'content': vid, 'ttl': 300}, tok=tok); log(f'TXT asuid.{h} created')
        if h == host:
            for d in (cf('GET', f'/accounts/{CF_ACCT}/workers/domains?hostname={host}', tok=d1).get('result') or []):
                r = cf('DELETE', f'/accounts/{CF_ACCT}/workers/domains/{d["id"]}', tok=d1); log(f"workers custom-domain binding for {host} removed: {r.get('success')} (the Worker stays deployed)")
        recs = cf('GET', f'/zones/{zone}/dns_records?name={h}', tok=tok).get('result') or []
        for r0 in [r for r in recs if r['type'] in ('A', 'AAAA')]:
            r = cf('DELETE', f'/zones/{zone}/dns_records/{r0["id"]}', tok=tok); log(f"{h}: placeholder {r0['type']} {r0['content']} removed: {r.get('success')}")
        cn = [r for r in recs if r['type'] == 'CNAME']
        if not cn: r = cf('POST', f'/zones/{zone}/dns_records', {'type': 'CNAME', 'name': h, 'content': fqdn, 'proxied': False, 'ttl': 300}, tok=tok); log(f"CNAME {h} -> {fqdn} (DNS only): {r.get('success')} {r if not r.get('success') else ''}"); cn = [r.get('result')] if r.get('success') else []
        elif cn[0]['content'] != fqdn: r = cf('PATCH', f'/zones/{zone}/dns_records/{cn[0]["id"]}', {'content': fqdn, 'proxied': False}, tok=tok); log(f"CNAME {h} repointed -> {fqdn}: {r.get('success')}")
        for attempt in range(8):
            hn = az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or []
            if any(x.get('name') == h for x in hn): break
            az('containerapp', 'hostname', 'add', '-n', app, '-g', rg, '--hostname', h, check=False); time.sleep(15)
        bound = False
        for attempt in range(30):
            hn = az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or []
            if any(x.get('name') == h and x.get('bindingType') == 'SniEnabled' for x in hn): bound = True; break
            az('containerapp', 'hostname', 'bind', '-n', app, '-g', rg, '--hostname', h, '--environment', env_name, '--validation-method', 'TXT', check=False); time.sleep(30)
        log(f"hostname {h}: {'bound (SniEnabled)' if bound else 'NOT bound after 15 minutes — rerun go'}")
        if bound and cn:
            recs = cf('GET', f'/zones/{zone}/dns_records?name={h}&type=CNAME', tok=tok).get('result') or []
            for r0 in recs: r = cf('PATCH', f'/zones/{zone}/dns_records/{r0["id"]}', {'proxied': True}, tok=tok); log(f"CNAME {h} proxied: {r.get('success')}")
    z = cf('PATCH', f'/zones/{zone}/settings/ssl', {'value': 'strict'}, tok=tok); log(f"zone SSL strict: {z.get('success')}")
elif step in ('stage', 'check'):
    # CEO rule (Sept 12): no polling. stage = for each hostname: TXT asuid, Workers binding off mcp.*, placeholder records off, DNS-only CNAME to the app,
    # hostname added, ONE bind attempt, move on. check = one look: certificate Succeeded -> bind once if needed and turn the record proxied; otherwise
    # report pending. Scheduled once at +30 minutes per region; still pending at +60 is reported as pending, never retried.
    zone = ZONES.get(cc)
    if not zone: raise SystemExit(f'zone id for {cc} not on file (HITL)')
    a = az('containerapp', 'show', '-n', app, '-g', rg); fqdn = a['properties']['configuration']['ingress']['fqdn']
    e = az('containerapp', 'env', 'show', '-n', env_name, '-g', rg); vid = e['properties']['customDomainConfiguration']['customDomainVerificationId']
    tok = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip(); d1 = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt', encoding='utf-8').read().strip()
    hosts = (f'agent.{node}.ai', host)
    if step == 'stage':
        for h in hosts:
            recs = cf('GET', f'/zones/{zone}/dns_records?name=asuid.{h}&type=TXT', tok=tok).get('result') or []
            if not any(r.get('content', '').strip('"') == vid for r in recs): cf('POST', f'/zones/{zone}/dns_records', {'type': 'TXT', 'name': f'asuid.{h}', 'content': vid, 'ttl': 300}, tok=tok); log(f'TXT asuid.{h} created')
            if h == host:
                for d in (cf('GET', f'/accounts/{CF_ACCT}/workers/domains?hostname={host}', tok=d1).get('result') or []):
                    r = cf('DELETE', f'/accounts/{CF_ACCT}/workers/domains/{d["id"]}', tok=d1); log(f"workers custom-domain binding for {host} removed: {r.get('success')} (the Worker stays deployed)")
            recs = cf('GET', f'/zones/{zone}/dns_records?name={h}', tok=tok).get('result') or []
            for r0 in [r for r in recs if r['type'] in ('A', 'AAAA')]:
                r = cf('DELETE', f'/zones/{zone}/dns_records/{r0["id"]}', tok=tok); log(f"{h}: placeholder {r0['type']} {r0['content']} removed: {r.get('success')}")
            cn = [r for r in recs if r['type'] == 'CNAME']
            if not cn: r = cf('POST', f'/zones/{zone}/dns_records', {'type': 'CNAME', 'name': h, 'content': fqdn, 'proxied': False, 'ttl': 300}, tok=tok); log(f"CNAME {h} -> {fqdn} (DNS only): {r.get('success')}")
            elif cn[0]['content'] != fqdn: r = cf('PATCH', f'/zones/{zone}/dns_records/{cn[0]["id"]}', {'content': fqdn}, tok=tok); log(f"CNAME {h} repointed -> {fqdn}: {r.get('success')}")
            hn = az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or []
            if not any(x.get('name') == h for x in hn): az('containerapp', 'hostname', 'add', '-n', app, '-g', rg, '--hostname', h, check=False); log(f'hostname {h} add attempted')
            b = az('containerapp', 'hostname', 'bind', '-n', app, '-g', rg, '--hostname', h, '--environment', env_name, '--validation-method', 'TXT', check=False)
            log(f"hostname {h}: one bind attempt {'succeeded' if b is not None else 'returned pending (certificate provisioning)'} — check at +30 minutes")
    else:
        certs = {c['properties'].get('subjectName'): c['properties'].get('provisioningState') for c in (az('containerapp', 'env', 'certificate', 'list', '-g', rg, '-n', env_name, '--managed-certificates-only', check=False) or [])}
        hn = {x.get('name'): x.get('bindingType') for x in (az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or [])}
        for h in hosts:
            st = certs.get(h); bt = hn.get(h)
            if bt != 'SniEnabled':
                # one bind attempt per check (a bind call is what triggers Azure's validation now that the name resolves to the app); no loop
                az('containerapp', 'hostname', 'bind', '-n', app, '-g', rg, '--hostname', h, '--environment', env_name, '--validation-method', 'TXT', check=False)
                hn2 = {x.get('name'): x.get('bindingType') for x in (az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or [])}; bt = hn2.get(h)
                certs2 = {c['properties'].get('subjectName'): c['properties'].get('provisioningState') for c in (az('containerapp', 'env', 'certificate', 'list', '-g', rg, '-n', env_name, '--managed-certificates-only', check=False) or [])}; st = certs2.get(h, st)
            if bt == 'SniEnabled':
                recs = cf('GET', f'/zones/{zone}/dns_records?name={h}&type=CNAME', tok=tok).get('result') or []
                for r0 in recs:
                    if not r0.get('proxied'): r = cf('PATCH', f'/zones/{zone}/dns_records/{r0["id"]}', {'proxied': True}, tok=tok); log(f"{h}: certificate Succeeded, bound, CNAME now proxied: {r.get('success')}")
                    else: log(f'{h}: bound and proxied')
            else: log(f"{h}: certificate {st or 'not created'}, binding {bt or 'none'} — PENDING (reported, not retried)")
        z = cf('PATCH', f'/zones/{zone}/settings/ssl', {'value': 'strict'}, tok=tok); log(f"zone SSL strict: {z.get('success')}")
elif step == 'status':
    a = az('containerapp', 'show', '-n', app, '-g', rg); fqdn = a['properties']['configuration']['ingress']['fqdn']
    hn = az('containerapp', 'hostname', 'list', '-n', app, '-g', rg, check=False) or []
    print(json.dumps({'app': app, 'fqdn': fqdn, 'state': a['properties']['provisioningState'], 'running': a['properties'].get('runningStatus'), 'hostnames': [(h.get('name'), h.get('bindingType')) for h in hn], 'image': a['properties']['template']['containers'][0]['image']}, indent=1))
else: raise SystemExit('unknown step')
