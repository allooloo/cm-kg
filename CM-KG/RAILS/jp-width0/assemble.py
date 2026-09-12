"""Step 5 — the workbook: Coverage (live COUNTA), Gaps, Prime Market, Standard Market, Growth Market, PRO Market, REITs and funds, Gaps detail, HITL,
Method. Pond-native: every input is read from the pond drops of node jp-cm-kg (newest drop wins per key); the output is written to
POND\\jp-cm-kg\\assembled\\<date>\\jp-issuers.xlsx and mirrored to CM-KG\\ISSUERS\\jp-issuers.xlsx. Every enriched cell carries a source URL, a read-by
label and a State. Nothing is inferred; machine-translated English is never a source (English names are the ones JPX and EDINET publish; the
Japanese legal name and address are carried as published)."""
import json, os, re, sys, datetime, shutil
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'jp-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\jp-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
def by_key(source, fn, k='key'): return {d[k]: d for d in pond.read_jsonl_all(NODE, source, fn, key=k)}
LEIM = by_key('width0', 'lei_match.jsonl'); E_LEIREC = by_key('width0', 'lei_records.jsonl')
def is_corp(r): return r['security_type'].startswith('Corporate')
RB = {'jpx': 'JPX listed-issuers workbook (data_e.xlsx, English)', 'edinet': 'EDINET code list (Edinetcode.zip, filer master with corporate number)', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'gleif_isin': 'GLEIF ISIN list for the LEI (lei-records/<lei>/isins)'}
EQ_ISIN = re.compile(r'^JP3\d{6}000\d$')
COLS = ['Legal name (English, as published)', 'Legal name (Japanese)', 'Name (kana)', 'Exchange', 'JPX section', 'Symbol', 'Security type', 'Size (TOPIX index series)',
        'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISINs on the LEI (all)',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'Corporate number (法人番号)', 'EDINET code', 'Register source', 'Register read by', 'Register State', 'Filer type (EDINET)', 'Consolidated (EDINET)', 'Capital (JPY million, EDINET)', 'Fiscal year end (EDINET)',
        'Registered office (EDINET address, Japanese)', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'Sector', 'Sector source', 'Sector read by', 'Sector State', 'Sector (17)', 'Industry (EDINET, Japanese)',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Annual report', 'Annual report source', 'Annual report read by',
        'Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar evidence',
        'Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Status', 'Roster source', 'Roster read by', 'Gaps']
def build(r):
    k = key(r); corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}
    o['Legal name (English, as published)'] = r['name']; o['Legal name (Japanese)'] = r.get('name_ja') or ''; o['Name (kana)'] = r.get('name_kana') or ''; o['Exchange'] = r['exchange']; o['JPX section'] = r.get('section') or ''; o['Symbol'] = r['symbol']; o['Security type'] = r['security_type']; o['Size (TOPIX index series)'] = '' if r.get('size') in ('-', 'None') else (r.get('size') or '')
    o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['jpx']
    if r.get('sector33') and r['sector33'] != '-': o['Sector'] = f"{r.get('sector33_code')} {r['sector33']}"; o['Sector (17)'] = f"{r.get('sector17_code')} {r.get('sector17')}"; o['Sector source'] = r['roster_src']; o['Sector read by'] = RB['jpx'] + ' (33-sector classification)'; o['Sector State'] = 'sourced'
    else: gaps.append(('Sector', 'no 33-sector code on the JPX line (funds, PRO Market and foreign lines carry none)'))
    if r.get('edinet_code'):
        o['EDINET code'] = r['edinet_code']; o['Corporate number (法人番号)'] = r.get('corporate_number') or ''; o['Register source'] = r['edinet_src']; o['Register read by'] = RB['edinet']; o['Register State'] = 'sourced' if r.get('corporate_number') else ''
        o['Filer type (EDINET)'] = r.get('filer_type') or ''; o['Consolidated (EDINET)'] = r.get('consolidated') or ''; o['Capital (JPY million, EDINET)'] = r.get('capital_jpy_m') or ''; o['Fiscal year end (EDINET)'] = r.get('fye') or ''; o['Industry (EDINET, Japanese)'] = r.get('industry_ja') or ''
        if not r.get('corporate_number'): gaps.append(('Corporate number (法人番号)', 'EDINET filer joined but no corporate number on the code list'))
        if r.get('address_ja'): o['Registered office (EDINET address, Japanese)'] = r['address_ja']; o['Registered office source'] = r['edinet_src']; o['Registered office read by'] = RB['edinet'] + ' (所在地, as published)'; o['Registered office State'] = 'sourced'
        else: gaps.append(('Registered office', 'no address on the EDINET code list'))
        if r.get('filer_type') == '内国法人・組合': o['Incorporation jurisdiction'] = 'Japan (EDINET domestic filer)'; o['Jurisdiction source'] = r['edinet_src']; o['Jurisdiction read by'] = RB['edinet'] + ' (提出者種別)'; o['Jurisdiction State'] = 'sourced'
    else:
        gaps.append(('EDINET code', 'no EDINET filer with this securities code (' + ('foreign issuer, PRO Market or fund line' if (r.get('foreign') or r['exchange'] in ('PRO Market', 'REITs and funds')) else 'code not on the EDINET list') + ')'))
        gaps.append(('Registered office', 'no EDINET filer joined'))
    m = LEIM.get(k) or {}; lei = m.get('lei') or ''; rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei:
        o['LEI'] = lei; o['LEI source'] = rec.get('src') or f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = m.get('match', 'GLEIF'); o['LEI State'] = 'sourced'; o['LEI registration status'] = rec.get('reg_status', '') if rec else 'record not read'
    else: gaps.append(('LEI', m.get('gap') or 'not matched'))
    isins = rec.get('isins') if rec else None
    if isins:
        eq = [i for i in isins if EQ_ISIN.match(i)]; o['ISINs on the LEI (all)'] = ', '.join(isins)
        if len(eq) == 1: o['ISIN'] = eq[0]; o['ISIN source'] = rec.get('isins_src', ''); o['ISIN read by'] = RB['gleif_isin'] + ' (the one equity-pattern ISIN JP3…000x)'; o['ISIN State'] = 'sourced'
        elif len(eq) > 1: gaps.append(('ISIN', f'{len(eq)} equity-pattern ISINs on the LEI (share classes / preferred); all listed in the next column; the Fill pass ties the ISIN to the code'))
        else: gaps.append(('ISIN', 'the LEI maps only non-equity ISINs (bonds); the Fill pass reads the ISIN from the JPX issuer page'))
    elif lei and isins is not None: gaps.append(('ISIN', 'GLEIF maps no ISIN to this LEI; the Fill pass reads the ISIN from the JPX issuer page'))
    elif lei: gaps.append(('ISIN', 'GLEIF ISIN list not read'))
    else: gaps.append(('ISIN', 'no LEI, so no GLEIF ISIN route; JPX and EDINET carry no ISIN on their lists'))
    if rec:
        if not o['Incorporation jurisdiction'] and rec.get('jur'): o['Incorporation jurisdiction'] = rec['jur']; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec']; o['Jurisdiction State'] = 'sourced'
        elif o['Incorporation jurisdiction'].startswith('Japan') and rec.get('jur') and rec['jur'] != 'JP': o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"EDINET domestic filer but GLEIF legal jurisdiction {rec['jur']}"))
        if rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address, as GLEIF transliterates it)'; o['HQ State'] = 'sourced'
    if not o['Incorporation jurisdiction']: gaps.append(('Incorporation jurisdiction', 'no EDINET filer type and no LEI record'))
    if not o['HQ city']: gaps.append(('HQ city', 'no LEI record (the EDINET address is Japanese text, carried as the registered office)'))
    if corp:
        gaps.append(('Auditor', 'Width 0 records no auditor; the Fill pass reads the annual securities report (有価証券報告書) through the EDINET API — Gemini reads Japanese as primary, machine-translated English never a source (ORDER-017 re-cut)'))
        gaps.append(('Annual report', 'the Fill pass fetches the latest 有価証券報告書 document id through the EDINET API (AGENT KEYS\\edinet.txt)'))
        gaps.append(('Share registrar', 'not searched at Width 0 (Fill pass: Perplexity Search + Tavily extraction only; the securities report names the 株主名簿管理人)'))
        gaps.append(('Newswire of habit', 'not searched at Width 0 (Fill pass); TDnet timely disclosure and EDINET filings are the Width 1 primaries'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['Prime Market', 'Standard Market', 'Growth Market', 'PRO Market', 'REITs and funds']; sheets = {s: [] for s in SHEETS}; gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets[r['exchange']].append(o)
    for f, why in gaps: gap_detail.append((r['exchange'], r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[(r['exchange'], f, why[:120])] += 1
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
        if 'name' in c.lower() or c in ('Share registrar', 'Registered office (EDINET address, Japanese)', 'Incorporation jurisdiction', 'Newswire of habit', 'Sector'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower() or c == 'Annual report': w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30; sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in SHEETS] + [f'{ex} fill %' for ex in SHEETS] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
NS = len(SHEETS); c0 = 3; cS = c0 + NS; cAll = cS + NS
cv.append(['Entities (rows)', 'A'] + [f"=COUNTA('{ex}'!A2:A{sheet_rows[ex] + 1})" for ex in SHEETS] + [''] * NS + [f"=SUM({get_column_letter(c0)}2:{get_column_letter(c0 + NS - 1)}2)", ''])
FIELDS = ['Legal name (English, as published)', 'Legal name (Japanese)', 'Security type', 'ISIN', 'LEI', 'Corporate number (法人番号)', 'EDINET code', 'Registered office (EDINET address, Japanese)', 'Incorporation jurisdiction', 'Sector', 'Fiscal year end (EDINET)', 'Auditor', 'Annual report', 'Share registrar', 'Newswire of habit', 'HQ city']
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
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the market tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node jp-cm-kg. Japanese text is carried as published; English names are the ones JPX and EDINET publish — no machine translation.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([18, 30, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Symbol', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('ISIN', 'Neither the JPX list nor the EDINET code list carries the ISIN; it comes from the GLEIF ISIN list of the matched LEI (one equity-pattern ISIN fills the cell). Issuers without an LEI have no keyless ISIN route at Width 0; the Fill pass reads the JPX issuer page. A JPX / JSDA ISIN master would close this directly (paid data — not proposed).'),
        ('LEI coverage', 'GLEIF holds about 3,500 Japanese corporate-registry records; smaller listed companies often have no LEI. Rows without an LEI keep the corporate number as their register key.'),
        ('Corporate number register (法人番号公表サイト)', 'The National Tax Agency corporate-number API needs an application ID (HITL); the EDINET code list already carries the number and the Japanese address, so nothing is lost at Width 0.'),
        ('Auditor / annual report', 'Read at the Fill pass from the 有価証券報告書 through the EDINET API (key on disk): Gemini reads Japanese as primary; machine-translated English is never a source; Mistral review only.'),
        ('Anthropic Admin API key', 'Balance and cost reads for the spend line need an Admin API key; the Messages key answers 401.')]
hs = wb.create_sheet('HITL — needs MK'); hs.append(['Item', 'What is needed'])
for cell in hs[1]: cell.font = BOLD; cell.fill = HFILL
for hh in HITL: hs.append(list(hh))
for row in hs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
hs.column_dimensions['A'].width = 34; hs.column_dimensions['B'].width = 140
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
METHOD = [('Order', 'ORDER-017 (re-cut Sept 11 2026) Japan Width 0 sweep, node jp-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried. Pond-native. Japanese as primary; machine-translated English never a source.'),
          ('Roster', 'JPX listed-issuers workbook (data_e.xlsx): every listed line with local code, English name as JPX publishes it, market section, 33- and 17-sector codes and the TOPIX size series. Tabs = Prime, Standard, Growth, PRO Market, REITs and funds; ETFs / ETNs counted, not carried.'),
          ('Register', 'EDINET code list (Edinetcode.zip): the filer master joined on the securities code — Japanese legal name, kana, English name as filed, address, industry, filer type, consolidation, capital, fiscal year end and the 13-digit corporate number (法人番号).'),
          ('LEI', 'GLEIF by the register key: registeredAs = the 12-digit company registration number inside the corporate number, at RA000412 (exact, no name matching). Fallback for lines without a corporate number: fuzzycompletions on the English name, accepted only on an exact name match (jurisdiction JP for domestic lines).'),
          ('ISIN', 'GLEIF ISIN list for the matched LEI; the one ISIN of the equity pattern (JP3 + 6 digits + 000 + check digit) fills the cell; bonds and multiple share classes are listed and left to the Fill pass.'),
          ('Sector', 'JPX 33-sector classification (and the 17-sector roll-up); the EDINET industry text is carried beside it in Japanese.'),
          ('Auditor / registrar / newswire', 'Blank at Width 0 by design (Fill pass: EDINET securities report through the API, Gemini Japanese reads, Perplexity Search + preset fast, Tavily extraction only; Mistral review only).'),
          ('Sources that answered machines', 'JPX (data_e.xlsx) · EDINET (Edinetcode.zip; documents API keyed, for Width 1) · GLEIF.'),
          ('Sources not used', 'No paid data (JPX / JSDA ISIN masters, TSE data feeds). The NTA corporate-number API needs an application ID (HITL).'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees; filled / confirmed belong to the Fill and Confirm passes.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'jp-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows (Corporate {sum(1 for o in data if o["Security type"].startswith("Corporate"))})')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:44s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
