"""Step 1 — pull the Dutch roster and registry references into raw/ (a junction to the open pond drop POND\\nl-cm-kg\\width0\\<date>\\). Public, no login.
  ESMA FIRDS ............... the EU Financial Instruments Reference Data System full equity files (weekly): every instrument admitted to trading on Euronext
                             Amsterdam (XAMS) and Euronext Growth Amsterdam (TNLA) with ISIN, issuer LEI, names, CFI, currency, first trading / admission
                             dates. Euronext's own list pages sit behind an anti-bot form (HITL note).
  KVK ...................... the Dutch trade register API is paid (401 without a key — HITL); the KVK number comes from the GLEIF LEI record's registeredAs
                             (RA000463 = KVK) and the link column is the public KVK search entry
  AFM ...................... the AFM registers (issuers, notifications) are JavaScript pages without a public export found; Width 1 reads the notification
                             registers per issuer (HITL note for a bulk export)
  GLEIF ISIN-to-LEI file ... reused from the day's drop when present (FIRDS already carries the issuer LEI)"""
import requests, json, os, re, sys, time, zipfile, io
import xml.etree.ElementTree as ET
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', 'Accept': 'application/json'}
os.makedirs('raw', exist_ok=True)
MICS = {'XAMS': 'Euronext Amsterdam', 'TNLA': 'Euronext Growth Amsterdam'}
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
        cache = os.path.join(os.environ.get('FIRDS_CACHE', 'raw'), d['file_name'])
        data = open(cache, 'rb').read() if os.path.exists(cache) else get(d['download_link']).content
        if not os.path.exists(cache): open(cache, 'wb').write(data)
        z = zipfile.ZipFile(io.BytesIO(data)); name = z.namelist()[0]
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
    print('FETCH DONE', flush=True)
