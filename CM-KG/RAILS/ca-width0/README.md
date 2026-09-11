# CM-KG rail — Canada Width 0 (ca-cm-kg) daily refresh

Builds `C:\ALLOOLOO\CM-KG\ISSUERS\ca-issuers.xlsx`: every listed issuer on TSX, TSXV, CSE and Cboe Canada, enriched per ORDER-001.
First run 2026-09-10. Run `run_refresh.ps1` from this folder. Keys are read from `C:\ALLOOLOO\AGENT KEYS\` by `keys.py` into environment variables at import and are never printed.

Rules of the rail: **blank is blank** — no transfer agent, auditor, or newswire is ever inferred; every enriched cell carries a source URL and a read-by label; prices, quotes and market data are never carried (the CSE and Cboe feeds contain them and the scripts drop them).

## Workers

| Step | Script | Source | Fields | Read-by label written to the sheet |
|---|---|---|---|---|
| 1 | `fetch_sources.py` | tsx.com company-directory JSON (`/json/company-directory/search/{tsx,tsxv}/^*`); TMX listed-companies workbook (`/en/resource/571`); `thecse.com/api/webapi/listed-companies/`; `www-api.cboe.com/ca/equities/listing-directory-data/`; GLEIF ISIN-to-LEI mapping file (`mapping.gleif.org/api/v2/isin-lei/latest`) | raw feeds into `raw/` | — |
| 2 | `build_roster.py` | the raw feeds | name, ticker, exchange, security type, CSE tier, sector/sub-sector, HQ province/region, listing date/type, CSE SEDAR issuer number | `tsx.com company directory (exchange list)` · `TMX listed-companies workbook … (exchange list)` · `thecse.com listed-companies API (exchange list)` · `cboe.com listing-directory API (exchange list)` |
| 3 | `enrich.py cse` | thecse.com company page data (`/_next/data/<build>/en/listings/<slug>.json`; build id from step 1; slug from the name, Tavily site-search fallback) | transfer agent, auditor, HQ city/province/country, website, year end | `CSE` (auditor) · `thecse.com company page data (exchange site)` (other fields) |
| 4 | `enrich.py isin` | Tavily search restricted to quote/profile domains (marketscreener, investing.com, stockanalysis, tradingview, morningstar, ceo.ca, exchanges), full page text; regex `[A-Z]{2}[A-Z0-9]{9}\d` + check digit; page must mention name and ticker; conflicts and single weak mentions left blank | ISIN | `Tavily search + regex extraction from page text` |
| 5 | `enrich.py corp` (TSX, TSXV, Cboe corporates) and `enrich.py corp_cse_missing` (CSE issuers whose page has no auditor) | Tavily search "<name> transfer agent auditor", full page text; transfer agent from a closed list within 300 chars of "transfer agent"; auditor from explicit phrases, then canonicalised to a recognised firm list in `assemble.py` — unrecognised strings go to Gaps; jurisdiction from statute phrases | transfer agent, auditor, incorporation jurisdiction | `Tavily regex` (auditor) · `Tavily search + regex extraction from page text` (transfer agent, jurisdiction) |
| 6 | `enrich.py wire` (corporates) | Tavily search "<name> announces" restricted to newswire.ca, prnewswire.com, newsfilecorp.com, globenewswire.com, businesswire.com, accesswire.com, thenewswire.com; hits must carry the issuer name; wire = majority of up to three releases, mixed = blank | newswire of habit + release URLs | `Tavily search restricted to wire domains (release hits)` |
| 7 | `enrich.py sedar` (TSX, TSXV, Cboe corporates) | Tavily search of sedarplus.ca; accepted only when the profile heading equals the name. CSE rows: link constructed from the SEDAR issuer number in the CSE feed | SEDAR+ profile link, issuer number | `Tavily search of sedarplus.ca (profile page whose heading matches the name)` · `constructed from SEDAR issuer number in CSE feed …` |
| 8 | `lei_match.py` (+ `--reverse` twin for speed; GLEIF caps at 60 req/min) | GLEIF `/fuzzycompletions` on the legal name, candidates stored per row | LEI candidates | — (decided in step 11) |
| 9 | `isin_lei_lookup.py` | GLEIF ISIN-to-LEI mapping file from step 1 — exact ISIN match. Note: the file carries no Canadian-prefixed ISINs (checked 2026-09-10, 9.25 M rows) | ISIN → LEI | `GLEIF ISIN-to-LEI mapping file (exact ISIN match)` |
| 10 | `lei_records.py` | GLEIF `/lei-records?filter[lei]=…` batches | registration status, jurisdiction, HQ city/region/country | `GLEIF …` (same label as the LEI cell) |
| 11 | `assemble.py` | all of the above | the workbook: Coverage (live COUNTA), Gaps, TSX, TSXV, CSE, Cboe Canada, Gaps detail, Method | LEI cell: mapping-file match first, else `GLEIF name-exact` (GLEIF legal name equals the roster name after case/space/punctuation normalisation only); looser matches (legal-form expansion, dropped "The") are fuzzy and stay in Gaps with the candidate named |

## Standing changes (2026-09-10)
- Incorporation jurisdiction comes from the GLEIF legal-jurisdiction field only (label `GLEIF LEI record …`); the statute-phrase read from filings is retired. Rows without an LEI record carry a blank jurisdiction and a Gaps line.
- Roster rows the TMX workbook has not classified yet leave corporate scope when the name reads as a fund (ETF, Fund, Index, Portfolio, CDR, Trust Units, ETP): security type `Fund (by name; not yet in TMX workbook)`.
- Cadence: monthly full re-harvest via `CM-KG\RAILS\monthly.ps1` (Task Scheduler "Allooloo CM-KG Canada monthly", 15th 18:00 machine time); daily not switched on.

## Known broken / not available (as of 2026-09-10)
- **SEDI**: sedi.ca answers HTTP 403 to automated clients and publishes no per-issuer URL. The column holds the insider-search entry URL tagged with the SEDAR issuer number where known, labelled unverified.
- **SEDAR+ (TSX, TSXV, Cboe)**: sedarplus.ca also answers 403 and its profile pages are barely indexed; fill is ~1 %. CSE links are constructed from the issuer number and are unfetched.
- **TSXV listing tier**: not published in any public issuer list found.
- **Cboe Canada sector**: the Cboe feed carries none.
- **ISIN**: no exchange list publishes ISINs; the ISIN column is a page-text read and stays blank on conflict.
- **TMX workbook lag**: sector and province for TSX/TSXV come from the monthly file (previous month-end); issuers listed since carry no sector.
- **GLEIF deep pagination** caps at 10,000 records per filter, so a bulk country pull is impossible; hence the per-name matcher.
- **TMX Money GraphQL `fullAddress`** is unreliable (wrong cities) and is not used.

## Files
`keys.py` key loader · `fetch_sources.py` · `build_roster.py` · `enrich.py` (tasks: cse, isin, corp, corp_cse_missing, wire, sedar) · `lei_match.py` · `isin_lei_lookup.py` · `lei_records.py` · `assemble.py` · `run_refresh.ps1` orchestrator. Working files live in `raw/` (re-runs resume: every worker skips keys already in its `raw/enr_*.jsonl`; delete those files for a clean sweep).
