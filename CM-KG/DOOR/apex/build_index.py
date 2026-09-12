"""Apex index builder (ORDER-018): rebuilds static/index.json (identifier -> node, index-only, no record bodies)
and static/nodes.json from the eleven regional stores' door/index.json and door/nodes.json.
Run from CM-KG\DOOR\apex; then `wrangler deploy`. Tenant guard: the subscription of record only.
Usage: python build_index.py [cc ...]   (no args = all eleven nodes)"""
import json, os, subprocess, sys, tempfile

TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
NODES = {'ca': 'canadacentral', 'uk': 'uksouth', 'au': 'australiaeast', 'sg': 'southeastasia', 'ch': 'switzerlandnorth',
         'de': 'germanywestcentral', 'fr': 'francecentral', 'nl': 'westeurope', 'jp': 'japaneast', 'kr': 'koreacentral', 'us': 'eastus'}
HERE = os.path.dirname(os.path.abspath(__file__)); STATIC = os.path.join(HERE, 'static')

def az(*a):
    r = subprocess.run(['az', *a], capture_output=True, text=True, shell=True); return r.stdout.strip()

acct = json.loads(az('account', 'show', '-o', 'json') or '{}')
if acct.get('tenantId') != TENANT or acct.get('id') != SUB: sys.exit('STOP: not the Allooloo tenant/subscription of record')

want = sys.argv[1:] or list(NODES)
idx = {'ticker': {}, 'isin': {}, 'lei': {}, 'alias': {}, 'name': {}, 'cmr': {}}
nodes = json.load(open(os.path.join(STATIC, 'nodes.json'), encoding='utf-8'))
tmp = tempfile.mkdtemp(prefix='apex-'); counts = {}
for cc in want:
    sa = f'allooloocmkg{cc}pond'; k = az('storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{NODES[cc]}', '-n', sa, '--query', '[0].value', '-o', 'tsv')
    if not k: k = az('storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{NODES[cc]}', '-n', sa, '--query', '[1].value', '-o', 'tsv')
    got = {}
    for fn in ('index.json', 'nodes.json'):
        p = os.path.join(tmp, f'{cc}-{fn}')
        az('storage', 'blob', 'download', '--account-name', sa, '--account-key', k, '-c', 'pond', '-n', f'door/{fn}', '-f', p, '--no-progress', '-o', 'none')
        got[fn] = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
    ni = got['index.json']
    if not ni: print(cc, 'no door/index.json in the regional store (node stays as listed)'); continue
    node = f'{cc}-cm-kg'; counts[cc] = len(ni.get('keys', []))
    for kind in idx:
        for ident, keys in (ni.get(kind) or {}).items():
            cur = idx[kind].get(ident)
            if cur is None: idx[kind][ident] = node
            elif isinstance(cur, list):
                if node not in cur: cur.append(node)
            elif cur != node: idx[kind][ident] = [cur, node]
    for x in (got['nodes.json'] or []):
        if x.get('node') == node:
            for y in nodes:
                if y.get('node') == node: y.update({kk: x[kk] for kk in ('live', 'as_of', 'records', 'exchanges') if kk in x})
for kind in idx:
    for ident, v in idx[kind].items():
        if isinstance(v, list): idx[kind][ident] = sorted(v)
json.dump(idx, open(os.path.join(STATIC, 'index.json'), 'w', encoding='utf-8'), separators=(',', ':'))
json.dump(nodes, open(os.path.join(STATIC, 'nodes.json'), 'w', encoding='utf-8'), indent=1)
print('node keys', counts); print('apex index', {kk: len(v) for kk, v in idx.items()}, 'size', os.path.getsize(os.path.join(STATIC, 'index.json')))
print('nodes live', [n['node'] for n in nodes if n.get('live')])
