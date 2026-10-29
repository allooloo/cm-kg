"""ES events (Width 1): issuer filings from the CNMV, Spain's national regulator and officially appointed mechanism for regulated information.
Two stores, both public HTML, no key:
  Informacion privilegiada (IP):      https://www.cnmv.es/portal/Informacion-Privilegiada/Resultado-IP?lei=<LEI>&fechaDesde=dd/mm/yyyy&fechaHasta=dd/mm/yyyy&page=<n>
  Otra informacion relevante (OIR):   https://www.cnmv.es/portal/Otra-Informacion-Relevante/Resultado-OIR?lei=<LEI>&fechaDesde=..&fechaHasta=..&page=<n>
  (the GET result pages behind the search forms Consulta-IP / Consulta-OIR; 10 records per page, page=0..N-1, "Pagina 1 de N")
Each record: registration date + time, CNMV category as filed ("Sobre resultados", "Sobre instrumentos financieros", ...), title as filed
(Spanish, as filed by the issuer), document link (cnmv.es/webservices/verdocumento/ver?t={guid}), "Numero de registro".

ISIN -> LEI: the FIRDS issuer LEI from the latest samples/roster-*.json (an LEI may also be passed directly).

fetch(isin_or_lei, since) -> [{"date", "type", "title", "url", "source", "store", "register_no", "issuer"}]
  "type" = CNMV category as filed; "store" = "IP" or "OIR".
Run: python events.py  -> samples/events-<date>.json for Iberdrola, Banco Santander, Inditex.
"""
import datetime as dt, glob, html, json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
STORES = {'IP': ('https://www.cnmv.es/portal/Informacion-Privilegiada/Resultado-IP', 'CNMV Informacion privilegiada'),
          'OIR': ('https://www.cnmv.es/portal/Otra-Informacion-Relevante/Resultado-OIR', 'CNMV Otra informacion relevante')}
REC = re.compile(r'liFechaRegistro" class="fecha-con-hora">\s*([\d/]+)\s*</li>\s*<li[^>]*liHora" class="time">\s*([\d:]*)\s*</li>.*?'
                 r'spanTituloCabecera" class="tit-small">([^<]*)<.*?descripcionSubtituloCabecera"[^>]*>([^<]*)<.*?'
                 r'subtituloRegistroEnlace" href="([^"]*)"[^>]*><span[^>]*>(.*?)</span>(.*?)(?=elementoPrimerNivel"|</ul>\s*</article>|$)', re.S)


def _get(url, params, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            r.raise_for_status(); return r.text
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(4 * (i + 1))


def parse(page):
    out = []
    for d, t, issuer, cat, href, title, tail in REC.findall(page):
        reg = re.search(r'N[uú]mero de registro:\s*(\d+)', tail)
        day = dt.datetime.strptime(d, '%d/%m/%Y').date().isoformat()
        out.append({'date': day + (' ' + t if t else ''), 'type': html.unescape(cat).strip(), 'title': html.unescape(re.sub(r'<[^>]+>', '', title)).strip(),
                    'url': html.unescape(href), 'issuer': html.unescape(issuer).strip(), 'register_no': reg.group(1) if reg else None})
    pages = re.search(r'P[aá]gina \d+ de (\d+)', page)
    return out, int(pages.group(1)) if pages else 1


def lei_for(isin_or_lei):
    q = (isin_or_lei or '').strip().upper()
    if re.fullmatch(r'[A-Z0-9]{18}\d{2}', q):
        return q
    files = sorted(glob.glob(os.path.join(HERE, 'samples', 'roster-*.json')))
    for r in (json.load(open(files[-1], encoding='utf-8'))['rows'] if files else []):
        if r['isin'] == q and r.get('lei'):
            return r['lei']
    return None


def fetch(isin_or_lei, since=None):
    a = dt.date.fromisoformat(since) if since else dt.date.today() - dt.timedelta(days=365)
    b = dt.datetime.now(dt.timezone.utc).date()
    lei = lei_for(isin_or_lei)
    if not lei:
        return []
    out = []
    for store, (url, label) in STORES.items():
        page, n = 0, 1
        while page < n:
            recs, n = parse(_get(url, {'lei': lei, 'fechaDesde': a.strftime('%d/%m/%Y'), 'fechaHasta': b.strftime('%d/%m/%Y'), 'page': page}))
            for r in recs:
                out.append({'date': r['date'], 'type': r['type'], 'title': r['title'], 'url': r['url'], 'source': label, 'store': store,
                            'register_no': r['register_no'], 'issuer': r['issuer'], 'lei': lei})
            page += 1
            time.sleep(0.3)
    out.sort(key=lambda e: e['date'], reverse=True)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    since = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=365)).isoformat()
    tests = ['ES0144580Y14', 'ES0113900J37', 'ES0148396007']   # Iberdrola, Banco Santander, Inditex
    res = {}
    for t in tests:
        ev = fetch(t, since)
        res[t] = {'lei': lei_for(t), 'count': len(ev), 'by_store': {s: sum(1 for e in ev if e['store'] == s) for s in STORES}, 'events': ev}
        print(t, res[t]['lei'], len(ev), res[t]['by_store'], (ev[0]['date'], ev[0]['type'], ev[0]['title'][:80]) if ev else '')
    out = {'source_url': ' | '.join(u for u, _ in STORES.values()), 'read_by': 'eu-sources/es/events.py',
           'read_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'since': since, 'issuers': res}
    p = os.path.join(HERE, 'samples', 'events-' + dt.datetime.now(dt.timezone.utc).date().isoformat() + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('->', p)
