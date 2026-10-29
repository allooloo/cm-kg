"""India halts - official lists of equity shares currently suspended from trading.

NSE (primary): the "Listing compliance" page https://www.nseindia.com/regulations/listing-compliance links two Excel files that NSE
refreshes under new dated names (the reader finds them on the page by their labels, so the link is never hard-coded):
  - "Listed companies suspended from trading for non-compliance" (e.g. .../mediaattachment/2026-10/Suspension_list_SOP_21102026_....xlsx)
    sheets: Suspension prior SOP, SOP Suspended, Liquidation, OTHERS. Columns: Symbol, Company, ISIN, Date of Suspension (+ Reason in OTHERS).
  - "Listed companies suspended from trading - Corporate Actions" (e.g. .../Suspension_List_23.10.2026_....xlsx)
    sheets: Immediate Susp- Resolution Plan, Capital Reduction, SCHEME & MERGER, SDD Suspension, ... Columns: ISIN, Symbol, Name,
    (Record date), Suspension Date (+ Remark / Reason).
  The sheet name is the store's own suspension category; reason = the row's Reason/Remark when given, else the sheet name.
  Promoter / director name columns are not read (not needed; personal data).
  The page needs the Akamai cookies set by a plain GET of https://www.nseindia.com/; the files on nsearchives.nseindia.com need none.
BSE: https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?segment=Equity&status=Suspended (the BSE "List of Scrips" page with
  Status = Suspended). Gives scrip code, scrip id, name, ISIN; no suspension date and no reason (those stay null). Mktcap discarded.

fetch() -> {"source_url","read_by","read_at","count","halted":[{"isin","ticker","name","since","reason","page", "venue", ...}]}
One row per (venue, ISIN). Usage: python halt.py   writes samples/halts-<date>.json
"""
import os, re, io, sys, json, time, html, datetime
import requests, openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roster  # noqa: E402

UA = roster.UA
NSE_HOME = 'https://www.nseindia.com/'
NSE_LC = 'https://www.nseindia.com/regulations/listing-compliance'
LABELS = {'non-compliance': 'Listed companies suspended from trading for non-compliance',
          'corporate-actions': 'Listed companies suspended from trading - Corporate Actions'}
BSE_SUSP = roster.BSE_API + '?Group=&Scripcode=&industry=&segment=Equity&status=Suspended'


def _date(v):
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    v = str(v or '').strip()
    for f in ('%d-%b-%y', '%d-%b-%Y', '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(v, f).date().isoformat()
        except ValueError:
            pass
    return v or None


def nse_links():
    s = requests.Session(); s.headers.update({'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9', 'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8'})
    s.get(NSE_HOME, timeout=60); time.sleep(1)
    t = None
    for i in range(3):
        r = s.get(NSE_LC, timeout=90)
        if r.status_code == 200 and 'uspen' in r.text:
            t = r.text; break
        time.sleep(4 * (i + 1))
    if t is None:
        raise RuntimeError('NSE listing-compliance page did not answer')
    links = {}
    for row in re.findall(r'<tr.*?</tr>', t, re.S):
        txt = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', row))).strip()
        for k, lab in LABELS.items():
            if lab.lower() in txt.lower():
                h = re.findall(r'href="([^"]+\.xlsx?)"', row)
                if h:
                    links[k] = h[0]
    return links


def nse_rows(kind, url):
    r = requests.get(url, headers={'User-Agent': UA}, timeout=120); r.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    out = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        hi = next((i for i, x in enumerate(rows[:10]) if x and any(str(c or '').strip().upper() == 'ISIN' for c in x)), None)
        if hi is None:
            continue
        hdr = [str(c or '').strip().lower() for c in rows[hi]]
        def col(*names):
            for n in names:
                for j, h in enumerate(hdr):
                    if h == n or h.startswith(n):
                        return j
            return None
        ci, cs, cn = col('isin'), col('symbol'), col('company', 'name of the company', 'company name')
        cd = col('date of suspension', 'suspension date'); cr = col('reason', 'remark')
        for x in rows[hi + 1:]:
            if not x or ci is None or not str(x[ci] or '').strip():
                continue
            isin = str(x[ci]).strip().upper()
            reason = str(x[cr]).strip() if cr is not None and x[cr] else None
            out.append({'isin': isin if len(isin) == 12 else None, 'raw_isin': None if len(isin) == 12 else isin,
                        'ticker': str(x[cs]).strip() if cs is not None and x[cs] else None, 'name': str(x[cn]).strip() if cn is not None and x[cn] else None,
                        'since': _date(x[cd]) if cd is not None else None, 'reason': reason or ws.title.strip(), 'category': ws.title.strip(),
                        'list': LABELS[kind], 'page': NSE_LC, 'file': url, 'venue': 'XNSE'})
    return out


def fetch():
    read_at = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    links = nse_links(); halted, seen = [], set()
    for k, u in links.items():
        time.sleep(1)
        for r in nse_rows(k, u):
            key = ('XNSE', r['isin'] or r['raw_isin'])
            if key in seen:
                continue
            seen.add(key); halted.append(r)
    n_nse = len(halted)
    bse_err = None
    try:
        for b in roster.bse_list('Suspended'):
            if (b['raw_isin'] or '').upper().startswith('INF'):
                continue
            key = ('XBOM', b['isin'] or b['code'])
            if key in seen:
                continue
            seen.add(key)
            halted.append({'isin': b['isin'], 'ticker': b['id'], 'name': b['name'], 'since': None, 'reason': None, 'page': roster.BSE_PAGE,
                           'venue': 'BSME' if b['group'] in roster.BSE_SME_GROUPS else 'XBOM', 'bse_code': b['code'], 'bse_group': b['group'], 'list': 'BSE List of Scrips, Status = Suspended'})
    except Exception as e:
        bse_err = str(e)
    from collections import Counter
    return {'source_url': NSE_LC, 'files': links, 'bse_source': BSE_SUSP,
            'read_by': 'NSE suspension lists (two Excel files linked on the listing-compliance page, every sheet) + BSE List of Scrips status=Suspended; '
                       'one row per (venue, ISIN); BSE rows carry no date or reason', 'read_at': read_at,
            'count': len(halted), 'count_by_venue': dict(Counter(h['venue'] for h in halted)), 'count_nse': n_nse,
            'count_nse_by_category': dict(Counter(h['category'] for h in halted if h['venue'] == 'XNSE')),
            'count_isin_null': sum(1 for h in halted if not h['isin']), 'bse_error': bse_err, 'language': 'en', 'halted': halted}


if __name__ == '__main__':
    res = fetch()
    os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
    out = os.path.join(HERE, 'samples', f'halts-{datetime.datetime.now(datetime.timezone.utc).date().isoformat()}.json')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('halted', res['count'], res['count_by_venue'], res['count_nse_by_category'], 'isin null', res['count_isin_null'], '->', out)
