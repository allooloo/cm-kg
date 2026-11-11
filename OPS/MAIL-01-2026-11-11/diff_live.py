"""MAIL-01: diff a Worker's live main module against the new bundle; print every changed line (shortened). usage: diff_live.py <script> <module>"""
import re, sys, difflib
n, mod = sys.argv[1], sys.argv[2]
s = lambda x: re.sub(r"//# sourceMappingURL.*", "", x).replace("\r\n", "\n").strip().split("\n")
a = s(open(f"C:/AGENTBEV/OPS/BEV-LIB-02-2026-11-10/live_{n}/{mod}", encoding="utf-8").read())
b = s(open(f"C:/AGENTBEV/OPS/BEV-LIB-04-2026-11-10/dry_{n}/{mod}", encoding="utf-8").read())
d = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
print(f"== {n}: {len(d)} changed lines")
for l in d:
    i = l.find("allooloo@hey.com"); j = l.find("#contact")
    k = i if i >= 0 else j if j >= 0 else 0
    print("  " + l[:1] + " …" + l[max(1, k - 70):k + 70])
