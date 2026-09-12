"""Pass 2.6 — Grok (grok-4.6, xAI Responses API with web_search + x_search) as the live layer in the weekly refresh: trading halts, suspensions and
reinstatements on exchange and NSX, plus announcements for issuers the sources left silent. Every finding must carry a URL; findings without one are dropped.
Deduped on (exchange, code, type, date, URL) by the assembler. Label: 'read by Grok (live)'. Wired into run_refresh.ps1 (LIVE_HOURS=168)."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
by_name = {norm(r['name']): r for r in issuers}; by_code = {(r['exchange'], r['ticker']): r for r in issuers}
HOURS = int(E.get('LIVE_HOURS', '168'))
def ask(prompt):
    res = grok(prompt); j = jparse(res.get('text', '')) or {}
    return (j.get('items', []) if isinstance(j, dict) else []), res
def halts():
    out = []; usage = []
    for ex, label in [('SIX', 'SIX Swiss Exchange'), ('BX Swiss', 'BX Swiss')]:
        items, res = ask(f"List every trading halt, suspension from quotation and reinstatement to quotation for companies on the {label} announced in the last {HOURS} hours. Use web search and X search. "
                         "Return JSON only: {\"items\": [{\"issuer\": \"legal name\", \"code\": \"exchange symbol\", \"kind\": \"trading_halt|suspension|reinstatement\", \"date\": \"YYYY-MM-DD\", \"title\": \"headline\", \"url\": \"source URL\"}]}. Only items with a real source URL.")
        usage.append(res.get('usage'))
        for it in items:
            r = by_code.get((ex, str(it.get('code', '')).upper())) or by_name.get(norm(it.get('issuer', '')))
            if not r or not str(it.get('url', '')).startswith('http') or not to_iso(it.get('date', '')): continue
            out.append(event(r, 'halt_resume', to_iso(it['date']), it.get('title') or f"{it['kind']} ({ex})", 'Grok live (web + X search)', it['url'], 'read by Grok (live)', detail=it.get('kind', '')))
    return out, usage
def silent(keys_silent):
    out = []; usage = []
    for k in keys_silent:
        r = byk[k]
        items, res = ask(f"List EQS News / SIX ad hoc and press releases issued by {r['name']} (SIX: {r['ticker']}, Switzerland) in the last {HOURS} hours, with the URL of each. Return JSON only: {{\"items\": [{{\"date\": \"YYYY-MM-DD\", \"title\": \"headline\", \"url\": \"URL\"}}]}}. Only real announcements with URLs; empty list if none.")
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
    w1 = pond.open_drop(NODE, 'width1') if pond.drops(NODE, 'width1') else r'C:\ALLOOLOO\CM-KG\RAILS\ch-width1\raw'
    with open(os.path.join(w1, 'grok_live.jsonl'), 'w', encoding='utf-8') as f:
        for e in evs + evs2: f.write(json.dumps(e, ensure_ascii=False) + '\n')
    json.dump({'halts': len(evs), 'newswire': len(evs2), 'issuers_asked': len(sil), 'usage': u1 + u2, 'date': TODAY.isoformat()}, open('raw/grok_live_usage.json', 'w'))
    print('grok live: halts/suspensions/reinstatements', len(evs), 'silent-issuer items', len(evs2), flush=True)
