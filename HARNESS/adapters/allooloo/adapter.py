"""Allooloo adapter — the port of the CM-KG Saturday sweep (C:\\ALLOOLOO\\CM-KG\\RAILS\\sweep_all.ps1 → sweep_node.ps1: harvest → immutable pond drop →
door data → regional store reload → apex index + deploy → Numbers Log line → surfaces re-render → snapshot) as the Allooloo program, all eleven nodes,
one run. Rulings kept (PROGRAM\\allooloo.md): Perplexity search layer, Grok second, Mistral review-only, Gemini leads reads on US and Japan, wire search
costs two searches per issuer, per-node lock, GLOBAL BUILD LOCK, pond rule (dated immutable drops; assemblers read only from the pond), upload only
the newest drop, the sweep rail's own C:\\ALLOOLOO\\.azure. The Saturday task of record keeps firing the Allooloo rail; this adapter proves
equivalence by dry run and does not switch the task.
Dry run: reads the newest assembled drop per node (POND\\<node>\\assembled\\<date>\\<cc>-events.jsonl and the issuers workbook) and the apex
node list the rail built (CM-KG\\DOOR\\apex\\static\\nodes.json), computes records/events per node, compares to the rail's own Numbers Log."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, H)
from core import gate, pond, weekfolder  # noqa: E402

ROOT = r"C:\ALLOOLOO"; CMKG = os.path.join(ROOT, "CM-KG"); POND = os.path.join(CMKG, "POND"); RAILS = os.path.join(CMKG, "RAILS")
NODES = [("nl", "westeurope"), ("ch", "switzerlandnorth"), ("fr", "francecentral"), ("de", "germanywestcentral"), ("sg", "southeastasia"), ("au", "australiaeast"), ("uk", "uksouth"), ("ca", "canadacentral"), ("jp", "japaneast"), ("kr", "koreacentral"), ("us", "eastus")]
REQUIRED = ["name", "ticker", "exchange"]


class Adapter:
    def __init__(self, prog, week, scope, dry, live, engines, weekfolder, log, kid):
        self.prog, self.week, self.scope, self.dry, self.live, self.eng, self.wf, self.log, self.kid = prog, week, scope, dry, live, engines, weekfolder, log, kid
        self.apex = {n["node"]: n for n in json.load(open(os.path.join(CMKG, "DOOR", "apex", "static", "nodes.json"), encoding="utf-8"))}

    def locks(self):
        return {"build_lock": os.path.exists(os.path.join(POND, ".build-lock")), "node_locks": [cc for cc, _ in NODES if os.path.exists(os.path.join(POND, f"{cc}-cm-kg", ".lock"))]}

    def width0(self):
        """Identity roster: exchange lists + GLEIF golden copy — monthly on the rail (<cc>-width0\\run_refresh.ps1); read the newest width0 drop per node."""
        out = {}
        for cc, _ in NODES:
            node = f"{cc}-cm-kg"; date, p = pond.latest(POND, node, "width0")
            files = len(os.listdir(p)) if p else 0
            out[node] = {"width0_drop": date, "files": files, "records_on_apex": self.apex.get(node, {}).get("records")}
        if self.live: self.log("[allooloo] width0 live = the node's <cc>-width0\\run_refresh.ps1 on the monthly clock; not run in this order")
        return {"nodes": len(out), "detail": out}

    def width1(self):
        """Disclosure over a 7-day window: newest width1 drop per node (the Saturday sweep's harvest step)."""
        out = {}
        for cc, _ in NODES:
            node = f"{cc}-cm-kg"; date, p = pond.latest(POND, node, "width1")
            out[node] = {"width1_drop": date, "files": len(os.listdir(p)) if p else 0}
        if self.live: self.log("[allooloo] width1 live = <cc>-width1\\run_refresh.ps1 (7-day window, new pond drop); not run in this order")
        return {"detail": out}

    def fill(self):
        """Fill + Confirm chain per node (<cc>-fill-confirm\\run_refresh.ps1): Grok live layer, aliases, ChatGPT batch, Gemini, Perplexity, Mistral review, rematch, confirm, rebuilds, spend."""
        out = {}
        for cc, _ in NODES:
            node = f"{cc}-cm-kg"; date, p = pond.latest(POND, node, "fill-confirm")
            out[node] = {"fill_confirm_drop": date}
        return {"detail": out}

    def gate(self):
        """Confirm mapped to gate: the events of the newest assembled drop carry source, read-by and State (sourced · filled · confirmed · conflict)."""
        out = {}
        for cc, _ in NODES:
            node = f"{cc}-cm-kg"; date, ev = pond.latest(POND, node, "assembled", f"{cc}-events.jsonl")
            states, n = {}, 0
            for row in pond.read_jsonl(ev):
                n += 1; st = (row.get("state") or row.get("State") or ("sourced" if row.get("source") or row.get("url") else "unsourced")); states[st] = states.get(st, 0) + 1
            out[node] = {"assembled_drop": date, "events_in_drop": n, "states": states}
        weekfolder.evidence(self.wf, "gate-assembled.json", out)
        return {"detail": out}

    def land(self):
        """Dry: recompute records and events per node from the newest assembled drop / the apex list the rail built, into the scratch; compare to the Numbers Log."""
        closing, diffs = {}, []
        nl = self._numbers_log()
        for cc, _ in NODES:
            node = f"{cc}-cm-kg"; ap = self.apex.get(node, {})
            rec, ev = ap.get("records"), ap.get("events")
            date, evp = pond.latest(POND, node, "assembled", f"{cc}-events.jsonl")
            ev_drop = sum(1 for _ in pond.read_jsonl(evp)) if evp else None
            closing[node] = {"records": rec or 0, "events": ev or 0, "as_of": ap.get("as_of"), "live": ap.get("live"), "assembled_drop": date, "events_in_newest_drop": ev_drop}
            last = nl.get(node)
            if last:
                if str(last["records"]) != str(rec): diffs.append(f"{node}: records apex {rec} vs numbers log {last['records']} ({last['date']})")
                if str(last["events"]) != str(ev): diffs.append(f"{node}: events apex {ev} vs numbers log {last['events']} ({last['date']})")
            if ev_drop is not None and ev is not None and ev_drop != ev: diffs.append(f"{node}: events in the newest assembled drop {ev_drop} vs apex {ev} (the apex counts the merged store, the drop is one sweep's window)")
        self.closing = closing
        weekfolder.evidence(self.wf, "equivalence.json", {"numbers_log": nl, "apex": self.apex, "differences": diffs})
        if self.live: self.log("[allooloo] land live = door data → regional store reload → apex → numbers line → re-render; the Saturday task of record does it; not run in this order")
        return {"nodes": len(closing), "records": sum(v["records"] for v in closing.values()), "events": sum(v["events"] for v in closing.values()), "differences": diffs, "detail": closing}

    def _numbers_log(self):
        s = open(os.path.join(ROOT, "START_ME_UP", "NODE-SURFACES.md"), encoding="utf-8").read()
        m = re.search(r"(## 9 NUMBERS LOG[\s\S]*?```\n)([\s\S]*?)(```)", s)
        out = {}
        for l in (m.group(2).splitlines() if m else []):
            p = [x.strip() for x in l.split("·")]
            if len(p) >= 4 and re.match(r"[a-z]{2}-cm-kg", p[0]) and p[2].isdigit(): out[p[0]] = {"date": p[1], "records": p[2], "events": p[3]}
        return out

    def check(self):
        from core import check as ck
        pack = ck.latest_pack("allooloo")
        return {"pack": pack["pack_id"] if pack else None, "doors": [(d["door"], d["result"]) for d in (pack["doors"] if pack else [])]}

    def finish(self, results, runs):
        closing = getattr(self, "closing", {}) or {}
        opening = dict(closing)
        weekfolder.write_counts(self.wf, "allooloo", self.week, opening, closing, claim_status=None, doors_green=None,
                                note="COMPOUND harness " + ("dry run: opening = closing (nothing landed); records and events per node from the apex list the rail built (CM-KG\\DOOR\\apex\\static\\nodes.json); locks " + json.dumps(self.locks()) if self.dry else "run"),
                                source=[r"C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json", r"C:\ALLOOLOO\START_ME_UP\NODE-SURFACES.md § 9 NUMBERS LOG", r"C:\ALLOOLOO\CM-KG\POND\<node>\assembled\<date>\<cc>-events.jsonl"])
        weekfolder.write_spend(self.wf, runs, note="dry run: no laboratory call; the rail's own spend per node is in CM-KG\\SPEND\\<node>-<yyyy-mm>.jsonl" if self.dry else "")
        weekfolder.write_landing(self.wf, f"# landing.md — allooloo {self.week} (COMPOUND harness {'dry run' if self.dry else 'run'})\n\nNothing landed by this run. No node lock taken; global BUILD lock respected.\n")
        weekfolder.evidence(self.wf, "hunt-results.json", results)
