"""Shared pieces for the United Kingdom Fill + Confirm rail (passes 2 and 3). Same shape as the Canada rail; UK pockets."""
import os, sys, re, json, time, threading, html, datetime
import requests, openpyxl
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\uk-width1'); sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0')
import keys
from common import norm, keytoks, to_iso, url_date, get, tavily, wire_of, classify, load_issuers, key, TODAY, name_match, _common_words, _unique_tokens, STOP, lock, UA, TH, TABS, event, CH_KEY
ISSUERS_XLSX = r'C:\ALLOOLOO\CM-KG\ISSUERS\uk-issuers.xlsx'
EVENTS_JSONL = r'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\uk-events.jsonl'
W0 = r'C:\ALLOOLOO\CM-KG\RAILS\uk-width0\raw'; W1 = r'C:\ALLOOLOO\CM-KG\RAILS\uk-width1\raw'
os.makedirs('raw', exist_ok=True); os.makedirs('raw/bodies', exist_ok=True)
E = os.environ
import pond
NODE = 'uk-cm-kg'
def jload(fn):
    """pond rule 3: a raw/<file> is read from every drop of this rail (newest wins per 'key' when rows carry one, union otherwise) plus the working folder"""
    out = []; seen = set()
    paths = ([p for d, p in pond.drops(NODE, 'fill-confirm')] + (['raw'] if os.path.isdir('raw') else [])) if fn.startswith('raw/') and fn.count('/') == 1 else [None]
    for p in paths:
        f = fn if p is None else os.path.join(p, os.path.basename(fn)); rp = os.path.realpath(f)
        if not os.path.exists(f) or rp in seen: continue
        seen.add(rp)
        for line in open(f, encoding='utf-8'):
            try: out.append(json.loads(line))
            except Exception: pass
    if out and all(isinstance(d, dict) and 'key' in d for d in out[:50]):
        byk = {}
        for d in out: byk[d.get('key')] = d   # newest drop last -> wins
        return list(byk.values())
    return out
def events(): return jload(EVENTS_JSONL)
def all_rows():
    """every row of uk-issuers.xlsx (1,570) as dicts with the tab name"""
    wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True); out = []
    for ex in TABS:
        ws = wb[ex]; it = ws.iter_rows(values_only=True); hdr = next(it)
        for r in it:
            d = dict(zip(hdr, r)); d['_tab'] = ex; out.append(d)
    return out
def resume(task, fn, items, threads=4, keyf=None, delay=0.0):
    keyf = keyf or (lambda r: r['exchange'] + '|' + r['ticker'])
    fn_out = f'raw/{task}.jsonl'; done = set()
    for d in jload(fn_out): done.add(d.get('key'))
    todo = [r for r in items if keyf(r) not in done]
    print(task, 'todo', len(todo), 'done', len(done), flush=True)
    out = open(fn_out, 'a', encoding='utf-8'); cnt = [0]
    def work(r):
        if delay: time.sleep(delay)
        try: res = fn(r)
        except Exception as e: res = {'error': repr(e)[:200]}
        res['key'] = keyf(r)
        with lock:
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); cnt[0] += 1
            if cnt[0] % 50 == 0: print(task, cnt[0], '/', len(todo), flush=True)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=threads) as ex: list(ex.map(work, todo))
    print(task, 'DONE', flush=True)
# ---- labs
def claude(prompt, system='', model='claude-sonnet-5', max_tokens=800):
    for i in range(5):
        r = requests.post('https://api.anthropic.com/v1/messages', headers={'x-api-key': E['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
                          json={'model': model, 'max_tokens': max_tokens, 'system': system, 'messages': [{'role': 'user', 'content': prompt}]}, timeout=180)
        if r.status_code in (429, 500, 502, 503, 529): time.sleep(6 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}'}
        j = r.json(); txt = ''.join(b.get('text', '') for b in j.get('content', []) if b.get('type') == 'text')
        return {'text': txt, 'usage': j.get('usage', {}), 'model': j.get('model')}
    return {'error': 'exhausted'}
def gemini(prompt, model='gemini-flash-latest'):
    for i in range(5):
        r = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={E["GEMINI_API_KEY"]}',
                          json={'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0, 'responseMimeType': 'application/json'}}, timeout=240)
        if r.status_code in (429, 500, 502, 503): time.sleep(8 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}'}
        j = r.json()
        try: txt = j['candidates'][0]['content']['parts'][0]['text']
        except Exception: return {'error': 'no text', 'raw': json.dumps(j)[:300]}
        return {'text': txt, 'usage': j.get('usageMetadata', {}), 'model': model}
    return {'error': 'exhausted'}
def mistral(prompt, model='mistral-small-latest'):
    for i in range(5):
        r = requests.post('https://api.mistral.ai/v1/chat/completions', headers={'Authorization': 'Bearer ' + E['MISTRAL_API_KEY']},
                          json={'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0, 'response_format': {'type': 'json_object'}}, timeout=180)
        if r.status_code in (429, 500, 502, 503): time.sleep(6 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}'}
        j = r.json(); return {'text': j['choices'][0]['message']['content'], 'usage': j.get('usage', {}), 'model': j.get('model')}
    return {'error': 'exhausted'}
def perplexity(prompt, model='sonar-pro'):
    for i in range(5):
        r = requests.post('https://api.perplexity.ai/chat/completions', headers={'Authorization': 'Bearer ' + E['PERPLEXITY_API_KEY']},
                          json={'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0}, timeout=180)
        if r.status_code in (429, 500, 502, 503): time.sleep(6 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}'}
        j = r.json(); return {'text': j['choices'][0]['message']['content'], 'citations': j.get('citations', []), 'usage': j.get('usage', {}), 'model': j.get('model')}
    return {'error': 'exhausted'}
def perplexity_agent(prompt, preset='low'):
    """Perplexity Agent API (POST /v1/responses, preset 'low' = grounded page recovery, 'fast' = cold single-fact read). Replaces sonar-pro from
    ORDER-010 Part B (Sonar Chat Completions retire 2026-09-27). Sources come from the search_results item in the output array; the answer text
    from the message item. Returns {'text', 'sources': [{url, title, date, snippet}], 'usage', 'cost', 'model', 'preset'}."""
    for i in range(5):
        r = requests.post('https://api.perplexity.ai/v1/responses', headers={'Authorization': 'Bearer ' + E['PERPLEXITY_API_KEY'], 'Content-Type': 'application/json'},
                          json={'preset': preset, 'input': prompt}, timeout=240)
        if r.status_code in (429, 500, 502, 503): time.sleep(6 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}', 'sources': []}
        j = r.json(); txt = ''; sources = []
        for o in j.get('output', []):
            if o.get('type') == 'search_results':
                for s in o.get('results', []) or []: sources.append({'url': s.get('url'), 'title': s.get('title'), 'date': s.get('date') or s.get('last_updated'), 'snippet': (s.get('snippet') or '')[:300]})
            if o.get('type') == 'message':
                for c in o.get('content', []) or []:
                    if c.get('type') == 'output_text': txt += c.get('text', '')
        u = j.get('usage') or {}
        return {'text': txt, 'sources': sources, 'usage': u, 'cost': (u.get('cost') or {}), 'model': j.get('model'), 'preset': preset, 'id': j.get('id')}
    return {'error': 'exhausted', 'sources': []}
def grok(prompt, model='grok-4.6', tools=({'type': 'web_search'}, {'type': 'x_search'})):
    for i in range(4):
        r = requests.post('https://api.x.ai/v1/responses', headers={'Authorization': 'Bearer ' + E['XAI_API_KEY']}, json={'model': model, 'input': prompt, 'tools': list(tools)}, timeout=300)
        if r.status_code in (429, 500, 502, 503): time.sleep(8 * (i + 1)); continue
        if not r.ok: return {'error': f'{r.status_code} {r.text[:200]}'}
        j = r.json(); txt = ''
        for o in j.get('output', []):
            if o.get('type') == 'message':
                for c in o.get('content', []):
                    if c.get('type') == 'output_text': txt += c.get('text', '')
        cites = []
        for o in j.get('output', []):
            for c in o.get('content', []) if isinstance(o.get('content'), list) else []:
                for a in c.get('annotations', []) or []:
                    if a.get('url'): cites.append(a['url'])
        return {'text': txt, 'citations': cites, 'usage': j.get('usage', {}), 'model': j.get('model')}
    return {'error': 'exhausted'}
# ---- Tavily budget guard. Plan moved to Growth (100,000 credits/month) on 2026-09-11; the cap is the plan limit less a 10 % floor,
# read live from /usage at import (fallback 90,000). Every worker here calls tavily() through this wrapper; past the cap it returns
# {'error': 'tavily cap'} and the field stays sourced. Override with TAVILY_CAP.
def _tavily_cap():
    if E.get('TAVILY_CAP'): return int(E['TAVILY_CAP'])
    try:
        a = requests.get('https://api.tavily.com/usage', headers=TH, timeout=20).json().get('account', {})
        lim = int(a.get('plan_limit') or 100000); used = int(a.get('plan_usage') or 0)
        return max(0, int(lim * 0.9) - used)
    except Exception: return 90000
_TAV_CALLS = [0]; TAVILY_CAP = _tavily_cap()
_tavily_raw = tavily
def tavily(payload):
    with lock:
        if _TAV_CALLS[0] >= TAVILY_CAP: return {'error': 'tavily cap', 'results': []}
        _TAV_CALLS[0] += 1
    return _tavily_raw(payload)
def jparse(txt):
    if not txt: return None
    m = re.search(r'\{.*\}', txt, re.S)
    try: return json.loads(m.group(0) if m else txt)
    except Exception: return None
def page_text(url, timeout=40, ua=None):
    """fetch a page and return visible text"""
    h = {'User-Agent': ua} if ua else ({'User-Agent': 'curl/8.0'} if 'globenewswire' in url else None)
    x = get(url, tries=2, timeout=timeout, headers=h)
    if x is None or x.status_code != 200: return None, (x.status_code if x else None)
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', x.text, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t)); t = re.sub(r'\s+', ' ', t)
    return t, 200
def ch_api(path, **params):
    for attempt in range(5):
        try:
            r = requests.get('https://api.company-information.service.gov.uk' + path, params=params, auth=(CH_KEY, ''), timeout=60)
            if r.status_code == 429: time.sleep(30); continue
            if r.status_code == 404: return None
            r.raise_for_status(); return r.json()
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None
def all_aliases():
    """every sourced alias per issuer key: from alias_sources.py plus Perplexity-found page names"""
    out = {}
    for d in jload('raw/aliases.jsonl'):
        for a in d.get('aliases', []): out.setdefault(d['key'], []).append(a)
    for d in jload('raw/perplexity_pages.jsonl'):
        if d.get('verified') and d.get('alias'): out.setdefault(d['key'], []).append({'alias': d['alias'], 'source': d['url'], 'read_by': d.get('alias_read_by', 'issuer news page (found by Perplexity (agent))')})
    return out
