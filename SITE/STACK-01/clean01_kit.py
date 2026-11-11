r"""clean01_kit.py — CLEAN-01 item 5 (CEO 2026-11-11: "Content-Signal on the ~105 hosts that state nothing — same policy as the rest of their estate"):
the Allooloo estate states `Content-Signal: search=yes, ai-input=yes, ai-train=yes` in robots.txt on every host that states a policy (516 of 516, read
2026-11-11). robots(t) puts that same line under the `User-agent: *` group of a robots.txt that carries none; a robots.txt that already states a
Content-Signal is returned unchanged. Used by stack_pages.py (post-pass over the bundle) and by the one-off bundle patch."""
import re
LINE = 'Content-Signal: search=yes, ai-input=yes, ai-train=yes'
def robots(t):
    if re.search(r'(?im)^\s*content-signal\s*:', t): return t
    m = re.search(r'(?im)^\s*user-agent\s*:\s*\*\s*$', t)
    if not m: return t
    nl = '\r\n' if '\r\n' in t else '\n'
    return t[:m.end()] + nl + LINE + t[m.end():] if t[m.end():m.end() + 1] in ('\n', '\r') else t[:m.end()] + nl + LINE + nl + t[m.end():]
