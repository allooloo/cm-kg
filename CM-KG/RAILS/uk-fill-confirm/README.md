# CM-KG rail — United Kingdom passes 2 (Fill) and 3 (Confirm)

Applies the labs to the pockets the Width 0 and Width 1 harvests left, then checks every filled or sourced identity field against a second independent source. Rebuilds `CM-KG\ISSUERS\uk-issuers.xlsx` and `CM-KG\DISCLOSURE\uk-disclosure.xlsx` (+ `events\uk-events.jsonl`) with **read-by on every touched field** and a **State** (sourced · filled · confirmed · conflict). The pre-pass workbooks are kept beside them as `uk-issuers-width0.xlsx`, `uk-disclosure-width1.xlsx`, `uk-events-width1.jsonl`; every rebuild also lands a versioned copy in `CM-KG\POND\uk-cm-kg\assembled\<date>\` (pond rule). First run 2026-09-11. Keys via the Width 0 loader; never printed. Working folder `raw\` is a junction to the open pond drop `POND\uk-cm-kg\fill-confirm\<date>\`.

Rules: aliases **sourced only** (Companies House previous names, GLEIF other entity names, the issuer's own regulatory-news page name, the exchange profile display name, a news-page title found by Perplexity) — never a guess; the CEO name rule applies to alias tokens too; no login fetches; no market data. Tavily calls run through a budget guard read live from the plan counter (Growth plan, 100,000 credits/month from 2026-09-11; cap = plan limit less a 10 % floor).

## Workers (pass 2 — Fill)

| Script | Engine / source | Duty | Label |
|---|---|---|---|
| `alias_sources.py` | Companies House REST API previous names, GLEIF LEI record other names, Investegate page display name, LSE issuer profile display name | "Also known as" per issuer, each alias with its source URL; `aliases.json` handed to the Width 1 assembler for the rematch | `Companies House REST API (previous names)` · `GLEIF LEI record (other entity names)` · `investegate.co.uk company page (display name)` · `LSE issuer profile (display name)` |
| `claude_adjudicate.py` | Claude claude-sonnet-5 | rule the Width 0 pockets from cited evidence: GLEIF mapping-file LEI conflicts (49), unmatched Companies House rows (263, API name search as evidence), unrecognised auditor strings (79); blank with reason otherwise | `adjudicated by Claude` |
| `ch_accounts.py` | Companies House document API (key) | the latest accounts filing PDF per issuer (1,164; image PDFs, no text layer), kept for the ChatGPT read | — |
| `fetch_bodies.py` | Investegate announcement pages | bodies of every financial_statement / agm_record_date announcement (7,196 of 7,219; Business Wire blocks 23) cached for the readers | — |
| `chatgpt_batch.py` | ChatGPT gpt-4.1-mini, Batch API, strict JSON schema | A. accounts: the accounts PDF read as page images in ≤100-page parts (1,875 parts, 1,122 issuers): auditor, period end, going-concern language, registrar — **the auditor lift**. B. results: 4,634 results announcements: period end, statement date, auditor named, going-concern language | `read by ChatGPT (batch)` |
| `gemini_agm.py` | Gemini gemini-flash-latest (long context) | the 12-month RNS set per issuer without an AGM/record-date event or without a registrar (554 issuers): meeting / record dates stated (1,129 findings), registrar named (59) | `read by Gemini` |
| `perplexity_pages.py` | Perplexity — this run sonar-pro; from ORDER-010 Part B the Agent API (preset low) | current regulatory-news page for issuers with a missing/empty Investegate page (14 asked, 9 verified); page titles as sourced aliases (6) | `read by Perplexity (agent)` → `read by Perplexity (agent · low/fast)` |
| `rematch.py` | Tavily + aliases; Claude on collisions | wire / RNS title match re-run on legal name OR sourced alias for zero-event and ambiguous issuers (7 targets, 0 events found, 10 collisions ruled) | `Tavily search (wire domains) … [alias: X, source]` · `adjudicated by Claude` |
| `grok_live.py` | Grok grok-4.6, xAI Responses API, web + X search | weekly live layer: suspensions / restorations / cancellations per market and news for silent issuers; URL required (validation run: 5 items, 0 silent-issuer items) | `read by Grok (live)` |
| `mistral_reads.py` | Mistral mistral-small-latest | non-English announcements in the UK set: 0 found, 0 read | `read by Mistral` |

## Pass 3 — Confirm (`confirm.py`, then `conflict_adjudicate.py`)
Second sources: ISIN → the GLEIF mapping file (issuer's LEI) or a second quote page; LEI → the Companies House number on the LEI record equals the name-route number, or the mapping file agrees with the name-exact match; Companies House number → the LEI record's registeredAs or the API name search returning the same number; registrar → a Gemini RNS read, the ChatGPT accounts read, the Aquis record, or a second page on a different domain; auditor → the ChatGPT accounts read (the statutory accounts), else a second page; newswire → the dominant service in the Width 1 event set; jurisdiction → GLEIF legal jurisdiction vs Companies House; alias → two sources agreeing. Agree → confirmed with both cited; disagree → conflict → Claude rules from both readings (558 cases: 483 ruled, 75 unsettled and blanked with the reason in Gaps).

## Results (first run)
- Auditor: 646 → 1,030 issuers (Main Market 338 → 467, AIM 285 → 507, Aquis 23 → 56) of 1,234 corporates; 369 confirmed by the accounts read, 524 filled.
- Fields written: ChatGPT auditor 385, registrar 270, accounts period end 917, going-concern flag 919 (228 material-uncertainty); Claude LEI 46 ruled / 3 blanked, Companies House numbers 32, auditor strings 23; Gemini registrar 27; newswire from the Width 1 event set 359; aliases 2,897 on 1,183 issuers.
- States (identity fields): ISIN confirmed 1,173; see the Method tab for the full state table.
- Disclosure: see `rebuild_disclosure.py` output on the Method tab (Gemini AGM/record-date rows, ChatGPT results reads in Detail, confirmations across RNS / Companies House / wire within 45 days).

## Refresh sequence (`run_refresh.ps1`, called by `CM-KG\RAILS\uk-weekly.ps1` after the Width 1 refresh; skips on the node lock)
Grok live layer (7 days) → Width 1 assemble with the live layer → aliases → bodies → ChatGPT results batch submit → Gemini → Mistral → batch collect → confirm → rebuild issuers → rebuild disclosure → spend.

## Known broken (2026-09-11)
- Companies House accounts are image PDFs: no text layer, so the read is by page image (ChatGPT) — 42 issuers' documents did not download (document API errors).
- The Anthropic Messages API key cannot read balance or cost (Admin API key needed: HITL).
- Business Wire blocks body fetch; Sonar Chat Completions retire 2026-09-27 (Agent API wired from ORDER-010 Part B).
- 2026-09-11: the scheduled UK weekly task fired mid-build and overwrote the Width 1 event set (see `uk-width1\README.md`); this rail's files were untouched, the disclosure rebuild was re-run after the 12-month recovery.
