"""p50 latency from Toronto, London and Singapore via the Globalping public measurement network (no key). Measures a GET of /facts.json
on each host from three probes per city and reports the median total time. Usage: python latency.py mcp.ca-cm-kg.ai mcp.capitalmarketsknowledgegraph.ai"""
import sys, time, json, requests, statistics
def measure(host):
    body = {'type': 'http', 'target': host, 'limit': 9, 'locations': [{'city': 'Toronto', 'limit': 3}, {'city': 'London', 'limit': 3}, {'city': 'Singapore', 'limit': 3}],
            'measurementOptions': {'request': {'path': '/facts.json', 'method': 'GET'}, 'protocol': 'HTTPS'}}
    r = requests.post('https://api.globalping.io/v1/measurements', json=body, timeout=60); r.raise_for_status(); mid = r.json()['id']
    for _ in range(40):
        time.sleep(3); m = requests.get(f'https://api.globalping.io/v1/measurements/{mid}', timeout=60).json()
        if m.get('status') == 'finished': break
    out = {}
    for res in m.get('results', []):
        city = res['probe']['city']; t = res['result'].get('timings', {}); st = res['result'].get('statusCode')
        if t.get('total') is not None: out.setdefault(city, []).append((t['total'], st, t.get('firstByte')))
    return {c: {'p50_ms_total': statistics.median([x[0] for x in v]), 'p50_ms_first_byte': statistics.median([x[2] for x in v if x[2] is not None] or [0]), 'status': sorted(set(x[1] for x in v)), 'n': len(v)} for c, v in out.items()}
if __name__ == '__main__':
    for h in sys.argv[1:]:
        print(h); print(json.dumps(measure(h), indent=1))
