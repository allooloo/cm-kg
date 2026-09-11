"""Step 6 — Tavily reads for the fields the ASX / NSX records leave blank: share registry (when the ASX company record carries no registry address)
and newswire of habit beyond the ASX announcements platform. Rules: registry only from a closed list of Australian registries within 300 characters
of "registry" / "registrar"; wire = majority of up to three releases on the wire domains that carry the issuer name. Auditor is NOT read at Width 0:
the annual report announcement on the ASX platform is recorded as the source link (ORDER-010: source link only). Every accepted value keeps the
source URL and an evidence snippet. Pond-native: outputs go to the open drop for source 'enrich' (POND\au-cm-kg\enrich\<date>\)."""
import keys, os, sys, json, re, time, threading, requests
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import pond
TAV = os.environ['TAVILY_API_KEY']; H = {'Authorization': 'Bearer ' + TAV}
NODE = 'au-cm-kg'; DROP = 'raw'  # raw = junction to the open width0 drop (pond_migrate / pond_open)
ROSTER = 'raw/roster.json'
rows = json.load(open(ROSTER, encoding='utf-8'))
def is_corp(r): return r['security_type'] == 'Corporate'
def key(r): return r['exchange'] + '|' + r['symbol']
STOP = {'limited', 'ltd', 'the', 'company', 'co', 'group', 'holdings', 'holding', 'trust', 'fund', 'inc', 'corp', 'corporation', 'international', 'global', 'capital', 'resources', 'mining', 'minerals', 'metals', 'gold', 'energy', 'exploration', 'australia', 'australian', 'pty', 'nl', 'and', 'technologies', 'technology', 'ordinary', 'shares', 'fpo'}
def norm(s): return re.sub(r'[^a-z0-9 ]', ' ', s.lower().replace('&', ' and '))
def keytoks(n):
    t = [w for w in norm(n).split() if w not in STOP]
    return t[:2] if t else norm(n).split()[:1]
def mentions(txt, r): n = norm(txt); return all(k in n for k in keytoks(r['name']))
lock = threading.Lock()
def tavily(payload):
    for attempt in range(6):
        try:
            x = requests.post('https://api.tavily.com/search', json=payload, headers=H, timeout=120)
            if x.status_code == 429 or x.status_code >= 500: time.sleep(5 * (attempt + 1)); continue
            if x.status_code != 200: return {'error': x.status_code, 'text': x.text[:200]}
            return x.json()
        except Exception: time.sleep(3 * (attempt + 1))
    return {'error': 'exhausted'}
def run(task, fn, filt):
    fn_out = os.path.join(DROP, f'enr_{task}.jsonl'); done = {}
    if os.path.exists(fn_out):
        for line in open(fn_out, encoding='utf-8'):
            try: d = json.loads(line); done[d['key']] = d
            except Exception: pass
    todo = [r for r in rows if filt(r) and key(r) not in done]
    print(task, 'todo', len(todo), 'done', len(done), '->', fn_out, flush=True)
    out = open(fn_out, 'a', encoding='utf-8'); cnt = [0]
    def work(r):
        try: res = fn(r)
        except Exception as e: res = {'error': repr(e)[:200]}
        res['key'] = key(r)
        with lock:
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 50 == 0: print(task, cnt[0], '/', len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '3'))) as ex: list(ex.map(work, todo))
    print(task, 'DONE', flush=True)
REG_LIST = [('Computershare Investor Services Pty Limited', r'Computershare'), ('MUFG Corporate Markets (formerly Link Market Services)', r'MUFG Corporate Markets|Link Market Services|Link Group'), ('Boardroom Pty Limited', r'Boardroom(?: Pty)?(?: Limited| Ltd)?'), ('Automic Group', r'Automic'),
            ('Advanced Share Registry Limited', r'Advanced Share Registry'), ('Security Transfer Australia', r'Security Transfer (?:Australia|Registrars)'), ('XCEND', r'\bXCEND\b|Xcend'), ('Registry Direct', r'Registry Direct'), ('BoardRoom Limited', r'BoardRoom Limited'), ('Capital Transfer Agency', r'Capital Transfer Agency')]
def do_reg(r):
    j = tavily({'query': f"{r['name']} share registry", 'max_results': 6, 'include_raw_content': True})
    if 'error' in j: return {'error': j['error']}
    rg = Counter(); src = {}
    for x in j.get('results', []):
        txt = (x.get('raw_content') or '') + '\n' + (x.get('content') or ''); txt = re.sub(r'[ \t]+', ' ', txt)
        if not mentions(txt, r): continue
        for m in re.finditer(r'(?i)\bshare regist(?:ry|rar)\b|\bregistry\b|\bregistrar\b', txt):
            win = txt[max(0, m.start() - 300):m.end() + 300]
            for label, pat in REG_LIST:
                if re.search(pat, win): rg[label] += 1; src.setdefault(label, (x['url'], re.sub(r'\s+', ' ', win)[:300]))
    if not rg: return {'reg': '', 'reg_gap': 'none found', 'n_results': len(j.get('results', []))}
    (b, s) = rg.most_common(1)[0]
    if len(rg) > 1 and rg.most_common(2)[1][1] == s: return {'reg': '', 'reg_gap': 'conflict: ' + '; '.join(f'{k}({v})' for k, v in rg.most_common(3)), 'reg_cands': dict(rg)}
    return {'reg': b, 'reg_src': src[b][0], 'reg_ev': src[b][1], 'reg_cands': dict(rg)}
WIRES = {'prnewswire.com': 'PR Newswire', 'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'accesswire.com': 'ACCESS Newswire', 'newsfilecorp.com': 'Newsfile', 'medianet.com.au': 'Medianet', 'prwire.com.au': 'PRWire'}
INDEX_PAT = re.compile(r'globenewswire\.com/(?:organization|search)|businesswire\.com/(?:news/home/\?|portal)|prnewswire\.com/news/[^/]+/?$|accesswire\.com/newsroom|newsfilecorp\.com/company/')
def do_wire(r):
    j = tavily({'query': f"{r['name']} announces", 'max_results': 8, 'include_domains': list(WIRES.keys())})
    if 'error' in j: return {'error': j['error']}
    hits = []
    for x in j.get('results', []):
        u = x['url']; dom = re.sub(r'^https?://(www\.)?', '', u).split('/')[0]; dom = '.'.join(dom.split('.')[-2:]) if not dom.endswith('.com.au') else '.'.join(dom.split('.')[-3:])
        if dom not in WIRES or INDEX_PAT.search(u) or not mentions(x['title'] + ' ' + x['content'][:300], r): continue
        m = re.search(r'/(20\d\d)/(\d\d)/(\d\d)/', u) or re.search(r'-(20\d\d)(\d\d)(\d\d)', u)
        hits.append({'url': u, 'wire': WIRES[dom], 'date': f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else '', 'title': x['title'][:120]})
    hits = hits[:3]
    if not hits: return {'wire': '', 'gap': 'no wire releases matched issuer name', 'n_results': len(j.get('results', []))}
    c = Counter(h['wire'] for h in hits); (b, s) = c.most_common(1)[0]
    if len(hits) >= 2 and s < 2: return {'wire': '', 'gap': 'mixed wires in releases seen: ' + '; '.join(h['wire'] for h in hits), 'hits': hits}
    return {'wire': b, 'hits': hits, 'n_hits': len(hits), 'note': '' if len(hits) == 3 else f'{len(hits)} release(s) seen'}
if __name__ == '__main__':
    task = sys.argv[1]
    if task == 'reg': run('reg', do_reg, lambda r: is_corp(r) and not r.get('registry_address'))
    if task == 'wire': run('wire', do_wire, lambda r: is_corp(r))
