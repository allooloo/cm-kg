"""Step 7 — the workbook: Coverage (live COUNTA), Gaps, Xetra, Gaps detail, HITL, Method. Pond-native: every input is read from the pond drops of node de-cm-kg
(newest drop wins per key); the output is written to POND\\de-cm-kg\\assembled\\<date>\\de-issuers.xlsx and mirrored to CM-KG\\ISSUERS\\de-issuers.xlsx.
Every enriched cell carries a source URL, a read-by label and a State. Nothing is inferred."""
import json, os, re, sys, datetime, shutil, csv
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'de-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\de-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
def by_key(source, fn, k='key'): return {d[k]: d for d in pond.read_jsonl_all(NODE, source, fn, key=k)}
E_REG = by_key('width0', 'enr_reg.jsonl'); E_WIRE = by_key('width0', 'enr_wire.jsonl')
E_LEIREC = by_key('width0', 'lei_records.jsonl'); E_MATCH = by_key('width0', 'lei_match.jsonl', 'name')
ISIN_LEI = pond.read_json_latest(NODE, 'width0', 'isin_lei_hits.json') or {}
ISIN_META = pond.read_json_latest(NODE, 'width0', 'isin_lei_meta.json') or {}
ISIN_LEI_SRC = 'https://mapping.gleif.org/api/v2/isin-lei/latest (' + ISIN_META.get('file', 'daily file') + ')'
RA = {}
_ra = pond.latest(NODE, 'width0', 'gleif_ra_list.csv')
if _ra:
    _rd = csv.reader(open(_ra, encoding='utf-8-sig', errors='replace')); _h = [re.sub(r'^[^A-Za-z]+', '', h) for h in next(_rd)]  # the saved file carries a double-encoded BOM before the first header
    def _col(name): return next((i for i, h in enumerate(_h) if h.startswith(name)), None)
    _ic, _ir, _il, _io = _col('Registration Authority Code'), _col('International name of Register'), _col('Local name of Register'), _col('International name of organisation responsible')
    for row in _rd:
        if _ic is None or len(row) <= _ic or not row[_ic]: continue
        reg = (row[_ir] if _ir is not None and len(row) > _ir else '') or (row[_il] if _il is not None and len(row) > _il else '')
        org = row[_io] if _io is not None and len(row) > _io else ''
        def _fix(t):
            try: return t.encode('latin-1').decode('utf-8')  # the fetch saved the list as latin-1-decoded text
            except Exception: return t
        RA[row[_ic]] = _fix(reg or '') + ((' — ' + _fix(org)) if org else '')
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '').replace('-', ' ')
    s = re.sub(r'\b(AG|SE|KGAA|GMBH|LTD|LIMITED|INC|PLC|NV|N|O|HOLDING|HOLDINGS|GROUP|GRUPPE|AKTIENGESELLSCHAFT|CORP|CORPORATION|CO|INH|VZ|ST|NA|ON|VNA|VZO)\b', ' ', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
def names_overlap(a, b):
    """exchange short names are abbreviated (UTD.INTERNET, BAY.MOTOREN WERKE, HIGHLIGHT E AND E): the mapping-file LEI is another entity only when the two names share no distinctive token (a token of 4+ letters, or a 3-letter token that starts a name), allowing prefix abbreviations"""
    ta = [t for t in name_key(a).split() if len(t) >= 3]; tb = [t for t in name_key(b).split() if len(t) >= 3]
    if not ta or not tb: return name_key(a) == name_key(b)
    for x in ta:
        for y in tb:
            if x == y or (len(x) >= 4 and len(y) >= 4 and (x.startswith(y) or y.startswith(x))): return True
    return False
def is_corp(r): return r['security_type'] == 'Corporate'
RB = {'xetra': 'Xetra all-tradable-instruments file (exchange list, daily)', 'gleif_map': 'GLEIF ISIN-to-LEI mapping file (exact ISIN match)', 'gleif_exact': 'GLEIF name-exact', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'tavily': 'Tavily search + regex extraction from page text', 'tavily_wire': 'Tavily search restricted to wire domains (release hits)'}
HR_SEARCH = 'https://www.handelsregister.de/rp_web/erweitertesuche.xhtml'; BANZ = 'https://www.bundesanzeiger.de/pub/en/start?0'
COLS = ['Legal name', 'Symbol', 'WKN', 'Exchange', 'Segment (Xetra group)', 'Security type', 'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'Register number (HR)', 'Register court', 'Handelsregister link (unverified — search entry)', 'Register source', 'Register read by', 'Register State',
        'Registered office', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'Sector', 'Sector source', 'Sector read by', 'Sector State',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Annual report (Bundesanzeiger)', 'Annual report source', 'Annual report read by',
        'Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar evidence',
        'Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Designated sponsor', 'Trading currency', 'Status', 'Roster source', 'Roster read by', 'Gaps']
def build(r):
    k = key(r); corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}
    o['Legal name'] = r['name']; o['Symbol'] = r['symbol']; o['WKN'] = r.get('wkn') or ''; o['Exchange'] = r['exchange']; o['Segment (Xetra group)'] = r.get('segment') or ''; o['Security type'] = r['security_type']
    o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['xetra'] + (f" ({r['file_date'].strip()})" if r.get('file_date') else ''); o['Trading currency'] = r.get('currency') or ''; o['Designated sponsor'] = r.get('designated_sponsor') or ''
    o['ISIN'] = r['isin']; o['ISIN source'] = r['roster_src']; o['ISIN read by'] = RB['xetra']; o['ISIN State'] = 'sourced'
    lei = ''; m = E_MATCH.get(r['name']); exact = [(l, v) for l, v in (m or {}).get('matches', [])]
    if ISIN_LEI.get(r['isin']):
        lei = ISIN_LEI[r['isin']].split('|')[0]; o['LEI'] = lei; o['LEI source'] = ISIN_LEI_SRC; o['LEI read by'] = RB['gleif_map']; o['LEI State'] = 'sourced'
        mrec = E_LEIREC.get(lei)
        if mrec and not names_overlap(mrec['name'], r['name']): o['LEI State'] = 'conflict'; gaps.append(('LEI', f"mapping file maps ISIN {r['isin']} to LEI {lei}, whose GLEIF legal name is \"{mrec['name']}\", not the issuer; LEI kept with State conflict, not used as a register route"))
    elif exact:
        lei = exact[0][0]; o['LEI'] = lei; o['LEI source'] = f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = RB['gleif_exact']; o['LEI State'] = 'sourced'
    else: gaps.append(('LEI', 'ISIN not in the GLEIF ISIN-to-LEI mapping file; ' + ('no GLEIF legal name equals the roster name' if m else 'GLEIF name lookup not run')))
    rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei: o['LEI registration status'] = rec.get('reg_status', '') if rec else 'record not read'
    ras = (rec.get('registeredAs') or '').strip()
    if rec and re.search(r'(?i)\bHR[AB]\b', ras) and o['LEI State'] != 'conflict':
        o['Register number (HR)'] = ras; o['Register court'] = RA.get(rec.get('registeredAt') or '', rec.get('registeredAt') or ''); o['Handelsregister link (unverified — search entry)'] = HR_SEARCH
        o['Register source'] = rec['src']; o['Register read by'] = RB['gleif_rec'] + ' (registeredAs / registeredAt: the Handelsregister sheet and the keeping court)'; o['Register State'] = 'sourced'
        o['Incorporation jurisdiction'] = 'Germany (Handelsregister ' + ras.split()[0].upper() + ')'; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec'] + ' (registeredAs)'; o['Jurisdiction State'] = 'sourced'
    else:
        if corp: gaps.append(('Register number (HR)', 'no LEI record with a Handelsregister registeredAs (HRA/HRB); handelsregister.de is a search form without an API (HITL)' if not rec else f"LEI record registeredAs '{ras}' is not a Handelsregister sheet ({rec.get('jur') or 'jurisdiction unknown'})"))
        if rec.get('jur'): o['Incorporation jurisdiction'] = rec['jur']; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec']; o['Jurisdiction State'] = 'sourced'
        else: gaps.append(('Incorporation jurisdiction', 'no LEI record'))
    if o['Incorporation jurisdiction'].startswith('Germany') and rec.get('jur') and not rec['jur'].startswith('DE'): o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"Handelsregister sheet but GLEIF legal jurisdiction {rec['jur']}"))
    if rec.get('legal_city') or rec.get('legal_lines'):
        o['Registered office'] = ', '.join(v for v in ((rec.get('legal_lines') or []) + [rec.get('legal_city'), rec.get('legal_region'), rec.get('legal_postal'), rec.get('legal_country')]) if v); o['Registered office source'] = rec['src']; o['Registered office read by'] = RB['gleif_rec'] + ' (legal address)'; o['Registered office State'] = 'sourced'
    else: gaps.append(('Registered office', 'no LEI record'))
    if rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address)'; o['HQ State'] = 'sourced'
    else: gaps.append(('HQ city', 'no LEI record'))
    gaps.append(('Sector', 'the Xetra instruments file carries index membership, not a sector classification; Fill pass'))
    if corp: gaps.append(('Auditor', 'Width 0 records the annual report link only (ORDER-015: source link, not a read)')); o['Annual report (Bundesanzeiger)'] = BANZ; o['Annual report source'] = BANZ; o['Annual report read by'] = 'Bundesanzeiger public search entry (scrape-hostile: link only, unverified per issuer)'
    c = E_REG.get(k)
    if c and c.get('reg'): o['Share registrar'] = c['reg']; o['Share registrar source'] = c['reg_src']; o['Share registrar read by'] = RB['tavily']; o['Share registrar evidence'] = c.get('reg_ev', ''); o['Share registrar State'] = 'sourced'
    else: gaps.append(('Share registrar', (c.get('reg_gap') or 'none found') if c else ('not searched (non-corporate)' if not corp else 'not searched')))
    w = E_WIRE.get(k)
    if w and w.get('wire'): o['Newswire of habit'] = w['wire']; o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits']); o['Newswire read by'] = RB['tavily_wire']; o['Newswire State'] = 'sourced'
    else: gaps.append(('Newswire of habit', ((w.get('gap') or 'search error') if w else ('not searched (non-corporate)' if not corp else 'not searched')) + '; EQS ad hoc / corporate news is read at Width 1'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['Xetra']; sheets = {s: [] for s in SHEETS}; gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets['Xetra'].append(o)
    for f, why in gaps: gap_detail.append(('Xetra', r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[('Xetra', f, why[:120])] += 1
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
        if c in ('Legal name', 'Share registrar', 'Registered office', 'Incorporation jurisdiction', 'Newswire of habit', 'Register court', 'Designated sponsor'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower() or 'Annual report (' in c: w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30; sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column', 'Xetra filled', 'Xetra fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
cv.append(['Entities (rows)', 'A', f"=COUNTA('Xetra'!A2:A{sheet_rows['Xetra'] + 1})", ''])
FIELDS = ['Legal name', 'Symbol', 'WKN', 'Segment (Xetra group)', 'Security type', 'ISIN', 'LEI', 'Register number (HR)', 'Register court', 'Registered office', 'Incorporation jurisdiction', 'Sector', 'Auditor', 'Annual report (Bundesanzeiger)', 'Share registrar', 'Newswire of habit', 'HQ city']
rix = 3
for f in FIELDS:
    col = get_column_letter(COLS.index(f) + 1); cv.append([f, col, f"=COUNTA('Xetra'!{col}2:{col}{max(sheet_rows['Xetra'] + 1, 2)})", f"=IF(C$2=0,0,C{rix}/C$2)"]); rix += 1
for row in cv.iter_rows(min_row=2):
    for cell in row:
        cell.font = ARIAL
        if cell.column == 4: cell.number_format = '0.0%'
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the Xetra tab. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node de-cm-kg.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([16, 30, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Symbol', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('Handelsregister', 'handelsregister.de is a public search form (no API, no deep links); the register sheet (HRA/HRB) and court are taken from the GLEIF LEI record instead. A register API key (e.g. the Common Register Portal bulk service) would give per-company sheets, officers and documents.'),
        ('Regulated Market vs Scale', "The Xetra instruments file carries index and country groups, not the Frankfurt segment (Regulated Market / Scale); the Börse Frankfurt API refuses plain clients (403 CORS). The Segment column shows the Xetra group; the Regulated Market / Scale split needs the exchange."),
        ('Bundesanzeiger', 'Scrape-hostile: the annual-report column is the public search entry, link only, unverified per issuer.'),
        ('Anthropic Admin API key', 'Balance and cost reads for the spend line need an Admin API key; the Messages key answers 401.')]
hs = wb.create_sheet('HITL — needs MK'); hs.append(['Item', 'What is needed'])
for cell in hs[1]: cell.font = BOLD; cell.fill = HFILL
for h in HITL: hs.append(list(h))
for row in hs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
hs.column_dimensions['A'].width = 34; hs.column_dimensions['B'].width = 140
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
n_map = sum(1 for r in rows if ISIN_LEI.get(r['isin'])); n_exact = sum(1 for r in rows if not ISIN_LEI.get(r['isin']) and (E_MATCH.get(r['name']) or {}).get('matches'))
METHOD = [('Order', 'ORDER-015 Part A Germany Width 0 sweep, node de-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried. Pond-native. Duty line: MiFID II product governance.'),
          ('Roster', "Deutsche Börse's daily Xetra all-tradable-instruments file: common shares (instrument type CS) in the German product groups (DAX, MDAX, SDAX, TecDAX, DEUTSCHLAND) or with a German ISIN; foreign shares traded on Xetra are left out. Segment = the Xetra product group."),
          ('LEI', f'GLEIF ISIN-to-LEI mapping file, exact ISIN match ({n_map} rows); fallback GLEIF name-exact ({n_exact} rows). German ISINs are well mapped.'),
          ('Handelsregister', 'The register sheet (HRA/HRB number) and the keeping court come from the LEI record (registeredAs / registeredAt, court named through the GLEIF registration-authority list). handelsregister.de itself is a search form (HITL); the link column is the public search entry.'),
          ('Registered office / HQ', 'GLEIF legal address and headquarters city.'),
          ('Sector', 'Not in the exchange file; blank at Width 0 (Fill pass).'),
          ('Auditor', 'Not read at Width 0 (source link only): the Bundesanzeiger public search entry is the link; the Fill pass reads the annual report from the issuer site.'),
          ('Share registrar', 'Tavily page text, provider taken only from a closed list (Link Market Services, Computershare Deutschland, ADEUS, Better Orange, Clearstream registered shares, in-house Aktienregister) within 300 characters of "share register" / "Aktienregister"; ties blank and flagged.'),
          ('Newswire of habit', 'Tavily search restricted to EQS News (DGAP), PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile, pressetext, IRW-Press; majority of up to three releases. EQS ad hoc and corporate news is the Width 1 primary.'),
          ('Sources that answered machines', 'xetra.com all-tradable-instruments CSV · GLEIF API, mapping file and RA list · Tavily.'),
          ('Sources that refused machines', 'api.boerse-frankfurt.de (403 CORS) · handelsregister.de (search form) · bundesanzeiger.de (scrape-hostile, link only) · eqs-news.com news paths (404 on the old paths; Width 1 finds the current feed).'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees; filled / confirmed belong to the Fill and Confirm passes.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'de-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:36s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
