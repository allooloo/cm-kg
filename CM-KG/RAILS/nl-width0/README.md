# nl-width0 — Netherlands Width 0 (ORDER-016 Part A)

Pond-native rail for node `nl-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\nl-cm-kg\width0\<date>\`; `assemble.py` reads every drop (newest wins per key) and writes `POND\nl-cm-kg\assembled\<date>\nl-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\nl-issuers.xlsx`. Sourced or blank; no prices. Duty line on the node page: MiFID II product governance.

## Steps
1. `fetch_sources.py` — ESMA FIRDS full equity files (the same weekly zips as the French rail): every share admitted to trading on Euronext Amsterdam (XAMS) and Euronext Growth Amsterdam (TNLA) with the issuer LEI. Euronext's own list pages sit behind an anti-bot form (HITL).
2. `build_roster.py` — 123 share lines on Euronext Amsterdam (86 Dutch ISINs; the rest are foreign-ISIN lines carried outside the Dutch corporate scope); no TNLA share lines in the file.
3. `isin_lei_lookup.py` / `lei_match.py` / `lei_records.py` — GLEIF records for every LEI.
4. KVK: the trade-register API is paid (401 without a key — HITL); the KVK number comes from the LEI record's registeredAs (RA000463) and the link column is the public search entry. AFM: the issuer register is a JavaScript page without a public export (HITL); the link column is the public entry.
5. `enrich.py reg|wire` — Tavily: agent from a closed list (Euroclear Nederland, ABN AMRO, ING, IQ EQ, Computershare, Intertrust / CSC, Rabobank, Van Lanschot Kempen); wires (GlobeNewswire, Business Wire, PR Newswire, ACCESS, Newsfile, EQS).
6. `assemble.py` — the workbook (Coverage, Gaps, two market tabs, Gaps detail, HITL, Method).

## First run — 2026-09-11 (assembled drop 2026-09-11-2)
| Field | Euronext Amsterdam (123 lines; 86 Dutch) |
|---|---|
| ISIN, LEI, listing date | 123 |
| KVK number (from the LEI record) + legal form (ELF) | 83 |
| Registered office, jurisdiction, HQ city | 111 |
| Sector | 0 (no FIRDS sector; register code needs the KVK API) |
| Auditor / annual report | 0 (link only) |
| Share registrar | 6 |
| Newswire of habit | 55 |

Answered machines: ESMA FIRDS, GLEIF, Tavily. Refused: live.euronext.com lists (anti-bot), api.kvk.nl (401), AFM registers (JavaScript, no export).

## Refresh
No scheduled task (global BUILD lock). `run_refresh.ps1` to be written with the Width 1 rail.
