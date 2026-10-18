"""Office adapter — checks and statement only (Book § 8). No weekly hunt; FO-KG refreshes are CEO-called (C:\\MATTHEWKEDDY\\FO-KG\\harvest: fetch_sources →
build_records → assemble → build_nodes → export; sweep_all.ps1). Counts come from the Family Office Knowledge Graph's own render at request time
(familyofficeknowledgegraph.ai facts.json / records/nodes.json), never typed. The five COMPOUND zones are office rows."""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, H)
from core import weekfolder  # noqa: E402

NODES_URL = "https://familyofficeknowledgegraph.ai/records/nodes.json"


class Adapter:
    def __init__(self, prog, week, scope, dry, live, engines, weekfolder, log, kid):
        self.prog, self.week, self.scope, self.dry, self.live, self.eng, self.wf, self.log, self.kid = prog, week, scope, dry, live, engines, weekfolder, log, kid

    def nodes(self):
        try:
            j = json.load(urllib.request.urlopen(urllib.request.Request(NODES_URL, headers={"User-Agent": "compound-hunter/1.0"}), timeout=30))
            lst = j.get("nodes") if isinstance(j, dict) else j
            return {(n.get("node") or n.get("id")): {"records": (n.get("records") if isinstance(n.get("records"), int) else n.get("count")), "fields": n.get("fields"), "as_of": n.get("as_of"), "door": n.get("door")}
                    for n in (lst or []) if isinstance(n, dict) and (n.get("node") or n.get("id"))}
        except Exception as e:
            self.log(f"[office] nodes.json unreachable: {e!r}"); return {}

    def check(self):
        from core import check as ck
        pack = ck.latest_pack("office")
        return {"pack": pack["pack_id"] if pack else None, "doors": [(d["door"], d["result"]) for d in (pack["doors"] if pack else [])]}

    def finish(self, results, runs):
        closing = self.nodes()
        weekfolder.write_counts(self.wf, "office", self.week, closing, closing, note="checks and statement only; FO-KG node counts read live from records/nodes.json; nothing landed", source=[NODES_URL])
        weekfolder.write_spend(self.wf, runs, note="no weekly hunt")
        weekfolder.write_landing(self.wf, f"# landing.md — office {self.week}\n\nNo landing: FO-KG refreshes are CEO-called.\n")
        weekfolder.evidence(self.wf, "hunt-results.json", results)
