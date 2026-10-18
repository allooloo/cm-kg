r"""ORDER-032 C.1 — the warm-standby door for one node on AWS, in the AWS region of that node's ark bucket (in-country: a node's standby never serves from
another node's region). Runs on the laptop as standby-deployer (C:\MATTHEWKEDDY\AGENT KEYS\aws-standby-deployer.txt, never printed); no Docker needed.
  1. image   copy allooloocmkg.azurecr.io/cmkg-door:<tag> into ECR allooloo-standby/cmkg-door:<tag> (registry API to registry API, digests checked)
  2. cert    one Cloudflare Origin CA certificate for mcp.<node>.ai + agent.<node>.ai (new key made here, kept under AZURE\certs\<cc>\standby\, git-ignored)
             -> Secrets Manager allooloo-standby/<cc>-origin-ca {cert, key}; Cloudflare then runs full (strict) against the standby too
  3. network default VPC public subnets; security group allooloo-standby-door-<cc>: 443/tcp from Cloudflare's published IPv4 ranges only
  4. compute ECS cluster allooloo-standby; task definition cmkg-door-<cc> (Fargate 0.25 vCPU / 0.5 GB, ORIGIN=aws, reads its ark bucket via the task role,
             HTTPS 443 with the Origin CA cert); service allooloo-standby-<cc> at desired count 0 — scaled to zero until a swap
Usage: python standby_deploy.py <cc> [door tag]   (default tag 0.13.2). Create-only and idempotent: what exists is reused, nothing deleted.
Writes zones-032\standby-<cc>.json (the standby's record: region, repo, digest, task definition, service, scaled state)."""
import os, sys, json, base64, hashlib, subprocess, datetime, urllib.request
import requests, boto3
ACCT = '159822161213'; ACR = 'allooloocmkg'; ACR_SERVER = 'allooloocmkg.azurecr.io'
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
ARK = {'nl': 'eu-central-1', 'ch': 'eu-central-2', 'fr': 'eu-west-3', 'de': 'eu-central-1', 'sg': 'ap-southeast-1', 'au': 'ap-southeast-2', 'uk': 'eu-west-2', 'ca': 'ca-central-1', 'jp': 'ap-northeast-1', 'kr': 'ap-northeast-2', 'us': 'us-east-1'}
CF_ZONES = {'ca': '4d2c6dc2f534dd8c013f6e66544eed4c', 'uk': '999f8cab6ae570a878379f0e37cd87b0', 'au': '8732370fd5742f40dba657be3eab5d37', 'sg': '0d4ae29fdde22945ffd2858bc2922576', 'ch': '0ea4358fbd0c1dc5ccf069448ccefe48', 'de': '0e7b54741212fb036c2cf18b9392ed25', 'fr': '645c30886df97804e3b793399e303c2b', 'nl': 'e5a042d3df88b7e170d5225ecfacb008', 'jp': 'f1c120f9d544c4af28bd6029ce071b96', 'kr': 'cd87134802ca140f4767253f39453ce1', 'us': '64516e94b82d13781980dff99c20c8b0'}
cc = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else '0.13.2'; REGION = ARK[cc]; NODE = f'{cc}-cm-kg'
HERE = os.path.dirname(os.path.abspath(__file__)); REC = os.path.join(HERE, f'standby-{cc}.json')
rec = json.load(open(REC, encoding='utf-8')) if os.path.exists(REC) else {'node': NODE, 'aws_region': REGION}
def log(*a): print(*a, flush=True)
_k = open(r'C:\MATTHEWKEDDY\AGENT KEYS\aws-standby-deployer.txt', encoding='utf-8').read().split()
S = boto3.session.Session(aws_access_key_id=_k[0], aws_secret_access_key=_k[1], region_name=REGION); del _k
ident = S.client('sts').get_caller_identity()
if ident['Account'] != ACCT or not ident['Arn'].endswith(':user/standby-deployer'): raise SystemExit('STOP: not standby-deployer in account ' + ACCT)
def az(*a):
    p = subprocess.run(['az', *a], capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
    if p.returncode != 0: raise SystemExit(f"az {' '.join(a[:3])} failed: {(p.stderr or p.stdout)[-300:]}")
    return p.stdout.strip()

# ---- 1. image: ACR -> ECR over the registry APIs
ecr = S.client('ecr'); REPO = 'allooloo-standby/cmkg-door'
try: ecr.create_repository(repositoryName=REPO, imageTagMutability='IMMUTABLE', imageScanningConfiguration={'scanOnPush': True}, tags=[{'Key': 'order', 'Value': 'ORDER-032'}]); log('ECR repository created', REPO, REGION)
except ecr.exceptions.RepositoryAlreadyExistsException: log('ECR repository present', REPO, REGION)
have = [t for d in ecr.describe_images(repositoryName=REPO).get('imageDetails', []) for t in d.get('imageTags', [])]
ECR_HOST = f'{ACCT}.dkr.ecr.{REGION}.amazonaws.com'
if TAG in have: log('image present in ECR:', TAG)
else:
    acct = json.loads(az('account', 'show', '-o', 'json'))
    if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the Allooloo tenant/subscription of record')
    acr_pw = az('acr', 'credential', 'show', '-n', ACR, '--query', 'passwords[0].value', '-o', 'tsv'); A = requests.Session(); A.auth = (ACR, acr_pw)
    tok = base64.b64decode(ecr.get_authorization_token()['authorizationData'][0]['authorizationToken']).decode().split(':', 1); E = requests.Session(); E.auth = (tok[0], tok[1])
    acc = ', '.join(['application/vnd.docker.distribution.manifest.v2+json', 'application/vnd.oci.image.manifest.v1+json', 'application/vnd.docker.distribution.manifest.list.v2+json', 'application/vnd.oci.image.index.v1+json'])
    r = A.get(f'https://{ACR_SERVER}/v2/cmkg-door/manifests/{TAG}', headers={'Accept': acc}); r.raise_for_status(); mt = r.headers['Content-Type']; man = r.content; mj = json.loads(man)
    if 'manifests' in mj:   # an index: take linux/amd64
        d = next(m['digest'] for m in mj['manifests'] if m.get('platform', {}).get('architecture') == 'amd64' and m.get('platform', {}).get('os') == 'linux')
        r = A.get(f'https://{ACR_SERVER}/v2/cmkg-door/manifests/{d}', headers={'Accept': acc}); r.raise_for_status(); mt = r.headers['Content-Type']; man = r.content; mj = json.loads(man)
    blobs = [mj['config']] + mj['layers']
    for b in blobs:
        dg = b['digest']
        if E.head(f'https://{ECR_HOST}/v2/{REPO}/blobs/{dg}').status_code == 200: log('  blob present', dg[:19]); continue
        data = A.get(f'https://{ACR_SERVER}/v2/cmkg-door/blobs/{dg}').content
        if 'sha256:' + hashlib.sha256(data).hexdigest() != dg: raise SystemExit(f'digest mismatch on {dg}')
        r = E.post(f'https://{ECR_HOST}/v2/{REPO}/blobs/uploads/'); r.raise_for_status(); loc = r.headers['Location']; loc = loc if loc.startswith('http') else f'https://{ECR_HOST}{loc}'
        r = E.patch(loc, data=data, headers={'Content-Type': 'application/octet-stream', 'Content-Range': f'0-{len(data) - 1}'}); r.raise_for_status(); loc = r.headers.get('Location', loc); loc = loc if loc.startswith('http') else f'https://{ECR_HOST}{loc}'
        r = E.put(loc + ('&' if '?' in loc else '?') + f'digest={dg}', data=b''); r.raise_for_status(); log('  blob copied', dg[:19], f'{len(data) / 1e6:.1f} MB')
    r = E.put(f'https://{ECR_HOST}/v2/{REPO}/manifests/{TAG}', data=man, headers={'Content-Type': mt}); r.raise_for_status()
    log('image copied to ECR:', f'{ECR_HOST}/{REPO}:{TAG}', 'digest', 'sha256:' + hashlib.sha256(man).hexdigest()[:16])
IMAGE = f'{ECR_HOST}/{REPO}:{TAG}'; rec.update({'ecr_image': IMAGE, 'door_tag': TAG})

# ---- 2. one Origin CA certificate for mcp. + agent., key made here, into Secrets Manager
sm = S.client('secretsmanager'); SECRET = f'allooloo-standby/{cc}-origin-ca'
try: sm.describe_secret(SecretId=SECRET); log('Origin CA secret present', SECRET)
except sm.exceptions.ResourceNotFoundException:
    d = os.path.join(r'C:\ALLOOLOO\AZURE\certs', cc, 'standby'); os.makedirs(d, exist_ok=True); kf, csrf, pf = (os.path.join(d, x) for x in ('origin.key', 'origin.csr', 'origin.pem'))
    if not os.path.exists(pf):
        subprocess.run(['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes', '-keyout', kf, '-out', csrf, '-subj', f'/CN=mcp.{NODE}.ai'], check=True, capture_output=True)
        t = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-origin-ca.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
        r = requests.post('https://api.cloudflare.com/client/v4/certificates', headers={'Authorization': 'Bearer ' + t}, json={'hostnames': [f'mcp.{NODE}.ai', f'agent.{NODE}.ai'], 'requested_validity': 5475, 'request_type': 'origin-rsa', 'csr': open(csrf, encoding='utf-8').read()}, timeout=60).json()
        if not r.get('success'): raise SystemExit(f"Origin CA refused: {r.get('errors')}")
        open(pf, 'w', encoding='utf-8').write(r['result']['certificate']); rec['origin_ca'] = {'id': r['result']['id'], 'expires_on': r['result']['expires_on'], 'hostnames': r['result']['hostnames']}
    sm.create_secret(Name=SECRET, SecretString=json.dumps({'cert': open(pf, encoding='utf-8').read(), 'key': open(kf, encoding='utf-8').read()}), Tags=[{'Key': 'order', 'Value': 'ORDER-032'}, {'Key': 'node', 'Value': NODE}])
    log('Origin CA certificate issued for', f'mcp.{NODE}.ai + agent.{NODE}.ai', '-> secret', SECRET)
SECRET_ARN = sm.describe_secret(SecretId=SECRET)['ARN']; rec['secret'] = SECRET

# ---- 3. network: default VPC, public subnets, 443 from Cloudflare only
ec2 = S.client('ec2'); vpc = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])['Vpcs']
if not vpc: raise SystemExit(f'STOP: no default VPC in {REGION}')
VPC = vpc[0]['VpcId']; SUBNETS = [s['SubnetId'] for s in ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [VPC]}, {'Name': 'default-for-az', 'Values': ['true']}])['Subnets']]
SGN = f'allooloo-standby-door-{cc}'; sg = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [SGN]}, {'Name': 'vpc-id', 'Values': [VPC]}])['SecurityGroups']
# Cloudflare's published edge ranges from its API (www.cloudflare.com/ips-v4 refuses plain clients, 403 on the NL deploy 2026-10-18)
ranges = requests.get('https://api.cloudflare.com/client/v4/ips', timeout=30).json()['result']['ipv4_cidrs']
if sg: SG = sg[0]['GroupId']; log('security group present', SG)
else:
    SG = ec2.create_security_group(GroupName=SGN, Description=f'ORDER-032 standby door {NODE}: 443 from Cloudflare only', VpcId=VPC, TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'order', 'Value': 'ORDER-032'}]}])['GroupId']; log('security group created', SG)
# ingress applied whether the group is new or not (a group left without its rule by an interrupted run is completed here); existing rules are kept
have_r = {r['CidrIp'] for p_ in ec2.describe_security_groups(GroupIds=[SG])['SecurityGroups'][0]['IpPermissions'] if p_.get('FromPort') == 443 for r in p_.get('IpRanges', [])}
want_r = [c for c in ranges if c not in have_r]
if want_r: ec2.authorize_security_group_ingress(GroupId=SG, IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': c, 'Description': 'Cloudflare'} for c in want_r]}])
log('security group', SG, '443 from', len(have_r) + len(want_r), 'Cloudflare ranges (' + str(len(want_r)) + ' added)')
rec.update({'vpc': VPC, 'subnets': SUBNETS, 'security_group': SG})

# ---- 4. compute: ECS on Fargate, scaled to zero
logs = S.client('logs'); LG = f'/allooloo/standby/{cc}'
try: logs.create_log_group(logGroupName=LG, tags={'order': 'ORDER-032'}); logs.put_retention_policy(logGroupName=LG, retentionInDays=90)
except logs.exceptions.ResourceAlreadyExistsException: pass
ecs = S.client('ecs'); ecs.create_cluster(clusterName='allooloo-standby', tags=[{'key': 'order', 'value': 'ORDER-032'}])
env = [{'name': k, 'value': v} for k, v in {'ORIGIN': 'aws', 'NODE': NODE, 'REGION': REGION, 'PUBLIC_HOST': f'mcp.{NODE}.ai', 'ARK_BUCKET': f'allooloo-ark-{NODE}', 'ARK_REGION': REGION, 'TLS_PORT': '443', 'PORT': '8080', 'CONTACT': 'developers@allooloo.ai'}.items()]
td = ecs.register_task_definition(family=f'cmkg-door-{cc}', networkMode='awsvpc', requiresCompatibilities=['FARGATE'], cpu='256', memory='512',
    executionRoleArn=f'arn:aws:iam::{ACCT}:role/allooloo-standby-exec', taskRoleArn=f'arn:aws:iam::{ACCT}:role/allooloo-standby-task', runtimePlatform={'cpuArchitecture': 'X86_64', 'operatingSystemFamily': 'LINUX'},
    containerDefinitions=[{'name': 'door', 'image': IMAGE, 'essential': True, 'user': '0', 'portMappings': [{'containerPort': 443, 'protocol': 'tcp'}], 'environment': env,
        'secrets': [{'name': 'TLS_CERT', 'valueFrom': f'{SECRET_ARN}:cert::'}, {'name': 'TLS_KEY', 'valueFrom': f'{SECRET_ARN}:key::'}],
        'logConfiguration': {'logDriver': 'awslogs', 'options': {'awslogs-group': LG, 'awslogs-region': REGION, 'awslogs-stream-prefix': 'door'}}}],
    tags=[{'key': 'order', 'value': 'ORDER-032'}, {'key': 'node', 'value': NODE}])['taskDefinition']['taskDefinitionArn']
SVC = f'allooloo-standby-{cc}'; cur = [s for s in ecs.describe_services(cluster='allooloo-standby', services=[SVC])['services'] if s['status'] == 'ACTIVE']
net = {'awsvpcConfiguration': {'subnets': SUBNETS, 'securityGroups': [SG], 'assignPublicIp': 'ENABLED'}}
if cur: ecs.update_service(cluster='allooloo-standby', service=SVC, taskDefinition=td, desiredCount=cur[0]['desiredCount']); log('service updated to', td.split('/')[-1], 'desired', cur[0]['desiredCount'])
else: ecs.create_service(cluster='allooloo-standby', serviceName=SVC, taskDefinition=td, desiredCount=0, launchType='FARGATE', networkConfiguration=net, tags=[{'key': 'order', 'value': 'ORDER-032'}]); log('service created', SVC, 'desired 0 (scaled to zero)')
s = ecs.describe_services(cluster='allooloo-standby', services=[SVC])['services'][0]
rec.update({'cluster': 'allooloo-standby', 'service': SVC, 'task_definition': td, 'desired': s['desiredCount'], 'running': s['runningCount'], 'log_group': LG, 'updated': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z'})
json.dump(rec, open(REC, 'w', encoding='utf-8'), indent=1); log('standby', NODE, REGION, 'desired', s['desiredCount'], 'running', s['runningCount'], '->', REC)
