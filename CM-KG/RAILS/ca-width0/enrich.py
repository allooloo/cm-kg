import keys, os, sys, json, re, time, threading, requests
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
TAV = os.environ['TAVILY_API_KEY']; H = {'Authorization': 'Bearer ' + TAV}
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
rows = json.load(open('raw/roster.json'))
CORP_TYPES = ('Corporate', 'CPC', 'Income Trust', '')
def is_corp(r): return r['security_type'].split(' (')[0] in CORP_TYPES
def key(r): return r['exchange'] + '|' + r['symbol']
STOP = {'inc', 'corp', 'corporation', 'ltd', 'limited', 'the', 'company', 'co', 'trust', 'fund', 'etf', 'group', 'holdings', 'class', 'a', 'b', 'units', 'unit', 'shares', 'share', 'common', 'cdr', 'cad', 'hedged', 'plc', 'ltee'}
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
            if x.status_code == 429 or x.status_code >= 500:
                time.sleep(5 * (attempt + 1)); continue
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

# ---------- ISIN
ISIN_DOMS = ['marketscreener.com', 'investing.com', 'stockanalysis.com', 'tradingview.com', 'morningstar.ca', 'morningstar.com', 'ceo.ca', 'boerse-frankfurt.de', 'londonstockexchange.com', 'ft.com']
def isin_ok(s):
    if not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', s): return False
    digits = ''.join(str(int(c, 36)) for c in s); total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1: d *= 2
        total += d // 10 + d % 10
    return total % 10 == 0
def do_isin(r):
    j = tavily({'query': f"{r['name']} {r['root']} ISIN", 'max_results': 4, 'include_raw_content': True, 'include_domains': ISIN_DOMS})
    if 'error' in j: return {'error': j['error']}
    results = j.get('results', [])
    if not results or not any(x.get('raw_content') for x in results):
        j2 = tavily({'query': f"{r['name']} {r['root']} ISIN", 'max_results': 5, 'include_raw_content': True})
        if 'error' not in j2: results = results + j2.get('results', [])
    support = Counter(); urls = {}
    for x in results:
        txt = (x.get('raw_content') or '') + ' ' + (x.get('content') or '')
        if not mentions(txt, r): continue
        toks = set(re.findall(r'[A-Z0-9.:-]+', txt))
        tick_in = r['root'] in toks or any(t.startswith(r['root'] + '.') or t.startswith(r['root'] + ':') for t in toks)
        if not tick_in: continue
        found = set(s for s in re.findall(r'\b[A-Z]{2}[A-Z0-9]{9}\d\b', txt) if isin_ok(s))
        strong = r['root'].lower() in x['url'].lower() or all(k in x['url'].lower() for k in keytoks(r['name']))
        for s in found:
            support[s] += 2 if strong else 1; urls.setdefault(s, []).append(x['url'])
    if not support: return {'isin': '', 'gap': 'no ISIN found on issuer pages', 'n_results': len(j.get('results', []))}
    best, score = support.most_common(1)[0]
    if len(support) > 1 and support.most_common(2)[1][1] == score:
        return {'isin': '', 'gap': 'ISIN conflict: ' + ', '.join(f'{k}({v})' for k, v in support.most_common(4)), 'cands': dict(support)}
    if score < 2: return {'isin': '', 'gap': 'single weak ISIN mention: ' + best, 'cands': dict(support), 'urls': urls[best][:2]}
    return {'isin': best, 'src': urls[best][0], 'support': score, 'cands': dict(support)}

# ---------- corporate: transfer agent, auditor, jurisdiction
TA_LIST = [('Computershare', r'Computershare(?: Trust Company of Canada| Investor Services Inc\.?)?'), ('TSX Trust Company', r'TSX Trust(?: Company)?'), ('Odyssey Trust Company', r'Odyssey Trust(?: Company)?'), ('Endeavor Trust Corporation', r'Endeavor Trust(?: Corporation)?'), ('Olympia Trust Company', r'Olympia Trust(?: Company)?'), ('Capital Transfer Agency', r'Capital Transfer Agency(?: ULC| Inc\.?)?'), ('Marrelli Trust Company Limited', r'Marrelli Trust(?: Company(?: Limited)?)?'), ('National Securities Administrators Ltd.', r'National Securities Administrators(?: Ltd\.?)?'), ('Alliance Trust Company', r'Alliance Trust(?: Company)?'), ('AST Trust Company (Canada)', r'AST Trust Company(?: \(Canada\))?'), ('Broadridge', r'Broadridge(?: Financial Solutions| Investor Communications)?'), ('Continental Stock Transfer & Trust', r'Continental Stock Transfer'), ('Pacific Stock Transfer', r'Pacific Stock Transfer'), ('VStock Transfer', r'VStock Transfer'), ('Securities Transfer Corporation', r'Securities Transfer Corp'), ('Equiniti / EQ', r'Equiniti|EQ Shareowner Services'), ('Transfer Online', r'Transfer Online'), ('Reliable Stock Transfer', r'Reliable Stock Transfer'), ('Nevada Agency and Transfer', r'Nevada Agency and Transfer'), ('Issuer Direct', r'Issuer Direct'), ('Empire Stock Transfer', r'Empire Stock Transfer'), ('Action Stock Transfer', r'Action Stock Transfer'), ('Globex Transfer', r'Globex Transfer'), ('Link Market Services', r'Link Market Services'), ('Automic', r'Automic'), ('Boardroom', r'Boardroom Pty'), ('Equity Financial Trust', r'Equity Financial Trust'), ('Valiant Trust', r'Valiant Trust'), ('CST Trust Company', r'CST Trust Company'), ('Mountain Share Transfer', r'Mountain Share Transfer'), ('Colonial Stock Transfer', r'Colonial Stock Transfer'), ('ClearTrust', r'ClearTrust'), ('Worldwide Stock Transfer', r'Worldwide Stock Transfer'), ('West Coast Stock Transfer', r'West Coast Stock Transfer'), ('Manhattan Transfer Registrar', r'Manhattan Transfer Registrar'), ('Signature Stock Transfer', r'Signature Stock Transfer'), ('Standard Registrar & Transfer', r'Standard Registrar'), ('Island Stock Transfer', r'Island Stock Transfer')]
TOK = r"(?:[A-Z][A-Za-z&.'’\-]*|&|and|de|et)"
FIRM = TOK + r"(?: " + TOK + r"){0,6}?"
AUD_PAT = [re.compile(r"[Aa]uditors?\s+(?:of\s+the\s+(?:Company|Corporation|Trust|Fund|Issuer|Bank)\s+)?(?:is|are|were|was|:|,|—|–|-)?\s*(?:currently\s+)?(" + FIRM + r"\s(?:LLP|LLC|S\.E\.N\.C\.R\.L\.|s\.r\.l\.|s\.e\.n\.c\.r\.l\.|SENCRL|Inc\.|Ltd\.|Limited|Professional Corporation|Chartered Professional Accountants|CPA))"),
           re.compile(r"(" + FIRM + r"\s(?:LLP|Inc\.|Ltd\.|S\.E\.N\.C\.R\.L\.))\s*,?\s+(?:Chartered Professional Accountants|Chartered Accountants|Independent Registered Public Accounting Firm|Licensed Public Accountants|Independent Auditors?)"),
           re.compile(r"(?:appoint(?:ed|ment of)|re-?appoint(?:ed|ment of)|engaged)\s+(" + FIRM + r"\s(?:LLP|Inc\.|Ltd\.))\s+as\s+(?:the\s+)?(?:Company's\s+|Corporation's\s+|its\s+)?(?:independent\s+)?auditors?")]
NOISE_AUD = re.compile(r'(?i)^(?:the |our |its |report|independent|registered|audit committee|consolidated|annual|financial|by |of |and |with |for |to |from |as |or |that |which )')
def clean_aud(s):
    s = re.sub(r'\s+', ' ', s).strip(' ,.;:')
    s = re.sub(r'^(?:the|The|of|by|and|with|for)\s+', '', s)
    toks = s.split()
    # strip a run of >=2 leading ALL-CAPS heading words when the rest of the firm name is mixed case
    if len(toks) > 3 and toks[0].isupper() and toks[1].isupper() and not all(t.isupper() or t in ('&', 'and') for t in toks[:-1]):
        while len(toks) > 2 and toks[0].isupper() and len(toks[0]) >= 2: toks.pop(0)
        s = ' '.join(toks)
    return s
JUR_PAT = re.compile(r"(?:Business Corporations Act|Companies Act|Corporations Act|Company Act)\s*\((British Columbia|Ontario|Alberta|Qu[eé]bec|Manitoba|Saskatchewan|Nova Scotia|New Brunswick|Newfoundland and Labrador|Prince Edward Island|Yukon|Bermuda|Nevada|Canada)\)|(Canada Business Corporations Act|Business Corporations Act \(Canada\)|Delaware General Corporation Law|Cayman Islands Companies (?:Act|Law)|BVI Business Companies Act|Bermuda Companies Act|Israel(?:i)? Companies Law|Companies Act 2006|Companies Act 1985|Corporations Act 2001|Nevada Revised Statutes|Colorado Business Corporation Act|Wyoming Business Corporation Act|Florida Business Corporation Act|Ontario Business Corporations Act|British Columbia Business Corporations Act|Alberta Business Corporations Act)")
JMAP = {'Canada Business Corporations Act': 'Canada (federal, CBCA)', 'Business Corporations Act (Canada)': 'Canada (federal, CBCA)', 'Canada': 'Canada (federal, CBCA)', 'Delaware General Corporation Law': 'Delaware, US', 'Cayman Islands Companies Act': 'Cayman Islands', 'Cayman Islands Companies Law': 'Cayman Islands', 'BVI Business Companies Act': 'British Virgin Islands', 'Bermuda Companies Act': 'Bermuda', 'Bermuda': 'Bermuda', 'Israel Companies Law': 'Israel', 'Israeli Companies Law': 'Israel', 'Companies Act 2006': 'United Kingdom', 'Companies Act 1985': 'United Kingdom', 'Corporations Act 2001': 'Australia', 'Nevada Revised Statutes': 'Nevada, US', 'Nevada': 'Nevada, US', 'Colorado Business Corporation Act': 'Colorado, US', 'Wyoming Business Corporation Act': 'Wyoming, US', 'Florida Business Corporation Act': 'Florida, US', 'Ontario Business Corporations Act': 'Ontario', 'British Columbia Business Corporations Act': 'British Columbia', 'Alberta Business Corporations Act': 'Alberta', 'Québec': 'Québec', 'Quebec': 'Québec'}
def pick(c):
    if not c: return '', 'none found'
    (b, s) = c.most_common(1)[0]
    if len(c) > 1 and c.most_common(2)[1][1] == s:
        return '', 'conflict: ' + '; '.join(f'{k}({v})' for k, v in c.most_common(3))
    return b, ''
def do_corp(r):
    j = tavily({'query': f"{r['name']} transfer agent auditor", 'max_results': 5, 'include_raw_content': True})
    if 'error' in j: return {'error': j['error']}
    ta = Counter(); ta_src = {}; au = Counter(); au_src = {}; ju = Counter(); ju_src = {}
    for x in j.get('results', []):
        txt = (x.get('raw_content') or '') + '\n' + (x.get('content') or ''); txt = re.sub(r'[ \t]+', ' ', txt)
        if not mentions(txt, r): continue
        for m in re.finditer(r'(?i)transfer agent', txt):
            win = txt[max(0, m.start() - 300):m.end() + 300]
            for label, pat in TA_LIST:
                if re.search(pat, win):
                    ta[label] += 1; ta_src.setdefault(label, (x['url'], re.sub(r'\s+', ' ', win)[:300]))
        for pat in AUD_PAT:
            for m in pat.finditer(txt):
                a = clean_aud(m.group(1))
                if len(a) < 5 or NOISE_AUD.search(a) or 'transfer' in a.lower() or a.lower().startswith(('company', 'corporation')): continue
                au[a] += 1; au_src.setdefault(a, (x['url'], re.sub(r'\s+', ' ', txt[max(0, m.start() - 80):m.end() + 80])[:260]))
        for m in JUR_PAT.finditer(txt):
            g = m.group(1) or m.group(2); lab = JMAP.get(g, g)
            ju[lab] += 1; ju_src.setdefault(lab, (x['url'], re.sub(r'\s+', ' ', txt[max(0, m.start() - 100):m.end() + 60])[:240]))
    ta_v, ta_g = pick(ta); au_v, au_g = pick(au); ju_v, ju_g = pick(ju)
    return {'ta': ta_v, 'ta_gap': ta_g, 'ta_src': ta_src.get(ta_v, ('', ''))[0], 'ta_ev': ta_src.get(ta_v, ('', ''))[1], 'ta_cands': dict(ta),
            'aud': au_v, 'aud_gap': au_g, 'aud_src': au_src.get(au_v, ('', ''))[0], 'aud_ev': au_src.get(au_v, ('', ''))[1], 'aud_cands': dict(au.most_common(5)),
            'jur': ju_v, 'jur_gap': ju_g, 'jur_src': ju_src.get(ju_v, ('', ''))[0], 'jur_ev': ju_src.get(ju_v, ('', ''))[1], 'jur_cands': dict(ju)}

# ---------- newswire
WIRES = {'newswire.ca': 'Canada Newswire (CNW)', 'prnewswire.com': 'PR Newswire', 'newsfilecorp.com': 'Newsfile', 'globenewswire.com': 'GlobeNewswire', 'businesswire.com': 'Business Wire', 'accesswire.com': 'ACCESS Newswire', 'thenewswire.com': 'TheNewswire'}
INDEX_PAT = re.compile(r'newswire\.ca/news/[^/]+/?(\?|$)|newsfilecorp\.com/company/|globenewswire\.com/(?:organization|search)|businesswire\.com/(?:news/home/\?|portal)|prnewswire\.com/news/[^/]+/?$|accesswire\.com/newsroom')
def do_wire(r):
    j = tavily({'query': f"{r['name']} announces", 'max_results': 8, 'include_domains': list(WIRES.keys())})
    if 'error' in j: return {'error': j['error']}
    hits = []
    for x in j.get('results', []):
        u = x['url']; dom = re.sub(r'^https?://(www\.)?', '', u).split('/')[0]
        dom = '.'.join(dom.split('.')[-2:])
        if dom not in WIRES or INDEX_PAT.search(u): continue
        if not mentions(x['title'] + ' ' + x['content'][:300], r): continue
        m = re.search(r'/(20\d\d)/(\d\d)/(\d\d)/', u) or re.search(r'-(20\d\d)(\d\d)(\d\d)', u)
        dt = f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else ''
        hits.append({'url': u, 'wire': WIRES[dom], 'date': dt, 'title': x['title'][:120]})
    hits = hits[:3]
    if not hits: return {'wire': '', 'gap': 'no wire releases matched issuer name', 'n_results': len(j.get('results', []))}
    c = Counter(h['wire'] for h in hits); (b, s) = c.most_common(1)[0]
    if len(hits) >= 2 and s < 2:
        return {'wire': '', 'gap': 'mixed wires in releases seen: ' + '; '.join(h['wire'] for h in hits), 'hits': hits}
    return {'wire': b, 'hits': hits, 'n_hits': len(hits), 'note': '' if len(hits) == 3 else f'{len(hits)} release(s) seen'}

# ---------- SEDAR+ profile
PROF = re.compile(r'^\s*#\s*(.+?)\s*\((\d{9})\)', re.M)
def do_sedar(r):
    j = tavily({'query': f"{r['name']} View Issuer Profile", 'max_results': 6, 'include_domains': ['sedarplus.ca']})
    if 'error' in j: return {'error': j['error']}
    res = j.get('results', [])
    for x in res:
        u = x['url']
        if not ('profile.html' in u or re.search(r'/csa-party/\d{9}\.html', u)): continue
        m = PROF.search(x.get('content') or '')
        if not m: continue
        pname, pno = m.group(1), m.group(2)
        if norm(pname).replace(' ', '') == norm(r['name']).replace(' ', ''):
            return {'sedar_no': pno, 'profile_name': pname, 'url': u, 'canon': f'https://www.sedarplus.ca/csa-party/{pno}.html?_locale=en', 'match': 'exact'}
    for x in res:
        u = x['url']; m = PROF.search(x.get('content') or '')
        if m and ('profile.html' in u or re.search(r'/csa-party/\d{9}\.html', u)):
            pname, pno = m.group(1), m.group(2)
            if keytoks(pname) == keytoks(r['name']) and norm(pname).split()[-1:] == norm(r['name']).split()[-1:]:
                return {'sedar_no': pno, 'profile_name': pname, 'url': u, 'canon': f'https://www.sedarplus.ca/csa-party/{pno}.html?_locale=en', 'match': 'loose'}
    seen = []
    for x in res[:4]:
        m = PROF.search(x.get('content') or ''); seen.append((m.group(1) if m else '', x['url'][:90]))
    return {'sedar_no': '', 'gap': 'no SEDAR+ profile matched name', 'seen': seen}

# ---------- CSE site
def slug(n):
    s = n.lower().replace('&', 'and'); s = re.sub(r"['’.]", '', s); s = re.sub(r'[^a-z0-9]+', '-', s).strip('-'); return s
CSE_BUILD = open('raw/cse_build_id.txt').read().strip() if os.path.exists('raw/cse_build_id.txt') else 'Te7Aapm5mYHXo2_9ZTcSR'
def slug_variants(n):
    base = n.lower(); outs = []
    for amp in ['and', '', '-']:
        s = base.replace('&', amp); s = re.sub(r"['’.]", '', s); s = re.sub(r'[^a-z0-9]+', '-', s).strip('-'); outs.append(s)
        mm = re.match(r'^(.*?\b(?:inc|corp|corporation|ltd|limited|company|co|trust|holdings|group)\b)', s)
        if mm: outs.append(mm.group(1).strip('-'))
    seen = []
    for o in outs:
        if o not in seen: seen.append(o)
    return seen
def cse_page(s):
    u = f'https://thecse.com/_next/data/{CSE_BUILD}/en/listings/{s}.json'
    for attempt in range(4):
        try:
            x = requests.get(u, headers=UA, timeout=60); break
        except Exception:
            time.sleep(3)
    else: return None
    if x.status_code != 200 or 'staticCompanyInfo' not in x.text: return None
    return x.json()['pageProps'].get('staticCompanyInfo') or {}
def do_cse(r):
    sc = None; s = ''
    for s in slug_variants(r['name']):
        sc = cse_page(s)
        if sc is not None: break
    if sc is None:  # last resort: Tavily site search for the company page slug
        j = tavily({'query': f"{r['name']} {r['root']}", 'max_results': 6, 'include_domains': ['thecse.com']})
        for x in j.get('results', []):
            mm = re.search(r'thecse\.com/listings/([a-z0-9-]+)', x['url'])
            if not mm: continue
            cand = cse_page(mm.group(1))
            if cand is not None and (cand.get('symbol', '').split('.')[0] == r['root'] or cand.get('title', '').lower()[:10] == r['name'].lower()[:10]):
                sc, s = cand, mm.group(1); break
    if sc is None: return {'error': 'company page not found', 'slug': slug(r['name'])}
    ad = sc.get('address') or {}
    return {'slug': s, 'page': f'https://thecse.com/listings/{s}/', 'auditor': sc.get('auditor') or '', 'transferAgent': sc.get('transferAgent') or '', 'city': ad.get('locality') or '', 'province': ad.get('administrativeArea') or '', 'country': ad.get('country') or '', 'jurisdiction': sc.get('corporateJurisdiction') or '', 'website': sc.get('url') or '', 'fye': sc.get('financialYearEnd') or '', 'securityType': sc.get('securityType') or '', 'sector': sc.get('sector') or ''}

if __name__ == '__main__':
    task = sys.argv[1]
    if task == 'cse': run('cse', do_cse, lambda r: r['exchange'] == 'CSE')
    if task == 'isin': run('isin', do_isin, lambda r: True)
    if task == 'corp': run('corp', do_corp, lambda r: is_corp(r) and r['exchange'] != 'CSE')
    if task == 'corp_cse_missing':  # CSE issuers whose company page carries no auditor
        cse = {}
        if os.path.exists('raw/enr_cse.jsonl'):
            for line in open('raw/enr_cse.jsonl', encoding='utf-8'):
                d = json.loads(line)
                if 'error' not in d or d['key'] not in cse: cse[d['key']] = d
        missing = set(k for k, d in cse.items() if 'error' in d or not d.get('auditor'))
        run('corp', do_corp, lambda r: r['exchange'] == 'CSE' and is_corp(r) and key(r) in missing)
    if task == 'wire': run('wire', do_wire, lambda r: is_corp(r))
    if task == 'sedar': run('sedar', do_sedar, lambda r: is_corp(r) and r['exchange'] != 'CSE')
