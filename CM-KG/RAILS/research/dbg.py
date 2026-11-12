import json, urllib.request, urllib.error, write as W
K = open(r'C:\ALLOOLOO\AGENT KEYS\claude.txt', encoding='utf-8').read().strip().splitlines()[0]
o = W.join('us')[100]; g = W.digest(o)
for extra in ({}, {'thinking': {'type': 'disabled'}}):
    body = {'model': W.MODEL, 'max_tokens': 1100, **extra, 'system': [{'type': 'text', 'text': W.SYSTEM, 'cache_control': {'type': 'ephemeral'}}], 'messages': [{'role': 'user', 'content': 'The numbers:\n' + json.dumps(g, ensure_ascii=False)}]}
    try: r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.anthropic.com/v1/messages', data=json.dumps(body).encode(), headers={'x-api-key': K, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}), timeout=60).read()); print(extra, [b['type'] for b in r['content']], r['usage']['input_tokens'], r['usage']['output_tokens'], r['usage'].get('output_tokens_details')); print(r['content'][-1].get('text', '')[:1800])
    except urllib.error.HTTPError as e: print(extra, e.code, e.read()[:300])
