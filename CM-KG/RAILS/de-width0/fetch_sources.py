"""Step 1 — pull the German roster and registry references into raw/ (a junction to the open pond drop POND\\de-cm-kg\\width0\\<date>\\). Public, no login.
  Xetra all tradable instruments ... https://www.xetra.com/resource/blob/1528/6f0fdd1e9ac5f3adb42e9ba7d6bb96b0/data/allTradableInstruments.csv (Deutsche Börse's
                                     daily list: instrument name, ISIN, WKN, mnemonic, instrument type CS/ETF/ETN/ETC, product assignment group = DAX / MDAX / SDAX /
                                     TecDAX / DEUTSCHLAND / country groups, designated sponsor; tick-size and price columns dropped at write)
  Deutsche Börse listed companies .. https://www.deutsche-boerse-cash-market.com/dbcm-en/instruments-statistics/statistics/listed-companies (JavaScript page; the
                                     Regulated Market / Scale split is not machine-readable there and the Börse Frankfurt API refuses plain clients (403 CORS) — HITL note)
  GLEIF registration authorities ... https://www.gleif.org RA list (RA code → register name, e.g. the Amtsgericht that keeps the Handelsregister sheet) — used to name the
                                     court behind an LEI record's registeredAt
  GLEIF ISIN-to-LEI file ........... https://mapping.gleif.org/api/v2/isin-lei/latest"""
import requests, json, os, re, sys, time, csv, io
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
os.makedirs('raw', exist_ok=True)
XETRA = 'https://www.xetra.com/resource/blob/1528/6f0fdd1e9ac5f3adb42e9ba7d6bb96b0/data/allTradableInstruments.csv'
KEEP = ['Product Status', 'Instrument Status', 'Instrument', 'ISIN', 'Product ID', 'Instrument ID', 'WKN', 'Mnemonic', 'MIC Code', 'Trading Model Type', 'Product Assignment Group', 'Product Assignment Group Description', 'Designated Sponsor', 'Instrument Type', 'Reporting Market', 'Market Segment', 'Country', 'Home Market', 'Currency', 'Trading Currency', 'Segment']
def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=180, **kw)
            if r.status_code in (429, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
if __name__ == '__main__':
    r = get(XETRA); text = r.content.decode('utf-8', errors='replace'); lines = text.splitlines()
    date_line = lines[1] if len(lines) > 1 else ''
    rd = csv.reader(io.StringIO('\n'.join(lines[2:])), delimiter=';'); hdr = [h.strip() for h in next(rd)]
    keep_ix = [(h, hdr.index(h)) for h in KEEP if h in hdr]
    rows = [{h: (row[i] if i < len(row) else '') for h, i in keep_ix} for row in rd if row]
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'file_date': date_line, 'src': 'https://www.xetra.com/xetra-en/instruments/shares/list-of-tradable-shares (file allTradableInstruments.csv)', 'columns': [h for h, i in keep_ix], 'rows': rows}, open('raw/xetra_instruments.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('Xetra rows', len(rows), 'CS', sum(1 for x in rows if x.get('Instrument Type') == 'CS'), 'DE ISIN CS', sum(1 for x in rows if x.get('Instrument Type') == 'CS' and x.get('ISIN', '').startswith('DE')), flush=True)
    ra = None
    for u in ('https://www.gleif.org/content/2-about-lei/7-code-lists/2-gleif-registration-authorities-list/2025-10-08_ra-list-v1.9.csv', 'https://www.gleif.org/content/2-about-lei/7-code-lists/2-gleif-registration-authorities-list/2024-11-13_ra-list-v1.8.csv'):
        x = get(u)
        if x is not None and x.status_code == 200 and x.content.decode('utf-8-sig', 'replace').startswith('Registration Authority Code'): ra = x.content.decode('utf-8-sig', 'replace'); open('raw/gleif_ra_list.csv', 'w', encoding='utf-8').write(ra); print('GLEIF RA list', u.split('/')[-1], flush=True); break
    if ra is None:
        page = get('https://www.gleif.org/en/about-lei/code-lists/gleif-registration-authorities-list')
        m = re.search(r'href="([^"]+ra-list[^"]*\.csv)"', page.text) if page is not None else None
        if m:
            u = m.group(1) if m.group(1).startswith('http') else 'https://www.gleif.org' + m.group(1); x = get(u)
            if x is not None and x.status_code == 200: open('raw/gleif_ra_list.csv', 'w', encoding='utf-8').write(x.content.decode('utf-8-sig', 'replace')); print('GLEIF RA list', u, flush=True)
        else: print('GLEIF RA list not found (courts will be shown by RA code)', flush=True)
    if '--no-gleif' not in sys.argv and not os.path.exists('raw/isin-lei-latest.zip'):
        meta = requests.get('https://mapping.gleif.org/api/v2/isin-lei/latest', headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()['data']['attributes']
        rr = requests.get(meta['downloadLink'], timeout=600); open('raw/isin-lei-latest.zip', 'wb').write(rr.content); open('raw/isin-lei-latest.txt', 'w').write(meta['fileName']); print('GLEIF mapping file', meta['fileName'], flush=True)
    print('FETCH DONE', flush=True)
