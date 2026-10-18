r"""ORDER-033 — ARK BACKFILL (2026-10-18). Copies every dated drop since 2026-09-12 from each node's live Azure pond into its ark bucket, paths identical
to the pond, plus the door as published today and the node's NUMBERS LOG lines; the apex's sweepREVIEW reports and index into allooloo-ark-apex/apex/.
Runs on the laptop (shape call, logged): reader = the Allooloo Azure login (storage keys in memory only), writer = ark-writer from
C:\MATTHEWKEDDY\AGENT KEYS\aws-ark-writer.txt (never printed). Put only, never overwrite: same MD5 as the existing ark object = skipped (decided from
the listings, no download); a differing object is written beside as <name>-2, -3 ... Retention lands by the bucket default.
Layout of record (the nightly jobs write the same keys from image 0.31.7):
  <node>/pond/<source>/<drop>/<file>      <node>/door/<as_of>/door-bundle.tar.gz      <node>/numbers/<sweep date>.txt
  apex/reports/<sweepREVIEW file>         apex/index/<as_of>/index.json, nodes.json
Usage: python ark_backfill.py [cc ... | apex]   (default: the eleven nodes and the apex). Writes START_ME_UP\ORDER-033-BACKFILL-<date>.json."""
import os, sys, io, re, json, tarfile, hashlib, base64, subprocess, datetime, threading
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.config import Config
THREADS = int(os.environ.get('BACKFILL_THREADS', '6'))   # many small blobs far away (Singapore 22,431) want more in flight
CFG = Config(max_pool_connections=max(10, THREADS + 8), retries={'max_attempts': 5, 'mode': 'standard'})
from azure.storage.blob import BlobServiceClient
ROOT = r'C:\ALLOOLOO'; SINCE = '2026-09-12'; TODAY = datetime.date.today().isoformat()
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
NODES = {'nl': ('westeurope', 'eu-central-1'), 'ch': ('switzerlandnorth', 'eu-central-2'), 'fr': ('francecentral', 'eu-west-3'), 'de': ('germanywestcentral', 'eu-central-1'),
         'sg': ('southeastasia', 'ap-southeast-1'), 'au': ('australiaeast', 'ap-southeast-2'), 'uk': ('uksouth', 'eu-west-2'), 'ca': ('canadacentral', 'ca-central-1'),
         'jp': ('japaneast', 'ap-northeast-1'), 'kr': ('koreacentral', 'ap-northeast-2'), 'us': ('eastus', 'us-east-1')}
def az(*a):
    p = subprocess.run(['az', *a], capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
    if p.returncode != 0: raise SystemExit(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-300:]}")
    return p.stdout.strip()
acct = json.loads(az('account', 'show', '-o', 'json'))
if acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
_k = open(r'C:\MATTHEWKEDDY\AGENT KEYS\aws-ark-writer.txt', encoding='utf-8').read().split()
SESSION = boto3.session.Session(aws_access_key_id=_k[0], aws_secret_access_key=_k[1]); del _k
LOCK = threading.Lock()
def say(*a):
    with LOCK: print(*a, flush=True)
def listing(s3, bucket, prefix):
    have = {}
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix):
        for o in page.get('Contents', []): have[o['Key']] = o['ETag'].strip('"')
    return have
def put(s3, bucket, have, key, data, md5=None):
    """put only, never overwrite; returns ('written'|'skipped', key)"""
    md5 = md5 or hashlib.md5(data).hexdigest()
    k = key; n = 1
    while k in have and have[k] != md5: n += 1; k = f'{key}-{n}'
    if have.get(k) == md5: return 'skipped', k
    s3.put_object(Bucket=bucket, Key=k, Body=data, ContentMD5=base64.b64encode(bytes.fromhex(md5)).decode())
    with LOCK: have[k] = md5
    return 'written', k
def det_tar(entries):
    """a deterministic gzip tar (sorted names, zero mtimes) so a re-run of the same door produces the same bytes and is skipped"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz', compresslevel=6) as t:
        for name, data in sorted(entries):
            ti = tarfile.TarInfo(name); ti.size = len(data); ti.mtime = 0; ti.mode = 0o644; t.addfile(ti, io.BytesIO(data))
    raw = buf.getvalue(); return raw[:4] + b'\x00\x00\x00\x00' + raw[8:]   # gzip header mtime zeroed
def numbers_lines(cc):
    s = open(os.path.join(ROOT, 'START_ME_UP', 'NODE-SURFACES.md'), encoding='utf-8').read()
    m = re.search(r'## 9 NUMBERS LOG[\s\S]*?```\n([\s\S]*?)```', s); by = {}
    for l in m.group(1).splitlines():
        p = [x.strip() for x in l.split('·')]
        if len(p) > 2 and p[0] == f'{cc}-cm-kg' and re.match(r'\d{4}-\d{2}-\d{2}$', p[1]): by.setdefault(p[1], []).append(l)
    return by
def node(cc):
    reg, aws_reg = NODES[cc]; nodename = f'{cc}-cm-kg'; bucket = f'allooloo-ark-{cc}-cm-kg'
    key = az('storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{reg}', '-n', f'allooloocmkg{cc}pond', '--query', '[0].value', '-o', 'tsv')
    cont = BlobServiceClient(f'https://allooloocmkg{cc}pond.blob.core.windows.net', credential=key).get_container_client('pond')
    s3 = SESSION.client('s3', region_name=aws_reg, config=CFG); have = listing(s3, bucket, nodename + '/')
    blobs = []; per_drop = {}
    for b in cont.list_blobs(name_starts_with='pond/'):
        p = b.name.split('/')
        if len(p) < 4 or p[2][:10] < SINCE: continue
        blobs.append(b); per_drop[(p[1], p[2])] = per_drop.get((p[1], p[2]), 0) + 1
    st = {'written': 0, 'skipped': 0, 'bytes': 0, 'beside': []}
    def one(b):
        md5 = bytes(b.content_settings.content_md5).hex() if b.content_settings.content_md5 else None
        k = f'{nodename}/{b.name}'
        if md5 and have.get(k) == md5:
            with LOCK: st['skipped'] += 1
            return
        data = cont.get_blob_client(b.name).download_blob().readall()
        r, kk = put(s3, bucket, have, k, data)
        with LOCK:
            st[r] += 1
            if r == 'written': st['bytes'] += len(data)
            if kk != k: st['beside'].append(kk)
    with ThreadPoolExecutor(max_workers=THREADS) as ex: list(ex.map(one, blobs))
    # the door as published now, one bundle under its as_of
    facts = json.loads(cont.get_blob_client('door/facts.json').download_blob().readall()); as_of = ((facts.get('nodes') or {}).get(nodename) or {}).get('as_of') or TODAY
    names = [b.name for b in cont.list_blobs(name_starts_with='door/')]
    with ThreadPoolExecutor(max_workers=16) as ex: entries = list(ex.map(lambda n: (n, cont.get_blob_client(n).download_blob().readall()), names))
    tb = det_tar(entries); r, kk = put(s3, bucket, have, f'{nodename}/door/{as_of}/door-bundle.tar.gz', tb); st[r] += 1; st['bytes'] += len(tb) if r == 'written' else 0
    for d, lines in sorted(numbers_lines(cc).items()):
        if d < SINCE: continue
        data = ('\n'.join(lines) + '\n').encode('utf-8'); r, kk = put(s3, bucket, have, f'{nodename}/numbers/{d}.txt', data); st[r] += 1; st['bytes'] += len(data) if r == 'written' else 0
    # count check: ark objects per dated drop == pond blobs per dated drop (the -2 variants are extra, never counted as the drop's own)
    after = listing(s3, bucket, nodename + '/pond/'); check = {}
    for (src, dr), n in sorted(per_drop.items()):
        a = sum(1 for k in after if k.startswith(f'{nodename}/pond/{src}/{dr}/') and not re.search(r'-\d+$', k))
        check[f'{src}/{dr}'] = {'pond': n, 'ark': a, 'ok': a == n}
    bad = [d for d, v in check.items() if not v['ok']]
    res = {'node': nodename, 'bucket': bucket, 'region': aws_reg, 'blobs_since': len(blobs), 'drops': len(per_drop), **st, 'door_as_of': as_of, 'door_blobs': len(names), 'count_check': 'PASS' if not bad else f'FAIL {bad}', 'drops_checked': check}
    say(f"{nodename}: written {st['written']} · skipped {st['skipped']} · {st['bytes']/1e6:.1f} MB · {len(per_drop)} drops · count check {res['count_check'] if not bad else 'FAIL ' + str(len(bad)) + ' drops'} · beside {len(st['beside'])}")
    return res
def apex():
    s3 = SESSION.client('s3', region_name='us-east-1'); bucket = 'allooloo-ark-apex'; have = listing(s3, bucket, 'apex/'); st = {'written': 0, 'skipped': 0, 'bytes': 0}
    sm = os.path.join(ROOT, 'START_ME_UP')
    for f in sorted(os.listdir(sm)):
        if f.startswith('sweepREVIEW-') and f.endswith('.md') and '.pre' not in f:
            data = open(os.path.join(sm, f), 'rb').read(); r, k = put(s3, bucket, have, f'apex/reports/{f}', data); st[r] += 1; st['bytes'] += len(data) if r == 'written' else 0
    for f in ('NODE-SURFACES.md',):
        data = open(os.path.join(sm, f), 'rb').read(); r, k = put(s3, bucket, have, f'apex/reports/{f.replace(".md", "")}-{TODAY}.md', data); st[r] += 1; st['bytes'] += len(data) if r == 'written' else 0
    nodes = json.load(open(os.path.join(ROOT, r'CM-KG\DOOR\apex\static\nodes.json'), encoding='utf-8')); as_of = max((n.get('as_of') or '') for n in nodes) or TODAY
    for f in ('index.json', 'nodes.json'):
        data = open(os.path.join(ROOT, r'CM-KG\DOOR\apex\static', f), 'rb').read(); r, k = put(s3, bucket, have, f'apex/index/{as_of}/{f}', data); st[r] += 1; st['bytes'] += len(data) if r == 'written' else 0
    say(f"apex: written {st['written']} · skipped {st['skipped']} · {st['bytes']/1e6:.1f} MB · index as_of {as_of}")
    return {'node': 'apex', 'bucket': bucket, 'region': 'us-east-1', **st, 'index_as_of': as_of}
want = sys.argv[1:] or list(NODES) + ['apex']
results = {}
with ThreadPoolExecutor(max_workers=11) as ex:
    futs = {cc: ex.submit(apex if cc == 'apex' else node, *([] if cc == 'apex' else [cc])) for cc in want}
    for cc, f in futs.items():
        try: results[cc] = f.result()
        except Exception as e: results[cc] = {'node': cc, 'error': repr(e)[:400]}; say(f'{cc}: FAILED {repr(e)[:300]}')
out = os.path.join(ROOT, 'START_ME_UP', f'ORDER-033-BACKFILL-{TODAY}.json'); prev = json.load(open(out, encoding='utf-8')) if os.path.exists(out) else {}
prev.update(results); json.dump(prev, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); say('written', out)
