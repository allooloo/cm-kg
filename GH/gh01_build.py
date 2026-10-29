r"""gh01_build.py — GH-01: assemble the two public repositories' files under C:\ALLOOLOO\GH\ from the surfaces of record, never typed:
  sm-eco-10060/  README.md (the apex text after MANIFEST-03/04, from the apex index.md of record; first line links the .org) · registry.json (the generator's
                 lane file, the same roster read the pages use) · signals.json (the apex signals.json) · schema/member.schema.json · LICENSE · CITATION.cff
  acm-68000/     README.md (the acm-68000.org text: the signals, the rules, the Allooloo door; first line links the .org) · signals.json (the seven signals,
                 code · state · action · page, from acm-68000.org/.well-known/acm-68000.json) · schema/signal.schema.json · LICENSE
Banned-words rule (SITE-03A, ruling (b)) checked over both folders; a hit stops the build. Usage: python -X utf8 -I gh01_build.py"""
import os, re, json, shutil, urllib.request
GH = r"C:\ALLOOLOO\GH"; SNAP = r"C:\GREENCORE\AUDITS\GREAT-CULL-02-2026-10-10\snapshots"; LANE = r"C:\GREENCORE\AUDITS\SITE-03A-2026-10-28"
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, s): os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8", newline="\n").write(s)
# ---- sm-eco-10060
md = rd(os.path.join(SNAP, "sm-eco-10060.org", "index.md")).split("\n")
title = md[0].lstrip("# ").strip(); body = "\n".join(md[1:]).strip()
body = re.sub(r"^> sm-eco-10060\.org\s*\n", "", body).strip()
readme = f"# {title}\n\nReference site: **https://sm-eco-10060.org/** — this repository is the manifest as a document. Licence: MIT (see `LICENSE`). Cite it with `CITATION.cff`.\n\n{body}\n\n## Files\n\n- `registry.json` — the 49 members in registry order: code, namespace, jurisdiction, canonical node, Allooloo node, record door, Agent Card, duty (the line as the node publishes it; `null` where no Allooloo node serves the market). Rewritten by the nightly rebuild (ECO-OPS-01) when the roster moves.\n- `signals.json` — the seven ACM-68000 signals the member pages carry (source acm-68000.org).\n- `schema/member.schema.json` — the member record's schema.\n"
wr(os.path.join(GH, "sm-eco-10060", "README.md"), readme)
shutil.copy2(os.path.join(LANE, "registry.json"), os.path.join(GH, "sm-eco-10060", "registry.json"))
shutil.copy2(os.path.join(SNAP, "sm-eco-10060.org", "signals.json"), os.path.join(GH, "sm-eco-10060", "signals.json"))
# ---- acm-68000
acm = json.loads(rd(os.path.join(SNAP, "sm-eco-10060.org", "signals.json")))   # the seven signals as read from acm-68000.org/signals.json at the SM build (code · state · action · page; the .org wins)
sig = [{"code": s["code"], "state": s["state"], "action": s["action"], "page": s["page"]} for s in acm["signals"]]
wr(os.path.join(GH, "acm-68000", "signals.json"), json.dumps({"protocol": "ACM-68000", "standard": "https://acm-68000.org/", "operator": "Allooloo Technologies Corp.", "licence": "MIT", "rule": "append-only · non-breaking · non-substitutable · deterministic", "signals": sig}, indent=2, ensure_ascii=False) + "\n")
table = "\n".join(f"| {s['code']} | {s['state']} | {s['action']} | {s['page']} |" for s in sig)
wr(os.path.join(GH, "acm-68000", "README.md"), f"""# ACM-68000 — the seven canonical signals

Reference site: **https://acm-68000.org/** — this repository is the signal protocol as a document. Operator: Allooloo Technologies Corp. Licence: MIT (see `LICENSE`).

**State determines behavior.** ACM-68000 is the base deterministic execution vocabulary for agentic commerce: seven states, fixed meanings, no scoring, ranking or narrative interpretation. An agent does not need to infer what a state means. The number is the contract.

## The seven signals

| Signal | State | Action | Page |
|---|---|---|---|
{table}

## Rules of the vocabulary

1. **Append-only.** A code, once published, keeps its meaning forever. New codes may be added; none is renamed, renumbered or removed.
2. **Non-breaking.** An agent written against today's seven keeps working against every later version.
3. **Non-substitutable.** A code is never reused for a different state, and a state is never carried by a different code.
4. **Deterministic.** The same inputs give the same signal. A signal carries a state, not an opinion.
5. **Domain profiles apply, never redefine.** A domain — for example the issuer states on the Electronic Compliance Object pages (fr-eco.ai, de-eco.ai …) — maps its own conditions onto these seven; it never changes what a code means.

## Where the signals are served

- Listed issuers: `get_signal` at **https://mcp.getissuer.ai/mcp** (the Allooloo door; one signed record per listed company, served from the issuer's own country) and on every market's Electronic Compliance Object page.
- The jurisdiction layer the signals pair with: **https://sm-eco-10060.org/** (github.com/allooloo/sm-eco-10060).
- Receipts for decisions cleared: **https://rco-a2a.ai/**.

## Files

- `signals.json` — the seven signals: code, state, action, page.
- `schema/signal.schema.json` — the signal record's schema.
""")
shutil.copy2(os.path.join(GH, "sm-eco-10060", "LICENSE"), os.path.join(GH, "acm-68000", "LICENSE"))
# ---- the banned-words rule over both folders (ruling (b): duty lines of record are exempt)
duties = sorted({r["duty"] for r in json.load(open(os.path.join(GH, "sm-eco-10060", "registry.json"), encoding="utf-8"))["registry"] if r.get("duty") and re.search("product", r["duty"], re.I)})
ex = re.compile("|".join([re.escape(d) for d in duties] + [r"Know Your Product"]), re.I); pat = re.compile(r"CPG|product|barcode|GTIN|grocery|consumer goods|SPARKS|gtinfetch", re.I)
hits = {}
for repo in ("sm-eco-10060", "acm-68000"):
    for root, _, fs in os.walk(os.path.join(GH, repo)):
        if ".git" in root: continue
        for f in fs:
            m = pat.findall(ex.sub("", rd(os.path.join(root, f))))
            if m: hits[os.path.relpath(os.path.join(root, f), GH)] = m
print("files:", sorted(os.path.relpath(os.path.join(r, f), GH) for repo in ("sm-eco-10060", "acm-68000") for r, _, fs in os.walk(os.path.join(GH, repo)) if ".git" not in r for f in fs))
print("banned hits:", hits or 0)
if hits: raise SystemExit("STOP: banned words in the repo files")
