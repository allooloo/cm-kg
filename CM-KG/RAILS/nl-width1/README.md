# nl-width1 — Netherlands Width 1 (ORDER-016 Part B), disclosure events over 12 months

Pond-native rail for node `nl-cm-kg`. Workers write into `raw\` (a junction to the open drop `CM-KG\POND\nl-cm-kg\width1\<date>\`); the assembler reads every drop plus the last versioned event set, dedupes on (exchange, code, type, date, URL), and writes `CM-KG\DISCLOSURE\nl-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\nl-events.jsonl` with a versioned copy under `CM-KG\POND\nl-cm-kg\assembled\<date>\`.

## Sources
| Worker | Source | Read-by label |
|---|---|---|
| afm_events.py | AFM notification registers (afm.nl) read per issuer keyword with the 12-month date window: inside information (ad hoc), financial reporting, directors' and supervisory board transactions, substantial holdings, net short positions, approved prospectuses, public offers; each row with date, issuer as registered, subject and the register detail page | AFM notification register (afm.nl, per issuer keyword) |
| wire_search.py | Tavily over GlobeNewswire, Business Wire, PR Newswire, ACCESS Newswire, Newsfile | Tavily search (wire domains) + published_date / + URL date |

Euronext Amsterdam announcement pages refuse machines (anti-bot form). The AFM pages render their first results page server-side; the paged remainder is JavaScript (HITL: bulk export / AFM update service).

## First run — 2026-09-11 (12-month window, 84 Dutch corporate lines; assembled drop 2026-09-11-3)
**2,706 events**, every one dated and URL-carrying, State sourced. Issuers with at least one event: 84 of 84.

By type: ad_hoc 1,233 · directors_dealings 688 · results 365 · newswire_release 244 · agm_egm 84 · takeover 42 · dividend 25 · prospectus 17 · director_change 3 · halt_suspension 3 · major_holder 2.
By source: AFM registers 2,408 · wires 298. By language: Dutch 910 (register rows other than inside information), undeclared 1,796.
Gaps: 1 row.

## Refresh
`run_refresh.ps1` (no scheduled task: global BUILD lock): `pond_open.py nl-cm-kg nl-width1 width1`, the two workers with `WINDOW_DAYS=7`, `assemble_disclosure.py`.
