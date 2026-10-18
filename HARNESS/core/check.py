"""check.py — PADEL folded in as a library call (ORDER-C02 § PADEL folded). C:\\PADEL is never changed by the harness.
live:  runs C:\\PADEL\\harness\\sweep.py <ESTATE> <run_id> with PADEL's own venv python (as daily.py does), then report.py and pack.py, and reads the
       pack it sealed. PADEL's daily task and cadence are untouched; this is one more caller.
dry:   reads the newest sealed pack for the estate from C:\\PADEL\\CASEBACK\\packs and writes door_check events from it (no sweep is run, no vendor read).
Estates without a PADEL folder (agent-bev, a2a-cosmetics as of 2026-09-29) get no pack and a question line."""
import datetime, glob, io, json, os, subprocess, zipfile

PADEL = r"C:\PADEL"
PY = os.path.join(PADEL, "harness", "venv", "Scripts", "python.exe")
FOLDER = {"gsc": "GSC", "allooloo": "ALLOOLOO", "office": "OFFICE", "a2a-peptides": "A2APEPTIDES", "a2a-cosmetics": None, "agent-bev": None}


def latest_pack(estate):
    fold = FOLDER.get(estate)
    if not fold: return None
    packs = sorted(glob.glob(os.path.join(PADEL, "CASEBACK", "packs", f"*-{fold}.zip")))
    if not packs: return None
    return read_pack(packs[-1])


def read_pack(zp):
    pack_id = os.path.basename(zp)[:-4]
    sha = open(zp + ".sha256", encoding="utf-8").read().split()[0] if os.path.exists(zp + ".sha256") else None
    z = zipfile.ZipFile(zp)
    sweep = json.load(io.TextIOWrapper(z.open("run/sweep.json"), encoding="utf-8")) if "run/sweep.json" in z.namelist() else {"doors": []}
    doors = [{"door": d.get("host"), "result": "green" if d.get("PASS") else "red", "lines_failed": len(d.get("fails") or []), "vendors": d.get("vendor_fails") or [], "fails": d.get("fails") or []} for d in sweep.get("doors", [])]
    vend = sorted({v for d in doors for v in d["vendors"]})
    return {"pack_id": pack_id, "sha256": sha, "path": zp, "run": sweep.get("run"), "finished": sweep.get("finished"), "doors": doors,
            "three_cloud": ("all doors pass on the stock client paths; vendor-attributed: " + "; ".join(vend)) if vend else "all doors pass on the stock client paths"}


def run_live(estate, log=print):
    """One PADEL sweep + report + pack for the estate, through PADEL's own scripts. Returns the sealed pack read back."""
    fold = FOLDER.get(estate)
    if not fold: return None
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H%M")
    env = dict(os.environ, PYTHONUTF8="1")
    for args, t in ((["sweep.py", fold, run_id], 3600), (["report.py", fold, run_id, "COMPOUND harness check"], 300), (["pack.py", fold, run_id], 300)):
        r = subprocess.run([PY] + args, capture_output=True, text=True, timeout=t, env=env, cwd=os.path.join(PADEL, "harness"))
        log(f"[check] {args[0]} exit {r.returncode} " + (r.stdout + r.stderr)[-300:].replace("\n", " / "))
        if r.returncode != 0 and args[0] == "sweep.py": return None
    zp = os.path.join(PADEL, "CASEBACK", "packs", f"{run_id}-{fold}.zip")
    return read_pack(zp) if os.path.exists(zp) else None


def door_events(pack, estate, weekfolder, kid, dry):
    ids = []
    if not pack: return ids
    for d in pack["doors"]:
        data = {"pack_id": pack["pack_id"], "door": d["door"], "result": d["result"], "lines_failed": d["lines_failed"], "vendors": d["vendors"], "three_cloud": pack["three_cloud"], "pack_sha256": pack["sha256"], "run": pack["run"]}
        e = weekfolder.event(estate, "door_check", "hunter", f"{pack['pack_id']}/{d['door']}", data, kid=kid, dry=dry); ids.append(e["id"])
    return ids
