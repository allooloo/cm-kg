r"""One-time migration of the existing rails' raw folders into the pond (CEO standing rule, 2026-09-11), plus the working-folder junction every
rail uses from now on: <rail>\raw is a directory junction to the rail's current open drop (POND\<node>\<rail>\<date>\), so resume-safe workers keep
writing to raw\ and the assemblers read raw\ (the open drop) plus every earlier drop through pond.read_jsonl_all. A run_refresh opens a new drop
first (python pond_open.py <node> <rail>), which closes the previous drop (immutable from then on) and re-points the junction.
Usage: python pond_migrate.py <rail-folder> <node> <source> <date> "<note>"   e.g. python pond_migrate.py ca-width1 ca-cm-kg width1 2026-09-10 "ORDER-003 first run"
"""
import os, sys, subprocess, json, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import pond
RAILS = r'C:\ALLOOLOO\CM-KG\RAILS'
def junction(link, target):
    if os.path.islink(link) or os.path.isdir(link):
        if os.path.isdir(link) and not os.path.islink(link):
            # a real folder left behind must never be deleted: move it aside as its own drop
            raise SystemExit(f'{link} is a real folder; migrate it first')
        os.rmdir(link)
    subprocess.check_call(['cmd', '/c', 'mklink', '/J', link, target], stdout=subprocess.DEVNULL)
def is_junction(p):
    try: return os.path.isdir(p) and bool(os.readlink(p))
    except OSError: return False
def migrate(rail, node, source, date, note):
    raw = os.path.join(RAILS, rail, 'raw')
    if is_junction(raw): print(rail, 'raw is already a junction ->', os.readlink(raw)); return os.readlink(raw)
    if not os.path.isdir(raw): print(rail, 'has no raw folder'); return None
    d = pond.migrate_dir(raw, node, source, date, note + f'\nMigrated {datetime.date.today().isoformat()} from {raw}. Immutable: never overwritten, never deleted; a re-run is a new drop.')
    open(os.path.join(d, '.open'), 'w').write(date + '\n')  # the migrated drop stays open until the next run_refresh opens a new one (workers may still be appending)
    subprocess.check_call(['cmd', '/c', 'mklink', '/J', raw, d], stdout=subprocess.DEVNULL)
    print(rail, 'raw ->', d); return d
if __name__ == '__main__':
    rail, node, source, date = sys.argv[1:5]; note = sys.argv[5] if len(sys.argv) > 5 else ''
    migrate(rail, node, source, date, note)
