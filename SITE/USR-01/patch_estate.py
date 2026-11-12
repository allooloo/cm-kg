r"""patch_estate.py — USR-01/03: the estate source (CM-KG\ESTATE\worker). A .pre-usr01-2026-11-11 copy beside every file touched. Idempotent per file.
  chrome.js   FOR DESKS carries the eighth door (get_research); a Research link in the FOR HUMANS footer row; the top nav unchanged; SURFACES_VERSION 2026-11-11.1
  desks.js    DESKS: get_research (its page getresearch.ai; live when the apex router's descriptor answers)
  nav02.js    the desk check knows get_research is the router's own tool (live only when the router's tool list carries it)
  asof.js     getasof.ai's llms.txt, facts and card carry the doors list with the eighth door
  do5.js      the twenty-two node pages that named no exchange: a Coverage line from the venue roster; venues in their facts.json and llms.txt
  surfaces.js the twelve curated node pages' facts.json carry their venue roster block
Usage: python -X utf8 -I patch_estate.py"""
import pathlib, shutil
W = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker')
def edit(name, pairs, mark):
    p = W / name; pre = W / name.replace('.js', '.pre-usr01-2026-11-11.js'); s = p.read_text(encoding='utf-8')
    if mark in s: print(name, 'already patched'); return
    if not pre.exists(): shutil.copy2(p, pre)
    for o, n in pairs:
        assert s.count(o) == 1, (name, s.count(o), o[:90]); s = s.replace(o, n)
    p.write_text(s, encoding='utf-8'); print(name, 'patched')
edit('chrome.js', [
  ("export const SURFACES_VERSION = '2026-11-05.3';", "export const SURFACES_VERSION = '2026-11-11.1';   // .1 = USR-01/03: getresearch.ai (Data Research); FOR DESKS carries get_research; a Research link in the footer row; the venue roster on the node pages; was 2026-11-05.3\nconst SV_PREV_USR01 = '2026-11-05.3';"),
  ("export const DESK_ORDER = ['get_issuer', 'get_orderability', 'get_target_market', 'get_as_of', 'get_filings', 'get_ticker', 'get_auditor'];", "export const DESK_ORDER = ['get_issuer', 'get_orderability', 'get_target_market', 'get_as_of', 'get_filings', 'get_ticker', 'get_auditor', 'get_research'];   // USR-03: the eighth door"),
  ("<a href=\"https://investor.allooloo.ai\">Investor Relations</a> · <a href=\"https://allooloo.io/#contact\">Support</a>", "<a href=\"https://investor.allooloo.ai\">Investor Relations</a> · <a href=\"https://getresearch.ai/\">Research</a> · <a href=\"https://allooloo.io/#contact\">Support</a>"),
], "USR-03: the eighth door")
edit('desks.js', [
  ("['get_auditor', 'https://getauditor.ai/', 'https://mcp.getauditor.ai/mcp.json']];", "['get_auditor', 'https://getauditor.ai/', 'https://mcp.getauditor.ai/mcp.json'], ['get_research', 'https://getresearch.ai/', null]];   // USR-03: get_research is the router's own tool (no host of its own): live when the router's tool list carries it (nav02 runDesks)"),
], "'get_research', 'https://getresearch.ai/'")
edit('nav02.js', [
  ("  const live = await Promise.all(DESKS.map(async ([t, u, mj]) => { let ok = false; try {", "  const apexTools = await rpc('https://mcp.getissuer.ai/mcp', 'tools/list').then(j => new Set(((j.result && j.result.tools) || []).map(x => x.name))).catch(() => new Set());   // USR-03: get_research is on the router's own tool list\n  const live = await Promise.all(DESKS.map(async ([t, u, mj]) => { if (!mj) return apexTools.has(t) ? [t, u] : null; let ok = false; try {"),
], "USR-03: get_research is on the router's own tool list")
DL_OLD = "get_auditor https://getauditor.ai/"
s = (W / 'asof.js').read_text(encoding='utf-8')
if 'get_research https://getresearch.ai/' not in s:
    shutil.copy2(W / 'asof.js', W / 'asof.pre-usr01-2026-11-11.js'); n = s.count("'get_auditor https://getauditor.ai/']"); m = s.count("get_auditor https://getauditor.ai/',   // DOORS-01: the doors order")
    assert n == 2 and m == 1, (n, m)
    s = s.replace("'get_auditor https://getauditor.ai/']", "'get_auditor https://getauditor.ai/', 'get_research https://getresearch.ai/']").replace("get_auditor https://getauditor.ai/',   // DOORS-01: the doors order", "get_auditor https://getauditor.ai/ · get_research https://getresearch.ai/',   // DOORS-01: the doors order · USR-03")
    (W / 'asof.js').write_text(s, encoding='utf-8'); print('asof.js patched')
else: print('asof.js already patched')
edit('do5.js', [
  ("import { M, EU_REGIME, EU_ROWS, VERSION5 } from './do5-data.js';", "import { M, EU_REGIME, EU_ROWS, VERSION5 } from './do5-data.js';\nimport { VENUES } from './venues-data.js';   // USR-01: the venue roster (every exchange on the record keyed to its node; regulator, halts page, disclosure channel from the market file)\nconst venueOf = cc => (VENUES.by_node || {})[cc] || null;\nconst vfield = f => (f && f.value ? (f.source ? `${esc(f.value)} (${a(String(f.source).split(' ')[0], 'source')}${f.read_date ? ', read ' + esc(f.read_date) : ''})` : esc(f.value)) : 'not on the market file');"),
  ("    : li([`State: NODE OPENING`, `Store it will read: ${esc(d.store_named || val(e.regulated_information_store) || 'not named yet')}`]);", "    : li([`State: NODE OPENING`, `Store it will read: ${esc(d.store_named || val(e.regulated_information_store) || 'not named yet')}`]);\n  const vn = venueOf(cc);   // USR-01: the Coverage line and the venue lines, from the venue roster\n  const sv = vn ? li([`Coverage: ${esc(vn.coverage || 'not on the market file')}`, `Exchanges on the record: ${Object.entries(vn.exchanges_on_record || {}).map(([k, n]) => `${code(k)} ${int(Number(n))}`).join(' · ') || 'none'}`, `Regulator: ${vfield(vn.regulator)}`, `Halts page: ${vfield(vn.halts_page)}`, `Disclosure channel: ${vfield(vn.disclosure_channel)}`]) : '';"),
  ("  return { v, html: `<h2>Node</h2>${s1}<h2>Door</h2>${s2}<h2>Kit</h2>${s3}` };", "  return { v, html: `<h2>Node</h2>${s1}${sv ? `<h2>Venues</h2>${sv}` : ''}<h2>Door</h2>${s2}<h2>Kit</h2>${s3}` };"),
  ("`Issuer page: https://${issuerHost(c.cc)}/ · rules: https://${c.cc}-eco.ai/`].join('\\n') + '\\n';", "`Issuer page: https://${issuerHost(c.cc)}/ · rules: https://${c.cc}-eco.ai/`, venueOf(c.cc) ? `Coverage: ${venueOf(c.cc).coverage || 'not on the market file'}. Venue roster: https://getresearch.ai/venues.json` : null].filter(Boolean).join('\\n') + '\\n';"),
  ("as_of: b.v.asOf || null, resolver: GI_MCP, operator: OPERATOR, surface_version: VERSION5 }; }\n  else if (c.kind === 'regime-iss')", "as_of: b.v.asOf || null, resolver: GI_MCP, operator: OPERATOR, surface_version: VERSION5, coverage: (venueOf(c.cc) || {}).coverage || null, venues: venueOf(c.cc), venue_roster: 'https://getresearch.ai/venues.json' }; }\n  else if (c.kind === 'regime-iss')"),
], "import { VENUES } from './venues-data.js'")
edit('surfaces.js', [
  ("    coverage: d.coverage, exchanges: v.exchanges,", "    coverage: d.coverage, exchanges: v.exchanges, venues: (VENUES.by_node || {})[cc] || null, venue_roster: 'https://getresearch.ai/venues.json',   // USR-01: the venue roster block\n   "),
], "USR-01: the venue roster block")
s = (W / 'surfaces.js').read_text(encoding='utf-8')
if "from './venues-data.js'" not in s:
    i = s.index('import '); s = s[:i] + "import { VENUES } from './venues-data.js';   // USR-01\n" + s[i:]; (W / 'surfaces.js').write_text(s, encoding='utf-8'); print('surfaces.js import added')
