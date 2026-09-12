"""Step 1 — pull the Japanese roster and register references into raw/ (a junction to the open pond drop POND\\jp-cm-kg\\width0\\<date>\\). Public, no key.
  JPX listed issuers ......... data_e.xlsx from jpx.co.jp (English): every listed line with local code, English name, market section (Prime / Standard /
                               Growth, domestic or foreign, PRO Market, ETFs / ETNs, REITs and funds), 33- and 17-sector codes and names, size index
  EDINET code list ........... Edinetcode.zip from disclosure2dl.edinet-fsa.go.jp: every EDINET filer with EDINET code, listed flag, consolidation flag,
                               capital, fiscal year end, Japanese and English names, address (Japanese), industry (Japanese), securities code (5 digits =
                               JPX local code + check digit) and the 13-digit corporate number (法人番号) — the national register key
  EDINET documents API ....... not read at Width 0 (Width 1 reads filings per issuer with AGENT KEYS\\edinet.txt)
No price or market data is carried. Machine-translated English is never a source: the English names are the ones EDINET and JPX publish."""
import requests, json, os, io, zipfile, csv, datetime
import openpyxl
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
os.makedirs('raw', exist_ok=True); TODAY = datetime.date.today().isoformat()
JPX = 'https://www.jpx.co.jp/english/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_e.xlsx'
EDINET = 'https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip'
def jpx():
    b = requests.get(JPX, headers=UA, timeout=300).content; open('raw/jpx_data_e.xlsx', 'wb').write(b)
    wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True); ws = wb.worksheets[0]; it = ws.iter_rows(values_only=True); hdr = [str(h).strip() for h in next(it)]
    rows = [dict(zip(hdr, r)) for r in it if r and r[1] is not None]
    json.dump({'src': JPX, 'fetched': TODAY, 'header': hdr, 'rows': rows}, open('raw/jpx_listed.json', 'w', encoding='utf-8'), ensure_ascii=False, default=str)
    from collections import Counter
    print('JPX rows', len(rows), 'effective date', rows[0].get('Effective Date'), Counter(r.get('Section/Products') for r in rows).most_common(12), flush=True)
def edinet():
    b = requests.get(EDINET, headers=UA, timeout=300).content; open('raw/Edinetcode.zip', 'wb').write(b)
    z = zipfile.ZipFile(io.BytesIO(b)); t = z.read(z.namelist()[0]).decode('cp932', 'replace'); lines = t.splitlines()
    stamp = lines[0]; rows = list(csv.reader(io.StringIO('\n'.join(lines[1:])))); hdr = rows[0]
    EN = {'ＥＤＩＮＥＴコード': 'edinet_code', '提出者種別': 'filer_type', '上場区分': 'listed', '連結の有無': 'consolidated', '資本金': 'capital_jpy_m', '決算日': 'fye', '提出者名': 'name_ja', '提出者名（英字）': 'name_en', '提出者名（ヨミ）': 'name_kana', '所在地': 'address_ja', '提出者業種': 'industry_ja', '証券コード': 'sec_code', '提出者法人番号': 'corporate_number'}
    out = [{EN.get(h, h): v for h, v in zip(hdr, r)} for r in rows[1:] if len(r) == len(hdr)]
    json.dump({'src': EDINET, 'fetched': TODAY, 'stamp': stamp, 'rows': out}, open('raw/edinet_codes.json', 'w', encoding='utf-8'), ensure_ascii=False)
    from collections import Counter
    print('EDINET filers', len(out), 'stamp', stamp, Counter(r['listed'] for r in out), 'with sec code', sum(1 for r in out if r.get('sec_code')), 'with corporate number', sum(1 for r in out if r.get('corporate_number')), flush=True)
if __name__ == '__main__':
    jpx(); edinet()
