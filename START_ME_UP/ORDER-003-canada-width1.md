# ORDER-003 — Canada Width 1: Disclosure
Date: Sept 10 2026 · Node: ca-cm-kg · Fly by wire.

## What it is
The disclosure trail per issuer — the fact that a filing or event exists, when, and where. Not the documents.
This is the layer a dealer's product-knowledge duty actually needs, and the recurring line the desk will serve.

## Scope
The 2,851 corporate issuers in CM-KG\ISSUERS\ca-issuers.xlsx (Security type = corporate). Funds, ETFs and CDRs
are out of this order. Backfill window: 12 months to date. Then the rail runs daily.

## Do
1. Per issuer, collect events of these types, each with date, source, URL, and read-by:
   - Newswire release (title, wire, date) — from the issuer's newswire of habit first, then the other four.
   - Exchange bulletin — TSX / TSXV / CSE / Cboe Canada daily bulletins: listings, delistings, name and symbol
     changes, consolidations, halts and resumes, transfers between exchanges.
   - Halt / resume — CIRO trading-halt notices, cross-checked against exchange bulletins.
   - Corporate action — CDS bulletins: record dates, dividend and distribution dates, splits, rights, exchanges.
   - Financial statement date — from the newswire release announcing results (title match), not from SEDAR+.
   - AGM / record date — from the newswire or bulletin that announces it.
   - Insider and early-warning filings — SEDI and the early-warning system are 403 to machines (ORDER-001).
     Do NOT attempt. Record the column as broken; the newswire copy of an early-warning press release counts
     as an event when one exists.
2. Write CM-KG\DISCLOSURE\ca-disclosure.xlsx: one Events tab (one row per event, keyed on ticker + ISIN + exchange),
   a Coverage tab (events per issuer, issuers with zero events, live COUNTA/COUNTIF), a Gaps tab, a Method tab.
   Arial, frozen headers, AutoFilter. Source URL and read-by on every row.
3. Also write CM-KG\DISCLOSURE\events\ca-events.jsonl — one line per event, same fields — the machine copy the
   node and the desk will read.
4. Blank is blank. No event without a URL. No date inferred from a headline. Ambiguous wire results (name match
   on a different issuer) go to Gaps, not Events.
5. Rails under CM-KG\RAILS\ca-width1\ with README naming each worker, source, fields, read-by label, and the
   known-broken list. Daily refresh = last 48 hours, idempotent on (ticker, type, date, URL).
6. Report: events by type, issuers with zero events (count and the first 20 names), fill by source,
   Gaps count, what is broken.

## Don't
- No test harness before the run.
- No SEDAR+ or SEDI fetch attempts — they are broken and reported; do not burn the run on them.
- No prices, quotes, volumes, or market data in any event row.
- No reference to any other company's estate, code, or canon.
