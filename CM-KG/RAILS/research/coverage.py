r"""coverage.py — USR-01 (2026-11-11): the two new public research fields, read per issuer with the source page and read date on each row.
  coverage        which research houses cover the issuer — from the issuer's own investor-relations page (and filings); how many; since when where the page says
  open_research   every openly published research note on the issuer (issuer-sponsored and independent publishers): one dated, sourced, linked row each
Reader: Perplexity (sonar) finds the pages — one search call per issuer, no Tavily (OFF by the CEO's standing order). Sourced or blank: a house is kept only
when this rail fetches the cited page itself and reads the house's name on it, and the page is not an aggregator; an open-research row is kept only when
its link answers and the page names the issuer. What cannot be read on the page is dropped and the page is listed in pages_checked. A non-English page on a
European node is read through Mistral (mistral-small-latest) for the house names, as the fill rails do. Nothing is inferred; none found is a stated result.
Drop: CM-KG\POND\<cc>-cm-kg\research-coverage\<date>\raw.jsonl (append; a re-run the same day resumes), spend.json beside.
Usage: python -X utf8 coverage.py <cc> [--limit N] [--threads N]"""
import sys, os, re, json, html, time, datetime, threading, urllib.request, urllib.error, urllib.parse, concurrent.futures as cf
KEYS = r'C:\ALLOOLOO\AGENT KEYS'; NUM = r'C:\ALLOOLOO\CM-KG\RESEARCH\numbers'; POND = r'C:\ALLOOLOO\CM-KG\POND'
key = lambda n: open(os.path.join(KEYS, n + '.txt'), encoding='utf-8').read().strip().splitlines()[0]
PPLX = key('perplexity'); TODAY = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
EU_MISTRAL = {'de', 'fr', 'nl', 'ch', 'it', 'es', 'se', 'dk', 'no', 'fi', 'be', 'at', 'pl', 'pt', 'lu', 'gr', 'cz'}
AGG = ('marketbeat', 'tipranks', 'yahoo', 'seekingalpha', 'zacks', 'investing.com', 'marketwatch', 'benzinga', 'stockanalysis', 'wallstreetzen', 'simplywall', 'fintel', 'gurufocus', 'morningstar', 'nasdaq.com', 'tradingview', 'wikipedia', 'reddit', 'barchart', 'marketscreener', 'macrotrends', 'finviz', 'investopedia', 'cnbc', 'bloomberg', 'reuters', 'wsj.com', 'ft.com', 'fool.com', 'google.', 'msn.com', 'stocktwits', 'x.com', 'twitter', 'linkedin', 'facebook', 'youtube', 'perplexity')
UA = {'User-Agent': 'Mozilla/5.0 (compatible; Allooloo research read; +https://allooloo.io)', 'Accept': 'text/html,application/xhtml+xml,application/pdf;q=0.8,*/*;q=0.5', 'Accept-Language': 'en'}
SP = {'calls': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'mistral_calls': 0, 'mistral_tokens': 0, 'fetches': 0}; LOCK = threading.Lock()
def post(url, body, headers, timeout=120):
    for i in range(5):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', **headers}), timeout=timeout).read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529): time.sleep(6 * (i + 1)); continue
            return {'error': f'{e.code} {e.read()[:160]!r}'}
        except Exception as e: time.sleep(3 * (i + 1)); err = repr(e)[:120]
    return {'error': 'exhausted'}
def page(url):
    """the page as this rail reads it: (visible text, status). PDFs and blocked pages return (None, status)."""
    with LOCK: SP['fetches'] += 1
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25); ct = r.headers.get('content-type') or ''; raw = r.read(1500000)
        if 'html' not in ct and 'text' not in ct: return None, f'{r.status} {ct.split(";")[0]}'
        t = raw.decode(r.headers.get_content_charset() or 'utf-8', 'replace'); t = re.sub(r'(?is)<script.*?</script>|<style.*?</style>|<!--.*?-->', ' ', t)
        return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t))), r.status
    except urllib.error.HTTPError as e: return None, e.code
    except Exception as e: return None, type(e).__name__
norm = lambda s: re.sub(r'[^a-z0-9]+', ' ', str(s or '').lower()).strip()
STOP = {'inc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited', 'plc', 'holdings', 'holding', 'group', 'the', 'sa', 'ag', 'nv', 'se', 'llc', 'lp', 'trust', 'fund', 'etf', 'class', 'common', 'stock', 'de', 'and', 'of'}
def names_issuer(text, name, ticker):
    toks = [t for t in norm(name).split() if t not in STOP and len(t) > 2][:2]; n = norm(text)
    return bool(toks) and all(t in n for t in toks)
def focus(t):
    i = [m.start() for m in re.finditer(r'(?i)analyst coverage|covered by|research coverage|analysts?\b', t)]; a = max(0, (i[0] if i else 0) - 1500); return t[a:a + 12000]
def haiku_houses(text, name):
    """the page's own list of research houses, read off the fetched text (Claude, Haiku class); every name is then checked against the page by this rail"""
    j = post('https://api.anthropic.com/v1/messages', {'model': 'claude-haiku-5-5', 'max_tokens': 900, 'thinking': {'type': 'disabled'}, 'messages': [{'role': 'user', 'content': f'The text below is a web page about {name}. If it lists research houses (brokers, banks, research firms) that cover the company, list them exactly as written on the page, with the analyst name where the page gives one. JSON only: {{"houses": [{{"house": "", "analyst": null}}]}}. If the page lists none, return an empty list. Do not add any house that is not written on the page.\n\n' + focus(text)}]}, {'x-api-key': key('claude'), 'anthropic-version': '2023-06-01'})
    u = j.get('usage') or {}
    with LOCK: SP['haiku_calls'] = SP.get('haiku_calls', 0) + 1; SP['haiku_in'] = SP.get('haiku_in', 0) + u.get('input_tokens', 0); SP['haiku_out'] = SP.get('haiku_out', 0) + u.get('output_tokens', 0)
    try: m = re.search(r'\{.*\}', ''.join(b.get('text', '') for b in j['content'] if b.get('type') == 'text'), re.S); return [h for h in json.loads(m.group(0)).get('houses') or [] if isinstance(h, dict) and h.get('house')]
    except Exception: return []
def mistral_houses(text, name):
    j = post('https://api.mistral.ai/v1/chat/completions', {'model': 'mistral-small-latest', 'temperature': 0, 'response_format': {'type': 'json_object'}, 'messages': [{'role': 'user', 'content': f'The text below is an investor-relations page of {name}. List the research houses (brokers, banks, research firms) the page names as covering the company, exactly as written on the page. JSON only: {{"houses": ["..."]}}. If the page names none, return an empty list.\n\n{text[:14000]}'}]}, {'Authorization': 'Bearer ' + key('mistral')})
    with LOCK: SP['mistral_calls'] += 1; SP['mistral_tokens'] += (j.get('usage') or {}).get('total_tokens', 0)
    try: return json.loads(j['choices'][0]['message']['content']).get('houses') or []
    except Exception: return []
PROMPT = """Issuer: {name} — listed on {exchange}, ticker {ticker}{isin}.
Task A (coverage): find the issuer's OWN investor-relations page that lists the sell-side or independent research houses covering it (often titled "Analyst Coverage"). Give that page's URL and the research houses it names, exactly as written, with the analyst name and an initiation date only if the page states them.
Task B (open research): find research notes on this issuer that are published openly and free to read in full (issuer-sponsored research such as Edison, Zacks SCR, Sidoti-style sponsored notes, Hardman, Trinity Delta; or independent publishers). Give each note's publisher, title, publication date (YYYY-MM-DD) and direct URL. News articles, press releases, price-target aggregators and paywalled reports are not research notes.
Reply with JSON only, no prose: {{"coverage_page": "<url or null>", "houses": [{{"house": "", "analyst": null, "since": null}}], "open_research": [{{"publisher": "", "title": "", "date": "", "url": "", "kind": "issuer-sponsored|independent"}}]}}. If you cannot find a page for A or any note for B, return null and empty lists. Do not guess."""
def read_one(o, cc):
    idn = o['identity']; v = lambda k: idn[k].get('value'); name, tick, ex = v('name'), v('ticker'), v('exchange')
    j = post('https://api.perplexity.ai/chat/completions', {'model': 'sonar', 'temperature': 0, 'messages': [{'role': 'user', 'content': PROMPT.format(name=name, exchange=ex, ticker=tick, isin=f", ISIN {v('isin')}" if v('isin') else '')}]}, {'Authorization': 'Bearer ' + PPLX})
    res = {'cmr': o['cmr'], 'read_date': TODAY, 'engine': 'Perplexity sonar (search) · page read by this rail'}
    if j.get('error'): res['error'] = j['error']; return res
    u = j.get('usage') or {}
    with LOCK: SP['calls'] += 1; SP['prompt_tokens'] += u.get('prompt_tokens', 0); SP['completion_tokens'] += u.get('completion_tokens', 0); SP['cost'] += ((u.get('cost') or {}).get('total_cost') or 0)
    txt = j['choices'][0]['message']['content']; m = re.search(r'\{.*\}', txt, re.S)
    try: a = json.loads(m.group(0)) if m else {}
    except Exception: a = {}
    checked = []; houses = []; cp = a.get('coverage_page') if isinstance(a.get('coverage_page'), str) and a.get('coverage_page', '').startswith('http') else None
    if cp:
        host = urllib.parse.urlparse(cp).netloc.lower()
        if any(g in host for g in AGG) or 'sec.gov' in host: checked.append({'page': cp, 'result': 'not the issuer\'s own investor-relations page — not read'})
        else:
            t, st = page(cp)
            if t is None: checked.append({'page': cp, 'result': f'not readable by this rail ({st})'})
            else:
                n = norm(t); claimed = [h for h in (a.get('houses') or []) if isinstance(h, dict) and h.get('house')]
                if cc in EU_MISTRAL and not re.search(r'\b(analyst|coverage|research)\b', t, re.I): claimed = claimed + [{'house': h} for h in mistral_houses(t, name)]; rb = 'issuer IR page, fetched by this rail; house names read through Mistral (mistral-small-latest), each then found on the page'
                else: claimed = claimed + (haiku_houses(t, name) if names_issuer(t, name, tick) else []); rb = 'issuer IR page, fetched by this rail; each house name read on the page'
                for h in claimed:
                    hn = norm(h['house']); core = ' '.join(w for w in hn.split() if w not in STOP)[:40]
                    if core and len(core) > 2 and core in n and not any(x['house'].lower() == h['house'].lower() for x in houses):
                        houses.append({'house': h['house'], **({'analyst': h['analyst']} if h.get('analyst') and norm(h['analyst']) in n else {}), **({'since': h['since']} if h.get('since') and str(h['since'])[:4] in t else {}), 'source': cp, 'read_date': TODAY, 'read_by': rb, 'state': 'sourced'})
                checked.append({'page': cp, 'result': f'read: {len(houses)} of {len(claimed)} named houses found on the page' + ('' if names_issuer(t, name, tick) else '; the page does not name the issuer')})
                if not names_issuer(t, name, tick): houses = []
    rows = []
    for r in (a.get('open_research') or [])[:12]:
        if not (isinstance(r, dict) and str(r.get('url') or '').startswith('http') and r.get('publisher')): continue
        url = r['url']; host = urllib.parse.urlparse(url).netloc.lower()
        if any(g in host for g in AGG): checked.append({'page': url, 'result': 'an aggregator or news site — not a research note'}); continue
        t, st = page(url)
        if t is None and not str(st).startswith('200'): checked.append({'page': url, 'result': f'not readable by this rail ({st})'}); continue
        if t is not None and not names_issuer(t, name, tick): checked.append({'page': url, 'result': 'read: the page does not name the issuer'}); continue
        d = str(r.get('date') or '')[:10]; d = d if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d) else None
        rows.append({'date': d, 'publisher': r['publisher'], 'title': r.get('title') or None, 'kind': r.get('kind') if r.get('kind') in ('issuer-sponsored', 'independent') else None, 'source': url, 'read_date': TODAY, 'read_by': 'the note\'s own page, fetched by this rail' if t is not None else f'the note\'s link answers ({st}); a document, not read as text', 'state': 'sourced'})
    res['coverage'] = {'state': 'found' if houses else 'none_found', 'houses': houses, 'count': len(houses), 'since': 'stated per house where the page states it' if any('since' in h for h in houses) else 'not stated on the page read' if houses else None, 'read_date': TODAY}
    res['open_research'] = {'state': 'found' if rows else 'none_found', 'rows': sorted(rows, key=lambda x: (x['date'] or '', x['source']), reverse=True), 'read_date': TODAY}
    res['pages_checked'] = checked; return res
def main():
    a = sys.argv[1:]; cc = a[0]; lim = int(a[a.index('--limit') + 1]) if '--limit' in a else None; th = int(a[a.index('--threads') + 1]) if '--threads' in a else 12
    drop = a[a.index('--drop') + 1] if '--drop' in a else TODAY; only = set(a[a.index('--only') + 1].split(',')) if '--only' in a else None
    d = os.path.join(POND, f'{cc}-cm-kg', 'research-coverage', drop); os.makedirs(d, exist_ok=True); raw = os.path.join(d, 'raw.jsonl')
    done = {json.loads(l)['cmr'] for l in open(raw, encoding='utf-8')} if os.path.exists(raw) else set()
    todo = [o for o in (json.loads(l) for l in open(os.path.join(NUM, f'{cc}.jsonl'), encoding='utf-8')) if o['cmr'] not in done and o['identity']['name'].get('value') and (not only or o['cmr'].split('/')[-1] in only)]
    if lim: todo = todo[:lim]
    print(cc, 'to read', len(todo), 'already read', len(done), flush=True); n = [0]
    with open(raw, 'a', encoding='utf-8') as out, cf.ThreadPoolExecutor(th) as ex:
        for res in ex.map(lambda o: read_one(o, cc), todo):
            if res.get('error'): print('ERR', res['cmr'], res['error'][:100], flush=True); continue
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); n[0] += 1
            if n[0] % 250 == 0: print(cc, n[0], '/', len(todo), json.dumps(SP), flush=True)
    sp = os.path.join(d, 'spend.json'); prev = json.load(open(sp)) if os.path.exists(sp) else {}
    json.dump({k: prev.get(k, 0) + v for k, v in SP.items()}, open(sp, 'w'), indent=1); print(cc, 'DONE', n[0], json.dumps(SP), flush=True)
main()
