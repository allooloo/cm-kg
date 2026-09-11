"""Pass 2.3 — ChatGPT (Responses API via the Batch API, model gpt-4.1-mini, strict JSON schema) reads every financial_statement
release whose body was fetched and extracts: period_end, statement_date, auditor_named, going_concern (yes/no), plus the
release's own dateline date. One batch. Label: 'read by ChatGPT (batch)'.
  python chatgpt_batch.py submit   -> raw/openai_batch.json (batch id)
  python chatgpt_batch.py collect  -> raw/chatgpt_extract.jsonl"""
import hashlib
from fc_common import *
MODEL = 'gpt-4.1-mini'
SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['period_end', 'statement_date', 'auditor_named', 'going_concern', 'evidence'],
          'properties': {'period_end': {'type': 'string', 'description': 'fiscal period end the results cover, YYYY-MM-DD, or empty'},
                         'statement_date': {'type': 'string', 'description': 'date the financial statements were approved/filed/dated as stated in the release, YYYY-MM-DD, or empty'},
                         'auditor_named': {'type': 'string', 'description': 'audit firm named in the release, or empty'},
                         'going_concern': {'type': 'string', 'enum': ['yes', 'no'], 'description': 'yes only if the release itself contains going-concern language'},
                         'evidence': {'type': 'string', 'description': 'the sentence(s) the answers rest on, verbatim, max 400 chars'}}}
SYS = ('You extract facts from a single press release. Answer only from the text. Empty string when the text does not state it. '
       'Never infer a date from the headline; period_end must be stated in the body. Return strict JSON matching the schema.')
def body_of(url):
    fn = 'raw/bodies/' + hashlib.sha1(url.encode()).hexdigest() + '.txt'
    return open(fn, encoding='utf-8').read() if os.path.exists(fn) else ''
def submit():
    lines = []; seen = set()
    for e in events():
        if e['event_type'] != 'financial_statement' or e['url'] in seen: continue
        b = body_of(e['url'])
        if len(b) < 400: continue
        seen.add(e['url'])
        cid = hashlib.sha1(e['url'].encode()).hexdigest()[:24]
        lines.append(json.dumps({'custom_id': cid, 'method': 'POST', 'url': '/v1/responses', 'body': {'model': MODEL, 'input': [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': f"Issuer: {e['issuer']} ({e['exchange']}: {e['ticker']}). Release title: {e['title']}\n\nRELEASE TEXT:\n{b[:14000]}"}],
                                 'text': {'format': {'type': 'json_schema', 'name': 'fin_extract', 'strict': True, 'schema': SCHEMA}}, 'max_output_tokens': 400}}))
    open('raw/openai_batch_input.jsonl', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('batch requests', len(lines), flush=True)
    H = {'Authorization': 'Bearer ' + E['OPENAI_API_KEY']}
    f = requests.post('https://api.openai.com/v1/files', headers=H, files={'file': ('batch.jsonl', open('raw/openai_batch_input.jsonl', 'rb'))}, data={'purpose': 'batch'}, timeout=300).json()
    print('file', f.get('id'), f.get('error'))
    b = requests.post('https://api.openai.com/v1/batches', headers=H, json={'input_file_id': f['id'], 'endpoint': '/v1/responses', 'completion_window': '24h'}, timeout=120).json()
    print('batch', b.get('id'), b.get('status'), b.get('error'))
    json.dump({'batch': b, 'file': f, 'n': len(lines)}, open('raw/openai_batch.json', 'w'))
def collect():
    H = {'Authorization': 'Bearer ' + E['OPENAI_API_KEY']}
    meta = json.load(open('raw/openai_batch.json')); bid = meta['batch']['id']
    b = requests.get(f'https://api.openai.com/v1/batches/{bid}', headers=H, timeout=120).json()
    print('status', b.get('status'), b.get('request_counts'))
    if b.get('status') != 'completed': return False
    out = requests.get(f"https://api.openai.com/v1/files/{b['output_file_id']}/content", headers=H, timeout=600).text
    url_by_cid = {hashlib.sha1(e['url'].encode()).hexdigest()[:24]: e['url'] for e in events() if e['event_type'] == 'financial_statement'}
    n = 0; usage = {'input': 0, 'output': 0}
    with open('raw/chatgpt_extract.jsonl', 'w', encoding='utf-8') as f:
        for line in out.splitlines():
            if not line.strip(): continue
            d = json.loads(line); body = (d.get('response') or {}).get('body') or {}
            txt = ''
            for o in body.get('output', []):
                for c in o.get('content', []) if isinstance(o.get('content'), list) else []:
                    if c.get('type') == 'output_text': txt += c.get('text', '')
            u = body.get('usage') or {}; usage['input'] += u.get('input_tokens', 0); usage['output'] += u.get('output_tokens', 0)
            j = jparse(txt) or {}
            f.write(json.dumps({'url': url_by_cid.get(d['custom_id'], ''), 'custom_id': d['custom_id'], **j, 'error': (d.get('error') or (body.get('error') if isinstance(body, dict) else None))}, ensure_ascii=False) + '\n'); n += 1
    print('collected', n, 'usage', usage); json.dump({'usage': usage, 'n': n, 'model': MODEL}, open('raw/openai_batch_usage.json', 'w'))
    return True
if __name__ == '__main__':
    if sys.argv[1] == 'submit': submit()
    else: collect()
