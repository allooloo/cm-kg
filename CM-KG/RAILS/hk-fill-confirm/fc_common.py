"""Shared pieces for the Hong Kong Fill + Confirm rail (ORDER-035, 2026-10-22), the Singapore rail's shape with the Hong Kong pockets: the HKEX roster
(Main Board, GEM, REITs), HKEXnews documents from Width 1, English-language filings only. Pond-native: raw\\ is a junction to the open drop
POND\\hk-cm-kg\\fill-confirm\\<date>\\; jload reads every drop (newest wins per key). Reading order of record: Perplexity → Grok (second) → Mistral (review only);
Tavily for page extraction, ceiling 400,000 this month (pay-as-you-go limit, read live)."""
import os, sys, re, json, time, threading, html, datetime
import requests, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keys, pond
NODE = 'hk-cm-kg'; TABS = ['Main Board', 'GEM', 'REITs']
ISSUERS_XLSX = pond.latest_assembled(NODE, 'hk-issuers.xlsx') or r'C:\ALLOOLOO\CM-KG\ISSUERS\hk-issuers.xlsx'
EVENTS_JSONL = pond.latest_assembled(NODE, 'hk-events.jsonl') or r'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\hk-events.jsonl'
os.makedirs('raw', exist_ok=True); os.makedirs('raw/reports', exist_ok=True)
E = os.environ; lock = threading.Lock()
UA = 'Mozilla/5.0 (compatible; Allooloo Technologies Corp. CM-KG hk-fill-confirm; developers@allooloo.ai)'
CJK = re.compile(r'[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
def jload(fn):
    out = []; seen = set()
    paths = [p for d, p in pond.drops(NODE, 'fill-confirm')] + (['raw'] if os.path.isdir('raw') else [])
    for p in paths:
        f = os.path.join(p, os.path.basename(fn)); rp = os.path.realpath(f)
        if not os.path.exists(f) or rp in seen: continue
        seen.add(rp)
        for line in open(f, encoding='utf-8'):
            try: out.append(json.loads(line))
            except Exception: pass
    if out and all(isinstance(d, dict) and 'key' in d for d in out[:50]):
        byk = {}
        for d in out: byk[d.get('key')] = d
        return list(byk.values())
    return out
def all_rows():
    wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True); out = []
    for ex in TABS:
        ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it)
        for r in it:
            d = dict(zip(hdr, r)); d['_tab'] = ex
            if d.get('Stock code'): out.append(d)
    return out
def key_of(d): return d['_tab'] + '|' + str(d['Stock code'])
def events():
    out = []
    for line in open(EVENTS_JSONL, encoding='utf-8'):
        try: out.append(json.loads(line))
        except Exception: pass
    return out
def resume(task, fn, items, threads=4, keyf=key_of):
    fn_out = f'raw/{task}.jsonl'; done = {d.get('key') for d in jload(fn_out)}
    todo = [r for r in items if keyf(r) not in done]; print(task, 'todo', len(todo), 'done', len(done), flush=True)
    out = open(fn_out, 'a', encoding='utf-8'); cnt = [0]
    def work(r):
        try: res = fn(r)
        except Exception as e: res = {'error': repr(e)[:200]}
        res['key'] = keyf(r)
        with lock:
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 100 == 0: print(task, cnt[0], '/', len(todo), flush=True)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=threads) as ex: list(ex.map(work, todo))
    print(task, 'DONE', flush=True)
def get(url, timeout=60, tries=2, headers=None):
    for i in range(tries):
        try: return requests.get(url, timeout=timeout, headers={'User-Agent': UA, **(headers or {})})
        except Exception: time.sleep(2 * (i + 1))
    return None
# ---- Tavily (page extraction), budget read live: the pay-as-you-go limit of record is the ceiling
TH = {'Authorization': 'Bearer ' + E.get('TAVILY_API_KEY', '')}
def tavily_usage():
    try: return requests.get('https://api.tavily.com/usage', headers=TH, timeout=20).json().get('account', {})
    except Exception: return {}
_u = tavily_usage(); TAVILY_LEFT = int(E.get('TAVILY_CAP') or max(0, int(_u.get('paygo_limit') or 400000) - int(_u.get('paygo_usage') or 0) - 10000)); _TAV = [0]
def tavily_extract(urls, depth='basic'):
    with lock:
        if _TAV[0] >= TAVILY_LEFT: return {'error': 'tavily ceiling', 'results': []}
        _TAV[0] += 1
    for i in range(3):
        try:
            r = requests.post('https://api.tavily.com/extract', headers={**TH, 'Content-Type': 'application/json'}, json={'urls': urls, 'extract_depth': depth}, timeout=180)
            if r.status_code in (429, 500, 502, 503): time.sleep(6 * (i + 1)); continue
            return r.json()
        except Exception as e: err = repr(e)
        time.sleep(4)
    return {'error': 'exhausted', 'results': []}
# ---- labs (reading order of record: Perplexity → Grok → Mistral review only)
def perplexity_agent(prompt, preset='low'):
    """Perplexity Agent API (POST /v1/responses). Sources only from the search_results output item, never from the prose."""
    for i in range(5):
        r = requests.post('https://api.perplexity.ai/v1/responses', headers={'Authorization': 'Bearer ' + E['PERPLEXITY_API_KEY'], 'Content-Type': 'application/json'}, json={'preset': preset, 'input': prompt}, timeout=240)
        if r.status_code in (429, 500, 502, 503): time.sleep(6 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}', 'sources': []}
        j = r.json(); txt = ''; sources = []
        for o in j.get('output', []):
            if o.get('type') == 'search_results':
                for s in o.get('results', []) or []: sources.append({'url': s.get('url'), 'title': s.get('title'), 'date': s.get('date') or s.get('last_updated'), 'snippet': (s.get('snippet') or '')[:400]})
            if o.get('type') == 'message':
                for c in o.get('content', []) or []:
                    if c.get('type') == 'output_text': txt += c.get('text', '')
        u = j.get('usage') or {}
        return {'text': txt, 'sources': sources, 'usage': u, 'cost': (u.get('cost') or {}), 'model': j.get('model'), 'preset': preset}
    return {'error': 'exhausted', 'sources': []}
def grok(prompt, model='grok-4.6', tools=({'type': 'web_search'},)):
    for i in range(4):
        r = requests.post('https://api.x.ai/v1/responses', headers={'Authorization': 'Bearer ' + E['XAI_API_KEY']}, json={'model': model, 'input': prompt, 'tools': list(tools)}, timeout=300)
        if r.status_code in (429, 500, 502, 503): time.sleep(8 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}'}
        j = r.json(); txt = ''; cites = []
        for o in j.get('output', []):
            if o.get('type') == 'message':
                for c in o.get('content', []):
                    if c.get('type') == 'output_text':
                        txt += c.get('text', ''); cites += [a.get('url') for a in (c.get('annotations') or []) if a.get('url')]
        return {'text': txt, 'citations': cites, 'usage': j.get('usage', {}), 'model': j.get('model')}
    return {'error': 'exhausted'}
def mistral(prompt, model='mistral-small-latest'):
    for i in range(5):
        r = requests.post('https://api.mistral.ai/v1/chat/completions', headers={'Authorization': 'Bearer ' + E['MISTRAL_API_KEY']},
                          json={'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0, 'response_format': {'type': 'json_object'}}, timeout=180)
        if r.status_code in (429, 500, 502, 503): time.sleep(6 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}'}
        j = r.json(); return {'text': j['choices'][0]['message']['content'], 'usage': j.get('usage', {}), 'model': j.get('model')}
    return {'error': 'exhausted'}
def jparse(txt):
    if not txt: return None
    m = re.search(r'\{.*\}', txt, re.S)
    try: return json.loads(m.group(0) if m else txt)
    except Exception: return None
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', html.unescape(str(s or '')).lower().replace('&', ' and ')).strip()
FIRM_STOP = {'limited', 'ltd', 'company', 'co', 'the', 'hong', 'kong', 'cpa', 'certified', 'public', 'accountants', 'llp', 'and', 'registered', 'entity', 'auditor', 'pie', 'investor', 'services', 'share', 'registrar', 'registrars', 'of', 'branch', 'hk'}
def firm_tokens(s): return {t for t in norm(s).split() if t not in FIRM_STOP and len(t) > 1}
def same_firm(a, b):
    ta, tb = firm_tokens(a), firm_tokens(b)
    return bool(ta and tb and (ta <= tb or tb <= ta or len(ta & tb) >= max(1, min(len(ta), len(tb)) - 0)))
