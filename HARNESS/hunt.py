"""hunt.py — the COMPOUND hunt harness (ORDER-C02). One codebase, estate as a parameter, PADEL's harness as the pattern.

usage: hunt.py --estate <name> --week 2026-Wnn --scope <scope-id> [--stage width0|width1|fill|gate|land|check|all] [--dry-run] [--live] [--out <folder>]

Stages, in order, each writing ledger events and the week-folder contract of LEDGER-SCHEMA § 5:
  width0  roster and size (new participants)                     width1  the record's own page per roster line
  fill    the fields width1 left empty                            gate    the tailings-pond check (core.gate)
  land    under the estate's lock into the estate's own store      check   PADEL's door sweep as a library call (core.check)
Engine roles and the search layer come from PROGRAM\\<estate>.md. A lab out of credit is marked exhausted in the ledger and skipped.
No pause prompt. Non-interactive everywhere: each estate root's own AZURE_CONFIG_DIR and .gh are set from STARTHERE's rows (core.vault).
Keys are read from the estate's vault at launch, never copied, never printed.

--dry-run  reads the latest pond drops already on disk, runs gate and land against a scratch copy of the store under HARNESS\\dryrun\\, writes
           the week-folder contract to --out (default HARNESS\\dryrun\\<week>\\<estate>\\) and touches no ledger line, no lock, no store, no surface.
--live     allows laboratory calls. Refused unless the PROGRAM file's scope block carries go: <date> for the named scope (no go, no hunt: a note event
           'no go for <week>' is written and the run exits 0 so closeout can still sign a zero-spend statement).
"""
import argparse, datetime, json, os, sys, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from core import program, vault, engines, weekfolder, check, land  # noqa: E402
import adapters  # noqa: E402

STAGES = ["width0", "width1", "fill", "gate", "land", "check"]
TODAY = datetime.date.today().isoformat()


def log_to(path):
    f = open(path, "a", encoding="utf-8")
    def log(*a):
        line = " ".join(str(x) for x in a); print(line, flush=True); f.write(line + "\n"); f.flush()
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--estate", required=True); ap.add_argument("--week", required=True); ap.add_argument("--scope", default=None)
    ap.add_argument("--stage", default="all"); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--live", action="store_true"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    estate, week, dry = a.estate, a.week, a.dry_run
    if a.live and dry: sys.exit("hunt: --live and --dry-run exclude each other")
    prog = program.load(estate)
    scope = prog.scope(); sid = a.scope or scope["id"]
    vault.set_login_dirs(estate)
    out_root = a.out or (os.path.join(HERE, "dryrun") if dry else r"C:\COMPOUND")
    wf = weekfolder.folder(week, estate, root=out_root)
    log = log_to(os.path.join(wf, "evidence", f"hunt-{TODAY}.log"))
    log(f"[hunt] estate {estate} week {week} scope {sid} stage {a.stage} dry_run {dry} live {a.live} out {wf}")
    kid = weekfolder.rail_kid(estate)
    log(f"[hunt] rail kid {kid or 'none (events unsigned)'}; labs with a key: " + ", ".join(k for k, v in vault.available(estate).items() if v))
    live = bool(a.live)
    if live and not scope["go"]:
        log(f"[hunt] no go for {week} in {prog.path} (scope {sid}); no hunt")
        weekfolder.event(estate, "note", "hunter", f"{week}/{estate}", {"text": f"no go for {week} (scope {sid})", "program_path": prog.path}, kid=kid, dry=False)
        return 0
    roles = prog.engine_roles(); log("[hunt] engine roles from the program file:", json.dumps(roles))
    eng = engines.Engines(estate, roles, live=live, log=log)
    Adapter = adapters.load(estate)
    ad = Adapter(prog=prog, week=week, scope=sid, dry=dry, live=live, engines=eng, weekfolder=wf, log=log, kid=kid)
    stages = STAGES if a.stage == "all" else [a.stage]
    results = {}
    for st in stages:
        fn = getattr(ad, st, None)
        if fn is None: log(f"[hunt] {st}: not in this estate's program (skipped)"); continue
        log(f"[hunt] == {st}")
        try:
            results[st] = fn()
        except Exception as e:
            log(f"[hunt] {st} FAILED: {e!r}"); log(traceback.format_exc()[-1500:]); results[st] = {"error": repr(e)}
            if st in ("land",): break
    # spend + exhausted labs → the week folder and the ledger
    runs = eng.spend.runs(f"{week}/{sid}")
    for lab in sorted(eng.exhausted):
        if eng.keys.get(lab) is not None:  # a key exists but the lab refused: exhausted on the wire
            weekfolder.event(estate, "note", "hunter", f"{week}/{estate}/{lab}", {"text": f"{lab} exhausted during {week}; skipped, run continued"}, kid=kid, dry=dry)
    ad.finish(results, runs)
    log("[hunt] done", json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "detail"}) for k, v in results.items()}, default=str)[:1500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
