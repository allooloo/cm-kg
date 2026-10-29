"""Brazil halts - current trading suspensions on B3 (BVMF), DERIVED: B3 publishes no standing list of suspended instruments.

Two official inputs:
 1. B3 Plantao de Noticias (https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Index?agencia=18), B3's official news desk. Its list
    endpoint ListarTitulosNoticias?agencia=18&palavra=<word>&dataInicial=&dataFinal= (max 30-day window, last 365 days) is searched
    for "suspens" (Suspensao de negociacao ...) and "reabertura" (Reabertura dos negocios). Headlines read like
    "PRIO (PRIO-NM) - Suspensao de negociacao / Iminencia de divulgacao de fato relevante"; the ticker root is the code in brackets.
    Rule: a root is halted when its latest suspension notice is not followed by a "Reabertura" / "Revogacao" notice for the same root,
    and, for the intraday kind ("Iminencia de divulgacao de fato relevante", lifted within the session without a separate notice),
    only when the notice is from today (Sao Paulo date).
 2. CVM's register of public companies (https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv): SIT =
    "SUSPENSO(A) - DECISAO ADM" (registration suspended by CVM; B3 suspends trading on such a decision). Matched to B3 share lines by
    CNPJ (CVM FCA valor_mobiliario ticker list, or B3's listed-companies directory).
Each halted root is expanded to its B3 cash-market lines (B3 InstrumentsConsolidatedFile) to give ISIN and ticker. Reasons are Portuguese
as published. No key.

fetch() -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page", ...}]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, sys, re, io, csv, json, datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roster as R

NEWS = 'https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/ListarTitulosNoticias'
NEWS_PAGE = 'https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Index?agencia=18'
DETAIL = 'https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Detail?idNoticia={id}&agencia=18&dataNoticia={dt}'
INTRADAY = re.compile(r'Iminencia', re.I)
LIFT = re.compile(r'Reabertura|Revogacao', re.I)
SUSP = re.compile(r'Suspensao', re.I)
ROOT = re.compile(r'\(([A-Z0-9]{4})(?:-[A-Z0-9]+)?\)')


def news(word, days=365):
    end = datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).date()
    start = end - datetime.timedelta(days=days - 1)
    out, e = [], end
    while e >= start:
        s = max(start, e - datetime.timedelta(days=29))
        r = R._get(NEWS, params={'agencia': 18, 'palavra': word, 'dataInicial': s.isoformat(), 'dataFinal': e.isoformat()}, timeout=60)
        if r is not None and r.status_code == 200 and r.text.strip():
            try:
                out += [x['NwsMsg'] for x in r.json()]
            except ValueError:
                pass
        e = s - datetime.timedelta(days=1)
    return out


def fetch(days=365):
    today = datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).date().isoformat()
    susp = [m for m in news('suspens', days) if SUSP.search(m['headline']) and not LIFT.search(m['headline'])]
    lifts = [m for m in news('reabertura', days)] + [m for m in news('revogacao', days)]
    last_lift = {}
    for m in lifts:
        k = ROOT.search(m['headline'])
        if k and LIFT.search(m['headline']):
            last_lift[k.group(1)] = max(last_lift.get(k.group(1), ''), m['dateTime'])
    latest = {}
    for m in susp:
        k = ROOT.search(m['headline'])
        if k and m['dateTime'] > latest.get(k.group(1), {'dateTime': ''})['dateTime']:
            latest[k.group(1)] = m
    current = {}
    for root, m in latest.items():
        if last_lift.get(root, '') > m['dateTime']:
            continue
        if INTRADAY.search(m['headline']) and m['dateTime'][:10] != today:
            continue
        current[root] = {'since': m['dateTime'] + ' (America/Sao_Paulo)', 'reason': m['headline'], 'page': DETAIL.format(id=m['id'], dt=m['dateTime'].replace(' ', '%20')),
                         'basis': 'B3 Plantao de Noticias notice'}
    # CVM registration suspensions
    cad_fn = R._cached('cad_cia_aberta.csv', R.CAD_URL)
    cad = list(csv.DictReader(io.StringIO(open(cad_fn, 'rb').read().decode('latin-1')), delimiter=';'))
    cvm_susp = {r['CNPJ_CIA']: r for r in cad if r['SIT'].startswith('SUSPENSO')}
    fca = R.cvm_fca_tickers()
    try:
        b3c = R.b3_companies()
    except RuntimeError:
        b3c = {}
    digits = lambda s: re.sub(r'\D', '', s or '')
    cnpj_roots = {}
    for t, f in fca.items():
        cnpj_roots.setdefault(digits(f['cnpj']), set()).add(t[:4])
    for root, c in b3c.items():
        cnpj_roots.setdefault(digits(c['cnpj']), set()).add(root)
    cvm_matched = 0
    for cnpj, r in cvm_susp.items():
        roots = cnpj_roots.get(digits(cnpj), set())
        cvm_matched += bool(roots)
        for root in roots:
            current.setdefault(root, {'since': r['DT_INI_SIT'], 'reason': f"CVM: {r['SIT']} ({r['DENOM_SOCIAL']})", 'page': R.CAD_URL,
                                      'basis': 'CVM cad_cia_aberta SIT'})
    day, fname, status, recs = R.b3_instruments()
    halted = []
    for root, h in sorted(current.items()):
        lines = [x for x in recs if x['Asst'] == root and x['SgmtNm'] == 'CASH' and x['MktNm'] == 'EQUITY-CASH']
        if not lines:
            halted.append({'isin': None, 'ticker': root, 'name': None, 'category': None, 'in_b3_file': False, **h})
            continue
        for x in lines:
            halted.append({'isin': x['ISIN'] or None, 'ticker': x['TckrSymb'], 'name': x['CrpnNm'], 'category': x['SctyCtgyNm'], 'in_b3_file': True, **h})
    eq = [h for h in halted if h['category'] in ('SHARES', 'UNIT')]
    return {'source_url': NEWS_PAGE, 'also': [R.CAD_URL, 'B3 InstrumentsConsolidatedFile ' + day],
            'read_by': 'DERIVED: B3 Plantao de Noticias suspension notices (last %d days) without a later reopening notice; intraday '
                       '"Iminencia de divulgacao de fato relevante" halts only if dated today; plus CVM registrations SUSPENSO(A) - DECISAO ADM '
                       'matched by CNPJ; expanded to B3 cash-market lines' % days,
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'suspension_notices_read': len(susp), 'reopening_notices_read': len(lifts), 'halted_roots': len(current),
            'cvm_suspended_registrations': len(cvm_susp), 'cvm_suspended_matched_to_b3': cvm_matched,
            'count': len(halted), 'count_equity_lines': len(eq), 'language': 'pt', 'halted': halted}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('roots', res['halted_roots'], 'lines', res['count'], 'equity lines', res['count_equity_lines'], 'cvm suspended', res['cvm_suspended_registrations'],
          'matched', res['cvm_suspended_matched_to_b3'], '->', out)
