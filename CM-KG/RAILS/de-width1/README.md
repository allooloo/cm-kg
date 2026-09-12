# de-width1 — Germany Width 1 (ORDER-015 Part B), disclosure events over 12 months

Pond-native rail for node `de-cm-kg`. Workers write into `raw\` (a junction to the open drop `CM-KG\POND\de-cm-kg\width1\<date>\`); the assembler reads every drop plus the last versioned event set, dedupes on (exchange, code, type, date, URL), and writes `CM-KG\DISCLOSURE\de-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\de-events.jsonl` with a versioned copy under `CM-KG\POND\de-cm-kg\assembled\<date>\`.

## Sources
| Worker | Source | Read-by label |
|---|---|---|
| eqs_search.py | EQS News pages (eqs-news.com / DGAP: ad hoc, corporate news, voting rights, directors' dealings, other capital market information) found per issuer by Tavily; category from the URL path, language from the URL suffix | Tavily search (eqs-news.com) + published_date |
| wire_search.py | Tavily over PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile, pressetext, IRW-Press | Tavily search (wire domains) + published_date / + URL date |

Handelsregister events are not read: handelsregister.de is a search form without an API (HITL); Bundesanzeiger is scrape-hostile. The Xetra instrument names are abbreviated (BAY.MOTOREN WERKE AG ST), so the workers search on the GLEIF legal name; the first pass on the short names is kept as `*_pass1.jsonl` and merged.

## First run — 2026-09-11 (12-month window, 409 German corporate lines; assembled drop 2026-09-11-7)
**1,546 events**, every one dated and URL-carrying, State sourced. Issuers with at least one event: 306 of 409 (zero events: 103 — mostly names whose EQS headlines use a short form the name rule does not accept, e.g. "BMW AG" against "Bayerische Motoren Werke"; the Fill pass alias channel and rematch recover part of this).

By type: corporate_news 702 · newswire_release 482 · ad_hoc 152 · directors_dealings 71 · major_holder 67 · results 33 · exchange_bulletin 26 · agm_egm 10 · dividend 3.
By source: EQS News 1,037 · wires 509. By language: English 586, German 328 (632 undeclared, mostly wires).
Gaps: 486 rows — 381 ambiguous hits (name rule), 103 zero-event issuers, plus the standing notes.

## Refresh
`run_refresh.ps1` (no scheduled task: global BUILD lock, sweeps disabled until the 014–018 chain reports): `pond_open.py de-cm-kg de-width1 width1`, the two workers with `WINDOW_DAYS=7`, `assemble_disclosure.py`.
