"""MAIL-01: apply this order's two substitutions to the live stack-pages module and compare with the new build — equal means live was source before."""
import re
OWN = {"a2a-auditor.ai", "a2a-schema.ai", "acm-registry.org"}
live = open(r"C:/AGENTBEV/OPS/BEV-LIB-02-2026-11-10/live_stack-pages/entry.js", encoding="utf-8").read()
dry = open(r"C:/AGENTBEV/OPS/BEV-LIB-04-2026-11-10/dry_stack-pages/entry.js", encoding="utf-8").read()
pat = r"Contact: mailto:allooloo@hey\.com\\n((?:Expires|Preferred-Languages)[^\"]*?Canonical: https://([^/\\]+)/)"
x = re.sub(pat, lambda m: "Contact: " + ("https://" + m.group(2) + "/#contact" if m.group(2) in OWN else "https://allooloo.io/#contact") + "\\n" + m.group(1), live)
x = x.replace('<h2>Contact</h2><p class="meta">Allooloo Technologies Corp.', '<h2 id="contact">Contact</h2><p class="meta">Allooloo Technologies Corp.')
norm = lambda t: re.sub(r"//# sourceMappingURL.*", "", t).replace("\r\n", "\n").strip()
print("live + this change == new build:", norm(x) == norm(dry))
