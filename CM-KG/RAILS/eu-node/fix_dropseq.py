r"""fix_dropseq.py — DAY ORDER 4 (2026-10-24): pond._new_dir numbers a new drop above the highest drop of the day already present.
A job syncs only the newest assembled drop (say 2026-10-24-2), so the day's first name is free in the container and the old _new_dir took it; the
new drop then sorted below -2 and job_node refused the run ('no new assembled drop'). pond.py.pre-dropseq-20261024 beside."""
import io
p = r"C:\ALLOOLOO\CM-KG\RAILS\eu-node\pond.py"; t = io.open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in t else "\n"
o = nl.join(["def _new_dir(base):",
             "    d = os.path.join(base, _today()); n = 1",
             "    while os.path.exists(d):",
             "        n += 1; d = os.path.join(base, f'{_today()}-{n}')",
             "    os.makedirs(d); return d"])
n = nl.join(["def _new_dir(base):",
             "    # DAY ORDER 4 (2026-10-24): number above the highest drop of the day already present (a job syncs only the newest drop, so the",
             "    # day's first name can be free while a later -n stands; a new drop must always sort newest)",
             "    t = _today(); have = [0] + [int(x[11:] or 1) for x in (os.listdir(base) if os.path.isdir(base) else []) if re.match(r'^' + t + r'(-\\d+)?$', x)]",
             "    n = max(have) + 1; d = os.path.join(base, t if n == 1 else f'{t}-{n}')",
             "    os.makedirs(d); return d"])
assert t.count(o) == 1, 'anchor'
io.open(p, "w", encoding="utf-8", newline="").write(t.replace(o, n)); print("pond._new_dir numbered above the day's highest drop")
