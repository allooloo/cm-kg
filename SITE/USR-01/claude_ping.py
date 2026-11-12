import json, urllib.request, urllib.error
K = open(r'C:\ALLOOLOO\AGENT KEYS\claude.txt', encoding='utf-8').read().strip().splitlines()[0]
def post(model):
    b = json.dumps({'model': model, 'max_tokens': 20, 'messages': [{'role': 'user', 'content': 'Reply with the word ok.'}]}).encode()
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.anthropic.com/v1/messages', data=b, headers={'x-api-key': K, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}), timeout=60).read())
        return r['model'], r['content'][0]['text'], r['usage']
    except urllib.error.HTTPError as e: return model, e.code, e.read()[:200]
for m in ('claude-haiku-5-5', 'claude-haiku-4-5'): print(post(m))
try:
    r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.anthropic.com/v1/models?limit=30', headers={'x-api-key': K, 'anthropic-version': '2023-06-01'}), timeout=60).read())
    print([m['id'] for m in r['data']])
except Exception as e: print('models', e)
