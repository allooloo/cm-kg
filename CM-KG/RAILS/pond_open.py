r"""Open a new drop for a rail and re-point its raw\ junction at it (pond rule 1: a re-run is a new drop; the previous drop is closed and immutable).
Usage: python pond_open.py <node> <rail-folder> [source]   e.g. python pond_open.py uk-cm-kg uk-width1 width1
Carries forward nothing: workers start empty in the new drop; assemblers merge every drop on the existing keys."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import pond
RAILS = r'C:\ALLOOLOO\CM-KG\RAILS'
node, rail = sys.argv[1], sys.argv[2]; source = sys.argv[3] if len(sys.argv) > 3 else rail.split('-', 1)[1]
if pond.locked(node) and os.environ.get('POND_IGNORE_LOCK') != '1': raise SystemExit(f'{node} is locked (build order in flight); the sweep skips')
pond.close_drop(node, source)
d = pond.open_drop(node, source)
raw = os.path.join(RAILS, rail, 'raw')
if os.path.isdir(raw):
    try: os.readlink(raw); os.rmdir(raw)
    except OSError: raise SystemExit(f'{raw} is a real folder; run pond_migrate.py first')
subprocess.check_call(['cmd', '/c', 'mklink', '/J', raw, d], stdout=subprocess.DEVNULL)
print('open drop', d, '-> raw')
