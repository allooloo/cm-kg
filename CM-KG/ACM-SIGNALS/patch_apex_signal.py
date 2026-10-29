r"""patch_apex_signal.py — ACM-SIGNALS-01 (DAY ORDER 3, 2026-10-24): the resolver answers the ACM-68000 signal. Adds get_signal(identifier) to the apex
router (cm-kg-apex: mcp.getissuer.ai, mcp.capitalmarketsknowledgegraph.ai). Issuer states: ACM-200 TRADING (on the home market's register) · ACM-404 NOT ON THE
REGISTER (no node holds it) · ACM-451 READ THE FILING (a regulatory filing in the last three days — from the node's events, then Issuerwire's filings, named) ·
ACM-403 HALTED is advisory (the nodes carry no halt flag; the answer links the market's halts page through its ECO page) · ACM-300 CONDITIONAL when a bare ticker
names more than one issuer · ACM-000 NOT APPLICABLE when the identifier is a GTIN (routed to gtinfetch.ai) · ACM-500 SYSTEM ERROR when the home node does not
answer. Also declares PROTOCOL (it sat inside a comment). index.js.pre-signals01-20261024 beside. Usage: python -X utf8 -I patch_apex_signal.py"""
import io
P = r"C:\ALLOOLOO\CM-KG\DOOR\apex\index.js"
t = io.open(P, encoding="utf-8", newline="").read()
old_v = t[t.index("const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.12.1';"):]
old_v = old_v[:old_v.index("\n")]
assert "const PROTOCOL = '2025-06-18';" in old_v
t = t.replace(old_v, "const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.13.0';   // 0.13.0 = ACM-SIGNALS-01 (2026-10-24): get_signal, the ACM-68000 issuer state. " + old_v.split("// ", 1)[1].replace(" const PROTOCOL = '2025-06-18';", "") + "\nconst PROTOCOL = '2025-06-18';")
anchor = "  { name: 'list_nodes', title: 'List market nodes'"
i = t.index(anchor); j = t.index("\n", i)
tool = ("\n  { name: 'get_signal', title: 'Get ACM-68000 signal', annotations: { title: 'Get ACM-68000 signal', ...ANN }, description: 'The ACM-68000 signal for a listed security in its home market: ACM-200 TRADING (on the register), ACM-404 NOT ON THE REGISTER, ACM-451 READ THE FILING (a regulatory filing in the last three days, named), ACM-300 CONDITIONAL (a bare ticker names more than one issuer: add the exchange), ACM-000 NOT APPLICABLE (a GTIN: ask gtinfetch.ai), ACM-500 SYSTEM ERROR (the home node did not answer). ACM-403 HALTED is advisory: the nodes carry no halt flag yet, so the answer links the market\\'s halts page. Each signal has its page at https://acm-<code>.ai/.',"
        " inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'ISIN (best), ticker with exchange (TSX:SHOP, SHEL.L), LEI or CMR key.' } }, required: ['identifier'] } },")
t = t[:j] + tool + t[j:]
sig = r'''
// ---- ACM-SIGNALS-01 (2026-10-24): get_signal — the ACM-68000 issuer state, read live from the home node (and Issuerwire for filings), never typed
const SIGNALS = { 'ACM-000': 'NOT APPLICABLE', 'ACM-200': 'TRADING', 'ACM-300': 'CONDITIONAL', 'ACM-403': 'HALTED', 'ACM-404': 'NOT ON THE REGISTER', 'ACM-451': 'READ THE FILING', 'ACM-500': 'SYSTEM ERROR' };
const MEANING = { 'ACM-000': 'The issuer layer does not apply to this identifier.', 'ACM-200': 'On the home market\'s register: proceed.', 'ACM-300': 'More than one issuer matches: name the exchange or give the ISIN, then ask again.', 'ACM-403': 'Trading is halted or suspended: do not act until it resumes.', 'ACM-404': 'Not on the register of any of the twelve markets: do not act on it as listed.', 'ACM-451': 'A regulatory filing is dated in the last three days: a person reads it before the agent acts.', 'ACM-500': 'The home market\'s node did not answer: retry; no record is served from another store.' };
const IW = 'https://mcp.issuerwire.ai/mcp';
const HOME = { CA: 'ca-cm-kg', GB: 'uk-cm-kg', US: 'us-cm-kg', DE: 'de-cm-kg', FR: 'fr-cm-kg', NL: 'nl-cm-kg', CH: 'ch-cm-kg', AU: 'au-cm-kg', SG: 'sg-cm-kg', JP: 'jp-cm-kg', KR: 'kr-cm-kg', HK: 'hk-cm-kg', KY: 'hk-cm-kg', BM: 'hk-cm-kg' };
async function iw(name, args) {
  try { const r = await fetch(IW, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'getissuer get_signal (ACM-SIGNALS-01)' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(8000) });
    const raw = await r.text(); const line = raw.split('\n').find(l => l.trim().startsWith('{') || l.startsWith('data: {')); const j = JSON.parse(line.replace(/^data: /, ''));
    return JSON.parse(j.result.content[0].text); } catch (e) { return null; }
}
const sigOut = (code, extra) => ({ signal: code, state: SIGNALS[code], meaning: MEANING[code], signal_page: `https://acm-${code.slice(4)}.ai/`, standard: 'https://acm-68000.org/', read_at: new Date().toISOString(), ...extra,
  advisory_403: 'ACM-403 HALTED is advisory: the nodes carry no halt flag yet; read the market\'s halts page (named on its ECO page) before acting.' });
async function getSignal(idRaw) {
  const id = String(idRaw || '').trim(); const up = id.toUpperCase();
  if (/^\d{8}$|^\d{12,14}$/.test(id)) return sigOut('ACM-000', { identifier: id, note: 'a GTIN, not a listed-security identifier', route: { gtins: 'https://gtinfetch.ai/mcp', path: `https://gtinfetch.ai/01/${id.padStart(14, '0')}` } });
  const w = whichNode(id);
  if (!w.nodes.length) return sigOut('ACM-404', { identifier: id, matched_by: w.kind, note: 'no node of the twelve holds this identifier', nodes: NODES.filter(n => n.live).map(n => n.node) });
  const outs = await Promise.all(w.nodes.map(n => forward(n, 'resolve_issuer', { identifier: id })));
  const matches = [].concat(...outs.map(o => o.matches || []));
  if (!matches.length) { const un = outs.filter(o => o.error === 'unavailable'); return un.length ? sigOut('ACM-500', { identifier: id, unavailable: un.map(o => o.node) }) : sigOut('ACM-404', { identifier: id, matched_by: w.kind }); }
  const isIsin = w.kind === 'isin';
  if (!isIsin && w.kind !== 'cmr' && new Set(matches.map(m => m.cmr)).size > 1) return sigOut('ACM-300', { identifier: id, matched_by: w.kind, candidates: matches.map(m => ({ cmr: m.cmr, name: m.name, exchange: m.exchange, isin: m.isin || null })) });
  const homeNode = isIsin ? HOME[up.slice(0, 2)] : null;
  const ranked = matches.slice().sort((a, b) => ((b.node === homeNode) - (a.node === homeNode)) || ((b.security_type || '').startsWith('Corporate') - (a.security_type || '').startsWith('Corporate')) || (String(b.as_of).localeCompare(String(a.as_of))));
  const h = ranked[0]; const cc = h.node.split('-')[0]; const cut = new Date(Date.now() - 3 * 86400000).toISOString().slice(0, 10);
  const base = { identifier: id, issuer: h.name, node: h.node, cmr: h.cmr, exchange: h.exchange, isin: h.isin || null, lei: h.lei || null, as_of: h.as_of, record: h.record_url, events: h.events_url, eco: `https://${cc}-eco.ai/`, door: PUBLIC[h.node] ? PUBLIC[h.node].door : null,
    elsewhere: ranked.slice(1).map(m => ({ node: m.node, name: m.name, exchange: m.exchange, record: m.record_url })) };
  let filing = null;
  const ev = await forward(h.node, 'list_events_since', { identifier: h.cmr, limit: 25 });
  const e = (ev.events || []).find(x => x.event_type !== 'newswire_release' && String(x.date) >= cut);
  if (e) filing = { date: e.date, title: e.title, url: e.url || null, source: e.source || e.wire || null, from: 'node events' };
  if (!filing) {
    const mk = cc === 'uk' ? 'UK' : cc.toUpperCase();
    const ri = await iw('resolve_issuer', { query: h.isin || h.cmr.split('/').pop(), market: mk, limit: 3 });
    const key = ri && (ri.issuers || ri.matches || ri.results || [])[0] && ((ri.issuers || ri.matches || ri.results)[0].issuer_key);
    if (key) { const lf = await iw('list_filings', { issuer: key, since: cut, type: 'filing', limit: 3 }); const row = lf && (lf.rows || [])[0]; if (row && String(row.date) >= cut) filing = { date: row.date, title: row.title, issuerwire_row: row.id, issuer_key: key, read: 'get_row on https://mcp.issuerwire.ai/mcp', from: 'Issuerwire' }; }
  }
  if (filing) return sigOut('ACM-451', { ...base, filing });
  return sigOut('ACM-200', base);
}
'''
k = t.index("async function callTool(name, args) {")
t = t[:k] + sig.lstrip("\n") + t[k:]
t = t.replace("  if (name === 'list_nodes') return { door:", "  if (name === 'get_signal') return getSignal(args.identifier);\n  if (name === 'list_nodes') return { door:", 1)
t = t.replace("isError: !!(out && out.error && out.error !== 'ambiguous') }", "isError: !!(out && out.error && out.error !== 'ambiguous') }", 1)
io.open(P, "w", encoding="utf-8", newline="").write(t); print("patched", P, len(t))
