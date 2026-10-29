r"""SHELF-01 — cmkg-door 0.17.0: three tools beside the five (get_timeline · list_events · get_score) and the memo's optional as_of on get_record.
Nothing an existing call sends or receives changes: get_record without as_of answers exactly as 0.16.4. .pre copy: index.pre-shelf01-20261027.js."""
p = r'C:\ALLOOLOO\CM-KG\DOOR\container\index.js'
s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
rep("const SERVER_VERSION = '0.16.4';", "const SERVER_VERSION = '0.17.0';   // 0.17.0 = SHELF-01 (2026-10-27): get_timeline · list_events · get_score beside the five; get_record takes an optional as_of (Replay, sealed years only)\n// prior:")
rep("version: { type: 'integer', description: 'Prior version number; omitted = current.' } }, required: ['identifier'] } },",
    "version: { type: 'integer', description: 'Prior version number; omitted = current.' }, as_of: { type: 'string', description: 'YYYY-MM-DD (Replay): the record as it stood on that date, from the sealed market-year only; a date in a year not sealed answers \\'not sealed\\'. Omitted = current.' } }, required: ['identifier'] } },")
rep("  { name: 'list_nodes', title: 'List market nodes',",
"""  { name: 'get_timeline', title: 'Get an issuer timeline', annotations: { title: 'Get an issuer timeline', ...ANN }, description: 'Return the full dated list of an issuer\\'s event lines from its record start date, oldest first, no window cap: date, type, title as filed, source URL. The same lines list_events_since serves; each line is signed by the door.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker, ISIN, LEI, or a CMR key.' } }, required: ['identifier'] } },
  { name: 'list_events', title: 'List lifecycle events', annotations: { title: 'List lifecycle events', ...ANN }, description: 'Return dated lifecycle events on this market — listing, delisting, name_change, domicile_change, auditor_change, segment_move — each with issuer, type, source URL; the type map of this register and its gaps are published with the answer.',
    inputSchema: { type: 'object', properties: { type: { type: 'string', description: 'listing · delisting · name_change · domicile_change · auditor_change · segment_move; omitted = all.' }, since: { type: 'string', description: 'YYYY-MM-DD; omitted = everything held.' }, identifier: { type: 'string', description: 'Optional: one issuer only.' }, cursor: { type: 'integer' }, limit: { type: 'integer' } } } },
  { name: 'get_score', title: 'Get an issuer filing score', annotations: { title: 'Get an issuer filing score', ...ANN }, description: 'Return an issuer\\'s filing cadence, latency (days from period end to filing) and silence (longest gap): the issuer\\'s value, its exchange percentile and its sector percentile; as-of date and the years scored. Numbers and percentiles only.',
    inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker, ISIN, LEI, or a CMR key.' } }, required: ['identifier'] } },
  { name: 'list_nodes', title: 'List market nodes',""")
rep("""  if (name === 'list_nodes') return { door: `${NODE} node door (${REGION})`, live_nodes: liveNodes(), nodes: NODES };""",
"""  if (name === 'list_nodes') return { door: `${NODE} node door (${REGION})`, live_nodes: liveNodes(), nodes: NODES };
  // SHELF-01 (0.17.0): list_events reads the node's lifecycle index (door/events-by-type.json, written nightly beside the index); no identifier needed
  if (name === 'list_events') {
    const ix = await cached('door/events-by-type.json');
    if (!ix) return { error: 'not_built', note: `the lifecycle index is not on ${NODE} yet` };
    let keys = null;
    if (args.identifier) { const r0 = await resolveKeys(args.identifier); if (!r0.keys.length) return { error: 'not_found', identifier: args.identifier }; keys = new Set(r0.keys); }
    const want = args.type ? [args.type] : Object.keys(ix.types || {});
    if (args.type && !(ix.types || {})[args.type]) return { error: 'unknown_type', type: args.type, types: Object.keys(ix.types || {}), gaps: ix.gaps };
    let rows = []; for (const t of want) for (const e of (ix.types[t] || [])) if ((!args.since || (e.date || '') >= args.since) && (!keys || keys.has(e.cmr))) rows.push({ type: t, ...e });
    rows.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    const limit = Math.min(Math.max(parseInt(args.limit || 100, 10), 1), 500); const cursor = Math.max(parseInt(args.cursor || 0, 10), 0);
    return { node: NODE, register: ix.register, type_map: ix.type_map, gaps: ix.gaps, built_utc: ix.built_utc, total: rows.length, cursor, limit, next_cursor: cursor + limit < rows.length ? cursor + limit : null, events: rows.slice(cursor, cursor + limit) };
  }""")
rep("""  if (name === 'list_aliases') {""",
"""  if (name === 'get_timeline') {
    const r = await record(key); const evs = (await eventsOf(key)).slice().sort((a, b) => (a.date || '').localeCompare(b.date || ''));
    return { cmr: key, record_started: (FACTS && FACTS.live_record_began) || (r && r.as_of) || null, total: evs.length, record_event_count: r ? r.event_count : null, events: evs, note: 'every event line on the record, oldest first, no window cap' };
  }
  if (name === 'get_score') {
    const [, ex, t] = key.split('/'); const sc = await cached(`door/score/${ex}/${slug(t)}.json`);
    return sc || { error: 'not_scored', cmr: key, note: `no score for this issuer on ${NODE} yet: a market is scored only when its ledger entry is complete and its manifests verify` };
  }
  if (name === 'get_record' && args.as_of) return replay(key, String(args.as_of));
  if (name === 'list_aliases') {""")
# Replay: the record as it stood on a date, from the sealed market-year only (backfill/<year>/manifest.json + the per-issuer replay file)
rep("async function callTool(name, args) {",
"""async function replay(key, asOf) {
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(asOf)) return { error: 'bad_as_of', as_of: asOf, note: 'YYYY-MM-DD' };
  const y = asOf.slice(0, 4); const bf = await cached('backfill/facts.json');
  const sealed = bf && bf.years && bf.years[y];
  if (!sealed) return { status: 'not sealed', cmr: key, as_of: asOf, year: Number(y), ledger: bf ? { years_sealed: Object.keys(bf.years || {}).sort(), history_from: bf.history_from, year_in_progress: bf.year_in_progress } : null, note: 'no sealed market-year holds this date; the live record is never returned in its place' };
  const man = await cached(`backfill/${y}/manifest.json`);
  const [, ex, t] = key.split('/'); const mine = (await cached(`backfill/replay/${y}/${ex}/${slug(t)}.json`)) || { rows: [] };
  const rows = (mine.rows || []).filter(r => (r.date || '') <= asOf);
  const r = await record(key);
  const ident = {}; for (const [f, v] of Object.entries((r && r.identity) || {})) { const at = v && (v.read_at || v.as_of); ident[f] = at && String(at).slice(0, 10) <= asOf ? v : { state: 'not held as of this date', first_read: at || null }; }
  return { cmr: key, as_of: asOf, year: Number(y), sealed: true, manifest: man ? { hash_tree_root: man.hash_tree_root, rows: man.rows, run: man.run, rows_file: man.rows_file, signature: man.signature } : null,
    identity_as_of: ident, events_as_of: rows, events_in_year_to_date: rows.length, note: 'the disclosure lines are the sealed rows of the market-year, each signed; an identity field read after this date is shown as not held, never back-filled' };
}
async function callTool(name, args) {""")
open(p, 'w', encoding='utf-8').write(s)
print('door 0.17.0 patched')
