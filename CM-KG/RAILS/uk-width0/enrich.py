"""Step 9 — Tavily reads for the fields no registry or exchange list publishes as data: registrar, auditor, newswire of habit.
Rules: registrar only from a closed list of UK/Channel Islands registrar names within 300 characters of the word "registrar"; auditor only from
explicit phrases (auditor(s) is/are/was X LLP; X LLP, Statutory Auditor(s); appointed X LLP as auditor) and only when the string canonicalises to
a recognised audit-firm name (assemble.py); newswire only from release hits that carry the issuer name — RNS when the release sits on
londonstockexchange.com/news-article/<TIDM>/ or investegate.co.uk, else the wire domain — and only when one wire is the majority of up to three
releases seen. Majority across pages; ties = blank + Gaps. Every accepted value keeps the source URL and an evidence snippet.
Tasks: reg (registrar + auditor; corporates and closed-ended companies on all three markets, except Aquis registrar which the exchange page carries),
wire (all corporates). Resumable: keys already in raw/enr_<task>.jsonl are skipped."""
import keys, os, sys, json, re, time, threading, requests
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
TAV = os.environ['TAVILY_API_KEY']; H = {'Authorization': 'Bearer ' + TAV}
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def is_corp(r): return r['security_type'] in ('Corporate', 'Closed-ended investment company')
def key(r): return r['exchange'] + '|' + r['symbol']
STOP = {'plc', 'p', 'l', 'c', 'limited', 'ltd', 'the', 'company', 'co', 'group', 'holdings', 'holding', 'trust', 'fund', 'inc', 'corp', 'corporation', 'sa', 'nv', 'ag', 'se', 'international', 'investment', 'investments', 'ordinary', 'shares', 'ord', 'class', 'a', 'b', 'and'}
def norm(s): return re.sub(r'[^a-z0-9 ]', ' ', s.lower().replace('&', ' and '))
def keytoks(n):
    t = [w for w in norm(n).split() if w not in STOP]
    return t[:2] if t else norm(n).split()[:1]
def mentions(txt, r):
    n = norm(txt); return all(k in n for k in keytoks(r['name']))
lock = threading.Lock()
def tavily(payload):
    for attempt in range(6):
        try:
            x = requests.post('https://api.tavily.com/search', json=payload, headers=H, timeout=120)
            if x.status_code == 429 or x.status_code >= 500: time.sleep(5 * (attempt + 1)); continue
            if x.status_code != 200: return {'error': x.status_code, 'text': x.text[:200]}
            return x.json()
        except Exception:
            time.sleep(3 * (attempt + 1))
    return {'error': 'exhausted'}
def run(task, fn, filt):
    fn_out = f'raw/enr_{task}.jsonl'; done = {}
    if os.path.exists(fn_out):
        for line in open(fn_out, encoding='utf-8'):
            try:
                d = json.loads(line); done[d['key']] = d
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
    with ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '3'))) as ex:
        list(ex.map(work, todo))
    print(task, 'DONE', flush=True)

# ---------- registrar (closed list) and auditor (explicit phrases)
REG_LIST = [('Computershare Investor Services PLC', r'Computershare(?: Investor Services)?(?: PLC| plc| \(Jersey\) Limited| \(Guernsey\) Limited| \(BVI\) Ltd| \(Ireland\)| \(Channel Islands\)| \(C\.I\.\))?'),
            ('Equiniti Limited', r'Equiniti(?: Limited| Registrars| \(Jersey\) Limited)?|\bEQ Registrars\b'),
            ('MUFG Corporate Markets (formerly Link Group)', r'MUFG Corporate Markets(?: \(UK\) Limited| \(Guernsey\) Limited| \(Jersey\) Limited)?|Link Group|Link Market Services|Link Asset Services|Link Registrars|Capita Asset Services|Capita Registrars|Capita IRG'),
            ('Neville Registrars Limited', r'Neville Registrars'), ('Share Registrars Limited', r'Share Registrars'), ('SLC Registrars', r'SLC Registrars'), ('Avenir Registrars Limited', r'Avenir Registrars'),
            ('JTC Registrars Limited', r'JTC Registrars'), ('Ocorian', r'Ocorian'), ('Computershare Investor Services (Jersey) Limited', r'Computershare Investor Services \(Jersey\)'), ('Apex Registrars', r'Apex Registrars|Apex Fund Services \(Guernsey\)'),
            ('Crestbridge', r'Crestbridge'), ('Maitland Administration Services', r'Maitland Administration'), ('Sanne', r'\bSanne\b'), ('Aztec Financial Services', r'Aztec Financial Services'), ('Estera', r'\bEstera\b'), ('Ogier', r'Ogier Global'), ('Continental Stock Transfer & Trust', r'Continental Stock Transfer'), ('Computershare Trust Company', r'Computershare Trust Company')]
TOK = r"(?:[A-Z][A-Za-z&.'’\-]*|&|and|de|et|Associés)"
FIRM = TOK + r"(?: " + TOK + r"){0,6}?"
SUFFIX = r"(?:LLP|LLC|Limited|Ltd\.?|Inc\.?|Chartered Accountants|Statutory Auditors?|Registered Auditors?|S\.A\.|SA|GmbH|AG|Oy|AB|A/S|B\.V\.|Audit|Audit Services)"
AUD_PAT = [re.compile(r"[Aa]uditors?\s+(?:of\s+the\s+(?:Company|Group|Trust|Fund|Issuer)\s+)?(?:is|are|were|was|:|,|—|–|-)?\s*(?:currently\s+)?(" + FIRM + r"\s" + SUFFIX + r")"),
           re.compile(r"(" + FIRM + r"\s(?:LLP|Limited|Ltd\.?|Inc\.?|S\.A\.|GmbH|AG))\s*,?\s+(?:Chartered Accountants|Statutory Auditors?|Registered Auditors?|Independent Auditors?|Chartered Certified Accountants|Independent Registered Public Accounting Firm)"),
           re.compile(r"(?:appoint(?:ed|ment of)|re-?appoint(?:ed|ment of)|engaged)\s+(" + FIRM + r"\s(?:LLP|Limited|Ltd\.?|Inc\.?|S\.A\.|GmbH|AG))\s+as\s+(?:the\s+)?(?:Company's\s+|Group's\s+|its\s+)?(?:independent\s+|statutory\s+|external\s+)?auditors?"),
           re.compile(r"[Ii]ndependent [Aa]uditor'?s'? [Rr]eport[^.]{0,200}?\b(?:by|from)\s+(" + FIRM + r"\s" + SUFFIX + r")")]
NOISE_AUD = re.compile(r'(?i)^(?:the |our |its |report|independent|registered|audit committee|consolidated|annual|financial|by |of |and |with |for |to |from |as |or |that |which |company|group)')
def clean_aud(s):
    s = re.sub(r'\s+', ' ', s).strip(' ,.;:')
    s = re.sub(r'^(?:the|The|of|by|and|with|for)\s+', '', s)
    toks = s.split()
    if len(toks) > 3 and toks[0].isupper() and toks[1].isupper() and not all(t.isupper() or t in ('&', 'and') for t in toks[:-1]):
        while len(toks) > 2 and toks[0].isupper() and len(toks[0]) >= 2: toks.pop(0)
        s = ' '.join(toks)
    return s
def pick(c):
    if not c: return '', 'none found'
    (b, s) = c.most_common(1)[0]
    if len(c) > 1 and c.most_common(2)[1][1] == s:
        return '', 'conflict: ' + '; '.join(f'{k}({v})' for k, v in c.most_common(3))
    return b, ''
def do_reg(r):
    j = tavily({'query': f"{r['name']} registrar auditor annual report", 'max_results': 6, 'include_raw_content': True})
    if 'error' in j: return {'error': j['error']}
    rg = Counter(); rg_src = {}; au = Counter(); au_src = {}
    for x in j.get('results', []):
        txt = (x.get('raw_content') or '') + '\n' + (x.get('content') or ''); txt = re.sub(r'[ \t]+', ' ', txt)
        if not mentions(txt, r): continue
        for m in re.finditer(r'(?i)\bregistrars?\b', txt):
            win = txt[max(0, m.start() - 300):m.end() + 300]
            for label, pat in REG_LIST:
                if re.search(pat, win):
                    rg[label] += 1; rg_src.setdefault(label, (x['url'], re.sub(r'\s+', ' ', win)[:300]))
        for pat in AUD_PAT:
            for m in pat.finditer(txt):
                a = clean_aud(m.group(1))
                if len(a) < 5 or NOISE_AUD.search(a) or 'registrar' in a.lower() or a.lower().startswith(('company', 'corporation', 'group')): continue
                au[a] += 1; au_src.setdefault(a, (x['url'], re.sub(r'\s+', ' ', txt[max(0, m.start() - 80):m.end() + 80])[:260]))
    rg_v, rg_g = pick(rg); au_v, au_g = pick(au)
    return {'reg': rg_v, 'reg_gap': rg_g, 'reg_src': rg_src.get(rg_v, ('', ''))[0], 'reg_ev': rg_src.get(rg_v, ('', ''))[1], 'reg_cands': dict(rg),
            'aud': au_v, 'aud_gap': au_g, 'aud_src': au_src.get(au_v, ('', ''))[0], 'aud_ev': au_src.get(au_v, ('', ''))[1], 'aud_cands': dict(au.most_common(6)), 'n_results': len(j.get('results', []))}

# ---------- newswire of habit
WIRES = {'prnewswire.com': 'PR Newswire', 'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'londonstockexchange.com': 'RNS (via LSE)', 'investegate.co.uk': 'RNS (via Investegate)', 'accesswire.com': 'ACCESS Newswire', 'newsfilecorp.com': 'Newsfile'}
INDEX_PAT = re.compile(r'globenewswire\.com/(?:organization|search)|businesswire\.com/(?:news/home/\?|portal)|prnewswire\.com/news/[^/]+/?$|accesswire\.com/newsroom|londonstockexchange\.com/(?:stock/|news\?|news-article/?$)|investegate\.co\.uk/(?:company/|$)')
def do_wire(r):
    j = tavily({'query': f"{r['name']} announces", 'max_results': 10, 'include_domains': list(WIRES.keys())})
    if 'error' in j: return {'error': j['error']}
    hits = []
    for x in j.get('results', []):
        u = x['url']; dom = re.sub(r'^https?://(www\.)?', '', u).split('/')[0]
        dom = '.'.join(dom.split('.')[-2:]) if not dom.endswith('.co.uk') else '.'.join(dom.split('.')[-3:])
        if dom not in WIRES or INDEX_PAT.search(u): continue
        if dom == 'londonstockexchange.com':
            mm = re.search(r'/news-article/([A-Z0-9.]+)/', u)
            if not mm or mm.group(1) != r['symbol']: continue
        elif not mentions(x['title'] + ' ' + x['content'][:300], r): continue
        m = re.search(r'/(20\d\d)/(\d\d)/(\d\d)/', u) or re.search(r'-(20\d\d)(\d\d)(\d\d)', u)
        dt = f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else ''
        hits.append({'url': u, 'wire': WIRES[dom], 'date': dt, 'title': x['title'][:120]})
    hits = hits[:3]
    if not hits: return {'wire': '', 'gap': 'no wire releases matched issuer name / TIDM', 'n_results': len(j.get('results', []))}
    c = Counter(h['wire'].split(' (')[0] for h in hits); (b, s) = c.most_common(1)[0]
    if len(hits) >= 2 and s < 2:
        return {'wire': '', 'gap': 'mixed wires in releases seen: ' + '; '.join(h['wire'] for h in hits), 'hits': hits}
    return {'wire': b, 'hits': hits, 'n_hits': len(hits), 'note': '' if len(hits) == 3 else f'{len(hits)} release(s) seen'}

if __name__ == '__main__':
    task = sys.argv[1]
    if task == 'reg': run('reg', do_reg, lambda r: is_corp(r))
    if task == 'wire': run('wire', do_wire, lambda r: is_corp(r))
