# CM-KG rail — Canada Width 1 (Disclosure) daily refresh

Builds `C:\ALLOOLOO\CM-KG\DISCLOSURE\ca-disclosure.xlsx` (Events, Coverage, Gaps, Method) and `C:\ALLOOLOO\CM-KG\DISCLOSURE\events\ca-events.jsonl`: the disclosure trail per corporate issuer — the fact that a release, bulletin or event exists, its date, and where it is. Not the documents. First run 2026-09-10 with a 12-month window; the daily refresh runs the same workers over the last 48 hours (`WINDOW_DAYS=2`) and the assembler merges on the dedupe key (exchange, ticker, event type, date, URL).

Scope: the 2,851 corporate issuers in `CM-KG\ISSUERS\ca-issuers.xlsx` (Security type = corporate). Keys are read from `C:\ALLOOLOO\AGENT KEYS\` by the Width 0 loader; never printed.

Name rule (CEO, 2026-09-10): a wire release belongs to an issuer only when its title carries every key token of the name, or one token that is unique across the full 4,820-row roster **and** not a common English/French word (`common_words.txt`). Titles matched on a token failing either test go to Gaps as "ambiguous match". Enforced in `assemble_disclosure.py` on every wire event (`common.name_match`).

Rules: **no event without a URL**; **no date read out of a headline** — the event date is the release or bulletin date; wire hits that name another issuer are counted, not taken; blank is blank.

## Workers

| Step | Script | Source | Fields | Read-by label |
|---|---|---|---|---|
| 1 | `wire_pages.py` | Newsfile per-company page (`newsfilecorp.com/company/<id>/…`, latest 20), Cision (`newswire.ca/news/<slug>/?page=N`, walked back to the window), PR Newswire (`prnewswire.com/news/<slug>/?page=N`) — for issuers whose newswire of habit is one of the three | release title, date, URL, wire | `newsfilecorp.com company page` · `newswire.ca company page` · `prnewswire.com company page` |
| 2 | `wire_search.py` | Tavily: news topic over the seven wire domains with `published_date`; a general query `"<short name>" announces` over the same domains; general search on globenewswire.com and businesswire.com. Dates in order of trust: Tavily published_date, then the date in the release URL, then the release's own dateline as indexed in the snippet ("(Newsfile Corp. - …)", "… /CNW/", "… /PRNewswire/", ACCESS Newswire, TheNewswire). Title must carry the issuer name (all key tokens, or one token unique to that issuer across the roster). | release title, date, URL, wire | `Tavily search (wire domains) + published_date` · `… + URL date` · `… + dateline in indexed snippet` |
| 3 | `release_dates.py` | release pages of search hits that carried no date (Newsfile, Accesswire, TheNewswire): the date printed on the page | date | `Tavily search (wire domains) + release page date` |
| 3b | `newsfile_snippets.py` | Tavily search on newsfilecorp.com only (two general queries + one dated news query) for Newsfile-wire issuers and any issuer with undated Newsfile hits; the date is read from the release's own dateline "(Newsfile Corp. - Month D, YYYY)" as indexed in the snippet, or from published_date. Newsfile itself is never fetched. | release title, date, URL | `Tavily search (newsfilecorp.com) + dateline in indexed snippet` · `… + published_date` |
| 4 | `tsxv_bulletins.py` | TMX Info TSX Venture company-documents controller per PO id (`apps.tmx.com/TSXVenture/…GetPage=CompanyDocuments&PO_ID=…&BulletinsMode=on` with a date range); PO ids from the TMX listed-companies workbook | bulletin category, type, date, notice URL | `apps.tmx.com TSXV company documents` |
| 5 | `cse_bulletins.py` | CSE bulletins feed `website-data-api-v2.thecse.com/api/bulletins?locale=en` (every bulletin since 2003), filtered to issuer symbols and the window; page `thecse.com/bulletin/<slug>/` | bulletin title, kind, date, URL | `thecse.com bulletins API` |
| 6 | `assemble_disclosure.py` | all of the above | Events (typed from titles and bulletin kinds), Coverage (live COUNTIFS per issuer, zero-event flag), Gaps, Method; the jsonl twin | — |

Event types: `newswire_release`, `financial_statement` (results releases by title), `agm_record_date` (meeting / record-date releases and bulletins), `early_warning` (the wire copy of an early-warning release), `corporate_action` (dividends, distributions, consolidations, splits, rights, name/symbol changes, listings, delistings, NCIBs), `halt_resume` (halt, resume, cease-trade bulletins and releases), `exchange_bulletin` (other bulletins). Typing rules live in `common.py` (`TYPE_RULES`, `NOT_FIN`).

## Known broken / not available (2026-09-10)
- **SEDI and the early-warning system**: not attempted (ORDER-003); sedi.ca answers HTTP 403 to machines. Early-warning press releases on the wires are carried when they exist.
- **CIRO halts**: `ciro.ca/newsroom/halts-and-resumptions` answers HTTP 403 to machines and the browser navigation is denied. Halts and resumes come from TSXV and CSE bulletins and from wire releases only.
- **CDS bulletins**: bulletin lists sit behind the CDS participant login. Corporate-action dates come from exchange bulletins and wire releases only.
- **TSX (senior) bulletins**: no public per-issuer bulletin list found; the TMX company-documents controller serves TSXV only.
- **Cboe Canada notices**: the listing-notices pages render no list to machines; corporate-action bulletins are a subscription service.
- **Newsfile company page** shows the latest 20 releases; older Newsfile releases come from search plus release-page dates.
- **Newsfile bot protection**: more than ~2 requests per second draws 202/403/503 for about 15 minutes. Run Newsfile passes with `ONLY_WIRE=Newsfile DELAY=2 THREADS=2` (wire_pages) and `DELAY=1.5 THREADS=2` (release_dates); Tavily extract cannot read Newsfile either.
- **GlobeNewswire and Business Wire** block direct fetch; their releases come from search, dated from the URL.
- **TSXV issuers without a PO id** (listed after the workbook month) get no TSXV bulletins until the next workbook.

## Run
```
python wire_pages.py        (THREADS=5)   python wire_search.py   (THREADS=6)   python tsxv_bulletins.py (THREADS=4)   python cse_bulletins.py
python release_dates.py     (after wire_search)
python assemble_disclosure.py [xlsx path] [jsonl path]
```
`run_refresh.ps1` runs the sequence with `WINDOW_DAYS=2`. Workers resume from `raw/*.jsonl`; delete those files for a clean backfill (set `WINDOW_DAYS=365`).
