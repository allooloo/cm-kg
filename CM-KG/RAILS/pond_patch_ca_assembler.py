r"""One-off patch (2026-09-11): make the Canada Width 1 assembler read every pond drop of the rail (pond rule 3) instead of the working folder alone,
and merge the last versioned event set. Idempotent."""
import re, os
fn = r'C:\ALLOOLOO\CM-KG\RAILS\ca-width1\assemble_disclosure.py'
s = open(fn, encoding='utf-8').read()
if 'pond.drops(' in s: print('already patched'); raise SystemExit
old = """def load(fn):
    if not os.path.exists(fn): return []
    out = []
    for line in open(fn, encoding='utf-8'):
        try: out.append(json.loads(line))
        except Exception: pass
    return out"""
new = """import pond
NODE = 'ca-cm-kg'
def load(fn):
    \"\"\"pond rule 3: every drop of this rail (POND\\\\ca-cm-kg\\\\width1\\\\<date>\\\\) plus the working folder; the dedupe key keeps one copy per event\"\"\"
    out = []; seen_paths = set()
    paths = [p for d, p in pond.drops(NODE, 'width1')] + (['raw'] if os.path.isdir('raw') else [])
    for p in paths:
        f = os.path.join(p, os.path.basename(fn)); rp = os.path.realpath(f)
        if not os.path.exists(f) or rp in seen_paths: continue
        seen_paths.add(rp)
        for line in open(f, encoding='utf-8'):
            try: out.append(json.loads(line))
            except Exception: pass
    return out"""
assert old in s, 'load() not found'
s = s.replace(old, new, 1)
old2 = "for e in load('raw/grok_live.jsonl'): events.append(e)   # 48-hour live layer (read by Grok (live)), present on daily runs only\n"
new2 = old2 + """# pond rule 3: the last versioned event set is merged too (history is never dropped)
_prev = pond.latest_assembled(NODE, 'ca-events.jsonl') or (OUT_J if os.path.exists(OUT_J) else None)
if _prev:
    _n = 0
    for line in open(_prev, encoding='utf-8'):
        try:
            e = json.loads(line); e.pop('as_of', None); e.pop('node', None); e.pop('width', None); events.append(e); _n += 1
        except Exception: pass
    print('merged prior assembled events', _n, 'from', _prev, flush=True)
"""
assert old2 in s, 'grok line not found'
s = s.replace(old2, new2, 1)
open(fn, 'w', encoding='utf-8').write(s); print('patched', fn)
