"""MAIL-01 item 7: allooloo@hey.com leaves the ECO worker (eco-pages: the country <cc>-eco.ai pages, the regime page, allooloo.ai's kit) and the
ACM signals worker (acm-signals). Each mailto becomes that site's own contact form URL: https://<host>/#contact where the page carries the form
(the country and regime pages; their "Contact Us" heading gains id="contact"), otherwise Allooloo's form https://allooloo.io/#contact.
No email replaces it (CEO ruling 2026-10-27). Anchors .pre-mail01-2026-11-11 first."""
import pathlib, shutil
TAG = ".pre-mail01-2026-11-11"
def edit(p, pairs):
    p = pathlib.Path(p); a = p.with_name(p.name + TAG)
    if not a.exists(): shutil.copy2(p, a)
    s = p.read_text(encoding="utf-8")
    for x, y, n in pairs:
        assert s.count(x) == n, (p.name, s.count(x), x[:70]); s = s.replace(x, y)
    assert "allooloo@hey.com" not in s, f"{p.name}: an occurrence is left"
    p.write_text(s, encoding="utf-8", newline=""); print("edited", p)
edit(r"C:\ALLOOLOO\CM-KG\ECO\worker\index.js", [
    # the footer's Support link: the page's own form; allooloo.ai has none, so Allooloo's
    ('<a href="mailto:allooloo@hey.com">Support</a>', '<a href="${host === \'allooloo.ai\' || !host ? \'https://allooloo.io/#contact\' : `https://${host}/#contact`}">Support</a>', 1),
    ('return `<h2>Contact Us</h2><form action="${FORM}"', 'return `<h2 id="contact">Contact Us</h2><form action="${FORM}"', 1),
    # security.txt: allooloo.ai (no form) → Allooloo's form; the regime and country hosts → their own page's form
    ("T(`Contact: mailto:allooloo@hey.com\\nContact: https://allooloo.io/security\\nExpires: 2027-10-24T00:00:00Z", "T(`Contact: https://allooloo.io/#contact\\nContact: https://allooloo.io/security\\nExpires: 2027-10-24T00:00:00Z", 1),
    ("T(`Contact: mailto:allooloo@hey.com\\nContact: https://allooloo.io/security\\nExpires: 2027-10-23T00:00:00Z", "T(`Contact: https://${host}/#contact\\nContact: https://allooloo.io/security\\nExpires: 2027-10-23T00:00:00Z", 2),
])
edit(r"C:\ALLOOLOO\CM-KG\ACM-SIGNALS\worker\index.js", [
    ("T(`Contact: mailto:allooloo@hey.com\\nContact: https://allooloo.io/security", "T(`Contact: https://allooloo.io/#contact\\nContact: https://allooloo.io/security", 1),
])
