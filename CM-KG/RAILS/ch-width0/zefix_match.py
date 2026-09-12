"""Step 3 — Zefix (federal commercial register index) per issuer through the public web API the zefix.ch search uses (POST ZefixREST/api/v1/firm/search.json,
no account; the official ZefixPublicREST needs one — HITL note). A candidate becomes the issuer's register entry only when its name equals the roster name
after normalisation (AG / SA / Ltd / Inc / Holding spelling and punctuation) AND its legal form is a corporation (legalFormId 3); looser matches stay in Gaps.
Kept: UID (CHE-…), CH-ID, legal seat, register office, legal form, status, last SHAB date, the cantonal excerpt URL. Writes raw/zefix.jsonl."""
import requests, json, re, os, time, threading
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Content-Type': 'application/json', 'Origin': 'https://www.zefix.ch', 'Referer': 'https://www.zefix.ch/en/search/entity/welcome'}
LF = {x['id']: x['name']['en'] for x in json.load(open('raw/zefix_legalform.json', encoding='utf-8'))}
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '').replace('-', ' ')
    s = re.sub(r'\b(AG|SA|LTD|LIMITED|INC|PLC|N|I|N\.V|NV|HOLDING|HOLDINGS|GROUP|GROUPE|GRUPPE|SOCIETE ANONYME|AKTIENGESELLSCHAFT|CORP|CORPORATION|CO)\b', ' ', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
def search(q):
    for i in range(4):
        try:
            r = requests.post('https://www.zefix.ch/ZefixREST/api/v1/firm/search.json', json={'name': q, 'languageKey': 'en', 'maxEntries': 30, 'offset': 0}, headers=UA, timeout=60)
            if r.status_code in (429, 502, 503): time.sleep(5 * (i + 1)); continue
            if r.status_code != 200: return None, r.status_code
            return r.json().get('list', []), 200
        except Exception: time.sleep(3 * (i + 1))
    return None, 'exhausted'
lock = threading.Lock()
def match(r):
    q = re.sub(r'\s+[IN]$', '', r['name']).strip()  # SIX short names end with I (Inhaber/bearer) or N (Namen/registered)
    q = re.sub(r'\b(REG|BR|PC|PS)\b$', '', q).strip()
    cands, st = search(q[:60])
    if cands is None: return {'error': str(st)}
    nk = name_key(q); exact = [c for c in cands if name_key(c.get('name')) == nk and c.get('legalFormId') == 3]
    near = [c for c in cands if c.get('legalFormId') == 3 and (name_key(c.get('name')).startswith(nk) or nk.startswith(name_key(c.get('name'))))] if not exact else []
    pick = exact[0] if len(exact) == 1 else (exact[0] if exact and all(c['uid'] == exact[0]['uid'] for c in exact) else None)
    out = {'query': q, 'n_cands': len(cands), 'exact': [(c['name'], c['uidFormatted'], c['legalSeat'], c['status']) for c in exact][:5], 'near': [(c['name'], c['uidFormatted'], c['legalSeat']) for c in near][:5]}
    if pick:
        out.update({'uid': pick.get('uidFormatted'), 'uid_raw': pick.get('uid'), 'chid': pick.get('chidFormatted'), 'name': pick.get('name'), 'legal_seat': pick.get('legalSeat'), 'register_office_id': pick.get('registerOfficeId'), 'legal_form': LF.get(pick.get('legalFormId'), str(pick.get('legalFormId'))), 'status': pick.get('status'), 'shab_date': pick.get('shabDate'), 'excerpt_url': pick.get('cantonalExcerptWeb'), 'src': 'https://www.zefix.ch/en/search/entity/list?name=' + requests.utils.quote(q)})
    return out
if __name__ == '__main__':
    fn_out = 'raw/zefix.jsonl'; done = set()
    if os.path.exists(fn_out):
        for line in open(fn_out, encoding='utf-8'):
            try: done.add(json.loads(line)['key'])
            except Exception: pass
    todo = [r for r in rows if r['security_type'] in ('Corporate', 'Participation certificate') and r['exchange'] + '|' + r['symbol'] not in done and r['isin'].startswith('CH')]
    print('todo', len(todo), 'done', len(done), flush=True)
    out = open(fn_out, 'a', encoding='utf-8'); n = [0]
    def work(r):
        try: res = match(r)
        except Exception as e: res = {'error': repr(e)[:160]}
        res['key'] = r['exchange'] + '|' + r['symbol']
        with lock:
            out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush(); n[0] += 1
            if n[0] % 50 == 0: print(n[0], '/', len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=3) as ex: list(ex.map(work, todo))
    print('DONE', flush=True)
