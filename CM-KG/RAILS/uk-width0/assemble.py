"""Step 10 — the workbook: Coverage (live COUNTA), Gaps, LSE Main Market, AIM, Aquis Stock Exchange, Gaps detail, Method.
Every enriched cell carries a source URL, a read-by label and a State (sourced = one source read; blank = nothing read). Nothing is inferred."""
import json, os, re, sys, datetime
from collections import Counter, defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\ALLOOLOO\CM-KG\ISSUERS\uk-issuers.xlsx'
TODAY = datetime.date.today().isoformat()
rows = json.load(open('raw/roster.json', encoding='utf-8'))
def key(r): return r['exchange'] + '|' + r['symbol']
def load(fn, k='key'):
    d = {}
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try:
                x = json.loads(line); d[x[k]] = x
            except Exception: pass
    return d
E_REG = load('raw/enr_reg.jsonl'); E_WIRE = load('raw/enr_wire.jsonl'); E_CH = load('raw/ch_match.jsonl'); E_CHAPI = load('raw/ch_api.jsonl')
API_JUR = {'england-wales': 'England and Wales', 'scotland': 'Scotland', 'northern-ireland': 'Northern Ireland', 'wales': 'Wales', 'united-kingdom': 'United Kingdom', 'england': 'England', 'noneu': 'Overseas (non-EU)', 'eu': 'Overseas (EU)', 'isle-of-man': 'Isle of Man', 'guernsey': 'Guernsey', 'jersey': 'Jersey', 'european-union': 'European Union'}
E_LEIREC = load('raw/lei_records.jsonl'); E_MATCH = load('raw/lei_match.jsonl', 'name')
ISIN_LEI = json.load(open('raw/isin_lei_hits.json')) if os.path.exists('raw/isin_lei_hits.json') else {}
ISIN_LEI_SRC = 'https://mapping.gleif.org/api/v2/isin-lei/latest (' + (open('raw/isin-lei-latest.txt').read().strip() if os.path.exists('raw/isin-lei-latest.txt') else 'daily file') + ')'
CH_META = json.load(open('raw/ch_index_meta.json')) if os.path.exists('raw/ch_index_meta.json') else {}
CH_BULK_SRC = 'https://download.companieshouse.gov.uk/en_output.html (' + CH_META.get('file', 'BasicCompanyDataAsOneFile') + ')'
def is_corp(r): return r['security_type'] in ('Corporate', 'Closed-ended investment company')

RB = {'lse_expl': 'LSE price explorer (exchange list)', 'lse_inst': 'LSE instrument reference record (exchange site)', 'lse_prof': 'LSE issuer profile (exchange site)',
      'aq': 'aquis.eu company page data (exchange site; read in a browser session)', 'gleif_map': 'GLEIF ISIN-to-LEI mapping file (exact ISIN match)', 'gleif_exact': 'GLEIF name-exact',
      'gleif_rec': 'GLEIF LEI record (LEI per the LEI column)', 'ch_bulk': 'Companies House bulk data product (BasicCompanyDataAsOneFile, monthly)', 'ch_page': 'Companies House public profile page',
      'tavily': 'Tavily search + regex extraction from page text', 'tavily_wire': 'Tavily search restricted to wire domains and LSE news-article pages (release hits)'}
KNOWN_AUD = [('Deloitte Ireland LLP', r'Deloitte Ireland'), ('KPMG (Ireland)', r'KPMG.{0,12}Ireland'), ('PricewaterhouseCoopers (Ireland)', r'PricewaterhouseCoopers.{0,12}Ireland|PwC Ireland'), ('Ernst & Young (Ireland)', r'Ernst\s*&\s*Young.{0,12}Ireland'), ('Grant Thornton (Ireland)', r'Grant Thornton.{0,12}Ireland'), ('BDO (Ireland)', r'BDO.{0,12}Ireland'), ('Mazars (Ireland)', r'Mazars.{0,12}Ireland'),
             ('KPMG Huazhen LLP', r'KPMG Huazhen'), ('KPMG LLP', r'\bKPMG\b'), ('Deloitte LLP', r'\bDeloitte\b'), ('PricewaterhouseCoopers LLP', r'PricewaterhouseCoopers|\bPwC\b'), ('Ernst & Young LLP', r'Ernst\s*&\s*Young|\bEY\b|^&\s*Young\b'),
             ('HaysMac LLP', r'\bHaysMac\b'), ('RPG Crouch Chapman LLP', r'Crouch Chapman'), ('Crowe (Ireland)', r'Crowe.{0,12}Ireland'), ('Jeffreys Henry Audit', r'Jeffreys Henry'), ('PKF Francis Clark', r'Francis Clark'), ('PKF Smith Cooper', r'Smith Cooper'), ('Mercer & Hole', r'Mercer\s*&\s*Hole'), ('Rees Pollock', r'Rees Pollock'), ('Streets', r'Streets Audit'), ('Dains', r'\bDains\b'), ('CLA Evelyn Partners', r'CLA Evelyn'), ('James Cowper Kreston', r'James Cowper'), ('Thomas Westcott', r'Thomas Westcott'), ('Grunberg', r'Grunberg'), ('Barnes Roffe', r'Barnes Roffe'), ('Hillier Hopkins', r'Hillier Hopkins'), ('Lubbock Fine', r'Lubbock Fine'), ('SRLV', r'\bSRLV\b'), ('Sopher', r'Sopher \+ Co|Sopher'), ('Alliotts', r'Alliotts'), ('Kirk Rice', r'Kirk Rice'), ('Edwards Veeder', r'Edwards Veeder'),
             ('BDO LLP', r'\bBDO\b'), ('Grant Thornton UK LLP', r'Grant Thornton'), ('RSM UK Audit LLP', r'\bRSM\b'), ('Forvis Mazars LLP', r'Mazars'), ('Crowe U.K. LLP', r'\bCrowe\b'), ('PKF Littlejohn LLP', r'PKF Littlejohn|\bPKF\b'),
             ('Moore Kingston Smith LLP', r'Kingston Smith'), ('Haysmacintyre LLP', r'(?i)haysmacintyre'), ('Saffery LLP', r'Saffery'), ('Johnston Carmichael LLP', r'Johnston Carmichael'), ('MHA', r'\bMHA\b|MacIntyre Hudson'),
             ('Jeffreys Henry LLP', r'Jeffreys Henry'), ('UHY Hacker Young LLP', r'\bUHY\b|Hacker Young'), ('Cooper Parry Group Limited', r'Cooper Parry'), ('Azets Audit Services', r'\bAzets\b'), ('Price Bailey LLP', r'Price Bailey'),
             ('Buzzacott LLP', r'Buzzacott'), ('Gravita', r'\bGravita\b'), ('Evelyn Partners LLP', r'Evelyn Partners|Nexia Smith|Smith\s*&\s*Williamson'), ('HW Fisher LLP', r'HW Fisher|H\.W\. Fisher'), ('Kreston Reeves LLP', r'Kreston Reeves'),
             ('Menzies LLP', r'\bMenzies\b'), ('Bishop Fleming LLP', r'Bishop Fleming'), ('Larking Gowen LLP', r'Larking Gowen'), ('Duncan & Toplis', r'Duncan\s*&\s*Toplis'), ('Hazlewoods LLP', r'Hazlewoods'), ('Beever and Struthers', r'Beever'),
             ('Shipleys LLP', r'Shipleys'), ('Sumer Audit', r'\bSumer\b'), ('Xeinadin Audit Limited', r'Xeinadin'), ('Adler Shine LLP', r'Adler Shine'), ('Blick Rothenberg', r'Blick Rothenberg'), ('Wilson Wright LLP', r'Wilson Wright'),
             ('Ecovis Wingrave Yeats', r'Wingrave Yeats|\bEcovis\b'), ('DSW Audit', r'\bDSW\b'), ('Welbeck Associates', r'Welbeck'), ('Begbies Traynor', r'Begbies'), ('Gerald Edelman LLP', r'Gerald Edelman'), ('Frazer Hall', r'Frazer Hall'),
             ('Moore', r'\bMoore\b'), ('Nexia', r'\bNexia\b'), ('Baker Tilly', r'Baker Tilly'), ('Marcum LLP', r'\bMarcum\b'), ('MaloneBailey LLP', r'Malone\s?Bailey'), ('Davidson & Company LLP', r'Davidson\s*&\s*Company'), ('MNP LLP', r'\bMNP\b'),
             ('Mazars', r'\bMazars\b'), ('Rödl & Partner', r'R[oö]dl'), ('Pitcher Partners', r'Pitcher Partners'), ('Hall Chadwick', r'Hall Chadwick'), ('Stantons', r'Stantons'), ('Nexia Perth', r'Nexia Perth'), ('Elderton Audit', r'Elderton'), ('HLB Mann Judd', r'HLB Mann Judd')]
def canon_aud(name):
    for canon, pat in KNOWN_AUD:
        if re.search(pat, name): return canon
    return name
KNOWN_SET = set(c for c, _ in KNOWN_AUD)
def repick_aud(c):
    cands = c.get('aud_cands') or {}
    if not cands: return c.get('aud', ''), c.get('aud_gap', 'none found')
    merged = Counter()
    for k, v in cands.items():
        if re.match(r'(?i)^(?:audit|auditor|auditors|statutory|registered|independent|the)\b', k) or len(k.split()) < 2: continue  # regex noise such as "Audit LLP"
        merged[canon_aud(k)] += v
    if not merged: return '', 'only noise strings read: ' + '; '.join(list(cands)[:3])
    (b, s) = merged.most_common(1)[0]
    if len(merged) > 1 and merged.most_common(2)[1][1] == s:
        return '', 'conflict: ' + '; '.join(f'{k}({v})' for k, v in merged.most_common(3))
    return b, ''
def name_key(s):
    s = s.lower().replace('&', ' and ')
    return ' '.join(re.sub(r"[^a-z0-9 ]", ' ', s).split())
LEGAL_FORM = re.compile(r'\b(?:plc|p l c|public limited company|ltd|limited|inc|incorporated|corp|corporation|sa|s a|nv|n v|ag|se|lp|l p|co|company|holdings?)\b')
def entity_key(s): return ' '.join(LEGAL_FORM.sub(' ', name_key(s)).split())
JUR = {'GB': 'United Kingdom', 'GB-ENG': 'England and Wales', 'GB-WLS': 'England and Wales', 'GB-SCT': 'Scotland', 'GB-NIR': 'Northern Ireland', 'JE': 'Jersey', 'GG': 'Guernsey', 'IM': 'Isle of Man', 'IE': 'Ireland', 'BM': 'Bermuda', 'KY': 'Cayman Islands', 'VG': 'British Virgin Islands', 'GI': 'Gibraltar', 'CY': 'Cyprus', 'LU': 'Luxembourg', 'NL': 'Netherlands', 'US': 'United States', 'US-DE': 'Delaware, United States', 'AU': 'Australia', 'CA': 'Canada', 'ZA': 'South Africa', 'IL': 'Israel', 'SG': 'Singapore', 'HK': 'Hong Kong', 'CH': 'Switzerland', 'DE': 'Germany', 'FR': 'France', 'ES': 'Spain', 'IT': 'Italy', 'SE': 'Sweden', 'DK': 'Denmark', 'NO': 'Norway', 'FI': 'Finland', 'BE': 'Belgium', 'MT': 'Malta', 'MU': 'Mauritius', 'IN': 'India', 'CN': 'China', 'JP': 'Japan', 'KR': 'South Korea', 'EG': 'Egypt', 'KZ': 'Kazakhstan', 'RU': 'Russia', 'AE': 'United Arab Emirates', 'GR': 'Greece', 'PL': 'Poland', 'NZ': 'New Zealand', 'MY': 'Malaysia', 'TH': 'Thailand', 'ID': 'Indonesia', 'BR': 'Brazil', 'MX': 'Mexico', 'AR': 'Argentina', 'CL': 'Chile', 'PT': 'Portugal', 'AT': 'Austria', 'CZ': 'Czech Republic', 'RO': 'Romania', 'NG': 'Nigeria', 'KE': 'Kenya', 'GH': 'Ghana', 'BW': 'Botswana', 'TR': 'Türkiye', 'UA': 'Ukraine', 'GE': 'Georgia'}
def ch_jurisdiction(num, origin):
    if not num: return ''
    p = num[:2].upper()
    if p == 'SC': return 'Scotland (Companies House SC prefix)'
    if p == 'NI': return 'Northern Ireland (Companies House NI prefix)'
    if p == 'FC': return f'Overseas company registered at Companies House (FC prefix{", origin " + origin if origin else ""})'
    if p in ('OE',): return 'Overseas entity (Companies House OE register)'
    if p == 'RC': return 'Royal Charter company (Companies House RC prefix)'
    if p.isdigit() or p in ('OC', 'SO', 'NC', 'LP', 'SL'): return 'England and Wales (Companies House number without country prefix)' + (f'; country of origin {origin}' if origin and origin != 'United Kingdom' else '')
    return f'Companies House number prefix {p}' + (f'; country of origin {origin}' if origin else '')

COLS = ['Legal name', 'Ticker (TIDM)', 'Other instruments', 'Exchange', 'Market segment', 'Listing category', 'Security type',
        'ISIN', 'ISIN source', 'ISIN read by', 'ISIN State', 'SEDOL', 'SEDOL source', 'SEDOL read by', 'SEDOL State',
        'LEI', 'LEI source', 'LEI read by', 'LEI State', 'LEI registration status',
        'Companies House number', 'Companies House profile link', 'Companies House source', 'Companies House read by', 'Companies House State',
        'Registered office', 'Registered office source', 'Registered office read by', 'Registered office State',
        'Incorporation jurisdiction', 'Jurisdiction source', 'Jurisdiction read by', 'Jurisdiction State',
        'SIC code(s)', 'SIC source', 'SIC read by', 'SIC State',
        'Sector (FTSE ICB)', 'Sub-sector', 'Sector source', 'Sector read by', 'Sector State',
        'Auditor', 'Auditor source', 'Auditor read by', 'Auditor State', 'Auditor evidence', 'Accounts filing (Companies House)',
        'Registrar', 'Registrar source', 'Registrar read by', 'Registrar State', 'Registrar evidence',
        'Newswire of habit', 'Newswire releases seen', 'Newswire read by', 'Newswire State',
        'FCA NSM link (unverified — search entry)', 'NSM read by',
        'HQ city', 'HQ country', 'HQ source', 'HQ read by', 'HQ State',
        'Website', 'Website source', 'Website read by',
        'Admission date', 'Admission date source', 'Currency', 'Status', 'Roster source', 'Roster read by', 'Gaps']
NSM_COL = 'FCA NSM link (unverified — search entry)'
STATE_FIELDS = ['ISIN', 'SEDOL', 'LEI', 'Companies House', 'Registered office', 'Jurisdiction', 'SIC', 'Sector', 'Auditor', 'Registrar', 'Newswire', 'HQ']

def build(r):
    k = key(r); ex = r['exchange']; corp = is_corp(r); gaps = []; aq = ex == 'Aquis Stock Exchange'
    o = {c: '' for c in COLS}
    o['Legal name'] = r['name']; o['Ticker (TIDM)'] = r['symbol']; o['Other instruments'] = r['instruments']; o['Exchange'] = ex
    o['Market segment'] = r['segment'] + ((' (' + r['listing_category'] + ')') if aq and r['listing_category'] else '')
    o['Listing category'] = r['listing_category'] if not aq else r['listing_category']
    if not aq and not r['listing_category']: gaps.append(('Listing category', 'LSE issuer profile carries no listing category for this issuer'))
    o['Security type'] = r['security_type']; o['Currency'] = r['currency']; o['Status'] = r['status']
    o['Roster source'] = r['roster_src']; o['Roster read by'] = RB['aq'] if aq else RB['lse_expl']
    if r['admission_date']: o['Admission date'] = r['admission_date']; o['Admission date source'] = (r['profile_src'] if aq else (r['alldata_src'] or r['profile_src']))
    else: gaps.append(('Admission date', 'not on the exchange record'))
    if r['website']: o['Website'] = r['website']; o['Website source'] = r['profile_src']; o['Website read by'] = RB['aq'] if aq else RB['lse_prof']
    # ISIN / SEDOL: exchange data
    if r['isin']: o['ISIN'] = r['isin']; o['ISIN source'] = r['profile_src'] if aq else (r['alldata_src'] or r['roster_src']); o['ISIN read by'] = RB['aq'] if aq else RB['lse_inst']; o['ISIN State'] = 'sourced'
    else: gaps.append(('ISIN', 'exchange record carries no ISIN'))
    if r['sedol']: o['SEDOL'] = r['sedol']; o['SEDOL source'] = r['alldata_src']; o['SEDOL read by'] = RB['lse_inst']; o['SEDOL State'] = 'sourced'
    else: gaps.append(('SEDOL', 'Aquis page data carries no SEDOL' if aq else ('LSE instrument record carries no SEDOL' if not r['alldata_err'] else f"LSE instrument record not read (HTTP {r['alldata_err']})")))
    # LEI
    lei = ''; m = E_MATCH.get(r['name'])
    exact = [(l, v) for l, v in (m or {}).get('matches', []) if name_key(v) == name_key(r['name'])]
    if r['isin'] and ISIN_LEI.get(r['isin']):
        lei = ISIN_LEI[r['isin']].split('|')[0]; o['LEI'] = lei; o['LEI source'] = ISIN_LEI_SRC; o['LEI read by'] = RB['gleif_map']; o['LEI State'] = 'sourced'
        mrec = E_LEIREC.get(lei)
        if mrec and entity_key(mrec['name']) != entity_key(r['name']):
            o['LEI State'] = 'conflict'; gaps.append(('LEI', f"mapping file maps ISIN {r['isin']} to LEI {lei}, whose GLEIF legal name is \"{mrec['name']}\", not the issuer; LEI kept with State conflict, not used as a route to Companies House"))
    elif exact:
        lei = exact[0][0]; o['LEI'] = lei; o['LEI source'] = f'https://api.gleif.org/api/v1/lei-records/{lei}'; o['LEI read by'] = RB['gleif_exact']; o['LEI State'] = 'sourced'
        if len(exact) > 1: o['LEI registration status'] = f'(note: {len(exact)} LEIs carry this exact legal name; first taken) '
    else:
        why = ('ISIN not in the GLEIF ISIN-to-LEI mapping file; ' if r['isin'] else 'no ISIN; ')
        if m and m.get('matches'): why += 'GLEIF name match is fuzzy only, left blank: ' + '; '.join(f'{v} ({l})' for l, v in m['matches'][:2])
        elif m: why += 'no GLEIF legal name equals the roster name'
        else: why += 'GLEIF name lookup not run'
        gaps.append(('LEI', why))
    rec = E_LEIREC.get(lei, {}) if lei else {}
    if lei: o['LEI registration status'] += rec.get('reg_status', '') if rec else 'record not read'
    # Companies House
    ch = E_CH.get(k) or {}; num = ch.get('number', ''); prof = ch.get('profile'); page = ch.get('page')
    api = E_CHAPI.get(k)
    if api and api.get('number') and api.get('profile'):  # REST API pass (key present): number, profile, latest accounts filing take precedence
        num = api['number']; ap = api['profile']
        o['Companies House number'] = num; o['Companies House profile link'] = f'https://find-and-update.company-information.service.gov.uk/company/{num}'
        o['Companies House source'] = api.get('route_src') or ch.get('route_src', ''); o['Companies House read by'] = {'lei': 'GLEIF LEI record registeredAs (Companies House number on the LEI record)', 'name-exact': 'Companies House bulk data product, name-exact', 'api-search name-exact': 'Companies House REST API company search, name-exact (public company whose name equals the roster name)'}.get(api.get('route'), api.get('route', '')); o['Companies House State'] = 'sourced' + (f" (Companies House status: {ap['status']})" if ap.get('status') and ap['status'] != 'active' else '')
        if ap.get('office'): o['Registered office'] = ap['office']; o['Registered office source'] = api['profile_src']; o['Registered office read by'] = api['profile_rb']; o['Registered office State'] = 'sourced'
        else: gaps.append(('Registered office', 'Companies House API profile carries no registered office'))
        jl = API_JUR.get(ap.get('jurisdiction') or '', ap.get('jurisdiction') or '')
        o['Incorporation jurisdiction'] = (jl + ' (Companies House jurisdiction field)') if jl else ch_jurisdiction(num, ''); o['Jurisdiction source'] = api['profile_src']; o['Jurisdiction read by'] = api['profile_rb'] + (' (jurisdiction field)' if jl else ' (company number prefix)'); o['Jurisdiction State'] = 'sourced'
        if ap.get('sic'): o['SIC code(s)'] = '; '.join(ap['sic']); o['SIC source'] = api['profile_src']; o['SIC read by'] = api['profile_rb']; o['SIC State'] = 'sourced'
        else: gaps.append(('SIC code(s)', 'Companies House API profile lists no SIC code'))
        af = api.get('accounts_filing') or {}
        o['Accounts filing (Companies House)'] = af.get('url') or f'https://find-and-update.company-information.service.gov.uk/company/{num}/filing-history?category=accounts'
        if af.get('date'): o['Accounts filing (Companies House)'] += f"  [{af['date']} {af.get('description') or ''}]".rstrip()
    elif num:
        o['Companies House number'] = num; o['Companies House profile link'] = f'https://find-and-update.company-information.service.gov.uk/company/{num}'
        o['Companies House source'] = ch.get('route_src', ''); o['Companies House read by'] = ('GLEIF LEI record registeredAs (Companies House number on the LEI record)' if ch.get('route') == 'lei' else 'Companies House bulk data product, name-exact (current or previous company name equals the roster name)'); o['Companies House State'] = 'sourced'
        o['Accounts filing (Companies House)'] = f'https://find-and-update.company-information.service.gov.uk/company/{num}/filing-history?category=accounts'
        if prof:
            off = prof['office']; office = ', '.join(v for v in [off.get('care_of'), off.get('line1'), off.get('line2'), off.get('town'), off.get('county'), off.get('country'), off.get('postcode')] if v)
            o['Registered office'] = office; o['Registered office source'] = ch['profile_src']; o['Registered office read by'] = RB['ch_bulk']; o['Registered office State'] = 'sourced' if office else ''
            if not office: gaps.append(('Registered office', 'Companies House bulk row carries no address'))
            o['Incorporation jurisdiction'] = ch_jurisdiction(num, prof.get('origin', '')); o['Jurisdiction source'] = ch['profile_src']; o['Jurisdiction read by'] = RB['ch_bulk'] + ' (company number prefix + country of origin)'; o['Jurisdiction State'] = 'sourced'
            if prof.get('sic'): o['SIC code(s)'] = '; '.join(prof['sic']); o['SIC source'] = ch['profile_src']; o['SIC read by'] = RB['ch_bulk']; o['SIC State'] = 'sourced'
            else: gaps.append(('SIC code(s)', 'Companies House bulk row carries no SIC code'))
            if prof.get('status') and prof['status'] != 'Active': o['Companies House State'] += f" (Companies House status: {prof['status']})"
        elif page and page.get('status') == 200:
            if page.get('office'): o['Registered office'] = page['office']; o['Registered office source'] = page['url']; o['Registered office read by'] = RB['ch_page']; o['Registered office State'] = 'sourced'
            else: gaps.append(('Registered office', 'Companies House profile page carries no registered office'))
            o['Incorporation jurisdiction'] = ch_jurisdiction(num, ''); o['Jurisdiction source'] = page['url']; o['Jurisdiction read by'] = RB['ch_page'] + ' (company number prefix)'; o['Jurisdiction State'] = 'sourced'
            if page.get('sic'): o['SIC code(s)'] = '; '.join(page['sic']); o['SIC source'] = page['url']; o['SIC read by'] = RB['ch_page']; o['SIC State'] = 'sourced'
            else: gaps.append(('SIC code(s)', 'Companies House profile page lists no SIC code'))
            if page.get('type'): o['Companies House State'] += f" (page type: {page['type']})"
        else:
            gaps.append(('Registered office', f"Companies House number {num} not in the PLC index and profile page answered HTTP {page.get('status') if page else 'n/a'}"))
    else:
        gaps.append(('Companies House number', ((api.get('gap') + '; ') if api and api.get('gap') else '') + (ch.get('gap', 'not matched') if ch else 'Companies House match not run')))
        if rec.get('jur'):
            o['Incorporation jurisdiction'] = JUR.get(rec['jur'], rec['jur']) + f" ({rec['jur']})"; o['Jurisdiction source'] = rec['src']; o['Jurisdiction read by'] = RB['gleif_rec']; o['Jurisdiction State'] = 'sourced'
        elif r.get('country_inc'):
            o['Incorporation jurisdiction'] = JUR.get(r['country_inc'], r['country_inc']) + f" ({r['country_inc']})"; o['Jurisdiction source'] = r['profile_src']; o['Jurisdiction read by'] = RB['lse_prof'] + ' (country of incorporation)'; o['Jurisdiction State'] = 'sourced'
        else: gaps.append(('Incorporation jurisdiction', 'no Companies House number, no LEI record, no country of incorporation on the exchange profile'))
        if rec.get('legal_city') or rec.get('legal_lines'):
            o['Registered office'] = ', '.join(v for v in ((rec.get('legal_lines') or []) + [rec.get('legal_city'), rec.get('legal_region'), rec.get('legal_postal'), rec.get('legal_country')]) if v); o['Registered office source'] = rec['src']; o['Registered office read by'] = RB['gleif_rec'] + ' (legal address)'; o['Registered office State'] = 'sourced'
        elif r.get('address') and aq:
            o['Registered office'] = r['address']; o['Registered office source'] = r['profile_src']; o['Registered office read by'] = RB['aq'] + ' (registered address)'; o['Registered office State'] = 'sourced'
        else: gaps.append(('Registered office', 'no Companies House row, no LEI record'))
        gaps.append(('SIC code(s)', 'no Companies House row (SIC is a Companies House field)'))
    if o['Incorporation jurisdiction'] and rec.get('jur') and num:
        gl = JUR.get(rec['jur'], rec['jur'])
        if rec['jur'][:2] != 'GB' and not num.upper().startswith(('FC', 'OE')): o['Jurisdiction State'] = 'conflict'; gaps.append(('Incorporation jurisdiction', f"Companies House number {num} but GLEIF legal jurisdiction {rec['jur']} ({gl})"))
    # sector
    if r['sector']:
        o['Sector (FTSE ICB)'] = r['sector'] + (f" [{r['sector_code']}]" if r['sector_code'] else ''); o['Sub-sector'] = r['subsector']; o['Sector source'] = r['sector_src']; o['Sector read by'] = r['sector_rb']; o['Sector State'] = 'sourced'
    else: gaps.append(('Sector (FTSE ICB)', 'no sector on the exchange record'))
    # auditor / registrar
    c = E_REG.get(k)
    aud_v, aud_g = repick_aud(c) if c else ('', '')
    if aud_v and aud_v in KNOWN_SET:
        o['Auditor'] = aud_v; o['Auditor read by'] = 'Tavily regex'; o['Auditor source'] = c.get('aud_src') or ''; o['Auditor evidence'] = c.get('aud_ev', ''); o['Auditor State'] = 'sourced'
    elif aud_v: gaps.append(('Auditor', f'string read but not a recognised audit-firm name, left blank: "{aud_v}"'))
    else: gaps.append(('Auditor', (aud_g or 'none found') if c else ('not searched (fund/receipt/debt security)' if not corp else 'not searched')))
    if aq and r.get('aq_registrar'):
        o['Registrar'] = r['aq_registrar']; o['Registrar source'] = r['profile_src']; o['Registrar read by'] = RB['aq']; o['Registrar State'] = 'sourced'
    elif c and c.get('reg'):
        o['Registrar'] = c['reg']; o['Registrar source'] = c['reg_src']; o['Registrar read by'] = RB['tavily']; o['Registrar evidence'] = c['reg_ev']; o['Registrar State'] = 'sourced'
    else: gaps.append(('Registrar', (c.get('reg_gap') or 'none found') if c else ('not searched (fund/receipt/debt security)' if not corp else ('Aquis page carries no registrar' if aq else 'not searched'))))
    # newswire
    w = E_WIRE.get(k)
    if w and w.get('wire'):
        o['Newswire of habit'] = w['wire'] + (f" ({w['note']})" if w.get('note') else ''); o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits']); o['Newswire read by'] = RB['tavily_wire']; o['Newswire State'] = 'sourced'
    else:
        if w and w.get('hits'): o['Newswire releases seen'] = '\n'.join(h['url'] for h in w['hits'])
        gaps.append(('Newswire of habit', (w.get('gap') or 'search error') if w else ('not searched (fund/receipt/debt security)' if not corp else 'not searched')))
    # NSM: constructed, unverified
    o[NSM_COL] = 'https://data.fca.org.uk/#/nsm/nationalstoragemechanism' + (f'  [search by LEI {lei}]' if lei else '  [search by name]')
    o['NSM read by'] = 'constructed (NSM search entry; the NSM publishes no per-issuer URL, its search sits behind a terms-of-use gate and api.data.fca.org.uk answers HTTP 403) — UNVERIFIED'
    gaps.append(('FCA NSM link', 'unverified: search entry only' + ('' if lei else ', no LEI to search by')))
    # HQ
    if rec.get('hq_city'):
        o['HQ city'] = rec['hq_city']; o['HQ country'] = JUR.get(rec.get('hq_country') or '', rec.get('hq_country') or ''); o['HQ source'] = rec['src']; o['HQ read by'] = RB['gleif_rec'] + ' (headquarters address)'; o['HQ State'] = 'sourced'
    elif r.get('address'):
        parts = [p.strip() for p in r['address'].split(',')]
        o['HQ city'] = (r.get('aq_reg_town') if aq else (parts[-3] if len(parts) >= 3 else (parts[0] if parts else ''))) or ''; o['HQ country'] = (r.get('aq_reg_country') if aq else (parts[-1] if parts else '')) or ''
        o['HQ source'] = r['profile_src']; o['HQ read by'] = (RB['aq'] + ' (registered address)') if aq else (RB['lse_prof'] + ' (issuer address; city taken as the element before the postcode)'); o['HQ State'] = 'sourced' if o['HQ city'] else ''
        if not o['HQ city']: gaps.append(('HQ city', 'exchange address has no city element'))
    else: gaps.append(('HQ city', 'no LEI record and no address on the exchange profile'))
    o['Gaps'] = '; '.join(f'{f}: {why}' for f, why in gaps)
    return o, gaps

CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')  # page-text snippets can carry control characters openpyxl refuses
wb = Workbook(); wb.remove(wb.active)
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE')
SHEETS = ['LSE Main Market', 'AIM', 'Aquis Stock Exchange']
sheets = {s: [] for s in SHEETS}
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
    for o in data: ws.append([CTRL.sub('', o[c]) if isinstance(o[c], str) else o[c] for c in COLS])
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{len(data) + 1}"
    for i, c in enumerate(COLS, 1):
        w = 14
        if c in ('Legal name', 'Registrar', 'Auditor', 'Incorporation jurisdiction', 'Newswire of habit', 'Sector (FTSE ICB)', 'Registered office', 'SIC code(s)', 'Listing category'): w = 34
        if 'source' in c.lower() or 'link' in c.lower() or 'releases' in c.lower() or 'filing' in c.lower(): w = 44
        if 'read by' in c.lower(): w = 30
        if 'evidence' in c.lower() or c == 'Gaps': w = 60
        if c.endswith('State'): w = 10
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    sheet_rows[ex] = len(data)
cv = wb.create_sheet('Coverage', 0)
cv.append(['Field', 'Column'] + [f'{ex} filled' for ex in SHEETS] + [f'{ex} fill %' for ex in SHEETS] + ['All filled', 'All fill %'])
for cell in cv[1]: cell.font = BOLD; cell.fill = HFILL
cv.append(['Issuers (rows)', 'A'] + [f"=COUNTA('{ex}'!A2:A{sheet_rows[ex] + 1})" for ex in SHEETS] + ['', '', ''] + ["=SUM(C2:E2)", ''])
FIELDS = ['Legal name', 'Ticker (TIDM)', 'Market segment', 'Listing category', 'Security type', 'ISIN', 'SEDOL', 'LEI', 'Companies House number', 'Registered office', 'Incorporation jurisdiction', 'SIC code(s)', 'Sector (FTSE ICB)', 'Auditor', 'Accounts filing (Companies House)', 'Registrar', 'Newswire of habit', NSM_COL, 'HQ city', 'Website', 'Admission date']
rix = 3
for f in FIELDS:
    col = get_column_letter(COLS.index(f) + 1); line = [f, col]
    for ex in SHEETS: line.append(f"=COUNTA('{ex}'!{col}2:{col}{sheet_rows[ex] + 1})")
    for j, ex in enumerate(SHEETS): line.append(f"=IF({get_column_letter(3 + j)}$2=0,0,{get_column_letter(3 + j)}{rix}/{get_column_letter(3 + j)}$2)")
    line.append(f"=SUM(C{rix}:E{rix})"); line.append(f"=IF(I$2=0,0,I{rix}/I$2)")
    cv.append(line); rix += 1
for row in cv.iter_rows(min_row=2):
    for cell in row:
        cell.font = ARIAL
        if cell.column in (6, 7, 8, 10): cell.number_format = '0.0%'
cv.append([]); cv.append(['Note', 'Counts are live COUNTA formulas over the exchange tabs. A cell counts as filled only when a source was read; blanks are blanks (nothing inferred). Every enriched field carries source, read-by and State. Sweep date ' + TODAY + '.'])
for cell in cv[cv.max_row]: cell.font = ARIAL
cv.freeze_panes = 'A2'
for i, w in enumerate([34, 8, 16, 12, 20, 16, 12, 20, 12, 12], 1): cv.column_dimensions[get_column_letter(i)].width = w
gs = wb.create_sheet('Gaps', 1); gs.append(['Exchange', 'Field', 'Reason', 'Row count'])
for cell in gs[1]: cell.font = BOLD; cell.fill = HFILL
for (ex, f, why), n in sorted(gap_summary.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])): gs.append([ex, f, why, n])
gs.append([]); gs.append(['TOTAL', '', '', f'=SUM(D2:D{len(gap_summary) + 1})'])
for row in gs.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gs.freeze_panes = 'A2'; gs.auto_filter.ref = f'A1:D{len(gap_summary) + 1}'
for i, w in enumerate([20, 28, 100, 12], 1): gs.column_dimensions[get_column_letter(i)].width = w
gd = wb.create_sheet('Gaps detail'); gd.append(['Exchange', 'Ticker', 'Legal name', 'Security type', 'Field', 'Reason'])
for cell in gd[1]: cell.font = BOLD; cell.fill = HFILL
for g in gap_detail: gd.append(list(g))
for row in gd.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL
gd.freeze_panes = 'A2'; gd.auto_filter.ref = f'A1:F{len(gap_detail) + 1}'
for i, w in enumerate([20, 12, 40, 26, 28, 100], 1): gd.column_dimensions[get_column_letter(i)].width = w
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for cell in mt[1]: cell.font = BOLD; cell.fill = HFILL
n_isin_lei = sum(1 for r in rows if r['isin'] and ISIN_LEI.get(r['isin'])); n_exact = sum(1 for r in rows if not (r['isin'] and ISIN_LEI.get(r['isin'])) and E_MATCH.get(r['name'], {}).get('matches'))
n_ch_lei = sum(1 for v in E_CH.values() if v.get('route') == 'lei' and v.get('number')); n_ch_name = sum(1 for v in E_CH.values() if v.get('route') == 'name-exact' and v.get('number')); n_ch_page = sum(1 for v in E_CH.values() if v.get('page'))
METHOD = [
 ('Order', 'ORDER-007 United Kingdom Width 0 sweep, node uk-cm-kg, swept ' + TODAY + '. Fly by wire; sourced or blank; no prices or market data carried.'),
 ('Rosters', f"LSE Main Market and AIM: the exchange's public price-explorer feed (api.londonstockexchange.com components/refresh, the JSON the public page renders), categories=EQUITY, showonlylse=true, live {TODAY}; one row per issuer code per market, other instruments listed. Aquis Stock Exchange: the exchange's own page data (aquis.eu/companies and /companies/<symbol> Next.js data), read in a browser session on {TODAY} because aquis.eu answers HTTP 429 (Vercel checkpoint) to plain HTTP clients; Apex / Access / Aram segment and AQSE Main Market from that data."),
 ('Exchange enrichment', 'LSE: per-instrument reference record (api/gw/lse/instruments/alldata/<TIDM>: ISIN, SEDOL, segment, MiFIR type, funds type, admission date, ICB codes) and the issuer profile (api/v1/pages?path=issuer-profile: address, country of incorporation, web address, ICB industry/supersector/sector/subsector names, listing category). Price, volume, market-cap and news fields in those feeds were dropped at write time. Aquis: ISIN, sector, registrar, registered address, website, corporate adviser, admission date from the company record.'),
 ('LEI', f"GLEIF ISIN-to-LEI mapping file, exact ISIN match ({n_isin_lei} rows); GB-prefixed ISINs are present in the file (663,203 GB rows on {TODAY}). Fallback GLEIF fuzzy-completion on the legal name accepted only when the GLEIF legal name equals the roster name after case/space/punctuation normalisation ('GLEIF name-exact', {n_exact} rows); looser matches stay in Gaps. Registration status, headquarters city and legal jurisdiction from the LEI record."),
 ('Companies House', f"This registry answers machines: the public profile pages (find-and-update.company-information.service.gov.uk/company/<number>) return HTTP 200 to plain HTTP clients and the free bulk data product (BasicCompanyDataAsOneFile, monthly) downloads without a login. No key file exists in AGENT KEYS (companieshouse.txt absent), so the REST API (HTTP 401 without a key) was not used — web pages and the bulk file only. Number: from the LEI record's registeredAs when registered at RA000585 = Companies House ({n_ch_lei} rows), else name-exact against current and previous company names of public companies in the bulk file ({n_ch_name} rows); ambiguity → Gaps. Registered office, incorporation jurisdiction (number prefix: none = England and Wales, SC = Scotland, NI = Northern Ireland, FC = overseas company; plus country of origin), SIC codes and accounts category from the bulk row, or from the profile page when the number is not a public-company row ({n_ch_page} page reads)."),
 ('Auditor', 'Tavily search "<name> registrar auditor annual report", full page text; auditor only from explicit phrases (auditor(s) is/are X LLP; X LLP, Statutory Auditor(s)/Chartered Accountants; appointed X LLP as auditor; independent auditor\'s report … by X LLP), canonicalised to a recognised audit-firm list; unrecognised strings and ties go to Gaps. The Companies House accounts filing history is linked per row as the accounts source (a source, not a read: the filings were not parsed).'),
 ('Registrar', 'Aquis: the registrar named on the exchange\'s company record. LSE: Tavily page text, registrar taken only from a closed list (Computershare, Equiniti, MUFG Corporate Markets / Link, Neville, Share Registrars, SLC, Avenir, JTC, Ocorian, Apex, Crestbridge, Sanne, Aztec, Estera, Ogier, Continental) within 300 characters of the word "registrar"; majority across pages; ties left blank and flagged.'),
 ('Newswire of habit', 'Tavily search "<name> announces" restricted to londonstockexchange.com (RNS news-article pages, accepted only when the TIDM in the URL path equals the row\'s), investegate.co.uk (RNS mirror), prnewswire.com, globenewswire.com, businesswire.com, accesswire.com; up to three releases; wire recorded only when it is the majority. Mixed = blank + flagged. The LSE news API itself answered HTTP 403 to this client after the roster pull and was not used per issuer.'),
 ('FCA National Storage Mechanism', 'data.fca.org.uk publishes no per-issuer URL; the NSM search UI sits behind a terms-of-use acceptance gate (not accepted by the machine) and api.data.fca.org.uk answers HTTP 403 to plain clients. The column holds the NSM search entry URL with the LEI to search by, labelled unverified, and every row carries a Gaps line.'),
 ('Sector', 'FTSE ICB sector and sub-sector from the LSE issuer profile (names and codes); where the profile carried none, the price-explorer sector filter sweep (45 ICB sectors) supplied the sector. Aquis sector from the company record (Aquis\'s own sector list, not ICB).'),
 ('State', 'sourced = one source read (URL in the source column); blank = nothing read. filled / confirmed / conflict are Fill and Confirm pass states (not run in Width 0), except jurisdiction conflict where the Companies House number and the GLEIF legal jurisdiction disagree.'),
 ('Blank is blank', 'No registrar, auditor, or newswire was inferred. Every enriched cell carries a source URL, a read-by label and a State. Fund, receipt and debt securities on the exchange lists were kept as rows with exchange data only.'),
 ('Not searched by design', 'Prices, quotes, market cap, volume, index membership beyond the LSE roundel, anything behind a login.'),
 ('Sources that answered machines', 'LSE api.londonstockexchange.com (JSON, no key; blocked with HTTP 403 after ~3,100 calls in one hour, cleared later) · Companies House bulk file and profile pages (HTTP 200) · GLEIF API and mapping file (HTTP 200) · Tavily (search API).'),
 ('Sources that refused machines', 'aquis.eu (HTTP 429 Vercel checkpoint; read in a browser) · Companies House REST API (HTTP 401, no key file) · FCA NSM api.data.fca.org.uk (HTTP 403) and NSM UI (terms gate) · LSE news list API (HTTP 403 after the roster pull).'),
]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for cell in row: cell.font = ARIAL; cell.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 34; mt.column_dimensions['B'].width = 150
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print('saved', OUT)
for ex, data in sheets.items():
    print(f'== {ex}: {len(data)} rows')
    for f in FIELDS:
        n = sum(1 for o in data if o[f]); print(f'   {f:36s} {n:5d} {n / max(1, len(data)) * 100:5.1f}%')
print('gap rows', len(gap_detail))
