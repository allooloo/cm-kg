"""Brazil Width 0 roster - listed equity shares of B3 S.A. - Brasil, Bolsa, Balcao (ISO 10383 MIC BVMF).

Source of record: B3's daily "Cadastro de Instrumentos (Listado)" file, InstrumentsConsolidatedFile_<YYYYMMDD>_1.csv, published keyless on
arquivos.b3.com.br (GET /api/download/requestname?fileName=InstrumentsConsolidatedFile&date=YYYY-MM-DD returns a one-time token, then
GET /api/download/?token=<token>). One line per instrument (ticker) with ISIN, CFI code, issuer name (CrpnNm), segment, market, category.
Scope: SgmtNm=CASH, MktNm=EQUITY-CASH, SctyCtgyNm=SHARES, CFI ES* (common/ordinary) or EP* (preferred). One row per ISIN (each share class
has its own ISIN and ticker: ...3 = ON, ...4 = PN, ...5/6 = PNA/PNB, ...11/12 = special classes). Excluded and counted: SHARES lines whose CFI
is not ES/EP (CEPACs, receipts, the TAXA rate lines), UNIT certificates (SctyCtgyNm=UNIT; `--units` adds them), BDRs, funds, ETFs, odd-lot
and block-trade segments (same ISIN, other ticker suffix). The column MktCptlstn is dropped (no prices / valuations).
ISIN is read from the B3 file, never computed. MIC: ISO 10383 (iso20022.org ISO10383_MIC.csv) lists BVMF as the operating MIC
"B3 S.A. - BRASIL BOLSA BALCAO"; B3's organised OTC (Mercado de Balcao) share lines are kept on BVMF and flagged by governance level.
LEI: neither B3 nor CVM carries one. Optional exact ISIN -> LEI map from GLEIF (api.gleif.org /lei-records?filter[isin]=<ISIN>); on
2026-10-24 GLEIF's ISIN map held no Brazilian share ISINs (it carries the US ADR ISINs of some issuers), so LEIs stay blank.
Cross-check + issuer keys: CVM open data, Formulario Cadastral (FCA) valor_mobiliario file (ticker -> issuer CNPJ / CVM code), dados.cvm.gov.br.

fetch() -> {"source_url", "read_by", "read_at", "count", "rows": [{"isin","name","mic","lei","ticker","cfi", ...}]}
Usage: python roster.py [--units] [--no-lei]   writes samples/roster-<date>.json
"""
import os, sys, io, csv, json, time, zipfile, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
MARKET = 'br'
MIC = 'BVMF'
B3_REQ = 'https://arquivos.b3.com.br/api/download/requestname'
B3_DL = 'https://arquivos.b3.com.br/api/download/'
FCA_URL = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{y}.zip'
CAD_URL = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv'
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
_last = [0.0]


def _get(url, tries=4, **kw):
    """GET with a gentle pace (<= 2 requests/second) and retry/backoff."""
    for i in range(tries):
        wait = 0.55 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.get(url, headers={**UA, **kw.pop('headers', {})}, timeout=kw.pop('timeout', 300), **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(4 * (i + 1))
    return None


def _cached(name, url, max_age_h=20):
    """Download url into cache/name unless a copy younger than max_age_h exists."""
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, name)
    if os.path.exists(fn) and time.time() - os.path.getmtime(fn) < max_age_h * 3600:
        return fn
    r = _get(url)
    if r is None or r.status_code != 200:
        if os.path.exists(fn):
            return fn
        raise RuntimeError(f'download failed: {url} ({None if r is None else r.status_code})')
    open(fn, 'wb').write(r.content)
    return fn


def b3_instruments(date=None):
    """Latest B3 InstrumentsConsolidatedFile -> (date 'YYYY-MM-DD', file name, [dict rows]). Walks back up to 10 days to the last trading day."""
    d0 = date or datetime.date.today()
    for back in range(0, 11):
        d = d0 - datetime.timedelta(days=back)
        fn = os.path.join(CACHE, f'InstrumentsConsolidatedFile_{d:%Y%m%d}.csv')
        if not os.path.exists(fn):
            r = _get(B3_REQ, params={'fileName': 'InstrumentsConsolidatedFile', 'date': d.isoformat()}, timeout=60)
            if r is None or r.status_code != 200:
                continue
            try:
                tok = r.json().get('token')
            except ValueError:
                tok = None
            if not tok:
                continue
            f = _get(B3_DL, params={'token': tok})
            if f is None or f.status_code != 200 or len(f.content) < 100000:
                continue
            os.makedirs(CACHE, exist_ok=True)
            open(fn, 'wb').write(f.content)
        lines = open(fn, 'rb').read().decode('latin-1').splitlines()
        status = lines[0] if lines and lines[0].startswith('Status') else ''
        rows = list(csv.DictReader(lines[1:] if status else lines, delimiter=';'))
        return d.isoformat(), os.path.basename(fn), status, rows
    raise RuntimeError('No B3 InstrumentsConsolidatedFile found in the last 10 days')


def cvm_fca_tickers():
    """CVM FCA valor_mobiliario (latest document version per company, current and previous year): ticker -> {cnpj, cvm_code, name, market, segment}."""
    out = {}
    y = datetime.date.today().year
    for yr in (y - 1, y):
        try:
            fn = _cached(f'fca_cia_aberta_{yr}.zip', FCA_URL.format(y=yr))
        except RuntimeError:
            continue
        z = zipfile.ZipFile(fn)
        main = list(csv.DictReader(io.StringIO(z.read(f'fca_cia_aberta_{yr}.csv').decode('latin-1')), delimiter=';'))
        code = {}
        for r in main:
            code[r['CNPJ_CIA']] = r['CD_CVM'].lstrip('0')
        vm = list(csv.DictReader(io.StringIO(z.read(f'fca_cia_aberta_valor_mobiliario_{yr}.csv').decode('latin-1')), delimiter=';'))
        latest = {}
        for r in vm:
            k = r['CNPJ_Companhia']
            if k not in latest or int(r['Versao'] or 0) > latest[k]:
                latest[k] = int(r['Versao'] or 0)
        for r in vm:
            if int(r['Versao'] or 0) != latest[r['CNPJ_Companhia']]:
                continue
            t = (r['Codigo_Negociacao'] or '').strip().upper()
            if not t or r['Data_Fim_Negociacao']:
                continue
            out[t] = {'cnpj': r['CNPJ_Companhia'], 'cvm_code': code.get(r['CNPJ_Companhia'], ''), 'name': r['Nome_Empresarial'],
                      'market': r['Mercado'], 'segment': r['Segmento'], 'fca_year': yr}
    return out


B3_COMPANIES = 'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/'


def b3_companies():
    """B3 listed-companies directory (the 'Empresas listadas' page's own API; base64 JSON path parameter), cached daily:
    issuingCompany (4-letter ticker root) -> {codeCVM, cnpj, companyName}."""
    import base64
    fn = os.path.join(CACHE, f'b3_companies_{datetime.date.today():%Y%m%d}.json')
    if os.path.exists(fn):
        return json.load(open(fn, encoding='utf-8'))
    allr, p = [], 1
    while True:
        q = base64.b64encode(json.dumps({'language': 'pt-br', 'pageNumber': p, 'pageSize': 120}).encode()).decode()
        r = _get(B3_COMPANIES + q, timeout=60)
        if r is None or r.status_code != 200:
            raise RuntimeError('B3 listed companies API did not answer')
        j = json.loads(r.content.decode('utf-8', 'replace'))
        allr += j['results']
        if p >= j['page']['totalPages']:
            break
        p += 1
    out = {}
    for x in allr:
        out.setdefault(x['issuingCompany'], {'codeCVM': x['codeCVM'], 'cnpj': x['cnpj'], 'companyName': x['companyName']})
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
    return out


def gleif_lei(isins):
    """Exact ISIN -> LEI map from GLEIF (api.gleif.org filter[isin]). One request per ISIN, paced <= 2/s."""
    hit = {}
    for isin in isins:
        r = _get(GLEIF, params={'filter[isin]': isin}, headers={'Accept': 'application/vnd.api+json'}, timeout=60)
        if r is not None and r.status_code == 200:
            d = r.json().get('data') or []
            if len(d) == 1:
                hit[isin] = d[0]['id']
    return hit


def fetch(units=False, lei=True):
    day, fname, status, recs = b3_instruments()
    cash = [r for r in recs if r['SgmtNm'] == 'CASH' and r['MktNm'] == 'EQUITY-CASH']
    shares = [r for r in cash if r['SctyCtgyNm'] == 'SHARES']
    keep = [r for r in shares if r['CFICd'][:2] in ('ES', 'EP')]
    unit_rows = [r for r in cash if r['SctyCtgyNm'] == 'UNIT']
    if units:
        keep += unit_rows
    fca = cvm_fca_tickers()
    best = {}
    for r in keep:
        if r['ISIN'] and r['ISIN'] not in best:
            best[r['ISIN']] = r
    noisin = [r for r in keep if not r['ISIN']]
    try:
        b3c = b3_companies()
    except RuntimeError:
        b3c = {}
    rows = []
    for r in sorted(best.values(), key=lambda x: (x['CrpnNm'], x['TckrSymb'])) + noisin:
        f = fca.get(r['TckrSymb'], {})
        key_src = 'CVM FCA valor_mobiliario (ticker)' if f else ''
        if not f and r['Asst'] in b3c and b3c[r['Asst']]['codeCVM']:
            c = b3c[r['Asst']]
            f = {'cvm_code': c['codeCVM'].lstrip('0'), 'cnpj': c['cnpj']}
            key_src = 'B3 listed companies (issuingCompany = asset root)'
        rows.append({'isin': r['ISIN'] or None, 'name': r['CrpnNm'].strip(), 'mic': MIC, 'lei': '', 'ticker': r['TckrSymb'], 'cfi': r['CFICd'],
                     'category': r['SctyCtgyNm'], 'specification': ' '.join(r['SpcfctnCd'].split()), 'governance_level': r['CorpGovnLvlNm'] or '',
                     'asset_root': r['Asst'], 'currency': r['TradgCcy'], 'cvm_code': f.get('cvm_code', ''), 'cnpj': f.get('cnpj', ''),
                     'issuer_key_source': key_src, 'lei_source': ''})
    lei_hits = {}
    if lei:
        lei_hits = gleif_lei([r['isin'] for r in rows if r['isin']])
        for r in rows:
            if r['isin'] in lei_hits:
                r['lei'] = lei_hits[r['isin']]; r['lei_source'] = 'GLEIF ISIN map (api.gleif.org filter[isin])'
    src = f'{B3_DL}?token=<one-time> (via {B3_REQ}?fileName=InstrumentsConsolidatedFile&date={day})'
    return {'source_url': src, 'file': fname.replace('.csv', '_1.csv'), 'file_status': status,
            'read_by': f'B3 Cadastro de Instrumentos (InstrumentsConsolidatedFile) {day}; SgmtNm=CASH, MktNm=EQUITY-CASH, SctyCtgyNm=SHARES'
                       + (' + UNIT' if units else '') + ', CFI ES*/EP*; ISIN as published by B3; MIC BVMF (ISO 10383)',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'b3_file_date': day,
            'records_scanned': len(recs), 'count': len(rows), 'count_with_isin': sum(1 for r in rows if r['isin']),
            'count_without_isin': sum(1 for r in rows if not r['isin']),
            'count_by_cfi2': {k: sum(1 for r in rows if r['cfi'][:2] == k) for k in sorted({r['cfi'][:2] for r in rows})},
            'excluded': {'shares_non_ES_EP_cfi': len(shares) - len([r for r in shares if r['CFICd'][:2] in ('ES', 'EP')]),
                         'unit_lines': 0 if units else len(unit_rows)},
            'otc_lines_mercado_de_balcao': sum(1 for r in rows if 'BALC' in r['governance_level'].upper()),
            'lei_method': 'GLEIF exact ISIN map (api.gleif.org/api/v1/lei-records?filter[isin]=)' if lei else 'not looked up (--no-lei)',
            'lei_hits': len(lei_hits), 'with_cvm_code': sum(1 for r in rows if r['cvm_code']), 'scope': 'B3 listed shares (BVMF)', 'rows': rows}


def crosscheck(result):
    """CVM side: active registrations (cad_cia_aberta.csv SIT=ATIVO) and FCA tickers vs. the B3 roster."""
    fn = _cached('cad_cia_aberta.csv', CAD_URL)
    cad = list(csv.DictReader(io.StringIO(open(fn, 'rb').read().decode('latin-1')), delimiter=';'))
    active = {r['CD_CVM'].lstrip('0') for r in cad if r['SIT'] == 'ATIVO'}
    codes = {r['cvm_code'] for r in result['rows'] if r['cvm_code']}
    return {'source_url': CAD_URL + ' + ' + FCA_URL.format(y='<year>') + ' (valor_mobiliario)',
            'cvm_registered_companies_active': len(active), 'roster_issuers_with_cvm_code': len(codes),
            'roster_issuers_cvm_status_active': len(codes & active),
            'roster_rows_without_fca_ticker_match': sum(1 for r in result['rows'] if not r['cvm_code'])}


if __name__ == '__main__':
    res = fetch(units='--units' in sys.argv, lei='--no-lei' not in sys.argv)
    res['crosscheck'] = crosscheck(res)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], 'with ISIN', res['count_with_isin'], res['count_by_cfi2'], 'LEI hits', res['lei_hits'], 'cvm codes', res['with_cvm_code'], '->', out)
    print('crosscheck', res['crosscheck'], 'excluded', res['excluded'])
