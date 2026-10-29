"""Brazil Width 1 events - issuer regulated information filed with CVM (Empresas.NET / RAD), read from CVM's open data portal.

Store: CVM's RAD / ENET (Empresas.NET) system is where listed companies file. CVM publishes the index of every filing keyless on
dados.cvm.gov.br (Portal Dados Abertos CVM), one zip per year:
  - IPE  (Informacoes Periodicas e Eventuais: fatos relevantes, comunicados ao mercado, assembleias, avisos aos acionistas, ...)
         https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_<YYYY>.zip
         columns: CNPJ_Companhia, Nome_Companhia, Codigo_CVM, Data_Referencia, Categoria, Tipo, Especie, Assunto, Data_Entrega,
                  Tipo_Apresentacao, Protocolo_Entrega, Versao, Link_Download (a rad.cvm.gov.br/ENET download link)
  - ITR  (quarterly statements) and DFP (annual statements): the index csv inside itr_cia_aberta_<YYYY>.zip / dfp_cia_aberta_<YYYY>.zip
         (CNPJ_CIA, DT_REFER, VERSAO, DENOM_CIA, CD_CVM, CATEG_DOC, ID_DOC, DT_RECEB, LINK_DOC)
Each event: date = Data_Entrega / DT_RECEB (delivery date, no time in the open data), type = the store's own Categoria (IPE) or CATEG_DOC
(ITR/DFP), type_en = null (CVM publishes no English code table for IPE categories: the dataset's meta file meta_ipe_cia_aberta.txt is
Portuguese only), title = Assunto exactly as filed; when Assunto is empty the Especie (document species as filed) is used and
title_field says so. ITR/DFP carry no subject: title is null.
Freshness: CVM refreshes the IPE/ITR/DFP files about weekly (IPE 2026 last modified 2026-10-18, newest Data_Entrega 2026-10-17). Filings
after the newest Data_Entrega in the IPE file are filled from B3's Plantao de Noticias (sistemasweb.b3.com.br/PlantaoNoticias, agencia=18,
B3's official republication of issuer filings); those carry channel "B3 Plantao de Noticias", title = the B3 headline as published, type null.

Resolution of the key: ISIN -> B3 InstrumentsConsolidatedFile ticker/asset root -> CVM FCA valor_mobiliario (ticker -> CNPJ/CVM code),
else B3 listed-companies directory (asset root -> codeCVM). A CVM code (digits) or CNPJ (00.000.000/0000-00) is accepted directly.
fetch(isin_or_issuer, since) -> [{"date","type","type_en","title","url","source", ...}]
Usage: python events.py [ISIN ...]   (default: three large issuers) writes samples/events-<date>.json
"""
import os, sys, io, re, csv, json, time, zipfile, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roster as R  # same folder: B3 file + FCA loaders, cache, pacing

CVM = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{d}/DADOS/{f}_cia_aberta_{y}.zip'
NEWS = 'https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/ListarTitulosNoticias'
NEWS_DETAIL = 'https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Detail?idNoticia={id}&agencia=18&dataNoticia={dt}'
SOURCE_IPE = 'CVM open data IPE (dados.cvm.gov.br, RAD/ENET filings index)'
SOURCE_PER = 'CVM open data {k} (dados.cvm.gov.br, RAD/ENET filings index)'
SOURCE_NEWS = 'B3 Plantao de Noticias (sistemasweb.b3.com.br, agencia=18)'
_mem = {}


def _year_index(kind, y):
    """kind in IPE/ITR/DFP -> list of dict rows of that year's index (cached; refreshed when older than 20 h)."""
    key = (kind, y)
    if key in _mem:
        return _mem[key]
    f = kind.lower()
    try:
        fn = R._cached(f'{f}_cia_aberta_{y}.zip', CVM.format(d=kind, f=f, y=y))
    except RuntimeError:
        _mem[key] = []; return []
    z = zipfile.ZipFile(fn)
    name = f'{f}_cia_aberta_{y}.csv'
    rows = list(csv.DictReader(io.StringIO(z.read(name).decode('latin-1')), delimiter=';')) if name in z.namelist() else []
    _mem[key] = rows
    return rows


def _issuer_map():
    if 'map' in _mem:
        return _mem['map']
    day, fname, status, recs = R.b3_instruments()
    by_isin = {}
    for r in recs:
        if r['ISIN'] and r['SgmtNm'] == 'CASH':
            by_isin.setdefault(r['ISIN'], []).append(r)
    fca = R.cvm_fca_tickers()
    try:
        b3c = R.b3_companies()
    except RuntimeError:
        b3c = {}
    _mem['map'] = (by_isin, fca, b3c)
    return _mem['map']


def resolve(key):
    """-> {'cvm_code','cnpj','ticker_root','tickers','how'}"""
    key = key.strip()
    by_isin, fca, b3c = _issuer_map()
    if re.fullmatch(r'\d{1,6}', key):
        return {'cvm_code': key.lstrip('0'), 'cnpj': '', 'ticker_root': '', 'tickers': [], 'how': 'CVM code given'}
    if re.fullmatch(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', key):
        return {'cvm_code': '', 'cnpj': key, 'ticker_root': '', 'tickers': [], 'how': 'CNPJ given'}
    lines = by_isin.get(key.upper(), [])
    tickers = sorted({l['TckrSymb'] for l in lines}) or ([key.upper()] if re.fullmatch(r'[A-Z0-9]{4}\d{1,2}', key.upper()) else [])
    root = (lines[0]['Asst'] if lines else (tickers[0][:4] if tickers else ''))
    for t in tickers:
        if t in fca and fca[t]['cvm_code']:
            return {'cvm_code': fca[t]['cvm_code'], 'cnpj': fca[t]['cnpj'], 'ticker_root': root, 'tickers': tickers, 'how': f'CVM FCA valor_mobiliario ticker {t}'}
    if root in b3c and b3c[root]['codeCVM']:
        return {'cvm_code': b3c[root]['codeCVM'].lstrip('0'), 'cnpj': '', 'ticker_root': root, 'tickers': tickers, 'how': f'B3 listed companies issuingCompany {root}'}
    return {'cvm_code': '', 'cnpj': '', 'ticker_root': root, 'tickers': tickers, 'how': 'unresolved'}


def _b3_news(root, start, end):
    """B3 Plantao de Noticias headlines for '(ROOT' between start and end (<= 30-day windows, as the page enforces)."""
    out, e = [], end
    while e >= start:
        s = max(start, e - datetime.timedelta(days=29))
        r = R._get(NEWS, params={'agencia': 18, 'palavra': root, 'dataInicial': s.isoformat(), 'dataFinal': e.isoformat()}, timeout=60)
        if r is not None and r.status_code == 200 and r.text.strip():
            try:
                for x in r.json():
                    m = x['NwsMsg']
                    if re.search(r'\(' + re.escape(root) + r'(\b|-)', m['headline']):
                        out.append(m)
            except ValueError:
                pass
        e = s - datetime.timedelta(days=1)
    return out


def fetch(isin_or_issuer, since, news_gap=True):
    """since: 'YYYY-MM-DD' or date. Returns newest first."""
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    who = resolve(isin_or_issuer)
    code, cnpj = who['cvm_code'], who['cnpj']
    if not code and not cnpj:
        return []
    match = (lambda c, n: c.lstrip('0') == code) if code else (lambda c, n: n == cnpj)
    today = datetime.date.today()
    out, newest_ipe = [], ''
    for y in range(since.year, today.year + 1):
        ipe = _year_index('IPE', y)
        if ipe:
            if ('newest', y) not in _mem:
                _mem[('newest', y)] = max(r['Data_Entrega'] for r in ipe)
            newest_ipe = max(newest_ipe, _mem[('newest', y)])
        for r in ipe:
            if not match(r['Codigo_CVM'], r['CNPJ_Companhia']) or r['Data_Entrega'] < since.isoformat():
                continue
            title, tf = (r['Assunto'].strip(), 'Assunto') if r['Assunto'].strip() else (r['Especie'].strip() or None, 'Especie')
            out.append({'date': r['Data_Entrega'], 'type': r['Categoria'], 'type_en': None, 'title': title, 'url': r['Link_Download'],
                        'source': SOURCE_IPE, 'title_field': tf, 'tipo': r['Tipo'], 'especie': r['Especie'], 'reference_date': r['Data_Referencia'],
                        'presentation': r['Tipo_Apresentacao'], 'version': r['Versao'], 'protocol': r['Protocolo_Entrega'],
                        'issuer': r['Nome_Companhia'], 'cvm_code': r['Codigo_CVM'], 'channel': 'CVM RAD/ENET (IPE)'})
        for kind in ('ITR', 'DFP'):
            for r in _year_index(kind, y):
                if not match(r['CD_CVM'], r['CNPJ_CIA']) or r['DT_RECEB'] < since.isoformat():
                    continue
                out.append({'date': r['DT_RECEB'], 'type': r['CATEG_DOC'], 'type_en': None, 'title': None, 'url': r['LINK_DOC'],
                            'source': SOURCE_PER.format(k=kind), 'title_field': None, 'reference_date': r['DT_REFER'], 'version': r['VERSAO'],
                            'issuer': r['DENOM_CIA'], 'cvm_code': r['CD_CVM'].lstrip('0'), 'channel': f'CVM RAD/ENET ({kind})'})
    if news_gap and who['ticker_root'] and newest_ipe:
        gap_start = max(since, datetime.date.fromisoformat(newest_ipe) + datetime.timedelta(days=1))
        if gap_start <= today:
            for m in _b3_news(who['ticker_root'], gap_start, today):
                out.append({'date': m['dateTime'].replace(' ', 'T') + '+local(America/Sao_Paulo)', 'type': None, 'type_en': None, 'title': m['headline'],
                            'url': NEWS_DETAIL.format(id=m['id'], dt=m['dateTime'].replace(' ', '%20')), 'source': SOURCE_NEWS,
                            'title_field': 'headline', 'channel': 'B3 Plantao de Noticias (after CVM file cut-off ' + newest_ipe + ')'})
    out.sort(key=lambda e: e['date'], reverse=True)
    for e in out:
        e['resolved_by'] = who['how']
    return out


if __name__ == '__main__':
    tests = sys.argv[1:] or ['BRPETRACNPR6', 'BRVALEACNOR0', 'BRITUBACNPR1']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ (+ ITR, DFP)', 'gap_fill': NEWS + ' (agencia=18)',
           'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': since.isoformat(),
           'key_required': False, 'type_en_note': 'null: CVM publishes no English label table for IPE Categoria / CATEG_DOC', 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        res['issuers'][q] = {'resolved': resolve(q), 'count': len(ev),
                             'by_type': {str(k): sum(1 for e in ev if e['type'] == k) for k in sorted({e['type'] for e in ev}, key=str)},
                             'by_channel': {k: sum(1 for e in ev if e['channel'] == k) for k in sorted({e['channel'] for e in ev})}, 'events': ev}
        print(q, len(ev), res['issuers'][q]['by_channel'], flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
