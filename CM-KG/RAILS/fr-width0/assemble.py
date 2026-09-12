"""Step 7 — the workbook: Coverage (live COUNTA), Gaps, Euronext Paris, Euronext Growth Paris, Euronext Access Paris, Gaps detail, HITL, Method. Pond-native: every
input is read from the pond drops of node fr-cm-kg (newest drop wins per key); the output is written to POND\\fr-cm-kg\\assembled\\<date>\\fr-issuers.xlsx and
mirrored to CM-KG\\ISSUERS\\fr-issuers.xlsx. Every enriched cell carries a source URL, a read-by label and a State. Nothing is inferred."""
import json, os, re, sys, datetime, shutil
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'fr-cm-kg'; TODAY = datetime.date.today().isoformat()
MIRROR = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\fr-issuers.xlsx'
def key(r): return r['exchange'] + '|' + r['symbol']
rows = json.load(open(pond.latest(NODE, 'width0', 'roster.json'), encoding='utf-8'))
def by_key(source, fn, k='key'): return {d[k]: d for d in pond.read_jsonl_all(NODE, source, fn, key=k)}
E_REG = by_key('width0', 'enr_reg.jsonl'); E_WIRE = by_key('width0', 'enr_wire.jsonl'); SIREN = by_key('width0', 'siren.jsonl')
E_LEIREC = by_key('width0', 'lei_records.jsonl')
BDIF = {}
_b = pond.read_json_latest(NODE, 'width0', 'bdif_societes.json') or {}
def name_key(s):
    s = (s or '').upper().replace('&', ' AND ').replace('.', '').replace(',', '').replace('-', ' ').replace("'", ' ')
    s = re.sub(r'\b(SA|SE|SCA|SAS|SOCIETE ANONYME|SOCIETE EUROPEENNE|GROUP|GROUPE|HOLDING|HOLDINGS|CIE|COMPAGNIE|ETS|ETABLISSEMENTS|LTD|PLC|NV|INC|CORP)\b', ' ', s)
    for a, b in (('É', 'E'), ('È', 'E'), ('Ê', 'E'), ('À', 'A'), ('Ç', 'C'), ('Ô', 'O'), ('Û', 'U'), ('Î', 'I')): s = s.replace(a, b)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())
for s in _b.get('societes', []): BDIF.setdefault(name_key(s.get('raison_sociale')), s)
BDIF_SRC = _b.get('src', 'https://bdif.amf-france.org/')
def names_overlap(a, b):
    ta = [t for t in name_key(a).split() if len(t) >= 3]; tb = [t for t in name_key(b).split() if len(t) >= 3]
    if not ta or not tb: return name_key(a) == name_key(b)
    for x in ta:
        for y in tb:
            if x == y or (len(x) >= 4 and len(y) >= 4 and (x.startswith(y) or y.startswith(x))): return True
    return False
def is_corp(r): return r['security_type'] == 'Corporate'
RB = {'firds': 'ESMA FIRDS full equity file (EU instrument reference data per trading venue)', 'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'siren': 'French State company search (recherche-entreprises.api.gouv.fr; INSEE / RNE register data)', 'bdif': 'AMF BDIF regulatory-information database (filer token)', 'tavily': 'Tavily search + regex extraction from page text', 'tavily_wire': 'Tavily search restricted to wire domains (release hits)'}
LEGAL_FORM = {'5800': 'Société européenne (SE)', '5710': 'Société anonyme à conseil d\'administration (SA)', '5720': 'Société anonyme à directoire (SA)', '5599': 'SA à conseil d\'administration (s.a.i.)', '5699': 'SA à directoire (s.a.i.)', '5306': 'Société en commandite par actions (SCA)', '5385': 'Société d\'exercice libéral en commandite par actions', '5710 ': 'SA', '5499': 'Société à responsabilité limitée (SARL)', '5770': 'SAS', '5785': 'SAS à associé unique', '6540': 'SCI', '5442': 'SARL d\'attribution'}
COLS = ['Legal name', 'FIRDS short name', 'Exchange', 'MIC', 'Security type', 'CFI', 'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'SIREN', 'Register link (Annuaire des entreprises)', 'Infogreffe link (unverified — search entry)', 'Register source', 'Register read by', 'Register State', 'Legal form (nature juridique)', 'Register status', 'Date of creation', 'NAF code',
        'AMF filer token (BDIF)', 'AMF BDIF link', 'AMF source', 'AMF read by',
        'Registered office', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'Sector', 'Sector source', 'Sector read by', 'Sector State',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Annual report', 'Annual report source', 'Annual report read by',
        'Share registrar', 'Share registrar source', 'Share registrar read by', 'Share registrar State', 'Share registrar evidence',
        'Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'HQ city', 'HQ source', 'HQ read by', 'HQ State', 'Listing date', 'Listing date source', 'Trading currency', 'Status', 'Roster source', 'Roster read by', 'Gaps']
def build(r):
    k = key(r); corp = is_corp(r); gaps = []; o = {c: '' for c in COLS}; french = r['isin'].startswith('FR')
    o['Legal name'] = r['name']; o['FIRDS short name'] = r.get('name_short') or ''; o['Exchange'] = r['exchange']; o['MIC'] = r['mic']; o['Security type'] = r['security_type'] + ('' if french or not corp else ' (foreign ISIN)'); o['CFI'] = r.get('cfi') or ''
    o['Status'] = r['status']; o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['firds']; o['Trading currency'] = r.get('currency') or ''
    if r.get('listing_date'): o['Listing date'] = r['listing_date']; o['Listing date source'] = r['roster_src']
    else: gaps.append(('Listing date', 'no first-trading or admission date on the FIRDS record'))
    o['ISIN'] = r['isin']; o['ISIN source'] = r['roster_src']; o['ISIN read by'] = RB['firds']; o['ISIN State'] = 'sourced'
    lei = r.get('lei') or ''; rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei:
        o['LEI'] = lei; o['LEI source'] = r['roster_src']; o['LEI read by'] = RB['firds'] + ' (issuer LEI on the instrument record)'; o['LEI State'] = 'sourced'; o['LEI registration status'] = rec.get('reg_status', '') if rec else 'record not read'
        if rec and not names_overlap(rec['name'], r['name']): o['LEI State'] = 'conflict'; gaps.append(('LEI', f"FIRDS issuer LEI {lei} names \"{rec['name']}\", not the instrument's issuer name; LEI kept with State conflict"))
    else: gaps.append(('LEI', 'no issuer LEI on the FIRDS record'))
    s = SIREN.get(k) or {}
    if s.get('siren'):
        o['SIREN'] = s['siren']; o['Register link (Annuaire des entreprises)'] = s.get('annuaire', ''); o['Infogreffe link (unverified — search entry)'] = f"https://www.infogreffe.fr/entreprise/{s['siren']}"; o['Register source'] = s.get('src', ''); o['Register read by'] = RB['siren'] + ' — ' + (s.get('route') or ''); o['Register State'] = 'sourced'
        o['Legal form (nature juridique)'] = LEGAL_FORM.get(str(s.get('legal_form') or ''), str(s.get('legal_form') or '')); o['Register status'] = {'A': 'Active', 'C': 'Ceased'}.get(s.get('status'), s.get('status') or ''); o['Date of creation'] = s.get('created') or ''; o['NAF code'] = s.get('naf') or ''
        if s.get('address'): o['Registered office'] = s['address']; o['Registered office source'] = s.get('src', ''); o['Registered office read by'] = RB['siren'] + ' (siège)'; o['Registered office State'] = 'sourced'
        o['Incorporation jurisdiction'] = 'France (RCS-registered ' + (o['Legal form (nature juridique)'] or 'company') + ')'; o['Jurisdiction source'] = s.get('src', ''); o['Jurisdiction read by'] = RB['siren'] + ' (nature juridique)'; o['Jurisdiction State'] = 'sourced'
        ras = re.sub(r'\D', '', rec.get('registeredAs') or '')
        if rec.get('registeredAt') in ('RA000189', 'RA000192') and ras and ras != s['siren']: o['Register State'] = 'conflict'; gaps.append(('SIREN', f"name-exact SIREN {s['siren']} but the LEI record registeredAs {rec.get('registeredAs')}"))
        if s.get('city'): o['HQ city'] = s['city'].title(); o['HQ source'] = s.get('src', ''); o['HQ read by'] = RB['siren'] + ' (siège commune)'; o['HQ State'] = 'sourced'
    else:
        if french and corp: gaps.append(('SIREN', ('no company in the State search equals the roster name (' + str(s.get('n_cands', 0)) + ' candidates; near: ' + '; '.join(x[1] for x in s.get('near', [])[:2]) + ')') if s and not s.get('error') else ('search error ' + str(s.get('error')) if s else 'not searched')))
        elif not french: gaps.append(('SIREN', 'foreign ISIN: not a French register entry'))
        if rec.get('jur'): o['Incorporation jurisdiction'] = rec['jur']; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec']; o['Jurisdiction State'] = 'sourced'
        else: gaps.append(('Incorporation jurisdiction', 'no register entry and no LEI record'))
    if o['Incorporation jurisdiction'].startswith('France') and rec.get('jur') and not rec['jur'].startswith('FR'): o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"RCS entry but GLEIF legal jurisdiction {rec['jur']}"))
    if not o['Registered office']:
        if rec.get('legal_city') or rec.get('legal_lines'):
            o['Registered office'] = ', '.join(v for v in ((rec.get('legal_lines') or []) + [rec.get('legal_city'), rec.get('legal_region'), rec.get('legal_postal'), rec.get('legal_country')]) if v); o['Registered office source'] = rec['src']; o['Registered office read by'] = RB['gleif_rec'] + ' (legal address)'; o['Registered office State'] = 'sourced'
        else: gaps.append(('Registered office', 'no register entry and no LEI record'))
    if not o['HQ city']:
        if rec.get('hq_city'): o['HQ city'] = rec['hq_city']; o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address)'; o['HQ State'] = 'sourced'
        else: gaps.append(('HQ city', 'no register entry and no LEI record'))
    b = BDIF.get(name_key(r['name']))
    if b: o['AMF filer token (BDIF)'] = b['jeton']; o['AMF BDIF link'] = 'https://bdif.amf-france.org/'; o['AMF source'] = BDIF_SRC; o['AMF read by'] = RB['bdif'] + ' (name-exact in the last 10,000 items)'
    elif french and corp: gaps.append(('AMF filer token (BDIF)', 'no filer with this name in the last 10,000 BDIF items (the API caps at 10,000; older filers need a per-filer search — HITL)'))
    if s.get('naf'): o['Sector'] = 'NAF ' + s['naf']; o['Sector source'] = s.get('src', ''); o['Sector read by'] = RB['siren'] + ' (activité principale, NAF)'; o['Sector State'] = 'sourced'
    else: gaps.append(('Sector', 'no register entry; FIRDS carries no sector'))
    if corp: gaps.append(('Auditor', 'Width 0 records the annual report link only (ORDER-016: source link, not a read); Euronext hosts no report index — the Fill pass reads the issuer site or the AMF filing')); gaps.append(('Annual report', 'no exchange-hosted annual-report index (AMF filings sit in BDIF per filer; Fill pass)'))
    c = E_REG.get(k)
    if c and c.get('reg'): o['Share registrar'] = c['reg']; o['Share registrar source'] = c['reg_src']; o['Share registrar read by'] = RB['tavily']; o['Share registrar evidence'] = c.get('reg_ev', ''); o['Share registrar State'] = 'sourced'
    else: gaps.append(('Share registrar', (c.get('reg_gap') or 'none found') if c else ('not searched (foreign ISIN / non-corporate)' if not (corp and french) else 'not searched')))
    w = E_WIRE.get(k)
    if w and w.get('wire'): o['Newswire of habit'] = w['wire']; o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits']); o['Newswire read by'] = RB['tavily_wire']; o['Newswire State'] = 'sourced'
    else: gaps.append(('Newswire of habit', ((w.get('gap') or 'search error') if w else ('not searched (foreign ISIN / non-corporate)' if not (corp and french) else 'not searched')) + '; AMF BDIF regulated information is the Width 1 primary'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['Euronext Paris', 'Euronext Growth Paris', 'Euronext Access Paris']; sheets = {s: [] for s in SHEETS}; gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets[r['exchange']].append(o)
    for f, why in gaps: gap_detail.append((r['exchange'], r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[(r['exchange'], f, why[:120])] += 1
sheet_rows = {}
for ex, data in sheets.items():
    ws = wb.create_sheet(ex); ws.append(COLS)
    for cell in ws[1]: cell.font = BOLD; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical='top')
    data.sort(key=lambda o: (0 if o['ISIN'].startswith('FR') else 1, o['Legal name'].lower()))
    for o in data: ws.append([CTRL.sub('', o[c]) if isinstance(o[c], str) else o[c] for c in COLS])
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{max(len(data) + 1, 2)}"
    for i, c in enumerate(COLS, 1):
        w = 14
        if c in ('Legal name', 'Share registrar', 'Registered office', 'Incorporation jurisdiction', 'Newswire of habit', 'Legal form (nature juridique)'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower(): w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30; sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in SHEETS] + [f'{ex} fill %' for ex in SHEETS] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
cv.append(['Entities (rows)', 'A'] + [f"=COUNTA('{ex}'!A2:A{sheet_rows[ex] + 1})" for ex in SHEETS] + ['', '', ''] + ["=SUM(C2:E2)", ''])
FIELDS = ['Legal name', 'Security type', 'ISIN', 'LEI', 'SIREN', 'Register link (Annuaire des entreprises)', 'AMF filer token (BDIF)', 'Registered office', 'Incorporation jurisdiction', 'Sector', 'Auditor', 'Annual report', 'Share registrar', 'Newswire of habit', 'HQ city', 'Listing date']
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
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the market tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '. Inputs: the pond drops of node fr-cm-kg. Lines with a foreign ISIN are carried as exchange lines outside the French corporate scope.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([22, 30, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'ISIN', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
HITL = [('Euronext issuer lists', 'live.euronext.com list pages and their data endpoint sit behind an anti-bot form (Drupal antibot), also from a browser session; the roster comes from the ESMA FIRDS full equity files instead (official, weekly, with issuer LEI). A Euronext data account would give the exchange\'s own list and segment flags.'),
        ('INPI / Infogreffe', 'The register of record (RNE) is read through the State\'s public company search (no key); per-company Infogreffe pages sit behind a search UI and the INPI API needs an account. The Infogreffe link column is the public search entry, unverified.'),
        ('AMF BDIF per-filer search', 'The informations API answers the last 10,000 items without a filter parameter that machines can use; filer tokens beyond that window need the site\'s search (JavaScript).'),
        ('Anthropic Admin API key', 'Balance and cost reads for the spend line need an Admin API key; the Messages key answers 401.')]
hs = wb.create_sheet('HITL — needs MK'); hs.append(['Item', 'What is needed'])
for cell in hs[1]: cell.font = BOLD; cell.fill = HFILL
for h in HITL: hs.append(list(h))
for row in hs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
hs.column_dimensions['A'].width = 34; hs.column_dimensions['B'].width = 140
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
n_s = sum(1 for s in SIREN.values() if s.get('siren')); n_lei = sum(1 for s in SIREN.values() if s.get('siren') and 'GLEIF' in (s.get('route') or ''))
METHOD = [('Order', 'ORDER-016 Part A France Width 0 sweep, node fr-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried. Pond-native. Duty line: MiFID II product governance.'),
          ('Roster', "ESMA FIRDS full equity files (weekly): every share (CFI ES…) admitted to trading on Euronext Paris (XPAR), Euronext Growth Paris (ALXP) and Euronext Access Paris (XMLI) without a termination date, with the issuer LEI, full and short name, currency, first trading and admission dates. Lines with a foreign ISIN are kept as exchange lines outside the French corporate scope. Euronext's own list pages refuse machines (anti-bot)."),
          ('LEI', 'The issuer LEI comes with the FIRDS record (reported by the venue); the LEI record supplies registration status, legal address, headquarters and jurisdiction. A FIRDS LEI whose GLEIF legal name shares no token with the instrument name is State conflict.'),
          ('SIREN / register', f"The State's public company search (recherche-entreprises.api.gouv.fr): route 1 the SIREN on the LEI record's registeredAs (INSEE, RA000189) looked up and confirmed ({n_lei} rows); route 2 name-exact ({n_s - n_lei} rows). Carried: SIREN, legal form (nature juridique), status, date of creation, NAF code, siège address; the Annuaire des entreprises page as the register link; Infogreffe as an unverified search entry."),
          ('AMF filer identity', 'AMF BDIF filer token (RS…) by name-exact against the filers named in the last 10,000 BDIF items; the AMF regulated-information trail is the Width 1 primary.'),
          ('Registered office / HQ', 'Siège from the register; GLEIF legal address and headquarters as fallback.'),
          ('Sector', 'NAF code from the register (activité principale); no exchange sector at Width 0.'),
          ('Auditor', 'Not read at Width 0 (source link only per the order); no exchange-hosted annual-report index; the Fill pass reads the issuer site or the AMF filing.'),
          ('Share registrar', 'Tavily page text, agent taken only from a closed list (Uptevia, Société Générale Securities Services, CACEIS Corporate Trust, BNP Paribas Securities Services, Euroclear France, CIC service titres, Banque Transatlantique, Computershare) within 300 characters of "registrar" / "teneur de compte" / "service titres"; ties blank and flagged.'),
          ('Newswire of habit', 'Tavily search restricted to Actusnews, GlobeNewswire, Business Wire, PR Newswire, ACCESS Newswire, Newsfile, EQS News; majority of up to three releases.'),
          ('Sources that answered machines', 'ESMA FIRDS (Solr file index + zipped XML) · recherche-entreprises.api.gouv.fr · bdif.amf-france.org API (last 10,000 items) · GLEIF · Tavily.'),
          ('Sources that refused machines', 'live.euronext.com lists (anti-bot form) · Infogreffe per-company pages (search UI) · INPI API (account).'),
          ('State', 'sourced = one source read; conflict = the second registry disagrees; filled / confirmed belong to the Fill and Confirm passes.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
outdir = pond.assembled(NODE); out = os.path.join(outdir, 'fr-issuers.xlsx'); wb.save(out)
os.makedirs(os.path.dirname(MIRROR), exist_ok=True); shutil.copy(out, MIRROR)
print('saved', out, 'mirrored to', MIRROR)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows (French ISIN {sum(1 for o in data if o["ISIN"].startswith("FR"))})')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:40s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
