r"""patch_gh01_source.py — GH-01: each .org apex and its llms.txt gains a "Source: github.com/allooloo/<repo>" line.
sm-eco-10060.org: the generator (site03a.py) — the apex page gets the line under the Standalone-standard paragraph, llms.txt and index.md a Source line.
acm-68000.org: the snapshot of record (index.html, llms.txt, index.md) by a pass, as manifest04_acm.py did; its card is unchanged (no re-sign needed)."""
import os, re, json, shutil, hashlib, pathlib
# ---- the generator
p = r"C:\GREENCORE\PROTOCOLS\site03a.py"; shutil.copy2(p, r"C:\GREENCORE\AUDITS\SITE-03A-2026-10-28\site03a.py.pre-gh01"); s = open(p, encoding="utf-8").read()
def rep(old, new):
    global s; assert old in s, old[:70]; s = s.replace(old, new, 1)
rep('    tail = "  <h2>Sovereign</h2>\\n" + "\\n".join(f"  <p>{esc(x)}</p>" for x in SOV)',
    '    tail = "  <h2>Sovereign</h2>\\n" + "\\n".join(f"  <p>{esc(x)}</p>" for x in SOV) + \'\\n  <p class="meta">Source: <a href="https://github.com/allooloo/sm-eco-10060">github.com/allooloo/sm-eco-10060</a></p>\'   # GH-01')
rep('(["Sovereign", ""] + [x + "\\n" for x in SOV] if apex else [])', '(["Sovereign", ""] + [x + "\\n" for x in SOV] + ["Source: github.com/allooloo/sm-eco-10060", ""] if apex else [])')
open(p, "w", encoding="utf-8", newline="\n").write(s); print("site03a.py: Source line on the apex (page, llms.txt, index.md)")
# ---- acm-68000.org snapshot
SNAP = pathlib.Path(r"C:\GREENCORE\AUDITS\GREAT-CULL-02-2026-10-10\snapshots"); D = SNAP / "acm-68000.org"; BK = pathlib.Path(r"C:\GREENCORE\AUDITS\SITE-03A-2026-10-28\backup\gh01\acm-68000.org"); BK.mkdir(parents=True, exist_ok=True)
LINE = "Source: github.com/allooloo/acm-68000"
for f, old, new in (("index.html", '  <p class="meta">Operator: Allooloo Technologies Corp. · Open standard, MIT licence</p>', '  <p class="meta">Operator: Allooloo Technologies Corp. · Open standard, MIT licence · Source: <a href="https://github.com/allooloo/acm-68000">github.com/allooloo/acm-68000</a></p>'),
                   ("llms.txt", "Licence: MIT\n", "Licence: MIT\n" + LINE + "\n"), ("index.md", "Licence: MIT\n", "Licence: MIT\n" + LINE + "\n")):
    t = (D / f).read_text(encoding="utf-8"); assert old in t, (f, old[:40])
    if not (BK / f).exists(): shutil.copy2(D / f, BK / f)
    (D / f).write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
mp = SNAP / "acm-68000.org.manifest.json"; man = json.loads(mp.read_text(encoding="utf-8"))
for pth in ("/", "/llms.txt", "/index.md"):
    rel = "index.html" if pth == "/" else pth.lstrip("/"); body = (D / rel).read_bytes(); v = man["paths"][pth]; v["sha256"] = hashlib.sha256(body).hexdigest(); v["bytes"] = len(body); v["gh_01"] = True
mp.write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8"); print("acm-68000.org: Source line on the page, llms.txt, index.md; manifest re-hashed")
