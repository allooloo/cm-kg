"""Step 5 — the workbook: Coverage (live COUNTA), Gaps, KOSPI, KOSDAQ, KONEX, Gaps detail, HITL, Method. Pond-native: every input is read from the pond
drops of node kr-cm-kg (newest drop wins per key); the output is written to POND\\kr-cm-kg\\assembled\\<date>\\kr-issuers.xlsx and mirrored to
CM-KG\\ISSUERS\\kr-issuers.xlsx. Every enriched cell carries a source URL, a read-by label and a State. Nothing is inferred. Korean text is carried
as published; the English name is the one DART publishes (no machine translation)."""
import json, os, re, sys, datetime, shutil
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'kr-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\kr-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
def by_key(source, fn, k='key'): return {d[k]: d for d in pond.read_jsonl_all(NODE, source, fn, key=k)}
LEIM = by_key('width0', 'lei_match.jsonl'); E_LEIREC = by_key('width0', 'lei_records.jsonl')
def is_corp(r): return r['security_type'] == 'Corporate'
RB = {'kind': 'KIND (KRX) listed-company list (corpList.do download)', 'dart_cc': 'DART corpCode.xml (filer master, keyed API)', 'dart_co': 'DART company.json (company profile per corp_code, keyed API)', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'gleif_isin': 'GLEIF ISIN list for the LEI (lei-records/<lei>/isins)'}
EQ_ISIN = re.compile(r'^KR7\d{6}00\d$')
COLS = ['Legal name (English, DART)', 'Legal name (Korean)', 'Stock name (DART)', 'Exchange', 'Symbol', 'Security type',
        'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISINs on the LEI (all)',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'Corporate registration number (법인등록번호)', 'Business registration number (사업자등록번호)', 'DART corp code', 'Register source', 'Register read by', 'Register State', 'Corp class (DART)', 'Establishment date (DART)', 'Fiscal month',
        'Registered office (DART address, Korean)', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'Sector', 'Sector source', 'Sector read by', 'Sector State', 'Industry code (DART, KSIC)', 'Main products (KIND, Korean)',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Annual report', 'Annual report source', 'Annual report read by',
        'Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar evidence',
        'Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Region (KIND)', 'Listing date', 'Listing date source', 'Website', 'IR page', 'CEO (as published)', 'Status', 'Roster source', 'Roster read by', 'Gaps']
def build(r):
    k = key(r); corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}
    o['Legal name (English, DART)'] = r.get('name_en') or ''; o['Legal name (Korean)'] = r.get('name_ko') or ''; o['Stock name (DART)'] = r.get('stock_name') or ''; o['Exchange'] = r['exchange']; o['Symbol'] = r['symbol']; o['Security type'] = r['security_type']
    o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['kind']; o['Region (KIND)'] = r.get('region_ko') or ''; o['Website'] = r.get('website') or r.get('hm_url') or ''; o['IR page'] = r.get('ir_url') or ''; o['CEO (as published)'] = r.get('ceo_ko') or r.get('ceo_dart') or ''; o['Fiscal month'] = r.get('fiscal_month') or r.get('acc_mt') or ''; o['Main products (KIND, Korean)'] = r.get('products_ko') or ''
    if r.get('listing_date'): o['Listing date'] = r['listing_date']; o['Listing date source'] = r['roster_src']
    if not r.get('name_en'): gaps.append(('Legal name (English)', 'no English name on DART (corpCode / company profile)'))
    if r.get('industry_ko'): o['Sector'] = r['industry_ko']; o['Sector source'] = r['roster_src']; o['Sector read by'] = RB['kind'] + ' (업종)'; o['Sector State'] = 'sourced'; o['Industry code (DART, KSIC)'] = r.get('induty_code') or ''
    else: gaps.append(('Sector', 'no industry on the KIND line'))
    if r.get('corp_code'):
        o['DART corp code'] = r['corp_code']
        if r.get('company_src'):
            o['Corporate registration number (법인등록번호)'] = r.get('jurir_no') or ''; o['Business registration number (사업자등록번호)'] = r.get('bizr_no') or ''; o['Register source'] = r['company_src']; o['Register read by'] = RB['dart_co']; o['Register State'] = 'sourced' if (r.get('jurir_no') or r.get('bizr_no')) else ''
            o['Corp class (DART)'] = {'Y': 'Y (KOSPI)', 'K': 'K (KOSDAQ)', 'N': 'N (KONEX)', 'E': 'E (other)'}.get(r.get('corp_cls') or '', r.get('corp_cls') or ''); o['Establishment date (DART)'] = r.get('est_dt') or ''
            if r.get('address_ko'): o['Registered office (DART address, Korean)'] = r['address_ko']; o['Registered office source'] = r['company_src']; o['Registered office read by'] = RB['dart_co'] + ' (adres, as published)'; o['Registered office State'] = 'sourced'
            else: gaps.append(('Registered office', 'no address on the DART profile'))
            if r.get('jurir_no'): o['Incorporation jurisdiction'] = 'South Korea (DART filer with a corporate registration number)'; o['Jurisdiction source'] = r['company_src']; o['Jurisdiction read by'] = RB['dart_co'] + ' (jurir_no)'; o['Jurisdiction State'] = 'sourced'
        else: gaps.append(('Register id', 'DART company profile not read for this corp code')); gaps.append(('Registered office', 'DART profile not read'))
    else: gaps.append(('DART corp code', 'no DART filer with this stock code')); gaps.append(('Register id', 'no DART filer joined')); gaps.append(('Registered office', 'no DART filer joined'))
    m = LEIM.get(k) or {}; lei = m.get('lei') or ''; rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei:
        o['LEI'] = lei; o['LEI source'] = rec.get('src') or f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = m.get('match', 'GLEIF'); o['LEI State'] = 'sourced'; o['LEI registration status'] = rec.get('reg_status', '') if rec else 'record not read'
    else: gaps.append(('LEI', m.get('gap') or 'not matched'))
    isins = rec.get('isins') if rec else None
    if isins:
        eq = [i for i in isins if EQ_ISIN.match(i)]; o['ISINs on the LEI (all)'] = ', '.join(isins)
        if len(eq) == 1: o['ISIN'] = eq[0]; o['ISIN source'] = rec.get('isins_src', ''); o['ISIN read by'] = RB['gleif_isin'] + ' (the one equity-pattern ISIN KR7…00x)'; o['ISIN State'] = 'sourced'
        elif len(eq) > 1: gaps.append(('ISIN', f'{len(eq)} equity-pattern ISINs on the LEI (common and preferred lines); all listed in the next column; the Fill pass ties the ISIN to the code'))
        else: gaps.append(('ISIN', 'the LEI maps only non-equity ISINs; the Fill pass reads the ISIN from the KIND / KRX issuer page'))
    elif lei and isins is not None: gaps.append(('ISIN', 'GLEIF maps no ISIN to this LEI; the Fill pass reads the ISIN from the KIND / KRX issuer page'))
    elif lei: gaps.append(('ISIN', 'GLEIF ISIN list not read'))
    else: gaps.append(('ISIN', 'no LEI, so no GLEIF ISIN route; KIND and DART carry no ISIN (the KRX ISIN is KR7 + code + 00 + check digit — not derived, by rule)'))
    if rec:
        if not o['Incorporation jurisdiction'] and rec.get('jur'): o['Incorporation jurisdiction'] = rec['jur']; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec']; o['Jurisdiction State'] = 'sourced'
        elif o['Incorporation jurisdiction'].startswith('South Korea') and rec.get('jur') and not rec['jur'].startswith('KR'): o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"DART filer but GLEIF legal jurisdiction {rec['jur']}"))
        if rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address, as GLEIF carries it)'; o['HQ State'] = 'sourced'
    if not o['Incorporation jurisdiction']: gaps.append(('Incorporation jurisdiction', 'no DART corporate registration number and no LEI record'))
    if not o['HQ city']: gaps.append(('HQ city', 'no LEI record (the DART address is Korean text, carried as the registered office)'))
    if corp:
        gaps.append(('Auditor', 'Width 0 records no auditor; the Fill pass reads the 사업보고서 (annual report) through the DART API — ORDER-017 re-cut'))
        gaps.append(('Annual report', 'the Fill pass fetches the latest 사업보고서 receipt number through the DART list API (AGENT KEYS\\dart.txt)'))
        gaps.append(('Share registrar', 'not searched at Width 0 (Fill pass: Perplexity Search + Tavily extraction only; the annual report names the 명의개서대리인)'))
        gaps.append(('Newswire of habit', 'not searched at Width 0 (Fill pass); DART filings and KIND disclosures are the Width 1 primaries'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['KOSPI', 'KOSDAQ', 'KONEX']; sheets = {s: [] for s in SHEETS}; gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets[r['exchange']].append(o)
    for f, why in gaps: gap_detail.append((r['exchange'], r['symbol'], r.get('name_en') or r.get('name_ko'), r['security_type'], f, why)); gap_summary[(r['exchange'], f, why[:120])] += 1
sheet_rows = {}
for ex, data in sheets.items():
    ws = wb.create_sheet(ex); ws.append(COLS)
    for cell in ws[1]: cell.font = BOLD; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical='top')
    data.sort(key=lambda o: (0 if o['Security type'] == 'Corporate' else 1, o['Symbol']))
    for o in data: ws.append([CTRL.sub('', o[c]) if isinstance(o[c], str) else o[c] for c in COLS])
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{max(len(data) + 1, 2)}"
    for i, c in enumerate(COLS, 1):
        w = 14
        if 'name' in c.lower() or c in ('Share registrar', 'Registered office (DART address, Korean)', 'Incorporation jurisdiction', 'Newswire of habit', 'Sector', 'Main products (KIND, Korean)'): w = 34
        if 'source' in c.lower() or 'releases' in c.lower() or c in ('Annual report', 'Website', 'IR page'): w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30; sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in SHEETS] + [f'{ex} fill %' for ex in SHEETS] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
NS = len(SHEETS); c0 = 3; cS = c0 + NS; cAll = cS + NS
cv.append(['Entities (rows)', 'A'] + [f"=COUNTA('{ex}'!E2:E{sheet_rows[ex] + 1})" for ex in SHEETS] + [''] * NS + [f"=SUM({get_column_letter(c0)}2:{get_column_letter(c0 + NS - 1)}2)", ''])
FIELDS = ['Legal name (English, DART)', 'Legal name (Korean)', 'Security type', 'ISIN', 'LEI', 'Corporate registration number (법인등록번호)', 'Business registration number (사업자등록번호)', 'DART corp code', 'Registered office (DART address, Korean)', 'Incorporation jurisdiction', 'Sector', 'Fiscal month', 'Auditor', 'Annual report', 'Share registrar', 'Newswire of habit', 'HQ city', 'Website']
rix = 3
for f in FIELDS:
    col = get_column_letter(COLS.index(f) + 1); line = [f, col]
    for ex in SHEETS: line.append(f"=COUNTA('{ex}'!{col}2:{col}{max(sheet_rows[ex] + 1, 2)})")
    for j in range(NS): line.append(f"=IF({get_column_letter(c0 + j)}$2=0,0,{get_column_letter(c0 + j)}{rix}/{get_column_letter(c0 + j)}$2)")
    line.append(f"=SUM({get_column_letter(c0)}{rix}:{get_column_letter(c0 + NS - 1)}{rix})"); line.append(f"=IF({get_column_letter(cAll)}$2=0,0,{get_column_letter(cAll)}{rix}/{get_column_letter(cAll)}$2)"); cv.append(line); rix += 1
for row in cv.iter_rows(min_row=2):
    for cell in row:
        cell.font = ARIAL
        if cell.column in list(range(cS, cS + NS)) + [cAll + 1]: cell.number_format = '0.0%'
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the market tabs (row count on the Symbol column: KONEX lines can lack an English name). A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node kr-cm-kg. Korean text is carried as published; the English name is the one DART publishes.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([12, 34, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Symbol', 'Name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('ISIN', 'KIND and DART carry no ISIN; it comes from the GLEIF ISIN list of the matched LEI (one equity-pattern ISIN fills the cell). The KRX ISIN follows a fixed pattern from the code but is not derived (sourced or blank). A KRX data licence would close this directly (paid — not proposed).'),
        ('LEI coverage', 'GLEIF keys Korean companies by the business registration number (RA000657); listed companies without an LEI keep the DART registration numbers as their register keys.'),
        ('Auditor / annual report', 'Read at the Fill pass from the 사업보고서 through the DART API (key on disk); Korean as primary, machine-translated English never a source.'),
        ('KRX data portal', 'data.krx.co.kr serves its lists through a generate.cmd form; KIND (the KRX disclosure site) answers the corpList download directly and is the roster of record here.'),
        ('Anthropic Admin API key', 'Balance and cost reads for the spend line need an Admin API key; the Messages key answers 401.')]
hs = wb.create_sheet('HITL — needs MK'); hs.append(['Item', 'What is needed'])
for cell in hs[1]: cell.font = BOLD; cell.fill = HFILL
for hh in HITL: hs.append(list(hh))
for row in hs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
hs.column_dimensions['A'].width = 34; hs.column_dimensions['B'].width = 140
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
METHOD = [('Order', 'ORDER-017 (re-cut Sept 11 2026) South Korea Width 0 sweep, node kr-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried. Pond-native. Korean as primary; machine-translated English never a source.'),
          ('Roster', 'KIND (KRX disclosure site) listed-company list: Korean name, 6-digit code, market (KOSPI / KOSDAQ / KONEX), industry, main products, listing date, fiscal month, CEO, website, region.'),
          ('Register', 'DART corpCode.xml (filer master with corp_code and English name) and DART company.json per corp_code: corporate registration number (법인등록번호), business registration number (사업자등록번호), address, homepage, IR page, KSIC industry code, establishment date, corp class. Keyed API (AGENT KEYS\\dart.txt).'),
          ('LEI', 'GLEIF golden copy joined locally: registeredAs = the DART business registration number (RA000657) or the corporate registration number — exact; fallback the DART English or KIND Korean name equal to a GLEIF legal or other name (jurisdiction KR).'),
          ('ISIN', 'GLEIF ISIN list for the matched LEI; the one ISIN of the equity pattern (KR7 + code + 00 + check digit) fills the cell; others are listed and left to the Fill pass.'),
          ('Sector', 'KIND industry text (업종) with the DART KSIC code beside it.'),
          ('Auditor / registrar / newswire', 'Blank at Width 0 by design (Fill pass: DART annual report through the API, Perplexity Search + preset fast, Tavily extraction only; Grok second; Mistral review only).'),
          ('Sources that answered machines', 'KIND (corpList download) · DART (corpCode.xml, company.json — keyed) · GLEIF (golden copy, ISIN lists).'),
          ('Sources not used', 'No paid data (KRX data licences, KSD). data.krx.co.kr form endpoints not read.'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees; filled / confirmed belong to the Fill and Confirm passes.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'kr-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows (Corporate {sum(1 for o in data if o["Security type"] == "Corporate")})')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:44s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
