import json, os, re, sys, datetime
from collections import Counter, defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\ca-issuers.xlsx'
TODAY = datetime.date.today().isoformat()
rows = json.load(open('raw/roster.json'))
def key(r): return r['exchange'] + '|' + r['symbol']
def load(fn):
    d = {}
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try:
                x = json.loads(line); d[x['key']] = x
            except Exception: pass
    return d
E_CSE = load('raw/enr_cse.jsonl'); E_ISIN = load('raw/enr_isin.jsonl'); E_CORP = load('raw/enr_corp.jsonl')
E_WIRE = load('raw/enr_wire.jsonl'); E_SEDAR = load('raw/enr_sedar.jsonl'); E_LEI = {**load('raw/lei_match2.jsonl'), **load('raw/lei_match.jsonl')}; E_LEIREC = load('raw/lei_records.jsonl')
ISIN_LEI = json.load(open('raw/isin_lei_hits.json')) if os.path.exists('raw/isin_lei_hits.json') else {}
ISIN_LEI_SRC = 'https://mapping.gleif.org/api/v2/isin-lei/latest (' + (open('raw/isin-lei-latest.txt').read().strip() if os.path.exists('raw/isin-lei-latest.txt') else 'isin-lei-20260910T071509.zip') + ')'
CORP_TYPES = ('Corporate', 'CPC', 'Income Trust', '')
def is_corp(r): return r['security_type'].split(' (')[0] in CORP_TYPES

RB = {'tsx_dir': 'tsx.com company directory (exchange list)', 'tmx_xlsx': 'TMX listed-companies workbook (exchange list, monthly; data month named in the source column)',
      'cse_api': 'thecse.com listed-companies API (exchange list)', 'cse_page': 'thecse.com company page data (exchange site)', 'cboe_api': 'cboe.com listing-directory API (exchange list)',
      'gleif': 'GLEIF LEI record (LEI per the LEI column)', 'tavily': 'Tavily search + regex extraction from page text', 'tavily_wire': 'Tavily search restricted to wire domains (release hits)',
      'cse_sedar': 'constructed from SEDAR issuer number in CSE feed (sedarplus.ca/csa-party/<no>.html pattern)', 'tavily_sedar': 'Tavily search of sedarplus.ca (profile page whose heading matches the name)'}
PROV = {'CA-ON': 'Ontario', 'CA-BC': 'British Columbia', 'CA-AB': 'Alberta', 'CA-QC': 'Québec', 'CA-MB': 'Manitoba', 'CA-SK': 'Saskatchewan', 'CA-NS': 'Nova Scotia', 'CA-NB': 'New Brunswick', 'CA-NL': 'Newfoundland and Labrador', 'CA-PE': 'Prince Edward Island', 'CA-YT': 'Yukon', 'CA-NT': 'Northwest Territories', 'CA-NU': 'Nunavut', 'CA': 'Canada (federal)'}
KNOWN_AUD = [('KPMG LLP', r'\bKPMG\b'), ('Deloitte LLP', r'\bDeloitte\b|\bTouche\b'), ('PricewaterhouseCoopers LLP', r'PricewaterhouseCoopers|\bPwC\b'), ('Ernst & Young LLP', r'Ernst\s*&\s*Young|\bEY\b|^&\s*Young\b'), ('MNP LLP', r'\bMNP\b'), ('BDO Canada LLP', r'\bBDO\b'), ('Raymond Chabot Grant Thornton LLP', r'Raymond Chabot'), ('Doane Grant Thornton LLP', r'Doane Grant Thornton'), ('Grant Thornton LLP', r'Grant Thornton'), ('Davidson & Company LLP', r'Davidson\s*&\s*Company'), ('Dale Matheson Carr-Hilton LaBonte LLP', r'Dale Matheson|Carr-?Hilton|\bDMCL\b'), ('Manning Elliott LLP', r'Manning Elliott'), ('Crowe MacKay LLP', r'Crowe MacKay'), ('Smythe LLP', r'\bSmythe\b'), ('Baker Tilly WM LLP', r'Baker Tilly WM'), ('Baker Tilly', r'Baker Tilly'), ('Zeifmans LLP', r'Zeifmans'), ('UHY McGovern Hurley LLP', r'McGovern Hurley|\bUHY\b'), ('Kreston GTA LLP', r'Kreston'), ('Clearhouse LLP', r'Clearhouse'), ('Saturna Group Chartered Professional Accountants LLP', r'Saturna'), ('Marcum LLP', r'\bMarcum\b'), ('MaloneBailey LLP', r'Malone\s?Bailey'), ('Haskell & White LLP', r'Haskell'), ('SRCO Professional Corporation', r'\bSRCO\b'), ('Kingston Ross Pasnak LLP', r'Kingston Ross'), ('DNTW Toronto LLP', r'\bDNTW\b'), ('Charlton & Company', r'Charlton\s*&'), ('De Visser Gray LLP', r'De\s?Visser Gray'), ('Morgan & Company LLP', r'Morgan\s*&\s*Company'), ('WDM Chartered Professional Accountants', r'\bWDM\b'), ('Richter LLP', r'\bRichter\b'), ('Forvis Mazars LLP', r'Mazars'), ('Wolrige Mahon LLP', r'Wolrige'), ('McCarney Group LLP', r'McCarney'), ('Antares Professional Corporation', r'Antares Professional'), ('Segal GCSE LLP', r'Segal GCSE'), ('Stern & Lovrics LLP', r'Stern\s*&\s*Lovrics'), ('Buckley Dodds LLP', r'Buckley Dodds'), ('Turner, Moss & Company', r'Turner,? Moss'), ('Pinnacle CPA', r'Pinnacle CPA'), ('Harbourside CPA LLP', r'Harbourside'), ('SHIM & Associates LLP', r'\bSHIM\b'), ('Adam Sung Kim Ltd.', r'Adam Sung Kim'), ('Sam S. Mah Inc.', r'Sam S\.? Mah'), ('Deloitte & Associés', r'Associ[eé]s'), ('PSB Boisjoli LLP', r'Boisjoli'), ('Petrie Raymond LLP', r'Petrie Raymond'), ('Crowe BGK LLP', r'Crowe BGK'), ('Mao & Ying LLP', r'Mao\s*&\s*Ying'), ('Wasserman Ramsay', r'Wasserman Ramsay'), ('Jones & O\'Connell LLP', r"Jones\s*&\s*O'?Connell")]
def canon_aud(name):
    for canon, pat in KNOWN_AUD:
        if re.search(pat, name, re.I): return canon
    return name
KNOWN_SET = set(c for c, _ in KNOWN_AUD)
def is_known_aud(name): return name in KNOWN_SET
def repick_aud(c):
    cands = c.get('aud_cands') or {}
    if not cands: return c.get('aud', ''), c.get('aud_gap', 'none found')
    merged = Counter()
    for k, v in cands.items(): merged[canon_aud(k)] += v
    (b, s) = merged.most_common(1)[0]
    if len(merged) > 1 and merged.most_common(2)[1][1] == s:
        return '', 'conflict: ' + '; '.join(f'{k}({v})' for k, v in merged.most_common(3))
    return b, ''
def name_key(s):
    s = s.lower().replace('&', ' and ').replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('ô', 'o')
    return ' '.join(re.sub(r"[^a-z0-9 ]", ' ', s).split())
def name_exact_matches(m, name):
    """exact = GLEIF legal name equals roster name after case/space/punctuation normalisation only; loose = the matcher's normalised matches that are not exact."""
    if not m: return [], []
    exact = [(lei, v) for lei, v in m.get('matches', []) if name_key(v) == name_key(name)]
    for v, lei in m.get('cands', []):
        if lei and name_key(v) == name_key(name) and lei not in [l for l, _ in exact]: exact.append((lei, v))
    loose = [(lei, v) for lei, v in m.get('matches', []) if name_key(v) != name_key(name)]
    return exact, loose
def jur_label(j):
    if not j: return ''
    if j in PROV: return f'{PROV[j]} ({j})'
    return j

COLS = ['Legal name', 'Ticker', 'Root ticker', 'Other instruments', 'Exchange', 'Listing tier', 'Security type',
        'ISIN', 'ISIN source', 'ISIN read by',
        'LEI', 'LEI source', 'LEI read by', 'LEI registration status',
        'Sector', 'Sub-sector', 'Sector source', 'Sector read by',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction evidence',
        'SEDAR+ profile link', 'SEDAR+ issuer number', 'SEDAR+ source', 'SEDAR+ read by',
        'SEDI link (unverified — HTTP 403 on fetch)', 'SEDI read by',
        'Transfer agent', 'Transfer agent source', 'Transfer agent read by', 'Transfer agent evidence',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor evidence',
        'Newswire of habit', 'Newswire releases seen', 'Newswire read by',
        'HQ city', 'HQ province/state', 'HQ country/region', 'HQ source', 'HQ read by',
        'Listing date', 'Listing type', 'Status', 'Roster source', 'Roster read by', 'Gaps']
SEDI_COL = 'SEDI link (unverified — HTTP 403 on fetch)'
ENRICHED = ['ISIN', 'LEI', 'Sector', 'Incorporation jurisdiction', 'SEDAR+ profile link', 'SEDI link', 'Transfer agent', 'Auditor', 'Newswire of habit', 'HQ city', 'HQ province/state', 'Listing tier']

def build(r):
    k = key(r); ex = r['exchange']; corp = is_corp(r); gaps = []
    o = {c: '' for c in COLS}
    o['Legal name'] = r['name']; o['Ticker'] = r['symbol']; o['Root ticker'] = r['root']; o['Other instruments'] = r['instruments']; o['Exchange'] = ex
    o['Security type'] = r['security_type'] or ('Corporate (unclassified)' if ex in ('TSX', 'TSXV') else '')
    ld = str(r['listing_date'] or '')
    if re.fullmatch(r'\d{8}', ld): ld = f'{ld[:4]}-{ld[4:6]}-{ld[6:]}'
    o['Listing date'] = ld; o['Listing type'] = r['listing_type']; o['Status'] = r['status']
    o['Roster source'] = r['roster_src']; o['Roster read by'] = {'TSX': RB['tsx_dir'], 'TSXV': RB['tsx_dir'], 'CSE': RB['cse_api'], 'Cboe Canada': RB['cboe_api']}[ex]
    cse = E_CSE.get(k) if ex == 'CSE' else None
    if cse and 'error' in cse: cse = None
    # tier
    if r['tier']: o['Listing tier'] = r['tier']
    elif ex in ('TSX', 'Cboe Canada'): o['Listing tier'] = 'n/a (single-tier market)'
    else: gaps.append(('Listing tier', 'TSXV tier not published in the public issuer lists used'))
    # sector
    if r['sector']:
        o['Sector'] = r['sector']; o['Sub-sector'] = r['sub_sector']
        o['Sector source'] = r['enrich_src'] if ex in ('TSX', 'TSXV') else r['roster_src']
        o['Sector read by'] = RB['tmx_xlsx'] if ex in ('TSX', 'TSXV') else RB['cse_api']
    else:
        gaps.append(('Sector', 'exchange list carries no sector' if ex == 'Cboe Canada' else 'not in TMX July workbook (listed after 31-Jul-2026 or not covered)'))
    # ISIN
    i = E_ISIN.get(k)
    if i and i.get('isin') and r['security_type'].startswith('CDR') and not i['isin'].startswith('CA'):
        gaps.append(('ISIN', f"page ISIN {i['isin']} is not a Canadian ISIN; for a CDR that is the underlying share, not the receipt — left blank"))
    elif i and i.get('isin'):
        o['ISIN'] = i['isin']; o['ISIN source'] = i['src']; o['ISIN read by'] = RB['tavily']
    else:
        gaps.append(('ISIN', (i.get('gap') if i else 'not searched') if not (i and 'error' in i) else 'search error'))
    # LEI: (a) ISIN-to-LEI mapping file, exact ISIN; (b) GLEIF legal name equal to the roster name (case/space/punctuation only) = "GLEIF name-exact";
    #      looser name matches (legal-form expansion, dropped "The") are fuzzy and stay in Gaps with the candidate noted.
    m = E_LEI.get(k); lei = ''; exact, loose = name_exact_matches(m, r['name'])
    if o['ISIN'] and ISIN_LEI.get(o['ISIN'], ''):
        lei = ISIN_LEI[o['ISIN']].split('|')[0]; rec = E_LEIREC.get(lei, {})
        o['LEI'] = lei; o['LEI source'] = ISIN_LEI_SRC; o['LEI read by'] = 'GLEIF ISIN-to-LEI mapping file (exact ISIN match)'; o['LEI registration status'] = rec.get('reg_status', '')
    elif exact:
        lei = exact[0][0]; rec = E_LEIREC.get(lei, {})
        o['LEI'] = lei; o['LEI source'] = f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = 'GLEIF name-exact'; o['LEI registration status'] = rec.get('reg_status', '')
        if len(exact) > 1: o['LEI registration status'] += f" (note: {len(exact)} LEIs carry this exact legal name; first taken)"
    else:
        why = ('ISIN not in the GLEIF ISIN-to-LEI mapping file; ' if o['ISIN'] else 'no ISIN; ')
        if loose: why += 'GLEIF name match is fuzzy only, left blank: ' + '; '.join(f'{v} ({l})' for l, v in loose[:2])
        elif m: why += 'no GLEIF legal name equals the roster name'
        else: why += 'GLEIF name lookup not run'
        gaps.append(('LEI', why))
    rec = E_LEIREC.get(lei, {}) if lei else {}
    # jurisdiction
    c = E_CORP.get(k)
    if rec.get('jur'):
        o['Incorporation jurisdiction'] = jur_label(rec['jur']); o['Jurisdiction source'] = o['LEI source']; o['Jurisdiction read by'] = RB['gleif']
    elif cse and cse.get('jurisdiction'):
        o['Incorporation jurisdiction'] = cse['jurisdiction']; o['Jurisdiction source'] = cse['page']; o['Jurisdiction read by'] = RB['cse_page']
    else:
        # standing change 2026-09-10: jurisdiction comes from the GLEIF legal-jurisdiction field only; the statute-phrase read is retired
        gaps.append(('Incorporation jurisdiction', 'no LEI record (GLEIF legal jurisdiction is the only source since 2026-09-10)'))
    # SEDAR+
    if r.get('sedar_no'):
        o['SEDAR+ profile link'] = f"https://www.sedarplus.ca/csa-party/{r['sedar_no']}.html?_locale=en"; o['SEDAR+ issuer number'] = r['sedar_no']; o['SEDAR+ source'] = r['roster_src']; o['SEDAR+ read by'] = RB['cse_sedar']
    else:
        s = E_SEDAR.get(k)
        if s and s.get('sedar_no'):
            o['SEDAR+ profile link'] = s['canon']; o['SEDAR+ issuer number'] = s['sedar_no']; o['SEDAR+ source'] = s['url']; o['SEDAR+ read by'] = RB['tavily_sedar'] + (' [loose name match]' if s.get('match') == 'loose' else '')
        else:
            gaps.append(('SEDAR+ profile link', (s.get('gap') or 'search error') if s else ('not searched (fund/receipt security)' if not corp else 'not searched')))
    # SEDI: constructed, unverified (sedi.ca answers HTTP 403 to automated fetch; no per-issuer URL is published)
    sno = o['SEDAR+ issuer number']
    o[SEDI_COL] = 'https://www.sedi.ca/sedi/SVTIIBIselectIssuer?locale=en_CA' + (f'#sedar-issuer-{sno}' if sno else '')
    o['SEDI read by'] = 'constructed (SEDI insider-information-by-issuer search entry' + ('; issuer number from SEDAR+ column' if sno else '; no issuer number known') + ') — UNVERIFIED: HTTP 403 on fetch'
    gaps.append(('SEDI link', 'unverified: sedi.ca returns HTTP 403 to automated clients; link is the issuer-search entry' + ('' if sno else ' with no issuer number')))
    # transfer agent / auditor
    if cse and cse.get('transferAgent'):
        o['Transfer agent'] = cse['transferAgent']; o['Transfer agent source'] = cse['page']; o['Transfer agent read by'] = RB['cse_page']
    elif c and c.get('ta'):
        o['Transfer agent'] = c['ta']; o['Transfer agent source'] = c['ta_src']; o['Transfer agent read by'] = RB['tavily']; o['Transfer agent evidence'] = c['ta_ev']
    else:
        gaps.append(('Transfer agent', (c.get('ta_gap') or 'none found') if c else ('not searched (fund/receipt security)' if not corp else 'not searched')))
    if cse and cse.get('auditor'):
        o['Auditor'] = cse['auditor']; o['Auditor source'] = cse['page']; o['Auditor read by'] = 'CSE'
    else:
        aud_v, aud_g = repick_aud(c) if c else ('', '')
        if aud_v and is_known_aud(aud_v):
            o['Auditor'] = aud_v; o['Auditor read by'] = 'Tavily regex'
            o['Auditor source'] = c.get('aud_src') or ''; o['Auditor evidence'] = c.get('aud_ev', '')
        elif aud_v:
            gaps.append(('Auditor', f'string read but not a recognised audit-firm name, left blank: "{aud_v}"'))
        else:
            gaps.append(('Auditor', (aud_g or 'none found') if c else ('not searched (fund/receipt security)' if not corp else 'not searched')))
    # newswire
    w = E_WIRE.get(k)
    if w and w.get('wire'):
        o['Newswire of habit'] = w['wire'] + (f" ({w['note']})" if w.get('note') else ''); o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits']); o['Newswire read by'] = RB['tavily_wire']
    else:
        if w and w.get('hits'): o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits'])
        gaps.append(('Newswire of habit', (w.get('gap') or 'search error') if w else ('not searched (fund/receipt security)' if not corp else 'not searched')))
    # HQ
    if cse and cse.get('city'):
        o['HQ city'] = cse['city']; o['HQ province/state'] = cse['province']; o['HQ country/region'] = cse['country']; o['HQ source'] = cse['page']; o['HQ read by'] = RB['cse_page']
    elif rec.get('hq_city'):
        o['HQ city'] = rec['hq_city']; o['HQ province/state'] = PROV.get(rec.get('hq_region') or '', rec.get('hq_region') or ''); o['HQ country/region'] = rec.get('hq_country', ''); o['HQ source'] = o['LEI source']; o['HQ read by'] = RB['gleif']
        if r['hq_prov'] and r['hq_prov'] != (rec.get('hq_region') or '').replace('CA-', ''):
            o['HQ province/state'] += f" [TMX workbook says {r['hq_prov']}]"
    elif r['hq_prov'] or r['hq_region']:
        o['HQ province/state'] = r['hq_prov']; o['HQ country/region'] = r['hq_region'] + (f" ({r['hq_country_hint']})" if r['hq_country_hint'] else ''); o['HQ source'] = r['enrich_src']; o['HQ read by'] = RB['tmx_xlsx']
        gaps.append(('HQ city', 'TMX workbook gives province/region only; no LEI record to supply city'))
    else:
        gaps.append(('HQ city', 'no HQ source (no LEI match; exchange list carries no address)'))
        gaps.append(('HQ province/state', 'no HQ source'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps

wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
sheets = {'TSX': [], 'TSXV': [], 'CSE': [], 'Cboe Canada': []}
gap_detail = []; gap_summary = Counter()
for r in rows:
    o, gaps = build(r); sheets[r['exchange']].append(o)
    for f, why in gaps:
        gap_detail.append((r['exchange'], r['symbol'], r['name'], r['security_type'], f, why)); gap_summary[(r['exchange'], f, why)] += 1
sheet_rows = {}
for ex, data in sheets.items():
    ws = wb.create_sheet(ex); ws.append(COLS)
    for cell in ws[1]: cell.font = BOLD; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical='top')
    data.sort(key=lambda o: o['Legal name'].lower())
    for o in data: ws.append([o[c] for c in COLS])
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{len(data) + 1}"
    for i, c in enumerate(COLS, 1):
        w = 14
        if c in ('Legal name', 'Transfer agent', 'Auditor', 'Incorporation jurisdiction', 'Newswire of habit', 'Sector'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower(): w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    sheet_rows[ex] = len(data)
# Coverage tab with live COUNTA formulas
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in sheets] + [f'{ex} fill %' for ex in sheets] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
cv.append(['Issuers (rows)', 'A'] + [f"=COUNTA('{ex}'!A2:A{sheet_rows[ex] + 1})" for ex in sheets] + ['', '', '', ''] + [f"=SUM(C2:F2)", ''])
FIELDS = ['Legal name', 'Ticker', 'Exchange', 'Listing tier', 'Security type', 'ISIN', 'LEI', 'Sector', 'Incorporation jurisdiction', 'SEDAR+ profile link', SEDI_COL, 'Transfer agent', 'Auditor', 'Newswire of habit', 'HQ city', 'HQ province/state', 'HQ country/region', 'Listing date']
rix = 3
for f in FIELDS:
    col = get_column_letter(COLS.index(f) + 1)
    line = [f, col]
    for ex in sheets: line.append(f"=COUNTA('{ex}'!{col}2:{col}{sheet_rows[ex] + 1})")
    for j, ex in enumerate(sheets): line.append(f"=IF({get_column_letter(3 + j)}$2=0,0,{get_column_letter(3 + j)}{rix}/{get_column_letter(3 + j)}$2)")
    line.append(f"=SUM(C{rix}:F{rix})"); line.append(f"=IF(K$2=0,0,K{rix}/K$2)")
    cv.append(line); rix += 1
for row in cv.iter_rows(min_row=2):
    for cell in row:
        cell.font = ARIAL
        if cell.column >= 7 and cell.column != 11: cell.number_format = '0.0%'
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the exchange tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Sweep date ' + TODAY + '.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
for i, w in enumerate([26, 8, 12, 12, 12, 14, 12, 12, 12, 14, 12, 12], 1): cv.column_dimensions[get_column_letter(i)].width = w
# Gaps tabs
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([14, 26, 90, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Ticker', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
for i, w in enumerate([14, 12, 40, 18, 26, 90], 1): gd.column_dimensions[get_column_letter(i)].width = w
# Method tab
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
METHOD = [
 ('Order', 'ORDER-001 Canada Width 0 sweep, node ca-cm-kg, swept ' + TODAY),
 ('Rosters', 'TSX and TSXV: tsx.com company directory JSON (live, ' + TODAY + '). CSE: thecse.com listed-companies API (live, Delisted rows excluded). Cboe Canada: cboe.com listing-directory API (live, all 399 securities).'),
 ('Exchange enrichment', 'TSX/TSXV sector, sub-sector, HQ province/region, listing date/type from the TMX listed-companies workbook (published 2026-08-14, data as of 31-Jul-2026; issuers listed after that date carry no sector). CSE transfer agent, auditor, HQ address, website from thecse.com company page data. Cboe feed carries symbol, name, security type only; no market data was carried into this workbook.'),
 ('LEI', 'GLEIF fuzzy-completion search on the legal name; accepted only when the GLEIF legal name equals the roster name after normalisation (case, punctuation, legal-form abbreviations). Jurisdiction and HQ city come from the matched LEI record.'),
 ('ISIN', 'Tavily search restricted to quote/profile domains (marketscreener, investing.com, stockanalysis, tradingview, morningstar, ceo.ca, exchanges), full page text; ISIN accepted only when the page mentions the issuer name and ticker, the check digit validates, and support is unambiguous. Conflicts and weak single mentions are left blank and flagged.'),
 ('Transfer agent / auditor / jurisdiction (TSX, TSXV, Cboe)', 'Tavily search "<name> transfer agent auditor", full page text; transfer agent taken only from a closed list of agent names within 300 characters of the words "transfer agent"; auditor only from explicit phrases (auditor(s) is/are X LLP; X LLP, Chartered Professional Accountants; appointed X LLP as auditor); jurisdiction only from statute phrases (Business Corporations Act (Province), Canada Business Corporations Act, ...). Majority across pages; ties left blank and flagged as conflict. Evidence snippet and source URL kept per cell.'),
 ('Newswire of habit', 'Tavily search restricted to newswire.ca, prnewswire.com, newsfilecorp.com, globenewswire.com, businesswire.com, accesswire.com, thenewswire.com; release hits whose title/summary carries the issuer name; up to three releases kept; wire recorded only when it is the majority of the releases seen. Mixed = blank + flagged.'),
 ('SEDAR+', 'CSE: link constructed from the SEDAR issuer number in the CSE feed using the observed sedarplus.ca/csa-party/<number>.html pattern. Others: Tavily search of sedarplus.ca accepted only when the profile page heading equals the issuer name. sedarplus.ca answers HTTP 403 to automated clients, so links are not verified by fetch.'),
 ('SEDI', 'sedi.ca answers HTTP 403 to automated clients (curl and headless browser) and publishes no per-issuer URL; column left blank for every row and counted in Gaps.'),
 ('Blank is blank', 'No transfer agent, auditor, or newswire was inferred. Every enriched cell carries a source URL and a read-by column. Fund and receipt securities (ETFs, CDRs, closed-end funds, warrants, debt) were searched for ISIN only in Width 0.'),
 ('Not searched by design', 'Prices, quotes, market cap, volume, index membership.'),
]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 140
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
# console report
print('saved', OUT)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:28s} {n:5d} {n / len(data) * 100:5.1f}%')
print('gap rows', len(gap_detail))
