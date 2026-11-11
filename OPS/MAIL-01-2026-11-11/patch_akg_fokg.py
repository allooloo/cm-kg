"""MAIL-01 item 7: allooloo@hey.com leaves agent-kg.ai and familyofficeknowledgegraph.ai — the home page's contact line and facts.json contact.agents_mail.
Each points at the site's own contact form (https://<host>/#contact; both pages carry id="contact"). No email replaces it. The public fo-kg-door copy
gets the same edit. Anchors .pre-mail01-2026-11-11 first."""
import pathlib, shutil
TAG = ".pre-mail01-2026-11-11"
SITES = {r"C:\MATTHEWKEDDY\SITE\public": "agent-kg.ai", r"C:\MATTHEWKEDDY\FO-KG\SITE\public": "familyofficeknowledgegraph.ai",
         r"C:\MATTHEWKEDDY\PUBLIC\fo-kg-door\public": "familyofficeknowledgegraph.ai"}
for d, host in SITES.items():
    for name, pairs in {
        "index.html": [('<p class="contact-direct">The agents that built this read their own mail: <a href="mailto:allooloo@hey.com">allooloo@hey.com</a></p>',
                        f'<p class="contact-direct">Write to us through the contact form: <a href="https://{host}/#contact">https://{host}/#contact</a></p>')],
        "facts.json": [('"agents_mail": "allooloo@hey.com"', None)]}.items():
        p = pathlib.Path(d) / name; a = p.with_name(p.name + TAG)
        if not a.exists(): shutil.copy2(p, a)
        raw = p.read_bytes(); nl = b"\r\n" if b"\r\n" in raw else b"\n"; s = raw.decode("utf-8").replace("\r\n", "\n")
        for x, y in pairs:
            if y is None:   # facts.json: contact.form → the form anchor; the mail line goes
                import re
                m = re.search(r'("form": ")([^"]*)(",\n\s*)"agents_mail": "allooloo@hey\.com"', s); assert m, (p, "facts contact block")
                s = s[:m.start()] + f'"form": "https://{host}/#contact"' + s[m.end():]
            else:
                assert s.count(x) == 1, (p, x[:60]); s = s.replace(x, y)
        assert "allooloo@hey.com" not in s, p
        p.write_bytes(s.replace("\n", nl.decode()).encode("utf-8")); print("edited", p)
