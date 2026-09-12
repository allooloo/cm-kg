"""Step 6 — Tavily reads for the fields no registry publishes: share-register agent (closed list of Swiss share-register service providers within 300 characters
of "share register" / "Aktienregister" / "registre des actions") and newswire of habit (majority of up to three releases on the wire domains that carry the
issuer name; EQS News counts as a wire). Auditor is NOT read here (annual report link only at Width 0). Every accepted value keeps the source URL and an
evidence snippet. raw\\ is a junction to the open width0 drop."""
import keys, os, sys, json, re, time, threading, requests
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import pond
TAV = os.environ['TAVILY_API_KEY']; H = {'Authorization': 'Bearer ' + TAV}
NODE = 'ch-cm-kg'
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def is_corp(r): return r['security_type'] == 'Corporate'
def key(r): return r['exchange'] + '|' + r['symbol']
STOP = {'limited', 'ltd', 'the', 'company', 'co', 'group', 'holdings', 'holding', 'trust', 'fund', 'inc', 'corp', 'corporation', 'international', 'global', 'capital', 'investments', 'investment', 'ag', 'sa', 'and', 'technologies', 'technology', 'industries', 'engineering', 'swiss', 'schweiz', 'suisse', 'europe', 'n', 'i', 'reg', 'br', 'pc', 'ps', 'bearer', 'registered', 'aktiengesellschaft'}
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
    fn_out = f'raw/enr_{task}.jsonl'; done = {}
    if os.path.exists(fn_out):
        for line in open(fn_out, encoding='utf-8'):
            try: d = json.loads(line); done[d['key']] = d
            except Exception: pass
    todo = [r for r in rows if filt(r) and key(r) not in done]
    print(task, 'todo', len(todo), 'done', len(done), flush=True)
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
REG_LIST = [('Computershare Schweiz AG', r'Computershare'), ('areg.ch ag', r'\bareg\b'), ('ShareCommService AG', r'ShareComm'), ('Devigus Engineering AG (share register)', r'Devigus'), ('SIX SIS AG', r'SIX SIS'), ('Nimbus AG', r'\bNimbus AG\b'), ('Aktienregister (in-house)', r'(?i)aktienregister|share register is kept by the company')]
def do_reg(r):
    j = tavily({'query': f"{r['name']} Aktienregister share register", 'max_results': 6, 'include_raw_content': True})
    if 'error' in j: return {'error': j['error']}
    rg = Counter(); src = {}
    for x in j.get('results', []):
        txt = (x.get('raw_content') or '') + '\n' + (x.get('content') or ''); txt = re.sub(r'[ \t]+', ' ', txt)
        if not mentions(txt, r): continue
        for m in re.finditer(r'(?i)\bshare regist(?:rar|ry|er)\b|\bregistrar\b|\baktienregister\b|\bregistre des actions\b', txt):
            win = txt[max(0, m.start() - 300):m.end() + 300]
            for label, pat in REG_LIST:
                if re.search(pat, win): rg[label] += 1; src.setdefault(label, (x['url'], re.sub(r'\s+', ' ', win)[:300]))
    if not rg: return {'reg': '', 'reg_gap': 'none found', 'n_results': len(j.get('results', []))}
    (b, s) = rg.most_common(1)[0]
    if len(rg) > 1 and rg.most_common(2)[1][1] == s: return {'reg': '', 'reg_gap': 'conflict: ' + '; '.join(f'{k}({v})' for k, v in rg.most_common(3)), 'reg_cands': dict(rg)}
    return {'reg': b, 'reg_src': src[b][0], 'reg_ev': src[b][1], 'reg_cands': dict(rg)}
WIRES = {'prnewswire.com': 'PR Newswire', 'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'accesswire.com': 'ACCESS Newswire', 'newsfilecorp.com': 'Newsfile', 'eqs-news.com': 'EQS News', 'dgap.de': 'EQS News'}
INDEX_PAT = re.compile(r'globenewswire\.com/(?:organization|search)|businesswire\.com/(?:news/home/\?|portal)|prnewswire\.com/news/[^/]+/?$|accesswire\.com/newsroom|newsfilecorp\.com/company/|eqs-news\.com/(?:company|search)')
def do_wire(r):
    j = tavily({'query': f"{r['name']} announces", 'max_results': 8, 'include_domains': list(WIRES.keys())})
    if 'error' in j: return {'error': j['error']}
    hits = []
    for x in j.get('results', []):
        u = x['url']; dom = '.'.join(re.sub(r'^https?://(www\.)?', '', u).split('/')[0].split('.')[-2:])
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
    if task == 'reg': run('reg', do_reg, lambda r: is_corp(r) and r['isin'].startswith('CH'))
    if task == 'wire': run('wire', do_wire, lambda r: is_corp(r) and r['isin'].startswith('CH'))
