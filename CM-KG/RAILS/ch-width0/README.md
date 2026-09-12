# ch-width0 — Switzerland Width 0 (ORDER-015 Part A)

Pond-native rail for node `ch-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\ch-cm-kg\width0\<date>\`; `assemble.py` reads every drop (newest wins per key) and writes `POND\ch-cm-kg\assembled\<date>\ch-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\ch-issuers.xlsx`. Sourced or blank; no prices. Duty line on the node page: FinSA.

## Steps
1. `fetch_sources.py` — SIX Swiss Exchange share-explorer feed (`six-group.com/fqs/ref.json`, PortalSegment EQ: 810 lines; ICB industry requested but empty), BX Swiss instruments list (28 pages of 500: 13,890 lines, 6,653 with a Swiss ISIN, labels Share / Fund / ETF / ETP / Bond / AMC / deriBX), Zefix legal-form table, GLEIF mapping zip (reused from the day's Singapore drop).
2. `build_roster.py` — 829 rows: 810 SIX lines (223 Swiss ISINs; the rest are foreign-ISIN lines carried outside the Swiss corporate scope) + 19 BX Swiss share lines with a Swiss ISIN not on SIX.
3. `isin_lei_lookup.py` / `lei_match.py` / `lei_records.py` — GLEIF: 569 of 626 ISINs in the mapping file (Swiss ISINs are well mapped); name-exact for the rest; LEI records.
4. `zefix_match.py` — Zefix through the public web API behind zefix.ch (POST firm/search.json, no account): route 1 the SIX short name equals a corporation's name; route 2 (added on the day because SIX short names are abbreviated) the GLEIF legal name, accepting the candidate whose UID equals the LEI record's registeredAs or whose name equals the GLEIF name. Kept: UID, CH-ID, legal seat, legal form, status, last SHAB date, cantonal excerpt URL.
5. `enrich.py reg|wire` — Tavily: share-register agent from a closed list (Computershare Schweiz, areg.ch, ShareCommService, Devigus, SIX SIS, Nimbus, in-house); wires (PR Newswire, GlobeNewswire, Business Wire, ACCESS, Newsfile, EQS News).
6. `assemble.py` — the workbook (Coverage, Gaps, SIX, BX Swiss, Gaps detail, HITL, Method).

## First run — 2026-09-11 (assembled drop 2026-09-11-2)
| Field | SIX (810 lines; 223 Swiss) | BX Swiss (19) |
|---|---|---|
| ISIN | 810 | 19 |
| LEI | 744 | 15 |
| UID (Zefix) + legal seat | 176 | 13 |
| Registered office (GLEIF) | 744 | 15 |
| Incorporation jurisdiction | 746 | 18 |
| Sector | 0 (feed empty) | 0 |
| Auditor / annual report | 0 (link only; SIX hosts no report index) | 0 |
| Share registrar | 51 | 7 |
| Newswire of habit | 155 | 11 |
| Listing date | 810 | 0 |

Answered machines: six-group.com feed (JSON), bxswiss.com list (HTML), zefix.ch web API (JSON), GLEIF, Tavily. Refused: ZefixPublicREST (401 without an account), SIX issuer-list downloads (404), SER ad hoc pages on the old paths (404).

## Refresh
No scheduled task (global BUILD lock; sweeps disabled until the 014–018 chain reports). `run_refresh.ps1` to be written with the Width 1 rail.
