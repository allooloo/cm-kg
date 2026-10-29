"""ES halts: current trading suspensions on the Spanish exchanges (XMAD) and BME Growth (GROW), DERIVED from CNMV filings.
Spain publishes no machine-readable "currently suspended" list. Suspensions are decided by the CNMV (art. 21 LMVSI) -- or for BME Growth by
BME Growth -- and are published on the CNMV regulated-information stores under the category
"Sobre suspensiones, levantamientos y exclusiones de negociacion":
  IP  : https://www.cnmv.es/portal/Informacion-Privilegiada/Consulta-IP   (category checkbox 9;  CNMV's own suspension / lift decisions)
  OIR : https://www.cnmv.es/portal/Otra-Informacion-Relevante/Consulta-OIR (category checkbox 25; issuer / market notices of the same)
  (ASP.NET form POST -> GET result page Resultado-IP / Resultado-OIR?tipos=..&fechaDesde=..&fechaHasta=..&page=n; public, no key)
Rule: per issuer, the latest notice in the window decides. A suspension notice ("suspender la negociacion", "acuerda la suspension") is open,
unless it names a same-session lift time ("El levantamiento tendra lugar ...", "se levantara ...") -- a timed news-pending pause. A lift
("levantar la suspension", "levantamiento de la suspension") or an exclusion ("exclusion de negociacion" -- delisting) closes it.
An open issuer is "halted" when its share is still in the FIRDS roster (samples/roster-*.json, matched by issuer name); otherwise it is
listed under halted_not_in_roster. Second source: the BME ShareDetailsInfo "active" flag for every roster ISIN (as seen 2026-10-24: blank =
trading, "S" = suspended, "C" = closed/excluded); an ISIN flagged "S" with no CNMV notice in the window is added with source "BME ShareDetailsInfo status flag".

fetch(days=365) -> {"source_url", "read_by", "read_at", "count", "halted": [{"isin", "ticker", "name", "since", "reason", "page"}], ...}
"""
import datetime as dt, glob, html, json, os, re, sys, time, unicodedata
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
FORMS = {'IP': ('https://www.cnmv.es/portal/Informacion-Privilegiada/Consulta-IP', 9),
         'OIR': ('https://www.cnmv.es/portal/Otra-Informacion-Relevante/Consulta-OIR', 25)}
P = 'ctl00$ContentPrincipal$'
BME = 'https://apiweb.bolsasymercados.es/Market/v1/EQ/ShareDetailsInfo'
REC = re.compile(r'liFechaRegistro" class="fecha-con-hora">\s*([\d/]+)\s*</li>\s*<li[^>]*liHora" class="time">\s*([\d:]*)\s*</li>.*?'
                 r'spanTituloCabecera" class="tit-small">([^<]*)<.*?descripcionSubtituloCabecera"[^>]*>([^<]*)<.*?'
                 r'subtituloRegistroEnlace" href="([^"]*)"[^>]*><span[^>]*>(.*?)</span>', re.S)


def _fold(s):
    s = unicodedata.normalize('NFKD', html.unescape(s or '')).encode('ascii', 'ignore').decode().lower()
    return s


def _norm(s):
    s = re.sub(r'[^a-z0-9 ]', ' ', _fold(s))
    s = re.sub(r'\b(s a|sa|s l|sl|socimi|sociedad anonima|grupo|group|holdings?|the|y|de|del|la|el)\b', ' ', s)
    return ' '.join(s.split())


def _req(s, method, url, **kw):
    for i in range(4):
        try:
            r = s.request(method, url, timeout=120, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            r.raise_for_status(); return r
        except requests.RequestException:
            if i == 3:
                raise
            time.sleep(4 * (i + 1))


def notices(days):
    a = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=days)
    b = dt.datetime.now(dt.timezone.utc).date()
    out, urls = [], {}
    for store, (form, box) in FORMS.items():
        s = requests.Session(); s.headers.update(UA)
        r = _req(s, 'GET', form)
        f = dict(re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', r.text))
        f.update({P + 'wucCodigoLEI$txtCodigoLEI': '', P + 'wucNombreEntidad$txtDenominacion': '', P + 'wucFechas$ult_dias': '',
                  P + 'wucTipoEntidad$lstTipoentidad2$%d' % box: 'on', P + 'wucFechas$fecha_desde': a.isoformat(),
                  P + 'wucFechas$fecha_hasta': b.isoformat(), P + 'buttonOk': 'Buscar'})
        r = _req(s, 'POST', form, data=f)
        base, page, n = r.url.split('&page=')[0], 0, 1
        urls[store] = re.sub(r'tipos=[^&]+', 'tipos=<category blob>', base)
        text = r.text
        while True:
            for d, t, issuer, cat, href, title in REC.findall(text):
                out.append({'store': store, 'date': dt.datetime.strptime(d, '%d/%m/%Y').date().isoformat() + (' ' + t if t else ''),
                            'issuer': html.unescape(issuer).strip(), 'category': html.unescape(cat).strip(),
                            'title': html.unescape(re.sub(r'<[^>]+>', '', title)).strip(), 'url': html.unescape(href)})
            m = re.search(r'P[aá]gina \d+ de (\d+)', text)
            n = int(m.group(1)) if m else 1
            page += 1
            if page >= n:
                break
            text = _req(s, 'GET', base + '&page=%d' % page).text
            time.sleep(0.3)
    return out, urls


def classify(title):
    t = _fold(title)
    if re.search(r'exclusi[o]n de (la )?negociaci|excluir de (la )?negociaci|acuerda la exclusi', t):
        return 'excluded'
    if re.search(r'levant(ar|a|amiento de) (la |de la )?suspensi|reanud', t):
        return 'lifted'
    if re.search(r'suspend|suspensi', t):
        if re.search(r'(el levantamiento tendra lugar|se levantara|levantamiento.{0,40}(a las|hora))', t):
            return 'timed'
        return 'suspended'
    return None


def _roster():
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    return json.load(open(files[-1], encoding='utf-8'))['rows'] if files else []


def fetch(days=365):
    ns, urls = notices(days)
    state = {}
    for n in sorted(ns, key=lambda x: x['date']):
        c = classify(n['title'])
        if c:
            state[_norm(n['issuer'])] = dict(n, status=c)
    rows = _roster()
    halted, missing = [], []
    for k, s in state.items():
        if s['status'] != 'suspended':
            continue
        hits = [r for r in rows if _norm(r['name']) == k]
        if not hits:
            missing.append({'name': s['issuer'], 'since': s['date'], 'reason': s['title'], 'page': s['url'], 'store': s['store']})
            continue
        for r in hits:
            act = None
            try:
                j = requests.get(BME, params={'isin': r['isin'], 'language': 'es'}, headers=UA, timeout=60).json()
                act = j.get('active')
            except Exception:
                pass
            halted.append({'isin': r['isin'], 'ticker': r.get('ticker'), 'name': r['name'], 'mic': r['mic'], 'since': s['date'], 'reason': s['title'],
                           'page': s['url'], 'store': s['store'], 'bme_active_flag': act, 'source': 'CNMV ' + s['store'] + ' suspension notice (derived)'})
    # second pass: the exchange's own per-share status flag over the whole roster (BME ShareDetailsInfo active == "S")
    have = {h['isin'] for h in halted}
    flagged = 0
    for r in rows:
        try:
            j = requests.get(BME, params={'isin': r['isin'], 'language': 'es'}, headers=UA, timeout=60).json()
        except Exception:
            continue
        time.sleep(0.1)
        if (j.get('active') or '').strip().upper() == 'S':
            flagged += 1
            if r['isin'] not in have:
                halted.append({'isin': r['isin'], 'ticker': r.get('ticker'), 'name': r['name'], 'mic': r['mic'], 'since': None,
                               'reason': 'BME share status flag active=S (suspended); no CNMV suspension notice in the window',
                               'page': BME + '?isin=' + r['isin'], 'store': None, 'bme_active_flag': 'S', 'source': 'BME ShareDetailsInfo status flag'})
    return {'source_url': ' | '.join(urls.values()) + ' | ' + BME + '?isin=<roster ISIN>', 'read_by': 'eu-sources/es/halt.py', 'bme_flagged_S': flagged,
            'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'window_days': days, 'notices_read': len(ns),
            'count': len(halted), 'halted': halted, 'halted_not_in_roster': missing,
            'closed_in_window': [{'name': s['issuer'], 'status': s['status'], 'last': s['date'], 'reason': s['title']} for s in state.values() if s['status'] != 'suspended']}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out = fetch()
    p = os.path.join(HERE, 'samples', 'halts-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('notices', out['notices_read'], 'halted', out['count'], 'not_in_roster', len(out['halted_not_in_roster']), 'closed', len(out['closed_in_window']), '->', p)
    for h in out['halted']:
        print('  HALT', h['isin'], h['ticker'], h['name'], h['since'], h['bme_active_flag'], h['reason'][:100])
    for h in out['halted_not_in_roster']:
        print('  open-not-in-roster', h['name'], h['since'], h['reason'][:100])
    for h in out['closed_in_window']:
        print('  closed', h['status'], h['name'], h['last'], h['reason'][:80])

# DAY ORDER 4: the read-by label of record (the node's halt flag names its source, not a file)
_fetch_src = fetch
def fetch():
    h = _fetch_src(); h["read_by"] = "CNMV regulated information (trading suspensions and lifts; BME Growth notices)"; return h
