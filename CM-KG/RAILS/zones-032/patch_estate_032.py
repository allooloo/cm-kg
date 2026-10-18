r"""ORDER-032 C.4 — add the agent-swap.ai family to the estate Worker (CM-KG\ESTATE\worker): doors027.js (family), surfaces.js (live data + script-free
page), chrome.js (SURFACES_VERSION). .pre-032-20261018 copies beside each file; refuses to run twice (anchors must match exactly once)."""
import os, shutil
W = r'C:\ALLOOLOO\CM-KG\ESTATE\worker'
def load(fn):
    p = os.path.join(W, fn); pre = p + '.pre-032-20261018'
    if not os.path.exists(pre): shutil.copy2(p, pre)
    return p, open(p, encoding='utf-8').read()
def sub(s, a, b, fn):
    n = s.count(a)
    if n != 1: raise SystemExit(f'{fn}: anchor found {n} times: {a[:80]!r}')
    return s.replace(a, b)

# ---- doors027.js
p, s = load('doors027.js')
s = sub(s, "const GI = 'https://getissuer.ai';", "const GI = 'https://getissuer.ai';\nconst SWAP = 'https://agent-swap.ai';", 'doors027.js')
s = sub(s, "  if ((m = h.match(/^cite-(fact|dd)\\.(ai|com)$/))) return m[2] === 'ai' ? { kind: 'cite', which: m[1] } : { kind: 'redirect', canonical: `https://cite-${m[1]}.ai`, status: 301 };\n  return null;",
           "  if ((m = h.match(/^cite-(fact|dd)\\.(ai|com)$/))) return m[2] === 'ai' ? { kind: 'cite', which: m[1] } : { kind: 'redirect', canonical: `https://cite-${m[1]}.ai`, status: 301 };\n"
           "  if (/^agent-swap\\.(ai|com|io|org|co\\.uk)$/.test(h)) return h === 'agent-swap.ai' ? { kind: 'swap' } : { kind: 'redirect', canonical: SWAP, status: 301 };   // ORDER-032 C.4\n  return null;", 'doors027.js')
s = sub(s, "export const isNew = c => c && (c.kind === 'duty' || c.kind === 'getissuer' || c.kind === 'cite');",
           "export const isNew = c => c && (c.kind === 'duty' || c.kind === 'getissuer' || c.kind === 'cite' || c.kind === 'swap');", 'doors027.js')
s = sub(s, "export function label27(c) { return c.kind === 'duty' ?", "export function label27(c) { if (c.kind === 'swap') return SWAP_COPY.title; return c.kind === 'duty' ?", 'doors027.js')
s = sub(s, "export function desc27(c, live) {", "export function desc27(c, live) {\n  if (c.kind === 'swap') return SWAP_COPY.desc;", 'doors027.js')
s = sub(s, "export function pageArgs27(c, ctx, host) {",
           "export function pageArgs27(c, ctx, host) {\n  if (c.kind === 'swap') { const d = ctx.swap || { rows: [], swap_log: [], at: new Date().toISOString() }; return { title: SWAP_COPY.title, h1: SWAP_COPY.h1, state: 'live', asOf: d.at.slice(0, 10), body: swapBody(d, host), meta: { node: 'estate', as_of: d.at.slice(0, 10) } }; }", 'doors027.js')
s = sub(s, "export function facts27(c, host, live) { return c.kind === 'duty'",
           "export function facts27(c, host, live, ctx) { if (c.kind === 'swap') return swapFacts((ctx && ctx.swap) || { rows: [], swap_log: [], at: new Date().toISOString() }, host); return c.kind === 'duty'", 'doors027.js')
s = sub(s, "export function llms27(c, host, live) { return c.kind === 'duty'",
           "export function llms27(c, host, live, ctx) { if (c.kind === 'swap') return swapLlms((ctx && ctx.swap) || { rows: [], swap_log: [], at: new Date().toISOString() }, host); return c.kind === 'duty'", 'doors027.js')
s = sub(s, "export function paths27(c) { return (c.kind === 'getissuer'",
           "export function paths27(c) { if (c.kind === 'swap') return ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt']; return (c.kind === 'getissuer'", 'doors027.js')
s += open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swap_family.js'), encoding='utf-8').read()
open(p, 'w', encoding='utf-8').write(s); print('doors027.js: agent-swap family')

# ---- surfaces.js
p, s = load('surfaces.js')
s = sub(s, "      const a = D27.pageArgs27(c, ctx, host); const meta = a.meta; const paths = D27.paths27(c);",
           "      if (c.kind === 'swap') ctx.swap = await D27.swapData(env, url);   // ORDER-032 C.4: the serving cloud per node, live at render\n"
           "      const a = D27.pageArgs27(c, ctx, host); const meta = a.meta; const paths = D27.paths27(c);", 'surfaces.js')
s = sub(s, "      if (p === '/llms.txt') return text(D27.llms27(c, host, live), meta);\n      if (p === '/facts.json') return json(D27.facts27(c, host, live), meta);",
           "      if (p === '/llms.txt') return text(D27.llms27(c, host, live, ctx), meta, c.kind === 'swap' ? 'public, max-age=60' : undefined);\n"
           "      if (p === '/facts.json') return json(D27.facts27(c, host, live, ctx), meta, c.kind === 'swap' ? 'public, max-age=60' : undefined);", 'surfaces.js')
a = "      if (p === '/') return HTML(page({ host, title: a.title, desc: desc0, h1: a.h1, state: a.state, asOf: a.asOf, body: a.body, jsonld:"
if s.count(a) != 1: raise SystemExit('surfaces.js: page anchor')
i = s.index(a); j = s.index('\n', i); line = s[i:j]
k = line.rfind('), meta)')
if k < 0: raise SystemExit('surfaces.js: meta close not found in the D27 page line')
line2 = line[:k] + ')' + line[k:]
line2 = line2.replace("return HTML(page({", "return HTML((c.kind === 'swap' ? D27.stripScripts : (x => x))(page({", 1)
s = s[:i] + line2 + s[j:]
open(p, 'w', encoding='utf-8').write(s); print('surfaces.js: swap data + script-free page')

# ---- chrome.js
p, s = load('chrome.js')
s = sub(s, "export const SURFACES_VERSION = '2026-10-17.1';", "export const SURFACES_VERSION = '2026-10-18.1';   // ORDER-032 C.4 (2026-10-18): agent-swap.ai; was 2026-10-17.1", 'chrome.js')
open(p, 'w', encoding='utf-8').write(s); print('chrome.js: SURFACES_VERSION 2026-10-18.1')
