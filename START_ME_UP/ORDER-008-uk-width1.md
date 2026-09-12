# ORDER-008 — United Kingdom Width 1: Disclosure
Date: Sept 11 2026 · Node: uk-cm-kg · Fly by wire. Same shape as ORDER-003 (Canada Width 1), UK sources.

## Scope
The corporate issuers in CM-KG\ISSUERS\uk-issuers.xlsx (security type = corporate; funds/ETFs/investment trusts out).
Backfill window: 12 months to date. Then the weekly rail.

## Do
1. Per issuer, events with date, source URL, read-by:
   - Regulatory announcement — RNS via the LSE news explorer / issuer news page; the FCA National Storage Mechanism
     (NSM) search endpoint where it answers. Type by RNS headline category: results, trading update, AGM/GM notice,
     director dealing (PDMR), holdings in company (TR-1), admission/cancellation, suspension/restoration, dividend, name change.
   - Companies House filings — via the API (AGENT KEYS\companieshouse.txt): accounts filed, confirmation statement,
     officer appointments/resignations, name changes, charges. Filing date and description from the filing history.
   - Exchange notices — LSE market notices, AIM admissions/cancellations, Aquis notices, where public.
   - Newswire release — the issuer's newswire of habit from Width 0, then the other wires.
2. Write CM-KG\DISCLOSURE\uk-disclosure.xlsx (Events, Coverage, Gaps, Method; Arial, frozen, AutoFilter, live COUNTIFS)
   and CM-KG\DISCLOSURE\events\uk-events.jsonl. Same fields as Canada plus rns_category and ch_filing_type.
3. Blank is blank. No event without a URL. Ambiguous name matches to Gaps under the distinctive-token rule
   (unique across the 1,570-row roster AND not a common English word). Aliases: Companies House "previous names" are a
   source — use them.
4. Rails under CM-KG\RAILS\uk-width1\ with README. Weekly refresh = 7-day window, idempotent on (ticker, type, date, URL).
5. HITL — needs MK: list any source that needs an account, key or click, separately from broken sources.
6. Report: events by type, issuers with zero events (count + first 20), fill by source, Gaps, which sources answered
   machines and which refused, HITL list, what is broken.

## Don't
No test harness. No prices or market data. No fetch behind a login. No reference to any other company's estate.
