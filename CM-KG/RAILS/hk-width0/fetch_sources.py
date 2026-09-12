"""Step 1 — pull the Hong Kong roster into raw/ (a junction to the open pond drop POND\\hk-cm-kg\\width0\\<date>\\). Public, no key, English only by order.
  HKEX List of Securities .... ListOfSecurities.xlsx from hkex.com.hk: every listed security with stock code, English name, category (Equity, ETPs,
                               REITs, debt, warrants …), sub-category (Main Board / GEM / investment companies / depositary receipts), board lot,
                               ISIN, trading currency and eligibility flags. Equity lines carry the ISIN — the LEI route runs from it.
  GLEIF ISIN-to-LEI file ..... the daily mapping zip (mapping.gleif.org) for exact ISIN → LEI
No search layer, no wires, no lab reads on this node (ORDER-017 re-cut: Hong Kong stays Width 0, English only, no search, local-partner copy,
no door). No price or market data is carried."""
import requests, json, os, io, datetime, sys
import openpyxl
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
os.makedirs('raw', exist_ok=True); TODAY = datetime.date.today().isoformat()
HKEX = 'https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx'
def hkex():
    b = requests.get(HKEX, headers=UA, timeout=300).content; open('raw/ListOfSecurities.xlsx', 'wb').write(b)
    wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True); ws = wb.worksheets[0]; ws.reset_dimensions()
    rows = [r for r in ws.iter_rows(values_only=True) if r and any(c is not None for c in r)]
    stamp = str(rows[1][0] or ''); hi = next(i for i, r in enumerate(rows) if r and any(c and 'Stock Code' in str(c) for c in r)); hdr = [str(h).replace('\n', ' ').strip() for h in rows[hi]]
    out = [dict(zip(hdr, r)) for r in rows[hi + 1:]]
    json.dump({'src': HKEX, 'fetched': TODAY, 'stamp': stamp, 'header': hdr, 'rows': out}, open('raw/hkex_list.json', 'w', encoding='utf-8'), ensure_ascii=False, default=str)
    from collections import Counter
    print('HKEX rows', len(out), stamp, Counter(r.get('Category') for r in out).most_common(6), flush=True)
def gleif():
    if os.path.exists('raw/isin-lei-latest.zip'): return
    meta = requests.get('https://mapping.gleif.org/api/v2/isin-lei/latest', headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()['data']['attributes']
    rr = requests.get(meta['downloadLink'], timeout=600); open('raw/isin-lei-latest.zip', 'wb').write(rr.content); open('raw/isin-lei-latest.txt', 'w').write(meta['fileName']); print('GLEIF mapping file', meta['fileName'], flush=True)
if __name__ == '__main__':
    hkex()
    if '--no-gleif' not in sys.argv: gleif()
    print('FETCH DONE', flush=True)
