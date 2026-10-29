r"""backfill.py — BACKFILL-01 (DAY ORDER 7, Allooloo Datasets, epoch 2021-01-01): the live stack pointed backward, per market per year, newest year first.
Roster-driven (ENUM-01): the markets are the roster of record; each is read through its policy line (policy.json: archive, base URL, earliest reachable,
licence note, reader, adapter, pace). A roster market with no line stops the rail (named). Markets run in the B-3 order, one complete before the next.

A backfill row is a live row (the node's event row: exchange, ticker, isin, lei, issuer, event_type, date, title as filed, wire, source, url, read_by, detail,
node, width, state, pass) with four additions — era "backfill"; rule_in_force (the ECO rule and version in force on the row's own date, eco_history.py; blank
with the gap when the register holds none); provenance (archive, source URL, fetch time, document hash, parser version); backfill_run_id — signed Ed25519 with
the node-record key (kid allooloo-cmr-2026-10, the envelope of the live records). Backfill rows never enter the live stream, the halt lists, Issuerwire or the
digest counts: they live under backfill/<year>/ in the node's in-country pond, immutable (never overwritten; a re-run writes beside), with a signed
manifest.json per market per year (market, year, row count, document count, hash-tree root, history_from, source list, parser version, signature). The ark
copy rail mirrors backfill/ to the node's existing ark bucket under the same prefix. history_from (the earliest date actually read) is written to the store's
backfill/facts.json; build_index.py carries it onto the roster entry (apex facts), the ECO page prints it.

  python backfill.py plan                          every roster market: policy line, adapter, order, years done, next action
  python backfill.py run <cc> [--years 2026,2025]  pull, build, sign, land (pond + store), manifest, ark; resumable by (market, year, cursor = the sandbox raw)
  python backfill.py ledger [cc ...]                seed/refresh the order ledger entries (backfill-order/<cc>.json, apex store) from each market's store
  python backfill.py verify <cc> <year>            a random row: signature against the public key, rule_in_force against the ECO history for its date
Environment: BACKFILL_POLICY (a policy copy, dry runs), BACKFILL_LOCAL_ONLY=1 (no store, no ark), BACKFILL_ORDER_FORCE=1 (skip the B-3 gate, by hand only),
CMR_SIGNING_JWK (the job's vault secret; the laptop reads AGENT KEYS\cmr-signing-jwk.txt, never printed), ARK_* as the node jobs."""
import os, sys, json, hashlib, base64, datetime, random, subprocess, shutil, glob, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import roster, eco_history
ROOT = os.environ.get('CMKG_ROOT_WIN', r'C:\ALLOOLOO') if os.name == 'nt' else os.environ.get('CMKG_ROOT', '/job/ALLOOLOO')
RAILS = os.path.join(ROOT, 'CM-KG', 'RAILS'); POND = os.path.join(ROOT, 'CM-KG', 'POND')
POLICY = os.environ.get('BACKFILL_POLICY') or os.path.join(HERE, 'policy.json')
PARSER = 'backfill.py 1.0.0 (BACKFILL-01, 2026-10-25)'; KID = 'allooloo-cmr-2026-10'; JWKS = 'https://allooloo.ai/.well-known/jwks.json'
EPOCH = '2021-01-01'; T0 = datetime.datetime.now(datetime.timezone.utc); RUN = os.environ.get('CONTAINER_APP_JOB_EXECUTION_NAME') or f'bf-{T0.strftime("%Y%m%dT%H%M%SZ")}'
LOCAL_ONLY = os.environ.get('BACKFILL_LOCAL_ONLY') == '1'
def log(*a): print(T0.strftime('%H:%M:%S') if False else datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S'), *a, flush=True)
POL = json.load(open(POLICY, encoding='utf-8'))
def policy_or_stop():
    g = roster.require('backfill policy (RAILS\\backfill\\policy.json)', POL['markets'])   # stops the rail on a gap, named
    return POL['markets']

# ---------- signing (the live record envelope) ----------
sortd = lambda v: [sortd(x) for x in v] if isinstance(v, list) else ({k: sortd(v[k]) for k in sorted(v)} if isinstance(v, dict) else v)
canon = lambda o: json.dumps(sortd(o), separators=(',', ':'), ensure_ascii=False).encode('utf-8')
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip('=')
PROT = b64u(json.dumps({'alg': 'EdDSA', 'kid': KID}, separators=(',', ':')).encode())
_SK = None
def signer():
    global _SK
    if _SK is None:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        t = os.environ.get('CMR_SIGNING_JWK') or open(os.path.join(ROOT, 'AGENT KEYS', 'cmr-signing-jwk.txt'), encoding='utf-8').read()
        j = json.loads(t); _SK = Ed25519PrivateKey.from_private_bytes(base64.urlsafe_b64decode(j['d'] + '=' * (-len(j['d']) % 4)))
    return _SK
def jsnum(v):
    """a whole float (43.0) as the integer a JavaScript door serves (43): the signed bytes survive the door (SHELF-01 2026-10-28, review-us-2026)"""
    if isinstance(v, float) and v.is_integer(): return int(v)
    if isinstance(v, dict): return {k: jsnum(x) for k, x in v.items()}
    if isinstance(v, list): return [jsnum(x) for x in v]
    return v
def sign(o):
    o = jsnum({k: v for k, v in o.items() if k != 'signature'})
    s = signer().sign((PROT + '.' + b64u(canon(o))).encode())
    o['signature'] = {'alg': 'EdDSA', 'kid': KID, 'protected': PROT, 'signature': b64u(s), 'jwks': JWKS, 'over': "base64url(protected) + '.' + base64url(canonical JSON without signature: keys sorted, compact)"}
    return o
def verify_sig(o, pub_x):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    s = o['signature']; body = {k: v for k, v in o.items() if k != 'signature'}
    k = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(pub_x + '=' * (-len(pub_x) % 4)))
    try: k.verify(base64.urlsafe_b64decode(s['signature'] + '=' * (-len(s['signature']) % 4)), (s['protected'] + '.' + b64u(canon(body))).encode()); return True
    except Exception: return False
def merkle(hexes):
    lvl = [bytes.fromhex(h) for h in sorted(hexes)] or [hashlib.sha256(b'').digest()]
    while len(lvl) > 1: lvl = [hashlib.sha256(lvl[i] + (lvl[i + 1] if i + 1 < len(lvl) else lvl[i])).digest() for i in range(0, len(lvl), 2)]
    return lvl[0].hex()

# ---------- the store (the node's in-country pond) ----------
_C = {}
def store(cc):
    if cc in _C: return _C[cc]
    from azure.storage.blob import BlobServiceClient
    sa = f'allooloocmkg{cc}pond'; reg = roster.region(cc)
    if os.environ.get('STORAGE_KEY'): key = os.environ['STORAGE_KEY']
    else:
        p = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-n', sa, '-g', f'allooloo-cmkg-{reg}', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=(os.name == 'nt'), env=dict(os.environ, AZURE_CONFIG_DIR=os.environ.get('AZURE_CONFIG_DIR', r'C:\ALLOOLOO\.azure')))
        key = p.stdout.strip()
        if not key: raise SystemExit(f'store key not read for {sa}: {p.stderr[-200:]}')
    _C[cc] = BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client(os.environ.get('STORAGE_CONTAINER', 'pond')); return _C[cc]
def put_beside(cc, name, data, ct='application/json'):
    """immutable: the first write takes the name, a re-run lands beside (-2, -3 ...); never over"""
    from azure.storage.blob import ContentSettings
    c = store(cc); n, i = name, 1
    while c.get_blob_client(n).exists(): i += 1; root, ext = os.path.splitext(name); n = f'{root}-{i}{ext}'
    c.upload_blob(n, data, content_settings=ContentSettings(content_type=ct)); return n
def get_json(cc, name):
    try: return json.loads(store(cc).get_blob_client(name).download_blob().readall())
    except Exception: return None

# ---------- the day the live record began (its first pond drop) ----------
def live_start(cc):
    node = f'{cc}-cm-kg'; ds = []
    for sub in ('width1', 'width0'):
        d = os.path.join(POND, node, sub)
        if os.path.isdir(d): ds += [x[:10] for x in os.listdir(d) if re.match(r'\d{4}-\d{2}-\d{2}', x)]
    if not ds and not LOCAL_ONLY:
        try: ds = [b.name.split('/')[2][:10] for b in store(cc).list_blobs(name_starts_with='pond/width1/')][:1] + [b.name.split('/')[2][:10] for b in store(cc).list_blobs(name_starts_with='pond/width0/')][:1]
        except Exception: ds = []
    return min(ds) if ds else None

# ---------- adapters ----------
def sandbox(cc, tag):
    d = os.path.join(POND, f'{cc}-cm-kg', 'backfill', '_work', tag); os.makedirs(d, exist_ok=True); return d
def collect_raw(raw_dir, since, until):
    """every event the workers wrote (raw/<task>.jsonl rows with events[], or event rows), deduped on the live key, inside [since, until]"""
    seen, out = set(), []
    for f in sorted(glob.glob(os.path.join(raw_dir, '*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            try: d = json.loads(line)
            except Exception: continue
            evs = d.get('events') if isinstance(d.get('events'), list) else ([d] if d.get('date') and d.get('url') else [])
            for e in evs:
                if not (e.get('date') and e.get('url')) or not (since <= e['date'][:10] <= until): continue
                k = (e.get('exchange'), e.get('ticker'), e.get('event_type'), e['date'][:10], e['url'])
                if k in seen: continue
                seen.add(k); e = dict(e); e.pop('key', None); e['_raw_line'] = hashlib.sha256(line.encode('utf-8')).hexdigest(); e['_raw_file'] = os.path.basename(f); out.append(e)
    return out
def adapter_width1(cc, line, since, until, tag):
    """the market's live Width 1 workers, run in a sandbox copy of its rail with the window opened back to `since` (never the live raw/, never the pond lock)"""
    src = os.path.join(RAILS, f'{cc}-width1'); wd = sandbox(cc, tag); rail = os.path.join(wd, 'rail')
    if not os.path.isdir(rail): shutil.copytree(src, rail, ignore=shutil.ignore_patterns('raw', '__pycache__', '*.pre-*', '*.log'))
    os.makedirs(os.path.join(rail, 'raw'), exist_ok=True)
    days = (datetime.date.today() - datetime.date.fromisoformat(since)).days + 1
    env = dict(os.environ, WINDOW_DAYS=str(days), PYTHONIOENCODING='utf-8', **(line.get('env') or {}))
    for step in line['steps']:
        log(f'{cc} backfill step {step} (window {days} days, since {since})')
        p = subprocess.run([sys.executable, '-X', 'utf8', step], cwd=rail, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        open(os.path.join(wd, f'{step}.log'), 'a', encoding='utf-8').write(p.stdout[-20000:] + '\n' + p.stderr[-20000:])
        if p.returncode != 0: raise RuntimeError(f'{step} exit {p.returncode}: {(p.stderr or p.stdout)[-300:]}')
    return collect_raw(os.path.join(rail, 'raw'), since, until)
def adapter_eu(cc, line, since, until, tag):
    """the node's own events reader (eu-sources / row-sources <cc>\\events.py fetch(isin, since)), over today's roster drop, window opened back to `since`"""
    wd = sandbox(cc, tag); out = os.path.join(wd, 'events.jsonl')
    if not os.path.exists(out):
        p = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, 'eu_backfill.py'), cc, since, out], env=dict(os.environ, PYTHONIOENCODING='utf-8'), capture_output=True, text=True, encoding='utf-8', errors='replace')
        open(os.path.join(wd, 'eu_backfill.log'), 'a', encoding='utf-8').write(p.stdout[-20000:] + p.stderr[-20000:])
        if p.returncode != 0: raise RuntimeError(f'eu_backfill exit {p.returncode}: {(p.stderr or p.stdout)[-300:]}')
    return collect_raw(wd, since, until)
def adapter_edgar(cc, line, since, until, tag):
    """SHELF-01 2026-10-27: one line per filing on disk plus the filers' listings; run() seals it month by month (edgar_months / edgar_fan)"""
    wd = sandbox(cc, tag); out = os.path.join(wd, 'filings.ndjson')
    if not os.path.exists(out):
        p = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, 'edgar_backfill.py'), since, until, out], env=dict(os.environ, PYTHONIOENCODING='utf-8'), capture_output=True, text=True, encoding='utf-8', errors='replace')
        open(os.path.join(wd, 'edgar_backfill.log'), 'a', encoding='utf-8').write(p.stdout[-20000:] + p.stderr[-20000:])
        if p.returncode != 0: raise RuntimeError(f'edgar_backfill exit {p.returncode}: {(p.stderr or p.stdout)[-300:]}')
    return {'_stream': 'edgar', 'file': out, 'listings': out + '.listings.json'}
def edgar_months(src, since, until):
    """pass 1: the filing lines inside [since, until] split into month files beside the source (months/YYYY-MM.ndjson), each with its own line's sha256"""
    md = os.path.join(os.path.dirname(src), 'months'); os.makedirs(md, exist_ok=True); fh = {}; first = None
    for line in open(src, encoding='utf-8'):
        try: e = json.loads(line).get('e')
        except Exception: continue
        if not e or not (since <= e['date'][:10] <= until): continue
        m = e['date'][:7]; first = min(first or e['date'][:10], e['date'][:10])
        if m not in fh: fh[m] = open(os.path.join(md, f'{m}.ndjson'), 'w', encoding='utf-8')
        fh[m].write(json.dumps({'h': hashlib.sha256(line.encode('utf-8')).hexdigest(), 'e': e}, ensure_ascii=False) + '\n')
    for f in fh.values(): f.close()
    return md, first
def edgar_fan(md, m, L):
    """one month's filings, each fanned out to every listing line of its filer (as the live us rail attaches them), deduped on the live key"""
    seen, out = set(), []
    for line in open(os.path.join(md, f'{m}.ndjson'), encoding='utf-8'):
        d = json.loads(line); e = d['e']
        for ex, tk, nm in L.get(e['cik']) or []:
            k = (ex, tk, e['event_type'], e['date'][:10], e['url'])
            if k in seen: continue
            seen.add(k); out.append(dict(e, exchange=ex, ticker=tk, issuer=nm, _raw_line=d['h'], _raw_file='filings.ndjson'))
    return out
ADAPTERS = {'width1-window': adapter_width1, 'eu-node-events': adapter_eu, 'edgar': adapter_edgar}

# ---------- rows ----------
def build_rows(cc, line, raw, year, fetched_at):
    rows = []
    for e in raw:
        r = {k: v for k, v in e.items() if not k.startswith('_')}
        r.update({'node': f'{cc}-cm-kg', 'width': 1, 'state': r.get('state') or 'sourced', 'pass': 'backfill', 'era': 'backfill', 'backfill_run_id': RUN})
        rif, gap = eco_history.rule_in_force(cc, r['date'][:10]); r['rule_in_force'] = rif
        if gap: r['rule_in_force_gap'] = gap
        r['provenance'] = {'archive': line['archive'], 'source_url': r.get('url'), 'fetch_time': fetched_at, 'document_hash': 'sha256:' + e['_raw_line'],
                           'hash_of': f"the archive's own listing entry as fetched (raw/{e['_raw_file']} line); the document body hash is the nightly doc-hash pass", 'parser_version': PARSER, 'reader': r.get('read_by')}
        rows.append(sign(r))
    rows.sort(key=lambda x: (x['date'], x.get('exchange') or '', x.get('ticker') or '', x['url']))
    return rows

def years_for(cc, ls):
    top = int((ls or T0.date().isoformat())[:4]); return list(range(top, int(EPOCH[:4]) - 1, -1))
def done_years(cc):
    if LOCAL_ONLY:
        return sorted({int(os.path.basename(os.path.dirname(p))) for p in glob.glob(os.path.join(POND, f'{cc}-cm-kg', 'backfill', '*', 'manifest.json'))}, reverse=True)
    return sorted({int(b.name.split('/')[1]) for b in store(cc).list_blobs(name_starts_with='backfill/') if b.name.endswith('manifest.json') and b.name.split('/')[1].isdigit()}, reverse=True)

# ---------- the order ledger (B-3): one shared place, backfill-order/<cc>.json in the apex store ----------
# Each market's own job writes its entry after its run; the gate reads only this ledger. Jobs reach it with their managed identity (Storage Blob Data
# Contributor on this one container); the laptop with the account key. A market never reads another country's store.
ORDER_SA = os.environ.get('BACKFILL_ORDER_ACCOUNT', 'allooloocmkgapex'); ORDER_CONT = 'backfill-order'
_L = None
def ledger():
    global _L
    if _L is None:
        from azure.storage.blob import BlobServiceClient
        url = f'https://{ORDER_SA}.blob.core.windows.net'
        if os.environ.get('IDENTITY_ENDPOINT') or os.environ.get('MSI_ENDPOINT'):
            from azure.identity import ManagedIdentityCredential; cred = ManagedIdentityCredential()
        else:
            p = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-n', ORDER_SA, '-g', 'allooloo-cmkg-shared', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=(os.name == 'nt'), env=dict(os.environ, AZURE_CONFIG_DIR=os.environ.get('AZURE_CONFIG_DIR', r'C:\ALLOOLOO\.azure')))
            cred = p.stdout.strip()
            if not cred: raise RuntimeError(f'order ledger key not read: {p.stderr[-200:]}')
        _L = BlobServiceClient(url, credential=cred).get_container_client(ORDER_CONT)
    return _L
def order_get(cc):
    """the market's ledger entry, None when it has none; raises when the ledger cannot be read (the gate counts that as waiting)"""
    from azure.core.exceptions import ResourceNotFoundError
    try: return json.loads(ledger().get_blob_client(f'{cc}.json').download_blob().readall())
    except ResourceNotFoundError: return None
def order_publish(cc, ls):
    """write this market's progress to the ledger (the one mutable file per market); a failed write is logged, never fatal to the market's own run"""
    need = years_for(cc, ls); got = done_years(cc); left = sorted(set(need) - set(got), reverse=True)
    e = {'market': cc, 'need': need, 'done': sorted(set(got) & set(need), reverse=True), 'left': left, 'complete': not left, 'live_record_began': ls,
         'run': RUN, 'parser_version': PARSER, 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if LOCAL_ONLY: return dict(e, written=False)
    try:
        from azure.storage.blob import ContentSettings
        ledger().upload_blob(f'{cc}.json', json.dumps(e, indent=1).encode('utf-8'), overwrite=True, content_settings=ContentSettings(content_type='application/json'))
        log(f"order ledger: {cc} complete={e['complete']} left={left}"); return dict(e, written=True)
    except Exception as x:
        log(f'ORDER LEDGER WRITE FAILED for {cc}: {type(x).__name__}: {str(x)[:200]}'); return dict(e, written=False, error=str(x)[:200])

def run(cc, want_years=None):
    pol = policy_or_stop(); line = pol[cc]
    if line['adapter'] == 'none': log(f'{cc}: {line["why"]}'); return {'market': cc, 'adapter': 'none'}
    if line['adapter'] not in ADAPTERS: raise SystemExit(f'ROSTER POLICY GAP · backfill adapter {line["adapter"]!r} for {cc} has no reader — rail refused')
    order = [c for c in POL['order'] if c in roster.codes()]
    if os.environ.get('BACKFILL_ORDER_FORCE') != '1':
        for prev in order[:order.index(cc)]:   # B-3 gate (2026-10-26 fix): the order ledger, never another country's store; unreadable = waiting
            if pol[prev]['adapter'] == 'none': continue
            try: e = order_get(prev); why = None if e else 'no ledger entry yet'
            except Exception as x: e, why = None, f'ledger unreadable ({type(x).__name__}: {str(x)[:120]})'
            if e and not e.get('complete'): why = f"{prev} has {e.get('left')} to do"
            if why: log(f'{cc}: waiting on {prev} (B-3 order: one market complete before the next; {why})'); return {'market': cc, 'waiting_on': prev, 'why': why}
    ls = live_start(cc); ys = want_years or [y for y in years_for(cc, ls) if y not in done_years(cc)]
    if not ys: log(f'{cc}: every year from {EPOCH[:4]} is done'); return {'market': cc, 'complete': True, 'ledger': order_publish(cc, ls)}
    since = max(EPOCH, f'{min(ys)}-01-01'); until = min(f'{max(ys)}-12-31', (datetime.date.fromisoformat(ls) - datetime.timedelta(days=1)).isoformat() if ls else T0.date().isoformat())
    log(f'{cc}: backfill {line["archive"]} via {line["adapter"]} · years {ys} · window {since} → {until} (live record began {ls}) · run {RUN}')
    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw = ADAPTERS[line['adapter']](cc, line, since, until, f'{min(ys)}-{max(ys)}')
    stream = isinstance(raw, dict) and raw.get('_stream')   # SHELF-01 2026-10-27: EDGAR seals month by month from disk (every fanned-out line in one list does not fit a 4 GiB job)
    if stream: md, first = edgar_months(raw['file'], since, until); L = json.load(open(raw['listings'], encoding='utf-8'))
    facts = (get_json(cc, 'backfill/facts.json') if not LOCAL_ONLY else None) or {}
    lf = os.path.join(POND, f'{cc}-cm-kg', 'backfill', 'facts.json')
    if LOCAL_ONLY and os.path.exists(lf): facts = json.load(open(lf, encoding='utf-8'))
    if not stream: first = min((e['date'][:10] for e in raw), default=None)
    hf = min([x for x in (facts.get('history_from'), first) if x], default=None)
    out = {'market': cc, 'years': {}}; SRC = set()
    for y in sorted(ys, reverse=True):   # newest year first
        ld = os.path.join(POND, f'{cc}-cm-kg', 'backfill', str(y)); os.makedirs(ld, exist_ok=True); rp = os.path.join(ld, f'rows-{RUN}.jsonl')
        st = {'n': 0, 'bytes': 0, 'hashes': [], 'docs': set(), 'iss': set(), 'src': set()}
        batches = ((m, edgar_fan(md, m, L)) for m in sorted(x[:-7] for x in os.listdir(md) if x.startswith(f'{y}-'))) if stream else [(str(y), [e for e in raw if e['date'][:4] == str(y)])]
        with open(rp, 'wb') as f:   # rows sorted (date, exchange, ticker, url): a month batch is sorted inside, and months run in order
            for tag, evs in batches:
                rows = build_rows(cc, line, evs, y, fetched_at); del evs
                for r in rows:
                    b = (json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'); f.write(b); st['bytes'] += len(b)
                    st['hashes'].append(hashlib.sha256(canon(r)).hexdigest()); st['docs'].add(r['url']); st['iss'].add((r.get('exchange'), r.get('ticker'))); st['src'].add(r.get('source') or r.get('wire') or '')
                st['n'] += len(rows)
                if stream: log(f'{cc} {tag}: {len(rows)} rows')
                del rows
        man = sign({'dataset': 'Allooloo Datasets — backfill', 'market': cc, 'node': f'{cc}-cm-kg', 'year': y, 'window': [max(since, f'{y}-01-01'), min(until, f'{y}-12-31')],
                    'rows': st['n'], 'documents': len(st['docs']), 'issuers': len(st['iss']), 'hash_tree_root': merkle(st['hashes']), 'hash_tree': 'sha256 binary tree over the sorted sha256 of each signed row (canonical JSON)',
                    'history_from': hf, 'sources': sorted(st['src'] - {''}), 'archive': line['archive'], 'adapter': line['adapter'], 'parser_version': PARSER,
                    'run': RUN, 'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'rows_file': f'backfill/{y}/rows-{RUN}.jsonl', 'licence': 'the licence text is the CEO\'s hand (not written by BACKFILL-01)'})
        mpath = os.path.join(ld, 'manifest.json'); n = 1
        while os.path.exists(mpath): n += 1; mpath = os.path.join(ld, f'manifest-{n}.json')
        json.dump(man, open(mpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if not LOCAL_ONLY:
            with open(rp, 'rb') as f: man['rows_file'] = put_beside(cc, f'backfill/{y}/rows-{RUN}.jsonl', f, 'application/x-ndjson')
            put_beside(cc, f'backfill/{y}/manifest.json', json.dumps(man, ensure_ascii=False, indent=1).encode('utf-8'))
        SRC.update(man['sources'])
        out['years'][y] = {'rows': st['n'], 'documents': man['documents'], 'root': man['hash_tree_root'], 'bytes': st['bytes']}
        log(f'{cc} {y}: {st["n"]} rows · {man["documents"]} documents · root {man["hash_tree_root"][:16]} · history_from {hf}'); del st
    yrs = dict(facts.get('years') or {}); yrs.update({str(k): v for k, v in out['years'].items()})
    facts = {'market': cc, 'history_from': hf, 'history_from_note': f'the earliest date actually read (via {line["adapter"]}: ' + ', '.join(sorted({r for y in out["years"] for r in []} | set(SRC))) + f'); primary archive of the order: {line["archive"]}; depth declared, never assumed',
             'rows': sum(v['rows'] for v in yrs.values()), 'documents': sum(v['documents'] for v in yrs.values()), 'years': yrs, 'live_record_began': ls, 'epoch': EPOCH, 'year_in_progress': (min(int(k) for k in yrs) - 1) if yrs and min(int(k) for k in yrs) > int(EPOCH[:4]) else None, 'storage_bytes': sum(v.get('bytes', 0) for v in yrs.values()), 'spend_night': {'run': RUN, 'reader': line.get('reader'), 'reader_tokens': 0, 'reader_tokens_note': 'keyless archive reads, no engine call' if line.get('reader') == 'keyless' else 'archive key calls (no engine tokens)', 'storage_bytes_written': sum(v['bytes'] for v in out['years'].values())}, 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'run': RUN}
    os.makedirs(os.path.dirname(lf), exist_ok=True); json.dump(facts, open(lf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if not LOCAL_ONLY:
        from azure.storage.blob import ContentSettings
        store(cc).upload_blob('backfill/facts.json', json.dumps(facts, ensure_ascii=False, indent=1).encode('utf-8'), overwrite=True, content_settings=ContentSettings(content_type='application/json'))   # the one mutable file: the counts of record
        ark(cc, [f'backfill/{y}/' for y in out['years']])
        out['ledger'] = order_publish(cc, ls)
    out['facts'] = facts; return out

def ark(cc, prefixes):
    """the ark copy rail for backfill/: every object under the prefixes to the node's existing ark bucket, same key under <node>/ (put-only, same MD5 skipped)"""
    if os.environ.get('ARK_ENABLED', '1') != '1': log('ark off (ARK_ENABLED=0)'); return
    import boto3
    sys.path.insert(0, os.path.join(RAILS, 'zones-032')); import infra_policy
    node = f'{cc}-cm-kg'; bucket = os.environ.get('ARK_BUCKET') or f'allooloo-ark-{node}'; region = os.environ.get('ARK_REGION') or infra_policy.ark_region(cc)
    if os.environ.get('AWS_ACCESS_KEY_ID'): s3 = boto3.client('s3', region_name=region)
    else:
        k = open(os.path.join(r'C:\MATTHEWKEDDY\AGENT KEYS', 'aws-ark-writer.txt'), encoding='utf-8').read().split(); s3 = boto3.client('s3', region_name=region, aws_access_key_id=k[0], aws_secret_access_key=k[1])
    n = 0
    for pre in prefixes:
        for b in store(cc).list_blobs(name_starts_with=pre):
            data = store(cc).get_blob_client(b.name).download_blob().readall()
            s3.put_object(Bucket=bucket, Key=f'{node}/{b.name}', Body=data, ContentMD5=base64.b64encode(hashlib.md5(data).digest()).decode()); n += 1
    log(f'ark: {n} objects -> s3://{bucket}/{node}/backfill/ ({region})')

def verify(cc, year):
    pub = json.load(open(os.path.join(ROOT, 'CM-KG', 'NODE-SIGN', 'cmr-signing.pub.jwk.json'), encoding='utf-8'))
    if LOCAL_ONLY:
        fs = sorted(glob.glob(os.path.join(POND, f'{cc}-cm-kg', 'backfill', str(year), 'rows-*.jsonl'))); rows = [json.loads(l) for l in open(fs[-1], encoding='utf-8')]; src = fs[-1]
        man = json.load(open(os.path.join(POND, f'{cc}-cm-kg', 'backfill', str(year), 'manifest.json'), encoding='utf-8'))
    else:
        man = get_json(cc, f'backfill/{year}/manifest.json'); src = man['rows_file']
        rows = [json.loads(l) for l in store(cc).get_blob_client(src).download_blob().readall().decode('utf-8').splitlines() if l.strip()]
    r = random.SystemRandom().choice(rows); rif, gap = eco_history.rule_in_force(cc, r['date'][:10])
    res = {'market': cc, 'year': year, 'read_from': src, 'rows_in_file': len(rows), 'row': {k: r.get(k) for k in ('date', 'exchange', 'ticker', 'issuer', 'event_type', 'title', 'url', 'era', 'backfill_run_id')},
           'row_signature_verified': verify_sig(r, pub['x']), 'kid': r['signature']['kid'], 'public_key': 'CM-KG\\NODE-SIGN\\cmr-signing.pub.jwk.json (= the kid on ' + JWKS + ')',
           'rule_in_force': r.get('rule_in_force'), 'eco_history_for_date': rif, 'rule_in_force_matches_register': r.get('rule_in_force') == rif,
           'manifest_signature_verified': verify_sig(man, pub['x']), 'manifest_rows_match': man['rows'] == len(rows), 'hash_tree_root_matches': merkle([hashlib.sha256(canon(x)).hexdigest() for x in rows]) == man['hash_tree_root']}
    return res

def plan():
    pol = policy_or_stop(); order = POL['order']; out = []
    for n in roster.load():
        cc = roster.cc_of(n); l = pol[cc]
        out.append({'market': cc, 'country': n['country'], 'archive': l['archive'], 'adapter': l['adapter'], 'policy_line': True, 'wave': l['wave'], 'position': (order.index(cc) + 1) if cc in order else None, 'reader': l.get('reader'), 'pace_rps': (l.get('pace') or {}).get('rps')})
    return sorted(out, key=lambda x: (x['position'] or 99))

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == 'plan':
        for x in plan(): print(json.dumps(x, ensure_ascii=False))
    elif a[0] == 'run':
        ys = [int(y) for y in a[a.index('--years') + 1].split(',')] if '--years' in a else None
        print(json.dumps(run(a[1], ys), ensure_ascii=False, default=str)[:4000])
    elif a[0] == 'ledger':   # seed or refresh entries from the stores (laptop): python backfill.py ledger [cc ...]
        for c in (a[1:] or [c for c in POL['order'] if c in roster.codes()]): print(json.dumps(order_publish(c, live_start(c)), ensure_ascii=False))
    elif a[0] == 'verify':
        print(json.dumps(verify(a[1], int(a[2])), ensure_ascii=False, indent=1))
