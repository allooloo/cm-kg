r"""patch_digest_site04.py — SITE-04: the nightly digest line reads the ESTATE traffic number the standing TRAFFIC run writes (ops/traffic/latest.json),
and the fleet tag of record for the DIGEST-CAP-01 drift check comes from the env FLEET_TAG when set (so the digest job can run on a newer image than the
node fleet without flagging every node job). .pre copy beside."""
import shutil
p = r"C:\ALLOOLOO\CM-KG\RAILS\job\job_digest.py"; shutil.copy2(p, p + ".pre-site04-20261028"); s = open(p, encoding="utf-8").read()
def rep(old, new):
    global s; assert old in s, old[:60]; s = s.replace(old, new, 1)
rep("    FLEET = IMAGE_TAG;", "    FLEET = os.environ.get('FLEET_TAG') or IMAGE_TAG;   # SITE-04 (2026-10-28): the fleet tag of record by env when the digest runs ahead of the node fleet\n   ")
rep("    n_pass = sum(1 for r in rows if r['verdict'] == 'PASS');",
    "    # SITE-04 (2026-10-28): the ESTATE traffic number of the standing TRAFFIC run (cmkg-traffic-nightly, ops/traffic/latest.json); the RADAR tile keeps the typed LENS-01 figure (CEO)\n"
    "    tr_line = 'ESTATE traffic · not read (flag): ops/traffic/latest.json absent'\n"
    "    try:\n"
    "        tr = get_json(ops, 'traffic/latest.json')\n"
    "        if tr: tr_line = (f\"ESTATE traffic (the lens, 30 days {tr['window'][0]} .. {tr['window'][1]} UTC): {tr['estate_requests_30d']:,} requests · \" + ' · '.join(f\"{k} {v:,}\" for k, v in (tr.get('groups') or {}).items())\n"
    "                          + f\" · {round((tr.get('share_of_account') or 0) * 100, 1)}% of the account · roster {tr.get('roster')} · read {tr.get('read_at')} by {tr.get('written_by')}\")\n"
    "    except Exception as e: tr_line = f'ESTATE traffic · not read (flag): {repr(e)[:120]}'\n"
    "    n_pass = sum(1 for r in rows if r['verdict'] == 'PASS');")
rep("'backfill': BF, 'backfill_line': bf_line,", "'backfill': BF, 'backfill_line': bf_line, 'estate_traffic_line': tr_line,")
rep("cap_line0, '', cap_line, '',", "cap_line0, '', cap_line, '', tr_line, '',")
rep("<p>{cap_line}</p><p>{bf_line}</p>", "<p>{cap_line}</p><p>{tr_line}</p><p>{bf_line}</p>")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched job_digest.py")
