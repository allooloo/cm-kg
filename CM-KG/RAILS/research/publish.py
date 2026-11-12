r"""publish.py — USR-03 (2026-11-11): a market's research pages into the page store (Cloudflare KV allooloo-research, read by getresearch.ai and by
get_research on the apex router).  p:<cmr> = the page · i:<cc> = the market's index (exchange, code, name, ticker, ISIN, LEI) · meta = the publish ledger
(pages, record as-of, coverage found / none found / not read, open-research rows, licensed rows per market).
Write-on-change: only a page whose numbers_hash differs from the one last published is sent (ledger CM-KG\RESEARCH\published\<cc>.json). A page whose
issuer left the record is not removed here (Rule One); it is listed in the run's output for the CEO. The Cloudflare token is read in-process, never printed.
Usage: python -X utf8 publish.py <cc> [...]     exit 1 on a failed market"""
import sys, os, json, time, datetime, urllib.request, urllib.error
R = r'C:\ALLOOLOO\CM-KG\RESEARCH'; A = 'dd2832b36f171b815f84c8487aada36b'; NS = '7d0e0e4a059e444982b5eb1cc500efc1'
TOK = os.environ.get('CLOUDFLARE_KV_TOKEN') or open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare.txt', encoding='utf-8').read().strip().splitlines()[0]; BASE = f'https://api.cloudflare.com/client/v4/accounts/{A}/storage/kv/namespaces/{NS}'
def api(path, method='GET', body=None, raw=False):
    for i in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(BASE + path, method=method, data=body, headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json', 'User-Agent': 'Allooloo research publish'}), timeout=180).read()
            return r if raw else json.loads(r)
        except urllib.error.HTTPError as e:
            if e.code == 404 and raw: return None
            if e.code in (429, 500, 502, 503, 520, 524): time.sleep(8 * (i + 1)); continue
            raise RuntimeError(f'{e.code} {e.read()[:200]!r}')
        except Exception as e:
            if i == 5: raise
            time.sleep(5 * (i + 1))
    raise RuntimeError('retries')
def bulk(pairs):
    batch = []; size = 0; sent = 0
    def flush():
        nonlocal batch, size, sent
        if not batch: return
        r = api('/bulk', 'PUT', json.dumps(batch).encode());
        if not r.get('success'): raise RuntimeError(json.dumps(r.get('errors'))[:200])
        sent += len(batch); batch = []; size = 0
    for k, v in pairs:
        s = json.dumps(v, ensure_ascii=False, separators=(',', ':')); batch.append({'key': k, 'value': s}); size += len(s.encode())
        if len(batch) >= 2000 or size > 40_000_000: flush()
    flush(); return sent
def publish(cc):
    pages = [json.loads(l) for l in open(os.path.join(R, 'pages', f'{cc}.jsonl'), encoding='utf-8')]; man = json.load(open(os.path.join(R, 'pages', f'{cc}.manifest.json')))
    os.makedirs(os.path.join(R, 'published'), exist_ok=True); lf = os.path.join(R, 'published', f'{cc}.json'); led = json.load(open(lf)) if os.path.exists(lf) else {}
    import hashlib; ph = lambda p: 'page:' + hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()   # the page as written (a page rewritten over the same numbers is a changed page)
    todo = [p for p in pages if led.get(p['cmr']) != ph(p)]; gone = sorted(set(led) - {p['cmr'] for p in pages})
    n = bulk((('p:' + p['cmr'], p) for p in todo))
    v = lambda p, k: p['numbers']['identity'][k].get('value')
    ix = {'as_of': man['record_as_of'], 'issuers': sorted(([p['cmr'].split('/', 2)[1], p['cmr'].split('/', 2)[2], v(p, 'name'), v(p, 'ticker'), v(p, 'isin'), v(p, 'lei')] for p in pages), key=lambda x: (str(x[2] or '').lower(), x[0], x[1]))}
    bulk([('i:' + cc, ix)])
    led = {p['cmr']: ph(p) for p in pages} | {c: led[c] for c in gone}; json.dump(led, open(lf, 'w'))
    # the ledger is rebuilt whole from the manifests of every market published (the store is eventually consistent: a read-then-write of meta loses markets)
    meta = {'markets': {}}
    for f in sorted(os.listdir(os.path.join(R, 'published'))):
        c2 = f[:-5]; m2 = json.load(open(os.path.join(R, 'pages', f'{c2}.manifest.json')))
        meta['markets'][c2] = {k: m2[k] for k in ('pages', 'by_engine', 'by_template', 'coverage_found', 'coverage_none_found', 'coverage_not_read', 'open_research_rows', 'licensed_rows')} | {'as_of': m2['record_as_of'], 'sha256': m2['sha256']}
    meta['published_utc'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'); bulk([('meta', meta)])
    print(cc, 'pages', len(pages), 'sent (changed or new)', n, 'unchanged', len(pages) - len(todo), 'no longer on the record (left in the store)', len(gone), flush=True)
bad = 0
for cc in sys.argv[1:]:
    try: publish(cc)
    except Exception as e: bad += 1; print(cc, 'FAILED', repr(e)[:300], flush=True)
sys.exit(1 if bad else 0)
