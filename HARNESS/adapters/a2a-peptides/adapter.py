"""A2A Peptides adapter — the hub's record fills as the rail (C:\\A2APEPTIDES\\REGISTERS: core.py, pathway_fill.py, the register modules eu_ema, ca_dpd,
ch_swissmedic, jp_pmda, kr_nedrug; DATA layers raw → extracted → validated → pond per A2AP_9 SWEEPS). Participants: licensed suppliers, pharmacies,
distributors, authorised buyers. Store: DATA\\validated\\{substances, presentations, providers, rule_sets}; the rail's own counts file
DATA\\validated\\counts.<date>.json (newest). Local gate name kept: 'validated' (source page verified, primitive complete). Enforcement watch, pathway
status and licence status ride along as checks, not as the hunt. Breadth (new substances, presentations) is on the customer's word."""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, H)
from core import weekfolder  # noqa: E402

ROOT = r"C:\A2APEPTIDES"; DATA = os.path.join(ROOT, "DATA"); V = os.path.join(DATA, "validated")


class Adapter:
    def __init__(self, prog, week, scope, dry, live, engines, weekfolder, log, kid):
        self.prog, self.week, self.scope, self.dry, self.live, self.eng, self.wf, self.log, self.kid = prog, week, scope, dry, live, engines, weekfolder, log, kid

    def counts_file(self):
        fs = sorted(glob.glob(os.path.join(V, "counts.*.json")))
        return (fs[-1], json.load(open(fs[-1], encoding="utf-8"))) if fs else (None, {})

    def counts(self):
        p, c = self.counts_file(); v = c.get("validated", {})
        by_j = v.get("presentations_by_jurisdiction", {})
        out = {}
        for j, n in by_j.items():
            out[j] = {"records": n, "makers": None, "brands": v.get("distinct_brands_by_jurisdiction", {}).get(j), "pathway_rows": v.get("pathway_rows_by_jurisdiction", {}).get(j), "skus_with_banner": v.get("skus_with_banner_by_jurisdiction", {}).get(j)}
        out["_all"] = {"records": v.get("presentations"), "substances": v.get("substances"), "brands": v.get("distinct_brands"), "providers": len(os.listdir(os.path.join(V, "providers"))) if os.path.isdir(os.path.join(V, "providers")) else None, "source": p}
        return out

    def width0(self):
        if self.live: self.log("[a2a-peptides] width0 live: spine build (INN/UNII/INCI/CAS) + providers from the licence registers; on the customer's word; not run in this order")
        return {}

    def width1(self):
        if self.live: self.log("[a2a-peptides] width1 live: pathway fill per substance × jurisdiction (REGISTERS\\pathway_fill.py); not run in this order")
        return {}

    def fill(self):
        if self.live: self.log("[a2a-peptides] fill live: presentation fill from the MA/DIN/NDC/registro registers; shelf rule for SKUs; not run in this order")
        return {}

    def gate(self):
        pond = sum(len(f) for _, _, f in os.walk(os.path.join(DATA, "pond"))) if os.path.isdir(os.path.join(DATA, "pond")) else 0
        return {"pond_files": pond, "local_name": "validated (source page verified, primitive complete)"}

    def land(self):
        self.closing = self.counts()
        if self.live: self.log("[a2a-peptides] land live: validated → Postgres → the door on the Container Apps (a2a-peptides-mcp); not run in this order")
        return {"jurisdictions": len([k for k in self.closing if k != "_all"]), "records": self.closing["_all"]["records"], "detail": self.closing}

    def check(self):
        from core import check as ck
        pack = ck.latest_pack("a2a-peptides")
        return {"pack": pack["pack_id"] if pack else None, "note": "PADEL folder A2APEPTIDES has runs but no sealed pack as of 2026-09-29" if not pack else ""}

    def finish(self, results, runs):
        closing = getattr(self, "closing", None) or self.counts()
        nodes = {k: {"records": v["records"], "makers": v.get("makers"), "brands": v.get("brands")} for k, v in closing.items() if k != "_all"}
        weekfolder.write_counts(self.wf, "a2a-peptides", self.week, nodes, nodes, note="COMPOUND harness " + ("dry run: opening = closing; the rail's own counts file " + str(closing["_all"].get("source")) if self.dry else "run"),
                                source=[closing["_all"].get("source") or r"C:\A2APEPTIDES\DATA\validated\counts.<date>.json"])
        weekfolder.write_spend(self.wf, runs, note="dry run: no laboratory call" if self.dry else "")
        weekfolder.write_landing(self.wf, f"# landing.md — a2a-peptides {self.week} (COMPOUND harness {'dry run' if self.dry else 'run'})\n\nNothing landed by this run.\n")
        weekfolder.evidence(self.wf, "hunt-results.json", results)
