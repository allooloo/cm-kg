# kr-width1 — South Korea Width 1 (ORDER-017 re-cut), DART filings over 12 months

Pond-native rail for node `kr-cm-kg`. Workers write into `raw\` (a junction to the open drop `CM-KG\POND\kr-cm-kg\width1\<date>\`); the assembler reads every drop plus the last versioned event set, dedupes on (exchange, code, type, date, URL), and writes `CM-KG\DISCLOSURE\kr-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\kr-events.jsonl` with a versioned copy under `CM-KG\POND\kr-cm-kg\assembled\<date>\`. Korean titles as DART publishes them; no machine translation; no search layer at Width 1 (ORDER-017: Perplexity Search + preset fast and Tavily extraction belong to the Fill pass).

## Sources
| Worker | Source | Read-by label |
|---|---|---|
| dart_events.py | DART list API per corp_code over the window (100 rows a page, key `AGENT KEYS\dart.txt`): every filing with its Korean report name, receipt number, submitter, date and the DART viewer page. Event types come from the report name (the list response carries no publication-type field): 사업보고서 / 반기 / 분기보고서 and 실적 → results; 주요사항보고서 → ad hoc; 증권신고서 → prospectus; 임원ㆍ주요주주 → directors' dealings; 대량보유 → major holder; 주주총회 → AGM/EGM; 배당 → dividend; 매매거래정지 → halt; 공개매수 → takeover; 조회공시 / 공정공시 → exchange bulletin; audit and governance reports → regulatory filing | DART list API (filings per corp_code) |

KIND exchange disclosures are mirrored in the DART list; KIND's own search is a form and is not read.

## First run — 2026-09-12 (12-month window, 2,802 companies; assembled drop 2026-09-12-3)
**143,294 events**, every one dated and URL-carrying, State sourced. Issuers with at least one event: 2,700 of 2,802 (zero events: 60 — lines without a DART corp code).

By type: corporate_news 43,413 · directors_dealings 21,288 · results 17,577 · agm_egm 14,408 · prospectus 13,852 · major_holder 12,525 · ad_hoc 7,831 · regulatory_filing 5,348 · dividend 3,492 · exchange_bulletin 1,553 · halt_suspension 1,313 · director_change 509 · name_change 95 · takeover 90. Language: Korean 143,294.

The first assembly (drop 2026-09-12-2) typed every row regulatory_filing because the worker keyed on a response field DART does not return; the assembler now types DART rows from the report name at assembly, so the earlier drop and the prior event set re-type on merge. Nothing was deleted.

## Refresh
`run_refresh.ps1` (no scheduled task: global BUILD lock): `pond_open.py kr-cm-kg kr-width1 width1`, `dart_events.py` with `WINDOW_DAYS=7`, `assemble_disclosure.py`. The sweep uses about 4,000 of the 20,000 daily DART calls.
