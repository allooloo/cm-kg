"""MAIL-01 item 6: the standing ops-address rule, written once into each estate's doctrine (append-only; anchors first)."""
import pathlib, shutil
TAG = ".pre-mail01-2026-11-11"
RULE = """STANDING RULE (CEO, MAIL-01, 2026-11-11) — every sign-up and registration uses the estate's own ops address:
- agent-bev: ops@agent-bev.ai (Cloudflare Email Routing → the CEO's verified destination)
- wefetch: ops@mailfetch.ai (wefetch's system mailbox); wefetch's own mail sends from socials@wefetch.ai
- Allooloo: ops@allooloo.ai (sends through Allooloo's ACS, allooloo-ops-acs)
No new use of allooloo@hey.com anywhere (retired; the HEY account closes 2027-10-08). Public pages carry the site's own contact form, never an email
address (CEO ruling 2026-10-27, "we have contact forms"); security.txt takes an https Contact: line. Never send from gsc-em.com.
The one standing exception until the CEO chooses its replacement: the OPSAGENTS daily close mail still sends from the HEY box."""
def append(p, text, marker):
    p = pathlib.Path(p); a = p.with_name(p.name + TAG)
    if p.exists() and not a.exists(): shutil.copy2(p, a)
    s = p.read_text(encoding="utf-8") if p.exists() else ""
    if marker in s: print("already:", p); return
    p.write_text(s.rstrip("\n") + ("\n\n" if s else "") + text + "\n", encoding="utf-8", newline=""); print("written:", p)
append(r"C:\AGENTBEV\START_ME_UP\START_ME_UP_1_DOCTRINE.md", "- D-18 (MAIL-01, 2026-11-11) " + RULE.replace("\n", "\n  "), "D-18 (MAIL-01")
for root in (r"C:\ALLOOLOO\START_ME_UP", r"C:\GREENCORE\START_ME_UP"):
    append(pathlib.Path(root) / "OPS-ADDRESS-RULE.md", "# OPS-ADDRESS-RULE\n\n" + RULE, "STANDING RULE (CEO, MAIL-01")
