r"""DOORS-03 (2026-10-26) step a — read only: per node, the ISINs in the store's door/index.json that resolve to more than one record, with the venue pairs
involved. Reads every roster store (door/index.json, pond container), writes dup-isins-<label>-<UTC stamp>.json beside and prints the table.
Usage: python -X utf8 -I dup_isins.py <label> [cc ...]"""
import json, os, sys, subprocess, tempfile, datetime, collections, concurrent.futures as cf
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'
HERE = os.path.dirname(os.path.abspath(__file__))
def az(*a): return subprocess.run(['az', *a], capture_output=True, text=True, shell=True).stdout.strip()
nodes = json.load(open(r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json', encoding='utf-8'))
label = sys.argv[1] if len(sys.argv) > 1 else 'read'; want = sys.argv[2:]
tmp = tempfile.mkdtemp(prefix='doors03-')
def one(n):
    cc = n['node'].split('-')[0]; st = (n.get('region') or {}).get('store'); sa = f'allooloocmkg{cc}pond'
    k = az('storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{st}', '-n', sa, '--query', '[0].value', '-o', 'tsv')
    p = os.path.join(tmp, f'{cc}-index.json')
    az('storage', 'blob', 'download', '--account-name', sa, '--account-key', k, '-c', 'pond', '-n', 'door/index.json', '-f', p, '--no-progress', '-o', 'none')
    if not os.path.exists(p): return cc, None
    ix = json.load(open(p, encoding='utf-8')); node = n['node']
    isin = {i: [x for x in ks if x.startswith(node + '/')] for i, ks in (ix.get('isin') or {}).items()}
    dups = {i: ks for i, ks in isin.items() if len(ks) > 1}
    pairs = collections.Counter(' + '.join(sorted(k.split('/')[1] for k in ks)) for ks in dups.values())
    return cc, {'node': node, 'isins': len(isin), 'records': len(ix.get('keys') or []), 'dup_isins': len(dups), 'records_in_dups': sum(len(v) for v in dups.values()), 'venue_pairs': dict(pairs.most_common(8)), 'dups': dups}
rows = {}
with cf.ThreadPoolExecutor(8) as ex:
    for cc, r in ex.map(one, [n for n in nodes if not want or n['node'].split('-')[0] in want]): rows[cc] = r
print('| node | records | ISINs | ISINs on >1 record | records in those | venue pairs (top) |'); print('|---|---|---|---|---|---|')
for cc in sorted(rows):
    r = rows[cc]
    if not r: print(f'| {cc}-cm-kg | index not read | | | | |'); continue
    print(f"| {r['node']} | {r['records']} | {r['isins']} | {r['dup_isins']} | {r['records_in_dups']} | {'; '.join(f'{k} ×{v}' for k, v in list(r['venue_pairs'].items())[:4])} |")
print('total ISINs on >1 record:', sum(r['dup_isins'] for r in rows.values() if r), '· nodes with any:', sum(1 for r in rows.values() if r and r['dup_isins']))
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ')
json.dump(rows, open(os.path.join(HERE, f'dup-isins-{label}-{stamp}.json'), 'w'), indent=1)
