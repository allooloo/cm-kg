r"""patch_ref01.py — REF-01 (CEO chain 2, 2026-10-28): the country compliance-object pages take the chain. On every market page (the fr-eco.ai family, every
TLD the Worker serves) one line at the top of the duty block — "Member <n> of 49 under SM-ECO-10060 · <cc>-eco-10060.org" (link; n = registry order, read from
the registry of record at patch time; a market not in the registry prints "Served by Allooloo; not yet a registry member") — and one line at its foot —
"Receipts for decisions cleared in this market: rco-a2a.ai" (link). The EU regime page (eu-eco.ai) takes member 1. No other text changes. VERSION → 2026-10-28.2.
.pre copy beside. The Worker change rides the eco-refresh image (job\build_context.sh → acr build → job update) so the Sunday run keeps it."""
import json, shutil
REG = json.load(open(r"C:\GREENCORE\PROTOCOLS\_canon\registry\estate.json", encoding="utf-8"))
order = [m["cc"].lower() for arr in REG["jurisdictional_nodes"]["regions"].values() for m in arr]; assert len(order) == 49
p = r"C:\ALLOOLOO\CM-KG\ECO\worker\index.js"; shutil.copy2(p, r"C:\ALLOOLOO\CM-KG\ECO\worker\index.pre-ref01-20261028.js"); s = open(p, encoding="utf-8").read()
def rep(old, new):
    global s; assert old in s, old[:70]; s = s.replace(old, new, 1)
rep("const VERSION = '2026-10-28.1';", "const VERSION = '2026-10-28.2';   // REF-01 (2026-10-28): the member line at the top of the duty block, the receipts line at its foot, every market page + the EU regime page")
rep("const NM = Object.keys(MARKETS).length;", "const NM = Object.keys(MARKETS).length;\n"
    "// REF-01 (2026-10-28): the SM-ECO-10060 registry order (apex sm-eco-10060.org; 49 members, EU = 1 … ZA = 49), from C:\\GREENCORE\\PROTOCOLS\\_canon\\registry\\estate.json at patch time\n"
    "const REF01 = " + json.dumps({cc: i + 1 for i, cc in enumerate(order)}, separators=(", ", ": ")) + ";\n"
    "const memberLine = cc => REF01[cc] ? `<p class=\"meta\">Member ${REF01[cc]} of 49 under SM-ECO-10060 · <a href=\"https://${cc}-eco-10060.org/\">${cc}-eco-10060.org</a></p>` : '<p class=\"meta\">Served by Allooloo; not yet a registry member</p>';\n"
    "const RECEIPTS_LINE = '<p class=\"meta\">Receipts for decisions cleared in this market: <a href=\"https://rco-a2a.ai/\">rco-a2a.ai</a></p>';")
# the market page: the duty block is "The record" (the table + the door line)
rep("""<h2>The record</h2>
<table><thead><tr><th>Field</th><th>Value</th><th>Source</th></tr></thead><tbody>
${FIELDS.map(([k, l]) => fieldRow(k, l, m.fields[k])).join('\\n')}""", """<h2>The record</h2>
${memberLine(cc)}
<table><thead><tr><th>Field</th><th>Value</th><th>Source</th></tr></thead><tbody>
${FIELDS.map(([k, l]) => fieldRow(k, l, m.fields[k])).join('\\n')}""")
rep("""${st.live && n && n.regional_door ? `<p class="meta">Issuer records for this market: ${link(n.regional_door)}</p>` : ''}
<h2>ACM-68000 signals — issuer states</h2>""", """${st.live && n && n.regional_door ? `<p class="meta">Issuer records for this market: ${link(n.regional_door)}</p>` : ''}
${RECEIPTS_LINE}
<h2>ACM-68000 signals — issuer states</h2>""")
# the EU regime page: the duty block is "The regime"
rep("""<h2>The regime</h2>
<table><thead><tr><th>Field</th><th>Value</th><th>Source</th></tr></thead><tbody>
${RFIELDS.map(([k, l]) => fieldRow(k, l, m.fields[k])).join('\\n')}
</tbody></table>""", """<h2>The regime</h2>
${memberLine('eu')}
<table><thead><tr><th>Field</th><th>Value</th><th>Source</th></tr></thead><tbody>
${RFIELDS.map(([k, l]) => fieldRow(k, l, m.fields[k])).join('\\n')}
</tbody></table>
${RECEIPTS_LINE}""")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched index.js: REF01 map", len(order), "members; VERSION 2026-10-28.2")
