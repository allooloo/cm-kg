r"""publish_stores.py — RESLATE-01: the page store step of the re-slate. For each market: the pages its job wrote (research/state/pages.jsonl in the market's
store) and this run's manifest and exchange pages (research/out/<night>/) are brought here, then publish.py (write-on-change into the page store) and
exchange.py --publish run. The publish ledgers (CM-KG\RESEARCH\published\) are kept in the apex store (research/published/<cc>.json) so the job image holds
none. `seed` pushes the laptop's state into the stores (the first run's starting point).
Usage: python -X utf8 publish_stores.py <night> <cc> [...]   ·   python -X utf8 publish_stores.py seed <cc> [...]"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'isin-dis')); import store
R = r'C:\ALLOOLOO\CM-KG\RESEARCH'; POND = r'C:\ALLOOLOO\CM-KG\POND'; a = sys.argv[1:]; bad = 0
def latest_cov(cc):
    b = os.path.join(POND, f'{cc}-cm-kg', 'research-coverage'); import re
    ds = [d for d in os.listdir(b) if re.match(r'^\d{4}-\d{2}-\d{2}', d) and os.path.exists(os.path.join(b, d, 'raw.jsonl'))] if os.path.isdir(b) else []
    return os.path.join(b, sorted(ds, key=lambda d: (d[:10], int(d[11:] or 1)))[-1], 'raw.jsonl') if ds else None
if a[0] == 'seed':
    for cc in a[1:]:
        try:
            c = store.cont(cc); c.upload_blob('research/state/pages.jsonl', open(os.path.join(R, 'pages', f'{cc}.jsonl'), 'rb').read(), overwrite=True); cov = latest_cov(cc)
            if cov:   # one row per issuer: the newest read
                rows = {}
                for l in open(cov, encoding='utf-8'): j = json.loads(l); rows[j['cmr']] = l if l.endswith('\n') else l + '\n'
                c.upload_blob('research/state/coverage.jsonl', ''.join(rows.values()).encode('utf-8'), overwrite=True)
            print(cc, 'seeded: pages', sum(1 for _ in open(os.path.join(R, 'pages', f'{cc}.jsonl'), encoding='utf-8')), 'coverage rows', len(rows) if cov else 0, flush=True)
        except Exception as e: bad += 1; print(cc, 'FAILED', repr(e)[:200], flush=True)
    sys.exit(1 if bad else 0)
night = a[0]; ccs = a[1:]; ok = []
def apex():
    from azure.storage.blob import BlobServiceClient
    sa = os.environ.get('APEX_STORAGE_ACCOUNT', 'allooloocmkgapex'); k = subprocess.run((store.AZ if hasattr(store, 'AZ') else ['az']) + ['storage', 'account', 'keys', 'list', '-g', 'allooloo-cmkg-shared', '-n', sa, '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True).stdout.strip()
    return BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=k).get_container_client(os.environ.get('OPS_CONTAINER', 'ops'))
ops = apex(); os.makedirs(os.path.join(R, 'published'), exist_ok=True)
for f in ('pages', 'exchanges', 'numbers'): os.makedirs(os.path.join(R, f), exist_ok=True)
for b in ops.list_blobs(name_starts_with='research/published/'):   # every market's ledger: the page store's meta is rebuilt whole from them
    open(os.path.join(R, 'published', os.path.basename(b.name)), 'wb').write(ops.download_blob(b.name).readall())
for cc in ccs:
    try:
        c = store.cont(cc); man = c.download_blob(f'research/out/{night}/manifest.json').readall()
        open(os.path.join(R, 'pages', f'{cc}.manifest.json'), 'wb').write(man); open(os.path.join(R, 'pages', f'{cc}.jsonl'), 'wb').write(c.download_blob('research/state/pages.jsonl').readall()); ok.append(cc)
    except Exception as e: print(cc, 'no research output for', night, repr(e)[:120], flush=True)
for cc in list(os.listdir(os.path.join(R, 'published'))):   # a market published before but not this run still needs its manifest for the ledger
    c2 = cc[:-5]
    if not os.path.exists(os.path.join(R, 'pages', f'{c2}.manifest.json')):
        try: open(os.path.join(R, 'pages', f'{c2}.manifest.json'), 'wb').write(ops.download_blob(f'research/manifests/{c2}.json').readall())
        except Exception: os.remove(os.path.join(R, 'published', cc))
if ok:
    r = subprocess.run([sys.executable, '-X', 'utf8', 'publish.py'] + ok, cwd=HERE); bad += r.returncode != 0
    r = subprocess.run([sys.executable, '-X', 'utf8', 'exchange.py', '--publish'] + ok, cwd=HERE); bad += r.returncode != 0
    for cc in ok:
        ops.upload_blob(f'research/published/{cc}.json', open(os.path.join(R, 'published', f'{cc}.json'), 'rb').read(), overwrite=True); ops.upload_blob(f'research/manifests/{cc}.json', open(os.path.join(R, 'pages', f'{cc}.manifest.json'), 'rb').read(), overwrite=True)
print('page store: markets published', len(ok), 'of', len(ccs), flush=True); sys.exit(1 if bad else 0)
