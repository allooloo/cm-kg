r"""DOORS-05 (2026-10-26) — pond._new_dir numbers above the day's highest drop. Before: the first free name, so a job that syncs only the newest drop
(e.g. assembled/2026-10-26-2) wrote the bare 2026-10-26, which sorts below -2, and the node job refused the run ("no new assembled drop").
Patches every copy of pond.py under RAILS that carries the old function verbatim; .pre copy beside each. Usage: python -X utf8 -I fix_pond_new_dir.py [--dry]"""
import os, sys, glob, shutil
OLD = """def _new_dir(base):
    d = os.path.join(base, _today()); n = 1
    while os.path.exists(d):
        n += 1; d = os.path.join(base, f'{_today()}-{n}')
    os.makedirs(d); return d"""
NEW = """def _new_dir(base):
    # DOORS-05 (2026-10-26): number above the day's highest drop present, not the first free name — a job holds only the newest drop of the day,
    # and a bare <date> written after <date>-2 sorts below it (the node job then sees no new drop)
    t = _today(); os.makedirs(base, exist_ok=True)
    ns = [int(x[len(t) + 1:] or 1) if x != t else 1 for x in os.listdir(base) if x == t or (x.startswith(t + '-') and x[len(t) + 1:].isdigit())]
    d = os.path.join(base, t if not ns else f'{t}-{max(ns) + 1}')
    os.makedirs(d); return d"""
n = 0; other = []
for p in glob.glob(r'C:\ALLOOLOO\CM-KG\RAILS\**\pond.py', recursive=True):
    if '.pre' in p: continue
    s = open(p, encoding='utf-8').read()
    if OLD not in s: other.append(p); continue
    if '--dry' not in sys.argv:
        shutil.copy2(p, p + '.pre-pondnum-20261026'); open(p, 'w', encoding='utf-8', newline='').write(s.replace(OLD, NEW))
    n += 1
print('patched' if '--dry' not in sys.argv else 'would patch', n, '| not matching:', other)
