// ZONES-03 (CEO order 2026-10-27) — seven pages on the ZONES-02 template (zones02.js merges them into its page table and classifier; kind 'zone02').
// Under Data Vintage (linked from data-vintage.ai): data-replay.ai · data-bench.ai · data-cleanroom.ai · data-review.ai.
// Under Data Now (linked from data-now.ai): data-score.ai · data-timeline.ai · data-events.ai.
// Forwards (301, path kept): data-cleanroom.io and data-cleanroom.org → data-cleanroom.ai.
// Copy fence: KYP and Issuerwire.ai are the products; these seven are what Data Now and Data Vintage sell — never called products or divisions.
// A figure the wire does not serve yet is not printed: each page says what it is, then what is callable today, and nothing more. Counts live from
// list_nodes on every render. Pay line on every page. Cleanroom: "Price to be set."
export const FAM3 = { cleanroom: ['data-cleanroom.io', 'data-cleanroom.org'] };
export const UNDER = { vintage: ['replay', 'bench', 'cleanroom', 'review'], now: ['score', 'timeline', 'events'] };
export function classify3(h) {
  let m;
  if ((m = h.match(/^data-cleanroom\.(io|org)$/))) return { kind: 'redirect', canonical: 'https://data-cleanroom.ai', status: 301 };
  if ((m = h.match(/^data-(replay|bench|cleanroom|review|score|timeline|events)\.ai$/))) return { kind: 'zone02', key: m[1] };
  return null;
}
export const host3 = k => `data-${k}.ai`;
// H: the helpers of zones02.js — { esc, num, scale, call, exOf, kit, payBlock, GI_MCP, IW, IW_MCP, today }
export function build(H) {
  const { esc, num, scale, call, exOf, kit, payBlock, GI_MCP, IW, IW_MCP, today } = H;
  const up = (theme) => theme === 'vintage' ? 'Sold under <a href="https://data-vintage.ai/">Data Vintage</a>.' : 'Sold under <a href="https://data-now.ai/">Data Now</a>.';
  const histRow = v => [[esc(String(v.hist_markets)), 'markets with years held', 'list_nodes · backfill', 'record'], [esc(String(v.hist_years)), 'market-years held', 'list_nodes · backfill', 'pulse'], [esc(v.hist_rows), 'signed history rows', 'list_nodes · backfill', 'issuer']];
  const liveRow = v => [[esc(v.records), 'issuer records', 'list_nodes', 'issuer'], [esc(v.events), 'dated disclosure events', 'list_nodes', 'record'], [esc(String(v.nodes)), 'markets live', 'list_nodes', 'pulse']];
  const D = c => ({ mcp: GI_MCP, name: 'getissuer apex router' });
  // each page takes its example from a different market's roster entry, so no two pages carry the same calls
  const exAt = (ctx, cc) => { const n = (ctx.live || {})[`${cc}-cm-kg`] || {}; return (n.example || {}).isin || exOf(ctx).isin; };
  const who = (t, items) => `<h2>${t}</h2>` + num('W', items);
  // SHELF-01: per tool, the markets live read from the ledger (ctx.shelf = /shelf/state.json); a door tool is served once a market door lists it
  const liveOf = (ctx, t) => { const st = ctx.shelf || {}; if (t === 'timeline' || t === 'events') { const ms = ((st.door_tools || {})[t === 'timeline' ? 'get_timeline' : 'list_events']) || []; return ms.map(m => [m, null]); }
    return Object.entries(((st.tools || {})[t]) || {}).map(([m, ys]) => [m, ys]); };
  const liveLine = (ctx, t) => { const L = liveOf(ctx, t); const NM = { replay: 'Replay', bench: 'Bench', review: 'Review', score: 'Score', timeline: 'Timeline', events: 'Events' }; return `<p class="src">${NM[t] || t} on: ${L.length ? L.map(([m, ys]) => esc(m) + (ys && ys.length ? ` ${esc(String(Math.min(...ys)))}–${esc(String(Math.max(...ys)))}` : '')).join(', ') : 'no market yet'} (ledger)</p>`; };
  const isLive = (ctx, t) => liveOf(ctx, t).length > 0;
  const pending = (ctx, t, n, items) => isLive(ctx, t) ? '' : `<h2>${n} Not answered on a door yet</h2>` + num(n, items);

  return {
    replay: {
      title: 'Replay — the issuer record as it stood on a given date, from 2021',
      h1: 'Replay: the record as it stood on any date, 2021 forward.',
      desc: v => `Replay, under Data Vintage: the issuer record as it stood on a date from 2021 forward. Callable today: a record's earlier versions, its events inside the twelve-month window, and which market-years are held (${v.hist_markets} markets, ${v.hist_years} market-years, read from list_nodes at render).`,
      door: D,
      body: (ctx, v, host) => `${scale(histRow(v))}
<p class="lead">Replay answers one question about a listed company: what did its public record say on that day. ${up('vintage')}</p>
${who('Who reads it', ['A compliance reviewer reconstructing what a firm could have known on the day it acted.', 'A back-tester who must keep tomorrow’s facts out of yesterday’s decision.', 'An auditor’s agent tracing a disclosure back to the date it first appeared.'])}
${liveLine(ctx, 'replay')}<h2>1 Callable today</h2>${num(1, [...(isLive(ctx, 'replay') ? [`On a market door: <pre>${call('get_record', { identifier: exAt(ctx, 'us'), as_of: '2023-06-30' })}</pre> — the record as it stood on that date, from the sealed market-year (manifest id and year signature on the answer); a date in a year not sealed answers 'not sealed'.`] : []), `An earlier state of one record, by version number: <pre>${call('get_record', { identifier: exAt(ctx, 'uk'), version: 1 })}</pre> That version comes back whole: its as_of date, its version number, and each identity field with the page it was read from, who read it and its state — the name, ISIN or LEI as it stood then, not as corrected since.`, `What the issuer disclosed since a date inside the live twelve-month window: <pre>${call('list_events_since', { identifier: exAt(ctx, 'uk'), since: '2025-11-01' })}</pre>`, `Which market-years are held: <code>list_nodes</code> — each roster entry with history carries <code>backfill</code> (history_from, years, rows, documents).`])}
${pending(ctx, 'replay', 2, ['A read addressed by calendar date. Version history on a door starts the day the record first went on it; the earlier years held under Data Vintage sit as signed rows in the market’s own store. Until a dated read is answered, Replay is the three calls above.'])}
${who('What it leaves out', ['Restated figures: Replay shows the record as filed then, and a later correction stays in the later version.', 'Prices and quotes of the day; the record carries none.', 'Anything that was not on the public record on that date, however soon it appeared after.'])}
${payBlock(3, 'A replay of one issuer is one or two reads.')}<h2>4 Machine kit</h2>${kit(host, [up('vintage')])}`
    },
    bench: {
      title: 'Bench — a test set of issuers, dated questions and sourced answers',
      h1: 'Bench: issuers × dated questions × the answer with its source page.',
      desc: v => `Bench, under Data Vintage: a test set of issuers, dated questions and each answer with the page it came from. Callable today: the sourced record every answer cites, on ${v.nodes} live markets; the test set itself is not served on a door yet.`,
      door: D,
      body: (ctx, v, host) => `${scale(liveRow(v))}
<p class="lead">Bench is for the team that has to show its agent gets listed-company facts right. Each item pairs an issuer and a date with a question and the answer, and the answer names the source page it was read from. ${up('vintage')}</p>
${who('Who reads it', ['An evaluation team scoring a model or an agent on listed-company facts before it goes near a client.', 'A vendor proving accuracy to a buyer’s model-risk function, item by item.'])}
${who('The shape of one item', ['The issuer, by CMR key and ISIN; the date the question is asked as of; the question in plain words; the expected answer; the URL of the page that settles it.', 'Questions of the kind a desk asks: which firm signed the last annual report, whether trading was halted on a given day, what the legal name was as filed.'])}
${liveLine(ctx, 'bench')}<h2>1 Callable today</h2>${num(1, [...(isLive(ctx, 'bench') ? [`At <code>https://mcp.data-bench.ai/mcp</code>: <code>get_bench</code> for the questions, <code>score_bench</code> for a signed scorecard; the answers never leave that door.`] : []), `The record an answer is checked against; every field names its source page, who read it and its state: <pre>${call('get_record', { identifier: exAt(ctx, 'de') })}</pre>`, `The dated disclosures behind an answer: <pre>${call('list_events_since', { identifier: exAt(ctx, 'de'), since: v.last || today() })}</pre>`])}
${pending(ctx, 'bench', 2, ['The test set and its scoring. Until they are, Bench is the sourced record above.'])}
${who('What it leaves out', ['Opinions, forecasts and price questions: every item has one answer a public page settles.', 'The scoring of any particular vendor; the set measures, it does not rank.'])}
${payBlock(3, 'Checking one answer is one read.')}<h2>4 Machine kit</h2>${kit(host, [up('vintage')])}`
    },
    cleanroom: {
      title: 'Cleanroom — the licensed corpus, per market-year',
      h1: 'Cleanroom: the licensed corpus, per market-year.',
      desc: v => `Cleanroom, under Data Vintage: the licensed corpus of the record, per market-year. Price to be set. Held tonight: ${v.hist_markets} markets, ${v.hist_years} market-years, ${v.hist_rows} signed rows (list_nodes at render).`,
      door: D,
      body: (ctx, v, host) => `${scale(histRow(v))}
<p class="lead">Cleanroom is the record licensed as a corpus, one market-year at a time: the signed history rows of a market for a calendar year, for a model team or a research desk that needs the whole year rather than a call at a time. ${up('vintage')}</p>
${who('Who licenses it', ['A model team training or evaluating on company disclosures under a written licence.', 'A research desk running a study across a full year of one market’s filings.'])}
${who('What one market-year holds', ['Every signed row the backfill read for that market and calendar year, with the reference of the source document it came from.', 'The Ed25519 signature on each row and the key id it was signed under, so the licensee can check every row it received.', 'Public record only: no prices, no client data. A licence names its market and its year.'])}
<h2>1 Callable today</h2>${num(1, [`What is held, per market: <code>list_nodes</code> at <code>${GI_MCP}</code> — <code>backfill</code> names the years held, the rows and the source documents.`, 'Any single record or event in the live window, on the market door, as on every page of this estate.'])}
${liveLine(ctx, 'bench')}<h2>2 Price</h2>${num(2, ['Price to be set.'])}
${who('What it leaves out', ['Live records and tonight’s sweep: those are read call by call on the doors.', 'Any personal data beyond what an issuer itself filed on the public record.'])}
${payBlock(3, 'That is the price of one live read on a door; the corpus licence above is a separate line and is not priced yet.')}<h2>4 Machine kit</h2>${kit(host, [`Forwards here (301, path kept): ${FAM3.cleanroom.join(', ')}.`, up('vintage')])}`
    },
    review: {
      title: 'Review — the per-market, per-year disclosure report from the sealed layer',
      h1: 'Review: each market’s disclosure year — counts, latency, concentration.',
      desc: v => `Review, under Data Vintage: a per-market, per-year disclosure report from the sealed layer — counts, latency, concentration. Callable today: the counts per market (${v.hist_markets} markets with years held, ${v.hist_rows} rows, ${v.hist_docs} documents, list_nodes at render).`,
      door: D,
      body: (ctx, v, host) => `${scale([[esc(String(v.hist_markets)), 'markets with years held', 'list_nodes · backfill', 'record'], [esc(v.hist_rows), 'signed history rows', 'list_nodes · backfill', 'issuer'], [esc(v.hist_docs), 'source documents', 'list_nodes · backfill', 'pulse']])}
<p class="lead">Review reads a market’s year of disclosures back from the sealed layer and reports on it: how many, how late against the period they cover, and how concentrated among issuers. ${up('vintage')}</p>
${who('Who reads it', ['A market-structure analyst comparing disclosure habits between venues.', 'An exchange’s listings team or a regulator’s supervision desk looking at its own market’s year.', 'An index provider checking how evenly news flows across a market’s constituents.'])}
${who('The three measures', ['Counts: disclosures in the year, by type.', 'Latency: days between the end of a reporting period and the filing that reports it.', 'Concentration: how much of the year’s volume sits with the most active issuers.'])}
${liveLine(ctx, 'review')}<h2>1 Callable today</h2>${num(1, [...(isLive(ctx, 'review') ? [`At <code>https://mcp.data-review.ai/mcp</code>: <code>get_review</code> — the signed review of a market-year.`] : []), `The counts: <code>list_nodes</code> — per market, the years held, rows and source documents in <code>backfill</code>.`])}
${pending(ctx, 'review', 2, ['Latency and concentration. Until they are, Review is the counts above.'])}
${who('What it leaves out', ['A league table of individual issuers: the report speaks for a market and a year.', 'Any judgement of whether a disclosure was good, only when and how many.', 'Prices, volumes and market data.'])}
${payBlock(3, 'Reading the counts is one call.')}<h2>4 Machine kit</h2>${kit(host, [up('vintage')])}`
    },
    score: {
      title: 'Score — an issuer’s filing cadence and latency against its exchange and sector',
      h1: 'Score: how often and how late an issuer files, against its exchange and sector.',
      desc: v => `Score, under Data Now: issuer filing cadence and latency against exchange and sector, five years deep. Callable today: the issuer's dated events in the twelve-month window, on ${v.nodes} live markets (list_nodes at render).`,
      door: D,
      body: (ctx, v, host) => `${scale(liveRow(v))}
<p class="lead">Score puts one number beside a listed company: how regularly it files and how long after the period it does so, measured against the other issuers on its exchange and in its sector, over five years. ${up('now')}</p>
${who('Who reads it', ['A credit analyst watching for an issuer that now files later than it used to.', 'A stewardship team that treats filing discipline as one sign of governance.', 'A know-your-issuer desk adding a cadence check to its onboarding file.'])}
${who('What a score is made of', ['The dates of results releases and annual reports, set against the period ends they report.', 'The comparison set: the issuer’s own exchange, and its sector on that exchange.'])}
${liveLine(ctx, 'score')}<h2>1 Callable today</h2>${num(1, [...(isLive(ctx, 'score') ? [`On a market door: <pre>${call('get_score', { identifier: exAt(ctx, 'us') })}</pre> — cadence, latency and silence, each with its exchange and sector percentile.`] : []), `The dated events a score is built from, inside the live twelve-month window: <pre>${call('list_events_since', { identifier: exAt(ctx, 'sg'), since: '2025-11-01' })}</pre>`])}
${pending(ctx, 'score', 2, ['The score, the comparison and the five-year depth. Until they are, Score is the dated events above.'])}
${who('What it leaves out', ['A view to buy, sell or hold; a cadence number is not advice.', 'Price, volume and the contents of the results themselves — only their dates.'])}
${payBlock(3, 'One issuer’s events are one read.')}<h2>4 Machine kit</h2>${kit(host, [up('now')])}`
    },
    timeline: {
      title: 'Timeline — the dated event history of any issuer, in one call',
      h1: 'Timeline: everything an issuer disclosed, in date order, one call.',
      desc: v => `Timeline, under Data Now: the dated event history of any issuer, one call. Callable today: list_events_since on the market door, twelve-month window; ${v.events} dated events across ${v.nodes} markets (list_nodes at render).`,
      door: D,
      body: (ctx, v, host) => `${scale(liveRow(v))}
<p class="lead">Timeline is the disclosure trail of one company laid out by date: each event typed as its source typed it, with the link to the page it was read from. ${up('now')}</p>
${who('Who reads it', ['An analyst opening coverage on a company and reading its year in order.', 'A due-diligence team before an engagement, looking for what the company said and when.', 'A newsroom’s research agent checking a date before it is printed.'])}
${who('What each line carries', ['The date; the type the source gave it; the title; the URL of the page it was read from; who read it; its state.'])}
${liveLine(ctx, 'timeline')}<h2>1 Callable today</h2>${num(1, [...(isLive(ctx, 'timeline') ? [`On a market door: <pre>${call('get_timeline', { identifier: exAt(ctx, 'au') })}</pre> — every line on the record, oldest first, no window cap, each line signed.`] : []), `One call, one issuer, in date order: <pre>${call('list_events_since', { identifier: exAt(ctx, 'au'), since: '2025-11-01' })}</pre> The window is twelve months; the signed text of each disclosure is at <a href="${IW}">Issuerwire.ai</a>, the product, <code>${IW_MCP}</code>.`])}
${pending(ctx, 'timeline', 2, ['The years before the live window. Until they are, Timeline is the twelve months above.'])}
${who('What it leaves out', ['Summaries written by us: each line keeps the title its source gave.', 'Commentary, rumour and the press’s own stories about the company.', 'Market prices around each date.'])}
${payBlock(3, 'One timeline is one read.')}<h2>4 Machine kit</h2>${kit(host, [up('now')])}`
    },
    events: {
      title: 'Events — listings, delistings, renames, domicile and auditor changes, dated, across the markets',
      h1: 'Events: IPOs, delistings, renames, domicile and auditor changes, dated.',
      desc: v => `Events, under Data Now: IPOs, delistings, renames, domicile and auditor changes across ${v.nodes} markets, dated. Callable today: each issuer's typed events, its earlier record versions and its register signal (list_nodes at render).`,
      door: D,
      body: (ctx, v, host) => `${scale(liveRow(v))}
<p class="lead">Events is the corporate-change stream: a company arriving on a list, leaving it, changing its name, its domicile or its auditor, each with its date and source. ${up('now')}</p>
${who('Who reads it', ['An index provider maintaining its constituent lists.', 'A data vendor reconciling identifiers after a company renames itself.', 'A fund administrator following a redomiciliation through to the new register.'])}
${who('The five changes', ['A listing: the first day a security appears on its exchange’s list.', 'A delisting: the day it leaves that list.', 'A rename: a new legal name filed with the company registry.', 'A domicile change: a new jurisdiction of incorporation.', 'An auditor change: a different firm signing the annual report.'])}
${liveLine(ctx, 'events')}<h2>1 Callable today</h2>${num(1, [...(isLive(ctx, 'events') ? [`On a market door: <pre>${call('list_events', { type: 'delisting', since: '2026-09-01' })}</pre> — with the register's type map and its gaps.`] : []), `An issuer’s events as its source typed them: <pre>${call('list_events_since', { identifier: exAt(ctx, 'us'), since: '2025-11-01' })}</pre>`, `Its record as it stood before a change, by version: <pre>${call('get_record', { identifier: exAt(ctx, 'us'), version: 1 })}</pre>`, 'Whether it is still on its home register: <code>get_signal</code> (ACM-200 trading · ACM-403 halted · ACM-404 not on the register).'])}
${pending(ctx, 'events', 2, ['One stream of these changes across all markets. Until it is, Events is the three calls above, per issuer.'])}
${who('What it leaves out', ['Share-capital actions such as splits and dividends, unless the source itself typed them as an event.', 'Deal rumours and reported talks: a change enters when a register or an exchange records it.'])}
${payBlock(3, 'Each issuer checked is a read.')}<h2>4 Machine kit</h2>${kit(host, [up('now')])}`
    }
  };
}
