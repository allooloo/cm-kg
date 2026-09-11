"""Pass 2.6 — Grok (grok-4.6, xAI Responses API with web_search + x_search) as the 48-hour live layer in the daily refresh:
halts and resumes per exchange, and newswire releases for issuers the wires and bulletins left silent. Every finding must
carry a URL from Grok's citations; findings without one are dropped. Deduped on the existing key (exchange, ticker, type, date,
URL) by the assembler. Label: 'read by Grok (live)'. Wired into run_refresh.ps1 from 2026-09-11; not run for the backfill."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
by_name = {norm(r['name']): r for r in issuers}; by_tick = {(r['exchange'], r['root']): r for r in issuers}
HOURS = int(E.get('LIVE_HOURS', '48'))
def ask(prompt):
    res = grok(prompt)
    j = jparse(res.get('text', '')) or {}
    return j.get('items', []) if isinstance(j, dict) else [], res
def halts():
    out = []; usage = []
    for ex in ['TSX', 'TSX Venture Exchange', 'Canadian Securities Exchange (CSE)', 'Cboe Canada']:
        items, res = ask(f"List every trading halt and every resumption of trading for securities listed on the {ex} announced in the last {HOURS} hours. "
                         "Use web search and X search. Return JSON only: {\"items\": [{\"issuer\": \"legal name\", \"ticker\": \"symbol\", \"kind\": \"halt|resume\", \"date\": \"YYYY-MM-DD\", \"title\": \"headline\", \"url\": \"source URL\"}]}. Only items with a real source URL.")
        usage.append(res.get('usage'))
        for it in items:
            r = by_tick.get((ex.split()[0] if ex.startswith('TSX V') is False else 'TSXV', str(it.get('ticker', '')).split('.')[0].upper()))
            r = r or by_name.get(norm(it.get('issuer', '')))
            if not r or not str(it.get('url', '')).startswith('http') or not to_iso(it.get('date', '')): continue
            out.append(event(r, 'halt_resume', to_iso(it['date']), it.get('title') or f"{it['kind']} ({ex})", 'Grok live (web + X search)', it['url'], 'read by Grok (live)', detail=it.get('kind', '')))
    return out, usage
def silent_newswire(keys_silent):
    out = []; usage = []
    for k in keys_silent:
        r = byk[k]
        items, res = ask(f"List press releases issued by {r['name']} ({r['exchange']}: {r['ticker']}) in the last {HOURS} hours, with the newswire URL of each. "
                         "Return JSON only: {\"items\": [{\"date\": \"YYYY-MM-DD\", \"title\": \"headline\", \"url\": \"newswire URL\"}]}. Only real releases with URLs; empty list if none.")
        usage.append(res.get('usage'))
        for it in items:
            u = str(it.get('url', ''))
            if not u.startswith('http') or not wire_of(u) or not to_iso(it.get('date', '')): continue
            if name_match(it.get('title', ''), r['name'])[0] not in ('full', 'distinctive'): continue
            out.append(event(r, classify(it.get('title', '')), to_iso(it['date']), it['title'], wire_of(u), u, 'read by Grok (live)', wire=wire_of(u)))
    return out, usage
if __name__ == '__main__':
    from common import event
    evs, u1 = halts()
    cutoff = (TODAY - datetime.timedelta(hours=HOURS)).isoformat()
    recent = set(e['exchange'] + '|' + e['ticker'] for e in events() if e['date'] >= cutoff)
    silent = [k for k in byk if k not in recent][:int(E.get('LIVE_MAX_ISSUERS', '300'))]
    evs2, u2 = silent_newswire(silent)
    with open('raw/grok_live.jsonl', 'w', encoding='utf-8') as f:
        for e in evs + evs2: f.write(json.dumps(e, ensure_ascii=False) + '\n')
    json.dump({'halts': len(evs), 'newswire': len(evs2), 'issuers_asked': len(silent), 'usage': u1 + u2}, open('raw/grok_live_usage.json', 'w'))
    print('grok live: halts/resumes', len(evs), 'newswire', len(evs2), flush=True)
