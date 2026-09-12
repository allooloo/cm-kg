"""Pass 2.7 — Mistral (mistral-small-latest) as TRANSLATION AND REVIEW ONLY (CEO rule for the European nodes, 2026-09-11): reading order is
Perplexity (Agent API, low) → Grok → Mistral. Mistral never writes a field. It reads, in the native language, what the first two engines sourced —
the pages Perplexity located and the items Grok found — and CONFIRMS or DISPUTES them (issuer named, date and event kind as stated). Anything Mistral
finds that no engine sourced (an auditor, a registrar, a meeting or period date in a Dutch text) is a FLAG for the Review tab,
never a record value. Label: 'review by Mistral (nl)'. Writes raw/mistral_reads.jsonl (one row per reviewed URL)."""
from fc_common import *
LANG = 'nl'
LABEL = f'review by Mistral ({LANG})'
NATIVE = re.compile(r"(?i)\b(resultaten|jaarverslag|algemene vergadering|dividend|benoeming|persbericht|halfjaar|kwartaal|omzet)\b")
def native(e): return (e.get('language') or '') in ('nl',) or bool(NATIVE.search(e.get('title', '')))
targets = []
for e in events():
    if 'Grok' in (e.get('read_by') or '') and native(e): targets.append({'kind': 'grok_event', 'url': e['url'], 'key': e['exchange'] + '|' + e['ticker'], 'issuer': e['issuer'], 'date': e['date'], 'event_type': e['event_type'], 'title': e.get('title', '')})
for d in jload('raw/grok_live.jsonl') + [x for p in [pond.latest(NODE, 'width1', 'grok_live.jsonl')] if p for x in (json.loads(l) for l in open(p, encoding='utf-8'))]:
    if d.get('url') and native(d) and d['url'] not in [t['url'] for t in targets]: targets.append({'kind': 'grok_event', 'url': d['url'], 'key': d['exchange'] + '|' + d['ticker'], 'issuer': d.get('issuer', ''), 'date': d.get('date', ''), 'event_type': d.get('event_type', ''), 'title': d.get('title', '')})
for d in jload('raw/perplexity_pages.jsonl'):
    if d.get('verified') and d.get('url'): targets.append({'kind': 'perplexity_page', 'url': d['url'], 'key': d['key'], 'issuer': '', 'date': '', 'event_type': '', 'title': d.get('page_title', '')})
issuers = load_issuers(); byk = {key(r): r for r in issuers}
for t in targets:
    if not t['issuer']: t['issuer'] = (byk.get(t['key']) or {}).get('full_name') or (byk.get(t['key']) or {}).get('name') or ''
def fetch(t):
    txt, st = page_text(t['url'])
    if not txt or len(txt) < 200: return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'verdict': 'no_view', 'reason': f'page body not readable ({st})', 'flags': [], 'read_by': LABEL}
    if t['kind'] == 'grok_event':
        q = (f"Issuer: {t['issuer']}. An engine recorded this item from the page below: date {t['date']}, kind {t['event_type']}, headline \"{t['title']}\". "
             "Read the page in its own language and answer: does the page belong to this issuer, is the date the page states the same, is the kind right? "
             'Reply JSON only: {"issuer_named": true|false, "date_on_page": "YYYY-MM-DD or empty", "kind_ok": true|false, "verdict": "confirm|dispute", "reason": "one line in English", '
             '"flags": [{"field": "auditor|registrar|meeting_date|record_date|period_end|other", "value": "", "evidence": "verbatim, native language"}]}')
    else:
        q = (f"Issuer: {t['issuer']}. An engine located this page as the issuer's own investor-relations / announcements page. Read it in its own language and answer: "
             "does the page belong to this issuer (name, register number or ISIN stated)? "
             'Reply JSON only: {"issuer_named": true|false, "verdict": "confirm|dispute", "reason": "one line in English", '
             '"flags": [{"field": "auditor|registrar|meeting_date|record_date|period_end|other", "value": "", "evidence": "verbatim, native language"}]}')
    res = mistral(q + '\n\nPAGE TEXT:\n' + txt[:14000]); j = jparse(res.get('text', '')) or {}
    flags = [f for f in (j.get('flags') or []) if isinstance(f, dict) and f.get('value')]
    return {'kind': t['kind'], 'url': t['url'], 'key': t['key'], 'issuer': t['issuer'], 'issuer_named': j.get('issuer_named'), 'date_on_page': j.get('date_on_page', ''), 'kind_ok': j.get('kind_ok'), 'verdict': j.get('verdict') or 'no_view', 'reason': j.get('reason', ''), 'flags': flags[:6], 'usage': res.get('usage'), 'error': res.get('error'), 'read_by': LABEL}
if __name__ == '__main__':
    print('native-language items to review (Grok events + Perplexity pages):', len(targets), flush=True)
    resume('mistral_reads', fetch, targets[:int(E.get('MISTRAL_MAX', '600'))], threads=4, keyf=lambda t: t['url'])
    rows = jload('raw/mistral_reads.jsonl')
    json.dump({'n_targets': len(targets), 'reviewed': len(rows), 'confirmed': sum(1 for r in rows if r.get('verdict') == 'confirm'), 'disputed': sum(1 for r in rows if r.get('verdict') == 'dispute'), 'flags': sum(len(r.get('flags') or []) for r in rows), 'role': 'translation and review only; never writes a field; flags go to the Review tab'}, open('raw/mistral_count.json', 'w'))
