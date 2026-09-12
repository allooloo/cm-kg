# kr-width0 — South Korea Width 0 (ORDER-017 re-cut)

Pond-native rail for node `kr-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\kr-cm-kg\width0\<date>\`; `assemble.py` reads every drop (newest wins per key) and writes `POND\kr-cm-kg\assembled\<date>\kr-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\kr-issuers.xlsx`. Sourced or blank; no prices. Korean as primary; the English name is the one DART publishes (no machine translation). Duty line on the node page: suitability and appropriateness (FSCMA Articles 46 and 46-2).

## Steps
1. `fetch_sources.py` — KIND (KRX disclosure site) listed-company list (`corpList.do?method=download`, EUC-KR HTML table: Korean name, 6-digit code, market, industry, main products, listing date, fiscal month, CEO, website, region); DART `corpCode.xml` (filer master, keyed); DART `company.json` per listed corp_code (English name, corporate and business registration numbers, address, homepage, IR page, KSIC code, establishment date, corp class). Key: `AGENT KEYS\dart.txt` (read in-process). 3,931 profile calls.
2. `build_roster.py` — 2,802 lines: KOSPI 847 · KOSDAQ 1,841 · KONEX 114 (KIND's market label for KOSPI is the short form 유가). Every line typed Corporate (SPACs by name).
3. `lei_match_local.py` — LEI from the GLEIF golden copy extract (`RAILS\gleif-golden`, POND\estate\gleif-golden): registeredAs = the DART business registration number (RA000657) 261, the corporate registration number 33, name-exact 5 → 299 of 2,802.
4. `..\gleif-golden\lei_records_local.py KR` — the LEI records from the golden copy and the ISINs from the GLEIF ISIN-to-LEI mapping zip (13 Korean LEIs carry ISINs there).
5. `assemble.py` — the workbook (Coverage, Gaps, KOSPI, KOSDAQ, KONEX, Gaps detail, HITL, Method).

## First run — 2026-09-12 (assembled drop 2026-09-12)
| Field | KOSPI (847) | KOSDAQ (1,841) | KONEX (114) |
|---|---|---|---|
| Legal name (English, DART) | 843 | 1,787 | 112 |
| Legal name (Korean), sector (KIND 업종), fiscal month | 847 | 1,841 | 114 |
| DART corp code, business registration number, registered office (DART address) | 843 | 1,787 | 112 |
| Corporate registration number, incorporation jurisdiction | 841 | 1,768 | 112 |
| LEI + HQ city (GLEIF) | 226 | 72 | 1 |
| ISIN | 0 (GLEIF maps ISINs to 13 Korean LEIs; the KRX pattern KR7+code+00+check is not derived, by rule) | 0 | 0 |
| Auditor, annual report, registrar, newswire | 0 (Fill pass) | 0 | 0 |

Answered machines: KIND (corpList download), DART (keyed), GLEIF (golden copy, mapping file). Not used: data.krx.co.kr form endpoints, KSD, any paid licence. HITL: ISIN (a KRX data licence or the Fill pass reading the KIND issuer page), LEI coverage (GLEIF holds LEIs for about one KOSPI issuer in four), DART daily cap 20,000 calls.

## Refresh
None scheduled (global BUILD lock). Re-run steps 1–5 into a new drop; `company.json` and the LEI joins are resumable / idempotent.
