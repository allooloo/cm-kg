// ZONES-02 (CEO order 2026-10-26) — the zones paid 2026-10-25, on the estate Worker through the ORDER-027 dispatch (doors027.js): nine pages on one template,
// record-grade (numbered sections, live counts, no script, contact block). Three themes: data-now.ai · data-vintage.ai · data-ark.ai. Three rooms, one per theme:
// hunter-agent.ai (Data Now) · hedge-agent.ai (Data Vintage) · ark-agent.ai (Data Ark). Three contents: data-record.ai · data-eco.ai · data-rco.ai.
// Forwards (301, path kept): data-now .com/.io/.org and data-live.ai → data-now.ai · data-vintage .com/.io/.org → data-vintage.ai · data-ark.io → data-ark.ai.
// Copy fence: KYP and Issuerwire.ai are the products and are named as such; Data Now, Data Vintage and Data Ark are never called products or divisions — each page
// says what it is, what is in it, and which door the finserv agent calls. Counts live from list_nodes on every render, never typed. Pay line on every page.
// Build Record pricing is not set: data-vintage.ai carries "per market, per year — price to be set" and nothing else about price.
import { OPERATOR, CORPORATE, CONTACT, APEX, APEX_AGENT, SURFACES_VERSION, REGION_FULL, esc, int, today, num, table, scale, contactSection, icon, btn } from './chrome.js';
// SITE-02 (Site Build Plan v2.2 §4, 2026-10-28): the shelf cards — one line each from the Product Sheet v1.0 (2026-10-27), each linking to its zone or product
const card = (ic, title, text, href, label) => `<div class="card">${icon(ic)}<h3>${esc(title)}</h3><p>${esc(text)}</p>${btn(label || 'Open', href)}</div>`;
const CARDS_NOW = [['record', 'KYP', 'The issuer record. Every listed company in every market on the roster: who it is, where it is listed, what it disclosed and when — every fact with its source and date, every row signed, served from the issuer’s own country.', 'https://getissuer.ai/', 'Open KYP'], ['pulse', 'Issuerwire.ai', 'The issuer news. One signed row per filing or release, the source on every row, the record behind the headline.', 'https://issuerwire.ai/', 'Open Issuerwire'], ['ring', 'Score', 'How often and how late an issuer files, against its exchange and sector, five years deep. Numbers and percentiles.', 'https://data-score.ai/', 'Open Score'], ['pulse', 'Timeline', 'The dated event history of any issuer, in one call.', 'https://data-timeline.ai/', 'Open Timeline'], ['issuer', 'Events', 'Listings, delistings, renames, domicile and auditor changes across the markets, dated.', 'https://data-events.ai/', 'Open Events']];
const CARDS_VINTAGE = [['record', 'Replay', 'The record as it stood on any date, 2021 forward — what a reader could have known that morning.', 'https://data-replay.ai/', 'Open Replay'], ['key', 'Bench', 'The test set: issuers × dated questions × the answer with its source page. Score any agent against it.', 'https://data-bench.ai/', 'Open Bench'], ['receipt', 'Cleanroom', 'The sealed corpus, per market-year, with sources and signatures, under licence.', 'https://data-cleanroom.ai/', 'Open Cleanroom'], ['desk', 'Review', 'The per-market, per-year disclosure report: counts, latency, concentration. Signed data and a PDF.', 'https://data-review.ai/', 'Open Review']];
const cards = list => `<div class="cards">${list.map(c => card(...c)).join('')}</div>`;
import { totals } from './products.js';
import * as Z3 from './zones03.js';   // ZONES-03 (2026-10-27): seven pages under Data Now and Data Vintage, merged into P and classifyZ below

const GI_MCP = 'https://mcp.getissuer.ai/mcp';
const RCO_MCP = 'https://mcp.rco-a2a.ai/mcp';
const IW = 'https://issuerwire.ai/'; const IW_MCP = 'https://mcp.issuerwire.ai/mcp';
const KYP = 'https://kyp-model.ai/';
const JWKS = 'https://allooloo.ai/.well-known/jwks.json';
export const PAY = '$0.01 a read, paid in the call on x402.';
const PAY_HOW = 'Every read is free unless the agent asks for the offer (header <code>x402-pay: 1</code>); the door then answers HTTP 402 with a signed offer, and the same call carries the payment (x402 v2, USDC or Open USD on Base) and the receipt.';
const FAM = { now: ['data-now.com', 'data-now.io', 'data-now.org', 'data-live.ai'], vintage: ['data-vintage.com', 'data-vintage.io', 'data-vintage.org'], ark: ['data-ark.io', 'data-ark.org'], hedge: ['hedge-agent.com'], ...Z3.FAM3 };   // ZONES-02 tail (2026-10-26): data-ark.org and hedge-agent.com, paid the same day, not in the order's list

export function classifyZ(h) {
  let m; const z3 = Z3.classify3(h); if (z3) return z3;
  if (h === 'data-live.ai') return { kind: 'redirect', canonical: 'https://data-now.ai', status: 301 };
  if (h === 'hedge-agent.com') return { kind: 'redirect', canonical: 'https://hedge-agent.ai', status: 301 };
  if ((m = h.match(/^data-(now|vintage|ark)\.(ai|com|io|org)$/))) { if (m[1] === 'ark' && !['ai', 'io', 'org'].includes(m[2])) return null; return m[2] === 'ai' ? { kind: 'zone02', key: m[1] } : { kind: 'redirect', canonical: `https://data-${m[1]}.ai`, status: 301 }; }
  if ((m = h.match(/^(hunter|hedge|ark)-agent\.ai$/))) return { kind: 'zone02', key: m[1] === 'ark' ? 'arkroom' : m[1] };
  if ((m = h.match(/^data-(record|eco|rco)\.ai$/))) return { kind: 'zone02', key: m[1] };
  return null;
}

// ---------- live values (list_nodes, read at render)
function vals(ctx) {
  const t = totals(ctx); const L = Object.values(ctx.live || {}); const live = L.filter(n => n.live);
  const bf = live.filter(n => n.backfill && n.backfill.rows);
  return { records: int(t.records), events: int(t.events), nodes: t.nodes, last: t.last || '', live,
    hist_markets: bf.length, hist_rows: int(bf.reduce((a, n) => a + (n.backfill.rows || 0), 0)), hist_docs: int(bf.reduce((a, n) => a + (n.backfill.documents || 0), 0)),
    hist_years: bf.reduce((a, n) => a + ((n.backfill.years || []).length), 0), hist: bf };
}
const doorOf = n => (n.regional_door || n.door || '').replace(/\/mcp$/, '') + '/mcp';
const call = (name, args) => esc(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }));
const exOf = ctx => { const n = (ctx.live || {})['ca-cm-kg'] || Object.values(ctx.live || {}).find(x => x.live && x.example) || {}; return { node: n.node || 'ca-cm-kg', door: doorOf(n), isin: (n.example || {}).isin || '', url: (n.example || {}).record_url || '' }; };
const kit = (host, extra) => num('K', ['<a href="/llms.txt"><code>/llms.txt</code></a> · <a href="/facts.json"><code>/facts.json</code></a> · <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a> · <a href="/.well-known/security.txt"><code>/.well-known/security.txt</code></a> · <a href="/sitemap.xml"><code>/sitemap.xml</code></a> · <a href="/robots.txt"><code>/robots.txt</code></a>'].concat(extra || []));
const payBlock = (n, note) => `<h2>${n} Paying for a read</h2><p class="lead"><strong>${esc(PAY)}</strong> ${note}</p>`;   // the shared how-to (PAY_HOW) rides in llms.txt and facts.json, not on every page

// ---------- the nine pages: title, h1, description, body, door the agent calls
const P = {
  now: {
    title: 'Data Now — the issuer record as it stands tonight, for financial-services agents',
    h1: 'Data Now: the record today, per read.',
    desc: v => `Data Now: ${v.records} issuer records and ${v.events} dated disclosure events across ${v.nodes} markets, swept nightly; market date ${v.last}. Read on the market's own door.`,
    door: c => ({ mcp: GI_MCP, name: 'getissuer apex router' }),
    body: (ctx, v, host) => `${scale([[esc(v.records), 'issuer records', 'list_nodes', 'issuer'], [esc(v.events), 'dated disclosure events', 'list_nodes', 'record'], [esc(v.last), 'last sweep market date', 'list_nodes', 'pulse']])}
<p class="lead">The record today, per read. Five things Data Now sells: KYP · Issuerwire · Score · Timeline · Events.</p>${cards(CARDS_NOW)}
<p class="lead">Data Now is the present tense of the Capital Markets Record: each listed company's identity, its venue, its identifiers and the disclosures it made in the trailing twelve months, as read on the most recent nightly sweep of its home market. Nothing here is a forecast or a price. It is the state of the public record tonight, held in the country that publishes it.</p>
<h2>1 What it is</h2>${num(1, ['A nightly sweep per market at 02:00 local standard time rebuilds the register from the exchange lists and the company registries, then reads the disclosure wires and bulletins for the window.', `Live tonight: <strong>${esc(v.nodes)}</strong> markets, last market date <code>${esc(v.last)}</code>. The figures above are read from <code>list_nodes</code> when this page renders.`, 'A company that left the list keeps its record with its last state; nothing is deleted, every change is a new version.'])}
<h2>2 What is in it</h2>${num(2, ['Identity: legal name as filed, ticker on its own venue, ISIN, LEI with its registration status, jurisdiction from GLEIF.', 'Disclosure trail: results, material changes, halts and resumptions, director dealings, meeting notices — each dated, typed and linked to the page it was read from.', 'Halt flag: the venue’s own halt page, read nightly, with the time it was read.', 'Every field names its source page, who read it and its state (sourced, filled, confirmed); a blank stays blank and says why.'])}
<h2>3 The door a finserv agent calls</h2>${num(3, [`Any market, one address: <code>${GI_MCP}</code> (Streamable HTTP MCP, no sign-up). The router holds only an index and forwards to the market’s door; the record body never leaves its country.`, `Find the company: <pre>${call('resolve_issuer', { identifier: exOf(ctx).isin })}</pre>`, `What changed since last night: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: v.last || today() })}</pre>`, 'Is it trading on its home register right now: <code>get_signal</code> at the same router (ACM-200 trading · ACM-403 halted · ACM-404 not on the register).', `The signed disclosure rows themselves come from <a href="${IW}">Issuerwire.ai</a>, the product, at <code>${IW_MCP}</code>.`])}
<h2>4 The market doors</h2><div class="wrap">${table(['market', 'door', 'records', 'events', 'market date'], v.live.map(n => [`<code class="nw">${esc(n.node)}</code>`, `<code>${esc(doorOf(n))}</code>`, `<span class="n">${esc(int(n.records))}</span>`, `<span class="n">${esc(int(n.events))}</span>`, `<span class="nw">${esc(n.as_of || '')}</span>`]))}</div><p class="src">source: list_nodes at ${esc(APEX)}/mcp, read at render</p>
${payBlock(5, 'A watch over many issuers is many reads; each one is free unless the agent asks for the offer.')}<h2>6 Machine kit</h2>${kit(host, [`What Data Now sells, one page each: ${under('now')}.`, `Forwards here (301, path kept): ${FAM.now.join(', ')}.`, `The room that works this record: <a href="https://hunter-agent.ai/">hunter-agent.ai</a>.`])}`
  },
  vintage: {
    title: 'Data Vintage — each market’s past, year by year, for financial-services agents',
    h1: 'Data Vintage: five sealed years, 2021 →, per market-year.',
    desc: v => `Data Vintage: history per market from the 2021 epoch — ${v.hist_markets} market(s) with years held, ${v.hist_rows} signed rows, ${v.hist_docs} source documents, read from list_nodes at render. Per market, per year — price to be set.`,
    door: c => ({ mcp: GI_MCP, name: 'getissuer apex router (list_nodes carries the history counts)' }),
    body: (ctx, v, host) => `${scale([[esc(String(v.hist_markets)), 'markets with years held', 'list_nodes · backfill', 'record'], [esc(v.hist_rows), 'signed history rows', 'list_nodes · backfill', 'issuer'], [esc(String(v.hist_years)), 'market-years held', 'list_nodes · backfill', 'pulse']])}
<p class="lead">Five sealed years, 2021 →, per market-year. Four things Data Vintage sells: Replay · Bench · Cleanroom · Review.</p>${cards(CARDS_VINTAGE)}
<p class="lead">Ideation — the agent at run rate reads the record before it acts. Ignition — the agent being designed trains and tests on sealed years. The dataset you design agents on is itself kept by agents.</p>
<p class="lead">Data Vintage is the back catalogue. Where Data Now keeps the trailing twelve months, Vintage goes back, market by market and year by year, to the epoch of 1 January 2021: the disclosures each company made, read again from the wires and bulletins of the time, each row signed when it lands. A year is added to a market only when its rows are read and verified; a year still being read is named as in progress.</p>
<h2>1 What it is</h2>${num(1, ['One history per market, stored in that market’s own store beside the live record; the years are filled newest first by a nightly backfill run per market.', 'Each row is signed Ed25519 (kid <code>allooloo-cmr-2026-10</code>) and mirrored to the market’s ark on the night it lands.', 'History depth is never a market count: a market is live whether or not its earlier years are held yet.'])}
<h2>2 What is in it, tonight</h2><div class="wrap">${v.hist.length ? table(['market', 'history from', 'years held', 'year in progress', 'rows', 'documents'], v.hist.map(n => [`<code class="nw">${esc(n.node)}</code>`, `<span class="nw">${esc(n.backfill.history_from || '')}</span>`, esc((n.backfill.years || []).join(' · ')), esc(String(n.backfill.year_in_progress || '')), `<span class="n">${esc(int(n.backfill.rows))}</span>`, `<span class="n">${esc(int(n.backfill.documents))}</span>`])) : '<p>No market carries history yet.</p>'}</div><p class="src">source: the roster entry of each market (list_nodes, field backfill, from the store’s backfill/facts.json), read at render</p>
<h2>3 The door a finserv agent calls</h2>${num(3, [`How deep each market goes: <code>list_nodes</code> at <code>${GI_MCP}</code> — every roster entry with history carries <code>backfill</code> (history_from, years, rows, documents).`, `Inside the live window, by date: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: '2025-11-01' })}</pre> on the market door; the window is twelve months.`, `An earlier state of one record: <pre>${call('get_record', { identifier: exOf(ctx).isin, version: 1 })}</pre> (a version number; omitted = current).`, 'The signed rows before the live window are held in each market’s store and are not yet answered on a door; the roster says which years are there.'])}
<h2>4 Price</h2>${num(4, ['Build Record: per market, per year — price to be set.'])}
${payBlock(5, 'That is the price of one live read on a door; the Build Record above is a separate line and is not priced yet.')}<h2>6 Machine kit</h2>${kit(host, [`What Data Vintage sells, one page each: ${under('vintage')}.`, `Forwards here (301, path kept): ${FAM.vintage.join(', ')}.`, 'The room that works these years: <a href="https://hedge-agent.ai/">hedge-agent.ai</a>.'])}`
  },
  ark: {
    title: 'Data Ark — the second copy of every market’s record, write-once, in its own region',
    h1: 'Data Ark: the keep.',
    desc: v => `Data Ark: each market's record and history copied nightly, put-only, to a second cloud in its own region with object lock; ${v.nodes} markets on the roster; read through the same door.`,
    door: c => ({ mcp: GI_MCP, name: 'getissuer apex router (the market door answers from either cloud)' }),
    body: (ctx, v, host) => { const a = (ctx.ark && ctx.ark.nodes) || {}; const rows = Object.keys(a).sort().map(k => [`<code class="nw">${esc(k)}</code>`, `<span class="nw">${esc(a[k].last_write || '')}</span>`, esc(a[k].market_date || ''), `<span class="n">${esc(String(a[k].objects || ''))}</span>`]);
      return `${scale([[esc(String(Object.keys(a).length || '')), 'markets with an ark write', 'ark.json', 'record'], [esc(String(v.nodes)), 'markets on the roster', 'list_nodes', 'issuer']])}
<p class="lead">The keep. Microsoft Azure in-country; an Amazon Web Services copy per market. Not sold.</p>
<p class="lead">Data Ark is where a night’s record goes once it is closed: the files that make up each market’s door and its signed history rows, written to a second cloud in the same country or region, put-only, under an object lock that refuses any overwrite or delete for the retention period. It is the reason a record served last month can still be shown as served.</p>
<h2>1 What it is</h2>${num(1, ['One ark bucket per market, in a region that keeps the record’s residency; written at the close of the market’s sweep, after the green check.', 'Put-only: every object is a new key; nothing is replaced. Object lock holds each version for its retention period.', 'Where a market has a standby on the second cloud, its door answers from there at the same address when the serving cloud stops; <a href="https://agent-swap.ai/">agent-swap.ai</a> lists those markets and which cloud serves now.'])}
<h2>2 What is in it</h2>${num(2, ['The files of each market’s nightly close, with the market date they carry and the count of objects written.', 'The signed history rows of Data Vintage, mirrored on the night they land.', 'Nothing that is not already public record; no prices, no client data.'])}<div class="wrap">${rows.length ? table(['market', 'last ark write', 'market date', 'objects'], rows) : '<p>The ark log did not answer at render.</p>'}</div><p class="src">source: the ark log written at each sweep close (swap/ark.json), read at render</p>
<h2>3 The door a finserv agent calls</h2>${num(3, [`The record itself: the market door named on its roster entry, or any market through <code>${GI_MCP}</code> — the address does not change when the serving cloud does.`, 'Which cloud is answering now, and the last copy to the second cloud: <a href="https://agent-swap.ai/">agent-swap.ai</a>.', `Proof of what was served: the RCO receipt of the read, <code>get_receipt</code> at <code>${RCO_MCP}</code>.`])}
${payBlock(4, 'The copy itself is never sold; what is paid for is a read of the record it protects.')}<h2>5 Machine kit</h2>${kit(host, [`Forwards here (301, path kept): ${FAM.ark.join(', ')}.`, 'The room that keeps these copies: <a href="https://ark-agent.ai/">ark-agent.ai</a>.'])}`; }
  },
  hunter: {
    title: 'hunter-agent — the room for the agent that watches for news on listed companies',
    h1: 'hunter-agent: where the agent that hunts new disclosures works.',
    desc: v => `hunter-agent.ai, the Data Now room: an agent that watches ${v.nodes} markets for new filings, halts and releases each night, on the last sweep of ${v.last}.`,
    door: c => ({ mcp: GI_MCP, name: 'getissuer apex router' }),
    body: (ctx, v, host) => `${scale([[esc(v.events), 'events it can watch', 'list_nodes', 'record'], [esc(v.last), 'newest market date', 'list_nodes', 'pulse']])}
<p class="lead">This room belongs to Data Now. The agent that works here has one job: notice, before a person has to, that something changed for a company its firm holds, sells or covers — a halt, a results release, a director dealing, a change of auditor — and bring back the record line with its link, not a summary of it.</p>
<h2>1 Who works here</h2>${num(1, ['A watch agent at a dealer, a wealth platform, an asset manager or a compliance desk, holding a list of issuers by ISIN, ticker or LEI.', 'It runs after the market’s nightly close and before the desk opens; it does not trade, price or advise.'])}
<h2>2 Its round, in order</h2>${num(2, [`Read the roster and the market dates: <pre>${call('list_nodes', {})}</pre>`, `For each issuer on its list, ask what is new since its last round: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: v.last || today() })}</pre>`, 'For each one, ask whether it still trades on its home register: <code>get_signal</code> — ACM-403 is a halt read from the venue’s own page.', `For the signed text of a disclosure, go to <a href="${IW}">Issuerwire.ai</a>, the product: <code>${IW_MCP}</code>.`, 'Hand back: the event line, its date, its source URL and the receipt id of the read.'])}
<h2>3 What it leaves alone</h2>${num(3, ['Market prices, quotes and order books: none are carried, so none are hunted.', 'Rumour and commentary: an event enters the trail only when a wire, an exchange bulletin or a regulator’s register published it.', 'Its own judgement of materiality: it reports the event type the source gave; the desk decides what matters.', 'Markets it was not asked about: a watch list names its issuers, and the hunter stays inside it.'])}
<h2>4 The door it calls</h2>${num(4, [`<code>${GI_MCP}</code> for any market; the market door from <code>list_nodes</code> when it works one country only. MCP over Streamable HTTP, read-only, no account.`])}
${payBlock(5, 'A hunter that sweeps a long list every night pays per issuer only if it chose to take the offer.')}<h2>6 Machine kit</h2>${kit(host, ['The record this room works: <a href="https://data-now.ai/">data-now.ai</a>.'])}`
  },
  hedge: {
    title: 'hedge-agent — the room for the agent that tests a view against past disclosures',
    h1: 'hedge-agent: where an agent checks a thesis against what companies said before.',
    desc: v => `hedge-agent.ai, the Data Vintage room: an agent that reads each market's earlier years — ${v.hist_markets} market(s) with history held tonight, ${v.hist_rows} signed rows — before it trusts a pattern.`,
    door: c => ({ mcp: GI_MCP, name: 'getissuer apex router' }),
    body: (ctx, v, host) => `${scale([[esc(String(v.hist_markets)), 'markets with history', 'list_nodes · backfill', 'record'], [esc(v.hist_docs), 'source documents behind it', 'list_nodes · backfill', 'issuer']])}
<p class="lead">This room belongs to Data Vintage. The agent here works for an investment team, a risk function or a research desk that wants to know whether a pattern held in earlier years: how often a halt preceded a restatement, how long a results date slipped, which venues issued more bulletins. It needs the past as it was published then, with the date it was read, and it needs to show its sources.</p>
<h2>1 Who works here</h2>${num(1, ['A research or risk agent that runs studies over many issuers and several years, and must cite every row it used.', 'It reads; it never prices, scores or recommends — the study and its conclusions stay with the team that asked.'])}
<h2>2 Its method, in order</h2>${num(2, [`Find out which markets reach back how far: <code>list_nodes</code> — the <code>backfill</code> block of each roster entry (history_from, years held, the year in progress).`, 'Inside the trailing year, pull dated events per issuer with <code>list_events_since</code> and a start date.', 'For a record as it stood before a change, ask <code>get_record</code> with a <code>version</code>.', `Keep the receipt of every read (<code>receipt.decision_id</code>); <code>get_receipt</code> at <code>${RCO_MCP}</code> returns what was read, under which rule, when.`, 'Rows before the live window are held signed per market and are not yet served on a door; a study that needs them waits for the door or asks the operator.'])}
<h2>3 The door it calls</h2>${num(3, [`<code>${GI_MCP}</code> (any market) and each market door listed on the roster; read-only MCP, no account.`])}
${payBlock(4, 'A study touches thousands of records; the reads are free by default and paid only where the team wants the settled receipt.')}<h2>5 Machine kit</h2>${kit(host, [`Forwards here (301, path kept): ${FAM.hedge.join(', ')}.`, 'The years this room works: <a href="https://data-vintage.ai/">data-vintage.ai</a>.'])}`
  },
  arkroom: {
    title: 'ark-agent — the room for the agent that keeps the books of what was read',
    h1: 'ark-agent: where an agent proves, later, what it was given.',
    desc: v => `ark-agent.ai, the Data Ark room: an agent that files the receipt of every read and can show, months later, the record as it was served — across ${v.nodes} markets.`,
    door: c => ({ mcp: RCO_MCP, name: 'RCO — the Record of Cleared Orders' }),
    body: (ctx, v, host) => `${scale([[esc(String(v.nodes)), 'markets whose reads it files', 'list_nodes', 'record']])}
<p class="lead">This room belongs to Data Ark. The agent here is the record-keeper of a firm’s other agents: when a supervisor, an auditor or a client asks what a decision relied on, it produces the receipt, the record version that was served, and the copy that could not have been changed since.</p>
<h2>1 Who works here</h2>${num(1, ['A books-and-records agent beside a firm’s research, onboarding or product-review agents; it files, it does not decide.'])}
<h2>2 What it files, and where it finds it</h2>${num(2, ['The receipt id carried on each answer of a market door (<code>receipt.decision_id</code>, also the header <code>X-RCO-Decision-Id</code>).', `The signed receipt behind that id: <pre>${call('get_receipt', { decision_id: '<decision_id>' })}</pre> at <code>${RCO_MCP}</code> — what was cleared, the rule and its version, the records read, the signal, the issuing door, its signature and the ledger transaction id.`, `The record as served: its <code>signature</code> block verifies against <code>${JWKS}</code>; <code>get_record</code> with a <code>version</code> returns that version again.`, 'The second copy: each market’s ark write, put-only under object lock; the last write per market is on <a href="https://agent-swap.ai/">agent-swap.ai</a>.'])}
<h2>3 Questions it is built to answer</h2>${num(3, ['“Which version of this issuer’s record did our onboarding agent read on the day the account opened?” — the receipt names the record and its hash; the version call returns it.', '“Was the security halted when the research note went out?” — the receipt carries the signal the door gave at that time, ACM-200 or ACM-403.', '“Could anyone have edited what we relied on?” — the record’s signature still verifies, and the night’s copy sits under object lock in the market’s own region.', '“Who served it?” — the issuing door is on the receipt, signed with its own key.'])}
<h2>4 The door it calls</h2>${num(4, [`<code>${RCO_MCP}</code> for receipts (free to read, no account) and <code>${GI_MCP}</code> for the records they point at.`])}
${payBlock(5, 'Receipts are read free; a paid read leaves the settlement on its receipt, which is what this room files.')}<h2>6 Machine kit</h2>${kit(host, ['The copies this room keeps: <a href="https://data-ark.ai/">data-ark.ai</a>.'])}`
  },
  record: {
    title: 'data-record — the Capital Markets Record, one signed record per listed security',
    h1: 'data-record: what a Capital Markets Record is, field by field.',
    desc: v => `data-record.ai: the Capital Markets Record (CMR) — ${v.records} records live across ${v.nodes} markets tonight, each field sourced, each record signed Ed25519 and verifiable.`,
    door: c => ({ mcp: GI_MCP, name: 'getissuer apex router' }),
    body: (ctx, v, host) => { const e = exOf(ctx); return `${scale([[esc(v.records), 'records served', 'list_nodes', 'issuer'], [esc(String(v.nodes)), 'markets', 'list_nodes', 'record']])}
<p class="lead">The Capital Markets Record (CMR) is the unit everything else here is built from: one record per listed security on its home venue, keyed <code>&lt;market&gt;-cm-kg/&lt;venue&gt;/&lt;code&gt;</code>, carrying who the issuer is, where it trades, which identifiers bind it, and what it disclosed — with the source of every field beside the field.</p>
<h2>1 The shape</h2>${num(1, ['<code>cmr</code>, <code>node</code>, <code>as_of</code>, <code>version</code> — the key, the market, the sweep date, the version number.', '<code>identity</code> — name, ticker, venue, ISIN, LEI, security type, jurisdiction, auditor, registry numbers; each an object of <code>value</code>, <code>source_url</code>, <code>read_by</code>, <code>state</code>.', '<code>events</code> — dated, typed disclosures of the trailing twelve months with their URLs; <code>halt</code> — the venue’s halt flag with its read time.', '<code>signature</code> — Ed25519 (kid <code>allooloo-cmr-2026-10</code>), a detached JWS over the record’s canonical JSON (keys sorted, compact) without the signature member.'])}
<h2>2 Verifying one</h2>${num(2, [`Keyring: <code>${JWKS}</code> (also <code>/.well-known/jwks.json</code> on every market door).`, 'Take the record, drop <code>signature</code>, sort keys at every level, serialise compact, base64url it, join to <code>signature.protected</code> with a dot, verify <code>signature.signature</code> with the key the kid names.', 'A record whose signature does not verify is not a record served by this operator.'])}
<h2>3 The door a finserv agent calls</h2>${num(3, [`<pre>${call('get_record', { identifier: e.isin })}</pre> at <code>${esc(e.door)}</code> or any market through <code>${GI_MCP}</code>.`, e.url ? `Plain HTTP: <code>GET ${esc(e.url)}</code>.` : 'Plain HTTP: <code>GET https://&lt;door&gt;/record/&lt;venue&gt;/&lt;code&gt;</code>.', `<a href="${KYP}">KYP</a>, the product, is the Know Your Product file built on these records.`])}
<h2>4 The three states of a field</h2>${num(4, ['<code>sourced</code> — copied from a registry, an exchange list or a tag where the value is published as data.', '<code>filled</code> — read by an engine from a page the issuer or venue published, with the engine named in <code>read_by</code>.', '<code>confirmed</code> — read again at the source of record and found the same.', 'A field with no value carries a reason in its place; a reader sees the gap, never a guess.'])}
${payBlock(5, 'One record is one read, whether it comes back by MCP or by plain HTTP.')}<h2>6 Machine kit</h2>${kit(host)}`; }
  },
  eco: {
    title: 'data-eco — the Electronic Compliance Object, the rules of each market as a signed object',
    h1: 'data-eco: each market’s rules, as one object an agent can read.',
    desc: v => `data-eco.ai: the Electronic Compliance Object (ECO) — one signed object per market naming its regulator, its duty line, its halt page and its disclosure channel; ${v.nodes} markets live on the roster.`,
    door: c => ({ mcp: GI_MCP, name: 'getissuer apex router (get_signal reads the ECO)' }),
    body: (ctx, v, host) => `${scale([[esc(String(v.nodes)), 'markets with a live door', 'list_nodes', 'record']])}
<p class="lead">An Electronic Compliance Object (ECO) is a market’s rule book reduced to the fields an agent needs before it acts on a record from that market: who supervises it, what duty a distributor carries there, where the venue publishes halts and suspensions, which channel carries disclosure, and which identifiers the register accepts. Each field is sourced to the regulator’s or the venue’s own page, or left blank with the pages that were checked.</p>
<h2>1 Where it lives</h2>${num(1, ['One host per market: <code>https://&lt;market&gt;-eco.ai/</code>, with the object at <code>/eco.json</code> and the ACM-68000 signal list at <code>/signals.json</code>.', 'Each object is signed Ed25519 (kid <code>allooloo-eco-2026-10</code>); a source page that changes is flagged on the monthly re-read and the field goes back to the hunter — it is never rewritten by guess.'])}
<h2>2 The markets live tonight</h2><div class="wrap">${table(['market', 'ECO', 'duty line on the roster'], v.live.map(n => { const cc = n.node.split('-')[0]; return [`<code class="nw">${esc(n.node)}</code>`, `<a href="https://${cc}-eco.ai/">${cc}-eco.ai</a>`, esc(n.duty || '')]; }))}</div><p class="src">source: list_nodes (field duty), read at render</p>
<h2>3 The door a finserv agent calls</h2>${num(3, [`One call turns the object into an answer for a security: <pre>${call('get_signal', { identifier: exOf(ctx).isin })}</pre> at <code>${GI_MCP}</code> — ACM-200 trading on its home register, ACM-403 halted, ACM-404 not on the register, ACM-451 read the filing.`, 'The object itself: <code>GET https://&lt;market&gt;-eco.ai/eco.json</code>.'])}
${payBlock(4, 'A signal for a security is one read on the router; the ECO pages themselves are free to fetch.')}<h2>5 Machine kit</h2>${kit(host)}`
  },
  rco: {
    title: 'data-rco — the Record of Cleared Orders, a signed receipt for every decision',
    h1: 'data-rco: the receipt that says what an agent was cleared to rely on.',
    desc: v => `data-rco.ai: the Record of Cleared Orders (RCO) — a signed receipt for each cleared read on the ${v.nodes} market doors, readable by anyone at ${RCO_MCP}.`,
    door: c => ({ mcp: RCO_MCP, name: 'RCO — the Record of Cleared Orders' }),
    body: (ctx, v, host) => `${scale([[esc(String(v.nodes)), 'market doors that write receipts', 'list_nodes', 'record']])}
<p class="lead">The Record of Cleared Orders (RCO) is the ledger behind every answer a door gives an outside agent. When a market door resolves an identifier, it assigns a decision id, answers with it, and writes a receipt that names what was cleared, for which class of actor, under which rule and version, from which records, with which signal — signed by the door that issued it and anchored in a confidential ledger.</p>
<h2>1 What a receipt carries</h2>${num(1, ['<code>decision_id</code> and the object cleared: an ISIN, a ticker, an LEI or a CMR key.', 'The actor class (an AI agent over MCP), the rule and its version, the records read with their hashes and signatures, the signal (ACM-200, ACM-404 …), the time.', 'The issuing door, its Ed25519 signature (kid <code>allooloo-rco-2026-10</code>) and the ledger transaction id. No personal data, no amounts.'])}
<h2>2 Who writes, who reads</h2>${num(2, ['Writers: authorised doors only — the market doors, the getissuer router, the ECO pages and licensed firms holding an office key.', 'Readers: anyone, free, no account. A receipt is permanent; a second read never changes the first.'])}
<h2>3 The door a finserv agent calls</h2>${num(3, [`<pre>${call('get_receipt', { decision_id: '<decision_id>' })}</pre> at <code>${RCO_MCP}</code>.`, 'Where the id comes from: the <code>receipt</code> block on a door’s answer and the header <code>X-RCO-Decision-Id</code>.'])}
<h2>4 Why a firm keeps them</h2>${num(4, ['A supervisor asks what an automated process relied on: the receipt is the answer, dated and signed by a party other than the firm.', 'A record changes after a decision: the receipt still names the version and hash that was read, so the decision is judged against what was known then.', 'A dispute over a paid read: the settlement transaction rides on the receipt beside the read it paid for.', 'Several agents, one trail: every door writes to the same ledger, so receipts from different markets line up in one place.'])}
${payBlock(5, 'Reading a receipt is always free; the receipt of a paid read names its settlement.')}<h2>6 Machine kit</h2>${kit(host)}`
  }
};

// ZONES-03: the seven pages join the table with the same helpers
Object.assign(P, Z3.build({ esc, num, scale, call, exOf, kit, payBlock, GI_MCP, IW, IW_MCP, today }));
const under = t => Z3.UNDER[t].map(k => `<a href="https://${Z3.host3(k)}/">${esc(P[k].title.split(' — ')[0])}</a> (${Z3.host3(k)})`).join(' · ');

export function labelZ(c) { return P[c.key].title; }
export function descZ(c, live) { return P[c.key].desc(vals({ live })); }
export function targetZ(c) { const d = P[c.key].door(c); return { kind: 'apex', mcp: d.mcp, agent: `${APEX_AGENT}/.well-known/agent-card.json`, openapi: `${APEX}/openapi.json`, mcpjson: `${APEX}/mcp.json`, name: d.name }; }
export function pageArgsZ(c, ctx, host) { const v = vals(ctx); const p = P[c.key]; return { title: p.title, h1: p.h1, state: 'live', asOf: v.last || today(), body: p.body(ctx, v, host) + contactSection(host), meta: { node: 'estate', as_of: v.last || today() } }; }
export function factsZ(c, host, live, ctx) {
  const v = vals(ctx || { live }); const p = P[c.key]; const d = p.door(c);
  return { domain: host, kind: ['now', 'vintage', 'ark'].includes(c.key) ? 'theme' : ['hunter', 'hedge', 'arkroom'].includes(c.key) ? 'room' : 'content', title: p.title, description: p.desc(v), door: d.mcp, pay: PAY, pay_how: PAY_HOW.replace(/<[^>]+>/g, ''), operator: OPERATOR, corporate: CORPORATE, contact: CONTACT,
    as_of: v.last || today(), surface_version: SURFACES_VERSION, source: 'public-record', counts: { issuer_records: Number(v.records) || null, disclosure_events: Number(v.events) || null, markets_live: v.nodes, history_markets: v.hist_markets, history_rows: Number(v.hist_rows) || 0 }, counts_from: 'list_nodes (live on each render)',
    products_named: { KYP: KYP, 'Issuerwire.ai': IW }, price: c.key === 'vintage' ? 'Build Record: per market, per year — price to be set' : c.key === 'cleanroom' ? 'Price to be set.' : undefined, sold_under: Z3.UNDER.now.includes(c.key) ? 'Data Now (https://data-now.ai/)' : Z3.UNDER.vintage.includes(c.key) ? 'Data Vintage (https://data-vintage.ai/)' : undefined, forwards_here: FAM[c.key] || [],
    machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'] };
}
export function llmsZ(c, host, live, ctx) {
  const v = vals(ctx || { live }); const p = P[c.key]; const d = p.door(c);
  return [`# ${host} — ${p.title}`, `1. ${p.desc(v)}`, `2. The door the agent calls: ${d.mcp} (${d.name}); MCP Streamable HTTP, read-only, no account.`, `3. Pay: ${PAY} Reads are free unless the agent asks for the offer (x402-pay: 1); the 402 offer is signed.`,
    c.key === 'vintage' ? '4. Price: Build Record — per market, per year — price to be set.' : c.key === 'cleanroom' ? '4. Price: Price to be set.' : `4. Counts at render (list_nodes): ${v.records} issuer records, ${v.events} dated disclosure events, ${v.nodes} markets live, market date ${v.last}.`,
    `5. Products named on this estate: KYP (${KYP}) and Issuerwire.ai (${IW}).`, (FAM[c.key] || []).length ? `6. Forwards here (301, path kept): ${FAM[c.key].join(', ')}.` : '6. Forwards here: none.',
    `7. Operator: ${OPERATOR}. Corporate: ${CORPORATE}. Contact: ${CONTACT}.`, '8. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt', `9. Surface version: ${SURFACES_VERSION}.`].join('\n') + '\n';
}
export function pathsZ() { return ['/', '/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt']; }
export async function shelfData(env, url) { try { const r = await env.ASSETS.fetch(new URL('/shelf/state.json', url)); return r.ok ? await r.json() : null; } catch (e) { return null; } }   // SHELF-01
export async function arkData(env, url) { try { const r = await env.ASSETS.fetch(new URL('/swap/ark.json', url)); return r.ok ? await r.json() : null; } catch (e) { return null; } }
