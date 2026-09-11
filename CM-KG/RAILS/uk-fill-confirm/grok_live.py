"""Pass 2.6 — Grok (grok-4.6, xAI Responses API with web_search + x_search) as the live layer in the weekly refresh: suspensions, restorations and
cancellations on the LSE Main Market, AIM and Aquis, plus regulatory news for issuers the sources left silent in the window. Every finding must carry
a URL from Grok's citations; findings without one are dropped. Deduped on (exchange, ticker, type, date, URL) by the assembler. Label: 'read by Grok (live)'.
Wired into run_refresh.ps1 (LIVE_HOURS=168); one validation query on the backfill day, no backfill events written."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
by_name = {norm(r['name']): r for r in issuers}; by_tick = {(r['exchange'], r['ticker']): r for r in issuers}
HOURS = int(E.get('LIVE_HOURS', '168'))
def ask(prompt):
    res = grok(prompt); j = jparse(res.get('text', '')) or {}
    return (j.get('items', []) if isinstance(j, dict) else []), res
def halts():
    out = []; usage = []
    for ex, label in [('LSE Main Market', 'London Stock Exchange Main Market'), ('AIM', 'AIM (London Stock Exchange)'), ('Aquis Stock Exchange', 'Aquis Stock Exchange (AQSE)')]:
        items, res = ask(f"List every suspension of trading, restoration of trading and cancellation of admission for companies on the {label} announced in the last {HOURS} hours (RNS headlines 'Suspension', 'Restoration', 'Cancellation'). "
                         "Use web search and X search. Return JSON only: {\"items\": [{\"issuer\": \"legal name\", \"ticker\": \"TIDM\", \"kind\": \"suspension|restoration|cancellation\", \"date\": \"YYYY-MM-DD\", \"title\": \"headline\", \"url\": \"source URL\"}]}. Only items with a real source URL.")
        usage.append(res.get('usage'))
        for it in items:
            r = by_tick.get((ex, str(it.get('ticker', '')).upper())) or by_name.get(norm(it.get('issuer', '')))
            if not r or not str(it.get('url', '')).startswith('http') or not to_iso(it.get('date', '')): continue
            out.append(event(r, 'halt_resume', to_iso(it['date']), it.get('title') or f"{it['kind']} ({ex})", 'Grok live (web + X search)', it['url'], 'read by Grok (live)', detail=it.get('kind', '')))
    return out, usage
def silent(keys_silent):
    out = []; usage = []
    for k in keys_silent:
        r = byk[k]
        items, res = ask(f"List regulatory announcements (RNS) and press releases issued by {r['name']} ({r['exchange']}: {r['ticker']}) in the last {HOURS} hours, with the URL of each. "
                         "Return JSON only: {\"items\": [{\"date\": \"YYYY-MM-DD\", \"title\": \"headline\", \"url\": \"URL\"}]}. Only real announcements with URLs; empty list if none.")
        usage.append(res.get('usage'))
        for it in items:
            u = str(it.get('url', ''))
            if not u.startswith('http') or not to_iso(it.get('date', '')): continue
            if name_match(it.get('title', ''), r['name'])[0] not in ('full', 'distinctive'): continue
            out.append(event(r, classify(it.get('title', '')), to_iso(it['date']), it['title'], wire_of(u) or 'issuer news (Grok)', u, 'read by Grok (live)', wire=wire_of(u)))
    return out, usage
if __name__ == '__main__':
    evs, u1 = halts()
    cutoff = (TODAY - datetime.timedelta(hours=HOURS)).isoformat()
    recent = set(e['exchange'] + '|' + e['ticker'] for e in events() if e['date'] >= cutoff)
    sil = [k for k in byk if k not in recent][:int(E.get('LIVE_MAX_ISSUERS', '200'))]
    evs2, u2 = silent(sil) if E.get('LIVE_SILENT', '1') == '1' else ([], [])
    with open(W1 + r'\grok_live.jsonl', 'w', encoding='utf-8') as f:
        for e in evs + evs2: f.write(json.dumps(e, ensure_ascii=False) + '\n')
    json.dump({'halts': len(evs), 'newswire': len(evs2), 'issuers_asked': len(sil), 'usage': u1 + u2, 'date': TODAY.isoformat()}, open('raw/grok_live_usage.json', 'w'))
    print('grok live: suspensions/restorations', len(evs), 'silent-issuer news', len(evs2), flush=True)
