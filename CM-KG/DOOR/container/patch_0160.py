r"""patch_0160.py — NODE-ROW-01…09 (DAY ORDER 5, 2026-10-24): cmkg-door 0.15.0 -> 0.16.0 — NODE_COPY for the nine ROW markets (ky bm je in tw sa ae br mx):
country, jurisdiction, the regulator's disclosure rules as the duty line (the market's ECO page names them, sourced), the venues, ISIN-keyed records.
The door name comes from PUBLIC_HOST (default mcp.<node>.ai — the own-zone rule). index.js.pre-row-20261024 beside."""
import io, os, shutil
P = r"C:\ALLOOLOO\CM-KG\DOOR\container\index.js"
if not os.path.exists(P + '.pre-row-20261024'): shutil.copy2(P, P + '.pre-row-20261024')
t = io.open(P, encoding="utf-8", newline="").read()
ROW = {'ky': ('Cayman Islands', 'KY', 'CIMA', 'Cayman Islands Stock Exchange (CSX)', 'CSX market announcements'),
       'bm': ('Bermuda', 'BM', 'BMA', 'Bermuda Stock Exchange (BSX)', 'BSX market notices and company announcements'),
       'je': ('Jersey', 'JE', 'JFSC', 'The International Stock Exchange (TISE)', 'TISE market news'),
       'in': ('India', 'IN', 'SEBI', 'National Stock Exchange of India (NSE) and BSE', 'NSE and BSE corporate announcements'),
       'tw': ('Taiwan', 'TW', 'FSC', 'Taiwan Stock Exchange (TWSE) and Taipei Exchange (TPEx)', 'MOPS, the Market Observation Post System'),
       'sa': ('Saudi Arabia', 'SA', 'CMA', 'Saudi Exchange (Main Market and Nomu Parallel Market)', 'Saudi Exchange issuer announcements'),
       'ae': ('United Arab Emirates', 'AE', 'SCA', 'Abu Dhabi Securities Exchange, Dubai Financial Market and Nasdaq Dubai', 'the exchanges\u2019 issuer disclosures'),
       'br': ('Brazil', 'BR', 'CVM', 'B3', 'CVM regulated information (IPE, Empresas.NET)'),
       'mx': ('Mexico', 'MX', 'CNBV', 'Bolsa Mexicana de Valores (BMV) and Bolsa Institucional de Valores (BIVA)', 'BMV EMISNET and BIVA issuer information')}
if "'ky-cm-kg':" not in t:
    rows = "".join("  '%s-cm-kg': { country: '%s', jurisdiction: '%s', duty: '%s disclosure rules (see %s-eco.ai)', scope: '%s equity lines (the exchange\\'s own list); records keyed by ISIN; filings from %s.', example: '', exchanges: 'by MIC', ids: 'ISIN (the record key), LEI, legal name' },   // NODE-ROW (DAY ORDER 5)\n"
                   % (cc, c, j, reg, cc, ex.replace("'", "\\'"), st.replace("'", "\\'")) for cc, (c, j, reg, ex, st) in ROW.items())
    assert t.count("const NODE_COPY = {\n") == 1
    t = t.replace("const NODE_COPY = {\n", "const NODE_COPY = {\n" + rows, 1)
o = "const SERVER_VERSION = '0.15.0';"
if o in t: t = t.replace(o, "const SERVER_VERSION = '0.16.0';   // 0.16.0 = NODE-ROW (DAY ORDER 5, 2026-10-24): the nine ROW markets' copy.  ", 1)
io.open(P, "w", encoding="utf-8", newline="").write(t); print("door 0.16.0")
