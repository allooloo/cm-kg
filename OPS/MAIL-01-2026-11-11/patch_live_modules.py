"""MAIL-01: eco-pages and acm-signals have source drift (eco-pages live data is newer than the laptop's data.js; acm-signals source carries a newer
acm_first than live). So the edit is made on each Worker's LIVE module (fetched by live_vs_src.py), nothing else changed, and deployed unbundled with
the Worker's own wrangler.toml (main → the patched live file). Writes ship/<script>/ (patched module + wrangler.toml)."""
import pathlib, re, shutil
OPS = pathlib.Path(__file__).parent; LIVE = pathlib.Path(r"C:\AGENTBEV\OPS\BEV-LIB-02-2026-11-10")
JOBS = {
  "eco-pages": (r"C:\ALLOOLOO\CM-KG\ECO\wrangler.toml", "entry.js", [
    ('<a href="mailto:allooloo@hey.com">Support</a>', '<a href="${host === "allooloo.ai" || !host ? "https://allooloo.io/#contact" : `https://${host}/#contact`}">Support</a>', 1),
    ('return `<h2>Contact Us</h2><form action="${FORM}"', 'return `<h2 id="contact">Contact Us</h2><form action="${FORM}"', 1),
    ("T(`Contact: mailto:allooloo@hey.com\\nContact: https://allooloo.io/security\\nExpires: 2027-10-24T00:00:00Z", "T(`Contact: https://allooloo.io/#contact\\nContact: https://allooloo.io/security\\nExpires: 2027-10-24T00:00:00Z", 1),
    ("T(`Contact: mailto:allooloo@hey.com\\nContact: https://allooloo.io/security\\nExpires: 2027-10-23T00:00:00Z", "T(`Contact: https://${host}/#contact\\nContact: https://allooloo.io/security\\nExpires: 2027-10-23T00:00:00Z", 2)]),
  "acm-signals": (r"C:\ALLOOLOO\CM-KG\ACM-SIGNALS\wrangler.toml", "index.js", [
    ("T(`Contact: mailto:allooloo@hey.com\\nContact: https://allooloo.io/security", "T(`Contact: https://allooloo.io/#contact\\nContact: https://allooloo.io/security", 1)]),
}
for name, (toml, mod, pairs) in JOBS.items():
    src = (LIVE / f"live_{name}" / mod).read_text(encoding="utf-8")
    src = re.sub(r"\n//# sourceMappingURL=.*$", "\n", src.rstrip()) + "\n"
    for a, b, n in pairs:
        a, b = a.replace("\\n", "\n"), b.replace("\\n", "\n")   # the bundler writes template-literal \n escapes as real newlines
        assert src.count(a) == n, (name, src.count(a), a[:60]); src = src.replace(a, b)
    assert "allooloo@hey.com" not in src, name
    d = OPS / "ship" / name; d.mkdir(parents=True, exist_ok=True)
    (d / "worker.js").write_text(src, encoding="utf-8", newline="\n")
    t = pathlib.Path(toml).read_text(encoding="utf-8")
    t = re.sub(r'(?m)^main\s*=.*$', 'main = "worker.js"   # MAIL-01: the live module with only the address edits (source drift; see report)\nno_bundle = true', t, count=1)
    (d / "wrangler.toml").write_text(t, encoding="utf-8", newline="\n")
    print(name, "→", d, "· edits", len(pairs))
