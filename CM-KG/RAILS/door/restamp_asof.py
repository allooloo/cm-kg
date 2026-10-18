r"""ORDER-027 A1 (2026-10-17): a node's as_of is the sweep's MARKET DATE (the Friday the weekly task is armed for), never the UTC moment the node started.
Re-stamps door/facts.json and door/nodes.json in the node's regional store to that date. Facts and nodes only: no record or event blob is touched,
nothing re-harvested. Blob versioning is on in every store, so the previous facts/nodes stay as prior versions; a local copy of each is also kept
beside this run under C:\ALLOOLOO\AZURE\restamp\<date-of-run>\ (Rule One).
Usage: python restamp_asof.py <cc> <region> <yyyy-mm-dd>
Used by sweep_node.ps1 after the United States container job (the job stamps its own date from the container clock, which is UTC), and once by
ORDER-027 for the six doors the 2026-10-16 sweep stamped 2026-10-17. Tenant guard as provision_region.py. Storage keys in memory only."""
import json, os, sys, subprocess, datetime
TENANT = '04a24e43-dc13-4578-950a-910db076a799'; SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
cc, region, date = sys.argv[1], sys.argv[2], sys.argv[3]
datetime.date.fromisoformat(date)
node = f'{cc}-cm-kg'; rg = f'allooloo-cmkg-{region}'; sa = f'allooloocmkg{cc}pond'
def az(*a, raw=False):
    p = subprocess.run(['az', *a] + ([] if raw else ['-o', 'json']), capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
    if p.returncode != 0: raise SystemExit(f"az {' '.join(a[:4])} failed: {(p.stderr or p.stdout)[-400:]}")
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az('account', 'show')
if not acct or acct.get('tenantId') != TENANT or acct.get('id') != SUB: raise SystemExit('STOP: not the tenant/subscription of record')
k = az('storage', 'account', 'keys', 'list', '-n', sa, '-g', rg, '--query', '[0].value', '-o', 'tsv', raw=True)
keep = os.path.join(r'C:\ALLOOLOO\AZURE\restamp', datetime.date.today().isoformat()); os.makedirs(keep, exist_ok=True)
changed = []
for fn in ('facts.json', 'nodes.json'):
    p = os.path.join(keep, f'{cc}-{fn}')
    az('storage', 'blob', 'download', '--account-name', sa, '--account-key', k, '-c', 'pond', '-n', f'door/{fn}', '-f', p, '--no-progress', '-o', 'none', raw=True)
    j = json.load(open(p, encoding='utf-8'))
    pre = p.replace('.json', '.pre-027-20261017.json')
    if not os.path.exists(pre): os.replace(p, pre)
    else: os.remove(p)
    before = None
    if fn == 'facts.json':
        nf = (j.get('nodes') or {}).get(node)
        if nf is None: raise SystemExit(f'STOP: {node} missing from door/facts.json')
        before = nf.get('as_of'); nf['as_of'] = date
        if 'as_of' in j: j['as_of'] = max(v.get('as_of') or '' for v in j['nodes'].values())
        j['as_of_rule'] = 'market date of the weekly sweep (ORDER-027 A1)'
    else:
        for x in j:
            if x.get('node') == node: before = x.get('as_of'); x['as_of'] = date
        if before is None: raise SystemExit(f'STOP: {node} missing from door/nodes.json')
    out = os.path.join(keep, f'{cc}-{fn}')
    json.dump(j, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if before != date:
        az('storage', 'blob', 'upload', '--account-name', sa, '--account-key', k, '-c', 'pond', '-n', f'door/{fn}', '-f', out, '--overwrite', 'true', '--content-type', 'application/json', '--no-progress', '-o', 'none', raw=True)
        changed.append(f'{fn} {before} -> {date}')
print(f"{node} restamp: {'; '.join(changed) if changed else 'already ' + date} (door reloads facts and nodes within ten minutes)")
