# CM-KG rail — United Kingdom Width 1 (Disclosure) weekly refresh

Builds `C:\ALLOOLOO\CM-KG\DISCLOSURE\uk-disclosure.xlsx` (Events, Coverage, Gaps, HITL — needs MK, Method) and `C:\ALLOOLOO\CM-KG\DISCLOSURE\events\uk-events.jsonl`: the disclosure trail per corporate issuer — the fact that an announcement, filing or release exists, its date, and where it is. Not the documents. First run 2026-09-11 with a 12-month window (127,884 events, 1,227 of 1,234 corporates); the weekly refresh runs the same workers over the last 7 days (`WINDOW_DAYS=7`) and the assembler merges on the dedupe key (exchange, ticker, event type, date, URL).

Scope: the 1,234 corporate issuers in `CM-KG\ISSUERS\uk-issuers.xlsx` (Security type = Corporate; funds, investment companies, depositary receipts and debt out). Keys load from `C:\ALLOOLOO\AGENT KEYS\` through the Width 0 loader; never printed.

Name rule (CEO, 2026-09-10): a search-found wire release belongs to an issuer only when its title carries every key token of the name (or of a sourced alias — Companies House previous names are a source), or one token that is unique across the full 1,570-row roster **and** not a common English word (`common_words.txt`). Otherwise Gaps "ambiguous match". The issuer's own Investegate page, the Companies House filing history and the Aquis announcements feed are the issuer's own listings and are exempt.

Rules: **no event without a URL**; **no date read out of a headline** — the event date is the announcement, filing or release date; blank is blank.

## Workers

| Step | Script | Source | Fields | Read-by label |
|---|---|---|---|---|
| 1 | `investegate.py` | Investegate per-company listing `investegate.co.uk/company/<TIDM>?page=N` (50 per page, paged back to the window start; 3,159 pages read). RNS and the other regulatory information services (GNW = GlobeNewswire, PRN = PR Newswire, BZW = Business Wire, EQS, MFN) | announcement date, RIS source, RNS headline (= `rns_category`), URL; event type from the headline | `investegate.co.uk company page (RNS mirror)` |
| 2 | `ch_filings.py` | Companies House REST API filing history per issuer with a Companies House number (600 calls / 5 min) | filing date, registry category and description, form type; URL = the filing document page | `Companies House REST API (filing history)` |
| — | browser session + `aquis_ingest.py` | aquis.eu announcements feed (the exchange page's own Next.js data by year/month/page; 1,501 rows over 12 months, keyed by symbol) → `raw/aquis_announcements.json` | date, headline, URL | `aquis.eu announcements page data (exchange feed; read in a browser session)` |
| 3 | `wire_search.py` | Tavily: news topic over prnewswire.com, prnewswire.co.uk, globenewswire.com, businesswire.com, accesswire.com, newsfilecorp.com with `published_date`; a general `"<short name>" announces` query on the same domains, dated from the release URL | release title, date, URL, wire | `Tavily search (wire domains) + published_date` · `… + URL date` |
| 4 | `assemble_disclosure.py` | all of the above | Events (typed), Coverage (live COUNTIFS per issuer, zero-event flag), Gaps, HITL, Method; the jsonl twin | — |

Event types: `regulatory_announcement` (RNS not otherwise typed) · `financial_statement` (results, trading updates, annual report) · `agm_record_date` (AGM / GM notices and results, record dates) · `director_dealing` (PDMR dealings, board and adviser changes) · `early_warning` (Holding(s) in Company, TR-1, Form 8) · `corporate_action` (dividends, placings, issues, consolidations, name changes, admissions, offers, buybacks, total voting rights) · `halt_resume` (suspension, restoration, cancellation) · `newswire_release` · Companies House `ch_accounts_filed` · `ch_confirmation_statement` · `ch_officer_change` · `ch_name_change` · `ch_charge` · `ch_capital` · `ch_resolution` · `ch_psc` · `ch_auditor` · `ch_insolvency` · `ch_gazette` · `ch_other`. Typing rules live in `common.py` (`TYPE_RULES`, `NOT_FIN`, `CH_CATEGORY`).

## First run (2026-09-11)

| Measure | Value |
|---|---|
| Events | 127,884 (LSE Main Market 94,034 · AIM 30,171 · Aquis 3,679) |
| Issuers with events | 1,227 of 1,234; zero-event: 7 (listed in Gaps) |
| By source | Investegate 100,991 (1,220 issuers) · Companies House 23,943 (955 issuers) · Aquis feed 1,441 (75 issuers) · Tavily wires 1,509 (375 issuers) |
| RIS mix on Investegate | RNS 88,349 · GlobeNewswire 4,979 · Business Wire 2,882 · PR Newswire 2,648 · EQS 1,817 |
| Gaps | 274 rows: 263 issuers without a Companies House number (no filings source), 7 zero-event, 4 broken-source lines |

## Sources — who answers machines
| Source | Answer | Used as |
|---|---|---|
| investegate.co.uk | HTTP 200, paged, all three markets | RNS source of record |
| Companies House REST API | HTTP 200 with the key | filings per issuer |
| aquis.eu | HTTP 429 to plain clients; page data readable in a browser session; `public-api.elements.aquis.tech` HTTP 401 | announcements feed, browser read |
| LSE news list / market notices | the pages API exposes no news or notices component (404 on `rns-notices`, `notices`); the list loads through authenticated component calls | not used |
| FCA NSM | `api.data.fca.org.uk` HTTP 403; UI behind a terms-of-use modal | not used |
| Tavily | search API | wire releases outside the regulatory feed |

## HITL — needs MK (account, key or click)
- **FCA NSM**: accept the terms-of-use modal on data.fca.org.uk (a click) for a browser-session read; a machine route needs an FCA data account.
- **Aquis public API**: an Aquis Elements data account would replace the browser-session read of the announcements feed.
- **LSE news / notices**: an LSEG developer account for the authenticated news components (not blocking: Investegate carries RNS).

## Known broken / not available (2026-09-11)
- No LSE market notices or AIM notices as events (see the table). Aquis "notices" are trading-venue notices, not issuer events.
- Business Wire blocks direct fetch; GlobeNewswire and Business Wire releases come from search, dated from the URL.
- Issuers without a Companies House number (263 corporates: overseas incorporations and name-variant registrations) carry no filings until ORDER-009's adjudication fills the number.

## Run
```
python investegate.py (THREADS=4)   python ch_filings.py (THREADS=3)   python wire_search.py (THREADS=4)
python aquis_ingest.py <browser result file>          (after a browser-session read of the Aquis feed)
python assemble_disclosure.py [xlsx path] [jsonl path]
```
`run_refresh.ps1` runs the sequence with `WINDOW_DAYS=7`. Workers resume from `raw/*.jsonl`; delete those files for a clean backfill (`WINDOW_DAYS=365`).
