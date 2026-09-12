"""RADAR widgets 04/05 — agent calls per day from Cloudflare Workers analytics (GraphQL, the account token; read on the build machine, never in a Worker).
Writes CM-KG\ESTATE\public\calls.json: daily invocations of the apex router (cm-kg-apex) and the estate surfaces Worker (estate-pages) over the last 14 days.
Per regional door and calls-by-region need Zone Analytics Read on the token of record — not granted; stated in the file, not guessed. Run by the sweep or by hand."""
import json, datetime, os, requests
ACCT = 'dd2832b36f171b815f84c8487aada36b'
tok = open(r'C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt', encoding='utf-8').read().strip().splitlines()[0].strip()
since = (datetime.datetime.utcnow() - datetime.timedelta(days=14)).strftime('%Y-%m-%dT00:00:00Z')
q = {'query': '{ viewer { accounts(filter:{accountTag:"%s"}) { workersInvocationsAdaptive(limit:1000, filter:{datetime_geq:"%s", scriptName_in:["cm-kg-apex","estate-pages","allooloo-io","ai-ask"]}) { sum { requests errors } dimensions { scriptName date } } } } }' % (ACCT, since)}
r = requests.post('https://api.cloudflare.com/client/v4/graphql', headers={'Authorization': 'Bearer ' + tok}, json=q, timeout=90).json()
rows = (((r.get('data') or {}).get('viewer') or {}).get('accounts') or [{}])[0].get('workersInvocationsAdaptive') or []
by = {}
for x in rows:
    d = x['dimensions']['date']; s = x['dimensions']['scriptName']; by.setdefault(d, {}); by[d][s] = by[d].get(s, 0) + x['sum']['requests']
daily = [{'day': d, 'apex': v.get('cm-kg-apex', 0), 'estate': v.get('estate-pages', 0), 'allooloo_io': v.get('allooloo-io', 0), 'ask': v.get('ai-ask', 0)} for d, v in sorted(by.items())]
out = {'as_of': datetime.date.today().isoformat(), 'source': 'Cloudflare Workers analytics (workersInvocationsAdaptive, GraphQL) read by RAILS\\calls_analytics.py on the build machine', 'window_days': 14, 'daily': daily,
       'tool_mix': None, 'per_door_note': 'regional doors sit behind Cloudflare zones; per-door and per-country counts need Zone Analytics Read on the token of record (not granted) — HITL',
       'geography': {'note': 'calls by region need Zone Analytics Read on the token of record — HITL; not shown', 'source': 'Cloudflare zone analytics (not readable with the tokens on record)'}}
p = r'C:\ALLOOLOO\CM-KG\ESTATE\public\calls.json'; json.dump(out, open(p, 'w', encoding='utf-8'), indent=1); print('calls.json', len(daily), 'days', 'errors:' , (r.get('errors') or [{}])[0].get('message', '') if r.get('errors') else 'none')
