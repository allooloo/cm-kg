"""Mexico Width 0 roster - listed equity series of Bolsa Mexicana de Valores (ISO 10383 MIC XMEX) and Bolsa Institucional de Valores
(MIC BIVA). Regulator: CNBV (Registro Nacional de Valores).

Sources (both exchanges' own public pages, keyless):
 - BMV "Informacion de Emisora" (https://www.bmv.com.mx/es/emisoras/informacion-de-emisoras): the page's search service
   GET /es/Grupo_BMV/Informacion_de_emisora/_rid/541/_mto/3/_mod/doSearch?idTipoMercado=CGEN_CAPIT&idTipoInstrumento=CGEN_ELAC
   &idTipoEmpresa=<CGEN_ELNA Nacionales | CGEN_ELSP SAPIB | CGEN_ELEX Extranjeras> lists the share issuers (clave, razon social, idEmisora);
   each issuer's profile page https://www.bmv.com.mx/es/emisoras/perfil/<clave>-<idEmisora> lists its equity series with status
   (ACTIVA / SUSPENDIDA ...). BMV's lists carry no ISIN for national shares.
 - BIVA issuer directory (https://www.biva.mx/empresas/emisoras_inscritas/emisoras; JSON API on the same host):
   GET /emisoras/empresas?size=&page= (all issuers listed or secondary-listed on BIVA), GET /emisoras/empresas/<id> (primary exchange
   'bolsa', status), GET /emisoras/empresas/<id>/emisiones (each series with ISIN, tipo de valor, listing mode). ISINs come from here.
Scope: equity series only - BIVA idTipoInstrumento=1 "Acciones, CPOs, UVs" (tipoEmision=equity); BMV Capitales/Acciones of national,
SAPIB and foreign (Extranjeras) issuers. Excluded: SIEFORES (pension fund shares), FIBRAs, CKDs/CERPIs, TRACs/ETFs, warrants, SIC
(Mercado Global, foreign securities quoted in Mexico). One row per series (each series with its own ISIN is its own row). Rows found only
on BMV keep isin null (BMV publishes no ISIN for them on these pages). CPOs are kept (they are the traded equity line of several issuers).
MIC: primary exchange per BIVA's 'bolsa' field (BMV -> XMEX, BIVA -> BIVA); BMV-only rows -> XMEX. ISO 10383 (iso20022.org
ISO10383_MIC.csv): XMEX "BOLSA MEXICANA DE VALORES (MEXICAN STOCK EXCHANGE)", BIVA "BOLSA INSTITUCIONAL DE VALORES".
CFI: neither exchange publishes one on these pages -> blank. LEI: not carried; exact ISIN -> LEI from GLEIF (api.gleif.org
filter[isin]) where GLEIF holds the mapping. No prices are read (BIVA 'accionesEnCirculacion' is dropped too).

fetch() -> {"source_url","read_by","read_at","count","rows":[{"isin","name","mic","lei","ticker","cfi", ...}]}
Usage: python roster.py [--no-lei]   writes samples/roster-<date>.json
"""
import os, sys, re, json, time, html, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
MARKET = 'mx'
BMV = 'https://www.bmv.com.mx'
BMV_PAGE = BMV + '/es/emisoras/informacion-de-emisoras'
BMV_SEARCH = BMV + '/es/Grupo_BMV/Informacion_de_emisora/_rid/541/_mto/3/_mod/doSearch'
BMV_PROFILE = BMV + '/es/emisoras/perfil/{clave}-{id}'
BMV_TYPES = {'CGEN_ELNA': 'Nacionales', 'CGEN_ELSP': 'SAPIB', 'CGEN_ELEX': 'Extranjeras'}
BIVA = 'https://www.biva.mx'
BIVA_PAGE = BIVA + '/empresas/emisoras_inscritas/emisoras'
GLEIF = 'https://api.gleif.org/api/v1/lei-records'
MIC_OF = {'BMV': 'XMEX', 'BIVA': 'BIVA'}
_last = [0.0]


def _get(url, tries=4, **kw):
    """GET paced at <= 2 requests/second with retry/backoff."""
    hdr = {**UA, **kw.pop('headers', {})}
    for i in range(tries):
        wait = 0.55 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.get(url, headers=hdr, timeout=kw.get('timeout', 90), params=kw.get('params'))
            if r.status_code in (429, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(4 * (i + 1))
    return None


class BMVUnavailable(RuntimeError):
    """bmv.com.mx answered its 'Sitio Grupo BMV no disponible' page (site-wide unavailable page, HTTP 200)."""


def _bmv_json(t):
    if '({' not in t:
        if 'no disponible' in t:
            raise BMVUnavailable('bmv.com.mx answered "Sitio Grupo BMV no disponible" (site unavailable page)')
        raise BMVUnavailable('bmv.com.mx answered a non-JSONP page: ' + re.sub(r'\s+', ' ', t[:120]))
    return json.loads(t[t.index('({') + 1:t.rindex('})') + 1])


def bmv_available():
    r = _get(BMV + '/')
    return r is not None and r.status_code == 200 and 'no disponible' not in r.text[:3000]


def bmv_issuers_from_sample():
    """Fallback when bmv.com.mx is unavailable: the BMV issuer ids read by the latest roster run (samples/roster-*.json, field bmv_profile)."""
    sd = os.path.join(HERE, 'samples')
    files = sorted(f for f in os.listdir(sd) if f.startswith('roster-')) if os.path.isdir(sd) else []
    if not files:
        return [], None
    d = json.load(open(os.path.join(sd, files[-1]), encoding='utf-8'))
    out = {}
    for r in d['rows']:
        m = re.search(r'/perfil/(.+)-(\d+)$', r.get('bmv_profile') or '')
        if m:
            out[m.group(1)] = {'clave': m.group(1), 'razonSocial': r['name'], 'idEmisora': int(m.group(2)), 'tipo': r.get('bmv_company_type')}
    return list(out.values()), d['read_at']


def biva_json(path, **params):
    r = _get(BIVA + path, params=params or None, headers={'Accept': 'application/json, text/plain, */*', 'Referer': BIVA_PAGE})
    if r is None or r.status_code != 200:
        return None
    return r.json()


def bmv_issuers():
    """BMV share issuers by company type -> [{clave, razonSocial, idEmisora, tipo}]"""
    out = []
    for code, label in BMV_TYPES.items():
        r = _get(BMV_SEARCH, params={'idTipoMercado': 'CGEN_CAPIT', 'idTipoInstrumento': 'CGEN_ELAC', 'idTipoEmpresa': code, 'idSector': '',
                                     'idSubsector': '', 'idRamo': '', 'idSubramo': ''},
                 headers={'X-Requested-With': 'XMLHttpRequest', 'Referer': BMV_PAGE})
        if r is None or r.status_code != 200:
            raise RuntimeError(f'BMV search did not answer for {code}')
        for x in _bmv_json(r.content.decode('latin-1'))['response']['resultado'] or []:
            out.append({'clave': x['claveEmisora'].strip(), 'razonSocial': (x['razonSocial'] or '').strip(), 'idEmisora': x['idEmisora'], 'tipo': label})
    return out


def _clean(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s))).strip()


def bmv_series(clave, idemisora):
    """Profile page -> (razon social, [{serie, estatus, descripcion}]) of the 'Capitales' series table (the first one on the page)."""
    url = BMV_PROFILE.format(clave=clave, id=idemisora)
    r = _get(url)
    if r is None or r.status_code != 200:
        return None, [], url
    t = r.text
    name = _clean((re.search(r'<h3>(.*?)</h3>', t, re.S) or [None, ''])[1])
    box = t[t.find('id="boxSeries"'):]
    first = box[:box.find('</table>')] if '</table>' in box else ''
    sec = first if ('Serie' in first and 'Estatus' in first) else ''
    out = []
    for tr in re.findall(r'<tr>(.*?)</tr>', sec, re.S):
        tds = [_clean(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if len(tds) == 3:
            out.append({'serie': tds[0], 'estatus': tds[1], 'descripcion': tds[2]})
    return name, out, url


def biva_equity():
    """All BIVA issuers -> equity series with ISIN: [{id, clave, nombre, serie, isin, tipoValor, modoListado, bolsa, estatus}] (cached per day)"""
    fn = os.path.join(CACHE, f'biva_equity_{datetime.date.today():%Y%m%d}.json')
    if os.path.exists(fn):
        d = json.load(open(fn, encoding='utf-8'))
        return d['n'], d['rows']
    n, out = _biva_equity()
    os.makedirs(CACHE, exist_ok=True)
    json.dump({'n': n, 'rows': out}, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
    return n, out


def _biva_equity():
    first = biva_json('/emisoras/empresas', size=400, page=0)
    comps = first['content']
    out = []
    for c in comps:
        em = biva_json(f"/emisoras/empresas/{c['id']}/emisiones", size=200, page=0) or {}
        eq = [e for e in em.get('content', []) if e.get('idTipoInstrumento') == 1]
        if not eq:
            continue
        det = biva_json(f"/emisoras/empresas/{c['id']}") or {}
        for e in eq:
            out.append({'id': c['id'], 'clave': c['clave'].strip(), 'nombre': (det.get('razonSocial') or c['nombre']).strip(), 'serie': (e.get('serie') or '').strip(),
                        'isin': (e.get('isin') or '').strip() or None, 'tipoValor': e.get('tipoValor'), 'tipoInstrumento': e.get('tipoInstrumento'),
                        'modoListado': e.get('modoListado'), 'bolsa': det.get('bolsa'), 'estatus': det.get('estatus'), 'nombre_emision': e.get('nombre')})
    return len(comps), out


def gleif_lei(isins):
    hit = {}
    for isin in isins:
        r = _get(GLEIF, params={'filter[isin]': isin}, headers={'Accept': 'application/vnd.api+json'})
        if r is not None and r.status_code == 200:
            d = r.json().get('data') or []
            if len(d) == 1:
                hit[isin] = d[0]['id']
    return hit


def fetch(lei=True):
    n_biva, beq = biva_equity()
    bmv = bmv_issuers()
    rows, seen = [], set()
    by_key = {(b['clave'], b['serie']): b for b in beq}
    bmv_series_read, bmv_profiles = 0, {}
    for i in bmv:
        name, series, url = bmv_series(i['clave'], i['idEmisora'])
        bmv_profiles[i['clave']] = (name or i['razonSocial'], series, url, i['tipo'])
        bmv_series_read += len(series)
    # rows from BIVA (ISIN-bearing)
    for b in beq:
        prof = bmv_profiles.get(b['clave'])
        bmv_status = next((s['estatus'] for s in (prof[1] if prof else []) if s['serie'] == b['serie']), None)
        rows.append({'isin': b['isin'], 'name': b['nombre'], 'mic': MIC_OF.get(b['bolsa'] or '', 'XMEX' if prof else 'BIVA'), 'lei': '',
                     'ticker': f"{b['clave']} {b['serie']}".strip(), 'cfi': '', 'clave': b['clave'], 'serie': b['serie'],
                     'primary_exchange': b['bolsa'], 'listing_mode_biva': b['modoListado'], 'tipo_valor': b['tipoValor'],
                     'biva_status': b['estatus'], 'bmv_series_status': bmv_status, 'on_bmv_list': bool(prof), 'on_biva_list': True,
                     'isin_source': 'BIVA /emisoras/empresas/%d/emisiones' % b['id'] if b['isin'] else '', 'biva_id': b['id'],
                     'bmv_profile': prof[2] if prof else None, 'lei_source': ''})
        seen.add((b['clave'], b['serie']))
    # BMV-only series (no ISIN published)
    for clave, (name, series, url, tipo) in sorted(bmv_profiles.items()):
        for s in series:
            if (clave, s['serie']) in seen:
                continue
            rows.append({'isin': None, 'name': name, 'mic': 'XMEX', 'lei': '', 'ticker': f"{clave} {s['serie']}".strip(), 'cfi': '', 'clave': clave,
                         'serie': s['serie'], 'primary_exchange': 'BMV', 'listing_mode_biva': None, 'tipo_valor': s['descripcion'], 'biva_status': None,
                         'bmv_series_status': s['estatus'], 'bmv_company_type': tipo, 'on_bmv_list': True, 'on_biva_list': False, 'isin_source': '',
                         'biva_id': None, 'bmv_profile': url, 'lei_source': ''})
    lei_hits = gleif_lei(sorted({r['isin'] for r in rows if r['isin']})) if lei else {}
    for r in rows:
        if r['isin'] in lei_hits:
            r['lei'] = lei_hits[r['isin']]; r['lei_source'] = 'GLEIF ISIN map (api.gleif.org filter[isin])'
    rows.sort(key=lambda r: (r['mic'], r['clave'], r['serie']))
    return {'source_url': BIVA_PAGE + ' (GET ' + BIVA + '/emisoras/empresas, /emisoras/empresas/<id>/emisiones) + ' + BMV_PAGE + ' (doSearch + /es/emisoras/perfil/<clave>-<id>)',
            'read_by': 'BIVA issuer directory JSON (equity series with ISIN, idTipoInstrumento=1) merged with BMV Informacion de Emisora '
                       '(Capitales/Acciones: Nacionales, SAPIB, Extranjeras) series tables; MIC by primary exchange (ISO 10383 XMEX / BIVA)',
            'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'biva_issuers_scanned': n_biva, 'biva_equity_series': len(beq), 'bmv_share_issuers': len(bmv), 'bmv_series_read': bmv_series_read,
            'count': len(rows), 'count_with_isin': sum(1 for r in rows if r['isin']), 'count_without_isin': sum(1 for r in rows if not r['isin']),
            'count_by_mic': {m: sum(1 for r in rows if r['mic'] == m) for m in sorted({r['mic'] for r in rows})},
            'bmv_issuers_not_on_biva': sorted({r['clave'] for r in rows if not r['on_biva_list']}),
            'lei_method': 'GLEIF exact ISIN map (api.gleif.org/api/v1/lei-records?filter[isin]=)' if lei else 'not looked up (--no-lei)',
            'lei_hits': len(lei_hits), 'scope': 'XMEX + BIVA equity series', 'rows': rows}


if __name__ == '__main__':
    res = fetch(lei='--no-lei' not in sys.argv)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'roster-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('count', res['count'], 'with ISIN', res['count_with_isin'], res['count_by_mic'], 'BIVA eq series', res['biva_equity_series'],
          'BMV issuers', res['bmv_share_issuers'], 'not on BIVA', len(res['bmv_issuers_not_on_biva']), 'LEI hits', res['lei_hits'], '->', out)
