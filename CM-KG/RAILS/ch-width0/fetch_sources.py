"""Step 1 — pull the Swiss rosters and registry references into raw/ (a junction to the open pond drop POND\\ch-cm-kg\\width0\\<date>\\). Public, no login.
  SIX Swiss Exchange ...... the exchange's public share explorer feed https://www.six-group.com/fqs/ref.json?where=PortalSegment=EQ (ShortName, ISIN, ValorSymbol,
                            ValorNumber, SecTypeCode SS/RS/BS/PC, MarketSegment, ICBIndustry, Currency, ExchangeCode, FirstTradingDate, NumberInIssue; price
                            fields never requested)
  BX Swiss ................ the exchange's instruments list https://www.bxswiss.com/instruments/az/-/-/-/-/-/-/-/-/<page>/500 (label, symbol, ISIN, name; 'listed on BX Swiss')
  Zefix ................... legal-form table https://www.zefix.ch/ZefixREST/api/v1/legalForm.json (the same public web API the zefix.ch search uses; company search per
                            issuer in zefix_match.py). The official ZefixPublicREST needs an account (401) — noted as HITL, not needed for the web API.
  GLEIF ISIN-to-LEI file .. https://mapping.gleif.org/api/v2/isin-lei/latest"""
import requests, json, os, re, sys, time, html
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
os.makedirs('raw', exist_ok=True)
def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=120, **kw)
            if r.status_code in (429, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            return r
        except Exception: time.sleep(3 * (i + 1))
    return None
if __name__ == '__main__':
    j = get('https://www.six-group.com/fqs/ref.json', params={'select': 'ShortName,ISIN,ValorSymbol,ValorNumber,SecTypeCode,MarketSegment,ICBIndustry,Currency,TradingBaseCurrency,ExchangeCode,Exchange,FirstTradingDate,NumberInIssue', 'where': 'PortalSegment=EQ', 'page': 1, 'pagesize': 5000}).json()
    six = [dict(zip(j['colNames'], row)) for row in j['rowData']]
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'total': j.get('totalRows'), 'src': 'https://www.six-group.com/en/products-services/the-swiss-stock-exchange/market-data/shares/share-explorer.html (feed six-group.com/fqs/ref.json, PortalSegment=EQ)', 'rows': six}, open('raw/six_eq.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('SIX EQ rows', len(six), 'CH ISINs', sum(1 for x in six if str(x.get('ISIN', '')).startswith('CH')), flush=True)
    bx = []; page = 1
    while page <= 40:
        r = get(f'https://www.bxswiss.com/instruments/az/-/-/-/-/-/-/-/-/{page}/500')
        if r is None or r.status_code != 200: print('BX page', page, 'status', r.status_code if r else None); break
        blocks = re.findall(r'<a[^>]+href="(/instruments/([A-Z]{2}[A-Z0-9]{9}\d)[^"]*)"[^>]*>(.*?)</a>', r.text, re.S)
        if not blocks: break
        for href, isin, inner in blocks:
            label = re.search(r'class="label">(.*?)</span>', inner, re.S); code = re.search(r'heading--compact">(.*?)</span>', inner, re.S); name = re.search(r'heading--large">(.*?)</h2>', inner, re.S)
            bx.append({'isin': isin, 'label': html.unescape(re.sub(r'\s+', ' ', label.group(1))).strip() if label else '', 'code': html.unescape(re.sub(r'\s+', ' ', code.group(1))).strip().split(' ')[0] if code else '', 'name': html.unescape(re.sub(r'\s+', ' ', name.group(1))).strip() if name else '', 'url': 'https://www.bxswiss.com' + href.split('"')[0]})
        print('BX page', page, 'rows', len(blocks), flush=True)
        if len(blocks) < 500: break
        page += 1
    json.dump({'fetched': time.strftime('%Y-%m-%d'), 'src': 'https://www.bxswiss.com/instruments', 'rows': bx}, open('raw/bx_instruments.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('BX rows', len(bx), 'CH ISINs', sum(1 for x in bx if x['isin'].startswith('CH')), 'labels', sorted(set(x['label'] for x in bx))[:12], flush=True)
    lf = get('https://www.zefix.ch/ZefixREST/api/v1/legalForm.json').json(); json.dump(lf, open('raw/zefix_legalform.json', 'w', encoding='utf-8'), ensure_ascii=False)
    if '--no-gleif' not in sys.argv and not os.path.exists('raw/isin-lei-latest.zip'):
        meta = requests.get('https://mapping.gleif.org/api/v2/isin-lei/latest', headers={'Accept': 'application/vnd.api+json'}, timeout=60).json()['data']['attributes']
        rr = requests.get(meta['downloadLink'], timeout=600); open('raw/isin-lei-latest.zip', 'wb').write(rr.content); open('raw/isin-lei-latest.txt', 'w').write(meta['fileName']); print('GLEIF mapping file', meta['fileName'], flush=True)
    print('FETCH DONE', flush=True)
