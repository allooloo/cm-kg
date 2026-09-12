# jp-width0 — Japan Width 0 (ORDER-017 re-cut)

Pond-native rail for node `jp-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\jp-cm-kg\width0\<date>\`; `assemble.py` reads every drop (newest wins per key) and writes `POND\jp-cm-kg\assembled\<date>\jp-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\jp-issuers.xlsx`. Sourced or blank; no prices. Japanese as primary; the English names are the ones JPX and EDINET publish (no machine translation). Duty line on the node page: suitability principle (FIEA Article 40).

## Steps
1. `fetch_sources.py` — JPX listed-issuers workbook (`data_e.xlsx`, effective 2026-08-31: local code, English name, market section, 33/17-sector codes, TOPIX size series) and the EDINET code list (`Edinetcode.zip`, 11,389 filers: Japanese and English names, kana, address, industry, filer type, consolidation, capital, fiscal year end, securities code, 13-digit corporate number).
2. `build_roster.py` — 3,964 lines joined on the securities code (EDINET's 5-digit code = JPX code + check digit): Prime 1,557 · Standard 1,559 · Growth 598 · PRO Market 187 · REITs and funds 63. ETFs / ETNs 477 counted, not carried. 3,709 lines carry an EDINET filer, 3,703 a corporate number.
3. `lei_match_local.py` — LEI from the GLEIF golden copy extract (`RAILS\gleif-golden`): registeredAs = the 12-digit company registration number inside the corporate number (RA000412) 604, name-exact on the English name 287 → 891 of 3,964. (An API-route pass, `lei_match.py`, ran first and is kept beside it as `lei_match_api.jsonl`; the GLEIF API allows about one call a second, so the local join replaced it.)
4. `..\gleif-golden\lei_records_local.py JP` — the LEI records from the golden copy and the ISINs from the GLEIF ISIN-to-LEI mapping zip (532 of 869 LEIs carry ISINs; one equity-pattern ISIN JP3 + 6 digits + 00 + check fills the cell).
5. `assemble.py` — the workbook (Coverage, Gaps, five market tabs, Gaps detail, HITL, Method).

## First run — 2026-09-12 (assembled drop 2026-09-12-2)
| Field | Prime (1,557) | Standard (1,559) | Growth (598) | PRO (187) | REITs and funds (63) |
|---|---|---|---|---|---|
| English name, sector (JPX 33) | 1,557 | 1,557 | 598 | 187 | 63 (sector 0) |
| Japanese name, EDINET code, address, fiscal year end | 1,550 | 1,558 | 598 | 3 | 0 |
| Corporate number (法人番号), jurisdiction | 1,548 | 1,556 | 596 | 3 / 9 | 0 / 29 |
| LEI + HQ city (GLEIF) | 685 | 120 | 51 | 6 | 29 |
| ISIN (GLEIF mapping, equity pattern) | 469 | 53 | 11 | 1 | 3 |
| Auditor, annual report, registrar, newswire | 0 (Fill pass) | 0 | 0 | 0 | 0 |

Answered machines: JPX (xlsx), EDINET (code list; documents API keyed for Width 1), GLEIF (golden copy, mapping file). Not used: the NTA corporate-number API (application ID — HITL), JPX / JSDA ISIN masters (paid), TDnet (no API). HITL: ISIN for issuers without an LEI (the Fill pass reads the JPX issuer page), LEI coverage outside Prime, PRO Market lines (no EDINET filer: they file with the exchange, not EDINET).

## Refresh
None scheduled (global BUILD lock). Re-run steps 1–5 into a new drop; the golden copy is one download a build day under POND\estate\gleif-golden.
