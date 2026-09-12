# de-width0 — Germany Width 0 (ORDER-015 Part A)

Pond-native rail for node `de-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\de-cm-kg\width0\<date>\`; `assemble.py` reads every drop (newest wins per key) and writes `POND\de-cm-kg\assembled\<date>\de-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\de-issuers.xlsx`. Sourced or blank; no prices. Duty line on the node page: MiFID II product governance.

## Steps
1. `fetch_sources.py` — Deutsche Börse's daily Xetra all-tradable-instruments CSV (5,117 instruments; 1,419 common shares), the GLEIF registration-authorities list (RA code → register / court), the GLEIF mapping zip (reused from the day's Singapore drop).
2. `build_roster.py` — 420 rows: common shares in the German product groups (DAX 43, MDAX 53, SDAX 74, DEUTSCHLAND 250) or with a German ISIN; foreign shares traded on Xetra are left out. Segment = the Xetra product group; the Regulated Market / Scale split is not in the file (HITL: the Börse Frankfurt API refuses plain clients, 403 CORS).
3. `isin_lei_lookup.py` / `lei_match.py` / `lei_records.py` — GLEIF: 414 of 420 ISINs in the mapping file.
4. `enrich.py reg|wire` — Tavily: registered-share provider from a closed list (Link Market Services, Computershare Deutschland, ADEUS, Better Orange, Clearstream, in-house Aktienregister); wires (EQS News / DGAP, PR Newswire, GlobeNewswire, Business Wire, ACCESS, Newsfile, pressetext, IRW-Press).
5. `assemble.py` — the workbook (Coverage, Gaps, Xetra, Gaps detail, HITL, Method). Handelsregister sheet (HRA/HRB) and the keeping court come from the LEI record (registeredAs / registeredAt through the RA list); handelsregister.de is a search form (link column = public search entry). Bundesanzeiger = link only.

## First run — 2026-09-11 (assembled drop 2026-09-11)
| Field | Xetra (420) |
|---|---|
| ISIN, WKN, segment | 420 |
| LEI | 414 |
| Register number (HR) + court | 320 |
| Registered office (GLEIF) | 414 |
| Incorporation jurisdiction | 414 |
| Sector | 0 (not in the file) |
| Auditor | 0 (link only) |
| Annual report (Bundesanzeiger entry) | 420 (search entry, unverified) |
| Share registrar | 17 |
| Newswire of habit | 300 (EQS News dominant) |

Answered machines: xetra.com CSV, GLEIF (API, mapping, RA list), Tavily. Refused: api.boerse-frankfurt.de (403), handelsregister.de (search form), bundesanzeiger.de (scrape-hostile), eqs-news.com news paths (404 on the old paths; the news pages themselves are indexed and fetchable, used at Width 1).

## Refresh
No scheduled task (global BUILD lock; sweeps disabled until the 014–018 chain reports). `run_refresh.ps1` to be written with the Width 1 rail.

## Standing flag — Deutsche Börse data (CEO, 2026-09-11): review, not needed
Deutsche Börse Market Data + Services and the Börse Frankfurt API are marked "revisit at build end and regularly thereafter". They are never paid for on terminal or feed terms. The Xetra Scale segment column stays blank with its reason (the Xetra instruments file carries product groups, not the Regulated Market / Scale split; the Börse Frankfurt API refuses plain clients). Listed on the HITL tab as "review, not needed".
