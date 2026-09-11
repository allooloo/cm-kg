"""Pass 2.1b — re-run the wire title match with legal name OR sourced alias for (a) the issuers Width 1 left with zero events
and (b) the 'ambiguous match' Gaps rows. Aliases come from raw/aliases.jsonl (GLEIF, wire company page, exchange profile) and
raw/perplexity_pages.jsonl (verified page display names). A title is the issuer's when it carries every key token of the legal
name or of an alias, or one distinctive token (CEO rule). A title that matches aliases of two different issuers is a conflict:
'adjudicated by Claude'. New events carry read-by '<original read> [alias: X, source]'."""
import re, openpyxl
from fc_common import *
from common import _unique_tokens, _common_words
issuers = load_issuers(); byk = {key(r): r for r in issuers}
al = {}
for d in jload('raw/aliases.jsonl'):
    for a in d.get('aliases', []): al.setdefault(d['key'], []).append(a)
for k_, a_ in perplexity_aliases().items(): al.setdefault(k_, []).append(a_)
for k_, a_ in website_aliases().items(): al.setdefault(k_, []).append(a_)
def alias_toks(a): return keytoks(a['alias'])
def alias_match(title, k):
    """returns (alias dict, mode) or (None, '')"""
    n = norm(title); words = set(n.split()); uniq = _unique_tokens(); common = _common_words()
    for a in al.get(k, []):
        toks = alias_toks(a)
        if toks and all(t in n for t in toks): return a, 'full'
        for t in [w for w in norm(a['alias']).split() if w not in STOP and len(w) >= 5]:
            if t in words and t in uniq and t not in common: return a, 'distinctive'
    return None, ''
# alias token -> issuers (to detect two-issuer alias collisions)
tok_owner = {}
for k, lst in al.items():
    for a in lst:
        for t in alias_toks(a): tok_owner.setdefault(t, set()).add(k)
def wire_events_for(r):
    """search again (three query forms) and keep hits that match the legal name or an alias"""
    out = []; conflicts = []
    seen = set()
    from wire_search import DOMS, INDEX, clean, dateline, short_name
    queries = [{'query': r['name'], 'max_results': 20, 'topic': 'news', 'days': 365, 'include_domains': DOMS}, {'query': f'"{short_name(r["name"])}" announces', 'max_results': 20, 'include_domains': DOMS}]
    for a in al.get(key(r), [])[:3]:
        queries.append({'query': f'"{a["alias"]}" announces', 'max_results': 20, 'include_domains': DOMS})
    for q in queries:
        j = tavily(q)
        for x in j.get('results', []):
            u = clean(x['url']); w = wire_of(u)
            if not w or INDEX.search(u) or u in seen: continue
            mode, tok = name_match(x['title'], r['name']); a = None
            if mode not in ('full', 'distinctive'):
                a, mode = alias_match(x['title'], key(r))
                if not a: continue
                # collision: does the matched token belong to another issuer's alias too?
                others = set()
                for t in alias_toks(a):
                    others |= tok_owner.get(t, set())
                others.discard(key(r))
                if others and mode == 'distinctive': conflicts.append({'url': u, 'title': x['title'], 'alias': a['alias'], 'other_issuers': sorted(others)[:3]}); continue
            seen.add(u)
            date = to_iso(x.get('published_date', '')) or url_date(u) or dateline(x.get('content', ''))
            if not date: continue
            rb = ('Tavily search (wire domains)' + (' + published_date' if x.get('published_date') else (' + URL date' if url_date(u) else ' + dateline in indexed snippet')))
            if a: rb += f" [alias: {a['alias']}, {a['read_by']}]"
            from common import in_window, event, classify
            if in_window(date): out.append(event(r, classify(x['title']), date, x['title'], w, u, rb, wire=w))
    return out, conflicts
def fetch(r):
    evs, conflicts = wire_events_for(r)
    ruled = []
    for c in conflicts[:5]:
        res = claude(f"Release title: \"{c['title']}\" ({c['url']}). Candidate issuers: {r['name']} (alias '{c['alias']}') and {', '.join(byk[o]['name'] for o in c['other_issuers'] if o in byk)}. "
                     "Which issuer does this title belong to? Answer from the title and URL only. Reply JSON: {\"issuer\": \"<exact legal name or empty>\", \"reason\": \"one line\"}",
                     'You adjudicate attribution for a capital-markets registry. Never guess; empty when unsure. JSON only.')
        j = jparse(res.get('text', '')) or {}
        ruled.append({**c, 'ruling': j.get('issuer', ''), 'reason': j.get('reason', '')})
        if norm(j.get('issuer', '')) == norm(r['name']):
            from common import event, classify
            d = to_iso('') or url_date(c['url'])
            if d: evs.append(event(r, classify(c['title']), d, c['title'], wire_of(c['url']), c['url'], f"Tavily search (wire domains) + URL date [alias: {c['alias']}; adjudicated by Claude]", wire=wire_of(c['url'])))
    return {'events': evs, 'n': len(evs), 'conflicts': ruled, 'aliases': [a['alias'] for a in al.get(key(r), [])]}
if __name__ == '__main__':
    EV = events(); have = set(e['exchange'] + '|' + e['ticker'] for e in EV)
    wb = openpyxl.load_workbook(r'C:\ALLOOLOO\CM-KG\DISCLOSURE\ca-disclosure.xlsx', read_only=True); g = wb['Gaps']
    amb = set(f'{row[0]}|{row[1]}' for row in g.iter_rows(min_row=2, values_only=True) if row and row[3] == 'ambiguous match')
    targets = [r for r in issuers if key(r) not in have or key(r) in amb]
    print('rematch targets', len(targets), '(zero-event', sum(1 for r in targets if key(r) not in have), ', ambiguous', len(amb), ') | issuers with aliases', len(al), flush=True)
    resume('rematch', fetch, targets, threads=int(E.get('THREADS', '8')))
