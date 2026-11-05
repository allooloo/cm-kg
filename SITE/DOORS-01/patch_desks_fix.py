r"""patch_desks_fix.py — DOORS-01 fix: FOR DESKS read live after the purge was short on the route-bound page Workers (a Worker cannot reach another Worker's route on
the same zone, and the check is one per isolate across the hosts it serves; a cold isolate answered before the check ended). The desk check becomes its own:
a get_ door is live when its /mcp.json answers 200, or when its tool is on the tools/list of a node gate (us, ca, uk — any one that answers: the tool is answered
there for every market); a held name has no tool and no door, so it is never listed. Four-second reads, awaited at render up to 4.5 s, five-minute cache, refreshed
behind. .pre-desksfix-2026-11-05 copies beside. Usage: python -X utf8 -I patch_desks_fix.py"""
import pathlib, shutil
W = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker')
def edit(name, pairs, mark):
    p = W / name; pre = W / name.replace('.js', '.pre-desksfix-2026-11-05.js'); s = p.read_text(encoding='utf-8')
    if mark in s: print(name, 'already patched'); return
    if not pre.exists(): shutil.copy2(p, pre)
    for o, n in pairs:
        assert s.count(o) == 1, (name, s.count(o), o[:90]); s = s.replace(o, n)
    p.write_text(s, encoding='utf-8'); print(name, 'patched')
edit('nav02.js', [
  ("  const desks = (await Promise.all(DESKS.map(async ([t, u, mj]) => { try { const r = await fetch(mj, { headers: UA, redirect: 'manual', cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(8000) }); return r.status === 200 ? [t, u] : null; } catch (e) { return null; } }))).filter(Boolean);   // DOORS-01: the get_ doors that answer\n", ""),
  ("  DOORS = { live: nl.length, answering: up.filter(Boolean).length, desks, read_at:", "  DOORS = { live: nl.length, answering: up.filter(Boolean).length, read_at:"),
  ("each live door /mcp.json (the digest\\'s door check); each get_ door /mcp.json for FOR DESKS' };", "each live door /mcp.json (the digest\\'s door check)' };"),
  ("export async function doorCheck(ctx) {",
   "// DOORS-01 fix: the desk check (FOR DESKS) — its own, fast, independent of the node check\n"
   "let DK = null, DK_AT = 0, DK_RUN = null; const GATE_TOOL = { get_issuer: 'resolve_issuer' };\n"
   "async function runDesks() {\n"
   "  const gate = await Promise.any(['https://mcp.us-cm-kg.ai/mcp', 'https://mcp.ca-cm-kg.ai/mcp', 'https://mcp.uk-cm-kg.ai/mcp'].map(g => rpc(g, 'tools/list').then(j => { const t = (j.result && j.result.tools) || []; if (!t.length) throw new Error('no tools'); return new Set(t.map(x => x.name)); }))).catch(() => new Set());\n"
   "  const live = await Promise.all(DESKS.map(async ([t, u, mj]) => { let ok = false; try { const r = await fetch(mj, { headers: UA, redirect: 'manual', cf: { cacheTtl: 300 }, signal: AbortSignal.timeout(4000) }); ok = r.status === 200; } catch (e) { ok = false; } return ok || gate.has(GATE_TOOL[t] || t) ? [t, u] : null; }));\n"
   "  DK = live.filter(Boolean); DK_AT = Date.now(); setDesks(DK); return DK;\n"
   "}\n"
   "export async function deskCheck(ctx) {\n"
   "  if (DK && Date.now() - DK_AT < 300000) return DK;\n"
   "  if (!DK_RUN) { DK_RUN = runDesks().catch(() => DK).finally(() => { DK_RUN = null; }); if (ctx && ctx.waitUntil) ctx.waitUntil(DK_RUN); }\n"
   "  if (DK) return DK;   // stale: answer with the last check, refresh behind\n"
   "  try { return await Promise.race([DK_RUN, new Promise(r => setTimeout(() => r(DK), 4500))]); } catch (e) { return DK; }\n"
   "}\n"
   "export async function doorCheck(ctx) {"),
  ("import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ICONS, ROBOTS, SECURITY, esc, int, today, page, scale, text, json, headers, sitemap, setDoors } from './chrome.js';",
   "import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, ICONS, ROBOTS, SECURITY, esc, int, today, page, scale, text, json, headers, sitemap, setDoors, setDesks } from './chrome.js';"),
], "export async function deskCheck")
edit('chrome.js', [
  ("export const SURFACES_VERSION = '2026-11-05.2';", "export const SURFACES_VERSION = '2026-11-05.3';   // .3 = DOORS-01 fix: FOR DESKS from its own desk check (door /mcp.json, or the tool on a node gate); was 2026-11-05.2\nconst SV_PREV_DESKSFIX = '2026-11-05.2';"),
  ("const FOR_DESKS = () => { const l = (DOORS && DOORS.desks) || [];", "let DESK_LIVE = null; export const setDesks = d => { DESK_LIVE = d; };   // DOORS-01 fix: nav02.deskCheck\nconst FOR_DESKS = () => { const l = DESK_LIVE || [];"),
], "export const setDesks")
edit('protocols.js', [
  ("&& !p.startsWith('/.well-known/')) await N2.doorCheck(ctx);", "&& !p.startsWith('/.well-known/')) await Promise.all([N2.doorCheck(ctx), N2.deskCheck(ctx)]);   // DOORS-01 fix: the desk check beside the door check"),
], "N2.deskCheck(ctx)")
