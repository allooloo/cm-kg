r"""iw_compare2.py — IW-MOVE-01 step 6: the one-cycle comparison of record (CEO gate: deterministic parts byte for byte; timestamps and live-page reads
excluded). Reads trial\old and trial\new. What is set aside, and why, is fixed here and printed with the result:
  timestamps     read_at, last_read_at, started_at/_utc, finished_at/_utc, read times inside logs, as-of.txt (a timestamp and nothing else)
  the side's own name  execution name, image label, storage account name, the door address each side read, the edge's ray id / nonce (a live read of
                 each side's own door), the serial row id each database hands out
  database statistic   the planner's row ESTIMATE (pg_stat n_live_tup) — the COUNT beside it is compared
Everything else is compared exactly: every row of every ops_staging table as a multiset, every staging blob. What still differs is listed in full under
`residue` — nothing is waved through silently. Writes trial\comparison.json. Usage: python -X utf8 -I iw_compare2.py"""
import collections, json, pathlib, re
H = pathlib.Path(__file__).parent; T = H / 'trial'
DROP = {'read_at', 'last_read_at', 'started_at', 'finished_at', 'started_utc', 'finished_utc', 'execution', 'image', 'store', 'estimate', 'cf_ray', 'x_gsc_nonce', 'x_gsc_timestamp'}
def scrub(v, top=False, edge=False):
    if isinstance(v, dict): return {k: scrub(x, edge=(k == 'edge')) for k, x in v.items() if k not in DROP and not (top and k == 'id') and not (edge and k == 'url')}
    if isinstance(v, list): return [scrub(x) for x in v]
    return v
canon = lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)
def norm_text(s):
    s = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)?', '<time>', s); s = re.sub(r'(?m)^\d{2}:\d{2}:\d{2} ', '<t> ', s); s = re.sub(r'\b(amn|iw)-([a-z]+)-rail-[a-z0-9]{7}\b', r'<exec \2>', s)
    s = s.replace('allooloostgiwfrc', '<store>').replace('stgamnfrc', '<store>').replace('iwmove01-', ''); s = re.sub(r'https://(iw-door\.salmonpebble-af371cd2\.francecentral\.azurecontainerapps\.io|mcp\.a2a-amn\.ai|a2a-amn\.ai|agentmarketnews\.ai)', '<door>', s)
    return re.sub(r'\b\d+(\.\d+)? ?(s|ms|sec|seconds)\b', '<dur>', s)
out = {'set_aside': ['timestamps', "the side's own name (execution, image label, storage account, door address, edge ray/nonce, serial row id)", "the planner's row estimate (the count is compared)"], 'tables': {}, 'blobs': {}, 'residue': []}
for p in sorted((T / 'old' / 'db').glob('*.jsonl')):
    t = p.stem; R = {}
    for s in ('old', 'new'): R[s] = collections.Counter(canon(scrub(json.loads(l), top=True)) for l in open(T / s / 'db' / p.name, encoding='utf-8') if l.strip())
    a = R['old'] - R['new']; b = R['new'] - R['old']; out['tables'][t] = {'rows_old': sum(R['old'].values()), 'rows_new': sum(R['new'].values()), 'identical_rows': sum((R['old'] & R['new']).values()), 'differ_old': sum(a.values()), 'differ_new': sum(b.values())}
    if a or b: out['residue'].append({'table': t, 'only_old': [json.loads(x) for x in list(a.elements())[:6]], 'only_new': [json.loads(x) for x in list(b.elements())[:6]]})
on = {p.relative_to(T / 'old' / 'staging').as_posix(): p for p in (T / 'old' / 'staging').rglob('*') if p.is_file()}; nn = {p.relative_to(T / 'new' / 'staging').as_posix(): p for p in (T / 'new' / 'staging').rglob('*') if p.is_file()}
out['blob_names'] = {'old': len(on), 'new': len(nn), 'only_old': sorted(set(on) - set(nn)), 'only_new': sorted(set(nn) - set(on))}
def leaves(v, p=''):
    if isinstance(v, dict):
        for k in sorted(v): yield from leaves(v[k], f'{p}.{k}')
    elif isinstance(v, list):
        for x in v: yield from leaves(x, f'{p}[]')
    else: yield p, v
for name in sorted(set(on) & set(nn)):
    a, b = on[name].read_bytes(), nn[name].read_bytes()
    if a == b: out['blobs'][name] = 'identical bytes'; continue
    if name.endswith('.json'):
        ja, jb = scrub(json.loads(a)), scrub(json.loads(b))
        if canon(ja) == canon(jb): out['blobs'][name] = 'identical after the set-aside'; continue
        A = collections.Counter((p, canon(v)) for p, v in leaves(ja)); B = collections.Counter((p, canon(v)) for p, v in leaves(jb)); d = {}
        for (p, v) in (A - B): d.setdefault(p, {})['old'] = v[:120]
        for (p, v) in (B - A): d.setdefault(p, {})['new'] = v[:120]
        out['blobs'][name] = f'differs at {len(d)} values'; out['residue'].append({'blob': name, 'values': d})
    else:
        ta, tb = norm_text(a.decode('utf-8', 'replace')), norm_text(b.decode('utf-8', 'replace'))
        if ta == tb: out['blobs'][name] = 'identical after the set-aside'; continue
        la, lb = ta.splitlines(), tb.splitlines(); d = [{'old': x[:260], 'new': y[:260]} for x, y in zip(la, lb) if x != y]
        out['blobs'][name] = f'differs in {len(d)} of {len(la)}/{len(lb)} lines'; out['residue'].append({'blob': name, 'lines': d[:8]})
tb = out['tables']; out['summary'] = {'tables': len(tb), 'tables_identical': sum(1 for v in tb.values() if not v['differ_old'] and not v['differ_new']), 'rows_old': sum(v['rows_old'] for v in tb.values()), 'rows_identical': sum(v['identical_rows'] for v in tb.values()),
    'blobs': len(out['blobs']), 'blobs_identical_bytes': sum(v == 'identical bytes' for v in out['blobs'].values()), 'blobs_identical_after_set_aside': sum(v == 'identical after the set-aside' for v in out['blobs'].values()), 'residue_items': len(out['residue'])}
json.dump(out, open(T / 'comparison.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(out['summary'], indent=1)); print(json.dumps({k: v for k, v in tb.items() if v['differ_old'] or v['differ_new']}, indent=1)); print(json.dumps(out['residue'], indent=1, ensure_ascii=False)[:6000])
