r"""SHELF-01 — the seven ZONES-03 pages show, per tool, the markets live read from the ledger (shelf/state.json, written by the apex job's auto.py before
the estate deploy), and flip to 'served' with the tool's own call once it is live; until then the page says what is callable today, as before."""
import re
p = r'C:\ALLOOLOO\CM-KG\ESTATE\worker\zones03.js'
s = open(p, encoding='utf-8').read()
TOOL = {'replay': 'replay', 'bench': 'bench', 'review': 'review', 'score': 'score', 'timeline': 'timeline', 'events': 'events', 'cleanroom': 'cleanroom'}
CALL = {
 'replay': "`On a market door: <pre>${call('get_record', { identifier: exAt(ctx, 'us'), as_of: '2023-06-30' })}</pre> — the record as it stood on that date, from the sealed market-year (manifest id and year signature on the answer); a date in a year not sealed answers 'not sealed'.`",
 'score': "`On a market door: <pre>${call('get_score', { identifier: exAt(ctx, 'us') })}</pre> — cadence, latency and silence, each with its exchange and sector percentile.`",
 'bench': "`At <code>https://mcp.data-bench.ai/mcp</code>: <code>get_bench</code> for the questions, <code>score_bench</code> for a signed scorecard; the answers never leave that door.`",
 'review': "`At <code>https://mcp.data-review.ai/mcp</code>: <code>get_review</code> — the signed review of a market-year.`",
 'timeline': "`On a market door: <pre>${call('get_timeline', { identifier: exAt(ctx, 'au') })}</pre> — every line on the record, oldest first, no window cap, each line signed.`",
 'events': "`On a market door: <pre>${call('list_events', { type: 'delisting', since: '2026-09-01' })}</pre> — with the register's type map and its gaps.`",
}
helper = """  // SHELF-01: per tool, the markets live read from the ledger (ctx.shelf = /shelf/state.json); a door tool is served once a market door lists it
  const liveOf = (ctx, t) => { const st = ctx.shelf || {}; if (t === 'timeline' || t === 'events') { const ms = ((st.door_tools || {})[t === 'timeline' ? 'get_timeline' : 'list_events']) || []; return ms.map(m => [m, null]); }
    return Object.entries(((st.tools || {})[t]) || {}).map(([m, ys]) => [m, ys]); };
  const liveLine = (ctx, t) => { const L = liveOf(ctx, t); return `<p class="src">Markets live for this tool, read from the ledger: ${L.length ? L.map(([m, ys]) => esc(m) + (ys && ys.length ? ` (${esc(String(Math.min(...ys)))}–${esc(String(Math.max(...ys)))})` : '')).join(' · ') : 'none yet'}${ctx.shelf && ctx.shelf.updated_utc ? ' · read ' + esc(ctx.shelf.updated_utc.slice(0, 16).replace('T', ' ')) + ' UTC' : ''}</p>`; };
  const isLive = (ctx, t) => liveOf(ctx, t).length > 0;
  const pending = (ctx, t, n, items) => isLive(ctx, t) ? '' : `<h2>${n} Not answered on a door yet</h2>` + num(n, items);
"""
s = s.replace("  const who = (t, items) => `<h2>${t}</h2>` + num('W', items);", "  const who = (t, items) => `<h2>${t}</h2>` + num('W', items);\n" + helper, 1)
n_p = 0
for k in ['replay', 'bench', 'review', 'score', 'timeline', 'events']:
    a = s.index(f'    {k}: {{'); b = s.index('${payBlock(', a); seg = s[a:b]
    seg2 = re.sub(r"<h2>2 Not answered on a door yet</h2>\$\{num\(2, (\[.*?\])\)\}", lambda m: "${pending(ctx, '" + k + "', 2, " + m.group(1) + ")}", seg, flags=re.S)
    seg2 = seg2.replace("<h2>1 Callable today</h2>${num(1, [", "${liveLine(ctx, '" + k + "')}<h2>1 Callable today</h2>${num(1, [...(isLive(ctx, '" + k + "') ? [" + CALL[k] + "] : []), ", 1)
    if seg2 != seg: n_p += 1
    s = s[:a] + seg2 + s[b:]
a = s.index('    cleanroom: {'); b = s.index('${payBlock(', a); seg = s[a:b]
s = s[:a] + seg.replace("<h2>2 Price</h2>", "${liveLine(ctx, 'bench')}<h2>2 Price</h2>", 1) + s[b:]
open(p, 'w', encoding='utf-8').write(s)
print('pages patched', n_p)
