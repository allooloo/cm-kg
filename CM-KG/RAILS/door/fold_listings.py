r"""fold_listings.py — DOORS-03 (CEO order 2026-10-26): one record per listed company, one listing line per exchange and segment.
An ISIN that resolves to more than one record on a node is folded when the records are listing lines of the same issuer:
  derivative     a Eurex product whose identity.underlying_cmr is the issuer record (de)            -> listing line, type derivative
  dual-counter   an HKEX RMB counter (8xxxx) of a HKD counter, names alike once the trailing R is set aside -> listing line, type dual-counter
  same issuer    the same legal name once case, punctuation, legal-suffix spelling and a trailing class or currency tag are set aside
                 (never on jp: two TSE codes are two companies, so a shared ISIN there is a fill error) -> listing line, type listing / line
Anything else is left as it is and named (hand item): two issuers under one ISIN is a data error to fix at the source, never by folding.
The fold: the primary record (main venue, then the most events, then the shortest code) gains `listings` — one line per listing, each carrying the folded
record's whole identity block (every field's source, reader, state and read date kept), its as_of, version, kind, events URL and event count. The ISIN, and
every ticker, CMR, alias and name key of a folded line, resolve to the primary; the folded record leaves `keys`; its file is served as the primary record.
facts records (and records_by_exchange) drop by the lines folded. Idempotent: a primary that already carries a line is not folded twice.
  python fold_listings.py <cc> --data [<door data dir>]   nightly, after enrich_node.py and before door_gate.py (build dir layout records/<node>/<EX>/<code>.json)
  python fold_listings.py <cc> --store [--dry]            on the node's regional store (door/…): the live fold of 2026-10-26 and the us job after its gate.
                                                          The prior record files are copied first to door-folded/<UTC date>/<EX>/<code>.pre.json (pond container).
Writes fold-<cc>-<UTC stamp>.json beside (plan: folded groups, hand items, counts)."""
import os, sys, json, re, datetime, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO')
RANK = ['XETRA', 'TSX', 'TSXV', 'CBOE-CANADA', 'CSE', 'LSE', 'AIM', 'AQSE', 'NYSE', 'NASDAQ', 'NYSE-AMERICAN', 'CBOE', 'XPAR', 'ALXP', 'XMLI', 'XAMS', 'ALXA', 'SGX', 'SGX-CATALIST', 'HKEX', 'HKEX-GEM', 'HKEX-REIT', 'EUREX']
SUFFIX = {'ltd': 'limited', 'co': 'company', 'corp': 'corporation', 'inc': 'incorporated', 'hldgs': 'holdings', 'grp': 'group'}
TAIL = re.compile(r'(\s+(class [a-z]|cl [a-z]|usd|sgd|eur|gbp|hkd|cad|units?|etf units))+$')
v = lambda r, f: ((r.get('identity') or {}).get(f) or {}).get('value')
def norm(name, hk_rmb=False):
    s = str(name or '').lower().replace('&', ' and ').replace('®', ''); s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    if hk_rmb: s = re.sub(r'r$', '', s)                     # BABA-WR -> baba w ; TENCENT-R -> tencent
    s = ' '.join(SUFFIX.get(w, w) for w in s.split()); return TAIL.sub('', s).strip()
def code(k): return k.split('/', 2)[2]
def exch(k): return k.split('/')[1]
def classify(cc, keys, recs):
    eu = [k for k in keys if exch(k) == 'EUREX']; non = [k for k in keys if k not in eu]
    if eu and len(non) == 1 and all(v(recs[k], 'underlying_cmr') == non[0] for k in eu): return 'derivative', non[0], {k: 'derivative' for k in eu}
    if cc == 'hk' and len(keys) == 2:
        a, b = sorted(keys, key=lambda k: (code(k).startswith('8'), code(k)))
        if code(b).startswith('8') and not code(a).startswith('8') and norm(v(recs[a], 'name')).replace(' ', '') == norm(v(recs[b], 'name'), hk_rmb=True).replace(' ', ''): return 'dual-counter', a, {b: 'dual-counter'}
    if cc == 'jp': return 'different', None, {}
    names = {norm(v(recs[k], 'name')) for k in keys}
    if len(names) == 1 and '' not in names:
        nm = list(names)[0].replace(' ', ''); cs = [re.sub(r'[^A-Z0-9]', '', code(k).upper()) for k in keys]
        def rank(k):   # the primary line: main venue · a code the others extend · a code that starts the issuer's name · no preferred/note/unit/warrant tail · most events · shortest
            c0 = re.sub(r'[^A-Z0-9]', '', code(k).upper())
            return (RANK.index(exch(k)) if exch(k) in RANK else 99, 0 if all(x.startswith(c0) for x in cs) else 1, 0 if nm.startswith(c0.lower()) else 1,
                    1 if re.search(r'[PLUWZ]$|-P[A-Z]?$', code(k).upper()) and len(c0) > 3 else 0, -int(recs[k].get('event_count') or 0), len(code(k)), code(k))
        p = sorted(keys, key=rank)[0]
        return 'same issuer', p, {k: ('listing' if exch(k) != exch(p) else 'line') for k in keys if k != p}
    return 'different', None, {}
def line_of(k, r, typ, primary_key):
    return {'cmr': k, 'exchange': exch(k), 'code': code(k), 'type': typ, 'name': v(r, 'name'), 'as_of': r.get('as_of'), 'version': r.get('version'), 'kind': r.get('kind'),
            'events_url': r.get('events_url'), 'event_count': r.get('event_count'), 'identity': r.get('identity'), 'aliases': r.get('aliases') or [], 'halt': r.get('halt'),
            'folded_into': primary_key if k != primary_key else None}
# DOORS-04 (2026-10-26): ISIN corrections of record — RAILS\door\isin_corrections.json, {node: {cmr: {isin|null, was, source_url, read_by, read_at, note}}}.
# Each night the record gets the ISIN read at its register of record (state confirmed), or a blank with the reason when the register proves the old value
# belongs to another issuer but prints none for this one; the replaced value rides in `corrected_from`. The index follows the record.
CORR = os.path.join(HERE, 'isin_corrections.json')
LEI_KEYS = None; WORKERS = 1   # None = every record of the node; a list = only those (a targeted live run); False = skip the LEI rule (--no-lei)
def correct(node, index, get, put, plan):
    if not os.path.exists(CORR): return
    C = (json.load(open(CORR, encoding='utf-8')).get(node) or {})
    for key, c in C.items():
        r = get(key)
        if r is None: plan['corrected'].append({'cmr': key, 'state': 'record not readable'}); continue
        idn = r.setdefault('identity', {}); cur = (idn.get('isin') or {}).get('value'); new = c.get('isin')
        if cur == new and (idn.get('isin') or {}).get('read_at') == c.get('read_at'): continue
        idn['isin'] = {'value': new, 'source_url': c['source_url'], 'read_by': c['read_by'], 'read_at': c['read_at'], 'state': c.get('state') or ('confirmed' if new else None),   # DOORS-05: a manager-published value is filled
                       'corrected_from': {'value': c.get('was') or cur, 'why': c.get('note')}} | ({} if new else {'reason': c.get('note')})
        put(key, r)
        isn = index.setdefault('isin', {})
        for old in {cur, c.get('was')} - {None, new}:
            if isinstance(isn.get(old), list) and key in isn[old]:
                isn[old] = [k for k in isn[old] if k != key]
                if not isn[old]: isn.pop(old)
        if new: isn.setdefault(new, [])
        if new and key not in isn[new]: isn[new].append(key)
        plan['corrected'].append({'cmr': key, 'from': cur, 'to': new})
# ISIN disambiguation (2026-10-27): parents of record — RAILS\door\isin_parents.json, {node: {cmr: {cmr, relation, isin, basis, rule, set_at}}}, written by
# RAILS\isin-dis\decide.py. An ISIN resolves to the primary listing record; a secondary-venue, depositary or derivative record keeps its own identifiers,
# carries `parent` and leaves the ISIN index (store_index.py keeps it out of the store's index too). Applied each night before the fold.
PARENTS = os.path.join(HERE, 'isin_parents.json')
def reparent(node, index, get, put, plan):
    plan['reparented'] = []
    if not os.path.exists(PARENTS): return
    P = (json.load(open(PARENTS, encoding='utf-8')).get(node) or {})
    for key, p in P.items():
        r = get(key)
        if r is None: continue   # not on tonight's build
        if p.get('relation') == 'primary':
            # DOORS-06 tail (2026-10-27): the primary of a cross-node dual listing carries the other venue's listing line (read from that node's record
            # at decision time; its source and read date ride on the line). Its own line goes first, as the fold writes it.
            L = list(r.get('listings') or []) or [line_of(key, r, 'primary', key)]; have = {x['cmr'] for x in L}
            for ln in p.get('lines') or []:
                if ln['cmr'] not in have: L.append(ln)
            if L != r.get('listings'):
                r['listings'] = L; r['listing_rule'] = r.get('listing_rule') or 'one record per listed company; one listing line per exchange and segment (DOORS-03, 2026-10-26; cross-node lines DOORS-06 tail, 2026-10-27)'; put(key, r)
            plan['reparented'].append({'cmr': key, 'relation': 'primary', 'lines': [x['cmr'] for x in p.get('lines') or []]}); continue
        if r.get('parent') != p: r['parent'] = dict(r.get('parent') or {}, **p); put(key, r)
        if p.get('relation') == 'listing-line':   # DOORS-06 tail: a listing line of a primary on another node — not a record of this node (facts drop by one)
            plan['lines_folded'] += 1; ex = key.split('/')[1]; plan['by_exchange'][ex] = plan['by_exchange'].get(ex, 0) + 1
            if 'keys' in index: index['keys'] = [k for k in index['keys'] if k != key]
            for kind in ('name', 'alias'):
                for ident, ks in list((index.get(kind) or {}).items()):
                    if isinstance(ks, list) and key in ks:
                        ks2 = [k for k in ks if k != key]
                        if ks2: index[kind][ident] = ks2
                        else: index[kind].pop(ident)
        for kind, i in (('isin', p.get('isin')), ('lei', ((r.get('identity') or {}).get('lei') or {}).get('value'))):   # DOORS-06: the LEI follows the ISIN rule
            m = index.get(kind) or {}; i = str(i).upper() if i else None
            if i and isinstance(m.get(i), list) and key in m[i]:
                m[i] = [k for k in m[i] if k != key]
                if not m[i]: m.pop(i)
        plan['reparented'].append({'cmr': key, 'parent': p.get('cmr'), 'relation': p.get('relation')})
def fold(cc, index, get, put, stamp):
    node = f'{cc}-cm-kg'; plan = {'node': node, 'at': stamp, 'folded': [], 'hand': [], 'lines_folded': 0, 'by_exchange': {}, 'corrected': []}
    correct(node, index, get, put, plan)   # DOORS-04: ISINs re-read at the register of record go in first, so the fold sees the corrected index
    reparent(node, index, get, put, plan)  # ISIN disambiguation (2026-10-27): secondary-venue / derivative records leave the ISIN index before the fold looks
    if LEI_KEYS is not False:   # DOORS-05: the LEI by ISIN lookup first (lei_rule.py), on the corrected ISINs, before the fold copies identities into listing lines
        import lei_rule; lei_rule.apply(node, index, LEI_KEYS or [k for k in index.get('keys', []) if k.startswith(node + '/')], get, put, plan, workers=WORKERS)
    dups = {i: [k for k in ks if k.startswith(node + '/')] for i, ks in (index.get('isin') or {}).items()}
    dups = {i: ks for i, ks in dups.items() if len(ks) > 1}
    remap = {}
    for isin, ks in sorted(dups.items()):
        recs = {k: get(k) for k in ks}
        if any(r is None for r in recs.values()): plan['hand'].append({'isin': isin, 'keys': ks, 'why': 'a record file was not readable'}); continue
        cls, p, lines = classify(cc, ks, recs)
        if cls == 'different':
            plan['hand'].append({'isin': isin, 'keys': ks, 'names': {k: v(recs[k], 'name') for k in ks}, 'leis': {k: v(recs[k], 'lei') for k in ks}, 'why': 'two or more issuers under one ISIN (a fill error at the source)'}); continue
        pr = dict(recs[p]); have = {x['cmr'] for x in pr.get('listings') or []}
        L = list(pr.get('listings') or []) or [line_of(p, recs[p], 'primary', p)]
        for k, typ in lines.items():
            if k not in have: L.append(line_of(k, recs[k], typ, p))
            remap[k] = p; plan['by_exchange'][exch(k)] = plan['by_exchange'].get(exch(k), 0) + 1
        pr['listings'] = L; pr['listing_rule'] = 'one record per listed company; one listing line per exchange and segment (DOORS-03, 2026-10-26); every line keeps its fields with source and read date'
        put(p, pr)
        for k in lines: put(k, pr)          # the folded line's own address serves the one record
        plan['folded'].append({'isin': isin, 'class': cls, 'primary': p, 'lines': lines}); plan['lines_folded'] += len(lines)
    for kind, m in index.items():
        if kind == 'keys' or not isinstance(m, dict): continue
        for ident, ks in list(m.items()):
            if isinstance(ks, list) and any(k in remap for k in ks):
                nk = []
                for k in ks:
                    k2 = remap.get(k, k)
                    if k2 not in nk: nk.append(k2)
                m[ident] = nk
    if 'keys' in index: index['keys'] = [k for k in index['keys'] if k not in remap]
    return plan
def fix_facts(facts, node, plan):
    n = (facts.get('nodes') or {}).get(node)
    if not n or not plan['lines_folded']: return
    n['records'] = int(n.get('records') or 0) - plan['lines_folded']
    for ex, c in plan['by_exchange'].items():
        if isinstance(n.get('records_by_exchange'), dict) and ex in n['records_by_exchange']: n['records_by_exchange'][ex] -= c
    n['folded_listing_lines'] = int(n.get('folded_listing_lines') or 0) + plan['lines_folded']
    if 'records' in facts and isinstance(facts['records'], int): facts['records'] -= plan['lines_folded']
def slug(t): return re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
def main():
    cc = sys.argv[1]; node = f'{cc}-cm-kg'; stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ'); dry = '--dry' in sys.argv
    global LEI_KEYS, WORKERS
    if '--no-lei' in sys.argv: LEI_KEYS = False
    lk = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--lei-keys=')), None)
    if lk: LEI_KEYS = json.load(open(lk, encoding='utf-8'))
    if '--store' in sys.argv: WORKERS = 16
    if '--store' in sys.argv:
        from azure.storage.blob import BlobServiceClient, ContentSettings
        os.environ.setdefault('AZURE_CONFIG_DIR', os.path.join(ROOT, '.azure'))
        nodes = json.load(open(os.path.join(ROOT, 'CM-KG', 'DOOR', 'apex', 'static', 'nodes.json'), encoding='utf-8'))
        st = [x for x in nodes if x['node'] == node][0]['region']['store']; sa = f'allooloocmkg{cc}pond'
        key = os.environ.get('STORE_KEY') or (os.environ.get('STORAGE_KEY') if os.environ.get('STORAGE_ACCOUNT') == sa else None) or subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-g', f'allooloo-cmkg-{st}', '-n', sa, '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=(os.name == 'nt')).stdout.strip()
        c = BlobServiceClient(f'https://{sa}.blob.core.windows.net', credential=key).get_container_client(os.environ.get('STORAGE_CONTAINER', 'pond'))
        bj = lambda n: json.loads(c.download_blob(n).readall())
        index, facts = bj('door/index.json'), bj('door/facts.json'); day = stamp[:10]; saved = set()
        writes = {}
        def get(k):
            if k in writes: return json.loads(json.dumps(writes[k]))   # a record corrected earlier in this run
            try: return bj(f'door/records/{exch(k)}/{slug(code(k))}.json')
            except Exception: return None
        def put(k, rec): writes[k] = rec
        plan = fold(cc, index, get, put, stamp); fix_facts(facts, node, plan)
        if not dry:
            for k in writes:   # the prior file first, dated, in the pond (nothing deleted)
                n = f'door/records/{exch(k)}/{slug(code(k))}.json'; c.upload_blob(f'door-folded/{day}/{exch(k)}/{slug(code(k))}.pre.json', c.download_blob(n).readall(), overwrite=True)
            for k, rec in writes.items(): c.upload_blob(f'door/records/{exch(k)}/{slug(code(k))}.json', json.dumps(rec, ensure_ascii=False, separators=(',', ':')).encode(), overwrite=True, content_settings=ContentSettings(content_type='application/json'))
            for n0 in ('door/index.json', 'door/facts.json'): c.upload_blob(f'door-folded/{day}/{n0.split("/")[1].replace(".json", ".pre.json")}', c.download_blob(n0).readall(), overwrite=True)
            c.upload_blob('door/index.json', json.dumps(index, separators=(',', ':')).encode(), overwrite=True, content_settings=ContentSettings(content_type='application/json'))
            c.upload_blob('door/facts.json', json.dumps(facts, indent=1).encode(), overwrite=True, content_settings=ContentSettings(content_type='application/json'))
            c.upload_blob(f'door-folded/{day}/fold-plan.json', json.dumps(plan, ensure_ascii=False, indent=1).encode(), overwrite=True)
    else:
        args = [a for a in sys.argv[2:] if not a.startswith('--')]; data = args[0] if args else os.path.join(ROOT, 'CM-KG', 'DOOR', 'data')
        ip, fp = os.path.join(data, 'index.json'), os.path.join(data, 'facts.json'); index = json.load(open(ip, encoding='utf-8')); facts = json.load(open(fp, encoding='utf-8'))
        path = lambda k: os.path.join(data, 'records', node, exch(k), slug(code(k)) + '.json')
        def get(k):
            try: return json.load(open(path(k), encoding='utf-8'))
            except Exception: return None
        def put(k, rec):
            if not dry: json.dump(rec, open(path(k), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        plan = fold(cc, index, get, put, stamp); fix_facts(facts, node, plan)
        if not dry: json.dump(index, open(ip, 'w', encoding='utf-8'), separators=(',', ':')); json.dump(facts, open(fp, 'w', encoding='utf-8'), indent=1)
    out = os.path.join(HERE, f'fold-{cc}-{stamp}.json'); json.dump(plan, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"{node} fold{' (dry)' if dry else ''}: {len(plan['corrected'])} ISIN corrections applied, {len(plan.get('reparented') or [])} records re-parented,LEI rule {(plan.get('lei') or {}).get('counts')} changed {(plan.get('lei') or {}).get('changed')}, {len(plan['folded'])} ISINs folded, {plan['lines_folded']} listing lines, {len(plan['hand'])} hand items -> {out}")
    return 0
if __name__ == '__main__': sys.exit(main())
