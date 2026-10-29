r"""ZONES-02 — the 17 zones into COMPANY RECORDS\Allooloo_Domains_Master.xlsx: Build (the domains master) and Cloudflare agent access (the Cloudflare audit
list). Audit cells are read from the kit's apply file (zones02-kit-apply-<date>.json), never typed. Groups are Theme / Room / Content — the three themes are not
products (CEO copy fence). A .pre copy is kept beside; a zone already on a sheet is not added twice. Usage: python -X utf8 -I master_rows_z2.py"""
import openpyxl, shutil, json, glob, os, datetime
WB = r'C:\ALLOOLOO\COMPANY RECORDS\Allooloo_Domains_Master.xlsx'; HERE = os.path.dirname(os.path.abspath(__file__))
pre = WB.replace('.xlsx', '.pre-zones02-20261026.xlsx')
if not os.path.exists(pre): shutil.copy2(WB, pre)
K = json.load(open(sorted(glob.glob(os.path.join(HERE, 'zones02-kit-apply-*.json')))[-1]))
TOD = datetime.datetime.now(datetime.timezone.utc).date().isoformat()   # the house dates by UTC
ROWS = {  # zone: (group, role)
 'data-now.ai': ('Theme — Data Now', 'Data Now · the issuer record as it stands on the last sweep · canonical — serves; door: mcp.getissuer.ai/mcp'),
 'data-now.com': ('Theme — Data Now', 'twin — 301 to data-now.ai (path kept)'), 'data-now.io': ('Theme — Data Now', 'twin — 301 to data-now.ai (path kept)'), 'data-now.org': ('Theme — Data Now', 'twin — 301 to data-now.ai (path kept)'),
 'data-live.ai': ('Theme — Data Now', 'forward — 301 to data-now.ai (path kept)'),
 'data-vintage.ai': ('Theme — Data Vintage', 'Data Vintage · history per market from the 2021 epoch, signed rows · canonical — serves; Build Record price: per market, per year — price to be set'),
 'data-vintage.com': ('Theme — Data Vintage', 'twin — 301 to data-vintage.ai (path kept)'), 'data-vintage.io': ('Theme — Data Vintage', 'twin — 301 to data-vintage.ai (path kept)'), 'data-vintage.org': ('Theme — Data Vintage', 'twin — 301 to data-vintage.ai (path kept)'),
 'data-ark.ai': ('Theme — Data Ark', 'Data Ark · the second, write-once copy per market · canonical — serves'), 'data-ark.io': ('Theme — Data Ark', 'twin — 301 to data-ark.ai (path kept)'),
 'hunter-agent.ai': ('Room — hunter / hedge / ark agent', 'hunter-agent · the Data Now room (watch agent) · serves'), 'hedge-agent.ai': ('Room — hunter / hedge / ark agent', 'hedge-agent · the Data Vintage room (research agent) · serves'),
 'ark-agent.ai': ('Room — hunter / hedge / ark agent', 'ark-agent · the Data Ark room (books-and-records agent) · serves'),
 'data-record.ai': ('Content — record / ECO / RCO', 'data-record · the Capital Markets Record, field by field · serves'), 'data-eco.ai': ('Content — record / ECO / RCO', 'data-eco · the Electronic Compliance Object · serves'),
 'data-rco.ai': ('Content — record / ECO / RCO', 'data-rco · the Record of Cleared Orders · serves'),
 'data-ark.org': ('Theme — Data Ark', 'twin — 301 to data-ark.ai (path kept); found by the ZONES-02 tail, not in the order list'),
 'hedge-agent.com': ('Room — hunter / hedge / ark agent', 'twin — 301 to hedge-agent.ai (path kept); found by the ZONES-02 tail, not in the order list')}
wb = openpyxl.load_workbook(WB); b = wb['Build']; c = wb['Cloudflare agent access']
have_b = {r[0] for r in b.iter_rows(min_row=2, values_only=True) if r and r[0]}; have_c = {r[0] for r in c.iter_rows(min_row=2, values_only=True) if r and r[0]}
nb = nc = 0
for z, (grp, role) in ROWS.items():
    k = K[z]; ds = 'DNSSEC pending (DS issued; registrar Cloudflare Registrar publishes it)' if k['dnssec'] == 'pending' else f"DNSSEC {k['dnssec']}"
    surf = f"estate-pages Worker (apex + www) · {'canonical — serves' if 'serves' in role else '301 in the Worker'} · SSL {'full (strict)' if k['ssl'] == 'strict' else k['ssl']} · {ds}"
    if z not in have_b: b.append([z, grp, role, '.' + z.split('.', 1)[1], None, 'Cloudflare', f'Live (ZONES-02, {TOD})', surf]); nb += 1
    if z not in have_c:
        c.append([z, 'must be OFF (allow)', 'OFF' if k['fight'] is False else str(k['fight']), 'OFF' if k['robots_managed'] is False else 'ON', 'not read (no API answer on the house token)',
                  f"Audited {TOD} (CC, API read, ZONES-02): AI bots {k['ai_bots']} · Bot Fight Mode {'off' if k['fight'] is False else k['fight']} · crawler protection {k['crawler']} · managed robots.txt {'off' if k['robots_managed'] is False else 'on'}; SSL {k['ssl']}; HTTPS {k['https']}; TLS ≥ {k['min_tls']}; {ds}; bound to the estate Worker; Web Analytics beacon kept off the pages by Cache-Control no-transform (RUM auto-install not readable on the house tokens)"]); nc += 1
wb.save(WB); print('Build +', nb, '· Cloudflare agent access +', nc)
