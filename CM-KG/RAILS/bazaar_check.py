"""One-off x402 Bazaar listing check (no polling): scans the public CDP discovery list for the estate's two paid resources and asks CDP validate for their index
state. Writes AZURE\\bazaar-check-<UTC stamp>.txt/json."""
import json, urllib.request, datetime, sys, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8')
H = {'user-agent': 'Allooloo Technologies Corp. developers@allooloo.ai', 'accept': 'application/json', 'content-type': 'application/json'}
def get(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60).read())
OURS = ['https://agentic-x402.ai/api', 'https://agentic-trades.ai/x402/record/uk-cm-kg/LSE/BARC']
stamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%MZ'); out = {'checked_utc': stamp, 'validate': {}, 'listed': {}}
for r in OURS:
    try:
        rq = urllib.request.Request('https://api.cdp.coinbase.com/platform/v2/x402/validate', data=json.dumps({'resource': r, 'method': 'GET'}).encode(), method='POST', headers=H)
        out['validate'][r] = json.loads(urllib.request.urlopen(rq, timeout=60).read()).get('index')
    except Exception as e: out['validate'][r] = {'error': str(e)[:80]}
tot = get('https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources?limit=1')['pagination']['total']
def page(off):
    try: return get(f'https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources?limit=100&offset={off}').get('items', [])
    except Exception: return []
with cf.ThreadPoolExecutor(4) as ex:
    for items in ex.map(page, range(0, tot + 100, 100)):
        for it in items:
            if 'agentic-x402' in it['resource'] or 'agentic-trades' in it['resource']: out['listed'][it['resource']] = it.get('lastUpdated')
lines = [f"bazaar total {tot} · listed: {json.dumps(out['listed'])} · validate index: {json.dumps(out['validate'])}"]
base = rf'C:\ALLOOLOO\AZURE\bazaar-check-{stamp}'
json.dump(out, open(base + '.json', 'w'), indent=1); open(base + '.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
