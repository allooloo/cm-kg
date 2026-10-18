"""agent-bev adapter — from 2026-W41 the COMPOUND harness owns width0, width1, fill, gate and land for agent-bev (CEO go 2026-09-29 on C02's
PASS equivalence). The old rail at C:\\AGENTBEV\\RECORD\\rails stays on disk, untouched: its stage scripts (harvest.py products / fill / sheets /
assemble, land.py) are the estate's source modules and are driven here as subprocesses under the harness's orchestration, lane guard, ledger
events, week-folder contract and spend meter. width0 (new participants) is the harness's own: Sonar paging of every protected name's producer
list to the 100-page ceiling (PB-14 rule: stop when a page returns under 60 names or adds none), into a harness pond drop, new producers
appended to the node's producers.json (anchor copy beside it). Program file: PROGRAM\\agent-bev.md.
Store: RECORD\\<node>\\index.json + pond; door copy DOORS\\bev-nodes\\public\\index\\<node>.counts.json. Dry run: reads only, scratch land."""
import datetime, json, os, re, shutil, subprocess, sys, unicodedata, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, H)
from core import gate, land, pond, weekfolder, vault  # noqa: E402

ROOT = r"C:\AGENTBEV"; REC = os.path.join(ROOT, "RECORD"); RAILS = os.path.join(REC, "rails"); IDX = os.path.join(ROOT, "DOORS", "bev-nodes", "public", "index")
SMU7 = os.path.join(ROOT, "START_ME_UP", "START_ME_UP_7_ORDERS_LOG.md")
PY = sys.executable
REQUIRED = ["producer", "brand", "product", "category"]
EU = {"es", "fr", "it", "de", "pt", "pl", "be", "nl", "dk"}
CUVEE = re.compile(r"cuvee:[a-z_]+:\d{4}(\d{2})?:[a-z]{2}(/[a-z0-9-]+){0,2}:(\d{8,14}|-):-")
ROUTE_BAD = re.compile(r"amazon|shop|tienda|botiga|boutique|negozio|cart|carrito|comprar|checkout|kaufen|acquista|legal|privac|cookie|politica|impressum", re.I)
PAID = ("alimarket", "kompass", "europages", "dnb.com", "einforma", "infoempresa", "axesor", "iberinform", "empresite", "societe.com", "pappers", "verif.com", "infogreffe", "creditsafe", "northdata", "zoominfo", "linkedin", "facebook", "instagram")
GI_KIND = {"WINE": "wine", "SPIRIT": "spirits", "AROMATISED_WINE": "wine", "BEER": "beer", "CIDER": "cider_perry"}
TODAY = datetime.date.today().isoformat()


def aslug(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80]


def slug(s, cc):
    a = aslug(s)
    if len(a) >= 3 or cc in EU: return a
    u = re.sub(r"[^\w]+", "-", unicodedata.normalize("NFKC", str(s or "")).lower()).strip("-_")[:80]
    return u if len(u) >= 2 else a


def host(u):
    try: return (urllib.request.urlparse(u if "://" in str(u) else "https://" + str(u)).hostname or "").lower().replace("www.", "")
    except Exception: return ""


def jload(p, default=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return default


def jdump(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    t = p + f".tmp-{os.getpid()}"; open(t, "w", encoding="utf-8").write(json.dumps(o, indent=1, ensure_ascii=False)); os.replace(t, p)


def jparse(txt):
    if not txt: return None
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip(), flags=re.M)
    m = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", t)
    try: return json.loads(m.group(0)) if m else None
    except Exception: return None


class Adapter:
    def __init__(self, prog, week, scope, dry, live, engines, weekfolder, log, kid):
        self.prog, self.week, self.scope, self.dry, self.live, self.eng, self.wf, self.log, self.kid = prog, week, scope, dry, live, engines, weekfolder, log, kid
        self.landed = jload(os.path.join(REC, "landed.json"), [])
        sel = os.environ.get("COMPOUND_NODES")  # a test run names its nodes: COMPOUND_NODES=es,uk
        self.nodes = [n for n in self.landed if not sel or n.split("-")[0] in sel.split(",")]
        self.max_gis = int(os.environ.get("COMPOUND_MAX_GIS", "0") or 0)
        self.scratch = os.path.join(H, "dryrun", "scratch", "agent-bev")
        self.nodes_cfg = self._nodes_config()
        self.opening = {n: self.counts(n) for n in self.landed}
        self.stage_spend = {}
        self.landed_lines = []
        self.order = f"COMPOUND-{self.week}"

    def _nodes_config(self):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("bev_nodes_config", os.path.join(RAILS, "nodes_config.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            return getattr(m, "NODES", {})
        except Exception as e:
            self.log(f"[agent-bev] nodes_config.py not importable ({e!r})"); return {}

    def counts(self, node):
        c = jload(os.path.join(IDX, f"{node}.counts.json"))
        return {k: c.get(k) for k in ("records", "makers", "brands", "complete", "by_category")} if c else None

    # ---- the rail's stage scripts as subprocesses (one owner per node: the lane guard reads RECORD\<cc>-bev\.lane) ----
    def _env(self, cc):
        env = dict(os.environ, BEV_NODE=cc, BEV_ORDER=self.order, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        p = os.path.join(REC, f"{cc}-bev", ".lane")
        if os.path.exists(p): env["BEV_LANE"] = open(p, encoding="utf-8").read().strip()  # the harness runs as the node's own lane; the stage never skips
        return env

    def _run(self, cc, script, args, tag, timeout=6 * 3600):
        logp = os.path.join(self.wf, "evidence", f"{cc}-bev.{tag}.log")
        with open(logp, "a", encoding="utf-8") as lf:
            lf.write(f"== {script} {' '.join(args)} {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"); lf.flush()
            r = subprocess.run([PY, os.path.join(RAILS, script)] + args, cwd=RAILS, env=self._env(cc), stdout=lf, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        tail = open(logp, encoding="utf-8", errors="replace").read().splitlines()[-3:]
        self.log(f"[agent-bev] {cc}-bev {script} {' '.join(args)} exit {r.returncode} | " + " / ".join(tail)[-300:])
        return r.returncode, logp

    # ---- width0: new participants — the harness's own Sonar paging of every protected name's producer list ----
    def width0(self):
        out = {}
        for node in self.nodes:
            cc = node.split("-")[0]; cfg = self.nodes_cfg.get(cc) or {}
            pp = os.path.join(REC, node, "producers.json"); roster = jload(pp) or {"producers": []}
            known = {r["slug"] for r in roster.get("producers", [])}
            rec = {"roster_before": len(known), "gis": 0, "pages": 0, "names": 0, "new": 0, "sonar_calls": 0}
            if not self.live:
                rec["note"] = "dry run: no Sonar call; roster read only"; out[node] = rec; continue
            origins = (jload(os.path.join(REC, "cuvee", "origins", f"{cc}.json")) or {}).get("origins", [])
            origins = [o for o in origins if o.get("protected_name")]
            if self.max_gis: origins = origins[: self.max_gis]
            drop = os.path.join(REC, node, "pond", "harness", self.week, "width0")
            added = []
            for o in origins:
                rec["gis"] += 1; seen_names, pages_read = set(), 0
                url = (o.get("producer_group") or {}).get("url")
                kind = GI_KIND.get(o.get("product_type"), "spirits")
                for page in range(1, 101):
                    pf = os.path.join(drop, f"{o['slug']}.p{page}.json")
                    if os.path.exists(pf): j = jload(pf)
                    else:
                        q = (f'List the producers (wineries / distilleries / cider makers / breweries) registered with the {cfg.get("gi_body", "producer group")} of the {cfg.get("adj", "")} protected name "{o["protected_name"]}" ({kind.replace("_", "/")} {o.get("gi_type", "GI")}). '
                             f'Use that body\'s own producer directory page{(" at " + url) if url else ""} or the official register. ' + ("Give the first 80." if page == 1 else f"Give entries {80 * (page - 1) + 1} to {80 * page} of the same directory, in its own order; if it has no more, say so in the note.") +
                             ' Answer ONLY as JSON: {"list_page": "<url of the producer directory page>", "producers": [{"name": "<producer legal or trading name as listed>", "website": "<url or null>"}], "total_on_page": <number the page shows, or null>, "note": "<if the directory needs a login, is paid, lists only part, or has no more pages>"}')
                        a = self.eng.ask("sonar", q, preset="low"); rec["sonar_calls"] += 1
                        if a is None: j = {"error": "sonar unavailable or exhausted", "page": page}; jdump(pf, {"gi": o["protected_name"], "page": page, "query": q, "sonar": j, "read_date": TODAY}); break
                        j = {"text": a["text"], "sources": a["sources"], "read_by": f"sonar ({(a['raw'].get('model') or 'agent')} · low)", "model": a["raw"].get("model")}
                        jdump(pf, {"gi": o["protected_name"], "page": page, "query": q, "sonar": j, "read_date": TODAY})
                    sn = (j.get("sonar") if "sonar" in j else j) or {}
                    parsed = jparse(sn.get("text")) or {}; cited = {host(u) for u in (sn.get("sources") or [])}
                    lp = parsed.get("list_page") if isinstance(parsed.get("list_page"), str) and host(parsed.get("list_page")) in cited else ((sn.get("sources") or [None])[0])
                    if lp and any(ph in host(lp) for ph in PAID): lp = None
                    names = [p for p in (parsed.get("producers") or []) if isinstance(p, dict) and p.get("name")]
                    new_here = 0
                    for p in names:
                        s = slug(p["name"], cc)
                        if not s or len(s) < 3 or s in seen_names or not lp: continue
                        seen_names.add(s); rec["names"] += 1
                        if s in known: continue
                        known.add(s); rec["new"] += 1
                        added.append({"slug": s, "names": [p["name"]], "kind": kind, "sources": [{"source": f"harness-width0:{o['slug']}", "source_url": lp, "read_by": sn.get("read_by", "sonar"), "read_date": TODAY}],
                                      "website": p.get("website") if isinstance(p.get("website"), str) and p["website"].startswith("http") else None, "gis": [o["protected_name"]]})
                    pages_read += 1; rec["pages"] += 1
                    if len(names) < 60 or not names or all(slug(p["name"], cc) in seen_names for p in names) and new_here == 0 and page > 1: break
                    if "no more" in str(parsed.get("note") or "").lower(): break
            if added:
                anchor = pp + f".pre-{self.week}"
                if not os.path.exists(anchor): shutil.copyfile(pp, anchor)
                roster["producers"] = roster.get("producers", []) + added; roster["harness_width0"] = {"week": self.week, "added": len(added), "date": TODAY, "drop": drop}
                jdump(pp, roster)
            rec["roster_after"] = len(known); out[node] = rec
            self.log(f"[agent-bev] width0 {node}: gis {rec['gis']} pages {rec['pages']} names {rec['names']} new {rec['new']} sonar calls {rec['sonar_calls']}")
        weekfolder.evidence(self.wf, "width0-roster.json", out)
        return {"nodes": len(out), "new_producers": sum(v.get("new", 0) for v in out.values()), "sonar_calls": sum(v.get("sonar_calls", 0) for v in out.values()), "detail": out}

    # ---- width1: the record's own page per roster line (the rail's products stage: Sonar per producer not yet in the pond) ----
    def width1(self):
        out = {}
        for node in self.nodes:
            cc = node.split("-")[0]
            if not self.live: out[node] = {"note": "dry run"}; continue
            code, logp = self._run(cc, "harvest.py", ["products", "12"], "width1")
            ps = jload(os.path.join(REC, node, "products-stage.json")) or {}
            self.stage_spend.setdefault(node, {})["products"] = ps.get("spend"); out[node] = {"exit": code, "producers": ps.get("producers"), "spend": ps.get("spend", {}).get("sonar"), "exhausted": ps.get("exhausted")}
        return {"detail": out}

    # ---- fill: the fields width1 left empty (page reads, technical sheets, page reads again) ----
    def fill(self):
        out = {}
        for node in self.nodes:
            cc = node.split("-")[0]
            if not self.live: out[node] = {"note": "dry run"}; continue
            r = []
            for args, tag in ((["fill"], "fill-1"), (["sheets", "10"], "sheets"), (["fill"], "fill-2")):
                code, logp = self._run(cc, "harvest.py", args, tag); r.append((args[0], code))
                if args[0] == "sheets":
                    m = re.findall(r"sonar \$([0-9.]+)", open(logp, encoding="utf-8", errors="replace").read())
                    if m: self.stage_spend.setdefault(node, {})["sheets_sonar_usd_line"] = float(m[-1])
            out[node] = {"steps": r}
        return {"detail": out}

    # ---- gate: the rail's assemble (source rule + vocabularies + fences) then the COMPOUND gate on a sample ----
    def gate(self, sample=2000):
        out = {}
        for node in self.nodes:
            cc = node.split("-")[0]; rec = {}
            if self.live:
                code, logp = self._run(cc, "harvest.py", ["assemble"], "assemble")
                m = re.search(r"\[assemble\] records (\d+) \| refusals (\d+) \| conflicts (\d+)", open(logp, encoding="utf-8", errors="replace").read())
                rec = {"exit": code, "records": int(m.group(1)) if m else None, "refusals": int(m.group(2)) if m else None, "conflicts": int(m.group(3)) if m else None}
                if code == 0 and m: open(os.path.join(REC, node, ".assembled"), "w").close()
            p = os.path.join(REC, node, "index.json")
            if os.path.exists(p):
                recs = self._sample_records(p, sample); gated = []
                fences = {"hard": 0, "cuvee": 0, "route": 0, "tier": 0}
                for r in recs:
                    if not all(((r.get(f) or {}).get("value")) for f in REQUIRED): fences["hard"] += 1
                    cu = ((r.get("cuvee") or {}).get("string")) or ""
                    if not CUVEE.fullmatch(cu) and not (cu.startswith("cuvee:wine:-:") and (r.get("hs_code") or {}).get("state") == "conflict"): fences["cuvee"] += 1
                    rv = (r.get("order_route") or {}).get("value")
                    if rv and ROUTE_BAD.search(rv): fences["route"] += 1
                    if (r.get("tier") or {}).get("value"): fences["tier"] += 1
                    gated.append((r.get("record_id"), {f: r[f] for f in r if isinstance(r.get(f), dict) and "value" in r[f]}))
                counts, review, kept = gate.gate_store(gated, REQUIRED)
                rec.update({"sampled": len(recs), "fences": fences, "gate": counts, "review_flags": len(review)})
            out[node] = rec
        weekfolder.evidence(self.wf, "gate.json", out)
        return {"nodes": len(out), "detail": out}

    def _sample_records(self, path, n):
        recs = []; dec = json.JSONDecoder()
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(1 << 16); i = head.find('"records"')
            if i < 0: return recs
            buf = head[head.find("[", i) + 1:]
            while len(recs) < n:
                buf = buf.lstrip().lstrip(",").lstrip()
                if buf.startswith("]"): break
                try: obj, j = dec.raw_decode(buf); recs.append(obj); buf = buf[j:]
                except json.JSONDecodeError:
                    more = f.read(1 << 20)
                    if not more: break
                    buf += more
        return recs

    # ---- land: the rail's land.py per node under RECORD\.land-lock, with the order marker the lock entry hangs on ----
    def _order_marker(self):
        t = open(SMU7, encoding="utf-8").read()
        if f"- {self.order} " in t: return
        line = f"- {self.order} · {datetime.date.today().strftime('%b %d %Y')} · COMPOUND harness run (CEO go 2026-09-29; scope {self.scope}); landings below are the dated lock entries of record.\n"
        i = t.index("\n## Standing rule"); t = t[:i + 1] + line + t[i + 1:]
        shutil.copyfile(SMU7, SMU7 + f".pre-{self.order.lower()}-{TODAY}") if not os.path.exists(SMU7 + f".pre-{self.order.lower()}-{TODAY}") else None
        open(SMU7, "w", encoding="utf-8", newline="").write(t)

    def land(self):
        out = {}
        if not self.live:
            scratch = pond.scratch_copy(IDX, os.path.join(H, "dryrun", "scratch"), "agent-bev-index")
            same = all(land.byte_compare(os.path.join(IDX, f"{n}.counts.json"), os.path.join(scratch, f"{n}.counts.json")) for n in self.landed)
            self.closing = {n: self.counts(n) for n in self.landed}
            return {"nodes": len(self.landed), "byte_identical": same, "dry": True}
        self._order_marker()
        for node in self.nodes:
            cc = node.split("-")[0]; before = self.opening.get(node) or {}
            if not os.path.exists(os.path.join(REC, node, ".assembled")) or not os.path.exists(os.path.join(REC, node, "index.json")):
                out[node] = {"skipped": "not assembled"}; continue
            code, logp = self._run(cc, "land.py", [cc], "land", timeout=3 * 3600)
            after = self.counts(node) or {}
            ll = [l for l in open(SMU7, encoding="utf-8").read().splitlines() if l.strip().startswith(f"- LANDED {node} ")]
            line = ll[-1].strip() if ll else None
            if line: self.landed_lines.append(line)
            fc = None
            data = land.landing_data(node, before, {"records": after.get("records"), "verified": 0, "listed": after.get("records"), "fields": None}, sorted(os.listdir(IDX)) and [f for f in os.listdir(IDX) if f.startswith(node)], fc, SMU7, self.week,
                                     makers_after=after.get("makers"), brands_after=after.get("brands"), lock_entry_text=line, exit=code, order=self.order)
            e = weekfolder.event("agent-bev", "landing", "hunter", f"{self.week}/agent-bev/{node}", data, kid=self.kid, dry=False)
            out[node] = {"exit": code, "records_before": before.get("records"), "records_after": after.get("records"), "event": e["id"], "landed_line": bool(line)}
            self.log(f"[agent-bev] land {node}: exit {code} records {before.get('records')} → {after.get('records')} event {e['id']}")
        self.closing = {n: self.counts(n) for n in self.landed}
        return {"nodes": len(out), "detail": out}

    def check(self):
        from core import check as ck
        pack = ck.latest_pack("agent-bev")
        return {"pack": pack["pack_id"] if pack else None, "note": "agent-bev is not enrolled in PADEL; the edge instrument reads its five doors daily"}

    def claims(self):
        """claimed / verified makers from the sellers' door store (KV agent-bev-claims), read with the Allooloo D1/KV token; never a key printed."""
        try:
            tok = open(r"C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt", encoding="utf-8").read().strip().splitlines()[0]
            acc = "dd2832b36f171b815f84c8487aada36b"; H_ = {"Authorization": "Bearer " + tok, "User-Agent": "compound-hunter"}
            ns = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces?per_page=100", headers=H_), timeout=60))
            nid = next((n["id"] for n in ns.get("result", []) if n["title"] == "agent-bev-claims"), None)
            if not nid: return {"claimed": None, "verified": None, "note": "claims namespace not found"}
            keys = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces/{nid}/keys?prefix=claim:&limit=1000", headers=H_), timeout=60)).get("result", [])
            verified = 0
            for k in keys[:300]:
                try:
                    v = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces/{nid}/values/{urllib.request.quote(k['name'], safe='')}", headers=H_), timeout=30))
                    if str(v.get("status") or v.get("claim_status") or "").lower() == "verified": verified += 1
                except Exception: pass
            return {"claimed": len(keys), "verified": verified, "source": "KV agent-bev-claims keys claim:* (values read for state)"}
        except Exception as e:
            return {"claimed": None, "verified": None, "note": f"claims store unreadable: {e!r}"[:160]}

    def finish(self, results, runs):
        closing = getattr(self, "closing", None) or {n: self.counts(n) for n in self.landed}
        opening = self.opening
        cl = self.claims() if self.live else {"claimed": 0, "verified": 0}
        claim = {n: {"listed": (c or {}).get("records"), "claimed": None, "verified": None} for n, c in closing.items()}
        claim["_estate"] = cl
        # this run's spend: the harness meter (width0) + the rail's products-stage meters (width1) + the sheets line (fill), per node
        rail_runs = []
        for node, sp in self.stage_spend.items():
            s = (sp.get("products") or {}).get("sonar") or {}
            if s: rail_runs.append({"lab": "sonar", "amount": round(float(s.get("usd") or 0), 4), "calls": s.get("calls"), "run_id": f"{self.week}/{self.scope}/{node}/width1", "node": node, "source": f"RECORD\\{node}\\products-stage.json (the rail's products meter, this run)"})
            if sp.get("sheets_sonar_usd_line") is not None: rail_runs.append({"lab": "sonar", "amount": sp["sheets_sonar_usd_line"], "calls": None, "run_id": f"{self.week}/{self.scope}/{node}/sheets", "node": node, "source": "sheets stage spend line (the rail's meter, this run)"})
        weekfolder.write_counts(self.wf, "agent-bev", self.week, opening, closing, claim_status=claim, doors_green=None,
                                note="COMPOUND harness " + ("dry run" if self.dry else f"live run, scope {self.scope}; width0 by the harness (Sonar paging), width1/fill/gate/land through the rail's stage scripts under harness orchestration"),
                                source=[r"C:\AGENTBEV\DOORS\bev-nodes\public\index\<node>.counts.json (before and after)", r"C:\AGENTBEV\RECORD\landed.json", SMU7])
        weekfolder.write_spend(self.wf, runs + rail_runs, note="harness meter (width0 Sonar) + the rail's own meters per node for width1 and sheets; fill is page reads (no lab)")
        weekfolder.write_landing(self.wf, f"# landing.md — agent-bev {self.week} (COMPOUND harness {'dry run' if self.dry else 'live run'})\n\nLock: RECORD\\.land-lock (land.py). Order marker in START_ME_UP_7: {self.order}.\n\n" + ("\n".join(self.landed_lines) + "\n" if self.landed_lines else "No landing by this run.\n"))
        weekfolder.evidence(self.wf, "hunt-results.json", results)
