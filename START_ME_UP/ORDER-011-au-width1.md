# ORDER-011 — Australia Width 1: Disclosure
Date: Sept 11 2026 · Node: au-cm-kg · Fly by wire · pond-native. Same shape as ORDER-008 (UK Width 1), Australian sources.

## Scope
Corporate issuers in CM-KG\ISSUERS\au-issuers.xlsx (security type = corporate; ETFs, LICs, LITs, REITs-as-trusts out to Width 1-F).
Backfill window: 12 months to date. Then the weekly rail under the pond and the au lock.

## Do
1. Per issuer, events with date, source URL, read-by:
   - ASX announcements — the ASX announcements platform per company (public JSON per ASX code, as found in Part B recon).
     Type by ASX announcement category: results (Appendix 4E/4D, half-year/full-year), quarterly (Appendix 4C/5B),
     trading halt / suspension / reinstatement, substantial holder (Form 603/604/605), director interest (Appendix 3Y/3X/3Z),
     Appendix 3B (issue of securities), dividend/distribution, AGM notice and results, name change, price-sensitive flag carried.
   - ASIC — company register events where public (name changes, status changes, deregistration) from the weekly bulk file.
   - NSX — official list RSS. TMX Australia (Cboe Australia): reCAPTCHA-blocked — record as HITL, do not attempt.
   - Newswire release — issuer's newswire of habit from Width 0, then the other wires (Tavily).
2. Write CM-KG\DISCLOSURE\au-disclosure.xlsx (Events, Coverage, Gaps, Method) and events\au-events.jsonl.
   Fields as UK plus asx_category and price_sensitive (true/false as published).
3. Blank is blank. No event without a URL. Distinctive-token rule on wire titles (unique across the AU roster AND not a common English word).
4. Rails under CM-KG\RAILS\au-width1\ with README. Weekly refresh = 7-day window, pond drop, idempotent on (code, type, date, URL).
5. Report: events by type, issuers with zero events (count + first 20), fill by source, Gaps, which sources answered machines
   and which refused, HITL list, what is broken, spend line.

## Don't
No test harness. No prices or market data. No fetch behind a login. No reference to any other company's estate.
