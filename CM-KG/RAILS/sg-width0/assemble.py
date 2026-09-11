"""Step 7 — the workbook: Coverage (live COUNTA), Gaps, SGX Mainboard, SGX Catalist, Gaps detail, HITL, Method. Pond-native: every input is read from the
pond drops of node sg-cm-kg (newest drop wins per key); the output is written to POND\\sg-cm-kg\\assembled\\<date>\\sg-issuers.xlsx and mirrored to
CM-KG\\ISSUERS\\sg-issuers.xlsx. Every enriched cell carries a source URL, a read-by label and a State. Nothing is inferred."""
import json, os, re, sys, datetime, shutil
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'sg-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\sg-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
def by_key(source, fn, k='key'): return {d[k]: d for d in pond.read_jsonl_all(NODE, source, fn, key=k)}
E_REG = by_key('width0', 'enr_reg.jsonl'); E_WIRE = by_key('width0', 'enr_wire.jsonl')
E_LEIREC = by_key('width0', 'lei_records.jsonl'); E_MATCH = by_key('width0', 'lei_match.jsonl', 'name')
ISIN_LEI = pond.read_json_latest(NODE, 'width0', 'isin_lei_hits.json') or {}
ISIN_META = pond.read_json_latest(NODE, 'width0', 'isin_lei_meta.json') or {}
ISIN_LEI_SRC = 'https://mapping.gleif.org/api/v2/isin-lei/latest (' + ISIN_META.get('file', 'daily file') + ')'
ACRA = {d['uen']: d for d in pond.read_jsonl_all(NODE, 'width0', 'acra_pub.jsonl', key='uen')}
ACRA_META = pond.read_json_latest(NODE, 'width0', 'acra_index_meta.json') or {}
ACRA_SRC = 'https://data.gov.sg/collections/2/view (ACRA Information on Corporate Entities, monthly; built ' + ACRA_META.get('built', TODAY) + ')'
ACRA_RA = 'RA000523'
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '')
    s = re.sub(r'\bLIMITED\b', 'LTD', s); s = re.sub(r'\bPRIVATE\b', 'PTE', s); s = re.sub(r'\bCORPORATION\b', 'CORP', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
LEGAL_FORM = re.compile(r'\b(?:LTD|LIMITED|PTE|INC|CORPORATION|CORP|PLC|BHD|BERHAD|HOLDINGS?|GROUP|CO)\b')
def entity_key(s): return ' '.join(LEGAL_FORM.sub(' ', name_key(s)).split())
acra_by_name = {}
for uen, c in ACRA.items():
    acra_by_name.setdefault(name_key(c['name']), set()).add(uen)
    for p in c.get('former_names', []): acra_by_name.setdefault(name_key(p), set()).add(uen)
def is_corp(r): return r['security_type'] == 'Corporate'
RB = {'sgx_list': 'SGX listed-securities feed (exchange list; stock screener roster)', 'sgx_mm': 'SGX market metadata feed (exchange list; ISIN, issuer name, FISN)', 'sgx_scr': 'SGX stock screener (sector classification the exchange publishes; data provider named on the screener: Morningstar)',
      'gleif_map': 'GLEIF ISIN-to-LEI mapping file (exact ISIN match)', 'gleif_exact': 'GLEIF name-exact', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'acra_bulk': 'ACRA register bulk dataset (data.gov.sg, monthly)', 'tavily': 'Tavily search + regex extraction from page text', 'tavily_wire': 'Tavily search restricted to wire domains (release hits)'}
COLS = ['Legal name', 'SGX code', 'Market', 'Security type', 'Trading name', 'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'FISN',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'Manager / depositary (SGX metadata issuer name)', 'UEN', 'ACRA link (unverified — search entry)', 'ACRA source', 'ACRA read by', 'ACRA State', 'ACRA entity type', 'ACRA status', 'Incorporation date',
        'Registered office', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'Sector (SGX)', 'Sector source', 'Sector read by', 'Sector State', 'Primary SSIC (ACRA)',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Annual report (SGXNet)', 'Annual report source', 'Annual report read by',
        'Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar evidence',
        'Newswire of habit', 'SGXNet announcements link', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Listing date', 'Listing date source', 'Trading currency', 'Status', 'Roster source', 'Roster read by', 'Gaps']
ACRA_COL = 'ACRA link (unverified — search entry)'
SGXNET = 'https://www.sgx.com/stock-exchange/company-announcements'
def build(r):
    k = key(r); corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}
    o['Legal name'] = r['name']; o['SGX code'] = r['symbol']; o['Market'] = {'MAINBOARD': 'Mainboard', 'CATALIST': 'Catalist', 'GLOBAL_QUOTE': 'GlobalQuote'}.get(r['market'], r['market']); o['Security type'] = r['security_type']; o['Trading name'] = r.get('name_display') or ''
    o['Manager / depositary (SGX metadata issuer name)'] = r.get('manager') or ''; o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['sgx_list']; o['Trading currency'] = r.get('currency') or ''
    if r.get('listing_date'): o['Listing date'] = r['listing_date']; o['Listing date source'] = r['roster_src']
    else: gaps.append(('Listing date', 'not on the exchange feed'))
    if r.get('isin'): o['ISIN'] = r['isin']; o['ISIN source'] = r['mm_src']; o['ISIN read by'] = RB['sgx_mm']; o['ISIN State'] = 'sourced'; o['FISN'] = r.get('fisn') or ''
    else: gaps.append(('ISIN', 'stock code not in the SGX market metadata feed'))
    # LEI
    lei = ''; m = E_MATCH.get(r['name']); exact = [(l, v) for l, v in (m or {}).get('matches', [])]
    if r.get('isin') and ISIN_LEI.get(r['isin']):
        lei = ISIN_LEI[r['isin']].split('|')[0]; o['LEI'] = lei; o['LEI source'] = ISIN_LEI_SRC; o['LEI read by'] = RB['gleif_map']; o['LEI State'] = 'sourced'
        mrec = E_LEIREC.get(lei)
        if mrec and entity_key(mrec['name']) != entity_key(r['name']): o['LEI State'] = 'conflict'; gaps.append(('LEI', f"mapping file maps ISIN {r['isin']} to LEI {lei}, whose GLEIF legal name is \"{mrec['name']}\", not the issuer; LEI kept with State conflict, not used as a route to ACRA"))
    elif exact:
        lei = exact[0][0]; o['LEI'] = lei; o['LEI source'] = f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = RB['gleif_exact']; o['LEI State'] = 'sourced'
    else:
        why = ('ISIN not in the GLEIF ISIN-to-LEI mapping file; ' if r.get('isin') else 'no ISIN; ') + ('no GLEIF legal name equals the roster name' if m else 'GLEIF name lookup not run')
        gaps.append(('LEI', why))
    rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei: o['LEI registration status'] = rec.get('reg_status', '') if rec else 'record not read'
    # ACRA: (a) LEI record registeredAs (ACRA = RA000523) when the LEI is the issuer; (b) name-exact against current/former names in the bulk register
    uen = ''; route = ''
    if rec and rec.get('registeredAt') == ACRA_RA and rec.get('registeredAs') and o['LEI State'] != 'conflict':
        cand = re.sub(r'[^A-Z0-9]', '', rec['registeredAs'].upper())
        if 9 <= len(cand) <= 10: uen = cand; route = 'lei'
    if not uen:
        cands = acra_by_name.get(name_key(r.get('manager') or r['name']), set())
        live = {u for u in cands if (ACRA.get(u) or {}).get('status', '').lower().startswith('live')}
        if len(cands) == 1: uen = next(iter(cands)); route = 'name-exact'
        elif len(live) == 1: uen = next(iter(live)); route = 'name-exact'
        elif len(cands) > 1: gaps.append(('UEN', f'name matches {len(cands)} ACRA entities: ' + ', '.join(sorted(cands)[:4])))
    a = ACRA.get(uen)
    if uen and a:
        o['UEN'] = uen; o[ACRA_COL] = a['src']; o['ACRA source'] = rec['src'] if route == 'lei' else ACRA_SRC
        o['ACRA read by'] = ('GLEIF LEI record registeredAs (UEN on the LEI record) + ACRA bulk register row' if route == 'lei' else 'ACRA bulk register, name-exact (current or former entity name equals the roster name)') + (' — the manager / depositary entity, not the listed trust or receipt' if r.get('manager') else ''); o['ACRA State'] = 'sourced'
        o['ACRA entity type'] = (a.get('entity_type') or '') + ((' — ' + a['company_type']) if a.get('company_type') and a['company_type'] != 'na' else ''); o['ACRA status'] = a.get('status', ''); o['Incorporation date'] = a.get('incorporated', '')
        if a.get('address'): o['Registered office'] = a['address']; o['Registered office source'] = ACRA_SRC; o['Registered office read by'] = RB['acra_bulk'] + (' (registered office address)' if a.get('entity_type') == 'Local Company' else ' (registered address in Singapore)'); o['Registered office State'] = 'sourced'
        if a.get('entity_type') == 'Local Company':
            o['Incorporation jurisdiction'] = 'Singapore (ACRA-registered ' + ((a.get('company_type') or 'company').lower().replace('na', 'company')) + ')'; o['Jurisdiction source'] = ACRA_SRC; o['Jurisdiction read by'] = RB['acra_bulk'] + ' (entity type, company type)'; o['Jurisdiction State'] = 'sourced'
        elif a.get('entity_type') == 'Foreign Company Branch':
            o['Incorporation jurisdiction'] = ('Foreign company: ' + rec['jur'] + ' per GLEIF; ' if rec.get('jur') else 'Foreign company (') + 'ACRA foreign-company branch registration' + ('' if rec.get('jur') else '; place of incorporation not in the dataset)'); o['Jurisdiction source'] = ACRA_SRC + ((' · ' + rec['src']) if rec.get('jur') else ''); o['Jurisdiction read by'] = RB['acra_bulk'] + ' (entity type)' + ((' · ' + RB['gleif_rec']) if rec.get('jur') else ''); o['Jurisdiction State'] = 'sourced'
        else:
            o['Incorporation jurisdiction'] = 'Singapore (ACRA-registered ' + (a.get('entity_type') or 'entity').lower() + ')'; o['Jurisdiction source'] = ACRA_SRC; o['Jurisdiction read by'] = RB['acra_bulk'] + ' (entity type)'; o['Jurisdiction State'] = 'sourced'
        if a.get('ssic'): o['Primary SSIC (ACRA)'] = re.sub(r'\s+na$', '', a['ssic']).strip()
        if a.get('auditors'):
            o['Auditor'] = ' | '.join(x['name'] for x in a['auditors']); o['Auditor source'] = ACRA_SRC; o['Auditor read by'] = RB['acra_bulk'] + ' (audit firm of record)'; o['Auditor State'] = 'sourced'
        elif corp: gaps.append(('Auditor', 'Width 0 records the annual report link only (ORDER-013: source link, not a read); the ACRA dataset carries no audit firm name for this row'))
    elif uen:
        o['UEN'] = uen; o[ACRA_COL] = 'https://www.bizfile.gov.sg/'; o['ACRA source'] = rec.get('src', ''); o['ACRA read by'] = 'GLEIF LEI record registeredAs (UEN on the LEI record); not in the ACRA public-company index'; o['ACRA State'] = 'sourced'
        gaps.append(('ACRA status', 'UEN from the LEI record is not in the ACRA index (not a public company or foreign branch, and no name match)'))
    else:
        gaps.append(('UEN', 'no LEI registeredAs at ACRA and no name-exact ACRA entity'))
        if corp: gaps.append(('Auditor', 'Width 0 records the annual report link only (ORDER-013: source link, not a read); no ACRA row'))
    if not o['Incorporation jurisdiction']:
        if rec.get('jur'): o['Incorporation jurisdiction'] = rec['jur']; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec']; o['Jurisdiction State'] = 'sourced'
        else: gaps.append(('Incorporation jurisdiction', 'no ACRA row and no LEI record'))
    if o['Incorporation jurisdiction'].startswith('Singapore') and rec.get('jur') and not rec['jur'].startswith('SG'):
        o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"UEN {uen} at ACRA as a local company but GLEIF legal jurisdiction {rec['jur']}"))
    # registered office / HQ fallbacks
    if not o['Registered office']:
        if rec.get('legal_city') or rec.get('legal_lines'):
            o['Registered office'] = ', '.join(v for v in ((rec.get('legal_lines') or []) + [rec.get('legal_city'), rec.get('legal_region'), rec.get('legal_postal'), rec.get('legal_country')]) if v); o['Registered office source'] = rec['src']; o['Registered office read by'] = RB['gleif_rec'] + ' (legal address)'; o['Registered office State'] = 'sourced'
        else: gaps.append(('Registered office', 'no ACRA row and no LEI record'))
    if rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address)'; o['HQ State'] = 'sourced'
    else: gaps.append(('HQ city', 'no LEI record'))
    # sector
    if r.get('sector'): o['Sector (SGX)'] = r['sector']; o['Sector source'] = r['sector_src']; o['Sector read by'] = RB['sgx_scr']; o['Sector State'] = 'sourced'
    else: gaps.append(('Sector (SGX)', 'stock code not on the SGX stock screener or no sector there'))
    # annual report: link not readable by machine (SGXNet API refuses)
    if corp: gaps.append(('Annual report (SGXNet)', 'SGXNet announcements API answers 401 to machines; the annual-report announcement link needs an SGX API key (HITL)'))
    # share registrar
    c = E_REG.get(k)
    if c and c.get('reg'): o['Share registrar'] = c['reg']; o['Share registrar source'] = c['reg_src']; o['Share registrar read by'] = RB['tavily']; o['Share registrar evidence'] = c.get('reg_ev', ''); o['Share registrar State'] = 'sourced'
    else: gaps.append(('Share registrar', (c.get('reg_gap') or 'none found') if c else ('not searched (fund/trust/depositary security)' if not corp else 'not searched')))
    # newswire: SGXNet primary, then wires
    o['SGXNet announcements link'] = SGXNET
    w = E_WIRE.get(k)
    o['Newswire of habit'] = 'SGXNet (exchange platform)' + (f" + {w['wire']}" if w and w.get('wire') else ''); o['Newswire read by'] = RB['sgx_list'] + ' (every SGX-listed issuer releases on SGXNet; announcement count not read — API refuses machines)' + ((' · ' + RB['tavily_wire']) if w and w.get('wire') else ''); o['Newswire State'] = 'sourced'
    if w and w.get('hits'): o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits'])
    if corp and not (w and w.get('wire')): gaps.append(('Newswire of habit', 'wires beyond SGXNet: ' + ((w.get('gap') or 'search error') if w else 'not searched')))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['SGX Mainboard', 'SGX Catalist']; sheets = {s: [] for s in SHEETS}
def sheet_of(r): return 'SGX Catalist' if r['market'] == 'CATALIST' else 'SGX Mainboard'
gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets[sheet_of(r)].append(o)
    for f, why in gaps: gap_detail.append((sheet_of(r), r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[(sheet_of(r), f, why)] += 1
sheet_rows = {}
for ex, data in sheets.items():
    ws = wb.create_sheet(ex); ws.append(COLS)
    for cell in ws[1]: cell.font = BOLD; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical='top')
    data.sort(key=lambda o: o['Legal name'].lower())
    for o in data: ws.append([CTRL.sub('', o[c]) if isinstance(o[c], str) else o[c] for c in COLS])
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{max(len(data) + 1, 2)}"
    for i, c in enumerate(COLS, 1):
        w = 14
        if c in ('Legal name', 'Share registrar', 'Registered office', 'Incorporation jurisdiction', 'Newswire of habit', 'Auditor', 'Primary SSIC (ACRA)', 'ACRA entity type'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower(): w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30; sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in SHEETS] + [f'{ex} fill %' for ex in SHEETS] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
cv.append(['Entities (rows)', 'A'] + [f"=COUNTA('{ex}'!A2:A{sheet_rows[ex] + 1})" for ex in SHEETS] + ['', ''] + ["=SUM(C2:D2)", ''])
FIELDS = ['Legal name', 'SGX code', 'Security type', 'ISIN', 'LEI', 'UEN', ACRA_COL, 'Registered office', 'Incorporation jurisdiction', 'Sector (SGX)', 'Primary SSIC (ACRA)', 'Auditor', 'Annual report (SGXNet)', 'Share registrar', 'Newswire of habit', 'SGXNet announcements link', 'HQ city', 'Listing date']
rix = 3
for f in FIELDS:
    col = get_column_letter(COLS.index(f) + 1); line = [f, col]
    for ex in SHEETS: line.append(f"=COUNTA('{ex}'!{col}2:{col}{max(sheet_rows[ex] + 1, 2)})")
    for j, ex in enumerate(SHEETS): line.append(f"=IF({get_column_letter(3 + j)}$2=0,0,{get_column_letter(3 + j)}{rix}/{get_column_letter(3 + j)}$2)")
    line.append(f"=SUM(C{rix}:D{rix})"); line.append(f"=IF(G$2=0,0,G{rix}/G$2)"); cv.append(line); rix += 1
for row in cv.iter_rows(min_row=2):
    for cell in row:
        cell.font = ARIAL
        if cell.column in (5, 6, 8): cell.number_format = '0.0%'
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the market tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node sg-cm-kg (CM-KG\\POND\\sg-cm-kg).'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
gs = wb.create_sheet('Gaps', 1); gs.append(['Market', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([16, 30, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Market', 'Code', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('SGX API key (SGXNet announcements, company profiles)', 'api.sgx.com/announcements and /companies answer 401 / 403 to every client, including a browser session on sgx.com. Per-issuer SGXNet announcement pages and the annual-report announcement link need an SGX API key or a data subscription. The SGXNet link column is the public search entry, unverified per issuer.'),
        ('ACRA BizFile per-entity pages', 'The ACRA register is read from the free monthly bulk dataset on data.gov.sg (27 files by first letter). Per-UEN BizFile pages sit behind the search UI; the ACRA link column is the public BizFile entry, unverified by fetch. A BizFile API account would give per-UEN business profiles (officers, capital).'),
        ('Perplexity Agent API', 'Not used at Width 0; from the Fill pass every Perplexity read uses the Agent API (preset low / fast); Sonar Chat Completions retire 2026-09-27.')]
hs = wb.create_sheet('HITL — needs MK'); hs.append(['Item', 'What is needed'])
for cell in hs[1]: cell.font = BOLD; cell.fill = HFILL
for h in HITL: hs.append(list(h))
for row in hs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
hs.column_dimensions['A'].width = 34; hs.column_dimensions['B'].width = 140
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
n_map = sum(1 for r in rows if r.get('isin') and ISIN_LEI.get(r['isin'])); n_exact = sum(1 for r in rows if not (r.get('isin') and ISIN_LEI.get(r['isin'])) and (E_MATCH.get(r['name']) or {}).get('matches'))
METHOD = [('Order', 'ORDER-013 Part B Singapore Width 0 sweep, node sg-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried. Pond-native: every input read from CM-KG\\POND\\sg-cm-kg drops; output versioned under assembled\\.'),
          ('Trusts and receipts', 'For REITs, business trusts and depositary receipts the market-metadata issuer name is the manager or depositary (a Pte. Ltd.): the row is named by the exchange trading name, the manager is carried in its own column, and the ACRA row (UEN, registered office, jurisdiction) is the manager entity, labelled as such.'),
          ('Rosters', "SGX listed-securities feed (the exchange's public stock-screener roster: trading name, stock code, security type, market Mainboard / Catalist / GlobalQuote, trading currency, listing date; price fields never carried) joined by stock code to the SGX market-metadata feed (ISIN, issuer legal name, FISN). Stocks, REITs / business trusts and depositary receipts are rows; ETFs, warrants, bonds and structured products are not. The single GlobalQuote row sits on the Mainboard tab with Market = GlobalQuote."),
          ('LEI', f'GLEIF ISIN-to-LEI mapping file, exact ISIN match ({n_map} rows); fallback GLEIF name-exact ({n_exact} rows). Registration status, legal address, headquarters and legal jurisdiction from the LEI record. A mapping-file LEI whose legal name is another entity is kept with State conflict.'),
          ('ACRA (UEN)', "UEN from the LEI record's registeredAs when registered at RA000523 (ACRA) and the LEI is the issuer; else name-exact against current and former entity names of public companies and foreign-company branches in the ACRA bulk dataset (data.gov.sg, monthly). Entity type, company type, status, incorporation date, registered address, primary SSIC and the audit firm(s) of record from the bulk row. Per-UEN BizFile pages are behind a search UI (HITL); the link column is the public entry, unverified."),
          ('Registered office / HQ', 'ACRA registered address (local companies) or registered address in Singapore (foreign branches); else GLEIF legal address. HQ city from the GLEIF headquarters address only.'),
          ('Incorporation jurisdiction', 'ACRA entity type: Local Company = Singapore (with the ACRA company type); Foreign Company Branch = foreign company with the GLEIF legal jurisdiction when an LEI record exists; else the GLEIF legal jurisdiction. A local company whose GLEIF jurisdiction is not SG is State conflict.'),
          ('Sector', "The sector classification on SGX's own stock screener (identity fields only requested: company name, stock code, sector; the screener names Morningstar as its data provider). ACRA primary SSIC carried beside it as the registry's activity code."),
          ('Auditor', 'Not read at Width 0 (source link only, per the order). The ACRA bulk dataset has audit-firm columns but they are empty for all but one of 20,385 indexed rows, so the register gives no auditor; the annual-report announcement link is not readable by machine (SGXNet API 401) and stays blank with a HITL gap. The Fill pass reads the annual report from the issuer site or once an SGX key exists.'),
          ('Share registrar', "Tavily page text, registrar taken only from a closed list (Boardroom, Tricor Barbinder, M & C Services, KCK CorpServe, B.A.C.S., In.Corp, RHT, Elite Partners, Vistra, Intertrust, Computershare Hong Kong) within 300 characters of \"registrar\"; ties blank and flagged."),
          ('Newswire of habit', 'SGXNet is every SGX-listed issuer\'s primary channel (Listing Rules; recorded from the roster; the announcement count is not read because the API refuses machines). Wires beyond it: Tavily search restricted to PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile, Media OutReach, ACN Newswire; majority of up to three releases.'),
          ('Sources that answered machines', 'api.sgx.com securities feed, market-metadata feed and stock screener (JSON, no key) · data.gov.sg ACRA collection (27 CSV files via the v2 poll-download API) · GLEIF API and mapping file · Tavily.'),
          ('Sources that refused machines', 'api.sgx.com announcements (401) and companies / stockfacts (403) — also from a browser session on sgx.com · www.sgx.com company pages ("Page has been moved" to investors.sgx.com, a Flutter app) · ACRA BizFile per-UEN pages (search UI).'),
          ('Duty', 'MAS product due diligence (Monetary Authority of Singapore, Notice on Recommendations on Investment Products / Guidelines on Fair Dealing): the duty name on the sg-cm-kg node page.'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees; filled / confirmed belong to the Fill and Confirm passes.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'sg-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:40s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
