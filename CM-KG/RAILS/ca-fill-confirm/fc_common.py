"""Shared pieces for the Canada Fill + Confirm rail (passes 2 and 3)."""
import os, sys, re, json, time, threading, html, datetime
import requests, openpyxl
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\ca-width1'); sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\ca-width0')
import keys
from common import norm, keytoks, to_iso, url_date, get, tavily, wire_of, classify, load_issuers, key, TODAY, name_match, _common_words, _unique_tokens, STOP, lock, UA, TH
ISSUERS_XLSX = r'C:\ALLOOLOO\CM-KG\ISSUERS\ca-issuers.xlsx'
EVENTS_JSONL = r'C:\ALLOOLOO\CM-KG\DISCLOSURE\events\ca-events.jsonl'
W1 = r'C:\ALLOOLOO\CM-KG\RAILS\ca-width1\raw'
os.makedirs('raw', exist_ok=True); os.makedirs('raw/bodies', exist_ok=True)
E = os.environ
def jload(fn):
    out = []
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try: out.append(json.loads(line))
            except Exception: pass
    return out
def events(): return jload(EVENTS_JSONL)
def all_rows():
    """every row of ca-issuers.xlsx (4,820) as dicts with the tab name"""
    wb = openpyxl.load_workbook(ISSUERS_XLSX, read_only=True); out = []
    for ex in ['TSX', 'TSXV', 'CSE', 'Cboe Canada']:
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
def cision_page_name(page_html):
    """the company name a Cision / PR Newswire company page shows: <h1>'News from X …' or <title>'X Press Releases | Cision' / 'X News Releases | PR Newswire'"""
    if not page_html: return ''
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', page_html, re.S)
    h1t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', h1.group(1)))).strip() if h1 else ''
    mm = re.match(r'(?:News from|Nouvelles de)\s+(.+?)(?:\s+A wide array.*|\s+Press Releases.*|\s+News Releases.*|\s+Communiqués.*|\s*\|.*)?$', h1t, re.I)
    if mm: return mm.group(1).strip()
    t = re.search(r'<title>(.*?)</title>', page_html, re.S)
    tt = re.sub(r'\s+', ' ', html.unescape(t.group(1))).strip() if t else ''
    mm = re.match(r'(.+?)\s+(?:Press Releases|News Releases|Communiqués de presse)\s*\|', tt, re.I)
    return mm.group(1).strip() if mm else ''
def perplexity_aliases():
    """Aliases from the wire company pages Perplexity located: the alias is what the issuer's OWN listing page shows (Cision / PR Newswire h1,
    Newsfile page path, GlobeNewswire organization name in the URL) — never Perplexity's own wording. Release pages are not alias sources."""
    fn = 'raw/perplexity_aliases.json'
    if os.path.exists(fn): return json.load(open(fn, encoding='utf-8'))
    out = {}
    from urllib.parse import unquote
    for d in jload('raw/perplexity_pages.jsonl'):
        if not d.get('verified'): continue
        u = d['url']; name = ''; rb = ''
        m = re.match(r'https?://(?:www\.)?(newswire\.ca|prnewswire\.com)/news/([^/?]+)/?$', u)
        if m:
            x = get(u, tries=1, timeout=40)
            h1 = re.search(r'<h1[^>]*>(.*?)</h1>', x.text, re.S) if x is not None and x.status_code == 200 else None
            name = cision_page_name(x.text if x is not None and x.status_code == 200 else ''); rb = f'{m.group(1)} company page (found by Perplexity (agent))'
        m2 = re.match(r'https?://(?:www\.)?newsfilecorp\.com/company/\d+/([^/?]+)', u)
        if m2: name = unquote(m2.group(1)).replace('-', ' ').strip(); rb = 'newsfilecorp.com company page path (found by Perplexity (agent))'
        # GlobeNewswire /search/organization/<term> is a search page built from a query, not the issuer's own page: not an alias source
        legal = next((r['name'] for r in load_issuers() if key(r) == d['key']), '')
        if name and len(name) >= 3 and 'wide array' not in name.lower() and norm(name).replace(' ', '') != norm(legal).replace(' ', ''):
            out[d['key']] = {'alias': name, 'source': u, 'read_by': rb}
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return out
def website_aliases():
    """aliases read by website_alias.py: the issuer's own website <title>, site taken from the exchange profile's website field"""
    out = {}
    for d in jload('raw/website_aliases.jsonl'):
        if d.get('alias'): out[d['key']] = {'alias': d['alias'], 'source': d['website'], 'read_by': d['read_by']}
    return out
def jparse(txt):
    if not txt: return None
    m = re.search(r'\{.*\}', txt, re.S)
    try: return json.loads(m.group(0) if m else txt)
    except Exception: return None
def page_text(url, timeout=40, ua=None):
    """fetch a page and return visible text (GlobeNewswire only answers a plain UA)"""
    h = {'User-Agent': ua} if ua else ({'User-Agent': 'curl/8.0'} if 'globenewswire' in url else None)
    x = get(url, tries=2, timeout=timeout, headers=h)
    if x is None or x.status_code != 200: return None, (x.status_code if x else None)
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', x.text, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t)); t = re.sub(r'\s+', ' ', t)
    return t, 200
