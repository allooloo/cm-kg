"""Step 5 — the workbook: Coverage (live COUNTA), Gaps, NYSE, Nasdaq, Cboe, Gaps detail, HITL, Method. Pond-native: every input is read from the pond
drops of node us-cm-kg (newest drop wins per key); the output is written to POND\\us-cm-kg\\assembled\\<date>\\us-issuers.xlsx and mirrored to
CM-KG\\ISSUERS\\us-issuers.xlsx. Every enriched cell carries a source URL, a read-by label and a State. Nothing is inferred. EDGAR is the register of
record for a United States issuer (no national company register): CIK, SIC, state of incorporation, business address, fiscal year end and the
latest annual report come from the submissions header; LEI and ISIN come through GLEIF; auditor, registrar and newswire wait for the Fill pass."""
import json, os, re, sys, datetime, shutil
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'us-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\us-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
def by_key(source, fn, k='key'): return {d[k]: d for d in pond.read_jsonl_all(NODE, source, fn, key=k)}
LEIM = {d['cik']: d for d in pond.read_jsonl_all(NODE, 'width0', 'lei_match.jsonl', key='cik')}
E_LEIREC = by_key('width0', 'lei_records.jsonl')
E_REG = by_key('width0', 'enr_reg.jsonl'); E_WIRE = by_key('width0', 'enr_wire.jsonl')
def is_corp(r): return r['security_type'] == 'Corporate'
RB = {'edgar_list': 'EDGAR company_tickers_exchange.json (SEC list of exchange-listed filers)', 'edgar_sub': 'EDGAR submissions API (issuer header as filed)', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'gleif_isin': 'GLEIF ISIN list for the LEI (lei-records/<lei>/isins)'}
STATES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia', 'PR': 'Puerto Rico'}
COLS = ['Legal name', 'Exchange', 'Symbol', 'CIK', 'EDGAR filer page', 'Security type', 'Entity type', 'Filer category', 'SIC code', 'SIC description',
        'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'ISINs on the LEI (all)',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'State of incorporation', 'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'Business address', 'Business address source', 'Business address read by', 'Business address State',
        'Registered office (GLEIF legal address)', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Sector', 'Sector source', 'Sector read by', 'Sector State',
        'Fiscal year end (MMDD)', 'EIN', 'Former names', 'Website', 'IR website',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Annual report', 'Annual report form', 'Annual report date', 'Annual report source', 'Annual report read by',
        'Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar evidence',
        'Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Filings (12 months)', 'Other tickers (EDGAR)', 'Status', 'Roster source', 'Roster read by', 'Gaps']
def build(r):
    k = key(r); corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}
    o['Legal name'] = r['name']; o['Exchange'] = r['exchange']; o['Symbol'] = r['symbol']; o['CIK'] = str(r['cik']); o['EDGAR filer page'] = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(r['cik']):010d}"
    o['Security type'] = r['security_type']; o['Entity type'] = r.get('entity_type') or ''; o['Filer category'] = r.get('category') or ''; o['SIC code'] = r.get('sic') or ''; o['SIC description'] = r.get('sic_desc') or ''
    o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['edgar_list']; o['Filings (12 months)'] = r.get('filings_12m') or 0; o['Other tickers (EDGAR)'] = ', '.join(t for t in (r.get('tickers') or []) if t != r['symbol'])
    sub = r.get('submissions_src') if not r.get('submissions_error') else ''
    if not sub: gaps.append(('EDGAR submissions', f"submissions header not read ({r.get('submissions_error') or 'no response'})"))
    if r.get('sic'): o['Sector'] = f"{r['sic']} {r.get('sic_desc') or ''}".strip(); o['Sector source'] = sub; o['Sector read by'] = RB['edgar_sub'] + ' (SIC code as assigned by the SEC)'; o['Sector State'] = 'sourced'
    else: gaps.append(('Sector', 'no SIC code on the EDGAR header'))
    st = (r.get('state_inc') or '').upper()
    if st:
        o['State of incorporation'] = st
        if st in STATES: o['Incorporation jurisdiction'] = f'United States — {STATES[st]}'
        else: o['Incorporation jurisdiction'] = r.get('state_inc_desc') or st
        o['Jurisdiction source'] = sub; o['Jurisdiction read by'] = RB['edgar_sub'] + ' (stateOfIncorporation)'; o['Jurisdiction State'] = 'sourced'
    else: gaps.append(('Incorporation jurisdiction', 'no state of incorporation on the EDGAR header'))
    if r.get('business_city') or r.get('business_street'):
        o['Business address'] = ', '.join(v for v in (r.get('business_street'), r.get('business_city'), r.get('business_state'), r.get('business_zip')) if v); o['Business address source'] = sub; o['Business address read by'] = RB['edgar_sub'] + ' (business address)'; o['Business address State'] = 'sourced'
        o['HQ city'] = r.get('business_city') or ''; o['HQ source'] = sub; o['HQ read by'] = RB['edgar_sub'] + ' (business address city)'; o['HQ State'] = 'sourced'
    else: gaps.append(('Business address', 'no business address on the EDGAR header')); gaps.append(('HQ city', 'no business address on the EDGAR header'))
    o['Fiscal year end (MMDD)'] = r.get('fye') or ''; o['EIN'] = r.get('ein') or ''; o['Former names'] = ' | '.join(r.get('former_names') or []); o['Website'] = r.get('website') or ''; o['IR website'] = r.get('ir_website') or ''
    if r.get('latest_annual_accession'):
        acc = r['latest_annual_accession'].replace('-', ''); o['Annual report'] = f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{acc}/{r.get('latest_annual_doc') or ''}"; o['Annual report form'] = r.get('latest_annual_form') or ''; o['Annual report date'] = r.get('latest_annual_date') or ''; o['Annual report source'] = sub; o['Annual report read by'] = RB['edgar_sub'] + ' (latest annual report filing in the recent filings list)'
    elif corp: gaps.append(('Annual report', 'no 10-K / 20-F / 40-F in the recent filings list (new registrant or non-annual filer)'))
    m = LEIM.get(r['cik']) or {}
    lei = m.get('lei') or ''; rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei:
        o['LEI'] = lei; o['LEI source'] = rec.get('src') or f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = m.get('match', 'GLEIF name-exact'); o['LEI State'] = 'sourced'; o['LEI registration status'] = rec.get('reg_status', '') if rec else 'record not read'
    else: gaps.append(('LEI', m.get('gap') or 'not matched'))
    isins = rec.get('isins') if rec else None
    if isins:
        us = [i for i in isins if i.startswith('US')]; pick = us if us else isins
        o['ISIN'] = pick[0] if len(pick) == 1 else ''; o['ISINs on the LEI (all)'] = ', '.join(isins)
        if o['ISIN']: o['ISIN source'] = rec.get('isins_src', ''); o['ISIN read by'] = RB['gleif_isin']; o['ISIN State'] = 'sourced'
        else: gaps.append(('ISIN', f"{len(pick)} ISINs on the LEI (share classes / listings) — one line, several ISINs; all listed in the next column; the Fill pass ties the ISIN to the symbol"))
    elif lei and isins is not None: gaps.append(('ISIN', 'GLEIF maps no ISIN to this LEI'))
    elif lei: gaps.append(('ISIN', 'GLEIF ISIN list not read'))
    else: gaps.append(('ISIN', 'no LEI, so no GLEIF ISIN route; EDGAR carries no ISIN'))
    if rec:
        if rec.get('legal_city') or rec.get('legal_lines'):
            o['Registered office (GLEIF legal address)'] = ', '.join(v for v in ((rec.get('legal_lines') or []) + [rec.get('legal_city'), rec.get('legal_region'), rec.get('legal_postal'), rec.get('legal_country')]) if v); o['Registered office source'] = rec['src']; o['Registered office read by'] = RB['gleif_rec'] + ' (legal address)'; o['Registered office State'] = 'sourced'
        if st and rec.get('jur') and rec['jur'] not in (f'US-{st}', 'US'): o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"EDGAR state {st} but GLEIF legal jurisdiction {rec['jur']}"))
        if not o['HQ city'] and rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address)'; o['HQ State'] = 'sourced'
    if corp:
        gaps.append(('Auditor', 'Width 0 records the annual report link only; the Fill pass reads the 10-K cover (dei:AuditorName) — Gemini leads whole-filing reads, ChatGPT batch extracts (ORDER-017 re-cut)'))
        gaps.append(('Share registrar', 'not searched at Width 0 (ORDER-017: Perplexity Search + Tavily extraction only, in the Fill pass; the 10-K names the transfer agent)'))
        gaps.append(('Newswire of habit', 'not searched at Width 0 (Fill pass); 8-K exhibit 99.1 press releases on EDGAR are the Width 1 primary'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['NYSE', 'Nasdaq', 'Cboe']; sheets = {s: [] for s in SHEETS}; gap_detail = []; gap_summary = Counter()
for r in rows:
    if r['exchange'] not in sheets: continue
    o, gaps = build(r); sheets[r['exchange']].append(o)
    for f, why in gaps: gap_detail.append((r['exchange'], r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[(r['exchange'], f, why[:120])] += 1
sheet_rows = {}
for ex, data in sheets.items():
    ws = wb.create_sheet(ex); ws.append(COLS)
    for cell in ws[1]: cell.font = BOLD; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical='top')
    data.sort(key=lambda o: (0 if o['Security type'] == 'Corporate' else 1, o['Legal name'].lower()))
    for o in data: ws.append([CTRL.sub('', o[c]) if isinstance(o[c], str) else o[c] for c in COLS])
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{max(len(data) + 1, 2)}"
    for i, c in enumerate(COLS, 1):
        w = 14
        if c in ('Legal name', 'Share registrar', 'Business address', 'Registered office (GLEIF legal address)', 'Incorporation jurisdiction', 'Newswire of habit', 'Sector', 'Former names'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower() or c in ('Annual report', 'EDGAR filer page'): w = 44
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
FIELDS = ['Legal name', 'Security type', 'CIK', 'ISIN', 'LEI', 'State of incorporation', 'Incorporation jurisdiction', 'Business address', 'Registered office (GLEIF legal address)', 'Sector', 'Fiscal year end (MMDD)', 'Auditor', 'Annual report', 'Share registrar', 'Newswire of habit', 'HQ city', 'Website']
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
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the market tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node us-cm-kg. Funds, trusts, SPACs and non-operating entity types are carried on their tab with their type; the corporate scope is Security type = Corporate.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([12, 30, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Symbol', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('ISIN per share class', 'EDGAR carries no ISIN or CUSIP; the ISIN comes from the GLEIF ISIN list of the matched LEI. Issuers with several ISINs on one LEI (share classes, ADRs, listings) show the list and leave the ISIN cell blank until the Fill pass ties the ISIN to the symbol. A CUSIP licence would close this directly (CUSIP Global Services — paid; not proposed).'),
        ('LEI without a national register', 'There is no United States company register with an API; GLEIF is matched on the exact legal name and the EDGAR state of incorporation. Name-exact misses (renamed issuers, holding-company names) stay in Gaps.'),
        ('Auditor', 'Read at the Fill pass from the 10-K cover page (dei:AuditorName / AuditorLocation, iXBRL) — Gemini leads whole-filing reads, ChatGPT batch extracts, per the ORDER-017 re-cut.'),
        ('Anthropic Admin API key', 'Balance and cost reads for the spend line need an Admin API key; the Messages key answers 401.')]
hs = wb.create_sheet('HITL — needs MK'); hs.append(['Item', 'What is needed'])
for cell in hs[1]: cell.font = BOLD; cell.fill = HFILL
for hh in HITL: hs.append(list(hh))
for row in hs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
hs.column_dimensions['A'].width = 34; hs.column_dimensions['B'].width = 140
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
METHOD = [('Order', 'ORDER-017 (re-cut Sept 11 2026) United States Width 0 sweep, node us-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried. Pond-native. EDGAR keyless. Duty line: reasonable-basis suitability (FINRA Rule 2111).'),
          ('Roster', 'EDGAR company_tickers_exchange.json: every filer with a ticker and an exchange of NYSE, Nasdaq or CBOE; OTC and blank-exchange filers counted, not carried. One line per (exchange, ticker).'),
          ('Header', 'EDGAR submissions API per CIK (declared User-Agent, under 8 requests a second): name as filed, SIC code and description, state of incorporation, fiscal year end, filer category, entity type, EIN, business address, former names, tickers, and the recent filings list (last 12 months kept in the drop; the latest 10-K / 20-F / 40-F is the annual report link).'),
          ('LEI', 'GLEIF: filter[entity.legalName] then fuzzycompletions; a candidate becomes the LEI only when its legal name equals the EDGAR name after normalisation and its jurisdiction is US-<state of incorporation>. Foreign private issuers: name-exact with the jurisdiction as read.'),
          ('ISIN', 'GLEIF ISIN list for the matched LEI; one ISIN fills the cell, several are listed and the cell stays blank (HITL).'),
          ('Sector', 'The SIC code and description the SEC assigns (EDGAR header).'),
          ('Auditor / registrar / newswire', 'Blank at Width 0 by design (Fill pass: Gemini whole-filing reads, ChatGPT batch, Perplexity Search + preset fast, Tavily extraction only; Grok second; Mistral none).'),
          ('Sources that answered machines', 'EDGAR (company_tickers_exchange.json, submissions API, Archives) · GLEIF.'),
          ('Sources not used', 'No paid data (CUSIP Global Services, exchange reference-data feeds). Nasdaq and NYSE listing directories are not read: EDGAR is the register of record and carries the exchange.'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees; filled / confirmed belong to the Fill and Confirm passes.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'us-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows (Corporate {sum(1 for o in data if o["Security type"] == "Corporate")})')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:40s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
