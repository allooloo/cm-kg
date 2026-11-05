r"""master_add.py — ASOF-01 item 5: the new zones in the Allooloo domains master (COMPANY RECORDS\Allooloo_Domains_Master.xlsx) with their roles. Snapshot
first (Allooloo_Domains_Master.pre-asof01-2026-11-05.xlsx beside, never over). Build: eight rows after the gettargetmarket rows, styled as the row above.
Summary: three groups after gettargetmarket's, Total's range extended. Zone ids and plans as read (zones-pages-apply-*.json). Idempotent.
Usage: python -X utf8 -I master_add.py"""
import os, glob, json, shutil, copy, openpyxl
M = r'C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.xlsx'; Q = r'C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.pre-asof01-2026-11-05.xlsx'
if not os.path.exists(Q): shutil.copy2(M, Q)
R = json.load(open(sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zones-pages-apply-*.json')))[-1], encoding='utf-8'))
G_DOOR, G_FWD, G_HELD = 'Product — getasof (door)', 'Forwards — getasof', 'Held stock — getshareprice'
ROWS = [('getasof.ai', G_DOOR, 'getasof door', '.ai', 'Live — the As Of door page (getasof-pages); mcp./agent. the router'),
        ('getasof.com', G_FWD, 'Forward → getasof', '.com', '301 → getasof.ai (whole zone)'), ('getasof.org', G_FWD, 'Forward → getasof', '.org', '301 → getasof.ai (whole zone)'), ('getasof.io', G_FWD, 'Forward → getasof', '.io', '301 → getasof.ai (whole zone)')] + \
       [(f'getshareprice{t}', G_HELD, 'Held stock (no build)', t, '301 → allooloo.io (whole zone); nothing built until a separate order') for t in ('.ai', '.com', '.org', '.io')]
wb = openpyxl.load_workbook(M); ws = wb['Build']
have = {str(r[0].value).strip().lower() for r in ws.iter_rows(min_row=2) if r[0].value}
last = max(r[0].row for r in ws.iter_rows(min_row=2) if r[0].value and str(r[1].value or '').startswith(('Product — gettargetmarket', 'Forwards — get-targetmarket')))
todo = [x for x in ROWS if x[0] not in have]
if todo:
    ws.insert_rows(last + 1, len(todo))
    for i, (dom, grp, role, tld, state) in enumerate(todo):
        r = last + 1 + i; z = R[dom]
        vals = [dom, grp, role, tld, None, 'Cloudflare (zone)', state, '301' if 'Forward' in role or 'Held' in role else '200',
                f"ASOF-01 2026-11-05: on the account (zone {z['zone_id'][:8]}…, active, plan {z['plan']}); ledger tag estate:allooloo family:products role:{z['role']} product:{'getshareprice' if 'shareprice' in dom else 'getasof'}"]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v); src = ws.cell(row=last, column=c)
            if src.has_style: cell._style = copy.copy(src._style)
    print('Build: added', [x[0] for x in todo], 'after row', last)
else: print('Build: already in')
S = wb['Summary']; groups = [S.cell(row=r, column=1).value for r in range(1, S.max_row + 1)]
if G_DOOR not in groups:
    at = groups.index('Product — gettargetmarket (door and twins)') + 2; tot = groups.index('Total') + 1
    S.insert_rows(at, 3)
    for i, g in enumerate((G_DOOR, G_FWD, G_HELD)):
        S.cell(row=at + i, column=1, value=g); S.cell(row=at + i, column=2, value=f'=COUNTIF(Build!B:B,"{g}")')
        for c in (1, 2):
            if S.cell(row=at - 1, column=c).has_style: S.cell(row=at + i, column=c)._style = copy.copy(S.cell(row=at - 1, column=c)._style)
    tr = tot + 3; assert S.cell(row=tr, column=1).value == 'Total', S.cell(row=tr, column=1).value
    S.cell(row=tr, column=2, value=f'=SUM(B2:B{tr - 1})'); print('Summary: three groups at row', at, '· Total', S.cell(row=tr, column=2).value)
else: print('Summary: groups already in')
wb.save(M); print('saved', M, '· snapshot', Q)
