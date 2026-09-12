# fr-width1 — France Width 1 (ORDER-016 Part B), disclosure events over 12 months

Pond-native rail for node `fr-cm-kg`. Workers write into `raw\` (a junction to the open drop `CM-KG\POND\fr-cm-kg\width1\<date>\`); the assembler reads every drop plus the last versioned event set, dedupes on (exchange, code, type, date, URL), and writes `CM-KG\DISCLOSURE\fr-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\fr-events.jsonl` with a versioned copy under `CM-KG\POND\fr-cm-kg\assembled\<date>\`.

## Sources
| Worker | Source | Read-by label |
|---|---|---|
| bdif_events.py | AMF BDIF regulatory-information database, public API per filer token (`Jetons=RS…`, 12-month window): financial information, document filings (directors' declarations, threshold crossings, financial reports), offers, prospectus visas, with publication date and the BDIF page | AMF BDIF regulatory-information database (per filer token) |
| wire_search.py | Tavily over Actusnews, GlobeNewswire, Business Wire, PR Newswire, ACCESS Newswire, Newsfile | Tavily search (wire domains) + published_date / + URL date |

Euronext Paris announcement pages refuse machines (anti-bot form). Issuers without an AMF filer token at Width 0 (not among the filers of the last 10,000 BDIF items) have no BDIF trail here (HITL: per-filer search on the site).

## First run — 2026-09-11 (12-month window, 590 French corporate lines; assembled drop 2026-09-11-3)
**9,896 events**, every one dated and URL-carrying, State sourced. Issuers with at least one event: 422 of 590 (zero events: 168, of which 327 gap rows say "no AMF filer token" — the token index is capped at the last 10,000 BDIF items; large filers such as BNP Paribas and ADP fell outside it).

By type: directors_dealings 3,426 · regulatory_filing 2,922 · newswire_release 2,190 · takeover 654 · prospectus 303 · results 285 · major_holder 44 · agm_egm 29 · dividend 20 · halt_suspension 10 · director_change 9 · ad_hoc 4.
By source: AMF BDIF 7,441 · wires 2,455. By language: French 7,437 (BDIF), undeclared 2,459 (wires).
Gaps: 496 rows — 327 issuers without a filer token, ambiguous wire hits, 168 zero-event issuers.

## Refresh
`run_refresh.ps1` (no scheduled task: global BUILD lock): `pond_open.py fr-cm-kg fr-width1 width1`, the two workers with `WINDOW_DAYS=7`, `assemble_disclosure.py`.
