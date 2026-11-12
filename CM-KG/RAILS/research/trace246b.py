import openpyxl, collections, re, json, sys
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\isin-dis'); import store
slug = lambda t: re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
for cc in ('ch', 'kr'):
    wb = openpyxl.load_workbook(rf'C:\ALLOOLOO\CM-KG\ISSUERS\{cc}-issuers.xlsx', read_only=True); ws = wb[wb.sheetnames[0]]; rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]; print(cc, 'sheets', wb.sheetnames[:6], 'rows', len(rows) - 1, hdr[:14])
    H = {h.lower(): i for i, h in enumerate(hdr)}; tk = next((H[k] for k in H if k in ('ticker', 'symbol', 'code')), None); ex = next((H[k] for k in H if 'exchange' in k), None); st = next((H[k] for k in H if k in ('status', 'listing status', 'state')), None); ty = next((H[k] for k in H if 'type' in k), None)
    c = store.cont(cc); keys = set(store.bj(c, 'door/index.json')['keys']); have = {(k.split('/')[1], k.split('/', 2)[2]) for k in keys}
    miss = [r for r in rows[1:] if r[tk] is not None and (str(r[ex]), slug(r[tk])) not in have and (str(r[ex]), str(r[tk])) not in have]
    print(' workbook rows not on the door:', len(miss), 'by', collections.Counter((r[ex], r[ty] if ty is not None else None, r[st] if st is not None else None) for r in miss).most_common(8)); print(' sample', [tuple(str(x)[:30] for x in r[:8]) for r in miss[:4]])
    dup = collections.Counter((str(r[ex]), slug(r[tk])) for r in rows[1:] if r[tk] is not None); print(' duplicate ticker rows in the workbook:', sum(v - 1 for v in dup.values() if v > 1))
