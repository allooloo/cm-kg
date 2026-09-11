"""Step 7 — the workbook: Coverage (live COUNTA), Gaps, ASX, NSX, TMX Australia, Gaps detail, HITL, Method. Pond-native: every input is read from the
pond drops of this node (newest drop wins per key for identity workers); the output is written to POND\\au-cm-kg\\assembled\\<date>\\au-issuers.xlsx
and mirrored to CM-KG\\ISSUERS\\au-issuers.xlsx. Every enriched cell carries a source URL, a read-by label and a State. Nothing is inferred."""
import json, os, re, sys, datetime, shutil
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'au-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\au-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
def by_key(source, fn, k='key'): return {d[k]: d for d in pond.read_jsonl_all(NODE, source, fn, key=k)}
E_REG = by_key('width0', 'enr_reg.jsonl'); E_WIRE = by_key('width0', 'enr_wire.jsonl')
E_LEIREC = by_key('width0', 'lei_records.jsonl'); E_MATCH = by_key('width0', 'lei_match.jsonl', 'name')
ISIN_LEI = pond.read_json_latest(NODE, 'width0', 'isin_lei_hits.json') or {}
ISIN_META = pond.read_json_latest(NODE, 'width0', 'isin_lei_meta.json') or {}
ISIN_LEI_SRC = 'https://mapping.gleif.org/api/v2/isin-lei/latest (' + ISIN_META.get('file', 'daily file') + ')'
ASIC = {d['acn']: d for d in pond.read_jsonl_all(NODE, 'width0', 'asic_pub.jsonl', key='acn')}
ASIC_META = pond.read_json_latest(NODE, 'width0', 'asic_index_meta.json') or {}
ASIC_SRC = 'https://data.gov.au/data/dataset/asic-companies (' + ASIC_META.get('file', 'Company Dataset — Current') + ')'
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '')
    s = re.sub(r'\bLIMITED\b', 'LTD', s); s = re.sub(r'\bPROPRIETARY\b', 'PTY', s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
LEGAL_FORM = re.compile(r'\b(?:LTD|LIMITED|PTY|NL|INC|CORPORATION|CORP|PLC|HOLDINGS?|GROUP)\b')
def entity_key(s): return ' '.join(LEGAL_FORM.sub(' ', name_key(s)).split())
asic_by_name = {}
for acn, c in ASIC.items():
    asic_by_name.setdefault(name_key(c['name']), set()).add(acn)
    for p in c.get('previous_names', []): asic_by_name.setdefault(name_key(p['name']), set()).add(acn)
def is_corp(r): return r['security_type'] == 'Corporate'
STATE_NAMES = {'NSW': 'New South Wales', 'VIC': 'Victoria', 'QLD': 'Queensland', 'WA': 'Western Australia', 'SA': 'South Australia', 'TAS': 'Tasmania', 'ACT': 'Australian Capital Territory', 'NT': 'Northern Territory'}
def state_of(addr):
    m = re.search(r'\b(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\b\s*\d{4}', addr or '')
    return STATE_NAMES[m.group(1)] + f' ({m.group(1)})' if m else ''
def city_of(addr):
    m = re.search(r',\s*([A-Za-z .\'-]+?)\s+(?:NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\b', addr or '')
    return m.group(1).strip() if m else ''
RB = {'asx_dir': 'ASX listed-companies directory (exchange list)', 'asx_co': 'ASX company record (exchange site, asx.com.au company page data)', 'asx_ann': 'asx.com.au announcements search (exchange site)', 'nsx': 'NSX official list feed (exchange list)', 'tmx': 'TMX Australia listings page (exchange site; read in a browser session)',
      'gleif_map': 'GLEIF ISIN-to-LEI mapping file (exact ISIN match)', 'gleif_exact': 'GLEIF name-exact', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'asic_bulk': 'ASIC company register bulk dataset (data.gov.au, weekly)', 'tavily': 'Tavily search + regex extraction from page text', 'tavily_wire': 'Tavily search restricted to wire domains (release hits)'}
COLS = ['Legal name', 'ASX code', 'Exchange', 'Security type', 'Share description', 'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'ACN', 'ABN', 'ASIC link (unverified — search entry)', 'ASIC source', 'ASIC read by', 'ASIC State', 'ASIC status', 'ASIC registration date',
        'Registered office', 'Registered office source', 'Registered office read by', 'Registered office State',
        'State', 'State source', 'State read by', 'State State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'GICS sector', 'GICS industry group', 'Sector source', 'Sector read by', 'Sector State',
        'Auditor', 'Annual report (ASX announcement)', 'Annual report source', 'Annual report read by',
        'Share registry', 'Share registry source', 'Share registry read by', 'Share registry State', 'Share registry evidence',
        'Newswire of habit', 'ASX announcements (12 months)', 'ASX announcements link', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Website', 'Website source', 'Listing date', 'Listing date source', 'Status', 'Roster source', 'Roster read by', 'Gaps']
ASIC_COL = 'ASIC link (unverified — search entry)'
def build(r):
    k = key(r); ex = r['exchange']; corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}
    o['Legal name'] = r['name']; o['ASX code'] = r['symbol']; o['Exchange'] = ex; o['Security type'] = r['security_type']; o['Share description'] = r.get('share_description') or ''
    o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = {'ASX': RB['asx_dir'], 'NSX': RB['nsx'], 'TMX Australia': RB['tmx']}[ex]
    src_co = r.get('company_src') or r['roster_src']; rb_co = RB['asx_co'] if ex == 'ASX' else (RB['nsx'] if ex == 'NSX' else RB['tmx'])
    if r.get('listing_date'): o['Listing date'] = r['listing_date']; o['Listing date source'] = src_co
    else: gaps.append(('Listing date', 'not on the exchange record'))
    if r.get('website'): o['Website'] = r['website']; o['Website source'] = src_co
    if r.get('isin'): o['ISIN'] = r['isin']; o['ISIN source'] = src_co; o['ISIN read by'] = rb_co; o['ISIN State'] = 'sourced'
    else: gaps.append(('ISIN', 'exchange record carries no ISIN' + ('' if r.get('ks_ok') or ex != 'ASX' else ' (ASX key-statistics record not returned)')))
    # LEI
    lei = ''; m = E_MATCH.get(r['name']); exact = [(l, v) for l, v in (m or {}).get('matches', [])]
    if r.get('isin') and ISIN_LEI.get(r['isin']):
        lei = ISIN_LEI[r['isin']].split('|')[0]; o['LEI'] = lei; o['LEI source'] = ISIN_LEI_SRC; o['LEI read by'] = RB['gleif_map']; o['LEI State'] = 'sourced'
        mrec = E_LEIREC.get(lei)
        if mrec and entity_key(mrec['name']) != entity_key(r['name']): o['LEI State'] = 'conflict'; gaps.append(('LEI', f"mapping file maps ISIN {r['isin']} to LEI {lei}, whose GLEIF legal name is \"{mrec['name']}\", not the issuer; LEI kept with State conflict, not used as a route to ASIC"))
    elif exact:
        lei = exact[0][0]; o['LEI'] = lei; o['LEI source'] = f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = RB['gleif_exact']; o['LEI State'] = 'sourced'
    else:
        why = ('ISIN not in the GLEIF ISIN-to-LEI mapping file; ' if r.get('isin') else 'no ISIN; ') + ('no GLEIF legal name equals the roster name' if m else 'GLEIF name lookup not run')
        gaps.append(('LEI', why))
    rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei: o['LEI registration status'] = rec.get('reg_status', '') if rec else 'record not read'
    # ASIC: (a) LEI record registeredAs (ASIC = RA000014) when the LEI is the issuer; (b) name-exact against current/previous names in the bulk register
    acn = ''; route = ''
    if rec and rec.get('registeredAt') == 'RA000014' and rec.get('registeredAs') and o['LEI State'] != 'conflict':
        cand = re.sub(r'\D', '', rec['registeredAs'])
        if len(cand) == 9: acn = cand; route = 'lei'
    if not acn:
        cands = asic_by_name.get(name_key(r['name']), set())
        if len(cands) == 1: acn = next(iter(cands)); route = 'name-exact'
        elif len(cands) > 1: gaps.append(('ACN', f'name matches {len(cands)} ASIC companies: ' + ', '.join(sorted(cands)[:4])))
    a = ASIC.get(acn)
    if acn and a:
        o['ACN'] = acn; o['ABN'] = a.get('abn', ''); o[ASIC_COL] = a['src']; o['ASIC source'] = rec['src'] if route == 'lei' else ASIC_SRC
        o['ASIC read by'] = 'GLEIF LEI record registeredAs (ACN on the LEI record) + ASIC bulk register row' if route == 'lei' else 'ASIC bulk register, name-exact (current or previous company name equals the roster name)'; o['ASIC State'] = 'sourced'
        o['ASIC status'] = a.get('status', ''); o['ASIC registration date'] = a.get('registered', '')
        if a.get('state'): o['State'] = STATE_NAMES.get(a['state'], a['state']) + f" ({a['state']})"; o['State source'] = ASIC_SRC; o['State read by'] = RB['asic_bulk'] + ' (state of registration)'; o['State State'] = 'sourced'
        o['Incorporation jurisdiction'] = 'Australia (ASIC-registered ' + {'APUB': 'public company', 'APTY': 'proprietary company'}.get(a.get('type', ''), a.get('type', '')) + ')'; o['Jurisdiction source'] = ASIC_SRC; o['Jurisdiction read by'] = RB['asic_bulk'] + ' (company type)'; o['Jurisdiction State'] = 'sourced'
    elif acn:
        o['ACN'] = acn; o[ASIC_COL] = f'https://connectonline.asic.gov.au/RegistrySearch/faces/landing/panelSearch.jspx?searchText={acn}'; o['ASIC source'] = rec.get('src', ''); o['ASIC read by'] = 'GLEIF LEI record registeredAs (ACN on the LEI record); not in the ASIC public-company index'; o['ASIC State'] = 'sourced'
        gaps.append(('ASIC status', 'ACN from the LEI record is not in the ASIC bulk public-company index (proprietary or overseas registration)'))
    else:
        gaps.append(('ACN', 'no LEI registeredAs at ASIC and no name-exact ASIC company'))
        if rec.get('jur'): o['Incorporation jurisdiction'] = rec['jur']; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec']; o['Jurisdiction State'] = 'sourced'
        else: gaps.append(('Incorporation jurisdiction', 'no ASIC row and no LEI record'))
    if o['Incorporation jurisdiction'] and rec.get('jur') and acn and not rec['jur'].startswith('AU'):
        o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"ACN {acn} at ASIC but GLEIF legal jurisdiction {rec['jur']}"))
    # registered office / HQ / state
    if rec.get('legal_city') or rec.get('legal_lines'):
        o['Registered office'] = ', '.join(v for v in ((rec.get('legal_lines') or []) + [rec.get('legal_city'), rec.get('legal_region'), rec.get('legal_postal'), rec.get('legal_country')]) if v); o['Registered office source'] = rec['src']; o['Registered office read by'] = RB['gleif_rec'] + ' (legal address)'; o['Registered office State'] = 'sourced'
        if not o['State'] and rec.get('legal_region', '').startswith('AU-'): o['State'] = STATE_NAMES.get(rec['legal_region'][3:], rec['legal_region']) + f" ({rec['legal_region'][3:]})"; o['State source'] = rec['src']; o['State read by'] = RB['gleif_rec'] + ' (legal address region)'; o['State State'] = 'sourced'
    elif r.get('contact_address'):
        o['Registered office'] = r['contact_address']; o['Registered office source'] = src_co; o['Registered office read by'] = RB['asx_co'] + ' (contact address)'; o['Registered office State'] = 'sourced'
    else: gaps.append(('Registered office', 'no LEI record and no address on the exchange record'))
    if rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address)'; o['HQ State'] = 'sourced'
    elif city_of(r.get('contact_address')): o['HQ city'] = city_of(r['contact_address']); o['HQ source'] = src_co; o['HQ read by'] = RB['asx_co'] + ' (contact address)'; o['HQ State'] = 'sourced'
    else: gaps.append(('HQ city', 'no LEI record and no city in the exchange contact address'))
    if not o['State'] and state_of(r.get('contact_address')): o['State'] = state_of(r['contact_address']); o['State source'] = src_co; o['State read by'] = RB['asx_co'] + ' (contact address)'; o['State State'] = 'sourced'
    if not o['State']: gaps.append(('State', 'no ASIC row, no LEI region, no state in the exchange contact address'))
    # sector
    if r.get('sector') or r.get('gics_group'):
        o['GICS sector'] = r.get('sector') or ''; o['GICS industry group'] = r.get('gics_group') or r.get('industry_group') or ''; o['Sector source'] = src_co if r.get('sector') else r['roster_src']; o['Sector read by'] = rb_co if r.get('sector') else o['Roster read by']; o['Sector State'] = 'sourced'
    else: gaps.append(('GICS sector', 'no sector on the exchange record'))
    # auditor: source link only at Width 0
    ar = r.get('annual_report')
    if ar: o['Annual report (ASX announcement)'] = ar['url'] + f"  [{ar['date']} {ar['headline']}]"; o['Annual report source'] = r.get('ann_query', ''); o['Annual report read by'] = RB['asx_ann']
    elif corp: gaps.append(('Annual report (ASX announcement)', 'no announcement headed Annual Report in the last 12 months on the ASX platform' if ex == 'ASX' else 'not an ASX issuer'))
    gaps.append(('Auditor', 'Width 0 records the annual report link only (ORDER-010: source link, not a read)'))
    # share registry
    c = E_REG.get(k)
    if r.get('registry_address'): o['Share registry'] = r['registry_address']; o['Share registry source'] = src_co; o['Share registry read by'] = RB['asx_co'] + ' (share registry address)'; o['Share registry State'] = 'sourced'
    elif c and c.get('reg'): o['Share registry'] = c['reg']; o['Share registry source'] = c['reg_src']; o['Share registry read by'] = RB['tavily']; o['Share registry evidence'] = c.get('reg_ev', ''); o['Share registry State'] = 'sourced'
    else: gaps.append(('Share registry', (c.get('reg_gap') or 'none found') if c else ('not searched (fund/trust/debt security)' if not corp else 'not searched')))
    # newswire: ASX platform primary, then wires
    if r.get('ann_12m'):
        o['ASX announcements (12 months)'] = r['ann_12m']; o['ASX announcements link'] = f"https://www.asx.com.au/markets/trade-our-cash-market/announcements/{r['symbol']}"
    w = E_WIRE.get(k)
    if ex == 'ASX' and r.get('ann_12m'):
        o['Newswire of habit'] = 'ASX Announcements Platform' + (f" + {w['wire']}" if w and w.get('wire') else ''); o['Newswire read by'] = RB['asx_ann'] + ((' · ' + RB['tavily_wire']) if w and w.get('wire') else ''); o['Newswire State'] = 'sourced'
        if w and w.get('hits'): o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits'])
    elif w and w.get('wire'):
        o['Newswire of habit'] = w['wire']; o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits']); o['Newswire read by'] = RB['tavily_wire']; o['Newswire State'] = 'sourced'
    else:
        gaps.append(('Newswire of habit', 'no announcements in 12 months on the ASX platform and ' + ((w.get('gap') or 'search error') if w else ('not searched (fund/trust/debt security)' if not corp else 'not searched'))))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['ASX', 'NSX', 'TMX Australia']; sheets = {s: [] for s in SHEETS}
gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets[r['exchange']].append(o)
    for f, why in gaps: gap_detail.append((r['exchange'], r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[(r['exchange'], f, why)] += 1
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
        if c in ('Legal name', 'Share registry', 'Registered office', 'Incorporation jurisdiction', 'Newswire of habit', 'GICS industry group'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower() or 'Annual report (' in c: w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30; sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in SHEETS] + [f'{ex} fill %' for ex in SHEETS] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
cv.append(['Entities (rows)', 'A'] + [f"=COUNTA('{ex}'!A2:A{sheet_rows[ex] + 1})" for ex in SHEETS] + ['', '', ''] + ["=SUM(C2:E2)", ''])
FIELDS = ['Legal name', 'ASX code', 'Security type', 'ISIN', 'LEI', 'ACN', 'ABN', ASIC_COL, 'Registered office', 'State', 'Incorporation jurisdiction', 'GICS sector', 'Auditor', 'Annual report (ASX announcement)', 'Share registry', 'Newswire of habit', 'ASX announcements link', 'HQ city', 'Website', 'Listing date']
rix = 3
for f in FIELDS:
    col = get_column_letter(COLS.index(f) + 1); line = [f, col]
    for ex in SHEETS: line.append(f"=COUNTA('{ex}'!{col}2:{col}{max(sheet_rows[ex] + 1, 2)})")
    for j, ex in enumerate(SHEETS): line.append(f"=IF({get_column_letter(3 + j)}$2=0,0,{get_column_letter(3 + j)}{rix}/{get_column_letter(3 + j)}$2)")
    line.append(f"=SUM(C{rix}:E{rix})"); line.append(f"=IF(I$2=0,0,I{rix}/I$2)"); cv.append(line); rix += 1
for row in cv.iter_rows(min_row=2):
    for cell in row:
        cell.font = ARIAL
        if cell.column in (6, 7, 8, 10): cell.number_format = '0.0%'
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the exchange tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node au-cm-kg (CM-KG\\POND\\au-cm-kg).'])
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
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Code', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('ASIC Connect / ASIC API', 'The ASIC company register is read from the free weekly bulk dataset on data.gov.au. Per-company ASIC Connect pages (registered office, officeholders, documents) sit behind a search UI; the ASIC Connect API needs a registered account and key (AGENT KEYS\\asic.txt absent). The ASIC link column is the public search entry with the ACN, unverified by fetch.'),
        ('TMX Australia (formerly Cboe Australia)', 'tmxaustralia.com/listings/companies renders no issuer list to machines or in a browser (reCAPTCHA-gated, marketing page only). A list of TMX Australia primary listings needs the exchange (email) or a data account. No TMX Australia rows this run.'),
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
METHOD = [('Order', 'ORDER-010 Part B Australia Width 0 sweep, node au-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried. Pond-native: every input read from CM-KG\\POND\\au-cm-kg drops; output versioned under assembled\\.'),
          ('Rosters', "ASX: the exchange's listed-companies directory file (code, name, GICS industry group, listing date; market cap dropped) plus the per-company record the public ASX company pages render (header, key statistics — ISIN only, about — website, contact address, share-registry address). NSX: the official-list RSS feed (code, name, ISIN, industry, nominated adviser, listed date). TMX Australia: no machine-readable list (HITL)."),
          ('LEI', f'GLEIF ISIN-to-LEI mapping file, exact ISIN match ({n_map} rows); fallback GLEIF name-exact ({n_exact} rows). Registration status, legal address, headquarters and legal jurisdiction from the LEI record. A mapping-file LEI whose legal name is another entity is kept with State conflict.'),
          ('ASIC (ACN / ABN)', "ACN from the LEI record's registeredAs when registered at RA000014 (ASIC) and the LEI is the issuer; else name-exact against current and previous company names of public companies in the ASIC bulk dataset (data.gov.au, weekly). ABN, status, registration date, state of registration and company type from the bulk row. The ASIC Connect API needs a key (HITL); the link column is the public search entry, unverified."),
          ('Registered office / state / HQ', 'GLEIF legal address and headquarters; state from the ASIC row, else the GLEIF region, else the state code in the ASX contact address. HQ city from GLEIF, else the ASX contact address.'),
          ('GICS sector', 'From the ASX company record (sector) and directory (industry group); NSX industry from the feed.'),
          ('Auditor', 'Not read at Width 0: the latest announcement headed "Annual Report" on the ASX announcements platform (12-month search) is recorded as the source link per row; the Fill pass reads it.'),
          ('Share registry', "From the ASX company record's share-registry address where the exchange publishes it; else Tavily page text, registry taken only from a closed list (Computershare, MUFG Corporate Markets / Link, Boardroom, Automic, Advanced Share Registry, Security Transfer, XCEND, Registry Direct) within 300 characters of \"registry\"; ties blank and flagged."),
          ('Newswire of habit', 'The ASX announcements platform is every ASX entity\'s primary channel: recorded with the 12-month announcement count and link. Wires beyond it: Tavily search restricted to PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile, Medianet, PRWire; majority of up to three releases.'),
          ('Sources that answered machines', 'asx.com.au directory CSV and company research API (JSON, public token) · asx.com.au announcements search (HTML) · NSX official-list RSS · data.gov.au ASIC bulk dataset · GLEIF API and mapping file · Tavily.'),
          ('Sources that refused machines', 'tmxaustralia.com listings (reCAPTCHA, no list) · ASIC Connect per-company pages and API (key) · the retired asx.com.au/asx/1 JSON API (404).'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees; filled / confirmed belong to the Fill and Confirm passes.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'au-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:36s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
