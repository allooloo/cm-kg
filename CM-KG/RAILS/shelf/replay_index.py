r"""SHELF-01 step 2 (Replay) — the per-issuer view of a sealed market-year, built once when the year seals (and again only when its manifest changes).
For each sealed year of a node: the newest manifest (manifest.json, or the latest re-seal beside it: manifest-2.json, -3 …) is verified (its signature over
its body, and the hash tree root over the rows file), then the rows file is split per issuer: backfill/replay/<year>/<EX>/<code>.json {cmr, rows[], manifest}.
backfill/replay/<year>/_manifest.json carries the manifest the split was built from (the door answers Replay from it). Rows keep their own signatures.
A row whose exchange+ticker is not a key of the node's index is counted (unmapped), never guessed onto another record.
Usage: python -X utf8 -I replay_index.py <cc> [year ...] [--dry]"""
import os, sys, json, re, hashlib, base64, datetime, collections, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, '..', 'isin-dis'), os.path.join(HERE, '..', 'door')]
import store, store_index
from azure.storage.blob import ContentSettings
JS = ContentSettings(content_type='application/json')
sortd = lambda v: [sortd(x) for x in v] if isinstance(v, list) else ({k: sortd(v[k]) for k in sorted(v)} if isinstance(v, dict) else v)
canon = lambda o: json.dumps(sortd(o), separators=(',', ':'), ensure_ascii=False).encode('utf-8')
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip('=')
PUB = json.load(open(os.path.join(HERE, 'cmr-signing.pub.jwk.json'), encoding='utf-8'));   # the public key of record (= the kid on allooloo.ai/.well-known/jwks.json), beside the rails so the job image carries it
PUB = (PUB.get('keys') or [PUB])[0]['x']
def verify(o):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    s = o.get('signature') or {}; body = {k: v for k, v in o.items() if k != 'signature'}
    try: Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(PUB + '=' * (-len(PUB) % 4))).verify(base64.urlsafe_b64decode(s['signature'] + '=' * (-len(s['signature']) % 4)), (s['protected'] + '.' + b64u(canon(body))).encode()); return True
    except Exception: return False
def merkle(hs):
    lv = sorted(hs)
    if not lv: return hashlib.sha256(b'').hexdigest()
    while len(lv) > 1:
        if len(lv) % 2: lv.append(lv[-1])
        lv = [hashlib.sha256(bytes.fromhex(lv[i]) + bytes.fromhex(lv[i + 1])).hexdigest() for i in range(0, len(lv), 2)]
    return lv[0]
SLIM_DROP = {'signature', 'provenance', 'rule_in_force', 'rule_in_force_gap', 'read_by', 'backfill_run_id', 'node', 'width', 'pass', 'era', 'state', 'language', 'wire'}
def year_lines(c, man):
    """SHELF-01 2026-10-27 (us scale: a sealed year is ~1 GB): the rows file streamed from the store through a temp file, never one string in memory.
    Yields (line, row) and leaves the check in man['_check']: the manifest signature, and the hash tree root over every row read"""
    import tempfile
    fd, tp = tempfile.mkstemp(suffix='.jsonl'); os.close(fd); hs = []
    try:
        with open(tp, 'wb') as f: c.download_blob(man['rows_file'], max_concurrency=4).readinto(f)
        with open(tp, encoding='utf-8') as f:
            for l in f:
                if not l.strip(): continue
                r = json.loads(l); hs.append(hashlib.sha256(canon(r)).hexdigest()); yield l.rstrip('\n'), r
        man['_check'] = {'signature': verify({k: v for k, v in man.items() if k != '_check'}), 'root': merkle(hs) == man['hash_tree_root'], 'rows': len(hs)}
    finally:
        try: os.remove(tp)   # the temp copy only; the sealed file stays in the store
        except OSError: pass
def year_rows(c, man):
    """(ok, rows): the year's rows with the sealed-only fields set aside (signature, provenance … stay in the sealed file) and repeated strings shared"""
    pool = {}; s = lambda v: pool.setdefault(v, v) if isinstance(v, str) and len(v) < 400 else v
    rows = [{k: s(v) for k, v in r.items() if k not in SLIM_DROP} for _, r in year_lines(c, man)]
    ck = man.pop('_check'); return ck['signature'] and ck['root'], rows
def newest_manifest(c, y):
    ns = [b.name for b in c.list_blobs(name_starts_with=f'backfill/{y}/') if re.match(rf'backfill/{y}/manifest(-\d+)?\.json$', b.name)]
    return sorted(ns, key=lambda n: int((re.search(r'-(\d+)\.json$', n) or [0, 1])[1]))[-1] if ns else None
def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; dry = '--dry' in sys.argv; cc = a[0]; node = f'{cc}-cm-kg'
    c = store.cont(cc); ix = store.bj(c, 'door/index.json'); cmrs = set((ix.get('cmr') or {}).keys())
    ys = [int(y) for y in a[1:]] or sorted({int(b.name.split('/')[1]) for b in c.list_blobs(name_starts_with='backfill/') if re.match(r'backfill/\d{4}/manifest', b.name)})
    report = {}
    for y in ys:
        mn = newest_manifest(c, y)
        if not mn: report[y] = {'sealed': False}; continue
        man = store.bj(c, mn)
        by = collections.defaultdict(list); unmapped = 0   # per issuer, the sealed lines as written (the file is in date order, so each issuer's lines are too)
        for l, r in year_lines(c, man):
            k = f"{node}/{r.get('exchange')}/{r.get('ticker')}"
            if k.upper() in cmrs: by[(ix['cmr'][k.upper()] or [k])[0]].append(l)
            else: unmapped += 1
        ck = man.pop('_check'); sig_ok, root_ok = ck['signature'], ck['root']; rows = range(ck['rows'])
        if not (sig_ok and root_ok): report[y] = {'sealed': True, 'manifest': mn, 'signature': sig_ok, 'root': root_ok, 'built': False, 'why': 'the manifest does not verify — not lit'}; continue
        mref = {'name': mn, 'hash_tree_root': man['hash_tree_root'], 'rows': man['rows'], 'run': man['run'], 'rows_file': man['rows_file'], 'signature': man['signature']}
        if not dry:
            def put(item):
                k, rs = item; ex, code = k.split('/')[1], k.split('/', 2)[2]
                head = json.dumps({'cmr': k, 'year': y}, ensure_ascii=False, separators=(',', ':'))[:-1]; tail = json.dumps({'manifest': mref}, ensure_ascii=False, separators=(',', ':'))[1:]
                body = (head + ',"rows":[' + ','.join(rs) + '],' + tail).encode('utf-8')   # rows exactly as sealed, in date order
                for t in range(5):   # a timed-out write is tried again (us 2025, laptop run 2026-10-28)
                    try: c.upload_blob(f'backfill/replay/{y}/{ex}/{store_index.slug(code)}.json', body, overwrite=True, content_settings=JS, max_concurrency=2, timeout=600); break
                    except Exception:
                        if t == 4: raise
                        __import__('time').sleep(5 * (t + 1))
            with cf.ThreadPoolExecutor(16) as ex: list(ex.map(put, by.items()))
            c.upload_blob(f'backfill/replay/{y}/_manifest.json', json.dumps(dict(man, replay_built_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), replay_from=mn), ensure_ascii=False).encode(), overwrite=True, content_settings=JS)
        report[y] = {'sealed': True, 'manifest': mn, 'signature': sig_ok, 'root': root_ok, 'rows': len(rows), 'issuers': len(by), 'unmapped_rows': unmapped, 'built': not dry}
        print(cc, y, json.dumps(report[y]), flush=True)
    json.dump(report, open(os.path.join(HERE, f'replay-{cc}-{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")}.json'), 'w'), indent=1)
if __name__ == '__main__': main()
