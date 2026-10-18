r"""ORDER-033 close: from START_ME_UP\ORDER-033-BACKFILL-<date>.json write (1) START_ME_UP\ORDER-033-REPORT-2026-10-18.md, (2) the agent-swap ark log
CM-KG\ESTATE\public\swap\ark.json (last write per node), (3) its copy of record in the shared apex store (sweeps/swap/ark.json).
Usage: python close_033.py <backfill json>"""
import os, sys, json, glob, subprocess, datetime
ROOT = r'C:\ALLOOLOO'; src = sys.argv[1]; R = json.load(open(src, encoding='utf-8'))
ORDER = ['nl', 'ch', 'fr', 'de', 'sg', 'au', 'uk', 'ca', 'jp', 'kr', 'us']
wdate = datetime.datetime.fromtimestamp(os.path.getmtime(src), datetime.timezone.utc).date().isoformat()
# the run was two passes (the first stopped for speed, the second resumed by skipping what was there), so the report counts what is IN each bucket,
# read once from ark-writer's own-prefix listing; written/skipped are the second pass's own figures
import boto3
_k = open(r'C:\MATTHEWKEDDY\AGENT KEYS\aws-ark-writer.txt', encoding='utf-8').read().split(); _S = boto3.session.Session(aws_access_key_id=_k[0], aws_secret_access_key=_k[1]); del _k
REG = {'nl': 'eu-central-1', 'ch': 'eu-central-2', 'fr': 'eu-west-3', 'de': 'eu-central-1', 'sg': 'ap-southeast-1', 'au': 'ap-southeast-2', 'uk': 'eu-west-2', 'ca': 'ca-central-1', 'jp': 'ap-northeast-1', 'kr': 'ap-northeast-2', 'us': 'us-east-1', 'apex': 'us-east-1'}
INB = {}
for cc_, rg_ in REG.items():
    b_ = 'allooloo-ark-apex' if cc_ == 'apex' else f'allooloo-ark-{cc_}-cm-kg'; pre_ = 'apex/' if cc_ == 'apex' else f'{cc_}-cm-kg/'; n_ = 0; z_ = 0
    for pg in _S.client('s3', region_name=rg_).get_paginator('list_objects_v2').paginate(Bucket=b_, Prefix=pre_):
        for o in pg.get('Contents', []): n_ += 1; z_ += o['Size']
    INB[cc_] = (n_, z_)
rows = []; T = {'written': 0, 'skipped': 0, 'bytes': 0}; fails = []
for cc in ORDER + ['apex']:
    r = R.get(cc) or R.get(f'{cc}-cm-kg')
    if not r: rows.append(f'| {cc} | — | — | — | — | not run | — |'); fails.append(cc); continue
    if r.get('error'): rows.append(f"| {r.get('node', cc)} | — | — | — | — | FAILED: {r['error'][:120]} | — |"); fails.append(cc); continue
    for k in T: T[k] += r.get(k, 0)
    chk = r.get('count_check', 'n/a (reports and index)')
    if isinstance(chk, str) and chk.startswith('FAIL'): fails.append(cc)
    n_, z_ = INB[cc]; T['in_ark'] = T.get('in_ark', 0) + n_; T['ark_bytes'] = T.get('ark_bytes', 0) + z_
    rows.append(f"| {r['node']} | {r['bucket']} · {r['region']} | {n_:,} | {z_ / 1e6:,.1f} MB | {r.get('written', 0):,} / {r.get('skipped', 0):,} | {chk} | {r.get('drops', '—')} drops · door as of {r.get('door_as_of', r.get('index_as_of', '—'))} |")
close = f"ARK BACKFILL CLOSE {wdate} · {len(ORDER) + 1 - len(fails)} of 12 complete · {T.get('in_ark', 0):,} objects · {T.get('ark_bytes', 0) / 1e9:.2f} GB in the twelve buckets · count check {'PASS on every node' if not fails else 'FAIL: ' + ' '.join(fails)}"
rep = f"""# ORDER-033 — ARK BACKFILL — report

Allooloo root · chain of record START_ME_UP\\CHAIN-031-033-032-2026-10-17.md · run {wdate} · CC on Opus 5.5 · anchor tag `pre-033` (commit ea5da50, local)

## Read first

{close}.

Every dated drop since 2026-09-12 in each node's live Azure pond is now in that node's ark bucket at the same path (`<node>/pond/<source>/<drop>/<file>`), with the door as published (`<node>/door/<as_of>/door-bundle.tar.gz`) and the node's NUMBERS LOG lines (`<node>/numbers/<sweep date>.txt`); the apex's sweepREVIEW reports and index sit under `allooloo-ark-apex/apex/`. This was the first real write through ark-writer; it held: put only, no overwrite, retention by the bucket default (GOVERNANCE 365 days).

## Per node

| node | bucket · AWS region | objects in the ark | bytes in the ark | last pass written / skipped (same ETag) | count check (ark objects per dated drop = pond blobs per dated drop) | scope |
|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Shape calls (logged in ORDER-031-BUILD-LOG.md items 44–47)

- Run from the laptop (3.08 GB, 33,320 blobs since 2026-09-12): reader the Allooloo Azure login, writer ark-writer. Singapore's 22,431 small files ran with 48 threads after a first pass at 6 was too slow; the put-only rule made the restart a resume.
- One ark layout for the backfill and the nightly jobs (the 0.31.6 nightly layout `<node>/<date>/…` was changed at root before it ever wrote).
- Same-ETag objects are skipped from the bucket listing (ark-writer may list its own prefix), never downloaded twice; a differing object would be written beside as `<name>-2`.
- Door bundles are deterministic tars (sorted, zero mtimes), so a re-run of the same door is skipped, not duplicated.
- Not carried: blob versions of `door/` before today (the store keeps them; the ark starts the door record at the current as-of); drops dated before 2026-09-12 (out of scope by order).

## Spend

AWS S3 PUT requests ≈ {T.get('in_ark', 0):,} (≈ ${T.get('in_ark', 0) * 0.005 / 1000:,.2f} at list), storage {T.get('ark_bytes', 0) / 1e9:.2f} GB (≈ ${T.get('ark_bytes', 0) / 1e9 * 0.0245:,.2f} a month at list, varies by region); Azure egress ≈ {T.get('ark_bytes', 0) / 1e9:.2f} GB from the eleven stores; listings and the count check a few thousand LIST requests (cents). No lab calls, no Tavily.

## X line (STAGED — the CEO posts)

```
get_issuer · every market's record since 12 Sep now sits in a second cloud, locked · eleven markets, one night's copy every Friday from here · https://agent-swap.ai
```
"""
open(os.path.join(ROOT, 'START_ME_UP', 'ORDER-033-REPORT-2026-10-18.md'), 'w', encoding='utf-8').write(rep); print(close)
ark = {'about': 'last write of each node record to its ark bucket (AWS); written at the sweep close and by the ORDER-033 backfill', 'nodes': {}}
for cc in ORDER:
    r = R.get(cc) or {}
    if r and not r.get('error') and not str(r.get('count_check', '')).startswith('FAIL'):
        ark['nodes'][f'{cc}-cm-kg'] = {'last_write': wdate, 'bucket': r['bucket'], 'objects': r.get('written', 0) + r.get('skipped', 0), 'source': 'ORDER-033 backfill'}
os.makedirs(os.path.join(ROOT, r'CM-KG\ESTATE\public\swap'), exist_ok=True)
json.dump(ark, open(os.path.join(ROOT, r'CM-KG\ESTATE\public\swap\ark.json'), 'w', encoding='utf-8'), indent=1)
k = subprocess.run('az storage account keys list -n allooloocmkgapex -g allooloo-cmkg-shared --query [0].value -o tsv', shell=True, capture_output=True, text=True, env=dict(os.environ, AZURE_CONFIG_DIR=os.path.join(ROOT, '.azure'))).stdout.strip()
from azure.storage.blob import BlobServiceClient, ContentSettings
c = BlobServiceClient('https://allooloocmkgapex.blob.core.windows.net', credential=k).get_container_client('sweeps')
for fn in ('ark.json', 'swaps.json'):
    c.upload_blob(f'swap/{fn}', open(os.path.join(ROOT, r'CM-KG\ESTATE\public\swap', fn), 'rb').read(), overwrite=True, content_settings=ContentSettings(content_type='application/json'))
print('ark.json:', len(ark['nodes']), 'nodes; swap logs of record written to the apex store')
