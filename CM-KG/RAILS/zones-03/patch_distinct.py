r"""ZONES-03 — shared-text pass: each of the seven pages gets its own readers and its own content section, and its example from a different market."""
import shutil, os
p = r'C:\ALLOOLOO\CM-KG\ESTATE\worker\zones03.js'
pre = p + '.pre-sharedtext-20261027'
if not os.path.exists(pre): shutil.copy2(p, pre)
s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
rep("  const D = c => ({ mcp: GI_MCP, name: 'getissuer apex router' });",
"""  const D = c => ({ mcp: GI_MCP, name: 'getissuer apex router' });
  // each page takes its example from a different market's roster entry, so no two pages carry the same calls
  const exAt = (ctx, cc) => { const n = (ctx.live || {})[`${cc}-cm-kg`] || {}; return (n.example || {}).isin || exOf(ctx).isin; };
  const who = (t, items) => `<h2>${t}</h2>` + num('W', items);""")
# replay
rep("""${up('vintage')}</p>
<h2>1 Callable today</h2>${num(1, [`An earlier state of one record, by version number: <pre>${call('get_record', { identifier: exOf(ctx).isin, version: 1 })}</pre>`, `What the issuer disclosed since a date inside the live twelve-month window: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: '2025-11-01' })}</pre>`""",
"""${up('vintage')}</p>
${who('Who reads it', ['A compliance reviewer reconstructing what a firm could have known on the day it acted.', 'A back-tester who must keep tomorrow’s facts out of yesterday’s decision.', 'An auditor’s agent tracing a disclosure back to the date it first appeared.'])}
<h2>1 Callable today</h2>${num(1, [`An earlier state of one record, by version number: <pre>${call('get_record', { identifier: exAt(ctx, 'uk'), version: 1 })}</pre> That version comes back whole: its as_of date, its version number, and each identity field with the page it was read from, who read it and its state — the name, ISIN or LEI as it stood then, not as corrected since.`, `What the issuer disclosed since a date inside the live twelve-month window: <pre>${call('list_events_since', { identifier: exAt(ctx, 'uk'), since: '2025-11-01' })}</pre>`""")
rep("${num(2, ['A read addressed by calendar date. Until it is, Replay is the three calls above.'])}",
    "${num(2, ['A read addressed by calendar date. Version history on a door starts the day the record first went on it; the earlier years held under Data Vintage sit as signed rows in the market’s own store. Until a dated read is answered, Replay is the three calls above.'])}")
# bench
rep("""<h2>1 Callable today</h2>${num(1, [`The record an answer is checked against; every field names its source page, who read it and its state: <pre>${call('get_record', { identifier: exOf(ctx).isin })}</pre>`, `The dated disclosures behind an answer: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: v.last || today() })}</pre>`])}""",
"""${who('Who reads it', ['An evaluation team scoring a model or an agent on listed-company facts before it goes near a client.', 'A vendor proving accuracy to a buyer’s model-risk function, item by item.'])}
${who('The shape of one item', ['The issuer, by CMR key and ISIN; the date the question is asked as of; the question in plain words; the expected answer; the URL of the page that settles it.', 'Questions of the kind a desk asks: which firm signed the last annual report, whether trading was halted on a given day, what the legal name was as filed.'])}
<h2>1 Callable today</h2>${num(1, [`The record an answer is checked against; every field names its source page, who read it and its state: <pre>${call('get_record', { identifier: exAt(ctx, 'de') })}</pre>`, `The dated disclosures behind an answer: <pre>${call('list_events_since', { identifier: exAt(ctx, 'de'), since: v.last || today() })}</pre>`])}""")
# cleanroom
rep("""rather than a call at a time. ${up('vintage')}</p>""",
"""rather than a call at a time. ${up('vintage')}</p>
${who('Who licenses it', ['A model team training or evaluating on company disclosures under a written licence.', 'A research desk running a study across a full year of one market’s filings.'])}
${who('What one market-year holds', ['Every signed row the backfill read for that market and calendar year, with the reference of the source document it came from.', 'The Ed25519 signature on each row and the key id it was signed under, so the licensee can check every row it received.', 'Public record only: no prices, no client data. A licence names its market and its year.'])}""")
# review
rep("""and how concentrated among issuers. ${up('vintage')}</p>""",
"""and how concentrated among issuers. ${up('vintage')}</p>
${who('Who reads it', ['A market-structure analyst comparing disclosure habits between venues.', 'An exchange’s listings team or a regulator’s supervision desk looking at its own market’s year.', 'An index provider checking how evenly news flows across a market’s constituents.'])}
${who('The three measures', ['Counts: disclosures in the year, by type.', 'Latency: days between the end of a reporting period and the filing that reports it.', 'Concentration: how much of the year’s volume sits with the most active issuers.'])}""")
# score
rep("""<h2>1 Callable today</h2>${num(1, [`The dated events a score is built from, inside the live twelve-month window: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: '2025-11-01' })}</pre>`])}""",
"""${who('Who reads it', ['A credit analyst watching for an issuer that now files later than it used to.', 'A stewardship team that treats filing discipline as one sign of governance.', 'A know-your-issuer desk adding a cadence check to its onboarding file.'])}
${who('What a score is made of', ['The dates of results releases and annual reports, set against the period ends they report.', 'The comparison set: the issuer’s own exchange, and its sector on that exchange.'])}
<h2>1 Callable today</h2>${num(1, [`The dated events a score is built from, inside the live twelve-month window: <pre>${call('list_events_since', { identifier: exAt(ctx, 'sg'), since: '2025-11-01' })}</pre>`])}""")
# timeline
rep("""<h2>1 Callable today</h2>${num(1, [`One call, one issuer, in date order: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: '2025-11-01' })}</pre>""",
"""${who('Who reads it', ['An analyst opening coverage on a company and reading its year in order.', 'A due-diligence team before an engagement, looking for what the company said and when.', 'A newsroom’s research agent checking a date before it is printed.'])}
${who('What each line carries', ['The date; the type the source gave it; the title; the URL of the page it was read from; who read it; its state.'])}
<h2>1 Callable today</h2>${num(1, [`One call, one issuer, in date order: <pre>${call('list_events_since', { identifier: exAt(ctx, 'au'), since: '2025-11-01' })}</pre>""")
# events
rep("""<h2>1 Callable today</h2>${num(1, [`An issuer’s events as its source typed them: <pre>${call('list_events_since', { identifier: exOf(ctx).isin, since: '2025-11-01' })}</pre>`, `Its record as it stood before a change, by version: <pre>${call('get_record', { identifier: exOf(ctx).isin, version: 1 })}</pre>`""",
"""${who('Who reads it', ['An index provider maintaining its constituent lists.', 'A data vendor reconciling identifiers after a company renames itself.', 'A fund administrator following a redomiciliation through to the new register.'])}
${who('The five changes', ['A listing: the first day a security appears on its exchange’s list.', 'A delisting: the day it leaves that list.', 'A rename: a new legal name filed with the company registry.', 'A domicile change: a new jurisdiction of incorporation.', 'An auditor change: a different firm signing the annual report.'])}
<h2>1 Callable today</h2>${num(1, [`An issuer’s events as its source typed them: <pre>${call('list_events_since', { identifier: exAt(ctx, 'us'), since: '2025-11-01' })}</pre>`, `Its record as it stood before a change, by version: <pre>${call('get_record', { identifier: exAt(ctx, 'us'), version: 1 })}</pre>`""")
open(p, 'w', encoding='utf-8').write(s)
print('patched')
