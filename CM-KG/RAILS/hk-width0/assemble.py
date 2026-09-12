"""Step 4 — the workbook: Coverage (live COUNTA), Gaps, Main Board, GEM, REITs, Gaps detail, HITL, Method. Pond-native: every input is read from the pond
drops of node hk-cm-kg (newest drop wins per key); the output is written to POND\\hk-cm-kg\\assembled\\<date>\\hk-issuers.xlsx and mirrored to
CM-KG\\ISSUERS\\hk-issuers.xlsx. English only, no search layer, no lab reads, no door (ORDER-017 re-cut). Every enriched cell carries a source URL,
a read-by label and a State. Nothing is inferred."""
import json, os, re, sys, datetime, shutil
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'hk-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\hk-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
HITS = pond.read_json_latest(NODE, 'width0', 'isin_lei_hits.json') or {}
E_LEIREC = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_records.jsonl', key='key')}
LEIM = {d['key']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_match.jsonl', key='key')} if pond.latest(NODE, 'width0', 'lei_match.jsonl') else {}
MAPFILE = (open(pond.latest(NODE, 'width0', 'isin-lei-latest.txt')).read().strip() if pond.latest(NODE, 'width0', 'isin-lei-latest.txt') else 'isin-lei mapping file')
def is_corp(r): return r['security_type'] == 'Corporate'
RB = {'hkex': 'HKEX List of Securities (ListOfSecurities.xlsx)', 'gleif_map': f'GLEIF ISIN-to-LEI mapping file ({MAPFILE}, exact ISIN match)', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)'}
CC = {'HK': 'Hong Kong', 'KY': 'Cayman Islands', 'BM': 'Bermuda', 'CN': 'China (mainland)', 'VG': 'British Virgin Islands', 'SG': 'Singapore', 'US': 'United States', 'GB': 'United Kingdom', 'JE': 'Jersey', 'AU': 'Australia', 'CA': 'Canada', 'MY': 'Malaysia', 'TW': 'Taiwan', 'JP': 'Japan', 'LU': 'Luxembourg', 'IE': 'Ireland', 'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'KR': 'South Korea', 'TH': 'Thailand', 'ID': 'Indonesia', 'MO': 'Macao'}
COLS = ['Name of Securities (HKEX, English)', 'Exchange', 'Stock code', 'Security type', 'Sub-category (HKEX)',
        'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISIN country prefix',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status', 'Legal name (GLEIF)',
        'Register id (GLEIF registeredAs)', 'Register authority (GLEIF registeredAt)', 'Register source', 'Register read by', 'Register State',
        'Registered office (GLEIF legal address)', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'Sector', 'Sector source', 'Sector read by', 'Sector State',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Annual report', 'Annual report source', 'Annual report read by',
        'Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State',
        'Newswire of habit', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Trading currency', 'Board lot', 'Admitted to CCASS', 'Status', 'Roster source', 'Roster read by', 'Gaps']
def build(r):
    k = key(r); corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}
    o['Name of Securities (HKEX, English)'] = r['name']; o['Exchange'] = r['exchange']; o['Stock code'] = r['symbol']; o['Security type'] = r['security_type']; o['Sub-category (HKEX)'] = r.get('sub_category') or r.get('category') or ''
    o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['hkex']; o['Trading currency'] = r.get('currency') or ''; o['Board lot'] = r.get('board_lot') or ''; o['Admitted to CCASS'] = r.get('ccass') or ''
    if r.get('isin'): o['ISIN'] = r['isin']; o['ISIN source'] = r['roster_src']; o['ISIN read by'] = RB['hkex']; o['ISIN State'] = 'sourced'; o['ISIN country prefix'] = r['isin'][:2]
    else: gaps.append(('ISIN', 'no ISIN on the HKEX line'))
    hit = HITS.get(r.get('isin') or '', ''); lei = ''
    if hit and '|' not in hit: lei = hit; o['LEI'] = lei; o['LEI source'] = 'https://mapping.gleif.org/api/v2/isin-lei/latest'; o['LEI read by'] = RB['gleif_map']; o['LEI State'] = 'sourced'
    elif hit: gaps.append(('LEI', f'several LEIs map to this ISIN in the GLEIF file: {hit}'))
    else:
        m = LEIM.get(k) or {}
        if m.get('lei'): lei = m['lei']; o['LEI'] = lei; o['LEI source'] = f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = m.get('match', 'GLEIF name-exact'); o['LEI State'] = 'sourced'
        else: gaps.append(('LEI', 'ISIN not in the GLEIF mapping file' + ('; ' + m['gap'] if m.get('gap') else ' (no name route on this node: no search layer by order)')))
    rec = E_LEIREC.get(lei, {}) if lei else {}
    if rec:
        o['LEI registration status'] = rec.get('reg_status', ''); o['Legal name (GLEIF)'] = rec.get('name', '')
        if rec.get('registeredAs'): o['Register id (GLEIF registeredAs)'] = rec['registeredAs']; o['Register authority (GLEIF registeredAt)'] = rec.get('registeredAt', ''); o['Register source'] = rec['src']; o['Register read by'] = RB['gleif_rec'] + ' (registeredAs at the authority shown)'; o['Register State'] = 'sourced'
        else: gaps.append(('Register id', 'no registeredAs on the LEI record'))
        if rec.get('legal_city') or rec.get('legal_lines'): o['Registered office (GLEIF legal address)'] = ', '.join(v for v in ((rec.get('legal_lines') or []) + [rec.get('legal_city'), rec.get('legal_region'), rec.get('legal_postal'), rec.get('legal_country')]) if v); o['Registered office source'] = rec['src']; o['Registered office read by'] = RB['gleif_rec'] + ' (legal address)'; o['Registered office State'] = 'sourced'
        if rec.get('jur'): o['Incorporation jurisdiction'] = CC.get(rec['jur'].split('-')[0], rec['jur']) + f" ({rec['jur']})"; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec'] + ' (legal jurisdiction)'; o['Jurisdiction State'] = 'sourced'
        if r.get('isin') and rec.get('jur') and rec['jur'].split('-')[0] != r['isin'][:2] and r['isin'][:2] in CC: o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"ISIN prefix {r['isin'][:2]} but GLEIF legal jurisdiction {rec['jur']}"))
        if rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address)'; o['HQ State'] = 'sourced'
    else:
        if lei: gaps.append(('Register id', 'LEI record not read'))
        else: gaps.append(('Register id', 'no LEI; the Companies Registry (HK) and the Cayman / Bermuda registries have no free machine interface (HITL)')); gaps.append(('Registered office', 'no LEI record')); gaps.append(('Incorporation jurisdiction', 'no LEI record; the ISIN prefix is carried as read, not as a jurisdiction')); gaps.append(('HQ city', 'no LEI record'))
    gaps.append(('Sector', 'HKEX publishes the industry classification per issuer on its website pages, not in the List of Securities (no page reads by order)'))
    if corp:
        gaps.append(('Auditor', 'Width 0 only on this node (ORDER-017 re-cut): no filings read')); gaps.append(('Annual report', 'HKEXnews per-issuer search is a form; no page reads by order'))
        gaps.append(('Share registrar', 'not searched (no search layer on this node by order)')); gaps.append(('Newswire of habit', 'not searched (no search layer on this node by order)'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['Main Board', 'GEM', 'REITs']; sheets = {s: [] for s in SHEETS}; gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets[r['exchange']].append(o)
    for f, why in gaps: gap_detail.append((r['exchange'], r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[(r['exchange'], f, why[:120])] += 1
sheet_rows = {}
for ex, data in sheets.items():
    ws = wb.create_sheet(ex); ws.append(COLS)
    for cell in ws[1]: cell.font = BOLD; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical='top')
    data.sort(key=lambda o: (0 if o['Security type'] == 'Corporate' else 1, o['Stock code']))
    for o in data: ws.append([CTRL.sub('', o[c]) if isinstance(o[c], str) else o[c] for c in COLS])
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{max(len(data) + 1, 2)}"
    for i, c in enumerate(COLS, 1):
        w = 14
        if 'name' in c.lower() or c in ('Registered office (GLEIF legal address)', 'Incorporation jurisdiction'): w = 34
        if 'source' in c.lower(): w = 44
        if 'read by' in c.lower(): w = 30
        if c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30; sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in SHEETS] + [f'{ex} fill %' for ex in SHEETS] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
NS = len(SHEETS); c0 = 3; cS = c0 + NS; cAll = cS + NS
cv.append(['Entities (rows)', 'A'] + [f"=COUNTA('{ex}'!A2:A{sheet_rows[ex] + 1})" for ex in SHEETS] + [''] * NS + [f"=SUM({get_column_letter(c0)}2:{get_column_letter(c0 + NS - 1)}2)", ''])
FIELDS = ['Name of Securities (HKEX, English)', 'Security type', 'ISIN', 'LEI', 'Legal name (GLEIF)', 'Register id (GLEIF registeredAs)', 'Registered office (GLEIF legal address)', 'Incorporation jurisdiction', 'Sector', 'Auditor', 'Annual report', 'Share registrar', 'Newswire of habit', 'HQ city']
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
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the market tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node hk-cm-kg. English only; no search layer, no lab reads, no door on this node (ORDER-017 re-cut). Local-partner copy on the node page.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([14, 30, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Stock code', 'Name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('Local partner', 'Hong Kong stays Width 0 with local-partner copy on the node page (ORDER-017 re-cut): no search layer, no lab reads, no door. Width 1 (HKEXnews announcements) and Fill wait for a local partner or a CEO order.'),
        ('Companies Registry', 'The Hong Kong Companies Registry (ICRIS / e-Registry) is a paid search per company with no free machine interface; Cayman and Bermuda registries likewise. Register ids come only from the GLEIF record (registeredAs) where an LEI exists.'),
        ('LEI coverage', 'The GLEIF ISIN mapping covers a small share of HKEX lines (most issuers are Cayman or Bermuda incorporated and have no LEI); a name route was not run (no search layer by order; the HKEX short names are abbreviations). The GLEIF golden copy by name is the next keyless step if the CEO wants it.'),
        ('Sector', 'HKEX industry classification sits on per-issuer web pages, not in the List of Securities; not read by order.'),
        ('Anthropic Admin API key', 'Balance and cost reads for the spend line need an Admin API key; the Messages key answers 401.')]
hs = wb.create_sheet('HITL — needs MK'); hs.append(['Item', 'What is needed'])
for cell in hs[1]: cell.font = BOLD; cell.fill = HFILL
for hh in HITL: hs.append(list(hh))
for row in hs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
hs.column_dimensions['A'].width = 34; hs.column_dimensions['B'].width = 140
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
METHOD = [('Order', 'ORDER-017 (re-cut Sept 11 2026) Hong Kong Width 0 sweep, node hk-cm-kg, swept ' + TODAY + '. English only; no search layer; no lab reads; local-partner copy; no door. Fly by wire; sourced or blank; no prices or market data carried. Pond-native.'),
          ('Roster', 'HKEX List of Securities (ListOfSecurities.xlsx, ' + (rows[0].get('list_stamp', '') if rows else '') + '): Equity lines (Main Board, GEM, investment companies, trading-only securities, depositary receipts) and REITs with stock code, English name, ISIN, trading currency, board lot and eligibility flags. Warrants, CBBCs, ETPs and debt counted, not carried.'),
          ('LEI', 'GLEIF ISIN-to-LEI mapping file, exact ISIN match; the LEI record supplies the legal name, registration id and authority, legal address, jurisdiction and headquarters. No name route (no search layer by order).'),
          ('Register', 'No free machine interface at the Hong Kong Companies Registry or the Cayman / Bermuda registries; the register id is the GLEIF registeredAs where an LEI exists.'),
          ('Sector / auditor / registrar / newswire', 'Blank by order (Width 0 only, no page reads).'),
          ('Sources that answered machines', 'HKEX (ListOfSecurities.xlsx) · GLEIF.'),
          ('Sources not used', 'HKEXnews (per-issuer form), Companies Registry (paid search), CCASS pages, any lab or search API.'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'hk-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows (Corporate {sum(1 for o in data if o["Security type"] == "Corporate")})')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:40s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
