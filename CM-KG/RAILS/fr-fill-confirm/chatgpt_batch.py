"""Pass 2.3 — ChatGPT (Responses API via the Batch API, model gpt-4.1-mini, strict JSON schema). One batch over text windows cut from the issuer-site PDFs
(the PDFs carry a text layer, so no page images): for each annual report — auditor (signature block of the independent auditor's report), share
registry, period end, going-concern language; for each results announcements — period end and statement date. Label 'read by ChatGPT (batch)'.
  python chatgpt_batch.py submit | collect  -> raw/chatgpt_reports.jsonl"""
from fc_common import *
MODEL = 'gpt-4.1-mini'
H = {'Authorization': 'Bearer ' + E['OPENAI_API_KEY']}
SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['auditor', 'registry', 'period_end', 'statement_date', 'going_concern', 'evidence'],
          'properties': {'auditor': {'type': 'string', 'description': "audit firm that signed the independent auditor's report, proper name, or empty"},
                         'registry': {'type': 'string', 'description': 'share register / registrar service provider named (e.g. Computershare Schweiz, areg.ch, ShareCommService, Devigus, Nimbus), or empty'},
                         'period_end': {'type': 'string', 'description': 'financial period end the document covers, YYYY-MM-DD, or empty'},
                         'statement_date': {'type': 'string', 'description': 'date the directors signed / the report is dated, YYYY-MM-DD, or empty'},
                         'going_concern': {'type': 'string', 'enum': ['material_uncertainty', 'none_stated', 'not_readable'], 'description': 'material_uncertainty only if the text states a material uncertainty related to going concern'},
                         'evidence': {'type': 'string', 'description': 'the sentence(s) the auditor / registry answers rest on, verbatim, max 400 chars'}}}
SYS = ('You extract facts from excerpts of one issuer-published document (annual report, in English, German, French or Italian). Answer only from the text. Empty string when the excerpts do not state it. '
       'The auditor is the firm named in the independent auditor\'s report signature block, not a firm mentioned elsewhere. Return strict JSON matching the schema.')
def submit():
    lines = []
    for f in os.listdir('raw/reports'):
        d = json.load(open('raw/reports/' + f, encoding='utf-8'))
        if d.get('error') or d.get('no_text_layer'): continue
        parts = ['### AUDITOR REPORT PAGES\n' + '\n---\n'.join(d.get('auditor_windows', [])[:4]), '### REGISTRY\n' + '\n---\n'.join(d.get('registry_windows', [])[:3]), '### GOING CONCERN\n' + '\n---\n'.join(d.get('going_concern_windows', [])[:3]), '### PERIOD\n' + '\n---\n'.join(d.get('period_windows', [])[:2]), '### FRONT\n' + (d.get('front_text') or '')]
        text = '\n\n'.join(parts)[:40000]
        if len(text) < 400: continue
        lines.append(json.dumps({'custom_id': d['idsId'], 'method': 'POST', 'url': '/v1/responses', 'body': {'model': MODEL, 'input': [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': f"Issuer: {d.get('key')}. Document: {d.get('kind')} {d.get('headline')} ({d.get('date')}).\n\n{text}"}],
                                 'text': {'format': {'type': 'json_schema', 'name': 'issuer_doc_extract', 'strict': True, 'schema': SCHEMA}}, 'max_output_tokens': 400}}))
    open('raw/openai_reports_input.jsonl', 'w', encoding='utf-8').write('\n'.join(lines) + '\n'); print('batch requests', len(lines), flush=True)
    batches = []
    for i in range(0, len(lines), 5000):
        chunk = '\n'.join(lines[i:i + 5000]) + '\n'
        f = requests.post('https://api.openai.com/v1/files', headers=H, files={'file': (f'reports_batch_{i}.jsonl', chunk.encode('utf-8'))}, data={'purpose': 'batch'}, timeout=600).json()
        b = requests.post('https://api.openai.com/v1/batches', headers=H, json={'input_file_id': f['id'], 'endpoint': '/v1/responses', 'completion_window': '24h'}, timeout=120).json()
        print('batch', b.get('id'), b.get('status'), b.get('error')); batches.append({'batch': b, 'file': f})
    json.dump({'batches': batches, 'n': len(lines), 'kind': 'reports'}, open('raw/openai_batch_reports.json', 'w'))
def collect():
    if not os.path.exists('raw/openai_batch_reports.json'): print('no batch'); return True
    meta = json.load(open('raw/openai_batch_reports.json')); rows = []; usage = {'input': 0, 'output': 0}; alldone = True; counts = []
    for bb in meta['batches']:
        bid = bb['batch'].get('id')
        if not bid: continue
        b = requests.get(f'https://api.openai.com/v1/batches/{bid}', headers=H, timeout=120).json(); counts.append((bid, b.get('status'), b.get('request_counts')))
        if b.get('status') != 'completed': alldone = False; continue
        out = requests.get(f"https://api.openai.com/v1/files/{b['output_file_id']}/content", headers=H, timeout=900).text
        for line in out.splitlines():
            if not line.strip(): continue
            d = json.loads(line); body = (d.get('response') or {}).get('body') or {}; txt = ''
            for o in body.get('output', []):
                for c in o.get('content', []) if isinstance(o.get('content'), list) else []:
                    if c.get('type') == 'output_text': txt += c.get('text', '')
            u = body.get('usage') or {}; usage['input'] += u.get('input_tokens', 0); usage['output'] += u.get('output_tokens', 0)
            rows.append({'custom_id': d['custom_id'], **(jparse(txt) or {}), 'error': (d.get('error') or (body.get('error') if isinstance(body, dict) else None))})
    print(counts)
    if not alldone: return False
    docs = {f[:-5]: json.load(open('raw/reports/' + f, encoding='utf-8')) for f in os.listdir('raw/reports')}
    with open('raw/chatgpt_reports.jsonl', 'w', encoding='utf-8') as f:
        for r in rows:
            d = docs.get(r['custom_id'], {}); f.write(json.dumps({**r, 'key': d.get('key'), 'kind': d.get('kind'), 'document_url': d.get('pdf_url') or d.get('viewer'), 'date': d.get('date')}, ensure_ascii=False) + '\n')
    json.dump({'usage': usage, 'n': len(rows), 'model': MODEL}, open('raw/chatgpt_reports_usage.json', 'w')); print('collected', len(rows), usage); return True
if __name__ == '__main__':
    if sys.argv[1] == 'submit': submit()
    else: print('ALL COLLECTED' if collect() else 'PENDING')
