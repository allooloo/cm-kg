"""TSXV exchange bulletins per issuer, from the TMX Info TSX Venture company-documents controller (public, no session):
   http://apps.tmx.com/TSXVenture/TSXVentureHttpController?GetPage=CompanyDocuments&PO_ID=<po_id>&BulletinsMode=on&Start...&End...
Rows carry bulletin category, bulletin type, date, and a NOTICE_ID whose page is the bulletin. Read-by: 'apps.tmx.com TSXV company documents'."""
import re, html, json, sys
from common import *
issuers = [r for r in load_issuers() if r['exchange'] == 'TSXV']
SRC = 'http://apps.tmx.com/TSXVenture/TSXVentureHttpController'
def fetch(r):
    if not r.get('po_id'): return {'error': 'no PO id in TMX workbook (listed after the workbook month or not covered)', 'events': []}
    u = (f"{SRC}?GetPage=CompanyDocuments&PO_ID={r['po_id']}&BulletinsMode=on&StartMonth={SINCE.month}&StartDay={SINCE.day}&StartYear={SINCE.year}"
         f"&EndMonth={TODAY.month}&EndDay={TODAY.day}&EndYear={TODAY.year}")
    x = get(u)
    if x is None or x.status_code != 200: return {'error': f'http {x.status_code if x else "none"}', 'events': []}
    h = x.text; evs = []; cat = ''
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S):
        if 'NOTICE_ID=' not in row: continue
        cells = [html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c))).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]
        cells = [c for c in cells if c]
        dm = re.search(r'(\d{1,2}/[A-Za-z]{3}/20\d\d)', row); nid = re.search(r'NOTICE_ID=(\d+)', row)
        if not dm or not nid: continue
        date = to_iso(dm.group(1))
        texts = [c for c in cells if not re.fullmatch(r'\d{1,2}/[A-Za-z]{3}/20\d\d', c)]
        if len(texts) >= 2: cat, btype = texts[0], texts[1]
        elif texts: btype = texts[0]
        else: continue
        url = f"{SRC}?GetPage=NoticesContents&PO_ID=&NOTICE_ID={nid.group(1)}&CORRECTION_FLG=N&HC_FLAG1=checked"
        title = f'TSXV bulletin: {btype}' + (f' ({cat})' if cat else '')
        et = 'halt_resume' if re.search(r'HALT|RESUME|CEASE TRADE', btype, re.I) else ('corporate_action' if re.search(r'CONSOLIDAT|DIVIDEND|SPLIT|NAME CHANGE|SYMBOL CHANGE|DELIST|NEW LISTING|GRADUAT|RIGHTS|WARRANT|RECORD DATE|NORMAL COURSE|TRANSFER', btype + ' ' + cat, re.I) else 'exchange_bulletin')
        if in_window(date): evs.append(event(r, et, date, title, 'TSX Venture Exchange bulletin', url, 'apps.tmx.com TSXV company documents', detail=f'{cat} / {btype}'))
    return {'events': evs, 'n': len(evs), 'query': u}
if __name__ == '__main__':
    run_workers('tsxv_bulletins', fetch, issuers, threads=int(os.environ.get('THREADS', '4')))
