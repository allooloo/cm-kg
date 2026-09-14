r"""START_ME_UP_5 §7.5 — weekly Sunday scan of every surface in scope, exceptions only to the build log.
Runs aeo_scan.py with a dated 'weekly' label, then diffs every check against the newest earlier scan folder (AZURE\aeo-scan-*\summary.tsv).
Any check that changed status, any surface that errored, or any check name that is new or gone is appended to START_ME_UP\AEO-BUILD-LOG.md;
a clean week appends nothing there (one line goes to AZURE\aeo-weekly.log so the run itself is on record). Never a loop; one pass."""
import subprocess, sys, os, glob, datetime
sys.stdout.reconfigure(encoding='utf-8')
RAILS = r'C:\ALLOOLOO\CM-KG\RAILS'; AZ = r'C:\ALLOOLOO\AZURE'; LOG = r'C:\ALLOOLOO\START_ME_UP\AEO-BUILD-LOG.md'
def read(tsv):
    rows = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8') if l.strip()]
    head = rows[0][1:]; return head, {r[0]: dict(zip(head, r[1:])) for r in rows[1:]}
before = sorted(glob.glob(os.path.join(AZ, 'aeo-scan-*', 'summary.tsv')), key=os.path.getmtime)
prev = before[-1] if before else None
label = 'weekly'
subprocess.run([sys.executable, '-u', os.path.join(RAILS, 'aeo_scan.py'), label], check=False)
after = sorted(glob.glob(os.path.join(AZ, 'aeo-scan-*', 'summary.tsv')), key=os.path.getmtime)
cur = after[-1] if after else None
stamp = datetime.date.today().isoformat(); notes = []
if not cur or cur == prev: notes.append('scan produced no summary (rail error)')
else:
    h2, b = read(cur); h1, a = read(prev) if prev else ([], {})
    for k in [x for x in h2 if x not in h1]: notes.append(f'new check on the scanner: {k} (a moved bar, not a regression)')
    for k in [x for x in h1 if x not in h2]: notes.append(f'check gone from the scanner: {k}')
    for host, st in b.items():
        if 'error' in st or not st: notes.append(f'{host}: scan error'); continue
        for k in h2:
            was = a.get(host, {}).get(k); now = st.get(k)
            if was is not None and was != now: notes.append(f'{host}: {k} {was} → {now}')
open(os.path.join(AZ, 'aeo-weekly.log'), 'a', encoding='utf-8').write(f'{stamp} weekly scan {os.path.dirname(cur) if cur else "none"} · exceptions {len(notes)}\n')
if notes:
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'\n## Weekly scan exceptions — {stamp}\n' + ''.join(f'- {n}\n' for n in notes))
print('\n'.join(notes) or 'no exceptions')
