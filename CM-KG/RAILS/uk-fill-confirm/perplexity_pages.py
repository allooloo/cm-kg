"""Pass 2.5 — Perplexity Agent API (preset 'low', grounded) locates the current regulatory-news page for issuers whose Investegate page was missing
(HTTP 404 / no announcements in the window) — the issuer's own investor-relations RNS page or its Investegate / LSE news page — and the page is
verified by fetch. Sources are read from the search_results item of the response's output array; the answer's URL must be among them or verify by fetch.
The display name that page shows becomes a sourced alias (the page is the issuer's own listing); Perplexity's own wording is never an alias.
Label: 'read by Perplexity (agent · low)'. Migrated from sonar-pro on 2026-09-11 (Sonar Chat Completions retire 2026-09-27)."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
inv = {d['key']: d for d in jload(W1 + r'\investegate.jsonl')}
LABEL = 'read by Perplexity (agent · low)'
def fetch(r):
    prompt = (f"Find the official regulatory news (RNS) page for the UK-listed company {r['name']} (ticker {r['ticker']} on {r['exchange']}): its investor-relations 'regulatory news' / 'RNS announcements' page on the company's own website, "
              "or its company page on investegate.co.uk or londonstockexchange.com. Reply with JSON only: {\"url\": \"<page URL or empty>\", \"page_title\": \"<title as shown>\", \"note\": \"<one line>\"}.")
    res = perplexity_agent(prompt, preset='low'); j = jparse(res.get('text', '')) or {}
    u = (j.get('url') or '').strip(); out = {'url': u, 'page_title': j.get('page_title', ''), 'sources': res.get('sources', []), 'usage': res.get('usage'), 'cost': res.get('cost'), 'model': res.get('model'), 'preset': 'low', 'error': res.get('error'), 'verified': False, 'read_by': LABEL}
    if u.startswith('http'):
        t, st = page_text(u, timeout=40)
        if t and name_match(t[:6000], r['name'])[0] in ('full', 'distinctive'):
            out['verified'] = True
            x = get(u, tries=1, timeout=30)
            tt = re.search(r'<title>(.*?)</title>', x.text, re.S) if x is not None and x.status_code == 200 else None
            title = re.sub(r'\s+', ' ', html.unescape(tt.group(1))).strip() if tt else ''
            nm = re.split(r'\s*(?:\||–|—| - |:|\.\s)\s*', title)[0].strip() if title else ''
            nm = re.sub(r'(?i)\s*(regulatory news|rns announcements|rns|announcements|news|share price|investor relations|\(di\))\b.*$', '', nm).strip(' .,-')
            nm = re.sub(r'\s*\([A-Z0-9.\-]{1,8}\)\s*$', '', nm).strip()
            if nm and len(nm.split()) <= 6 and norm(nm).replace(' ', '') != norm(r['name']).replace(' ', '') and name_match(nm, r['name'])[0] in ('full', 'distinctive'):
                out['alias'] = nm; out['alias_read_by'] = f'issuer news page <title> (found by Perplexity (agent · low))'
        else: out['verify_status'] = st
    return out
if __name__ == '__main__':
    targets = [r for r in issuers if (inv.get(key(r)) or {}).get('gap') or (inv.get(key(r)) or {}).get('n', 0) == 0]
    print('issuers with a missing/empty Investegate page:', len(targets), flush=True)
    resume('perplexity_pages', fetch, targets, threads=int(E.get('THREADS', '4')))
