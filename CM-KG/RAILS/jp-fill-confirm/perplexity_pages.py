"""Pass 2.5 — Perplexity Agent API (preset 'fast' — ORDER-017 search layer) locates the current company page for issuers whose EQS News / SIX ad hoc search returned
nothing in the window or whose exchange record carried no website — the issuer's own investor-relations / EQS News / SIX ad hoc page — and the page is
verified by fetch. Sources are read from the search_results output item. The page's own title becomes a sourced alias. Label: 'read by Perplexity (agent · low)'."""
import re
from fc_common import *
issuers = load_issuers(); byk = {key(r): r for r in issuers}
rows = {r['_tab'] + '|' + str(r['Symbol']): r for r in all_rows()}
EV = events(); has_ev = set(e['exchange'] + '|' + e['ticker'] for e in EV)
LABEL = 'read by Perplexity (agent · fast)'
def fetch(r):
    prompt = (f"Find the official investor-relations or ad hoc / press-release page for the Tokyo Stock Exchange-listed company {r['name']} (securities code {r['ticker']}, {r['exchange']}; Japanese name {r.get('name_native') or ''}): the company's own website page (Japanese or English). "
              "Reply with JSON only: {\"url\": \"<page URL or empty>\", \"page_title\": \"<title as shown>\", \"note\": \"<one line>\"}.")
    res = perplexity_agent(prompt, preset='fast'); j = jparse(res.get('text', '')) or {}
    u = (j.get('url') or '').strip(); out = {'url': u, 'page_title': j.get('page_title', ''), 'sources': res.get('sources', []), 'usage': res.get('usage'), 'cost': res.get('cost'), 'model': res.get('model'), 'preset': 'fast', 'error': res.get('error'), 'verified': False, 'read_by': LABEL}
    if u.startswith('http'):
        t, st = page_text(u, timeout=40)
        if t and name_match(t[:6000], r['name'])[0] in ('full', 'distinctive'):
            out['verified'] = True
            x = get(u, tries=1, timeout=30)
            tt = re.search(r'<title>(.*?)</title>', x.text, re.S) if x is not None and x.status_code == 200 else None
            title = re.sub(r'\s+', ' ', html.unescape(tt.group(1))).strip() if tt else ''
            nm = re.split(r'\s*(?:\||–|—| - |:|\.\s)\s*', title)[0].strip() if title else ''
            nm = re.sub(r'(?i)\s*(asx announcements|announcements|investor relations|investors|home|share price)\b.*$', '', nm).strip(' .,-')
            nm = re.sub(r'\s*\([A-Z0-9.\-]{1,8}\)\s*$', '', nm).strip()
            if nm and len(nm.split()) <= 6 and norm(nm).replace(' ', '') != norm(r['name']).replace(' ', '') and name_match(nm, r['name'])[0] in ('full', 'distinctive'):
                out['alias'] = nm; out['alias_read_by'] = 'issuer page <title> (found by Perplexity (agent · fast))'
        else: out['verify_status'] = st
    return out
if __name__ == '__main__':
    targets = sorted(issuers, key=lambda r: 0 if key(r) not in has_ev else 1)  # jp-issuers.xlsx carries no website column: every issuer is a target, zero-event issuers first
    targets = targets[:int(E.get('PPLX_MAX', '4000'))]
    print('issuers to locate (no events in window or no website):', len(targets), flush=True)
    resume('perplexity_pages', fetch, targets, threads=int(E.get('THREADS', '4')))
