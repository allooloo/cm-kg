# CM-KG rail — United Kingdom Width 0 (uk-cm-kg)

Builds `C:\ALLOOLOO\CM-KG\ISSUERS\uk-issuers.xlsx`: every equity issuer on the LSE Main Market and AIM, plus Aquis Stock Exchange (Apex, Access, Aram, AQSE Main), enriched per ORDER-007. First run 2026-09-11 (1,570 rows: 896 Main Market · 596 AIM · 78 Aquis). Run `run_refresh.ps1` from this folder. Keys load in-process from `C:\ALLOOLOO\AGENT KEYS\` via `keys.py` and are never printed.

Rules of the rail: **sourced or blank** — no registrar, auditor or newswire is ever inferred; every enriched cell carries a source URL, a read-by label and a State (sourced · conflict; filled / confirmed belong to the Fill and Confirm passes). Prices, volumes, market caps and 52-week fields exist in the LSE and Aquis feeds and are dropped at write time; nothing priced is kept.

## Workers

| Step | Script | Source | Fields | Read-by label |
|---|---|---|---|---|
| 1 | `fetch_sources.py` | LSE price-explorer feed (`POST api.londonstockexchange.com/api/v1/components/refresh`, component `priceexplorersearch`, markets MAINMARKET / AIM, categories EQUITY, showonlylse) + a sweep of its 45 ICB sector filters; GLEIF ISIN-to-LEI mapping file; Companies House free bulk product `BasicCompanyDataAsOneFile` (~490 MB, monthly) | rosters and registry files into `raw/` | `LSE price explorer (exchange list)` |
| 2 | `ch_index.py` | the bulk file (5.69 M rows) | public-company rows only (4,642): number, name, status, registered office, incorporation date, SIC codes, previous names | `Companies House bulk data product (BasicCompanyDataAsOneFile, monthly)` |
| 3 | `lse_instruments.py` | `GET api.londonstockexchange.com/api/gw/lse/instruments/alldata/<TIDM>` | ISIN, SEDOL, trading segment, MiFIR type, funds type, admission date, ICB codes | `LSE instrument reference record (exchange site)` |
| 4 | `lse_issuer_profile.py` | `GET api.londonstockexchange.com/api/v1/pages?path=issuer-profile&parameters=tidm=…&tab=company-page&issuername=…` | address, country of incorporation, web address, ICB industry/supersector/sector/subsector, index roundel | `LSE issuer profile (exchange site)` |
| — | browser session (no script) | aquis.eu `/companies` page data (`__NEXT_DATA__`) and `/_next/data/<build>/companies/<symbol>.json` | Aquis roster: ISIN, segment, sector, registrar, registered address, website, corporate adviser, admission date → `raw/aquis.json` | `aquis.eu company page data (exchange site; read in a browser session)` |
| 5 | `build_roster.py` | steps 1, 3, 4 and `raw/aquis.json` | one row per issuer per market; security type from funds type / MiFIR type / name | — |
| 6 | `isin_lei_lookup.py` | GLEIF mapping file, exact ISIN (GB ISINs are present: 663,203 GB rows on 2026-09-11; 1,509 of 1,666 UK instrument ISINs hit) | LEI | `GLEIF ISIN-to-LEI mapping file (exact ISIN match)` |
| 7 | `lei_match.py` | GLEIF `/fuzzycompletions` for rows without a mapping hit (139 names) | LEI, accepted only when the GLEIF legal name equals the roster name (83) | `GLEIF name-exact` |
| 8 | `lei_records.py` | GLEIF `/lei-records?filter[lei]=…` | registration status, legal jurisdiction, legal and HQ address, `registeredAs` (Companies House number when `registeredAt` = RA000585) | `GLEIF LEI record (LEI per the LEI column)` |
| 9 | `ch_match.py` | LEI record `registeredAs` → Companies House number (1,055 rows); else name-exact against current and previous names in the PLC index (75); numbers not in the index → public profile page (4 reads) | number, profile link, registered office, jurisdiction (number prefix + country of origin), SIC codes, accounts filing-history link | `GLEIF LEI record registeredAs …` · `Companies House bulk data product …` · `Companies House public profile page` |
| 9b | `ch_api.py` | Companies House REST API — runs only when `AGENT KEYS\companieshouse.txt` exists (absent on 2026-09-11, so this step did not run) | number via API name search (exact name, public company), profile, jurisdiction field, SIC, latest accounts filing document link | `Companies House REST API (company profile)` |
| 10 | `enrich.py reg` | Tavily "<name> registrar auditor annual report", full page text | registrar from a closed list within 300 chars of "registrar"; auditor from explicit phrases, canonicalised to a recognised firm list in `assemble.py` (unrecognised → Gaps) | `Tavily search + regex extraction from page text` · `Tavily regex` |
| 11 | `enrich.py wire` | Tavily "<name> announces" restricted to LSE news-article pages (TIDM in the URL path = RNS), investegate.co.uk (RNS), PR Newswire, GlobeNewswire, Business Wire, ACCESS Newswire, Newsfile | newswire of habit = majority of up to three releases; mixed → blank | `Tavily search restricted to wire domains and LSE news-article pages (release hits)` |
| 12 | `assemble.py` | all of the above | Coverage (live COUNTA) · Gaps · LSE Main Market · AIM · Aquis Stock Exchange · Gaps detail · Method | — |

## Sources — who answers machines (tested 2026-09-11)

| Source | Answer | Used as |
|---|---|---|
| Companies House public profile pages | HTTP 200 to plain clients | profile reads for numbers outside the PLC index. **First registry in the estate that answers machines.** |
| Companies House bulk data product | HTTP 200, no login, ~490 MB monthly | registered office, jurisdiction, SIC, previous names |
| Companies House REST API | HTTP 401 without a key; no `companieshouse.txt` in AGENT KEYS | not used; `ch_api.py` ready |
| api.londonstockexchange.com | JSON, no key. Blocked with CloudFront HTTP 403 after ~3,100 calls in one hour at 4+4 threads; cleared in ~20 minutes | rosters, instrument records, issuer profiles — run at THREADS=1 |
| LSE news list API (issuer-profile tab=news) | HTTP 403 during the block; not retried per issuer | newswire read via Tavily instead |
| aquis.eu | HTTP 429 Vercel checkpoint to curl, requests and Tavily | read in the Browser pane; `raw/aquis.json` saved by the session |
| GLEIF API and mapping file | HTTP 200 | LEI, LEI record, ISIN→LEI |
| FCA National Storage Mechanism | api.data.fca.org.uk HTTP 403; UI behind a terms-of-use modal (not accepted by the machine); no per-issuer URL | column holds the search entry URL with the LEI to search by, labelled unverified; one Gaps line per row |

## Fill (first run, before the API pass)

| Field | Main Market (896) | AIM (596) | Aquis (78) |
|---|---|---|---|
| ISIN | 100 % | 100 % | 100 % |
| SEDOL | 100 % | 100 % | 0 % (not on the Aquis record) |
| LEI | 95.9 % | 98.0 % | 92.3 % |
| Companies House number / SIC / accounts link | 68.5 % | 77.5 % | 69.2 % |
| Registered office | 96.0 % | 98.2 % | 100 % |
| Incorporation jurisdiction | 100 % | 100 % | 93.6 % |
| Sector | 98.4 % | 99.8 % | 100 % (Aquis's own sector list) |
| Auditor | 37.7 % | 47.8 % | 29.5 % |
| Registrar | 38.4 % | 50.7 % | 100 % (exchange record) |
| Newswire of habit | 48.8 % | 66.4 % | 67.9 % |
| HQ city | 99.8 % | 100 % | 100 % |

Fund, depositary-receipt and debt rows (322) were kept with exchange data only and were not searched for auditor, registrar or newswire.

## Known broken / not available (as of 2026-09-11)
- **Listing category** (Equity Shares (Commercial Companies) / Transition / closed-ended funds / shell): the LSE issuer profile returns `listingcategory: null` for every issuer; the workbook carries the trading segment code instead (SET1, SET3, STMM, SSMM, SSQ3, SSX3/4, IOBE/U, SFM2; AIM: ASQ1, ASX1, AMSM) and a Gaps line per LSE row.
- **GLEIF mapping-file LEIs on the wrong entity**: 87 ISINs map to an LEI whose legal name is another entity (a registrar, a subsidiary, a renamed company). Those LEIs are kept with State `conflict`, reported in Gaps, and not used as a route to Companies House.
- **Companies House number** missing on 440 rows: funds and overseas issuers whose LEI is registered outside Companies House (Jersey, Guernsey, Bermuda, BVI, Cayman, Ireland …) and 123 UK-named issuers with neither a Companies House `registeredAs` nor a name-exact public-company row. The API name search (step 9b) is the next route.
- **FCA NSM**: no machine access; see the table.
- **Aquis SEDOL**: not published on the company record.
- **Auditor**: only explicit phrases count; "none found" on 513 corporates and 7 rows read only a noise string. The Companies House accounts filing link is recorded per row as the accounts source (a source, not a read: filings were not parsed).
- **LSE news API**: not used per issuer after the 403; RNS habit comes from LSE news-article URLs surfaced by Tavily.

## Files
`keys.py` (copy of the Canada loader) · `fetch_sources.py` · `ch_index.py` · `lse_instruments.py` · `lse_issuer_profile.py` · `build_roster.py` · `isin_lei_lookup.py` · `lei_match.py` · `lei_records.py` · `ch_match.py` · `ch_api.py` · `enrich.py` (tasks: reg, wire) · `assemble.py` · `run_refresh.ps1`. Working files live in `raw/` (git-ignored). Re-runs resume: every worker skips keys already in its `raw/*.jsonl`; delete those files for a clean sweep. `raw/aquis.json` must be refreshed in a browser session before a monthly run.
