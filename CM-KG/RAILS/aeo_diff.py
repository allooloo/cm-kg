r"""START_ME_UP_5 §7.3/§7.4 — diff two scan folders at check level and print the per-surface before/after table (markdown).
Usage: python aeo_diff.py <before-label> <after-label>   (labels as given to aeo_scan.py; folders AZURE\aeo-scan-<date>-<label>)"""
import json, sys, glob, os
sys.stdout.reconfigure(encoding='utf-8')
AZ = r'C:\ALLOOLOO\AZURE'
def load(label):
    d = sorted(glob.glob(os.path.join(AZ, f'aeo-scan-*-{label}')))[-1]; out = {}
    for f in glob.glob(os.path.join(d, '*.json')):
        j = json.load(open(f, encoding='utf-8')); h = os.path.basename(f)[:-5]
        st = {}
        for cat, c in j.get('checks', {}).items():
            for k, v in c.items(): st[k] = v['status']
        out[h] = {'level': j.get('level'), 'commerce': j.get('isCommerce'), 'st': st, 'err': j.get('error')}
    return d, out
db, B = load(sys.argv[1]); da, A = load(sys.argv[2])
cnt = lambda st, s: sum(1 for x in st.values() if x == s)
print(f'before: {db}\nafter:  {da}\n')
print('| surface | before (pass · neutral · fail) | after (pass · neutral · fail) | level | commerce | checks that moved |'); print('|---|---|---|---|---|---|')
allb = set(); alla = set()
for h in sorted(B):
    b, a = B[h], A.get(h, {'st': {}, 'level': '?', 'commerce': '?'})
    allb |= set(b['st']); alla |= set(a['st'])
    moved = [f"{k} {b['st'].get(k, '—')}→{a['st'].get(k, '—')}" for k in sorted(set(b['st']) | set(a['st'])) if b['st'].get(k) != a['st'].get(k)]
    print(f"| {h} | {cnt(b['st'], 'pass')} · {cnt(b['st'], 'neutral')} · {cnt(b['st'], 'fail')} | **{cnt(a['st'], 'pass')} · {cnt(a['st'], 'neutral')} · {cnt(a['st'], 'fail')}** | L{a['level']} | {a['commerce']} | {', '.join(moved) or 'none'} |")
print(f"\ncheck names before: {len(allb)} · after: {len(alla)} · new: {sorted(alla - allb) or 'none'} · gone: {sorted(allb - alla) or 'none'}")
fails = {}
for h, a in A.items():
    for k, v in a['st'].items():
        if v == 'fail': fails.setdefault(k, []).append(h)
print('remaining fails:', {k: len(v) for k, v in fails.items()} or 'none')
for k, v in fails.items(): print(f'  {k}: {", ".join(sorted(v))}')
