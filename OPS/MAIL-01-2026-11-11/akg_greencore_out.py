"""CEO rider (2026-11-11): agent-kg.ai never got GREENCORE-OUT-01. The rewriter's output (akg-gout/out/public, GREENCORE-OUT-01 rail/rewrite.py,
the one rewriter) is copied over the site assets; the three styles.css comments it does not read are edited by hand; worker/x402.js is brought in
line with the live Worker (holdings: wefetch · https://wefetch.ai/), so a future deploy cannot restore GreenCore. Anchors .pre-akg-gout-2026-11-11."""
import pathlib, shutil
TAG = ".pre-akg-gout-2026-11-11"; SITE = pathlib.Path(r"C:\MATTHEWKEDDY\SITE"); OUT = pathlib.Path(r"C:\ALLOOLOO\OPS\MAIL-01-2026-11-11\akg-gout\out")
def anchor(p):
    a = p.with_name(p.name + TAG)
    if not a.exists(): shutil.copy2(p, a)
n = 0
for f in (OUT / "public").rglob("*"):
    if f.is_file():
        dst = SITE / f.relative_to(OUT); anchor(dst); shutil.copy2(f, dst); n += 1
print("assets from the rewriter:", n)
def edit(p, pairs):
    p = SITE / p; anchor(p); b = p.read_bytes(); nl = b"\r\n" if b"\r\n" in b else b"\n"; s = b.decode("utf-8").replace("\r\n", "\n")
    for x, y in pairs:
        assert s.count(x) == 1, (p.name, x[:60]); s = s.replace(x, y)
    p.write_bytes(s.replace("\n", nl.decode()).encode("utf-8")); print("edited", p)
edit("public/styles.css", [("Matches gsc-em.com design language", "Matches the estate design language"), ("same as gsc-em.com v4", "the estate stack, v4")])
edit("worker/x402.js", [('holdings: [{ name: "GreenCore Solutions Corp.", url: "https://gsc-em.com" }]', 'holdings: [{ name: "wefetch", url: "https://wefetch.ai/" }]')])
left = [str(p) for p in SITE.joinpath("public").rglob("*") if p.is_file() and ".pre-" not in p.name and p.suffix in (".html", ".json", ".txt", ".md", ".css", ".js", ".svg")
        and any(w in p.read_text(encoding="utf-8", errors="ignore").lower() for w in ("greencore", "gsc-em.com"))]
print("assets still naming GreenCore or gsc-em.com:", left)
