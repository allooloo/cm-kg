r"""The pond (standing rule, CEO, 2026-09-11) — one copy per rails folder (never a shared src; copy this file beside the workers that use it).
Layout: C:\ALLOOLOO\CM-KG\POND\<node>\<source>\<yyyy-mm-dd>[-n]\   — one dated, immutable drop per harvest run. Never overwritten, never deleted;
a re-run is a new drop. Assemblers, Fill, Confirm and the door loader read only from drops and write versioned outputs (POND\<node>\assembled\<date>\,
mirrored to the canonical CM-KG\ISSUERS and CM-KG\DISCLOSURE paths). One lock file per node while a build order is in flight
(POND\<node>\.lock); the scheduled sweep skips when the lock exists.

  open_drop(node, source)      -> path of the drop a worker writes into. A drop stays 'open' (marker .open) for the run so resume-safe workers can
                                  append; close_drop() removes the marker and the drop is immutable from then on. A new run after close = a new drop.
  drops(node, source)          -> [(date, path)] every drop, oldest first
  latest(node, source, fn)     -> path of fn in the newest drop that holds it, or None
  read_jsonl_all(node, source, fn, key=None) -> rows from every drop; with key: newest drop wins per key (identity workers); without: union (events)
  assembled(node)              -> a new dated output folder POND\<node>\assembled\<date>[-n]\ (versioned outputs)
  lock(node, order) / unlock(node) / locked(node)
"""
import re, os, json, datetime, shutil
POND = r'C:\ALLOOLOO\CM-KG\POND'
def _today(): return datetime.date.today().isoformat()
def _new_dir(base):
    d = os.path.join(base, _today()); n = 1
    while os.path.exists(d):
        n += 1; d = os.path.join(base, f'{_today()}-{n}')
    os.makedirs(d); return d
def drops(node, source):
    base = os.path.join(POND, node, source)
    if not os.path.isdir(base): return []
    def _k(x):
        m = re.match(r'^(\d{4}-\d{2}-\d{2})(?:-(\d+))?$', x); return (m.group(1), int(m.group(2) or 1)) if m else (x, 0)
    out = [(x, os.path.join(base, x)) for x in sorted(os.listdir(base), key=_k) if os.path.isdir(os.path.join(base, x))]
    return out
def open_drop(node, source):
    """the current open drop for this worker (resume within a run), else a new dated drop"""
    env = os.environ.get('POND_DROP_' + source.upper().replace('-', '_'))
    if env and os.path.isdir(env): return env
    for date, p in reversed(drops(node, source)):
        if os.path.exists(os.path.join(p, '.open')): return p
    d = _new_dir(os.path.join(POND, node, source)); open(os.path.join(d, '.open'), 'w').write(_today() + '\n'); return d
def close_drop(node, source):
    for date, p in drops(node, source):
        m = os.path.join(p, '.open')
        if os.path.exists(m): os.remove(m)
def latest(node, source, fn):
    for date, p in reversed(drops(node, source)):
        if os.path.exists(os.path.join(p, fn)): return os.path.join(p, fn)
    return None
def read_jsonl_all(node, source, fn, key=None):
    rows = [] if key is None else {}
    for date, p in drops(node, source):
        f = os.path.join(p, fn)
        if not os.path.exists(f): continue
        for line in open(f, encoding='utf-8'):
            try: d = json.loads(line)
            except Exception: continue
            if key is None: rows.append(d)
            else: rows[d.get(key)] = d
    return rows if key is None else list(rows.values())
def read_json_latest(node, source, fn):
    p = latest(node, source, fn); return json.load(open(p, encoding='utf-8')) if p else None
def assembled(node):
    return _new_dir(os.path.join(POND, node, 'assembled'))
def latest_assembled(node, fn):
    return latest(node, 'assembled', fn)
def lock(node, order=''):
    os.makedirs(os.path.join(POND, node), exist_ok=True)
    open(os.path.join(POND, node, '.lock'), 'w').write(json.dumps({'order': order, 'since': datetime.datetime.now().isoformat(timespec='minutes')}))
def unlock(node):
    p = os.path.join(POND, node, '.lock')
    if os.path.exists(p): os.remove(p)
def locked(node): return os.path.exists(os.path.join(POND, node, '.lock'))
def migrate_dir(src_dir, node, source, date, note=''):
    """move an existing raw folder into the pond as an immutable drop dated <date> (files are moved, never copied twice; the folder is never deleted after)"""
    d = os.path.join(POND, node, source, date); n = 1
    while os.path.exists(d): n += 1; d = os.path.join(POND, node, source, f'{date}-{n}')
    shutil.move(src_dir, d)
    if note: open(os.path.join(d, 'DROP.md'), 'w', encoding='utf-8').write(note + '\n')
    return d
