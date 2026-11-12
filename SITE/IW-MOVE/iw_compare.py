r"""iw_compare.py — IW-MOVE-01 step 6: the one-cycle comparison (CEO gate: deterministic parts byte for byte; timestamps and live-page reads excluded).
Reads trial\old and trial\new (iw_trial.py snap). First pass (`scan`): for every ops_staging table, every column, the multiset of values on each side;
for every staging blob, every JSON leaf path. Prints where the sides differ, so the excluded set is chosen from what is seen, not assumed.
Usage: python -X utf8 -I iw_compare.py scan"""
import json, pathlib, sys, collections, hashlib
H = pathlib.Path(__file__).parent; T = H / 'trial'
def rows(side, t): return [json.loads(l) for l in open(T / side / 'db' / f'{t}.jsonl', encoding='utf-8') if l.strip()]
def canon(v): return json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)
def leaves(v, p=''):
    if isinstance(v, dict):
        for k in sorted(v): yield from leaves(v[k], f'{p}.{k}')
    elif isinstance(v, list):
        for i, x in enumerate(v): yield from leaves(x, f'{p}[]')
    else: yield p, v
tabs = sorted(p.stem for p in (T / 'old' / 'db').glob('*.jsonl')); print('== tables')
for t in tabs:
    o, n = rows('old', t), rows('new', t); cols = sorted({k for r in o + n for k in r}); diff = []
    for c in cols:
        a = collections.Counter(canon(r.get(c)) for r in o); b = collections.Counter(canon(r.get(c)) for r in n)
        if a != b:
            oa = list((a - b).elements()); ob = list((b - a).elements()); diff.append(f"{c}: {sum((a - b).values())} of {len(o)} values differ · old e.g. {oa[0][:110] if oa else ''} · new e.g. {ob[0][:110] if ob else ''}")
    print(f'{t}: rows {len(o)}/{len(n)} · columns {len(cols)} · differing columns {len(diff)}')
    for d in diff: print('    ', d)
print('== staging blobs')
on = {p.relative_to(T / 'old' / 'staging').as_posix(): p for p in (T / 'old' / 'staging').rglob('*') if p.is_file()}; nn = {p.relative_to(T / 'new' / 'staging').as_posix(): p for p in (T / 'new' / 'staging').rglob('*') if p.is_file()}
print('names: old', len(on), 'new', len(nn), 'only old', sorted(set(on) - set(nn))[:8], 'only new', sorted(set(nn) - set(on))[:8])
for name in sorted(set(on) & set(nn)):
    a, b = on[name].read_bytes(), nn[name].read_bytes()
    if a == b: print(f'{name}: IDENTICAL ({len(a)} bytes)'); continue
    try: ja, jb = json.loads(a), json.loads(b)
    except Exception:
        la, lb = a.decode('utf-8', 'replace').splitlines(), b.decode('utf-8', 'replace').splitlines(); d = [(x, y) for x, y in zip(la, lb) if x != y]
        print(f'{name}: differs · lines {len(la)}/{len(lb)} · differing lines {len(d)} · e.g. {d[0][0][:150] if d else ""} || {d[0][1][:150] if d else ""}'); continue
    A = collections.Counter((p, canon(v)) for p, v in leaves(ja)); B = collections.Counter((p, canon(v)) for p, v in leaves(jb)); paths = collections.Counter(p for p, _ in (A - B).keys()) + collections.Counter(p for p, _ in (B - A).keys())
    ex = {}
    for (p, v) in (A - B).keys(): ex.setdefault(p, [v[:70], ''])
    for (p, v) in (B - A).keys(): ex.setdefault(p, ['', ''])[1] = v[:70]
    print(f'{name}: differs at {len(paths)} paths of {len({p for p, _ in A})}')
    for p in sorted(paths)[:14]: print('     ', p, '· old', ex[p][0], '· new', ex[p][1])
