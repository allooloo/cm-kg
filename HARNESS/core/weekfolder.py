"""weekfolder.py — writes the week-folder contract of LEDGER-SCHEMA § 5 (counts.json, spend.json, landing.md, evidence\\) and the ledger events.
The same writer serves every estate; the adapter supplies the numbers from the estate's own store."""
import datetime, json, os, sys

COMPOUND = r"C:\COMPOUND"
sys.path.insert(0, os.path.join(COMPOUND, "LEDGER"))
import ledger  # noqa: E402

TODAY = datetime.date.today().isoformat()


def folder(week, estate, root=None):
    d = os.path.join(root or COMPOUND, week, estate)
    os.makedirs(os.path.join(d, "evidence"), exist_ok=True)
    return d


def write_counts(d, estate, week, opening, closing, claim_status=None, doors_green=None, note="", source=None, nodes_of_record=None):
    mon = datetime.date.fromisocalendar(int(week[:4]), int(week.split("W")[1]), 1)
    obj = {"estate": estate, "week": week, "period": {"from": mon.isoformat(), "to": (mon + datetime.timedelta(days=6)).isoformat()}, "note": note,
           "opening": opening, "closing": closing, "claim_status": claim_status or {}, "doors_green": doors_green, "source": source or [], "written_by": "COMPOUND harness", "written_on": TODAY}
    if nodes_of_record is not None: obj["nodes_of_record"] = nodes_of_record
    json.dump(obj, open(os.path.join(d, "counts.json"), "w", encoding="utf-8"), indent=1)
    return obj


def write_spend(d, runs, note=""):
    obj = {"runs": runs, "balance_note": note, "written_by": "COMPOUND harness", "written_on": TODAY}
    json.dump(obj, open(os.path.join(d, "spend.json"), "w", encoding="utf-8"), indent=1)
    return obj


def write_landing(d, text):
    open(os.path.join(d, "landing.md"), "w", encoding="utf-8", newline="\n").write(text if text.endswith("\n") else text + "\n")


def evidence(d, name, obj):
    p = os.path.join(d, "evidence", name)
    if isinstance(obj, (dict, list)): json.dump(obj, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    else: open(p, "w", encoding="utf-8", newline="\n").write(str(obj))
    return p


def event(estate, kind, actor, ref, data, kid=None, dry=False):
    """Write one ledger event (signed with kid when given; unsigned with actor '<rail>-unsigned' otherwise). In a dry run nothing is written."""
    if dry: return {"id": f"(dry-run {kind} {ref})", "dry": True}
    if kid is None and not actor.endswith("-unsigned"): actor = actor + "-unsigned"
    return ledger.append({"estate": estate, "kind": kind, "actor": actor, "ref": ref, "data": data}, kid=kid)


def rail_kid(estate):
    """The rail's signing kid on the office keyring (C02): present in the vault → sign; absent → unsigned events."""
    # one kid per estate rail (CEO ruling C02-7, 2026-09-29)
    kid = {"agent-bev": "rail-agent-bev-2026-09", "allooloo": "rail-allooloo-2026-09", "gsc": "rail-gsc-2026-09", "a2a-cosmetics": "rail-a2a-cosmetics-2026-09", "a2a-peptides": "rail-a2a-peptides-2026-09", "office": "rail-office-2026-09"}[estate]
    try:
        ledger.vault_paths(kid)
        return kid if (os.path.exists(ledger.vault_paths(kid)["seed"]) or os.path.exists(ledger.vault_paths(kid)["pem"])) else None
    except Exception:
        return None
