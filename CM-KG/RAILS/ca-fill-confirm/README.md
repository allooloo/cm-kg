# CM-KG rail — Canada passes 2 (Fill) and 3 (Confirm)

Applies the labs to the pockets the Width 0 and Width 1 harvests left, then checks every filled or sourced field against a second independent source. Rebuilds `CM-KG\ISSUERS\ca-issuers.xlsx` and `CM-KG\DISCLOSURE\ca-disclosure.xlsx` (+ `events\ca-events.jsonl`) with **read-by on every touched field** and a **State** (sourced · filled · confirmed · conflict). The pre-pass workbooks are kept beside them as `ca-issuers-width0.xlsx`, `ca-disclosure-width1.xlsx`, `ca-events-width1.jsonl`. First run 2026-09-10. Keys via the Width 0 loader; never printed.

Rules: aliases **sourced only** (GLEIF other entity names, the issuer's own wire company page, the exchange profile) — never a guess; the CEO name rule of 2026-09-10 applies to alias tokens too; no SEDAR+ / SEDI / CIRO / CDS fetches; no market data.

## Workers (pass 2 — Fill)

| Script | Engine / source | Duty | Label |
|---|---|---|---|
| `alias_sources.py` | GLEIF LEI record, wire company page (Cision / PR Newswire h1, Newsfile page path), exchange list / CSE page | "Also known as" per issuer, each alias with its source URL | `GLEIF LEI record (other entity names)` · `newswire.ca company page` · `prnewswire.com company page` · `newsfilecorp.com company page (page path)` · `exchange list (directory name)` |
| `perplexity_pages.py` | Perplexity sonar-pro (grounded) | current wire release page for issuers whose page was missing/stale; verified by fetch; display name becomes a sourced alias | `read by Perplexity (agent)` |
| `rematch.py` | Tavily + aliases; Claude on collisions | re-run the wire title match for zero-event and "ambiguous match" issuers using legal name OR alias | `Tavily search (wire domains) … [alias: X, source]` · `adjudicated by Claude` |
| `claude_adjudicate.py` | Claude claude-sonnet-5 | rule the Width 0 conflicting ISINs and unrecognised/conflicting auditor strings from the cited sources, or leave blank with reason | `adjudicated by Claude` |
| `fetch_bodies.py` | wires (Newsfile paced; Business Wire blocked) | release bodies for the readers, cached in `raw/bodies/` | — |
| `chatgpt_batch.py` | ChatGPT gpt-4.1-mini, Batch API, strict JSON schema | period end, statement date, auditor named, going-concern flag on financial_statement releases | `read by ChatGPT (batch)` |
| `gemini_agm.py` | Gemini gemini-flash-latest (long context) | AGM / special meeting / record dates stated in an issuer's 12-month release set (issuers without an agm_record_date event) | `read by Gemini` |
| `mistral_fr.py` | Mistral mistral-small-latest | the same fields from French-language releases | `read by Mistral (fr)` |
| `grok_live.py` | Grok grok-4.6, xAI Responses API, web + X search | 48-hour live layer in the daily refresh: halts/resumes per exchange, newswire for silent issuers; URL required | `read by Grok (live)` |

## Pass 3 — Confirm (`confirm.py`)
Second sources: ISIN → a second quote-page domain (Width 0 candidates or a fresh Tavily read); LEI → the GLEIF ISIN-to-LEI mapping file agreeing with the name-exact match (the only independent LEI source that answers; CA ISINs are absent from it, so most LEIs stay *sourced*); transfer agent / auditor → a second page on a different domain naming the same agent/firm (Tavily, different phrasing); newswire → the dominant wire in the issuer's Width 1 events; jurisdiction → GLEIF vs the statute phrase read from filings; alias → two alias sources agreeing. Events: financial_statement / agm_record_date rows confirmed by a second copy on another wire or a bulletin on the same date. Agree → confirmed with both sources; disagree → conflict.

## Rebuild
`rebuild_issuers.py` then `rebuild_disclosure.py`. Each Method tab lists all eight engines with the exact duty and the count of fields touched; engines that touched nothing say so.

## Alias channel 4 (standing change, 2026-09-10)
`website_alias.py`: the issuer's own website `<title>`, the site taken from the exchange profile's website field (TMX Money company record for TSX/TSXV, CSE company page for CSE). Generic titles, bare domains and titles equal to the legal name yield nothing. Runs on the zero-event issuers each weekly run (`TARGETS=all` for every corporate). Label: `issuer website <title> (site from exchange profile)`.

## Cadence (standing change, 2026-09-10)
Weekly, not daily: `CM-KG\RAILS\weekly.ps1` (Task Scheduler "Allooloo CM-KG Canada weekly", Friday 18:00 machine time = after TSX close in Toronto) runs the Width 1 refresh with `WINDOW_DAYS=7`, the Grok live layer with `LIVE_HOURS=168`, then this rail. `CM-KG\RAILS\monthly.ps1` ("Allooloo CM-KG Canada monthly", 15th 18:00) re-harvests identity from scratch and re-applies the Fill + Confirm columns.

## Refresh sequence (run_refresh.ps1)
`run_refresh.ps1` here runs after the Width 1 refresh: Grok live layer (48 h), body fetch for new financial/AGM/French releases, ChatGPT batch submit+collect, Gemini for issuers still without AGM events, Mistral for new French releases, confirm for issuers whose fields changed, then both rebuilds.

## Known broken (2026-09-10)
- Newsfile bot protection blocks release bodies at any pace after a burst; Newsfile financial releases mostly lack bodies (no ChatGPT read). Business Wire blocks all fetches.
- gpt-5 family needs organisation verification on this OpenAI account; gpt-4.1-mini used. gemini-2.5-flash is retired for new users; gemini-flash-latest used.
- Perplexity's `/v1/agent` endpoint exists but takes a different body; grounded chat completions (sonar-pro) were used and labelled per the order.
- LEI has no second independent source for Canadian ISINs.
