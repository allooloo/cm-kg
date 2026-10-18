"""A2A Cosmetics adapter — the hub's record fills as the rail (C:\\A2ACOSMETICS\\RAILS: kg_load.py → suppliers_find.py → pond_pass.py → product_sweep.py →
retailers_channels.py → labpass.py → validate_sources.py → export_record.py). Participants: makers, brands, manufacturers, distributors, retailers across
18 markets on 13 rule sets. Local gate names kept: 'labpass' (confirmed · changed · pond) and 'validated'. Store: DATA\\validated\\<area>\\<CC>.json;
pond DATA\\pond\\; raw DATA\\raw\\; spend DATA\\lab-spend-*.json and DATA\\SPEND-A2AC-07.json (metered)."""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, H)
from core import weekfolder  # noqa: E402

ROOT = r"C:\A2ACOSMETICS"; DATA = os.path.join(ROOT, "DATA"); V = os.path.join(DATA, "validated")
MARKETS = ["US", "MX", "CA", "BR", "UK", "FR", "DE", "NL", "IT", "ES", "PL", "CH", "AE", "IN", "SG", "JP", "KR", "AU"]
AREAS = ["suppliers", "products", "retailers", "ingredients", "enforcement"]


def rows(path):
    try:
        x = json.load(open(path, encoding="utf-8"))
        return x if isinstance(x, list) else (x.get("rows") or x.get("records") or [])
    except Exception: return []


class Adapter:
    def __init__(self, prog, week, scope, dry, live, engines, weekfolder, log, kid):
        self.prog, self.week, self.scope, self.dry, self.live, self.eng, self.wf, self.log, self.kid = prog, week, scope, dry, live, engines, weekfolder, log, kid

    def counts(self):
        out = {}
        for cc in MARKETS:
            c = {}
            for area in AREAS:
                p = os.path.join(V, area, f"{cc}.json")
                c[area] = len(rows(p)) if os.path.exists(p) else 0
            c["records"] = c["suppliers"] + c["products"] + c["retailers"]; c["makers"] = c["suppliers"]; c["brands"] = None
            out[cc] = c
        return out

    def width0(self):
        if self.live: self.log("[a2a-cosmetics] width0 live: kg_load (graph rows) + suppliers_find / retailers_channels stage B per market; not run in this order")
        return {"markets": len(MARKETS)}

    def width1(self):
        if self.live: self.log("[a2a-cosmetics] width1 live: product_sweep (brands' own product pages, structured data first); not run in this order")
        return {}

    def fill(self):
        if self.live: self.log("[a2a-cosmetics] fill live: ingredients (CosIng, hotlists), label and claims, market status, notification requirements; not run in this order")
        return {}

    def gate(self):
        pond = {area: sum(len(rows(p)) for p in glob.glob(os.path.join(DATA, "pond", area, "*.json"))) for area in AREAS if os.path.isdir(os.path.join(DATA, "pond", area))}
        return {"pond_rows": pond, "local_names": "labpass (confirmed · changed · pond); validated"}

    def land(self):
        self.closing = self.counts()
        if self.live: self.log("[a2a-cosmetics] land live: validate_sources → export_record → the door loader on the Container Apps; not run in this order")
        return {"markets": len(self.closing), "records": sum(v["records"] for v in self.closing.values()), "detail": self.closing}

    def check(self):
        from core import check as ck
        return {"pack": None, "note": "A2A Cosmetics is not enrolled in PADEL (no C:\\PADEL folder); the estate's own three-cloud rail is RAILS\\a2ac_three_cloud.py"}

    def spend_of_record(self):
        p = os.path.join(DATA, "SPEND-A2AC-07.json")
        if not os.path.exists(p): return []
        d = json.load(open(p, encoding="utf-8"))
        return [{"lab": k.split(" ")[0], "amount": round(v.get("cost_usd", 0), 4), "calls": v.get("calls"), "run_id": "A2AC-07 build (metered)", "source": p} for k, v in d.items() if isinstance(v, dict)]

    def finish(self, results, runs):
        closing = getattr(self, "closing", None) or self.counts()
        weekfolder.write_counts(self.wf, "a2a-cosmetics", self.week, closing, closing, note="COMPOUND harness " + ("dry run: opening = closing; rows counted from DATA\\validated\\<area>\\<CC>.json" if self.dry else "run"),
                                source=[r"C:\A2ACOSMETICS\DATA\validated\<area>\<CC>.json"])
        weekfolder.write_spend(self.wf, runs, note="dry run: no laboratory call; the build's metered spend of record is DATA\\SPEND-A2AC-07.json" if self.dry else "")
        weekfolder.evidence(self.wf, "spend-of-record.json", self.spend_of_record())
        weekfolder.write_landing(self.wf, f"# landing.md — a2a-cosmetics {self.week} (COMPOUND harness {'dry run' if self.dry else 'run'})\n\nNothing landed by this run.\n")
        weekfolder.evidence(self.wf, "hunt-results.json", results)
