r"""LIST-02 — read only: the apex agent card and every node agent card, checked against the roster of record (apex list_nodes): does the card state the
node count (34), carry or point to the roster, and name the node's example from the roster. Prints one line per card; writes cards-<UTC stamp>.json beside."""
import json, re, os, datetime, urllib.request, concurrent.futures as cf
UA = {'User-Agent': 'Allooloo LIST-02 card check', 'content-type': 'application/json', 'accept': 'application/json'}
b = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'list_nodes', 'arguments': {}}}).encode()
nodes = json.load(urllib.request.urlopen(urllib.request.Request('https://mcp.getissuer.ai/mcp', data=b, headers=UA), timeout=60))['result']['structuredContent']['nodes']
N = len([n for n in nodes if n.get('live')])
def card(url):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
    except Exception as e: return {'_error': str(e)[:80]}
targets = [('apex', 'https://agent.getissuer.ai/.well-known/agent-card.json', None)] + [(n['node'], n.get('agent_card') or f"https://agent.{n['node']}.ai/.well-known/agent-card.json", n) for n in nodes]
def check(t):
    name, url, n = t; c = card(url); s = json.dumps(c, ensure_ascii=False)
    nums = sorted({int(x) for x in re.findall(r'\b(\d{1,3}) (?:markets|nodes|national markets|market nodes)\b', s)})
    words = re.findall(r'\b(eleven|twelve|thirteen|fourteen|twenty|thirty)[- ]?(?:\w+ )?(markets|nodes)\b', s, re.I)
    ex = (n or {}).get('example') or {}
    return {'card': name, 'url': url, 'ok': '_error' not in c, 'error': c.get('_error'), 'counts_stated': nums, 'count_words': words, 'mentions_list_nodes': 'list_nodes' in s,
            'example_isin_on_card': bool(ex.get('isin')) and ex['isin'] in s, 'example_ticker_on_card': bool(ex.get('ticker')) and str(ex.get('ticker')).split('.')[0].split(':')[-1] in s, 'example': ex.get('isin')}
with cf.ThreadPoolExecutor(12) as ex: R = list(ex.map(check, targets))
for r in R: print(f"{r['card']:10s} ok={r['ok']} counts={r['counts_stated']} words={r['count_words']} list_nodes={r['mentions_list_nodes']} example_isin={r['example_isin_on_card']} ticker={r['example_ticker_on_card']} {r['error'] or ''}")
print('roster live', N, '| cards answering', sum(1 for r in R if r['ok']), 'of', len(R))
json.dump({'roster_live': N, 'cards': R}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"cards-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%MZ')}.json"), 'w'), indent=1)
