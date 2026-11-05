r"""master_add.py — DOORS-01 item 5: the new zones in the Allooloo domains master (COMPANY RECORDS\Allooloo_Domains_Master.xlsx) with their roles. Snapshot
first (Allooloo_Domains_Master.pre-doors01-2026-11-05.xlsx beside, never over). Build: nineteen rows after the getasof rows, styled as the row above.
Summary: three groups after gettargetmarket's, Total's range extended. Zone ids and plans as read (zones-pages-apply-*.json). Idempotent.
Usage: python -X utf8 -I master_add.py"""
import os, glob, json, shutil, copy, openpyxl
M = r'C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.xlsx'; Q = r'C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.pre-doors01-2026-11-05.xlsx'
if not os.path.exists(Q): shutil.copy2(M, Q)
R = json.load(open(sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zones-pages-apply-*.json')))[-1], encoding='utf-8'))
G_DOOR, G_FWD, G_HELD = 'Product — the get_ doors (getfilings · getticker · getauditor)', 'Forwards — the get_ doors', 'Held stock — get_ names (DOORS-01)'
ROWS = [(f'get{p}.ai', G_DOOR, f'get{p} door', '.ai', f'Live — the get_{p} door page (getdoors-pages); mcp./agent. the router') for p in ('filings', 'ticker', 'auditor')] +        [(z, G_FWD, f'Forward → {t}', '.' + z.split('.')[1], f'301 → {t} (whole zone)') for z, t in (('getfilings.io', 'getfilings.ai'), ('getticker.org', 'getticker.ai'), ('getticker.io', 'getticker.ai'), ('getauditor.org', 'getauditor.ai'), ('getauditor.io', 'getauditor.ai'))] +        [(z, G_HELD, 'Held stock (no build)', '.' + z.split('.')[1], '301 → allooloo.io (whole zone); nothing built until its own order') for z in ('getfinancials.ai', 'getfinancials.io', 'getbonds.ai', 'getbonds.org', 'getbonds.io', 'getownership.ai', 'getownership.io', 'getownership.org', 'getdividends.ai', 'getdividends.io', 'getdividends.org')]
wb = openpyxl.load_workbook(M); ws = wb['Build']
have = {str(r[0].value).strip().lower() for r in ws.iter_rows(min_row=2) if r[0].value}
last = max(r[0].row for r in ws.iter_rows(min_row=2) if r[0].value and str(r[1].value or '').startswith(('Product — getasof', 'Forwards — getasof', 'Held stock — getshareprice')))
todo = [x for x in ROWS if x[0] not in have]
if todo:
    ws.insert_rows(last + 1, len(todo))
    for i, (dom, grp, role, tld, state) in enumerate(todo):
        r = last + 1 + i; z = R[dom]
        vals = [dom, grp, role, tld, None, 'Cloudflare (zone)', state, '301' if 'Forward' in role or 'Held' in role else '200',
                f"DOORS-01 2026-11-05: on the account (zone {z['zone_id'][:8]}…, active, plan {z['plan']}); ledger tag estate:allooloo family:products role:{z['role']} product:{dom.split('.')[0]}"]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v); src = ws.cell(row=last, column=c)
            if src.has_style: cell._style = copy.copy(src._style)
    print('Build: added', [x[0] for x in todo], 'after row', last)
else: print('Build: already in')
S = wb['Summary']; groups = [S.cell(row=r, column=1).value for r in range(1, S.max_row + 1)]
if G_DOOR not in groups:
    at = groups.index('Held stock — getshareprice') + 2; tot = groups.index('Total') + 1
    S.insert_rows(at, 3)
    for i, g in enumerate((G_DOOR, G_FWD, G_HELD)):
        S.cell(row=at + i, column=1, value=g); S.cell(row=at + i, column=2, value=f'=COUNTIF(Build!B:B,"{g}")')
        for c in (1, 2):
            if S.cell(row=at - 1, column=c).has_style: S.cell(row=at + i, column=c)._style = copy.copy(S.cell(row=at - 1, column=c)._style)
    tr = tot + 3; assert S.cell(row=tr, column=1).value == 'Total', S.cell(row=tr, column=1).value
    S.cell(row=tr, column=2, value=f'=SUM(B2:B{tr - 1})'); print('Summary: three groups at row', at, '· Total', S.cell(row=tr, column=2).value)
else: print('Summary: groups already in')
wb.save(M); print('saved', M, '· snapshot', Q)
