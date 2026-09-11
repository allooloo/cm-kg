# CM-KG rail — Australia Width 0 (au-cm-kg)

Builds `C:\ALLOOLOO\CM-KG\ISSUERS\au-issuers.xlsx` (mirror of the versioned copy in `CM-KG\POND\au-cm-kg\assembled\<date>\`): every listed entity on ASX and the NSX official list, enriched per ORDER-010 Part B. First run 2026-09-11 (1,874 rows: ASX 1,830 · NSX 44 · TMX Australia 0). Pond-native: `raw\` is a junction to the open drop `POND\au-cm-kg\width0\<date>\`; `run_refresh.ps1` opens a new drop, skips on the node lock, and the assembler reads every drop (newest wins per key).

Rules of the rail: **sourced or blank** — no registry, auditor or newswire is ever inferred; every enriched cell carries a source URL, a read-by label and a State. Prices, volumes and market caps exist in the ASX feeds and are dropped at write time.

## Workers

| Step | Script | Source | Fields | Read-by label |
|---|---|---|---|---|
| 1 | `fetch_sources.py` | ASX listed-companies directory file (code, name, GICS industry group, listing date) + per-company research record the public ASX company pages render (header: sector, security type, status; key-statistics: ISIN; about: website, contact and share-registry addresses — the last three are empty on every record the API returns); NSX official-list RSS; ASIC Company Dataset (data.gov.au, weekly, 4.44 M rows); GLEIF ISIN-to-LEI file | rosters and registry files | `ASX listed-companies directory (exchange list)` · `ASX company record (exchange site, asx.com.au company page data)` · `NSX official list feed (exchange list)` |
| 2 | `asic_index.py` | the ASIC bulk file | public companies (APUB) and every row whose name equals an exchange-list name (31,839 companies): ACN, ABN, type, class, status, registration date, previous names | `ASIC company register bulk dataset (data.gov.au, weekly)` |
| 3 | `asx_announcements.py` | ASX announcements platform search page per code, two calendar years | 12-month announcement count, latest date, latest announcement headed "Annual Report" with its viewer link | `asx.com.au announcements search (exchange site)` |
| 4 | `build_roster.py` | steps 1–3 | one row per entity; security type from the ASX issue type / share description / name | — |
| 5 | `isin_lei_lookup.py` | GLEIF mapping file, exact ISIN (7,210 AU rows in the file; 157 of 1,870 hit — Australian issuers rarely register ISINs at GLEIF) | LEI | `GLEIF ISIN-to-LEI mapping file (exact ISIN match)` |
| 6 | `lei_match.py` | GLEIF fuzzycompletions for the 1,713 names without a mapping hit; accepted only on a name-exact match (458) | LEI | `GLEIF name-exact` |
| 7 | `lei_records.py` | GLEIF LEI records | registration status, legal address, HQ, jurisdiction, `registeredAs` (ACN when registered at RA000014 = ASIC) | `GLEIF LEI record (LEI per the LEI column)` |
| 8 | `enrich.py reg` / `enrich.py wire` | Tavily page text: share registry from a closed list (Computershare, MUFG Corporate Markets / Link, Boardroom, Automic, Advanced Share Registry, Security Transfer, XCEND, Registry Direct) within 300 chars of "registry"; wires beyond the ASX platform | share registry, newswire | `Tavily search + regex extraction from page text` · `Tavily search restricted to wire domains (release hits)` |
| 9 | `assemble.py` | every drop of the rail | Coverage · Gaps · ASX · NSX · TMX Australia · Gaps detail · HITL — needs MK · Method | ACN: LEI record `registeredAs` at ASIC (502) else name-exact against current and previous names in the ASIC index (1,253); mapping-file LEIs whose legal name is another entity carry State `conflict` (16) |

## Fill (first run, 2026-09-11)

| Field | ASX (1,830) | NSX (44) |
|---|---|---|
| ISIN | 100 % | 90.9 % |
| LEI | 33.4 % | 13.6 % |
| ACN / ABN / ASIC link | 93.8 % | 97.7 % |
| Incorporation jurisdiction | 94.8 % | 97.7 % |
| GICS sector | 93.9 % | 100 % (NSX industry) |
| Registered office / HQ city | 33.4 % | 13.6 % |
| State | 39.5 % | 15.9 % |
| Annual report link (auditor source) | 90.7 % | 0 % |
| Share registry | 36.1 % | 25.0 % |
| Newswire of habit | 99.7 % (ASX platform; 605 also on a wire) | 20.5 % |
| Listing date | 100 % | 100 % |

Gaps: 8,562 lines. Auditor is a source link only by order (1,874 lines). Registered office, HQ city and state are blank on 1,257 / 1,145 rows because the ASIC bulk file carries no address and the ASX company record returns empty address fields; the LEI record supplies them where an LEI exists.

## Sources — who answers machines (2026-09-11)
| Source | Answer | Used as |
|---|---|---|
| asx.com.au directory CSV and company research API | HTTP 200, public token; the older `/asx/1/` JSON API answers 404 | rosters, ISIN, sector, listing date; address fields empty |
| asx.com.au announcements search | HTTP 200 (HTML); announcement PDFs on announcements.asx.com.au answer plain clients with a text layer | announcement counts, annual report link |
| NSX official-list and company-news RSS | HTTP 200 | roster, announcements (recent only) |
| data.gov.au ASIC Company Dataset | HTTP 200, weekly zip | ACN, ABN, type, status, previous names |
| ASIC Connect per-company pages / API | search UI; API needs a registered key (`AGENT KEYS\asic.txt` absent) | not used — HITL |
| GLEIF | HTTP 200 | LEI, records, mapping file |
| tmxaustralia.com (formerly Cboe Australia) | reCAPTCHA-gated marketing page, no issuer list rendered to machines or in a browser | no rows — HITL |

## HITL — needs MK
- ASIC Connect API key (registered office, officeholders, dated register events).
- TMX Australia: a list of primary listings and announcements from the exchange or a data account.
- Anthropic Admin API key for the spend line's balance.

## Known broken (2026-09-11)
- ASX company records carry no website, contact or registry address for any code (fields present, empty).
- 161 ASX corporates lodged no announcement headed "Annual Report" in the window; 16 mapping-file LEIs belong to another entity (State conflict).
- NSX: no per-company announcement history beyond the RSS window; the TMX Australia tab is empty.

## Files
`keys.py` · `pond.py` · `fetch_sources.py` · `asic_index.py` · `asx_announcements.py` · `build_roster.py` · `isin_lei_lookup.py` · `lei_match.py` · `lei_records.py` · `enrich.py` · `assemble.py` · `run_refresh.ps1`.
