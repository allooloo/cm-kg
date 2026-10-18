r"""ORDER-032 C.3 — swap one node's door between Azure and its AWS warm standby by flipping the Cloudflare origin of mcp.<node>.ai and agent.<node>.ai.
  python swap.py <cc> to-aws        scale the standby to 1, read its public IP, save the current DNS records beside (swap-state-<cc>-<UTC>.json), point both
                                    hostnames (proxied) at the standby, prove the door: list_nodes + get_record with X-Allooloo-Origin: aws and the as-of
  python swap.py <cc> to-azure      restore the saved records exactly, prove X-Allooloo-Origin: azure, scale the standby back to 0
  python swap.py <cc> round-trip    both, in that order (the proof of record for the quarterly one-node test)
Each swap is appended to CM-KG\ESTATE\public\swap\swaps.json (the agent-swap.ai log of record); the estate is redeployed once at the end.
  --min-asof YYYY-MM-DD   the record date the AWS proof must show (default 2026-10-23, the first Azure sweep the ark carries)
  --ident <identifier>    the get_record identifier for the proof (default per node; NL = Heineken, ISIN NL0000009165)
Standby-deployer for ECS/EC2 (never printed); C:\ALLOOLOO\AGENT KEYS\cloudflare.txt for DNS. The DNS records are flipped, never deleted; the originals stay beside."""
import os, sys, json, time, datetime, subprocess
import requests, boto3
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = r'C:\ALLOOLOO'
ARK = {'nl': 'eu-central-1', 'ch': 'eu-central-2', 'fr': 'eu-west-3', 'de': 'eu-central-1', 'sg': 'ap-southeast-1', 'au': 'ap-southeast-2', 'uk': 'eu-west-2', 'ca': 'ca-central-1', 'jp': 'ap-northeast-1', 'kr': 'ap-northeast-2', 'us': 'us-east-1'}
CF_ZONES = {'ca': '4d2c6dc2f534dd8c013f6e66544eed4c', 'uk': '999f8cab6ae570a878379f0e37cd87b0', 'au': '8732370fd5742f40dba657be3eab5d37', 'sg': '0d4ae29fdde22945ffd2858bc2922576', 'ch': '0ea4358fbd0c1dc5ccf069448ccefe48', 'de': '0e7b54741212fb036c2cf18b9392ed25', 'fr': '645c30886df97804e3b793399e303c2b', 'nl': 'e5a042d3df88b7e170d5225ecfacb008', 'jp': 'f1c120f9d544c4af28bd6029ce071b96', 'kr': 'cd87134802ca140f4767253f39453ce1', 'us': '64516e94b82d13781980dff99c20c8b0'}
IDENT = {'nl': 'NL0000009165', 'uk': 'SHEL', 'de': 'SAP', 'fr': 'MC', 'ch': 'NESN', 'au': 'BHP', 'sg': 'D05', 'ca': 'SHOP', 'jp': '7203', 'kr': '005930', 'us': 'AAPL'}
a = sys.argv[1:]; cc, mode = a[0], a[1]; NODE = f'{cc}-cm-kg'; REGION = ARK[cc]
MIN_ASOF = a[a.index('--min-asof') + 1] if '--min-asof' in a else '2026-10-23'; ID = a[a.index('--ident') + 1] if '--ident' in a else IDENT[cc]
HOSTS = [f'mcp.{NODE}.ai', f'agent.{NODE}.ai']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
def log(*x): print(now(), *x, flush=True)
_k = open(r'C:\MATTHEWKEDDY\AGENT KEYS\aws-standby-deployer.txt', encoding='utf-8').read().split()
S = boto3.session.Session(aws_access_key_id=_k[0], aws_secret_access_key=_k[1], region_name=REGION); del _k
ecs, ec2 = S.client('ecs'), S.client('ec2'); SVC = f'allooloo-standby-{cc}'
CFT = open(os.path.join(ROOT, 'AGENT KEYS', 'cloudflare.txt'), encoding='utf-8').read().strip().splitlines()[0].strip()
def cf(method, path, body=None):
    r = requests.request(method, 'https://api.cloudflare.com/client/v4' + path, headers={'Authorization': 'Bearer ' + CFT}, json=body, timeout=60).json()
    if not r.get('success'): raise SystemExit(f'Cloudflare {method} {path}: {r.get("errors")}')
    return r['result']
def records(): return {h: [r for r in cf('GET', f'/zones/{CF_ZONES[cc]}/dns_records?name={h}&per_page=50') if r['type'] in ('A', 'AAAA', 'CNAME')] for h in HOSTS}
def mcp(method, params):
    r = requests.post(f'https://mcp.{NODE}.ai/mcp', headers={'content-type': 'application/json', 'accept': 'application/json, text/event-stream', 'cache-control': 'no-cache'}, json={'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}, timeout=60)
    return r.status_code, r.headers.get('x-allooloo-origin'), r.headers.get('x-cmr-as-of'), r.text
def prove(want):
    """read the door through Cloudflare after the flip; up to six reads ten seconds apart while the edge takes our own change (logged, bounded)"""
    for i in range(6):
        s1, o1, a1, t1 = mcp('tools/call', {'name': 'list_nodes', 'arguments': {}})
        s2, o2, a2, t2 = mcp('tools/call', {'name': 'get_record', 'arguments': {'identifier': ID}})
        log(f'proof read {i + 1}: list_nodes {s1} origin {o1} as_of {a1} · get_record {ID} {s2} origin {o2} as_of {a2}')
        if o1 == want and o2 == want and s1 == 200 and s2 == 200 and '"error"' not in t2[:400]:
            if want == 'aws' and (a2 or '') < MIN_ASOF: raise SystemExit(f'STOP: the standby answers but its record is as of {a2}, before {MIN_ASOF} — the ark has not carried that sweep yet')
            return {'at': now(), 'list_nodes': s1, 'get_record': s2, 'identifier': ID, 'origin': o2, 'as_of': a2, 'reads': i + 1}
        time.sleep(10)
    raise SystemExit(f'STOP: the door did not answer from {want} after six reads (records left as they are now; see the log)')
def swaplog(entry):
    p = os.path.join(ROOT, r'CM-KG\ESTATE\public\swap\swaps.json'); d = json.load(open(p, encoding='utf-8')); d['swaps'].append(entry)
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); log('swap log +1:', entry['node'], entry['from'], '->', entry['to'])
    # the log of record lives in the shared apex store (the apex job pulls it before each estate deploy, so a Friday deploy never rolls a swap back)
    k = subprocess.run('az storage account keys list -n allooloocmkgapex -g allooloo-cmkg-shared --query [0].value -o tsv', shell=True, capture_output=True, text=True, env=dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure')).stdout.strip()
    from azure.storage.blob import BlobServiceClient, ContentSettings
    BlobServiceClient('https://allooloocmkgapex.blob.core.windows.net', credential=k).get_container_client('sweeps').upload_blob('swap/swaps.json', json.dumps(d, ensure_ascii=False, indent=1).encode('utf-8'), overwrite=True, content_settings=ContentSettings(content_type='application/json'))
    log('swap log written to the apex store (sweeps/swap/swaps.json; blob versioning keeps every prior version)')
def to_aws():
    ecs.update_service(cluster='allooloo-standby', service=SVC, desiredCount=1); log('standby scaled to 1:', SVC, REGION)
    ecs.get_waiter('services_stable').wait(cluster='allooloo-standby', services=[SVC], WaiterConfig={'Delay': 15, 'MaxAttempts': 40})
    t = ecs.describe_tasks(cluster='allooloo-standby', tasks=ecs.list_tasks(cluster='allooloo-standby', serviceName=SVC, desiredStatus='RUNNING')['taskArns'][:1])['tasks'][0]
    eni = next(d['value'] for at in t['attachments'] for d in at['details'] if d['name'] == 'networkInterfaceId')
    ip = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni])['NetworkInterfaces'][0]['Association']['PublicIp']; log('standby task running, public IP', ip)
    before = records(); st = os.path.join(HERE, f'swap-state-{cc}-{now().replace(":", "")}.json'); json.dump({'node': NODE, 'saved_at': now(), 'records': before, 'standby_ip': ip}, open(st, 'w', encoding='utf-8'), indent=1); log('records saved beside:', st)
    for h, rs in before.items():
        for r in rs: cf('PATCH', f"/zones/{CF_ZONES[cc]}/dns_records/{r['id']}", {'type': 'A', 'name': h, 'content': ip, 'proxied': True, 'ttl': 1, 'comment': f'ORDER-032 swap to AWS standby {now()}'})
    log('origin flipped to AWS for', HOSTS); p = prove('aws')
    swaplog({'at': p['at'], 'node': NODE, 'from': 'azure', 'to': 'aws', 'proof': f"list_nodes {p['list_nodes']} · get_record {ID} {p['get_record']} · X-Allooloo-Origin {p['origin']} · as of {p['as_of']}", 'state_file': os.path.basename(st)})
    return p
def to_azure():
    st = sorted(f for f in os.listdir(HERE) if f.startswith(f'swap-state-{cc}-'))
    if not st: raise SystemExit('STOP: no saved records to restore')
    saved = json.load(open(os.path.join(HERE, st[-1]), encoding='utf-8'))['records']
    for h, rs in saved.items():
        for r in rs: cf('PATCH', f"/zones/{CF_ZONES[cc]}/dns_records/{r['id']}", {'type': r['type'], 'name': r['name'], 'content': r['content'], 'proxied': r['proxied'], 'ttl': r['ttl'], 'comment': r.get('comment') or ''})
    log('origin restored to Azure from', st[-1]); p = prove('azure')
    ecs.update_service(cluster='allooloo-standby', service=SVC, desiredCount=0); log('standby scaled back to 0')
    swaplog({'at': p['at'], 'node': NODE, 'from': 'aws', 'to': 'azure', 'proof': f"list_nodes {p['list_nodes']} · get_record {ID} {p['get_record']} · X-Allooloo-Origin {p['origin']} · as of {p['as_of']}", 'state_file': st[-1]})
    return p
out = {}
if mode in ('to-aws', 'round-trip'): out['to_aws'] = to_aws()
if mode in ('to-azure', 'round-trip'): out['to_azure'] = to_azure()
json.dump(out, open(os.path.join(HERE, f'swap-proof-{cc}-{now().replace(":", "")}.json'), 'w', encoding='utf-8'), indent=1)
e = dict(os.environ, CLOUDFLARE_API_TOKEN=open(os.path.join(ROOT, 'AGENT KEYS', 'cloudflare-d1.txt'), encoding='utf-8').read().strip().splitlines()[0].strip(), CI='1', WRANGLER_SEND_METRICS='false')
r = subprocess.run('npx --yes wrangler deploy', cwd=os.path.join(ROOT, r'CM-KG\ESTATE'), env=e, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
log('estate redeployed (swap log):', next((l for l in (r.stdout + r.stderr).splitlines() if 'Version ID' in l), 'see wrangler output'))
