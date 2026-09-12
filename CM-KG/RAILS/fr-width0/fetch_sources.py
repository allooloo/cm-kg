"""Step 1 — pull the French roster and registry references into raw/ (a junction to the open pond drop POND\\fr-cm-kg\\width0\\<date>\\). Public, no login.
  ESMA FIRDS ............... the EU Financial Instruments Reference Data System full equity files (FULINS_E_<date>_<n>of<m>.zip, weekly, listed by the
                             registers.esma.europa.eu Solr API): every instrument admitted to trading on an EU venue with ISIN, issuer LEI, full and short
                             name, CFI, currency, first trading date and admission date, per trading venue (MIC). Euronext Paris = XPAR, Euronext Growth
                             Paris = ALXP, Euronext Access Paris = XMLI. Euronext's own list pages sit behind an anti-bot form (HITL note).
  AMF BDIF ................. https://bdif.amf-france.org/back/api/v1/informations (the regulatory-information database; 'societes' carries the filer
                             identity: AMF token RS…, raison sociale) — the last 10,000 items are pageable; used to index filer names to AMF tokens
  recherche-entreprises .... https://recherche-entreprises.api.gouv.fr/search (the French State's public company search, no key): SIREN, legal name,
                             legal form, NAF code, registered office, status — per issuer in siren_match.py
  GLEIF ISIN-to-LEI file ... reused from the day's drop when present (FIRDS already carries the issuer LEI)"""
import requests, json, os, re, sys, time, zipfile, io
import xml.etree.ElementTree as ET
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
os.makedirs('raw', exist_ok=True)
MICS = {'XPAR': 'Euronext Paris', 'ALXP': 'Euronext Growth Paris', 'XMLI': 'Euronext Access Paris'}
def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=600, **kw)
            if r.status_code in (429, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
def firds_equity_files():
    j = get('https://registers.esma.europa.eu/solr/esma_registers_firds_files/select', params={'q': '*', 'fq': 'file_type:FULINS', 'wt': 'json', 'start': 0, 'rows': 60, 'sort': 'publication_date desc'}).json()
    docs = j['response']['docs']; latest = docs[0]['publication_date']
    return latest, [d for d in docs if d['publication_date'] == latest and '_E_' in d['file_name']]
def firds_rows(mics):
    latest, files = firds_equity_files(); rows = []; n = 0
    for d in files:
        z = zipfile.ZipFile(io.BytesIO(get(d['download_link']).content)); name = z.namelist()[0]
        for ev, el in ET.iterparse(z.open(name), events=('end',)):
            if el.tag.endswith('}RefData'):
                n += 1; ns = el.tag.split('}')[0] + '}'
                g = el.find(ns + 'FinInstrmGnlAttrbts'); tv = el.find(ns + 'TradgVnRltdAttrbts'); mic = tv.findtext(ns + 'Id') if tv is not None else ''
                if mic in mics:
                    rows.append({'isin': g.findtext(ns + 'Id'), 'full_name': g.findtext(ns + 'FullNm'), 'short_name': g.findtext(ns + 'ShrtNm'), 'cfi': g.findtext(ns + 'ClssfctnTp'), 'currency': g.findtext(ns + 'NtnlCcy'), 'mic': mic, 'lei': el.findtext(ns + 'Issr'),
                                 'first_trade': (tv.findtext(ns + 'FrstTradDt') or '')[:10], 'admission': (tv.findtext(ns + 'AdmssnApprvlDtByIssr') or '')[:10], 'termination': (tv.findtext(ns + 'TermntnDt') or '')[:10], 'file': d['file_name']})
                el.clear()
        print('FIRDS', d['file_name'], 'records so far', n, 'kept', len(rows), flush=True)
    return latest, files, rows
if __name__ == '__main__':
    latest, files, rows = firds_rows(set(MICS))
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'publication_date': latest[:10], 'files': [d['download_link'] for d in files], 'src': 'https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_firds (FIRDS full equity files ' + latest[:10] + ')', 'mics': MICS, 'rows': rows}, open('raw/firds_equities.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('FIRDS rows', len(rows), 'shares', sum(1 for r in rows if (r['cfi'] or '').startswith('ES')), flush=True)
    soc = {}; From = 0
    while From < 10000:
        r = get('https://bdif.amf-france.org/back/api/v1/informations', params={'From': From, 'Size': 200})
        if r is None or r.status_code != 200: break
        res = r.json().get('result') or []
        for it in res:
            for s in it.get('societes') or []:
                if s.get('jeton'): soc.setdefault(s['jeton'], {'jeton': s['jeton'], 'raison_sociale': s.get('raisonSociale'), 'n_items': 0, 'last': ''}); soc[s['jeton']]['n_items'] += 1; soc[s['jeton']]['last'] = max(soc[s['jeton']]['last'], (it.get('datePublication') or '')[:10])
        if len(res) < 200: break
        From += 200
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'src': 'https://bdif.amf-france.org/ (BDIF regulatory-information database, last 10,000 items, filer tokens)', 'societes': list(soc.values())}, open('raw/bdif_societes.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('BDIF filers indexed', len(soc), flush=True)
    print('FETCH DONE', flush=True)
