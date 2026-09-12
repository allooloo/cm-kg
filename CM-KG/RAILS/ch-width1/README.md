# ch-width1 — Switzerland Width 1 (ORDER-015 Part B), disclosure events over 12 months

Pond-native rail for node `ch-cm-kg`. Workers write into `raw\` (a junction to the open drop `CM-KG\POND\ch-cm-kg\width1\<date>\`); the assembler reads every drop plus the last versioned event set, dedupes on (exchange, code, type, date, URL), and writes `CM-KG\DISCLOSURE\ch-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\ch-events.jsonl` with a versioned copy under `CM-KG\POND\ch-cm-kg\assembled\<date>\`.

## Sources
| Worker | Source | Read-by label |
|---|---|---|
| eqs_search.py | EQS News pages (eqs-news.com; carries most Swiss ad hoc announcements, corporate news, voting rights) found per issuer by Tavily (news search over the window + general search restricted to the host); the EQS category comes from the URL path, the language from the URL suffix | Tavily search (eqs-news.com) + published_date |
| shab_events.py | SHAB / FOSC (Swiss Official Gazette of Commerce) publications API, rubric HR, keyword = UID and GLEIF legal name, 12-month window: register new registrations, mutations, deletions | SHAB publications API (Swiss Official Gazette of Commerce, commercial-register rubric) |
| wire_search.py | Tavily over PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile, pressetext, IRW-Press | Tavily search (wire domains) + published_date / + URL date |

SIX Exchange Regulation's own ad hoc pages answered 404 on every known path and no public feed was found (HITL). The exchange short names are abbreviated, so the workers search on the GLEIF legal name; the first pass on the short names is kept as `*_pass1.jsonl` and merged.

## First run — 2026-09-11 (12-month window, 233 Swiss corporate lines; assembled drop 2026-09-11-4)
**1,303 events**, every one dated and URL-carrying, State sourced. Issuers with at least one event: 190 of 233 (zero events: 43 — cantonal banks, second lines and small caps EQS does not carry).

By type: register_mutation 503 · newswire_release 432 · corporate_news 191 · ad_hoc 76 · results 65 · agm_egm 12 · register_deletion 8 · register_new_registration 5 · major_holder 4 · dividend 3 · director_change 2 · directors_dealings 1 · exchange_bulletin 1.
By source: SHAB 516 · wires 514 · EQS News 273. By language: German 476, English 188, French 78, Italian 7 (554 undeclared, mostly wires).
Gaps: 220 rows — 128 ambiguous wire hits (name rule), 47 issuers without a Zefix UID (no register events), 43 zero-event issuers, plus the standing notes.

## Refresh
`run_refresh.ps1` (no scheduled task: global BUILD lock, sweeps disabled until the 014–018 chain reports): `pond_open.py ch-cm-kg ch-width1 width1`, the three workers with `WINDOW_DAYS=7`, `assemble_disclosure.py`.
