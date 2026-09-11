# au-fill-confirm — Australia passes 2 (Fill) and 3 (Confirm), ORDER-012

Pond-native rail for node `au-cm-kg`. `raw\` is a junction to the open drop `CM-KG\POND\au-cm-kg\fill-confirm\<date>\`. Readers write there; `rebuild_issuers.py` and `rebuild_disclosure.py` read the latest assembled outputs plus every drop and write versioned copies to `POND\au-cm-kg\assembled\<date>\`, mirrored to `CM-KG\ISSUERS\au-issuers.xlsx` and `CM-KG\DISCLOSURE\au-disclosure.xlsx` (+ `events\au-events.jsonl`).

## First run — 2026-09-11 (1,792 issuers; assembled drops 2026-09-11-4 issuers, 2026-09-11-5 disclosure)

| Engine | Duty on Australia | Calls | Fields touched |
|---|---|---|---|
| Claude (claude-sonnet-5) | LEI conflict rulings, ACN gaps, Confirm conflict adjudication | 258 | LEI ruled 10 / blanked 1; ACN ruled 29 / blank with reason 17; conflicts ruled 110 / blanked 40 |
| ChatGPT (gpt-4.1-mini, Batch API) | Text windows from 2,442 ASX-lodged documents (annual reports, Appendix 4E/4D) | 2,442 | Auditor 1,483; share registry 653; accounts period end 1,615; going-concern flag 1,621 |
| Gemini (gemini-flash-latest) | AGM notices and registry pages for 1,131 issuers | 1,131 | Share registry 46; 23 dated events |
| Perplexity (Agent API, preset low) | Cold reads for 400 issuers with no events in window or no website | 400 | 346 pages verified, 38 aliases |
| Grok (grok-4.6, Responses + web/X search) | Live layer: halts, suspensions, reinstatements; silent issuers | running at rebuild time | events merge at the next rebuild_disclosure |
| Mistral | Non-English announcements | 0 (none found) | — |
| Tavily | Alias sources, Confirm second sources | see spend | — |

Aliases: 1,384 issuers with sourced aliases (3,262 from ASIC previous names, 40 GLEIF other names, 40 ASX records, 38 issuer page titles, 57 wire release pages).

States after Confirm (ASX + NSX): ISIN confirmed 949 / sourced 921; LEI confirmed 398 / sourced 203 / filled 10 / conflict 5; ACN sourced 1,741 / filled 29 / confirmed 19; auditor filled 1,309 / confirmed 172; share registry confirmed 429 / filled 717 / sourced 207; newswire confirmed 1,741; state confirmed 60 / filled 22 / sourced 635. Jurisdiction conflicts 55 (ACN at ASIC but GLEIF legal jurisdiction elsewhere).

Auditor fill: ASX 0 → 1,481 (268 corporates still blank: no annual-report announcement in the 12-month window or no text layer). Share registry: ASX 660 → 1,343, NSX 11 → 10 (one blanked on conflict).

Disclosure rebuild: 124,300 events (25 new from the passes, 112 confirmed by a second source, 2 rematch events, 51 collisions logged).

### Build-day notes
- `annual_reports.py` gained a `SHARD=i/n` helper (document shards into the shared `raw/reports` cache) so 2,459 PDFs finished inside the day; the weekly runs the single worker.
- `run_build.ps1` / `run_build2.ps1` are the build-day chains (Fill workers; Confirm + rebuilds). The weekly uses `run_refresh.ps1`.
- Grok live (LIVE_MAX_ISSUERS=200, sequential web+X searches) is the slowest step; it ran past the rebuilds and its events land in the next disclosure rebuild.
