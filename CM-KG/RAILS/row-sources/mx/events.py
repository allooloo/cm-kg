"""Mexico Width 1 events - issuer regulated information as published by the issuer's primary exchange (BMV EMISNET / BIVA).

Issuers file with CNBV and the exchange (BMV through EMISNET, BIVA through its DIV system); each exchange publishes the filings per issuer:
 - BMV (primary 'BMV'): the issuer pages filled from EMISNET, server-rendered, keyless:
     https://www.bmv.com.mx/es/emisoras/eventosrelevantes/<clave>-<idEmisora>-CGEN_CAPIT    (eventos relevantes, calificadora, comunicados BMV)
     https://www.bmv.com.mx/es/emisoras/informacionfinanciera/<clave>-<idEmisora>-CGEN_CAPIT (estados financieros, constancias, reportes anuales)
     https://www.bmv.com.mx/es/emisoras/informcioncorporativa/<clave>-<idEmisora>-CGEN_CAPIT (avisos de derechos, asambleas, recompras, ...)
   Each page is an accordion of sections; type = the Spanish section heading as published; type_en = the heading of the same section on
   BMV's own English page (https://www.bmv.com.mx/en/issuers/relevantevents|financialinformation|corporativeinformation/...), matched by
   position; null when the two pages do not have the same sections. title = the 'ASUNTO' / 'NOMBRE' cell exactly as published.
   The financial-information page shows only the latest document per section.
 - BIVA (primary 'BIVA'): GET https://www.biva.mx/emisoras/banco-informacion?empresa=<id>&tipoInformacion=<id>&fechaInicio=&fechaFin=
   (the 'Banco de informacion' page's JSON API). type = the category name from /emisoras/banco-informacion/tipo-informacion;
   type_en = null (BIVA publishes the category table in Spanish only). title = tipoDocumento as listed.
Key resolution: ISIN -> https://www.biva.mx/emisoras/empresas/isin/<ISIN> (clave, primary exchange 'bolsa', BIVA id); clave -> BMV idEmisora
from BMV's issuer search (Capitales). A BMV clave (e.g. AMX) is accepted directly.
Dates: BMV pages are Mexico City local time (marked +local(America/Mexico_City)); BIVA gives epoch ms (UTC).

fetch(isin_or_issuer, since) -> [{"date","type","type_en","title","url","source", ...}]
Usage: python events.py [ISIN|clave ...]   (default: three large issuers) writes samples/events-<date>.json
"""
import os, sys, re, json, html, datetime
from urllib.parse import urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roster as R

TABS = [('eventosrelevantes', 'relevantevents'), ('informacionfinanciera', 'financialinformation'), ('informcioncorporativa', 'corporativeinformation')]
ES_URL = R.BMV + '/es/emisoras/{tab}/{clave}-{id}-CGEN_CAPIT'
EN_URL = R.BMV + '/en/issuers/{tab}/{clave}-{id}-CGEN_CAPIT'
SKIP_H2 = ('Usuarios Registrados', 'Reg', 'Proporciona', 'Cambiar', 'Register', 'Introduce')
MONTHS = {'ene': 1, 'jan': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'aug': 8, 'sep': 9, 'oct': 10,
          'nov': 11, 'dic': 12, 'dec': 12}
_mem = {}


def _date(s):
    s = s.strip()
    m = re.match(r'(\d{1,2})-(\d{1,2})-(\d{4})(?:\s+(\d{1,2}):(\d{2}))?', s)
    if m:
        d, mo, y, hh, mm = m.groups()
    else:
        m = re.match(r'(\d{1,2})-([A-Za-z]{3})-(\d{4})(?:\s+(\d{1,2}):(\d{2}))?', s)
        if not m or m.group(2).lower() not in MONTHS:
            return None
        d, mo, y, hh, mm = m.group(1), MONTHS[m.group(2).lower()], m.group(3), m.group(4), m.group(5)
    try:
        return datetime.datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0))
    except ValueError:
        return None


def _sections(t):
    """accordion <li><h2>label</h2> ... <table> rows -> [(label, [(date_text, title, href)])]"""
    i = t.find('accordion-area')
    if i < 0:
        return []
    body = t[i:]
    parts = re.split(r'<h2>(.*?)</h2>', body, flags=re.S)
    out = []
    for k in range(1, len(parts), 2):
        label = R._clean(parts[k])
        if not label or label.startswith(SKIP_H2):
            continue
        rows = []
        tb = parts[k + 1]
        tb = tb[:tb.find('</table>')] if '</table>' in tb else ''
        for tr in re.findall(r'<tr>(.*?)</tr>', tb, re.S):
            tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
            if len(tds) < 2:
                continue
            href = re.search(r'href="([^"]+)"', tr)
            rows.append((R._clean(tds[0]), R._clean(tds[1]), href.group(1) if href else None))
        out.append((label, rows))
    return out


def _bmv_ids():
    if 'bmv' not in _mem:
        try:
            lst = R.bmv_issuers(); _mem['bmv_from'] = 'BMV issuer search'
        except (R.BMVUnavailable, RuntimeError):
            lst, at = R.bmv_issuers_from_sample(); _mem['bmv_from'] = f'roster sample read at {at} (bmv.com.mx unavailable)'
        _mem['bmv'] = {i['clave']: i for i in lst}
    return _mem['bmv']


def _bmv_up():
    if 'up' not in _mem:
        _mem['up'] = R.bmv_available()
    return _mem['up']


def resolve(key):
    key = key.strip()
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', key):
        d = R.biva_json('/emisoras/empresas/isin/' + key) or {}
        clave, bolsa, bid = (d.get('clave') or '').strip(), d.get('bolsa'), d.get('id')
        how = 'BIVA /emisoras/empresas/isin/' + key if clave else 'unresolved'
    else:
        clave, bolsa, bid, how = key.upper(), None, None, 'clave given'
        j = R.biva_json('/emisoras/empresas', clave=clave, size=10, page=0) or {}
        hit = [c for c in j.get('content', []) if c['clave'].strip() == clave]
        if hit:
            bid = hit[0]['id']
            bolsa = (R.biva_json(f'/emisoras/empresas/{bid}') or {}).get('bolsa')
    b = _bmv_ids().get(clave)
    if bolsa is None:
        bolsa = 'BMV' if b else None
    return {'clave': clave, 'primary': bolsa, 'biva_id': bid, 'bmv_id': b['idEmisora'] if b else None, 'how': how}


def _bmv_events(clave, idem, since):
    out = []
    for es_tab, en_tab in TABS:
        es_url = ES_URL.format(tab=es_tab, clave=clave, id=idem)
        r = R._get(es_url)
        if r is None or r.status_code != 200:
            continue
        es = _sections(r.text)
        e = R._get(EN_URL.format(tab=en_tab, clave=clave, id=idem))
        en = _sections(e.text) if e is not None and e.status_code == 200 else []
        same = len(en) == len(es) and all(len(a[1]) == len(b[1]) for a, b in zip(es, en))
        for n, (label, rows) in enumerate(es):
            for dtx, title, href in rows:
                d = _date(dtx)
                if d is None or d.date() < since:
                    continue
                out.append({'date': d.strftime('%Y-%m-%dT%H:%M') + '+local(America/Mexico_City)', 'type': label,
                            'type_en': en[n][0] if same else None, 'title': title or None,
                            'url': urljoin(es_url, html.unescape(href)) if href else es_url, 'source': f'BMV issuer page ({es_tab}, EMISNET)',
                            'page': es_url, 'channel': 'BMV EMISNET'})
    return out


def _biva_events(bid, since):
    if 'cats' not in _mem:
        _mem['cats'] = R.biva_json('/emisoras/banco-informacion/tipo-informacion') or []
    out, seen = [], set()
    today = datetime.date.today()
    for cat in _mem['cats']:
        page = 0
        while True:
            j = R.biva_json('/emisoras/banco-informacion', size=100, page=page, empresa=bid, tipoInformacion=cat['id'],
                            fechaInicio=since.isoformat(), fechaFin=today.isoformat())
            if not j:
                break
            for x in j.get('content', []):
                if x['id'] in seen:
                    continue
                seen.add(x['id'])
                d = datetime.datetime.fromtimestamp(x['fechaPublicacion'] / 1000, datetime.timezone.utc)
                if d.date() < since:
                    continue
                path = x.get('nombreArchivo') or ''
                out.append({'date': d.strftime('%Y-%m-%dT%H:%M:%SZ'), 'type': cat['nombre'], 'type_en': None, 'title': x.get('tipoDocumento'),
                            'url': urljoin(R.BIVA, path) if path else None, 'source': 'BIVA banco de informacion (biva.mx /emisoras/banco-informacion)',
                            'doc_type': x.get('docType'), 'biva_doc_id': x['id'], 'channel': 'BIVA'})
            if page + 1 >= (j.get('totalPages') or 0):
                break
            page += 1
    return out


def fetch(isin_or_issuer, since):
    """since: 'YYYY-MM-DD' or date. Returns newest first."""
    since = since if isinstance(since, datetime.date) else datetime.date.fromisoformat(str(since)[:10])
    who = resolve(isin_or_issuer)
    if who['primary'] == 'BIVA' and who['biva_id']:
        ev = _biva_events(who['biva_id'], since)
    elif who['bmv_id'] and _bmv_up():
        ev = _bmv_events(who['clave'], who['bmv_id'], since)
    elif who['biva_id']:
        ev = _biva_events(who['biva_id'], since)
        if who['bmv_id'] or who['primary'] == 'BMV':  # BMV-primary issuer read from BIVA because bmv.com.mx is down
            for e in ev:
                e['channel'] = 'BIVA (fallback: bmv.com.mx answered "Sitio Grupo BMV no disponible")'
    else:
        ev = []
    for e in ev:
        e['resolved_by'] = who['how']
    ev.sort(key=lambda e: e['date'], reverse=True)
    return ev


if __name__ == '__main__':
    tests = sys.argv[1:] or ['MX01AM050019', 'MX01WA000038', 'MXP370711014']
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since = today - datetime.timedelta(days=365)
    res = {'source_url': R.BMV + '/es/emisoras/{eventosrelevantes|informacionfinanciera|informcioncorporativa}/<clave>-<id>-CGEN_CAPIT ; '
                         + R.BIVA + '/emisoras/banco-informacion', 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'since': since.isoformat(), 'key_required': False, 'bmv_available_at_run': _bmv_up(), 'issuers': {}}
    for q in tests:
        ev = fetch(q, since)
        res['issuers'][q] = {'resolved': resolve(q), 'count': len(ev),
                             'by_type': {k: sum(1 for e in ev if e['type'] == k) for k in sorted({e['type'] for e in ev})},
                             'type_en_filled': sum(1 for e in ev if e['type_en']), 'events': ev}
        print(q, res['issuers'][q]['resolved'], len(ev), res['issuers'][q]['by_type'], flush=True)
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'events-{today.isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', out)
