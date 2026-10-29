r"""ZONES-03 — the nine zones into COMPANY RECORDS\Allooloo_Domains_Master.xlsx: Build (the domains master) and Cloudflare agent access (the Cloudflare audit
list). Audit cells are read from the kit's apply file (zones03-kit-apply-<date>.json), never typed. Groups are Theme / Room / Content — the three themes are not
products (CEO copy fence). A .pre copy is kept beside; a zone already on a sheet is not added twice. Usage: python -X utf8 -I master_rows_z2.py"""
import openpyxl, shutil, json, glob, os, datetime
WB = r'C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.xlsx'; HERE = os.path.dirname(os.path.abspath(__file__))
pre = WB.replace('.xlsx', '.pre-zones03-20261027.xlsx')
if not os.path.exists(pre): shutil.copy2(WB, pre)
K = json.load(open(sorted(glob.glob(os.path.join(HERE, 'zones03-kit-apply-*.json')))[-1]))
TOD = datetime.datetime.now(datetime.timezone.utc).date().isoformat()   # the house dates by UTC
ROWS = {  # zone: (group, role) — sold under Data Now / Data Vintage, never products or divisions (CEO copy fence)
 'data-replay.ai': ('Under Data Vintage', 'Replay · the record as it stood on any date, 2021 forward · serves; linked from data-vintage.ai'),
 'data-bench.ai': ('Under Data Vintage', 'Bench · the test set: issuers × dated questions × the answer with its source page · serves; linked from data-vintage.ai'),
 'data-cleanroom.ai': ('Under Data Vintage', 'Cleanroom · the licensed corpus, per market-year · serves; price to be set; linked from data-vintage.ai'),
 'data-cleanroom.io': ('Under Data Vintage', 'twin — 301 to data-cleanroom.ai (path kept)'), 'data-cleanroom.org': ('Under Data Vintage', 'twin — 301 to data-cleanroom.ai (path kept)'),
 'data-review.ai': ('Under Data Vintage', 'Review · per-market, per-year disclosure report from the sealed layer (counts, latency, concentration) · serves; linked from data-vintage.ai'),
 'data-score.ai': ('Under Data Now', 'Score · issuer filing cadence and latency against exchange and sector, five years deep · serves; linked from data-now.ai'),
 'data-timeline.ai': ('Under Data Now', 'Timeline · the dated event history of any issuer, one call · serves; linked from data-now.ai'),
 'data-events.ai': ('Under Data Now', 'Events · IPOs, delistings, renames, domicile and auditor changes across the markets, dated · serves; linked from data-now.ai')}
wb = openpyxl.load_workbook(WB); b = wb['Build']; c = wb['Cloudflare agent access']
have_b = {r[0] for r in b.iter_rows(min_row=2, values_only=True) if r and r[0]}; have_c = {r[0] for r in c.iter_rows(min_row=2, values_only=True) if r and r[0]}
nb = nc = 0
for z, (grp, role) in ROWS.items():
    k = K[z]; ds = 'DNSSEC pending (DS issued; registrar Cloudflare Registrar publishes it)' if k['dnssec'] == 'pending' else f"DNSSEC {k['dnssec']}"
    surf = f"estate-pages Worker (apex + www) · {'canonical — serves' if 'serves' in role else '301 in the Worker'} · SSL {'full (strict)' if k['ssl'] == 'strict' else k['ssl']} · {ds}"
    if z not in have_b: b.append([z, grp, role, '.' + z.split('.', 1)[1], None, 'Cloudflare', f'Live (ZONES-03, {TOD})', surf]); nb += 1
    if z not in have_c:
        c.append([z, 'must be OFF (allow)', 'OFF' if k['fight'] is False else str(k['fight']), 'OFF' if k['robots_managed'] is False else 'ON', 'not read (no API answer on the house token)',
                  f"Audited {TOD} (CC, API read, ZONES-03): AI bots {k['ai_bots']} · Bot Fight Mode {'off' if k['fight'] is False else k['fight']} · crawler protection {k['crawler']} · managed robots.txt {'off' if k['robots_managed'] is False else 'on'}; SSL {k['ssl']}; HTTPS {k['https']}; TLS ≥ {k['min_tls']}; {ds}; bound to the estate Worker; Web Analytics beacon kept off the pages by Cache-Control no-transform (RUM auto-install not readable on the house tokens)"]); nc += 1
wb.save(WB); print('Build +', nb, '· Cloudflare agent access +', nc)
