import openpyxl, collections, re, json, sys
sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\isin-dis'); import store
slug = lambda t: re.sub(r'[^A-Za-z0-9.\-]', '_', str(t))
for cc, sheets in (('ch', ['SIX', 'BX Swiss']), ('kr', None)):
    c = store.cont(cc); names = [b.name for b in c.list_blobs(name_starts_with='door/records/')]; print(cc, 'blobs by exchange', collections.Counter(n.split('/')[2] for n in names))
    have = {(n.split('/')[2], n.split('/', 3)[3][:-5]) for n in names}
    wb = openpyxl.load_workbook(rf'C:\ALLOOLOO\CM-KG\ISSUERS\{cc}-issuers.xlsx', read_only=True); print(' sheets', wb.sheetnames)
    for sn in (sheets or [s for s in wb.sheetnames if s.upper() in ('KOSPI', 'KOSDAQ', 'KONEX', 'KRX', 'ISSUERS')] or wb.sheetnames[2:5]):
        ws = wb[sn]; rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]; H = {h.lower(): i for i, h in enumerate(hdr)}
        tk = next((H[k] for k in H if k in ('ticker', 'symbol', 'code', 'short code', 'stock code')), None); print('  ', sn, 'rows', len(rows) - 1, hdr[:16])
        if tk is None: continue
        codes = [slug(r[tk]) for r in rows[1:] if r[tk] is not None]; d = collections.Counter(codes); onb = {s for (e, s) in have}
        miss = [r for r in rows[1:] if r[tk] is not None and slug(r[tk]) not in onb]
        ty = next((H[k] for k in H if 'type' in k or 'class' in k or 'category' in k), None); nm = next((H[k] for k in H if 'name' in k), 0)
        print('   distinct codes', len(d), 'duplicate rows', sum(v - 1 for v in d.values() if v > 1), 'rows not on the door', len(miss), collections.Counter(str(r[ty])[:40] if ty is not None else None for r in miss).most_common(6)); print('   sample', [(str(r[nm])[:40], str(r[tk])) for r in miss[:5]])
