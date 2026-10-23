# hk-width1 — Hong Kong Width 1 (ORDER-035, 2026-10-22), disclosure events over twelve months

Pond-native rail for node `hk-cm-kg` (a full node by the CEO ruling of 2026-10-22; the Sept 11 partner-beacon line is struck). `raw\` is a junction to the open drop `CM-KG\POND\hk-cm-kg\width1\<date>\`. The assembler reads every drop (newest wins per board-day), keeps the roster's documents, and writes `POND\hk-cm-kg\assembled\<date>\hk-events.jsonl` + `hk-disclosure.xlsx`, mirrored to `CM-KG\DISCLOSURE\events\hk-events.jsonl` and `CM-KG\DISCLOSURE\hk-disclosure.xlsx` (the previous mirror kept beside as `.pre-<stamp>`).

## Source
| Worker | Source | Read-by label |
|---|---|---|
| hkexnews_search.py | HKEXnews public title search (`www1.hkexnews.hk/search/titleSearchServlet.do`, `lang=E`), one call per board (SEHK = Main Board, GEM) per day: stock code(s), the HKEX headline category, the English title, the date-time and the document link | HKEXnews title search (titleSearchServlet.do, lang=E) |

Rules: English-language filings only (standing rule) — a title carrying a Chinese character is skipped and counted; type = the HKEX headline category as the exchange's own code table writes it, in English (`hkex_category`), with the house `event_type` mapped from it; title exactly as filed (line breaks joined), never translated; identifiers language-free. financialfilings.com is never a source (terms). No login, no form.

## First run — 2026-10-22 (366-day window, 732 board-days; assembled drops 2026-10-22, 2026-10-22-2)
- Read: 223,296 rows, 0 errors, 0 incomplete board-days.
- Kept: **162,874 events** for **2,795 of the 2,820** roster lines (as of 2026-10-22, the last completed Hong Kong trading day).
- Not on the roster: 49,697 rows (warrants, CBBCs, ETPs, debt, delisted lines).
- Duplicate pointers folded: 13,168.
- Outside the window: 21.
- Chinese-language titles: 0 (the English search returns English titles).
- Top categories: Monthly Returns 32,985; Next Day Disclosure Returns - [Share Buyback] 15,053; Circulars - [Other] 9,059; Overseas Regulatory Announcement 7,704; Date of Board Meeting 6,156.

The assembled drop 2026-10-22-2 fixes the house type of the combined heading "[Annual Report / Environmental, Social and Governance Information/Report]". The first drop had typed those 1,110 documents as esg_report; they are annual reports. Both drops are kept.

## Refresh
`run_refresh.ps1`: `pond_open.py hk-cm-kg hk-width1 width1`, the worker over `WINDOW_DAYS` (nightly 3, from the ORDER-036 job), then the assembler. The node job `cmkg-hk-rail` (East Asia, 18:00 UTC = 02:00 Hong Kong standard time) runs it under 0.32.0.
