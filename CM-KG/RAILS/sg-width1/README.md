# sg-width1 — Singapore Width 1 (ORDER-014 Part A), disclosure events over 12 months

Pond-native rail for node `sg-cm-kg`. Workers write into `raw\` (a junction to the open drop `CM-KG\POND\sg-cm-kg\width1\<date>\`); the assembler reads every drop plus the last versioned event set, dedupes on (market, code, type, date, URL), and writes `CM-KG\DISCLOSURE\sg-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\sg-events.jsonl` with a versioned copy under `CM-KG\POND\sg-cm-kg\assembled\<date>\`.

## Sources (SGXNet's API answers 401 to machines — the HITL stands)
| Worker | Source | Read-by label |
|---|---|---|
| sgxnet_search.py | The public SGXNet announcement pages on links.sgx.com (Issuer/Manager, Securities line with code and ISIN, category, broadcast date, sub-title, reference), found per issuer by Tavily (news search over the window + general search restricted to links.sgx.com); a document hit resolves to its page; pages are attributed by their own Securities line | links.sgx.com announcement page (SGXNet record; found by Tavily search) · Tavily search (links.sgx.com) + published_date |
| acra_events.py | ACRA monthly bulk register (Width 0 drop, by UEN): annual return date; non-Live status dated on the dataset build | ACRA register bulk dataset (data.gov.sg, monthly) |
| wire_search.py | Tavily over PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile, Media OutReach, ACN Newswire | Tavily search (wire domains) + published_date / + URL date |

Not sources: The Business Times, The Edge Singapore (paywalled); SGX company pages (403 / Flutter app). Issuer IR announcement pages: no website column at Width 0; Perplexity recovers pages in the Fill pass.

## First run — 2026-09-11 (12-month window, 563 corporate issuers; assembled drop 2026-09-11-4)
**3,478 events**, every one dated and URL-carrying, State sourced. Issuers with at least one event: 552 of 563 (zero events: 11). Thin, as the order expected: SGXNet coverage is what Tavily indexes on links.sgx.com (2,527 events for 521 issuers from 10,702 pages fetched, 4,580 of which belonged to other issuers and were dropped by the Securities-line check), not the full SGXNet trail.

By type: sgxnet_announcement 1,217 · results 851 · newswire_release 526 · annual_return 386 · director_change 160 · agm_egm 138 · substantial_shareholder 133 · halt_suspension 47 · status_change 9 · dividend 7 · name_change 4.
By source: links.sgx.com pages 2,373 · ACRA 395 · wires 556 (published_date 292, URL date 264) · links.sgx.com documents with Tavily's date 154.
SGXNet categories seen: General Announcement 982 · Financial Statements and Related Announcement 522 · Annual Reports and Related Documents 228 · Change – Announcement of Appointment 139 · Asset Acquisitions and Disposals 105 · Change – Announcement of Cessation 80 · Disclosure of Interest (substantial shareholders) 65 · Disclosure of Interest (directors) 59 · Placements 32 · Request for Trading Halt 26.

Gaps: 409 rows — 308 wire hits set aside under the name rule (ambiguous match), 87 issuers with no UEN (no ACRA register events), 11 zero-event issuers, and the three standing notes (SGXNet API, ACRA dates, IR pages).

## Refresh
`run_refresh.ps1` (to be called by `CM-KG\RAILS\sg-weekly.ps1`, Friday 03:30 machine time = 17:30 Singapore): `pond_open.py sg-cm-kg sg-width1 width1`, the three workers with `WINDOW_DAYS=7`, then `assemble_disclosure.py`. Skips while `POND\sg-cm-kg\.lock` exists.
