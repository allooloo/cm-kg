# sg-width0 — Singapore Width 0 (ORDER-013 Part B)

Pond-native rail for node `sg-cm-kg`. `raw\` is a directory junction to the open drop `CM-KG\POND\sg-cm-kg\width0\<date>\`; `assemble.py` reads every drop of the rail (newest wins per key) and writes `POND\sg-cm-kg\assembled\<date>\sg-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\sg-issuers.xlsx`. Sourced or blank; no prices; every enriched cell carries source, read-by and State.

## Steps
1. `fetch_sources.py` — SGX listed-securities feed (`api.sgx.com/securities/v1.1`, price fields dropped at write), SGX market metadata (`/marketmetadata/v2`: ISIN, issuer name, FISN), SGX stock screener (`/stockscreener/v2.0/all`, identity fields only: company name, stock code, sector), the 27 ACRA register CSVs from data.gov.sg collection 2 via the v2 poll-download API, the GLEIF ISIN-to-LEI mapping zip.
2. `acra_index.py` — 2,110,094 ACRA rows scanned, 20,385 kept (public companies, foreign-company branches, and any entity whose current or former name equals an SGX name): UEN, entity and company type, status, incorporation date, registered address, primary SSIC, former names, audit firms (empty in the dataset for all but one row).
3. `build_roster.py` — 639 rows: 563 corporates, 37 REITs / business trusts, 39 depositary receipts (Mainboard 401, Catalist 199, GlobalQuote 39). Trusts and receipts are named by the exchange trading name; the market-metadata issuer name (the manager or depositary, a Pte. Ltd.) is carried in its own column.
4. `isin_lei_lookup.py` — GLEIF mapping file: 0 SG-prefixed ISINs in the file; 17 hits (foreign-ISIN lines).
5. `lei_match.py` / `lei_records.py` — GLEIF name-exact: 154 of 652 names; LEI records for every LEI found.
6. `enrich.py reg|wire` — Tavily: share registrar from a closed list within 300 characters of "registrar"; wires beyond SGXNet (majority of up to three releases).
7. `assemble.py` — the workbook (Coverage, Gaps, SGX Mainboard, SGX Catalist, Gaps detail, HITL, Method).

## First run — 2026-09-11 (assembled drop 2026-09-11-3; -1 and -2 superseded, see their DROP.md)

| Field | Mainboard (440) | Catalist (199) |
|---|---|---|
| ISIN | 440 | 199 |
| LEI | 144 | 17 |
| UEN (ACRA) | 371 | 180 |
| Registered office | 393 | 184 |
| Incorporation jurisdiction | 393 | 184 |
| Sector (SGX screener) | 397 | 197 |
| Primary SSIC (ACRA) | 371 | 180 |
| Share registrar | 144 | 64 |
| Newswire of habit | 440 (SGXNet) | 199 (SGXNet) |
| Auditor | 0 (link only at Width 0; SGXNet API refuses) | 0 |
| Listing date | 363 | 197 |

Conflicts: 9 (mapping-file LEI naming another entity, or a local company whose GLEIF jurisdiction is not SG). Gap rows: 3,258.

Sources that answered machines: api.sgx.com securities, market-metadata and stock-screener feeds (no key) · data.gov.sg ACRA collection · GLEIF · Tavily. Refused: api.sgx.com announcements (401) and companies / stockfacts (403), also from a browser session on sgx.com; www.sgx.com company pages moved to the Flutter app at investors.sgx.com (renders nothing to a text client); ACRA BizFile per-UEN pages (search UI).

## Refresh
`run_refresh.ps1`: `pond_open.py sg-cm-kg sg-width0 width0`, then the steps above. No scheduled task until the node passes Width 1 (SWEEPS.md). Skips while `POND\sg-cm-kg\.lock` exists.
