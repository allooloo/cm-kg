"""Step 2 — one roster row per JPX listed line joined to the EDINET filer by securities code (EDINET's 5-digit code = JPX 4-digit local code + a check
digit). Tabs: Prime Market, Standard Market, Growth Market, PRO Market, REITs and funds. ETFs / ETNs are counted, not carried (not issuers of the
kind this graph records). Corporate scope = Prime / Standard / Growth / PRO lines whose EDINET filer type is a domestic corporation (内国法人・組合) or
whose JPX section says foreign. Writes raw/roster.json."""
import json, re
from collections import Counter
J = json.load(open('raw/jpx_listed.json', encoding='utf-8')); E = json.load(open('raw/edinet_codes.json', encoding='utf-8'))
by_code = {}
for r in E['rows']:
    sc = (r.get('sec_code') or '').strip()
    if sc and len(sc) == 5: by_code.setdefault(sc[:4], r)
TAB = {'Prime Market (Domestic)': 'Prime Market', 'Prime Market(Foreign)': 'Prime Market', 'Standard Market(Domestic)': 'Standard Market', 'Standard Market(Foreign)': 'Standard Market', 'Growth Market(Domestic)': 'Growth Market', 'Growth Market (Foreign)': 'Growth Market', 'PRO Market': 'PRO Market', 'REIT, Venture Funds, Country Funds and Infrastructure Funds': 'REITs and funds', 'Equity Contribution Securities': 'Standard Market'}
rows = []; skipped = Counter()
for x in J['rows']:
    sec = str(x.get('Section/Products') or '').strip(); code = str(x.get('Local Code') or '').strip()
    if sec not in TAB: skipped[sec] += 1; continue
    e = by_code.get(code, {}); foreign = 'Foreign' in sec
    if TAB[sec] == 'REITs and funds': st = 'REIT / listed fund'
    elif sec == 'Equity Contribution Securities': st = 'Equity contribution securities (cooperative bank)'
    elif foreign: st = 'Corporate (foreign issuer)'
    elif e and e.get('filer_type') and e['filer_type'] != '内国法人・組合': st = f"Non-corporate filer type ({e['filer_type']})"
    else: st = 'Corporate'
    rows.append(dict(exchange=TAB[sec], section=sec, symbol=code, name=str(x.get('Name (English)') or '').strip(), name_ja=e.get('name_ja') or '', name_en_edinet=e.get('name_en') or '', name_kana=e.get('name_kana') or '', security_type=st, foreign=foreign,
                     sector33_code=str(x.get('33 Sector(Code)') or ''), sector33=str(x.get('33 Sector(name)') or ''), sector17_code=str(x.get('17 Sector(Code)') or ''), sector17=str(x.get('17 Sector(name)') or ''), size_code=str(x.get('Size Code (New Index Series)') or ''), size=str(x.get('Size (New Index Series)') or ''),
                     effective_date=str(x.get('Effective Date') or ''), edinet_code=e.get('edinet_code') or '', corporate_number=e.get('corporate_number') or '', address_ja=e.get('address_ja') or '', industry_ja=e.get('industry_ja') or '', fye=e.get('fye') or '', capital_jpy_m=e.get('capital_jpy_m') or '', consolidated=e.get('consolidated') or '', filer_type=e.get('filer_type') or '', edinet_listed=e.get('listed') or '',
                     roster_src=J['src'], edinet_src=E['src'], edinet_stamp=E.get('stamp', ''), status='Listed (JPX list, effective ' + str(x.get('Effective Date') or '') + ')'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['exchange'] for r in rows), Counter(r['security_type'] for r in rows).most_common(6)); print('skipped', dict(skipped)); print('with EDINET filer', sum(1 for r in rows if r['edinet_code']), 'with corporate number', sum(1 for r in rows if r['corporate_number']), 'with sector33', sum(1 for r in rows if r['sector33'] and r['sector33'] != '-'))
