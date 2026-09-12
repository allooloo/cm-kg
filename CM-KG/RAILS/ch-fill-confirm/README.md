# ch-fill-confirm — Switzerland passes 2 (Fill) and 3 (Confirm), ORDER-015 Part B

Built from the Singapore rail (`sg-fill-confirm`) with the Swiss pockets: Zefix (UID) instead of ACRA, EQS News / SIX ad hoc pages and the SHAB API instead of SGXNet, Swiss registrars and audit firms in the closed lists, GLEIF full legal names for the searches. Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\ch-cm-kg\fill-confirm\<date>\`; rebuilds write versioned copies to `POND\ch-cm-kg\assembled\<date>\` and mirror to `CM-KG\ISSUERS\ch-issuers.xlsx`, `CM-KG\DISCLOSURE\ch-disclosure.xlsx` (+ `events\ch-events.jsonl`).

## Reading order (CEO rule for the European nodes, 2026-09-11)
Perplexity (Agent API, preset low) → Grok (live layer) → Mistral. Mistral is translation and review only: it never writes a field. `mistral_reads.py` runs in review mode over the native-language items that Perplexity and Grok sourced, confirms or disputes each one in the native language, and puts Mistral-only findings on the **Review** tab of the Disclosure workbook as flags. Label "review by Mistral (de/fr)". An earlier extraction pass (the pre-rule shape) is kept aside as `raw\mistral_reads_old-extraction.jsonl` and was never written to a record. `run_build.ps1` carries the order: aliases → Claude adjudication → annual reports → ChatGPT batch submit → Gemini AGM → Perplexity → rematch → Grok live → Mistral review; `run_build2.ps1` runs Confirm, conflict adjudication and the rebuilds after the ChatGPT batch has completed.

## First run — 2026-09-11 (233 corporates on SIX and BX Swiss; assembled drops 2026-09-11-6 issuers, -7 disclosure)
| Engine | Duty | Calls | Fields touched |
|---|---|---|---|
| Claude (claude-sonnet-5) | LEI conflicts 13 against the GLEIF record, Confirm conflicts 11 | 486 | LEI ruled 12, blanked 1; conflicts ruled 6, blanked 5 |
| ChatGPT (gpt-4.1-mini, Batch) | Text windows from 89 issuer-published PDFs (annual reports, results) | 89 | auditor 55, registrar 19, period end 85, going concern 89 |
| Gemini (gemini-flash-latest) | 12-month announcement sets for 188 issuers | 188 | registrar 8; 10 dated meeting / record-date events |
| Perplexity (Agent API, low) | Company pages for all 233 issuers | 233 | 179 verified pages; page-title aliases 25 |
| Grok (grok-4.6, Responses + web/x search) | Live layer, 40 issuers asked (168-hour window) | 42 | halts 0; silent-issuer items 4 |
| Mistral (mistral-small-latest) | Review only: 172 of 179 native-language targets reviewed | 165 | 163 confirmed, 2 disputed, 228 flags on the Review tab; no field written |
| Tavily | Rematch on legal name or sourced alias for 91 zero-event and ambiguous issuers | — | 124 events added |

Aliases: 233 issuers carry a sourced "Also known as" (GLEIF LEI record 213, issuer page title 25, release pages 6). States after the rebuild: ISIN confirmed 230 / sourced 599 (all lines); LEI sourced 734 / filled 12 / conflict 12; UID sourced 189; auditor filled 54 / confirmed 1; registrar confirmed 7 / filled 16 / sourced 49; newswire confirmed 91 / filled 4 / sourced 71. Auditor SIX 0 → 52, BX Swiss 0 → 3; registrar SIX 51 → 64, BX Swiss 7 → 8. Disclosure: 1,385 events (134 new from the passes; rematch collisions ruled 462 through Claude); confirmed-by-second-family 0 (the Swiss trail has one register family per item; the wire family rarely repeats the same results date).

`run_refresh.ps1` is the weekly shape (node lock and global BUILD lock respected; no scheduled task registered). `rebuild_disclosure.py` writes the Review tab and the 17-column Events sheet (Language included).
