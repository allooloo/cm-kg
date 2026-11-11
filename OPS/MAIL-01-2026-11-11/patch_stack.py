"""MAIL-01 item 7 (CEO 2026-11-11; ruling 2026-10-27 "we have contact forms"): allooloo@hey.com leaves the STACK-01 security.txt files.
The mailto line becomes the site's own contact form URL — https://<host>/#contact where the site's page carries the form (a2a-auditor.ai,
a2a-schema.ai, acm-registry.org; their Contact heading gains id="contact"), otherwise Allooloo's form https://allooloo.io/#contact. No email replaces it.
Patches the generator (stack_pages.py) and the generated worker/bundle.js the same way. Anchors .pre-mail01-2026-11-11 first."""
import pathlib, re, shutil, json
R = pathlib.Path(r"C:\ALLOOLOO\SITE\STACK-01"); TAG = ".pre-mail01-2026-11-11"
OWN_FORM = {"a2a-auditor.ai", "a2a-schema.ai", "acm-registry.org"}
def anchor(p):
    a = p.with_name(p.name + TAG)
    if not a.exists(): shutil.copy2(p, a)
# the generator: the same rule, by host
g = R / "stack_pages.py"; anchor(g); s = g.read_text(encoding="utf-8")
old = "SEC = lambda host: f'Contact: https://allooloo.io/security\\nContact: mailto:allooloo@hey.com\\n"
assert s.count(old) == 1, "SEC not found"
s = s.replace(old, "OWN_FORM = {'a2a-auditor.ai', 'a2a-schema.ai', 'acm-registry.org'}   # MAIL-01: the sites whose page carries the contact form\n"
                   "SEC = lambda host: f'Contact: https://allooloo.io/security\\nContact: {\"https://\" + host + \"/#contact\" if host in OWN_FORM else \"https://allooloo.io/#contact\"}\\n")
c_old = "return (f'<h2>Contact</h2><p class=\"meta\">Allooloo Technologies Corp."
assert s.count(c_old) == 1, "contact heading not found"
s = s.replace(c_old, "return (f'<h2 id=\"contact\">Contact</h2><p class=\"meta\">Allooloo Technologies Corp.")
g.write_text(s, encoding="utf-8", newline="")
# the bundle: each security.txt by its Canonical host; the contact heading gains its id
b = R / "worker" / "bundle.js"; anchor(b); t = b.read_text(encoding="utf-8")
n = 0
def fix(m):
    global n; n += 1; host = m.group(2)
    url = f"https://{host}/#contact" if host in OWN_FORM else "https://allooloo.io/#contact"
    return f"Contact: {url}\\n{m.group(1)}"
t2 = re.sub(r"Contact: mailto:allooloo@hey\.com\\n((?:Expires|Preferred-Languages)[^\"]*?Canonical: https://([^/\\]+)/)", fix, t)
h = t2.count('<h2>Contact</h2><p class=\\"meta\\">Allooloo Technologies Corp.')
t2 = t2.replace('<h2>Contact</h2><p class=\\"meta\\">Allooloo Technologies Corp.', '<h2 id=\\"contact\\">Contact</h2><p class=\\"meta\\">Allooloo Technologies Corp.')
assert "allooloo@hey.com" not in t2, "an occurrence is left in the bundle"
b.write_text(t2, encoding="utf-8", newline="")
print("security.txt fixed:", n, "· contact headings given id:", h)
