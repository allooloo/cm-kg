r"""agree.py — USR-03 test 1: the seven live doors read against ten issuers per market, and their research pages agree on every shared field.
Per market: ten issuers from the market's index on getresearch.ai (every n-th by name, so the ten span the list). Per issuer the live research page
(https://getresearch.ai/<path>.json) is compared with the seven doors, read as any agent reads them (stock JSON-RPC, no bearer):
  get_issuer         mcp.getissuer.ai resolve_issuer       name, ticker, exchange, ISIN, LEI, record as_of
  get_ticker         mcp.getticker.ai                      name, ISIN, LEI, ticker, exchange, security type, segment, status
  get_auditor        mcp.getauditor.ai                     auditor (value or not_on_record), changes (count or not_on_record)
  get_filings        mcp.getfilings.ai                     the count of filings in the page's window
  get_as_of          mcp.getasof.ai                        earliest sealed date of the market (sealed or not)
  get_orderability   mcp.getorderability.ai                the signal per client category the page states (or not determinable), the rule version
  get_target_market  mcp.gettargetmarket.ai                read; the page carries no target-market field, so no field is shared (the read is recorded)
Every door read leaves its receipt. Paced (three issuers at a time). Evidence: agree-<stamp>.json; exit 1 on any disagreement.
Usage: python -X utf8 -I agree.py [cc ...]"""
import sys, os, json, time, datetime, urllib.request, urllib.parse, concurrent.futures as cf
UA = {'content-type': 'application/json', 'accept': 'application/json', 'user-agent': 'Allooloo USR-01 agreement test'}; SITE = 'https://getresearch.ai'
def get(u):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'user-agent': UA['user-agent'], 'accept': 'application/json'}), timeout=60).read())
        except Exception as e:
            if i == 3: raise
            time.sleep(3 * (i + 1))
def call(host, name, args):
    b = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}).encode()
    for i in range(4):
        try:
            j = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://{host}/mcp', data=b, headers=UA), timeout=120).read()); r = j['result']; o = r.get('structuredContent') or json.loads(r['content'][0]['text'])
            if isinstance(o, dict) and o.get('error') == 'unavailable' and i < 3: time.sleep(5 * (i + 1)); continue
            return o
        except Exception as e:
            if i == 3: return {'error': 'test_read_failed', 'note': repr(e)[:120]}
            time.sleep(4 * (i + 1))
pv = lambda f: f.get('value') if isinstance(f, dict) and 'value' in f else None
dv = lambda f: f.get('value') if isinstance(f, dict) and 'value' in f else ('not_on_record' if isinstance(f, dict) and f.get('state') == 'not_on_record' else None)
def one(cc, row):
    ex, code = row[0], row[1]; path = f"/{cc}/{urllib.parse.quote(ex, safe='')}/{urllib.parse.quote(code, safe='')}"; pg = get(SITE + path + '.json'); n = pg['numbers']; i = n['identity']; cmr = pg['cmr']; mk = cc; diffs = []; reads = {}
    def cmp(door, field, page_v, door_v):
        if page_v != door_v: diffs.append({'door': door, 'field': field, 'page': page_v, 'door_value': door_v})
    r = call('mcp.getissuer.ai', 'resolve_issuer', {'identifier': cmr}); m = next((x for x in (r.get('matches') or []) if x.get('cmr') == cmr), None); reads['get_issuer'] = (r.get('receipt') or {}).get('id') or r.get('error')
    if not m: diffs.append({'door': 'get_issuer', 'field': 'cmr', 'page': cmr, 'door_value': r.get('error') or 'no match'})
    else:
        for k in ('name', 'ticker', 'exchange', 'isin', 'lei'): cmp('get_issuer', k, pv(i[k]), m.get(k))
        cmp('get_issuer', 'as_of', pg['as_of'], m.get('as_of'))
    t = call('mcp.getticker.ai', 'get_ticker', {'identifier': cmr, 'market': mk}); reads['get_ticker'] = (t.get('receipt') or {}).get('id') or t.get('error')
    if t.get('error'): diffs.append({'door': 'get_ticker', 'field': 'answer', 'page': cmr, 'door_value': t.get('error')})
    else:
        for k, d in (('name', t.get('issuer')), ('isin', t.get('isin')), ('lei', t.get('lei')), ('ticker', t.get('ticker')), ('exchange', (t.get('listing') or {}).get('exchange')), ('security_type', (t.get('listing') or {}).get('security_type')), ('segment', (t.get('listing') or {}).get('segment'))): cmp('get_ticker', k, dv(i[k]), dv(d))
        cmp('get_ticker', 'status', n['status']['value'], (t.get('status') or {}).get('value'))
    a = call('mcp.getauditor.ai', 'get_auditor', {'issuer': cmr, 'market': mk}); reads['get_auditor'] = (a.get('receipt') or {}).get('id') or a.get('error')
    if a.get('error'): diffs.append({'door': 'get_auditor', 'field': 'answer', 'page': cmr, 'door_value': a.get('error')})
    else:
        cmp('get_auditor', 'auditor', dv(n['auditor']['auditor']), dv(a.get('auditor'))); pc = n['auditor']['changes']; dc = a.get('changes')
        cmp('get_auditor', 'changes', len(pc) if isinstance(pc, list) else 'not_on_record', len(dc) if isinstance(dc, list) else 'not_on_record')
    w = n['disclosure']['window']; f = call('mcp.getfilings.ai', 'get_filings', {'issuer': cmr, 'from': w['from'], 'to': w['to'], 'market': mk}); reads['get_filings'] = (f.get('receipt') or {}).get('id') or f.get('error')
    cmp('get_filings', 'filings in the window', n['disclosure']['filings'], f.get('count') if not f.get('error') else f.get('error'))
    s = call('mcp.getasof.ai', 'get_as_of', {'issuer': cmr, 'as_of': pg['as_of'], 'market': mk}); reads['get_as_of'] = (s.get('receipt') or {}).get('id') or s.get('error')
    if s.get('error') == 'not_sealed': cmp('get_as_of', 'earliest sealed date', n['as_of_depth']['node_history_from'], s.get('earliest_sealed_date'))
    elif s.get('error'): diffs.append({'door': 'get_as_of', 'field': 'answer', 'page': cmr, 'door_value': s.get('error')})
    else: cmp('get_as_of', 'sealed', n['as_of_depth']['sealed'], True)
    od = n['orderability']; cats = list((od.get('outcomes') or {}).keys()) or ['retail client']; rc = []
    for c in cats:
        o = call('mcp.getorderability.ai', 'get_orderability', {'subject': cmr, 'client_category': c}); rc.append((o.get('receipt') or {}).get('id') or o.get('error'))
        cmp('get_orderability', f'signal ({c})', (od.get('outcomes') or {}).get(c, {}).get('signal'), o.get('signal') if not o.get('error') else o.get('error')); cmp('get_orderability', 'rule version', od.get('rule_version'), o.get('rule_version') if not o.get('error') else o.get('error'))
    reads['get_orderability'] = rc
    tm = call('mcp.gettargetmarket.ai', 'get_target_market', {'subject': pv(i['isin']) or cmr}); reads['get_target_market'] = tm.get('status') or tm.get('error') or 'read'
    return {'cmr': cmr, 'page': SITE + path, 'page_hash': pg['numbers_hash'], 'agree': not diffs, 'diffs': diffs, 'reads': reads}
meta = get(SITE + '/facts.json'); ccs = sys.argv[1:] or sorted(c for c, x in meta['markets'].items() if x.get('pages')); out = {'at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'markets': {}}; bad = 0; tot = 0
for cc in ccs:
    ix = get(f'{SITE}/sitemap-{cc}.xml'.replace('.xml', '.xml')) if False else None
    rows = [json.loads(l) for l in open(rf'C:\ALLOOLOO\CM-KG\RESEARCH\pages\{cc}.jsonl', encoding='utf-8')]; rows = sorted(([p['cmr'].split('/', 2)[1], p['cmr'].split('/', 2)[2]] for p in rows), key=lambda x: (x[0], x[1])); step = max(1, len(rows) // 10); pick = rows[::step][:10]
    with cf.ThreadPoolExecutor(3) as ex: res = list(ex.map(lambda r: one(cc, r), pick))
    out['markets'][cc] = res; b = sum(1 for r in res if not r['agree']); bad += b; tot += len(res); print(cc, 'issuers', len(res), 'agree', len(res) - b, 'disagree', b, [d for r in res for d in r['diffs']][:3] if b else '', flush=True)
out['issuers'] = tot; out['disagree'] = bad; out['PASS'] = bad == 0
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"agree-{out['at'].replace(':', '').replace('-', '')}.json"), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('AGREEMENT', 'PASS' if bad == 0 else 'FAIL', 'issuers', tot, 'disagreeing', bad); sys.exit(1 if bad else 0)
