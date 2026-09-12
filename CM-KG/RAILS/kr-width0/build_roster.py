"""Step 2 — one roster row per KIND listed company (Korean name, 6-digit code, market, industry, listing date, fiscal month, CEO, website, region)
joined to the DART filer by stock code (corp_code, English name) and to the DART company profile (corporate registration number, business
registration number, address, homepage, IR page, industry code, establishment date, corp class). Tabs: KOSPI, KOSDAQ, KONEX. Corporate scope =
every KIND line (KIND lists companies, not funds); SPACs are typed by name (기업인수목적). Writes raw/roster.json."""
import json, re
from collections import Counter
K = json.load(open('raw/kind_list.json', encoding='utf-8')); D = json.load(open('raw/dart_corpcode.json', encoding='utf-8'))
by_stock = {}
for r in D['rows']: by_stock.setdefault(r['stock_code'], r)
prof = {}
for line in open('raw/dart_company.jsonl', encoding='utf-8'):
    try: j = json.loads(line)
    except Exception: continue
    if j.get('corp_code'): prof[j['corp_code']] = j
MKT = {'유가증권': 'KOSPI', '코스닥': 'KOSDAQ', '코넥스': 'KONEX', 'KOSPI': 'KOSPI', 'KOSDAQ': 'KOSDAQ', 'KONEX': 'KONEX'}
rows = []; skipped = Counter()
for x in K['rows']:
    m = MKT.get((x.get('시장구분') or '').strip())
    if not m: skipped[x.get('시장구분') or 'blank'] += 1; continue
    code = (x.get('종목코드') or '').strip().zfill(6); d = by_stock.get(code, {}); p = prof.get(d.get('corp_code', ''), {}) if d else {}
    name_ko = (x.get('회사명') or '').strip(); name_en = (p.get('corp_name_eng') or d.get('corp_eng_name') or '').strip()
    st = 'SPAC (by name)' if '기업인수목적' in name_ko else 'Corporate'
    rows.append(dict(exchange=m, symbol=code, name=name_en or name_ko, name_ko=name_ko, name_en=name_en, security_type=st, industry_ko=(x.get('업종') or '').strip(), products_ko=(x.get('주요제품') or '').strip(), listing_date=(x.get('상장일') or '').strip(), fiscal_month=(x.get('결산월') or '').strip(), ceo_ko=(x.get('대표자명') or '').strip(), website=(x.get('홈페이지') or '').strip(), region_ko=(x.get('지역') or '').strip(),
                     corp_code=d.get('corp_code', ''), dart_modify_date=d.get('modify_date', ''), jurir_no=p.get('jurir_no', ''), bizr_no=p.get('bizr_no', ''), address_ko=p.get('adres', ''), hm_url=p.get('hm_url', ''), ir_url=p.get('ir_url', ''), induty_code=p.get('induty_code', ''), est_dt=p.get('est_dt', ''), acc_mt=p.get('acc_mt', ''), corp_cls=p.get('corp_cls', ''), ceo_dart=p.get('ceo_nm', ''), stock_name=p.get('stock_name', ''),
                     roster_src=K['src'], corpcode_src=D['src'], company_src=p.get('src', ''), status='Listed (KIND company list, ' + K.get('fetched', '') + ')'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['exchange'] for r in rows), Counter(r['security_type'] for r in rows)); print('skipped', dict(skipped)); print('with DART corp code', sum(1 for r in rows if r['corp_code']), 'with profile', sum(1 for r in rows if r['company_src']), 'with bizr_no', sum(1 for r in rows if r['bizr_no']), 'with English name', sum(1 for r in rows if r['name_en']))
