"""GSC adapter — the CPG Knowledge Graph gets NO standing hunt (Book § 8): checks and extras only. width0/width1/fill are extras on the CEO's go.
Counts come from the graph's own facts (gsc-knowledgegraph.ai/facts.json record block: brands, makers, retail_banners, sovereign_nodes — separate
registries, never summed) read live at run time; nothing typed. One program-file line feeds verified Cosmetics makers and brands into kg.* (an extra,
not a hunt; the feed runs through A2A Cosmetics' validated layer on the CEO's go)."""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, H)
from core import weekfolder  # noqa: E402

FACTS = "https://gsc-knowledgegraph.ai/facts.json"


class Adapter:
    def __init__(self, prog, week, scope, dry, live, engines, weekfolder, log, kid):
        self.prog, self.week, self.scope, self.dry, self.live, self.eng, self.wf, self.log, self.kid = prog, week, scope, dry, live, engines, weekfolder, log, kid

    def facts(self):
        try:
            j = json.load(urllib.request.urlopen(urllib.request.Request(FACTS, headers={"User-Agent": "compound-hunter/1.0"}), timeout=30))
            return j.get("record") or {}
        except Exception as e:
            self.log(f"[gsc] facts.json unreachable: {e!r}"); return {}

    def check(self):
        from core import check as ck
        pack = ck.latest_pack("gsc")
        return {"pack": pack["pack_id"] if pack else None, "doors": [(d["door"], d["result"]) for d in (pack["doors"] if pack else [])]}

    def finish(self, results, runs):
        r = self.facts()
        closing = {"cpg-kg": {"records": r.get("brands"), "makers": r.get("makers"), "brands": r.get("brands"), "retail_banners": r.get("retail_banners"), "nodes": r.get("sovereign_nodes"), "read_at": r.get("read_at")}}
        weekfolder.write_counts(self.wf, "gsc", self.week, closing, closing, note="checks and extras only; counts read live from gsc-knowledgegraph.ai/facts.json record block (brands, makers, retail banners are separate registries, never summed); nothing landed", source=[FACTS], nodes_of_record=r.get("sovereign_nodes"))
        weekfolder.write_spend(self.wf, runs, note="no standing hunt; extras on the CEO's go")
        weekfolder.write_landing(self.wf, f"# landing.md — gsc {self.week}\n\nNo landing: the CPG Knowledge Graph carries no standing weekly hunt (Book § 8). gtins.* read-only since THE LOAD; kg.* the additive layer.\n")
        weekfolder.evidence(self.wf, "hunt-results.json", results)
