r"""ISIN disambiguation (2026-10-27) — read only census, all roster stores.
Per node, from the store's door/index.json:
  distinct  — ISINs whose lookup lists more than one distinct record key (venue pairs given)
  repeated  — ISINs whose lookup lists the same record key more than once
Across nodes: ISINs present on more than one node's index (the apex answers those 'ambiguous').
Writes census-<label>-<UTC stamp>.json beside (indexes kept under idx-<stamp>/) and prints the table.
Usage: python -X utf8 -I census.py <label> [cc ...]"""
import json, os, sys, subprocess, datetime, collections, concurrent.futures as cf
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'
HERE = os.path.dirname(os.path.abspath(__file__))
def az(*a): return subprocess.run(['az', *a], capture_output=True, text=True, shell=True).stdout.strip()
nodes = json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))
label = sys.argv[1] if len(sys.argv) > 1 else 'read'; want = sys.argv[2:]
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ')
idx = os.path.join(HERE, f'idx-{stamp}'); os.makedirs(idx, exist_ok=True)
def one(n):
    cc = n['node'].split('-')[0]; st = (n.get('region') or {}).get('store'); sa = f'allooloocmkg{cc}pond'
    k = az('storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{st}', '-n', sa, '--query', '[0].value', '-o', 'tsv')
    p = os.path.join(idx, f'{cc}-index.json')
    az('storage', 'blob', 'download', '--account-name', sa, '--account-key', k, '-c', 'pond', '-n', 'door/index.json', '-f', p, '--no-progress', '-o', 'none')
    if not os.path.exists(p): return cc, None
    ix = json.load(open(p, encoding='utf-8')); node = n['node']
    isin = {i: [x for x in ks if x.startswith(node + '/')] for i, ks in (ix.get('isin') or {}).items()}
    distinct = {i: sorted(set(ks)) for i, ks in isin.items() if len(set(ks)) > 1}
    repeated = {i: ks for i, ks in isin.items() if len(ks) > len(set(ks))}
    pairs = collections.Counter(' + '.join(sorted(k.split('/')[1] for k in ks)) for ks in distinct.values())
    return cc, {'node': node, 'records': len(ix.get('keys') or []), 'isins': len(isin), 'distinct': distinct, 'repeated': repeated,
                'venue_pairs': dict(pairs.most_common(8)), 'isin_set': sorted(i for i, ks in isin.items() if ks)}
rows = {}
with cf.ThreadPoolExecutor(8) as ex:
    for cc, r in ex.map(one, [n for n in nodes if not want or n['node'].split('-')[0] in want]): rows[cc] = r
where = collections.defaultdict(list)
for cc, r in rows.items():
    for i in (r or {}).get('isin_set', []): where[i].append(cc)
cross = {i: sorted(c) for i, c in where.items() if len(c) > 1}
cross_by = collections.Counter(c for cs in cross.values() for c in cs)
print('| node | records | ISINs | >1 distinct record | same record repeated | on another node too | venue pairs |'); print('|---|---|---|---|---|---|---|')
for cc in sorted(rows):
    r = rows[cc]
    if not r: print(f'| {cc}-cm-kg | index not read | | | | | |'); continue
    print(f"| {r['node']} | {r['records']} | {r['isins']} | {len(r['distinct'])} | {len(r['repeated'])} | {cross_by.get(cc, 0)} | {'; '.join(f'{k} ×{v}' for k, v in list(r['venue_pairs'].items())[:4])} |")
print('distinct:', sum(len(r['distinct']) for r in rows.values() if r), '· repeated:', sum(len(r['repeated']) for r in rows.values() if r), '· cross-node ISINs:', len(cross))
pair_nodes = collections.Counter(' + '.join(c) for c in cross.values())
print('cross-node pairs:', dict(pair_nodes.most_common(12)))
for r in rows.values():
    if r: r.pop('isin_set')
json.dump({'stamp': stamp, 'rows': rows, 'cross': cross}, open(os.path.join(HERE, f'census-{label}-{stamp}.json'), 'w'), indent=1)
