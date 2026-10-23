"""Rebuild — the Hong Kong issuers workbook after Width 1 + Fill + Confirm (ORDER-035). Reads the newest assembled hk-issuers.xlsx (Width 0), raw/confirm.jsonl
and the Width 1 event set; writes a new versioned workbook POND\\hk-cm-kg\\assembled\\<date>\\hk-issuers.xlsx and mirrors it to CM-KG\\ISSUERS\\hk-issuers.xlsx
(the previous mirror kept beside as .pre-<stamp>). Filled per line: Auditor, Share registrar (value · source · read by · State · second source · second read by),
Annual report (HKEXnews), Newswire of habit (HKEXnews, with the count of documents in the window), HQ city (filled). The Gaps line is rewritten: a filled field
leaves it; a field still blank carries its reason. Nothing deleted: the Width 0 columns and values are carried as read."""
import shutil
from collections import Counter
from openpyxl import load_workbook
from fc_common import *
C = {d['key']: d for d in jload('raw/confirm.jsonl')}
EVN = Counter(e['exchange'] + '|' + e['ticker'] for e in events())
SRC = 'https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en'
def gaps_split(t):
    out = {}
    for part in (t or '').split('; '):
        if ':' in part: f, why = part.split(':', 1); out[f.strip()] = why.strip()
    return out
NEW_COLS = ['Auditor second source', 'Auditor second read by', 'Share registrar second source', 'Share registrar second read by', 'Newswire releases seen']
if __name__ == '__main__':
    wb = load_workbook(ISSUERS_XLSX); st = Counter()
    for tab in TABS:
        ws = wb[tab]; hdr = [c.value for c in ws[1]]
        for col in NEW_COLS:
            if col not in hdr: ws.cell(row=1, column=len(hdr) + 1, value=col); hdr.append(col)
        ix = {h: i + 1 for i, h in enumerate(hdr)}
        for row in range(2, ws.max_row + 1):
            code = ws.cell(row=row, column=ix['Stock code']).value
            if not code: continue
            k = f'{tab}|{code}'; d = C.get(k, {}); gaps = gaps_split(ws.cell(row=row, column=ix['Gaps']).value)
            def put(col, v):
                if col in ix and v not in (None, ''): ws.cell(row=row, column=ix[col], value=v)
            for fld, col in (('auditor', 'Auditor'), ('registrar', 'Share registrar')):
                x = d.get(fld)
                if x:
                    put(col, x['value']); put(f'{col} source', x['source']); put(f'{col} read by', x['read_by']); put(f'{col} State', x['state'])
                    if x.get('second_source'): put(f'{col} second source', x['second_source']); put(f'{col} second read by', x['second_read_by'])
                    if x.get('conflict'): put(f'{col} second source', x['conflict']['source']); put(f'{col} second read by', f"{x['conflict']['read_by']} names: {x['conflict']['value']} (conflict; the filing's value stands)")
                    gaps.pop(col, None); st[f'{fld} {x["state"]}'] += 1
                else: gaps[col] = 'not found on the English annual report page read or by the lab reads (ORDER-035 Fill)'; st[f'{fld} blank'] += 1
            ar = d.get('annual_report')
            if ar: put('Annual report', ar['value']); put('Annual report source', ar['source']); put('Annual report read by', ar['read_by']); gaps.pop('Annual report', None); st['annual report'] += 1
            else: gaps['Annual report'] = 'no English annual report on HKEXnews in the twelve-month window'
            n = EVN.get(k, 0)
            if n: put('Newswire of habit', 'HKEXnews'); put('Newswire releases seen', f'{n} English documents on HKEXnews in the trailing twelve months'); put('Newswire read by', 'HKEXnews title search (Width 1)'); put('Newswire State', 'sourced'); gaps.pop('Newswire of habit', None); st['newswire'] += 1
            hq = d.get('hq_city')
            if hq and not ws.cell(row=row, column=ix['HQ city']).value: put('HQ city', hq['value']); put('HQ source', hq['source']); put('HQ read by', hq['read_by']); put('HQ State', hq['state']); gaps.pop('HQ city', None); st['hq city filled'] += 1
            ws.cell(row=row, column=ix['Gaps'], value='; '.join(f'{f}: {w}' for f, w in gaps.items()) or None)
    me = wb['Method'] if 'Method' in wb.sheetnames else wb.create_sheet('Method')
    me.append(['ORDER-035 (2026-10-22)', 'Hong Kong a full node (CEO ruling 2026-10-22; the Sept 11 partner-beacon line struck). Width 1: HKEXnews title search, English only, trailing twelve months. Fill: the annual report Corporate Information page (Tavily page extraction) → Perplexity (agent · low) → Grok (grok-4.6) for what is still missing; Confirm: filing and lab agree = confirmed; disagree = conflict, both kept, Mistral review only. financialfilings.com never a source.'])
    me.append(['ORDER-035 counts', json.dumps(dict(st), ensure_ascii=False)])
    if 'HITL — needs MK' in wb.sheetnames:
        h = wb['HITL — needs MK']; h.append(['ORDER-035', 'Local partner line struck by the CEO ruling of 2026-10-22: Hong Kong is a full node. The Companies Registry (paid search) stands as HITL.'])
    adir = pond.assembled(NODE); out = os.path.join(adir, 'hk-issuers.xlsx'); wb.save(out)
    dst = r'C:\ALLOOLOO\CM-KG\ISSUERS\hk-issuers.xlsx'; stamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    if os.path.exists(dst): shutil.copy2(dst, f'{dst}.pre-{stamp}')
    shutil.copy2(out, dst)
    print('rebuild', out, dict(st))
