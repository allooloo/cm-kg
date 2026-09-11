"""Step 8 — Companies House number and profile per issuer.
Route 1 (sourced link): the GLEIF LEI record's registeredAs when registeredAt is RA000585 (Companies House) → the number; profile fields from
  the Companies House bulk index (raw/ch_plc.jsonl) or, when the number is not in the PLC index, the public profile page
  https://find-and-update.company-information.service.gov.uk/company/<number> (answers machines; no key file exists, so the API is not used).
Route 2 (name-exact): issuer name equals a Companies House current or previous company name after case / space / punctuation normalisation
  and the company is a public company; ambiguity (two numbers) → Gaps.
Writes raw/ch_match.jsonl keyed by exchange|symbol."""
import json, os, re, time, requests
from collections import defaultdict
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def load(fn, k):
    d = {}
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try:
                x = json.loads(line); d[x[k]] = x
            except Exception: pass
    return d
LEIREC = load('raw/lei_records.jsonl', 'key'); ISIN_LEI = json.load(open('raw/isin_lei_hits.json')) if os.path.exists('raw/isin_lei_hits.json') else {}
MATCH = load('raw/lei_match.jsonl', 'name')
CH = load('raw/ch_plc.jsonl', 'number')
def name_key(s):
    s = s.upper().replace('&', ' AND ').replace('.', '').replace(',', '')
    s = re.sub(r'\bP L C\b', 'PLC', s); s = re.sub(r'\bPUBLIC LIMITED COMPANY\b', 'PLC', s); s = re.sub(r'\bLIMITED\b', 'LTD', s)
    return ' '.join(re.sub(r"[^A-Z0-9 ]", ' ', s).split())
byname = defaultdict(set)
for num, c in CH.items():
    byname[name_key(c['name'])].add(num)
    for p in c.get('previous_names', []): byname[name_key(p['name'])].add(num)
LEGAL_FORM = re.compile(r'\b(?:PLC|P L C|PUBLIC LTD COMPANY|LTD|LIMITED|INC|INCORPORATED|CORP|CORPORATION|SA|S A|NV|N V|AG|SE|LP|L P|CO|COMPANY|HOLDINGS?)\b')
def entity_key(s): return ' '.join(LEGAL_FORM.sub(' ', name_key(s)).split())
def lei_for(r):
    """LEI whose GLEIF legal name is the roster issuer (legal-form words ignored). A mapping-file LEI held by a different entity
    (registrar, subsidiary, parent) is NOT used as a route to Companies House — it is reported as a conflict by assemble.py."""
    if r['isin'] and r['isin'] in ISIN_LEI:
        lei = ISIN_LEI[r['isin']].split('|')[0]; rec = LEIREC.get(lei)
        if rec and entity_key(rec['name']) == entity_key(r['name']): return lei
        if rec: return ''  # name disagrees: no route
    m = MATCH.get(r['name'])
    if m and m.get('matches'): return m['matches'][0][0]
    return ''
PAGE_CACHE = 'raw/ch_pages.jsonl'; pages = load(PAGE_CACHE, 'number'); pf = open(PAGE_CACHE, 'a', encoding='utf-8')
def fetch_page(num):
    if num in pages: return pages[num]
    url = f'https://find-and-update.company-information.service.gov.uk/company/{num}'
    rec = {'number': num, 'url': url}
    for attempt in range(4):
        try:
            x = requests.get(url, headers=UA, timeout=60)
            rec['status'] = x.status_code
            if x.status_code == 200:
                h = x.text
                def dd(label):
                    m = re.search(r'<dt[^>]*>\s*' + label + r'\s*</dt>\s*<dd[^>]*>(.*?)</dd>', h, re.S | re.I)
                    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', m.group(1))).strip() if m else ''
                rec['name'] = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', (re.search(r'<p class="heading-xlarge"[^>]*>(.*?)</p>', h, re.S) or re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S) or [None, ''])[1] if re.search(r'<p class="heading-xlarge"[^>]*>(.*?)</p>', h, re.S) or re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S) else '')).strip()
                rec['office'] = dd('Registered office address'); rec['status_text'] = dd('Company status'); rec['type'] = dd('Company type'); rec['incorporated'] = dd('Incorporated on')
                sic = re.search(r'Nature of business \(SIC\)(.*?)</ul>', h, re.S)
                rec['sic'] = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', li)).strip() for li in re.findall(r'<li[^>]*>(.*?)</li>', sic.group(1), re.S)] if sic else []
            break
        except Exception as e:
            rec['error'] = repr(e)[:120]; time.sleep(3)
    pages[num] = rec; pf.write(json.dumps(rec, ensure_ascii=False) + '\n'); pf.flush(); time.sleep(0.6)
    return rec
out = open('raw/ch_match.jsonl', 'w', encoding='utf-8'); n_lei = n_name = n_page = n_none = 0
for r in rows:
    k = r['exchange'] + '|' + r['symbol']; res = {'key': k}
    lei = lei_for(r); rec = LEIREC.get(lei) if lei else None
    num = ''
    if rec and rec.get('registeredAt') == 'RA000585' and rec.get('registeredAs'):
        num = rec['registeredAs'].strip().upper().zfill(8) if rec['registeredAs'].strip().isdigit() else rec['registeredAs'].strip().upper()
        res.update(number=num, route='lei', route_src=rec['src'])
    if not num:
        cands = byname.get(name_key(r['name']), set())
        if len(cands) == 1:
            num = next(iter(cands)); res.update(number=num, route='name-exact', route_src='https://download.companieshouse.gov.uk/en_output.html (BasicCompanyDataAsOneFile; name equals a current or previous company name)')
        elif len(cands) > 1: res.update(number='', route='ambiguous', gap='name matches %d Companies House public companies: %s' % (len(cands), ', '.join(sorted(cands)[:4])))
        elif rec and rec.get('registeredAt') and rec.get('registeredAt') != 'RA000585': res.update(number='', route='none', gap=f"LEI record registered at {rec['registeredAt']} ({rec.get('registeredAs') or ''}), not Companies House; no name-exact public company")
        else: res.update(number='', route='none', gap='no LEI registeredAs and no name-exact Companies House public company')
    if num:
        c = CH.get(num)
        if c:
            res.update(profile=c, profile_src=f'https://find-and-update.company-information.service.gov.uk/company/{num}', profile_rb='Companies House bulk data product (BasicCompanyDataAsOneFile, monthly)')
        else:
            p = fetch_page(num); n_page += 1
            res.update(page=p, profile_src=p['url'], profile_rb='Companies House public profile page (find-and-update.company-information.service.gov.uk)')
        if res['route'] == 'lei': n_lei += 1
        else: n_name += 1
    else: n_none += 1
    out.write(json.dumps(res, ensure_ascii=False) + '\n')
print('DONE lei-route', n_lei, 'name-exact', n_name, 'pages fetched', n_page, 'none', n_none, flush=True)
