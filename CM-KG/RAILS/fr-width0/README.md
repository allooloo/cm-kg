# fr-width0 — France Width 0 (ORDER-016 Part A)

Pond-native rail for node `fr-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\fr-cm-kg\width0\<date>\`; `assemble.py` reads every drop (newest wins per key) and writes `POND\fr-cm-kg\assembled\<date>\fr-issuers.xlsx`, mirrored to `CM-KG\ISSUERS\fr-issuers.xlsx`. Sourced or blank; no prices. Duty line on the node page: MiFID II product governance.

## Steps
1. `fetch_sources.py` — ESMA FIRDS full equity files (weekly zips found through the registers.esma.europa.eu Solr index; 729,992 instrument records scanned): every share admitted to trading on Euronext Paris (XPAR), Euronext Growth Paris (ALXP) and Euronext Access Paris (XMLI) with the issuer LEI, names, CFI, currency, first-trading and admission dates. Euronext's own list pages sit behind an anti-bot form (HITL). AMF BDIF: the last 10,000 regulatory-information items paged through the public API to index filer names to AMF tokens.
2. `build_roster.py` — 712 share lines (Paris 316, Growth 259, Access 137); 590 French ISINs; every line carries an issuer LEI.
3. `isin_lei_lookup.py` / `lei_match.py` / `lei_records.py` — GLEIF records for every LEI (693 of 711 ISINs also in the mapping file).
4. `siren_match.py` — the State's public company search (recherche-entreprises.api.gouv.fr, no key): the SIREN on the LEI record's registeredAs (INSEE, RA000189) looked up and confirmed (582), name-exact otherwise (1); 583 of 590 French corporates. Carried: SIREN, legal form, status, creation date, NAF code, siège; Annuaire des entreprises link; Infogreffe as an unverified search entry.
5. `enrich.py reg|wire` — Tavily: registrar / securities-services agent from a closed list (Uptevia, Société Générale Securities Services, CACEIS, BNP Paribas Securities Services, Euroclear France, CIC, Banque Transatlantique, Computershare); wires (Actusnews, GlobeNewswire, Business Wire, PR Newswire, ACCESS, Newsfile, EQS).
6. `assemble.py` — the workbook (Coverage, Gaps, three market tabs, Gaps detail, HITL, Method).

## First run — 2026-09-11 (assembled drop 2026-09-11)
| Field | Paris (316; 288 FR) | Growth (259; 234 FR) | Access (137; 68 FR) |
|---|---|---|---|
| ISIN, LEI, listing date | 316 | 259 | 137 |
| SIREN + register link | 286 | 231 | 66 |
| AMF filer token (BDIF, last 10,000 items) | 188 | 79 | 1 |
| Registered office | 310 | 257 | 131 |
| Incorporation jurisdiction | 310 | 257 | 131 |
| Sector (NAF) | 286 | 231 | 66 |
| Auditor / annual report | 0 (link only) | 0 | 0 |
| Share registrar | 73 | 33 | 5 |
| Newswire of habit | 224 | 160 | 14 |

Answered machines: ESMA FIRDS, recherche-entreprises.api.gouv.fr, bdif.amf-france.org API (last 10,000 items, no filter parameter found), GLEIF, Tavily. Refused: live.euronext.com lists (anti-bot form, also from a browser session), Infogreffe per-company pages (search UI), INPI API (account).

## Refresh
No scheduled task (global BUILD lock). `run_refresh.ps1` to be written with the Width 1 rail.
