"""Mexico halts - official current suspensions on BMV (XMEX) and BIVA.

Three official inputs, all keyless:
 1. BMV Vigilancia de Mercados, "Suspension Intradia" (https://www.bmv.com.mx/es/mercados/suspension-intradia). The page's table is filled
    from GET https://www.bmv.com.mx/es/Grupo_BMV/BmvJsonGeneric?idSitioPagina=10 -> response.suspensiones[] with claveEmision,
    claveSerie, causaSuspension, fechaHoraSuspension, fechaHoraActivacion (lift), nombre (esquema de levantamiento).
    Current = no lift time, or a lift time later than now.
 2. BIVA quotes suspensions, GET https://www.biva.mx/quotes/suspensions (the JSON list behind BIVA's market-information page).
 3. BMV issuer profiles (https://www.bmv.com.mx/es/emisoras/perfil/<clave>-<idEmisora>): each equity series carries a status; series whose
    status is not ACTIVA (e.g. SUSPENDIDA) are listed as standing suspensions. This part is DERIVED from the series status, with no
    cause or start date published on the profile (reason = the status text, since = null).
ISIN for each halted series is taken from BIVA (/emisoras/empresas/isin lookups are not possible by clave, so the roster's BIVA series
map is used: /emisoras/empresas + /emisiones); null when BIVA does not list the series. Reasons are Spanish as published.

fetch() -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page", ...}]}
Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, sys, json, datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roster as R

BMV_SUSP_PAGE = R.BMV + '/es/mercados/suspension-intradia'
BMV_SUSP = R.BMV + '/es/Grupo_BMV/BmvJsonGeneric'
BIVA_SUSP = '/quotes/suspensions'


def _parse_dt(s):
    if not s:
        return None
    for f in ('%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d-%m-%Y %H:%M'):
        try:
            return datetime.datetime.strptime(str(s)[:19], f)
        except ValueError:
            pass
    if isinstance(s, (int, float)):
        return datetime.datetime.fromtimestamp(s / 1000, ZoneInfo('America/Mexico_City')).replace(tzinfo=None)
    return None


def fetch(profiles=True):
    now = datetime.datetime.now(ZoneInfo('America/Mexico_City')).replace(tzinfo=None)
    r = R._get(BMV_SUSP, params={'idSitioPagina': 10}, headers={'X-Requested-With': 'XMLHttpRequest', 'Referer': BMV_SUSP_PAGE})
    bmv_list, bmv_note = None, None
    if r is not None and r.status_code == 200:
        try:
            bmv_list = R._bmv_json(r.content.decode('utf-8', 'replace'))['response'].get('suspensiones') or []
        except R.BMVUnavailable as e:
            bmv_note = str(e)
    else:
        bmv_note = 'no answer'
    bmv_up = bmv_note is None
    biva_list = R.biva_json(BIVA_SUSP)
    n_biva, beq = R.biva_equity()
    isin_of = {(b['clave'], b['serie']): b['isin'] for b in beq}
    name_of = {b['clave']: b['nombre'] for b in beq}
    halted = []
    for s in bmv_list or []:
        lift = _parse_dt(s.get('fechaHoraActivacion'))
        if lift is not None and lift <= now:
            continue
        cl, se = (s.get('claveEmision') or '').strip(), (s.get('claveSerie') or '').strip()
        halted.append({'isin': isin_of.get((cl, se)), 'ticker': f'{cl} {se}'.strip(), 'name': name_of.get(cl), 'since': s.get('fechaHoraSuspension'),
                       'reason': s.get('causaSuspension'), 'page': BMV_SUSP_PAGE, 'lift_scheme': s.get('nombre'), 'until': s.get('fechaHoraActivacion'),
                       'mic': 'XMEX', 'basis': 'BMV Suspension Intradia'})
    for s in biva_list or []:
        cl = str(s.get('emisora') or s.get('clave') or s.get('claveEmisora') or '').strip()
        se = str(s.get('serie') or s.get('claveSerie') or '').strip()
        halted.append({'isin': s.get('isin') or isin_of.get((cl, se)), 'ticker': f'{cl} {se}'.strip() or None, 'name': name_of.get(cl),
                       'since': s.get('fechaSuspension') or s.get('fecha') or s.get('fechaHoraSuspension'), 'reason': s.get('motivo') or s.get('causa') or s.get('causaSuspension'),
                       'page': R.BIVA + BIVA_SUSP, 'mic': 'BIVA', 'basis': 'BIVA quotes/suspensions', 'raw': s})
    series_read, not_active, profile_from = 0, 0, None
    if profiles and not bmv_up:
        # bmv.com.mx down: use the series statuses read from the BMV profiles by the latest roster run (same official pages, earlier read)
        sd = os.path.join(HERE, 'samples')
        files = sorted(f for f in os.listdir(sd) if f.startswith('roster-'))
        if files:
            d = json.load(open(os.path.join(sd, files[-1]), encoding='utf-8'))
            profile_from = f'BMV profiles as read by roster run at {d["read_at"]} ({files[-1]}); bmv.com.mx unavailable at halt run'
            for row in d['rows']:
                st = row.get('bmv_series_status')
                if st is None:
                    continue
                series_read += 1
                if st.upper() != 'ACTIVA':
                    not_active += 1
                    halted.append({'isin': row['isin'], 'ticker': row['ticker'], 'name': row['name'], 'since': None, 'reason': st, 'page': row['bmv_profile'],
                                   'mic': 'XMEX', 'basis': 'BMV profile series status (derived; read %s)' % d['read_at']})
    elif profiles:
        profile_from = 'BMV profiles read live'
        for i in R.bmv_issuers():
            name, series, url = R.bmv_series(i['clave'], i['idEmisora'])
            for s in series:
                series_read += 1
                if s['estatus'].upper() != 'ACTIVA':
                    not_active += 1
                    halted.append({'isin': isin_of.get((i['clave'], s['serie'])), 'ticker': f"{i['clave']} {s['serie']}".strip(), 'name': name or i['razonSocial'],
                                   'since': None, 'reason': s['estatus'], 'page': url, 'mic': 'XMEX', 'basis': 'BMV profile series status (derived)'})
    return {'source_url': BMV_SUSP_PAGE, 'also': [BMV_SUSP + '?idSitioPagina=10', R.BIVA + BIVA_SUSP, R.BMV + '/es/emisoras/perfil/<clave>-<id>'],
            'read_by': 'BMV Suspension Intradia JSON (current = no lift or lift in the future) + BIVA /quotes/suspensions + DERIVED standing '
                       'suspensions from BMV profile series status not ACTIVA',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'bmv_intraday_rows': None if bmv_list is None else len(bmv_list), 'biva_rows': None if biva_list is None else len(biva_list),
            'bmv_available_at_run': bmv_up, 'bmv_note': bmv_note, 'bmv_profile_statuses_from': profile_from,
            'bmv_profile_series_read': series_read, 'bmv_series_not_active': not_active,
            'count': len(halted), 'language': 'es', 'halted': halted}


if __name__ == '__main__':
    res = fetch(profiles='--no-profiles' not in sys.argv)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    print('bmv intraday', res['bmv_intraday_rows'], 'biva', res['biva_rows'], 'profile series', res['bmv_profile_series_read'],
          'not active', res['bmv_series_not_active'], 'halted', res['count'], '->', out)
