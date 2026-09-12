# hk-width0 — Hong Kong Width 0 (ORDER-017 re-cut)

Pond-native rail for node `hk-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\hk-cm-kg\width0\<date>\`; `assemble.py` reads every drop (newest wins per key) and writes `POND\hk-cm-kg\assembled\<date>\hk-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\hk-issuers.xlsx`. By order: Width 0 only, English only, no search layer, no lab reads, local-partner copy on the node page, no door. Sourced or blank; no prices.

## Steps
1. `fetch_sources.py` — HKEX List of Securities (`ListOfSecurities.xlsx`, updated as at 14/09/2026): every listed security with stock code, English name, category, sub-category, ISIN, trading currency, board lot and eligibility flags; the GLEIF ISIN-to-LEI mapping zip.
2. `build_roster.py` — 2,820 lines: Equity (Main Board 2,502 incl. investment companies, trading-only securities and depositary receipts; GEM 307) and REITs 11. Warrants 7,315, CBBCs 5,779, ETPs 417 and debt 1,323 counted, not carried. ISIN prefixes: KY 1,555 · CN 533 · BM 426 · HK 222 · SG 12 · VG 12 · US 9.
3. `isin_lei_lookup.py` / `lei_records.py` — exact ISIN → LEI from the GLEIF file (263 hits of 2,766 ISINs), then the LEI records.
4. `assemble.py` — the workbook (Coverage, Gaps, Main Board, GEM, REITs, Gaps detail, HITL, Method).

## First run — 2026-09-12 (assembled drop 2026-09-12)
| Field | Main Board (2,502) | GEM (307) | REITs (11) |
|---|---|---|---|
| Name, security type | 2,502 | 307 | 11 |
| ISIN | 2,457 | 298 | 11 |
| LEI (GLEIF ISIN file) + legal name | 271 | 3 | 0 |
| Register id (GLEIF registeredAs) | 253 | 3 | 0 |
| Registered office, jurisdiction, HQ city (GLEIF) | 271 | 3 | 0 |
| Sector, auditor, annual report, registrar, newswire | 0 (by order: no page reads, no search) | 0 | 0 |

Answered machines: HKEX list, GLEIF. Not used by order: HKEXnews, Companies Registry (paid search), any lab or search API. HITL: local partner for Width 1 and Fill; Companies Registry / Cayman / Bermuda registers have no free machine interface; LEI coverage is thin (most issuers are Cayman or Bermuda incorporated) — a GLEIF golden-copy name route is the next keyless step if the CEO wants it.

## Refresh
None scheduled (global BUILD lock; Width 0 only). Re-run steps 1–4 into a new drop.
