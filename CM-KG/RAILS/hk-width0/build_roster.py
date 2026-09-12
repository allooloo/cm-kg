"""Step 2 — one roster row per HKEX equity line (Category = Equity): Main Board, GEM, investment companies, trading-only securities, depositary
receipts; REITs carried on their own tab. Derivative warrants, CBBCs, ETPs and debt are counted, not carried. Security type from the sub-category;
the ISIN prefix says where the issuer is incorporated (HK, KY Cayman, BMG Bermuda, CN mainland H shares …) and is carried as read.
Writes raw/roster.json."""
import json, re
from collections import Counter
H = json.load(open('raw/hkex_list.json', encoding='utf-8')); SRC = H['src']
TAB = {'Equity Securities (Main Board)': 'Main Board', 'Equity Securities (GEM)': 'GEM', 'Investment Companies': 'Main Board', 'Trading Only Securities': 'Main Board', 'Depositary Receipts': 'Main Board'}
rows = []; skipped = Counter(); seen = set()
for x in H['rows']:
    cat = str(x.get('Category') or '').strip(); sub = str(x.get('Sub-Category') or '').strip(); code = str(x.get('Stock Code') or '').strip().zfill(5)
    if cat == 'Real Estate Investment Trusts': tab, st = 'REITs', 'REIT'
    elif cat == 'Equity' and sub in TAB:
        tab = TAB[sub]
        st = {'Equity Securities (Main Board)': 'Corporate', 'Equity Securities (GEM)': 'Corporate', 'Investment Companies': 'Investment company (Chapter 21)', 'Trading Only Securities': 'Trading-only security (not listed on HKEX)', 'Depositary Receipts': 'Depositary receipt'}[sub]
    else: skipped[cat] += 1; continue
    if code in seen: continue
    seen.add(code); isin = str(x.get('ISIN') or '').strip()
    rows.append(dict(exchange=tab, symbol=code, name=str(x.get('Name of Securities') or '').strip(), security_type=st, category=cat, sub_category=sub, isin=isin, isin_prefix=isin[:2], currency=str(x.get('Trading Currency') or '').strip(), board_lot=str(x.get('Board Lot') or ''),
                     stamp_duty=str(x.get('Subject to Stamp Duty') or ''), shortsell=str(x.get('Shortsell Eligible') or ''), ccass=str(x.get('Admitted to CCASS') or ''), rmb_counter=str(x.get('RMB Counter') or ''), roster_src=SRC, list_stamp=H.get('stamp', ''), status='Listed (HKEX List of Securities, ' + H.get('stamp', '') + ')'))
json.dump(rows, open('raw/roster.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
print('rows', len(rows), Counter(r['exchange'] for r in rows), Counter(r['security_type'] for r in rows).most_common(6)); print('skipped', dict(skipped)); print('ISIN prefixes', Counter(r['isin_prefix'] for r in rows).most_common(8))
