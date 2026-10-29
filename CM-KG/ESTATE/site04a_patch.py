r"""site04a_patch.py — SITE-04A (CEO, 2026-10-28): the own-shell hosts (ORDER-034 country issuer pages + kyp-model.org + issuerwire.org; the DAY ORDER 5 issuer
zones and the EU regime page) take the nav of record and the estate footer exactly as the shared template renders them. Body, look and layout stay as cut.
Routing: the country issuer pages' KYP link goes to getissuer.ai/#issuers. chrome.js gains navHeader()/estateFooter() (page() now renders through them — same
bytes), sovereign034.js and do5.js shells use them, issuer.css gains the shared chrome rules, SURFACES_VERSION → 2026-10-28.3. .pre copies beside every touched file."""
import shutil, re
W = r"C:\ALLOOLOO\CM-KG\ESTATE\worker"; P = r"C:\ALLOOLOO\CM-KG\ESTATE\public"; TAG = "pre-site04a-20261028"
def load(p): shutil.copy2(p, re.sub(r"(\.[a-z]+)$", f".{TAG}\\1", p)); return open(p, encoding="utf-8").read()
def save(p, s): open(p, "w", encoding="utf-8", newline="\n").write(s)
def rep(s, old, new, n=1):
    assert old in s, old[:80]; return s.replace(old, new, n)
# ---- chrome.js
c = load(W + r"\chrome.js")
c = rep(c, "export const SURFACES_VERSION = '2026-10-28.2';", "export const SURFACES_VERSION = '2026-10-28.3';")
OLD_HDR = """<header><div class="bar"><div class="in"><a class="logo" href="${CORPORATE}/" aria-label="Allooloo"><img src="/allooloo-logo.svg" width="160" height="40" alt="Allooloo"></a>
<nav aria-label="Estate"><ul>${NAV.map(([t, u]) => `<li><a href="${u}"${!nocurrent && u.startsWith(`https://${host}/`) ? ' aria-current="page"' : ''}>${t}</a></li>`).join('')}</ul></nav>
<button class="tint" type="button" data-tint aria-label="Light or dark">${icon('moon', 'moon')}${icon('sun', 'sun')}</button><a class="btn primary cta" href="${CTA[1]}">${CTA[0]}${icon('arrow')}</a></div></div>
${hero ? '' : `<div class="in">${ll}</div>`}</header>"""
NEW_HDR = """${navHeader(host, { nocurrent })}${hero ? '' : `<div class="in">${ll}</div>`}</header>"""
c = rep(c, OLD_HDR, NEW_HDR)
OLD_FTR = """<footer><section class="band" aria-label="Allooloo"><p class="tag">${esc(TAGLINE)}</p><p>${esc(BAND)}</p></section>${host === 'allooloo.io' ? `<p class="line">${OPERATOR} · 260-4611 Viking Way, Richmond, BC V6V 2K9, Canada</p>` : ''}<p class="row">${FOOTER_ROW}</p></footer>"""
c = rep(c, OLD_FTR, "${estateFooter(host)}")
HELPERS = """
// SITE-04A (2026-10-28): the nav of record and the estate footer as one kit, so the own-shell hosts (ORDER-034, DAY ORDER 5) render them byte-for-byte as the shared template does.
// navHeader opens <header> and closes the .bar; the caller closes </header>. kyp: the KYP link's href on a country issuer page (getissuer.ai/#issuers by the order).
export function navHeader(host, { nocurrent, kyp } = {}) {
  return `<header><div class="bar"><div class="in"><a class="logo" href="${CORPORATE}/" aria-label="Allooloo"><img src="/allooloo-logo.svg" width="160" height="40" alt="Allooloo"></a>
<nav aria-label="Estate"><ul>${NAV.map(([t, u]) => `<li><a href="${t === 'KYP' && kyp ? kyp : u}"${!nocurrent && u.startsWith(`https://${host}/`) ? ' aria-current="page"' : ''}>${t}</a></li>`).join('')}</ul></nav>
<button class="tint" type="button" data-tint aria-label="Light or dark">${icon('moon', 'moon')}${icon('sun', 'sun')}</button><a class="btn primary cta" href="${CTA[1]}">${CTA[0]}${icon('arrow')}</a></div></div>
`;
}
export function estateFooter(host) {
  return `<footer><section class="band" aria-label="Allooloo"><p class="tag">${esc(TAGLINE)}</p><p>${esc(BAND)}</p></section>${host === 'allooloo.io' ? `<p class="line">${OPERATOR} · 260-4611 Viking Way, Richmond, BC V6V 2K9, Canada</p>` : ''}<p class="row">${FOOTER_ROW}</p></footer>`;
}
"""
c = rep(c, "export function page({", HELPERS.lstrip("\n") + "export function page({")
save(W + r"\chrome.js", c)
# ---- sovereign034.js (ORDER-034 shell: the twelve country issuer pages + kyp-model.org + issuerwire.org)
s = load(W + r"\sovereign034.js")
s = rep(s, "import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ROBOTS, SECURITY, regionAzure, esc, int, today, headers, sitemap, form } from './chrome.js';",
        "import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ROBOTS, SECURITY, regionAzure, esc, int, today, headers, sitemap, form, navHeader, estateFooter, SPRITE } from './chrome.js';   // SITE-04A: the nav of record + the estate footer")
s = rep(s, "function shell({ host, title, desc, h1, state, asOf, body, sp }) {", "function shell({ host, title, desc, h1, state, asOf, body, sp, kyp }) {")
s = rep(s, """</head><body>
<header><a class="logo" href="${CORPORATE}/" aria-label="Allooloo"><img src="/allooloo-logo.svg" width="160" height="40" alt="Allooloo"></a><span>&nbsp;·&nbsp;${esc(host)}</span></header>
<main><h1>${esc(h1)}</h1><p class="state">${esc(state)} · as of ${esc(asOf || today())} · surfaces ${esc(SURFACES_VERSION)}</p>${body}
<h2>Contact</h2>${form(host)}</main>
<footer>${esc(sp(`${OPERATOR} · public-record only · no prices, no quotes, no licensed market data · `))}<a href="${CONTACT}">contact form</a> · <a href="${CORPORATE}/">allooloo.io</a> · <a href="/llms.txt">llms.txt</a> · <a href="https://kyp-model.org/">kyp-model.org</a> · <a href="https://issuerwire.org/">issuerwire.org</a> · © 2026</footer>
</body></html>`;""", """</head><body>${SPRITE}
${navHeader(host, { nocurrent: true, kyp })}</header>
<main><h1>${esc(h1)}</h1><p class="state">${esc(state)} · as of ${esc(asOf || today())} · surfaces ${esc(SURFACES_VERSION)}</p>${body}
<h2>Contact</h2>${form(host)}</main>
${estateFooter(host)}<script src="/webmcp.js"></script></body></html>`;""")
save(W + r"\sovereign034.js", s)
# ---- do5.js (DAY ORDER 5 shell: the ten own issuer zones, the thirteen European subdomains, eu-issuer.ai; the cm-kg node surfaces share the shell)
d = load(W + r"\do5.js")
d = rep(d, "import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ROBOTS, SECURITY, esc, int, today, headers, sitemap, form } from './chrome.js';",
        "import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ROBOTS, SECURITY, esc, int, today, headers, sitemap, form, navHeader, estateFooter, SPRITE } from './chrome.js';   // SITE-04A: the nav of record + the estate footer")
d = rep(d, "function shell({ host, title, desc, h1, state, asOf, body }) {", "function shell({ host, title, desc, h1, state, asOf, body, kyp }) {")
d = rep(d, """</head><body>
<header><a class="logo" href="${CORPORATE}/" aria-label="Allooloo"><img src="/allooloo-logo.svg" width="160" height="40" alt="Allooloo"></a><span>&nbsp;·&nbsp;${esc(host)}</span></header>
<main><h1>${esc(h1)}</h1><p class="state">${esc(state)} · as of ${esc(asOf || today())} · surfaces ${esc(VERSION5)}</p>${body}
<h2>Contact</h2>${form(host)}</main>
<footer>${esc(OPERATOR)} · public-record only · no prices · <a href="${CONTACT}">contact form</a> · <a href="${CORPORATE}/">allooloo.io</a> · <a href="/llms.txt">llms.txt</a> · © 2026</footer>
</body></html>`;""", """</head><body>${SPRITE}
${navHeader(host, { nocurrent: true, kyp })}</header>
<main><h1>${esc(h1)}</h1><p class="state">${esc(state)} · as of ${esc(asOf || today())} · surfaces ${esc(SURFACES_VERSION)}</p>${body}
<h2>Contact</h2>${form(host)}</main>
${estateFooter(host)}<script src="/webmcp.js"></script></body></html>`;""")
save(W + r"\do5.js", d)
# ---- issuer.css: the shared chrome rules (header bar, nav, tint, CTA, footer band) appended from estate.css, verbatim; the two-colour body rules stay
e = open(P + r"\estate.css", encoding="utf-8").read()
def rule(sel):
    m = re.search(re.escape(sel) + r"\{[^}]*\}", e); assert m, sel; return m.group(0)
root = re.search(r":root\{[^}]*\}", e).group(0); dark = re.search(r"@media \(prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{[^}]*\}\}", e).group(0); themed = re.search(r":root\[data-theme=\"dark\"\]\{[^}]*\}", e).group(0)
sels = [".in,main,footer", "header", ".bar", ".bar .in", ".logo", ".logo img", "nav", "nav ul", "nav a", "nav a:hover", "nav a[aria-current]", ".tint", ".tint:hover", ".tint .sun", ".btn,form button[type=submit]", ".btn.primary,form button[type=submit]", ".btn.primary .ic", ".btn:hover,form button[type=submit]:hover", ".btn .ic", ".cta", ".sprite", ".ic", "footer", ".band", ".band p", ".band .tag", "footer .line,footer .row", "footer a"]
block = "\n/* SITE-04A (2026-10-28): the nav of record and the estate footer, the shared template's rules verbatim (estate.css); the page body keeps the two-colour cut above. */\n" + root + "\n" + dark + "\n" + themed + "\n" + "\n".join(rule(x) for x in sels) + "\n" + \
        'html[data-theme="light"]{color-scheme:light}html[data-theme="dark"]{color-scheme:dark}\n' + \
        '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .logo img{content:url(/allooloo-logo-dark.svg)}:root:not([data-theme="light"]) .tint .sun{display:block}:root:not([data-theme="light"]) .tint .moon{display:none}}\n' + \
        ':root[data-theme="dark"] .logo img{content:url(/allooloo-logo-dark.svg)}:root[data-theme="dark"] .tint .sun{display:block}:root[data-theme="dark"] .tint .moon{display:none}\n' + \
        '@media (max-width:760px){nav{order:3;flex-basis:100%;margin-left:0}nav ul{gap:.2rem 1.4rem}.tint{margin-left:auto}.bar .in{gap:.4rem .75rem}}\n' + \
        'footer{border-top:0}\n'
i = load(P + r"\issuer.css"); save(P + r"\issuer.css", i.rstrip("\n") + "\n" + block)
print("patched chrome.js, sovereign034.js, do5.js, issuer.css; SURFACES_VERSION 2026-10-28.3")
