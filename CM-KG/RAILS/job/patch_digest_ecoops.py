r"""patch_digest_ecoops.py — ECO-OPS-01: the nightly digest shows the eco-ops row (digest/rows/<night>/eco-ops*.json) beside the eco-refresh row. .pre beside."""
import shutil
p = r"C:\ALLOOLOO\CM-KG\RAILS\job\job_digest.py"; shutil.copy2(p, p + ".pre-ecoops01-20261028"); s = open(p, encoding="utf-8").read()
old = "    # RCO-A-01 (2026-10-24): the receipts Allooloo's doors wrote that night"
assert old in s
new = ("    # ECO-OPS-01 (2026-10-28): the nightly rebuild of the SM-ECO-10060 set writes digest/rows/<night>/eco-ops.json (a same-night re-run lands beside as eco-ops-<n>.json)\n"
       "    names = sorted((b.name for b in ops.list_blobs(name_starts_with=f'digest/rows/{NIGHT}/eco-ops')), key=lambda x: int(re.search(r'-(\\d+)\\.json$', x).group(1)) if re.search(r'-(\\d+)\\.json$', x) else 1)\n"
       "    e = get_json(ops, names[-1]) if names else None\n"
       "    if e: row('eco-ops', 'eco', NIGHT, e.get('verdict'), e.get('hosts_changed'), (e.get('flags') or []) + ([] if e.get('rolled') else ['not rolled tonight']), e.get('hand_items') or [])\n"
       "    else: row('eco-ops', 'eco', None, 'NOT LANDED', None, ['no eco-ops row for this night'], [])\n" + old)
s = s.replace(old, new, 1); open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched job_digest.py for the eco-ops row")
