# jp-width1 — Japan Width 1 (ORDER-017 re-cut), statutory filings over 12 months

Pond-native rail for node `jp-cm-kg`. Workers write into `raw\` (a junction to the open drop `CM-KG\POND\jp-cm-kg\width1\<date>\`); the assembler reads every drop plus the last versioned event set, dedupes on (exchange, code, type, date, URL), and writes `CM-KG\DISCLOSURE\jp-disclosure.xlsx` + `CM-KG\DISCLOSURE\events\jp-events.jsonl` with a versioned copy under `CM-KG\POND\jp-cm-kg\assembled\<date>\`. Japanese titles as EDINET publishes them; no machine translation; no search layer at Width 1 (ORDER-017: Perplexity Search + preset fast and Tavily extraction belong to the Fill pass).

## Sources
| Worker | Source | Read-by label |
|---|---|---|
| edinet_events.py | EDINET API v2 documents list, one call per calendar day over the window (type=2, key `AGENT KEYS\edinet.txt`), cached as `raw\edinet_daily\<date>.json` and cut per roster EDINET code: securities reports, quarterly / half-year reports, extraordinary reports, large-shareholding reports, registration statements, tender offers, buy-back reports and amendments, each with its EDINET viewer page | EDINET API v2 documents list (statutory filings per EDINET code) |

TDnet (JPX timely disclosure: 決算短信, ad hoc) has no public API and its search is a JavaScript form (HITL: TDnet data feed or a local partner). PRO Market issuers file with the exchange, not EDINET.

## First run — 2026-09-12 (12-month window, 3,962 carried lines; assembled drop 2026-09-12-3)
366 daily lists, 84,317 documents in the window, **39,266 events** on the roster's issuers, every one dated and URL-carrying, State sourced. Issuers with at least one event: 3,708 of 3,962 (zero events: 254 — PRO Market lines and lines without an EDINET filer).

By type: regulatory_filing 13,295 · ad_hoc 8,230 (臨時報告書) · results 7,380 (有価証券報告書, 四半期 / 半期報告書) · corporate_news 6,105 (buy-back status reports) · prospectus 2,878 · major_holder 1,221 · takeover 157. Language: Japanese 39,266.

## Refresh
`run_refresh.ps1` (no scheduled task: global BUILD lock): `pond_open.py jp-cm-kg jp-width1 width1`, `edinet_events.py` with `WINDOW_DAYS=7` (seven daily lists), `assemble_disclosure.py`.
