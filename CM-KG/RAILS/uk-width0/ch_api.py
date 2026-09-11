"""Step 8b — Companies House REST API pass (runs only when C:\\ALLOOLOO\\AGENT KEYS\\companieshouse.txt exists; the key is read in-process and never printed).
  GET https://api.company-information.service.gov.uk/search/companies?q=<name>         (name search; accepted only on an exact normalised name match, public company)
  GET https://api.company-information.service.gov.uk/company/<number>                  (profile: registered office, status, type, jurisdiction, SIC codes, accounts)
  GET https://api.company-information.service.gov.uk/company/<number>/filing-history?category=accounts&items_per_page=1  (latest accounts filing link)
Rate limit 600 requests per five minutes. Writes raw/ch_api.jsonl keyed by exchange|symbol; assemble.py prefers these fields when present.
Rows covered: every roster row without a Companies House number from ch_match.py, plus a profile refresh for rows matched through the LEI or name route."""
import os, sys, json, re, time, requests
KEYFILE = r'C:\ALLOOLOO\AGENT KEYS\companieshouse.txt'
if not os.path.exists(KEYFILE): sys.exit('no Companies House key file — web pages and bulk file only (see README)')
KEY = open(KEYFILE, encoding='utf-8').read().strip()
AUTH = (KEY, '')
API = 'https://api.company-information.service.gov.uk'
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def load(fn, k):
    d = {}
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try:
                x = json.loads(line); d[x[k]] = x
            except Exception: pass
    return d
CH = load('raw/ch_match.jsonl', 'key'); done = load('raw/ch_api.jsonl', 'key')
def name_key(s):
    s = s.upper().replace('&', ' AND ').replace('.', '').replace(',', '')
    s = re.sub(r'\bP L C\b', 'PLC', s); s = re.sub(r'\bPUBLIC LIMITED COMPANY\b', 'PLC', s); s = re.sub(r'\bLIMITED\b', 'LTD', s)
    return ' '.join(re.sub(r"[^A-Z0-9 ]", ' ', s).split())
calls = [0]; window = [time.time()]
def get(path, **params):
    if calls[0] >= 550:
        wait = 300 - (time.time() - window[0])
        if wait > 0: time.sleep(wait)
        calls[0] = 0; window[0] = time.time()
    for attempt in range(5):
        try:
            r = requests.get(API + path, params=params, auth=AUTH, timeout=60); calls[0] += 1
            if r.status_code == 429: time.sleep(30); continue
            if r.status_code == 404: return None
            r.raise_for_status(); return r.json()
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None
out = open('raw/ch_api.jsonl', 'a', encoding='utf-8'); n_new = n_prof = 0
for r in rows:
    k = r['exchange'] + '|' + r['symbol']
    if k in done: continue
    prior = CH.get(k) or {}; num = prior.get('number', ''); res = {'key': k, 'api': True}
    if not num:
        s = get('/search/companies', q=r['name'], items_per_page=10) or {}
        cands = [it for it in s.get('items', []) if name_key(it.get('title', '')) == name_key(r['name']) and it.get('company_type') in ('plc', 'private-limited-guarant-nsc', 'ltd', 'oversea-company', 'old-public-company', 'scottish-partnership', 'other')]
        exact_plc = [it for it in cands if it.get('company_type') in ('plc', 'old-public-company', 'oversea-company')]
        pick = exact_plc if exact_plc else cands
        if len(pick) == 1:
            num = pick[0]['company_number']; res.update(number=num, route='api-search name-exact', route_src=f'{API}/search/companies?q=' + requests.utils.quote(r['name']))
            n_new += 1
        elif len(pick) > 1: res.update(number='', route='ambiguous', gap='API name search: %d exact-name companies (%s)' % (len(pick), ', '.join(p['company_number'] for p in pick[:4])))
        else: res.update(number='', route='none', gap='API name search: no company whose name equals the roster name')
    else: res.update(number=num, route=prior.get('route'), route_src=prior.get('route_src'))
    if num:
        p = get(f'/company/{num}')
        if p:
            ro = p.get('registered_office_address') or {}
            res['profile'] = {'name': p.get('company_name'), 'status': p.get('company_status'), 'type': p.get('type'), 'jurisdiction': p.get('jurisdiction'), 'incorporated': p.get('date_of_creation'),
                              'office': ', '.join(v for v in [ro.get('care_of'), ro.get('address_line_1'), ro.get('address_line_2'), ro.get('locality'), ro.get('region'), ro.get('country'), ro.get('postal_code')] if v),
                              'sic': p.get('sic_codes') or [], 'accounts': (p.get('accounts') or {}).get('last_accounts') or {}, 'previous_names': [x.get('name') for x in p.get('previous_company_names') or []]}
            res['profile_src'] = f'https://find-and-update.company-information.service.gov.uk/company/{num}'; res['profile_rb'] = 'Companies House REST API (company profile)'; n_prof += 1
            fh = get(f'/company/{num}/filing-history', category='accounts', items_per_page=1) or {}
            it = (fh.get('items') or [None])[0]
            if it:
                res['accounts_filing'] = {'date': it.get('date'), 'description': it.get('description'), 'type': it.get('type'), 'transaction_id': it.get('transaction_id'),
                                          'url': f"https://find-and-update.company-information.service.gov.uk/company/{num}/filing-history/{it.get('transaction_id')}/document?format=pdf&download=0" if it.get('transaction_id') else ''}
        else: res['profile_error'] = 'API profile 404'
    out.write(json.dumps(res, ensure_ascii=False) + '\n'); out.flush()
print('DONE new numbers', n_new, 'profiles', n_prof, 'calls', calls[0], flush=True)
