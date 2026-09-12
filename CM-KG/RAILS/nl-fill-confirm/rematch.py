"""Pass 2.1b — re-run the wire title match for zero-event issuers and for issuers with Gaps 'ambiguous match' rows, using the legal name OR a sourced alias
(KVK former names, exchange short name, GLEIF other names, wire page names). A title matches when it carries every key token of the name or an alias; a title
that matches two roster issuers goes to Claude, who rules from the release text or leaves it out. Search: Tavily over the wire domains and asx.com.au.
Labels: 'Tavily search (wire domains) … [alias: X, source]' · 'adjudicated by Claude'."""
import re
from fc_common import *
from collections import Counter
issuers = load_issuers(); byk = {key(r): r for r in issuers}
ALIASES = all_aliases()
EV = events(); per = Counter(e['exchange'] + '|' + e['ticker'] for e in EV)
amb = set()
try:
    wb = openpyxl.load_workbook(pond.latest_assembled(NODE, 'nl-disclosure.xlsx') or r'C:\ALLOOLOO\CM-KG\DISCLOSURE\nl-disclosure.xlsx', read_only=True); ws = wb['Gaps']; it = ws.iter_rows(values_only=True); hdr = next(it)
    for row in it:
        d = dict(zip(hdr, row))
        if d.get('Worker / field') == 'ambiguous match': amb.add(f"{d['Exchange']}|{d['Code']}")
except Exception: pass
DOMS = ['prnewswire.com', 'globenewswire.com', 'businesswire.com', 'accesswire.com', 'media-outreach.com', 'acnnewswire.com', 'regulator']
INDEX = re.compile(r'globenewswire\.com/(organization|search)|prnewswire\.com/news/[^/]+/?$|accesswire\.com/newsroom|media-outreach\.com/(company|search)')
def match_any(title, r):
    for nm, a in [(r['name'], None)] + [(a['alias'], a) for a in ALIASES.get(key(r), [])]:
        if name_match(title, nm)[0] == 'full': return nm, a
    return None, None
def others_matching(title, r): return [o['name'] for o in issuers if o is not r and name_match(title, o['name'])[0] == 'full'][:3]
SYS = "You decide which listed company a press release headline belongs to, from the release text only. Reply with strict JSON."
def fetch(r):
    k = key(r); evs = []; seen = set(); conflicts = []; amb_n = 0
    names = [r['name']] + [a['alias'] for a in ALIASES.get(k, [])]
    for nm in names[:4]:
        for payload in ({'query': nm, 'max_results': 15, 'topic': 'news', 'days': 365, 'include_domains': DOMS}, {'query': f'"{nm}"', 'max_results': 15, 'include_domains': DOMS}):
            j = tavily(payload)
            for x in j.get('results', []):
                u = x['url'].split('#')[0]
                if INDEX.search(u) or u in seen: continue
                mnm, alias = match_any(x['title'], r)
                if not mnm: amb_n += 1; continue
                date = to_iso(x.get('published_date', '')) or url_date(u)
                if not date: continue
                oth = others_matching(x['title'], r)
                rb = 'Tavily search (wire domains) + published_date' + (f" [alias: {alias['alias']}, {alias['read_by']}]" if alias else '')
                w = wire_of(u) or ('EQS News' if 'regulator' in u else '')
                if oth:
                    t, st = page_text(u)
                    res = claude(f"Headline: {x['title']}\nURL: {u}\nCandidates: {[r['name']] + oth}\nRelease text (start):\n{(t or '')[:6000]}\n\nWhich candidate issued this release? Reply JSON: {{\"issuer\": \"<name or empty>\", \"reason\": \"<one line>\"}}", SYS)
                    jj = jparse(res.get('text', '')) or {}
                    conflicts.append({'url': u, 'title': x['title'], 'candidates': [r['name']] + oth, 'ruling': jj.get('issuer', ''), 'usage': res.get('usage')})
                    if norm(jj.get('issuer', '')) != norm(r['name']): continue
                    rb += ' · adjudicated by Claude'
                seen.add(u); evs.append(event(r, classify(x['title'], default='newswire_release'), date, x['title'], w, u, rb, wire=w))
    return {'events': [e for e in evs if e['date'] >= (TODAY - datetime.timedelta(days=365)).isoformat()], 'n': len(evs), 'names_tried': names[:4], 'ambiguous': amb_n, 'conflicts': conflicts}
if __name__ == '__main__':
    targets = [r for r in issuers if per.get(key(r), 0) == 0 or key(r) in amb]
    print('rematch targets (zero-event or ambiguous):', len(targets), flush=True)
    resume('rematch', fetch, targets, threads=int(E.get('THREADS', '4')))
