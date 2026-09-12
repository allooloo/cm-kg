"""ORDER-018 — United States rail, run inside the East US container (the home address is blocked by EDGAR). Keyless EDGAR with the declared
User-Agent "Allooloo Technologies Corp. <CONTACT>"; under 8 requests a second.
  Width 0  company_tickers_exchange.json + submissions header per CIK (NYSE / Nasdaq / Cboe filers) -> roster; LEI by exact legal name against the
           GLEIF golden-copy US extract staged in the pond (registered-name route), ISIN from the GLEIF ISIN mapping zip; state of incorporation,
           SIC sector, business address, fiscal year end, latest annual report from the header
  Width 1  the 12-month filings list already in the submissions header: form -> event type (8-K items -> ad hoc / results; 10-K / 10-Q -> results;
           DEF 14A -> AGM; SC 13D/G -> major holder; 3/4/5 -> directors' dealings; S-1 / 424B -> prospectus; SC TO -> takeover; 25 / 15 -> delisting)
  Fill     auditor from the 10-K cover page iXBRL tag dei:AuditorName (regulator-tagged, sourced; AuditorLocation, AuditorFirmId beside it);
           transfer agent read by Gemini from a 10-K text window when a GEMINI key is present; Perplexity (agent, fast) company page + title alias
           when a PERPLEXITY key is present (PPLX_MAX); Grok live layer when an XAI key is present (LIVE_MAX_ISSUERS). Mistral none (order).
  Door     records / events / index / facts / nodes rendered in the door shape and uploaded to door/…; every raw file to pond/width0/<date>/…
Sourced or blank; no prices; nothing deleted."""
import os, re, io, json, time, zipfile, csv, datetime, threading, hashlib
from concurrent.futures import ThreadPoolExecutor
import requests
from azure.storage.blob import BlobServiceClient
TODAY = datetime.date.today(); SINCE = (TODAY - datetime.timedelta(days=366)).isoformat(); STAMP = TODAY.isoformat()
CONTACT = os.environ.get('CONTACT', 'allooloo@users.noreply.github.com'); UA = {'User-Agent': f'Allooloo Technologies Corp. {CONTACT}', 'Accept-Encoding': 'gzip, deflate'}
NODE = 'us-cm-kg'; REGION = os.environ.get('REGION', 'eastus'); HOST = 'https://mcp.us-cm-kg.ai'
bsc = BlobServiceClient(f"https://{os.environ['STORAGE_ACCOUNT']}.blob.core.windows.net", credential=os.environ['STORAGE_KEY']); cont = bsc.get_container_client(os.environ.get('STORAGE_CONTAINER', 'pond'))
W = '/job/work'; os.makedirs(W, exist_ok=True); LOG = []
def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOG.append(f'{time.strftime("%H:%M")} {s}')
def put(name, data, ct='application/json'):
    from azure.storage.blob import ContentSettings
    cont.upload_blob(name, data if isinstance(data, (bytes, bytearray)) else data.encode('utf-8'), overwrite=True, content_settings=ContentSettings(content_type=ct))
def get_blob(name):
    try: return cont.get_blob_client(name).download_blob().readall()
    except Exception as e: log('blob miss', name, e); return None
_gate = threading.Lock(); _last = [0.0]
def edgar(url, tries=4, **kw):
    for i in range(tries):
        with _gate:
            w = 0.13 - (time.time() - _last[0])
            if w > 0: time.sleep(w)
            _last[0] = time.time()
        try:
            r = requests.get(url, headers=UA, timeout=60, **kw)
            if r.status_code in (429, 403, 502, 503, 504): time.sleep(6 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
# ---------------- Width 0
def width0():
    r = edgar('https://www.sec.gov/files/company_tickers_exchange.json')
    if r is None or r.status_code != 200: raise SystemExit(f'EDGAR roster refused: {r.status_code if r is not None else None} — the container address is blocked too (HITL)')
    j = r.json(); rows = [dict(zip(j['fields'], d)) for d in j['data']]; put(f'pond/width0/{STAMP}/company_tickers_exchange.json', r.text)
    EXCH = {'NYSE': 'NYSE', 'Nasdaq': 'NASDAQ', 'CBOE': 'CBOE'}
    listed = [x for x in rows if (x.get('exchange') or '') in EXCH]; log('EDGAR roster', len(rows), 'listed on NYSE/Nasdaq/Cboe', len(listed))
    subs = {}; lock = threading.Lock(); n = [0]
    def one(cik):
        rr = edgar(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json')
        if rr is None or rr.status_code != 200: return
        d = rr.json(); rec = d.get('filings', {}).get('recent', {}); m = len(rec.get('form', []))
        recent = []; annual = None
        for i in range(m):
            f = {'form': rec['form'][i], 'date': rec['filingDate'][i], 'accession': rec['accessionNumber'][i], 'doc': (rec.get('primaryDocument') or [''] * m)[i], 'desc': (rec.get('primaryDocDescription') or [''] * m)[i], 'items': (rec.get('items') or [''] * m)[i], 'report_date': (rec.get('reportDate') or [''] * m)[i]}
            if f['date'] >= SINCE: recent.append(f)
            if annual is None and f['form'] in ('10-K', '20-F', '40-F', '10-KT'): annual = f
        b = (d.get('addresses') or {}).get('business') or {}
        with lock:
            subs[cik] = {'name': d.get('name'), 'sic': d.get('sic'), 'sic_desc': d.get('sicDescription'), 'state_inc': d.get('stateOfIncorporation'), 'state_inc_desc': d.get('stateOfIncorporationDescription'), 'fye': d.get('fiscalYearEnd'), 'category': d.get('category'), 'entity_type': d.get('entityType'), 'ein': d.get('ein'), 'tickers': d.get('tickers') or [], 'exchanges': d.get('exchanges') or [], 'former': [x.get('name') for x in (d.get('formerNames') or [])], 'website': d.get('website') or '', 'ir': d.get('investorWebsite') or '',
                         'business': ', '.join(v for v in (b.get('street1'), b.get('street2'), b.get('city'), b.get('stateOrCountry'), b.get('zipCode')) if v), 'city': b.get('city') or '', 'recent': recent, 'annual': annual, 'src': f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json'}
            n[0] += 1
            if n[0] % 500 == 0: log('submissions', n[0])
    ciks = sorted({x['cik'] for x in listed})
    with ThreadPoolExecutor(max_workers=4) as ex: list(ex.map(one, ciks))
    log('submissions read', len(subs), 'of', len(ciks)); put(f'pond/width0/{STAMP}/submissions.json', json.dumps(subs, ensure_ascii=False))
    roster = []; seen = set()
    for x in listed:
        k = (EXCH[x['exchange']], x['ticker'])
        if k in seen: continue
        seen.add(k); s = subs.get(x['cik']) or {}; sic = str(s.get('sic') or ''); nm = (s.get('name') or x['name'] or '').strip(); et = (s.get('entity_type') or '').lower()
        st = 'Fund / trust (by SIC or name)' if sic in ('6722', '6726') or re.search(r'\b(ETF|EXCHANGE TRADED FUND|TRUST SERIES|INDEX FUND)\b', nm.upper()) else ('SPAC (by SIC 6770)' if sic == '6770' else (f'Non-operating entity type ({et})' if et and et != 'operating' else 'Corporate'))
        roster.append({'exchange': k[0], 'ticker': x['ticker'], 'cik': x['cik'], 'name': nm, 'list_name': x['name'], 'security_type': st, **{kk: s.get(kk) for kk in ('sic', 'sic_desc', 'state_inc', 'state_inc_desc', 'fye', 'category', 'entity_type', 'ein', 'former', 'tickers', 'business', 'city', 'website', 'ir', 'annual', 'src')}, 'n_recent': len(s.get('recent') or [])})
    log('roster', len(roster), {e: sum(1 for r in roster if r['exchange'] == e) for e in ('NYSE', 'NASDAQ', 'CBOE')}); put(f'pond/width0/{STAMP}/roster.json', json.dumps(roster, ensure_ascii=False))
    return roster, subs
# ---------------- GLEIF (local joins over the staged golden-copy extract)
def norm(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper().replace('&', ' AND ')).split())
def norm_loose(s): return ' '.join(w for w in norm(s).split() if w not in {'INC', 'INCORPORATED', 'CORP', 'CORPORATION', 'CO', 'COMPANY', 'LTD', 'LIMITED', 'PLC', 'LLC', 'LP', 'HOLDINGS', 'HOLDING', 'GROUP', 'THE', 'NV', 'SA', 'AG', 'SE'})
def gleif(roster):
    recs = {}; b = get_blob('estate/gleif-golden/2026-09-12/lei-US.jsonl')
    if not b: log('no GLEIF extract in the pond; LEI blank'); return {}, {}
    for line in b.decode('utf-8').splitlines():
        try: d = json.loads(line); recs[d['lei']] = d
        except Exception: pass
    idx = json.loads(get_blob('estate/gleif-golden/2026-09-12/lei-index-US.json').decode('utf-8'))['name']; loose = {}
    for k, v in idx.items(): loose.setdefault(norm_loose(k), []).extend(v)
    match = {}
    for r in roster:
        st = (r.get('state_inc') or '').upper(); c = [recs[l] for l in idx.get(norm(r['name']), []) if l in recs] or [recs[l] for l in idx.get(norm(r['list_name']), []) if l in recs]
        route = 'GLEIF name-exact'
        if not c: c = [recs[l] for l in loose.get(norm_loose(r['name']), []) if l in recs]; route = 'GLEIF name-exact (suffix-insensitive)'
        if st and len(st) == 2 and st.isalpha(): c2 = [x for x in c if x['jur'] in (f'US-{st}', 'US')]; c = c2 or c
        act = [x for x in c if x['status'] == 'ACTIVE' and x['reg_status'] in ('ISSUED', 'PENDING_TRANSFER', 'PENDING_ARCHIVAL')]
        if len(c) > 1 and len(act) == 1: c = act
        if len(c) == 1: match[r['cik']] = {'lei': c[0]['lei'], 'match': f"{route} (jurisdiction US-{st}; GLEIF golden copy 2026-09-12)", 'rec': c[0]}
        elif len(c) > 1: match[r['cik']] = {'lei': '', 'gap': 'several GLEIF records share the exact name and jurisdiction: ' + ', '.join(x['lei'] for x in c[:4])}
        else: match[r['cik']] = {'lei': '', 'gap': 'no GLEIF record with the exact legal name in jurisdiction US' + (f'-{st}' if st else '')}
    log('LEI matched', sum(1 for m in match.values() if m.get('lei')), 'of', len(roster))
    want = {m['lei'] for m in match.values() if m.get('lei')}; isins = {l: [] for l in want}
    z = get_blob('estate/gleif-isin/isin-lei-latest.zip')
    if z:
        zf = zipfile.ZipFile(io.BytesIO(z)); n0 = zf.namelist()[0]; rd = csv.reader(io.TextIOWrapper(zf.open(n0), encoding='utf-8', newline='')); hdr = next(rd); li = hdr.index('LEI'); ii = hdr.index('ISIN')
        for row in rd:
            if row[li] in isins: isins[row[li]].append(row[ii])
        log('ISINs mapped to', sum(1 for v in isins.values() if v), 'LEIs')
    put(f'pond/width0/{STAMP}/lei_match.json', json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'rec'} for k, v in match.items()}, ensure_ascii=False))
    return match, isins
# ---------------- Width 1 from the submissions header
FORM_TYPE = [('takeover', r'^SC TO|^SC 14D9'), ('major_holder', r'^SC 13[DG]'), ('directors_dealings', r'^[345](/A)?$'), ('agm_egm', r'^DEF 14A|^DEFA14A|^PRE 14A'), ('prospectus', r'^S-1|^S-3|^S-4|^S-11|^F-1|^F-3|^424B|^F-10'), ('halt_suspension', r'^25(-NSE)?$|^15-12'), ('results', r'^10-K|^10-Q|^20-F|^40-F|^6-K'), ('ad_hoc', r'^8-K')]
ITEM_TYPE = {'2.02': 'results', '5.02': 'director_change', '1.01': 'corporate_news', '7.01': 'corporate_news', '8.01': 'corporate_news', '5.07': 'agm_egm', '3.01': 'halt_suspension', '1.03': 'ad_hoc', '4.01': 'director_change', '2.01': 'takeover'}
def width1(roster, subs):
    events = {}; n = 0
    for r in roster:
        s = subs.get(r['cik']) or {}; evs = []
        for f in s.get('recent') or []:
            et = next((t for t, pat in FORM_TYPE if re.match(pat, f['form'])), 'regulatory_filing')
            if f['form'].startswith('8-K') and f.get('items'):
                for it in [x.strip() for x in f['items'].split(',')]:
                    if it in ITEM_TYPE: et = ITEM_TYPE[it]; break
            acc = f['accession'].replace('-', ''); url = f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{acc}/{f['doc']}" if f.get('doc') else f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{acc}/"
            evs.append({'date': f['date'], 'event_type': et, 'title': f"{f['form']}" + (f" — {f['desc']}" if f.get('desc') else '') + (f" (items {f['items']})" if f.get('items') else ''), 'category': f['form'], 'reference': f['accession'], 'language': 'en', 'wire': 'EDGAR', 'source': 'SEC EDGAR filing index', 'url': url, 'read_by': 'EDGAR submissions API (filings list per CIK)', 'detail': f"report date {f.get('report_date') or ''}", 'state': 'sourced'})
        evs.sort(key=lambda e: e['date'], reverse=True); events[(r['exchange'], r['ticker'])] = evs; n += len(evs)
    log('Width 1 events', n, 'issuers with events', sum(1 for v in events.values() if v)); return events
# ---------------- Fill: auditor from the 10-K cover iXBRL tag; optional lab reads
def fill(roster, subs):
    out = {}; lock = threading.Lock(); cnt = [0]
    gem_key = os.environ.get('GEMINI_API_KEY', ''); pplx = os.environ.get('PERPLEXITY_API_KEY', ''); pmax = int(os.environ.get('PPLX_MAX', '0'))
    def gemini(prompt):
        try:
            rr = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={gem_key}', json={'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0, 'responseMimeType': 'application/json'}}, timeout=120)
            return rr.json()['candidates'][0]['content']['parts'][0]['text'] if rr.ok else ''
        except Exception: return ''
    def one(r):
        a = r.get('annual'); res = {}
        if a and a.get('doc'):
            acc = a['accession'].replace('-', ''); url = f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{acc}/{a['doc']}"
            rr = edgar(url, headers={**UA, 'Range': 'bytes=0-900000'}) if False else edgar(url)
            if rr is not None and rr.status_code in (200, 206):
                t = rr.text[:1500000]
                def tag(name):
                    m = re.search(r'<ix:nonNumeric[^>]*name="dei:' + name + r'"[^>]*>(.*?)</ix:nonNumeric>', t, re.S | re.I); return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''
                res = {'auditor': tag('AuditorName'), 'auditor_location': tag('AuditorLocation'), 'auditor_firm_id': tag('AuditorFirmId'), 'period_end': tag('DocumentPeriodEndDate'), 'well_known_seasoned': tag('EntityWellKnownSeasonedIssuer'), 'document_url': url, 'form': a['form'], 'filed': a['date'], 'read_by': 'EDGAR 10-K cover page iXBRL tag (dei:AuditorName, dei:AuditorLocation, dei:AuditorFirmId, dei:DocumentPeriodEndDate)'}
                if gem_key:
                    w = []
                    for m in re.finditer(r'(?i)transfer agent|registrar and transfer|stock transfer', re.sub(r'<[^>]+>', ' ', t)):
                        w.append(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)[max(0, m.start() - 300): m.end() + 300]))
                        if len(w) >= 3: break
                    if w:
                        j = gemini('From these excerpts of a 10-K, name the transfer agent / registrar of the registrant\'s common stock exactly as written, or empty if not stated. JSON only: {"transfer_agent": "", "evidence": "verbatim sentence"}\n\n' + '\n---\n'.join(w))
                        try: jj = json.loads(re.search(r'\{.*\}', j, re.S).group(0)); res['registrar'] = (jj.get('transfer_agent') or '').strip(); res['registrar_evidence'] = (jj.get('evidence') or '')[:300]; res['registrar_read_by'] = 'read by Gemini — 10-K text windows (transfer agent)'
                        except Exception: pass
        with lock:
            out[(r['exchange'], r['ticker'])] = res; cnt[0] += 1
            if cnt[0] % 500 == 0: log('fill', cnt[0])
    corp = [r for r in roster if r['security_type'] == 'Corporate']
    with ThreadPoolExecutor(max_workers=4) as ex: list(ex.map(one, corp))
    log('fill: auditor tags', sum(1 for v in out.values() if v.get('auditor')), 'period end', sum(1 for v in out.values() if v.get('period_end')), 'registrar (Gemini)', sum(1 for v in out.values() if v.get('registrar')), 'of', len(corp))
    if pplx and pmax:
        pp = {}
        def page(r):
            try:
                rr = requests.post('https://api.perplexity.ai/v1/responses', headers={'Authorization': 'Bearer ' + pplx}, json={'preset': 'fast', 'input': f"Find the official investor-relations page of the US-listed company {r['name']} ({r['exchange']}: {r['ticker']}). Reply JSON only: {{\"url\": \"<page URL or empty>\", \"page_title\": \"<title>\"}}"}, timeout=120); j = rr.json(); txt = ''.join(c.get('text', '') for o in j.get('output', []) if o.get('type') == 'message' for c in o.get('content', []) if c.get('type') == 'output_text')
                m = re.search(r'\{.*\}', txt, re.S); jj = json.loads(m.group(0)) if m else {}; u = (jj.get('url') or '').strip(); alias = ''
                if u.startswith('http'):
                    g = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30); tt = re.search(r'<title>(.*?)</title>', g.text, re.S | re.I) if g.ok else None
                    title = re.sub(r'\s+', ' ', tt.group(1)).strip() if tt else ''; nm = re.split(r'\s*(?:\||–|—| - |:)\s*', title)[0].strip()
                    if nm and 2 <= len(nm.split()) <= 6 and norm(nm) != norm(r['name']) and norm_loose(nm) and norm_loose(nm) in norm_loose(r['name']): alias = nm
                with lock: pp[(r['exchange'], r['ticker'])] = {'url': u, 'page_title': jj.get('page_title', ''), 'alias': alias, 'usage': j.get('usage'), 'read_by': 'read by Perplexity (agent · fast)'}
            except Exception as e:
                with lock: pp[(r['exchange'], r['ticker'])] = {'error': repr(e)[:120]}
        with ThreadPoolExecutor(max_workers=6) as ex: list(ex.map(page, corp[:pmax]))
        log('perplexity pages', len(pp), 'aliases', sum(1 for v in pp.values() if v.get('alias')))
        for k, v in pp.items(): out.setdefault(k, {})['perplexity'] = v
    put(f'pond/width0/{STAMP}/fill.json', json.dumps({f'{k[0]}|{k[1]}': v for k, v in out.items()}, ensure_ascii=False)); return out
# ---------------- door render
STATES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia', 'PR': 'Puerto Rico'}
def slug(t): return re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
def nkey(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('&', ' and ')).strip()
def F(v, src, rb, state='sourced', note=None):
    o = {'value': v if v not in ('', []) else None, 'source_url': src, 'read_by': rb, 'state': state if v not in ('', [], None) else None}
    if note and o['value'] is None: o['reason'] = note
    return o
def render(roster, match, isins, events, fills):
    idx = {'ticker': {}, 'isin': {}, 'lei': {}, 'alias': {}, 'name': {}, 'cmr': {}, 'keys': []}; n = 0; ev_total = 0; counts = {}
    RB_H = 'EDGAR submissions API (issuer header as filed)'; RB_L = 'EDGAR company_tickers_exchange.json (SEC list of exchange-listed filers)'
    for r in roster:
        key = f"{NODE}/{r['exchange']}/{r['ticker']}"; m = match.get(r['cik']) or {}; lei = m.get('lei') or ''; rec = m.get('rec') or {}; fl = fills.get((r['exchange'], r['ticker'])) or {}
        us = [i for i in isins.get(lei, []) if i.startswith('US')] if lei else []; st = (r.get('state_inc') or '').upper()
        ident = {'name': F(r['name'], r['src'], RB_H), 'ticker': F(r['ticker'], 'https://www.sec.gov/files/company_tickers_exchange.json', RB_L), 'exchange': F(r['exchange'], 'https://www.sec.gov/files/company_tickers_exchange.json', RB_L), 'security_type': F(r['security_type'], r['src'], RB_H), 'cik': F(str(r['cik']), r['src'], RB_H), 'edgar_filer_page': F(f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(r['cik']):010d}", r['src'], RB_H),
                 'isin': F(us[0] if len(us) == 1 else '', 'https://mapping.gleif.org/api/v2/isin-lei/latest', 'GLEIF ISIN-to-LEI mapping file (ISINs mapped to the LEI)', note=('several US ISINs on the LEI: ' + ', '.join(us) if len(us) > 1 else ('GLEIF maps no US ISIN to this LEI' if lei else 'no LEI, so no GLEIF ISIN route; EDGAR carries no ISIN'))),
                 'lei': F(lei, rec.get('src', ''), m.get('match', ''), note=m.get('gap')), 'lei_registration_status': F(rec.get('reg_status', ''), rec.get('src', ''), 'GLEIF LEI record'),
                 'state_of_incorporation': F(st, r['src'], RB_H + ' (stateOfIncorporation)'), 'jurisdiction': F(('United States — ' + STATES[st]) if st in STATES else (r.get('state_inc_desc') or ''), r['src'], RB_H + ' (stateOfIncorporation)'),
                 'sector': F(f"{r.get('sic') or ''} {r.get('sic_desc') or ''}".strip(), r['src'], RB_H + ' (SIC code as assigned by the SEC)'), 'business_address': F(r.get('business') or '', r['src'], RB_H + ' (business address)'), 'hq_city': F(r.get('city') or '', r['src'], RB_H + ' (business address city)'),
                 'fiscal_year_end': F(r.get('fye') or '', r['src'], RB_H + ' (fiscalYearEnd MMDD)'), 'filer_category': F(r.get('category') or '', r['src'], RB_H), 'entity_type': F(r.get('entity_type') or '', r['src'], RB_H), 'website': F(r.get('website') or '', r['src'], RB_H),
                 'annual_report': F(fl.get('document_url') or '', r['src'], RB_H + ' (latest 10-K / 20-F / 40-F in the recent filings list)'),
                 'auditor': F(fl.get('auditor') or '', fl.get('document_url', ''), fl.get('read_by', ''), note='no dei:AuditorName tag on the latest annual report cover (foreign private issuers and older filings carry none)'),
                 'auditor_location': F(fl.get('auditor_location') or '', fl.get('document_url', ''), fl.get('read_by', '')), 'auditor_firm_id': F(fl.get('auditor_firm_id') or '', fl.get('document_url', ''), fl.get('read_by', '')), 'accounts_period_end': F(fl.get('period_end') or '', fl.get('document_url', ''), fl.get('read_by', '')),
                 'registrar': F(fl.get('registrar') or '', fl.get('document_url', ''), fl.get('registrar_read_by', ''), state='filled', note='no transfer agent named in the 10-K text windows (Fill pass, Gemini)')}
        aliases = [{'value': a, 'source_url': r['src'], 'read_by': RB_H + ' (formerNames)'} for a in (r.get('former') or []) if a and nkey(a) != nkey(r['name'])][:6]
        for o in (rec.get('other_names') or []):
            nm = o.get('name') if isinstance(o, dict) else o
            if nm and nkey(nm) != nkey(r['name']) and not any(nkey(nm) == nkey(a['value']) for a in aliases): aliases.append({'value': nm, 'source_url': rec.get('src', ''), 'read_by': 'GLEIF LEI record (other entity names)'})
        pa = (fl.get('perplexity') or {}).get('alias')
        if pa and not any(nkey(pa) == nkey(a['value']) for a in aliases): aliases.append({'value': pa, 'source_url': fl['perplexity'].get('url', ''), 'read_by': 'issuer page <title> (found by Perplexity (agent · fast))'})
        evs = events.get((r['exchange'], r['ticker'])) or []; gaps = [{'field': k, 'reason': v['reason']} for k, v in ident.items() if v.get('reason')]
        recd = {'cmr': key, 'node': NODE, 'as_of': STAMP, 'version': 1, 'identity': ident, 'aliases': aliases, 'events_url': f"{HOST}/events/{r['exchange']}/{r['ticker']}", 'event_count': len(evs), 'gaps': gaps}
        put(f"door/records/{r['exchange']}/{slug(r['ticker'])}.json", json.dumps(recd, ensure_ascii=False, separators=(',', ':'))); put(f"door/events/{r['exchange']}/{slug(r['ticker'])}.json", json.dumps(evs, ensure_ascii=False, separators=(',', ':')))
        idx['keys'].append(key); idx['cmr'][key.upper()] = [key]; idx['ticker'].setdefault(r['ticker'].upper(), []).append(key); root = r['ticker'].split('.')[0].upper()
        if root != r['ticker'].upper(): idx['ticker'].setdefault(root, []).append(key)
        if ident['isin']['value']: idx['isin'].setdefault(ident['isin']['value'], []).append(key)
        if lei: idx['lei'].setdefault(lei.upper(), []).append(key)
        idx['name'].setdefault(nkey(r['name']), []).append(key)
        for a in aliases: idx['alias'].setdefault(nkey(a['value']), []).append(key)
        counts[r['exchange']] = counts.get(r['exchange'], 0) + 1; n += 1; ev_total += len(evs)
        if n % 500 == 0: log('rendered', n)
    facts = {'as_of': STAMP, 'records': n, 'events': ev_total, 'nodes': {NODE: {'as_of': STAMP, 'version': 1, 'records': n, 'records_by_exchange': counts, 'events': ev_total, 'issuers_with_events': sum(1 for v in events.values() if v), 'exchanges': ['NYSE', 'NASDAQ', 'CBOE']}}, 'source': 'public-record', 'operator': 'Allooloo Technologies Corp.', 'store': f'Azure Storage (regional pond, {REGION}) — blob per record and per issuer event list', 'tools': ['resolve_issuer', 'get_record', 'list_events_since', 'list_aliases', 'list_nodes'], 'mcp': '/mcp (Streamable HTTP, JSON-RPC 2.0, no auth)', 'region': REGION}
    nodes_b = get_blob('door/nodes.json'); nodes = json.loads(nodes_b.decode('utf-8')) if nodes_b else []
    for x in nodes:
        if x.get('node') == NODE: x.update({'live': True, 'as_of': STAMP, 'records': n, 'exchanges': ['NYSE', 'NASDAQ', 'CBOE']})
    put('door/index.json', json.dumps(idx, separators=(',', ':'))); put('door/facts.json', json.dumps(facts, indent=1)); put('door/nodes.json', json.dumps(nodes, indent=1))
    log('door rendered', n, 'records', ev_total, 'events', counts)
if __name__ == '__main__':
    t0 = time.time(); log('US rail start', STAMP, 'UA', UA['User-Agent'])
    roster, subs = width0(); match, isins = gleif(roster); events = width1(roster, subs); fills = fill(roster, subs); render(roster, match, isins, events, fills)
    put(f'pond/width0/{STAMP}/job.log', '\n'.join(LOG), 'text/plain'); log('US rail DONE in', round((time.time() - t0) / 60, 1), 'minutes')
