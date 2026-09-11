"""Pass 2.3 — ChatGPT (Responses API via the Batch API, model gpt-4.1-mini, strict JSON schema). Two batches, one label: 'read by ChatGPT (batch)'.
  A. accounts: each issuer's latest accounts filing PDF from Companies House (raw/accounts_pdf, image PDFs) uploaded to the Files API and read as
     input_file (the model reads page images): auditor name, period end, going-concern language, registrar if named, with page-level evidence.
     PDFs over 100 pages are split with pypdf into <=100-page parts; each part is one request; the parts are merged on collect (first non-empty wins,
     disagreement recorded). This is the auditor lift.
  B. results: every financial_statement announcement whose body was fetched (Investegate text): period end, statement date, auditor named, going concern.
  python chatgpt_batch.py submit_accounts | submit_results | collect   -> raw/chatgpt_accounts.jsonl, raw/chatgpt_results.jsonl"""
import hashlib, io
import pypdf
from fc_common import *
MODEL = 'gpt-4.1-mini'
H = {'Authorization': 'Bearer ' + E['OPENAI_API_KEY']}
SCHEMA_ACC = {'type': 'object', 'additionalProperties': False, 'required': ['auditor', 'period_end', 'going_concern', 'registrar', 'company_name', 'evidence', 'evidence_page'],
              'properties': {'auditor': {'type': 'string', 'description': "audit firm that signed the independent auditor's report, proper name, or empty"},
                             'period_end': {'type': 'string', 'description': 'financial year end the accounts cover, YYYY-MM-DD, or empty'},
                             'going_concern': {'type': 'string', 'enum': ['material_uncertainty', 'none_stated', 'not_readable'], 'description': "material_uncertainty only if the auditor's report or the notes state a material uncertainty related to going concern"},
                             'registrar': {'type': 'string', 'description': 'share registrar named in the report (e.g. Computershare Investor Services PLC, Equiniti, MUFG Corporate Markets, Neville Registrars, Share Registrars), or empty'},
                             'company_name': {'type': 'string', 'description': 'the company name printed on the accounts, or empty'},
                             'evidence': {'type': 'string', 'description': 'the auditor signature block or sentence the auditor answer rests on, verbatim, max 300 chars'},
                             'evidence_page': {'type': 'integer', 'description': 'page number in this document part where the auditor evidence appears, 0 if none'}}}
SCHEMA_RES = {'type': 'object', 'additionalProperties': False, 'required': ['period_end', 'statement_date', 'auditor_named', 'going_concern', 'evidence'],
              'properties': {'period_end': {'type': 'string', 'description': 'fiscal period end the results cover, YYYY-MM-DD, or empty'},
                             'statement_date': {'type': 'string', 'description': 'date the financial statements were approved/dated as stated, YYYY-MM-DD, or empty'},
                             'auditor_named': {'type': 'string', 'description': 'audit firm named in the announcement, or empty'},
                             'going_concern': {'type': 'string', 'enum': ['yes', 'no'], 'description': 'yes only if the announcement itself contains going-concern language'},
                             'evidence': {'type': 'string', 'description': 'the sentence(s) the answers rest on, verbatim, max 400 chars'}}}
SYS_ACC = ('You read one part of a company\'s statutory annual report and accounts filed at Companies House (scanned pages). Answer only from what is printed. '
           'Empty string when this part does not show it. The auditor is the firm named in the independent auditor\'s report signature block. Return strict JSON matching the schema.')
SYS_RES = ('You extract facts from a single regulatory announcement. Answer only from the text. Empty string when the text does not state it. '
           'Never infer a date from the headline; period_end must be stated in the body. Return strict JSON matching the schema.')
def body_of(url):
    fn = 'raw/bodies/' + hashlib.sha1(url.encode()).hexdigest() + '.txt'
    return open(fn, encoding='utf-8').read() if os.path.exists(fn) else ''
def upload(name, data):
    for i in range(4):
        f = requests.post('https://api.openai.com/v1/files', headers=H, files={'file': (name, data, 'application/pdf')}, data={'purpose': 'user_data'}, timeout=600)
        if f.status_code in (429, 500, 502, 503): time.sleep(10 * (i + 1)); continue
        j = f.json(); return j.get('id'), j.get('error')
    return None, 'upload exhausted'
def submit_accounts():
    acc = [json.load(open('raw/accounts_text/' + f, encoding='utf-8')) for f in os.listdir('raw/accounts_text')]
    acc = [a for a in acc if a.get('pdf') and os.path.exists(a['pdf'])]
    lines = []; parts_meta = {}; n_files = 0
    for a in acc:
        try: rd = pypdf.PdfReader(a['pdf'])
        except Exception as e: parts_meta[a['number']] = {'error': repr(e)[:100]}; continue
        n = len(rd.pages); ranges = [(s, min(s + 100, n)) for s in range(0, n, 100)]
        ids = []
        for (s, t) in ranges:
            w = pypdf.PdfWriter()
            for i in range(s, t): w.add_page(rd.pages[i])
            buf = io.BytesIO(); w.write(buf); data = buf.getvalue()
            if len(data) > 31 * 1024 * 1024: parts_meta.setdefault(a['number'], {})['skipped'] = f'part {s}-{t} over 32 MB'; continue
            fid, err = upload(f"{a['number']}_{s}_{t}.pdf", data)
            if not fid: parts_meta.setdefault(a['number'], {})['upload_error'] = str(err)[:100]; continue
            n_files += 1; cid = f"{a['number']}_{s}_{t}"; ids.append(cid)
            lines.append(json.dumps({'custom_id': cid, 'method': 'POST', 'url': '/v1/responses', 'body': {'model': MODEL, 'input': [{'role': 'system', 'content': SYS_ACC}, {'role': 'user', 'content': [{'type': 'input_text', 'text': f"Company on the register: {a.get('key', '')} — Companies House number {a['number']}. Accounts filing {a.get('filing_date')} ({a.get('description')}). Pages {s + 1}-{t} of {n}."}, {'type': 'input_file', 'file_id': fid}]}],
                                                                                                          'text': {'format': {'type': 'json_schema', 'name': 'accounts_extract', 'strict': True, 'schema': SCHEMA_ACC}}, 'max_output_tokens': 400}}))
        parts_meta[a['number']] = {**parts_meta.get(a['number'], {}), 'parts': ids, 'pages': n, 'key': a['key'], 'document_url': a['document_url'], 'filing_date': a.get('filing_date')}
        if n_files % 100 == 0: print('uploaded parts', n_files, flush=True)
    open('raw/openai_accounts_input.jsonl', 'w', encoding='utf-8').write('\n'.join(lines) + '\n'); json.dump(parts_meta, open('raw/openai_accounts_parts.json', 'w'))
    print('accounts batch requests', len(lines), 'files', n_files, flush=True)
    batches = []
    for i in range(0, len(lines), 5000):
        chunk = '\n'.join(lines[i:i + 5000]) + '\n'
        f = requests.post('https://api.openai.com/v1/files', headers=H, files={'file': (f'accounts_batch_{i}.jsonl', chunk.encode('utf-8'))}, data={'purpose': 'batch'}, timeout=600).json()
        b = requests.post('https://api.openai.com/v1/batches', headers=H, json={'input_file_id': f['id'], 'endpoint': '/v1/responses', 'completion_window': '24h'}, timeout=120).json()
        print('batch', b.get('id'), b.get('status'), b.get('error')); batches.append({'batch': b, 'file': f})
    json.dump({'batches': batches, 'n': len(lines), 'kind': 'accounts'}, open('raw/openai_batch_accounts.json', 'w'))
def submit_results():
    lines = []; seen = set()
    for e in events():
        if e['event_type'] != 'financial_statement' or e['url'] in seen: continue
        b = body_of(e['url'])
        if len(b) < 600: continue
        seen.add(e['url']); cid = hashlib.sha1(e['url'].encode()).hexdigest()[:24]
        lines.append(json.dumps({'custom_id': cid, 'method': 'POST', 'url': '/v1/responses', 'body': {'model': MODEL, 'input': [{'role': 'system', 'content': SYS_RES}, {'role': 'user', 'content': f"Issuer: {e['issuer']} ({e['exchange']}: {e['ticker']}). Announcement: {e['title']} ({e['date']})\n\nTEXT:\n{b[:16000]}"}],
                                                                                                    'text': {'format': {'type': 'json_schema', 'name': 'fin_extract', 'strict': True, 'schema': SCHEMA_RES}}, 'max_output_tokens': 400}}))
    open('raw/openai_results_input.jsonl', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('results batch requests', len(lines), flush=True)
    batches = []
    for i in range(0, len(lines), 5000):
        chunk = '\n'.join(lines[i:i + 5000]) + '\n'
        f = requests.post('https://api.openai.com/v1/files', headers=H, files={'file': (f'results_batch_{i}.jsonl', chunk.encode('utf-8'))}, data={'purpose': 'batch'}, timeout=600).json()
        b = requests.post('https://api.openai.com/v1/batches', headers=H, json={'input_file_id': f['id'], 'endpoint': '/v1/responses', 'completion_window': '24h'}, timeout=120).json()
        print('batch', b.get('id'), b.get('status'), b.get('error')); batches.append({'batch': b, 'file': f})
    json.dump({'batches': batches, 'n': len(lines), 'kind': 'results'}, open('raw/openai_batch_results.json', 'w'))
def collect_one(meta_fn, out_fn):
    if not os.path.exists(meta_fn): print(meta_fn, 'absent'); return True
    meta = json.load(open(meta_fn)); rows = []; usage = {'input': 0, 'output': 0}; alldone = True; counts = []
    for bb in meta['batches']:
        bid = bb['batch'].get('id')
        if not bid: continue
        b = requests.get(f'https://api.openai.com/v1/batches/{bid}', headers=H, timeout=120).json(); counts.append((bid, b.get('status'), b.get('request_counts')))
        if b.get('status') != 'completed': alldone = False; continue
        out = requests.get(f"https://api.openai.com/v1/files/{b['output_file_id']}/content", headers=H, timeout=900).text
        for line in out.splitlines():
            if not line.strip(): continue
            d = json.loads(line); body = (d.get('response') or {}).get('body') or {}
            txt = ''
            for o in body.get('output', []):
                for c in o.get('content', []) if isinstance(o.get('content'), list) else []:
                    if c.get('type') == 'output_text': txt += c.get('text', '')
            u = body.get('usage') or {}; usage['input'] += u.get('input_tokens', 0); usage['output'] += u.get('output_tokens', 0)
            rows.append({'custom_id': d['custom_id'], **(jparse(txt) or {}), 'error': (d.get('error') or (body.get('error') if isinstance(body, dict) else None))})
    print(meta_fn, counts)
    if not alldone: return False
    with open(out_fn, 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    json.dump({'usage': usage, 'n': len(rows), 'model': MODEL}, open(out_fn.replace('.jsonl', '_usage.json'), 'w'))
    print('collected', out_fn, len(rows), usage); return True
if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'submit_accounts': submit_accounts()
    elif cmd == 'submit_results': submit_results()
    else:
        a = collect_one('raw/openai_batch_accounts.json', 'raw/chatgpt_accounts.jsonl'); b = collect_one('raw/openai_batch_results.json', 'raw/chatgpt_results.jsonl')
        print('ALL COLLECTED' if a and b else 'PENDING')
