import openpyxl, collections, json
out = {}
for cc, sheets in (('ch', ['SIX']), ('kr', ['KOSPI', 'KOSDAQ', 'KONEX'])):
    wb = openpyxl.load_workbook(rf'C:\ALLOOLOO\CM-KG\ISSUERS\{cc}-issuers.xlsx', read_only=True); res = collections.Counter(); ex = []
    for sn in sheets:
        rows = list(wb[sn].iter_rows(values_only=True)); H = {str(h): i for i, h in enumerate(rows[0])}; g = collections.defaultdict(list)
        for r in rows[1:]:
            if r[H['Symbol']] is not None: g[str(r[H['Symbol']])].append(r)
        for s, rs in g.items():
            if len(rs) < 2: continue
            names = {str(r[0]) for r in rs}; isins = {str(r[H['ISIN']]) for r in rs}; types = {str(r[H['Security type']]) for r in rs}
            kind = ('identical row repeated' if len(isins) == 1 and len(names) == 1 else 'same issuer, same ISIN, name variant' if len(isins) == 1 else 'same issuer, another ISIN (another share line)' if len(names) == 1 else 'different names and ISINs under one symbol')
            res[kind] += len(rs) - 1
            if len(ex) < 6: ex.append((sn, s, sorted(names)[:2], sorted(isins)[:3], sorted(types)[:2]))
    print(cc, dict(res)); [print('  ', e) for e in ex]; out[cc] = {'by_kind': dict(res), 'examples': ex}
json.dump(out, open(r'C:\ALLOOLOO\SITE\USR-01\trace246.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
