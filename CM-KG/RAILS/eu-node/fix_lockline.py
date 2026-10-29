r"""fix_lockline.py — rewrite line 5 (the node lock test) of each European harvest script with the node's own lock path."""
import io
for cc in "it es se dk no fi be ie at pl pt lu gr cz".split():
    p = rf"C:\ALLOOLOO\CM-KG\RAILS\{cc}-width1\run_refresh.ps1"
    lines = io.open(p, encoding="utf-8").read().split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith("if (Test-Path") and ".lock'" in l)
    lines[i] = "if (Test-Path 'C:\\ALLOOLOO\\CM-KG\\POND\\%s-cm-kg\\.lock') { '%s-cm-kg locked (build order in flight): refresh skipped'; exit 0 }" % (cc, cc)
    io.open(p, "w", encoding="utf-8").write("\n".join(lines))
print(io.open(r"C:\ALLOOLOO\CM-KG\RAILS\it-width1\run_refresh.ps1", encoding="utf-8").read().split("\n")[4])
