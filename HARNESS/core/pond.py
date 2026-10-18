"""pond.py — dated, immutable drops for every estate (the Allooloo pond rule of 2026-09-11, the agent-bev pond of AB-006, generalised).
Layout: <pond_root>\\<node>\\<source>\\<yyyy-mm-dd>[-n]\\ — never overwritten, never deleted; a re-run is a new drop. Assemblers read only from drops.
The harness never deletes a drop and never edits one. Scratch copies for dry runs live under C:\\COMPOUND\\HARNESS\\dryrun\\, never in an estate's pond."""
import datetime, json, os, re, shutil


def _today(): return datetime.date.today().isoformat()


def _new_dir(base):
    d = os.path.join(base, _today()); n = 1
    while os.path.exists(d): n += 1; d = os.path.join(base, f"{_today()}-{n}")
    os.makedirs(d); return d


def drops(pond_root, node, source):
    base = os.path.join(pond_root, node, source)
    if not os.path.isdir(base): return []
    def k(x):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})(?:-(\d+))?$", x); return (m.group(1), int(m.group(2) or 1)) if m else (x, 0)
    return [(x, os.path.join(base, x)) for x in sorted(os.listdir(base), key=k) if os.path.isdir(os.path.join(base, x))]


def latest(pond_root, node, source, fn=None):
    for date, p in reversed(drops(pond_root, node, source)):
        if fn is None or os.path.exists(os.path.join(p, fn)): return (date, p if fn is None else os.path.join(p, fn))
    return (None, None)


def open_drop(pond_root, node, source):
    return _new_dir(os.path.join(pond_root, node, source))


def read_jsonl(path):
    if not path or not os.path.exists(path): return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: yield json.loads(line)
        except Exception: continue


def scratch_copy(src_dir, scratch_root, label):
    """Copy a store folder into the dry-run scratch (never the live store). Returns the scratch path."""
    dst = os.path.join(scratch_root, label)
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(src_dir, dst)
    return dst
