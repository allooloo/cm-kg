# nl-fill-confirm — Netherlands passes 2 (Fill) and 3 (Confirm), ORDER-016 Part B

Built from the Swiss rail (`ch-fill-confirm`) with the Dutch pockets: KVK number from the GLEIF record (RA000463) instead of Zefix, AFM notification registers instead of EQS / SHAB, Dutch agents (Euroclear Nederland, ABN AMRO, ING, IQ EQ, Computershare, Intertrust / CSC) and audit firms in the closed lists. Records are keyed by ISIN (the FIRDS roster carries no exchange symbol). Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\nl-cm-kg\fill-confirm\<date>\`; rebuilds write versioned copies to `POND\nl-cm-kg\assembled\<date>\` and mirror to `CM-KG\ISSUERS\nl-issuers.xlsx`, `CM-KG\DISCLOSURE\nl-disclosure.xlsx` (+ `events\nl-events.jsonl`).

## Reading order (CEO rule for the European nodes, 2026-09-11)
Perplexity (Agent API, preset low) → Grok (live layer) → Mistral. Mistral is translation and review only and never writes a field: `mistral_reads.py` reviews the Dutch-language items Perplexity and Grok sourced, confirms or disputes each in Dutch, and puts Mistral-only findings on the **Review** tab of the Disclosure workbook as flags. Label "review by Mistral (nl)". Chains: `run_build.ps1` (aliases → Claude → annual reports → ChatGPT batch submit, guarded against resubmission → Gemini AGM → Perplexity → rematch → Grok live → Mistral review) and `run_build2.ps1` (Confirm → conflict adjudication → rebuilds → spend) after the batch completed.

## First run — 2026-09-11 (84 Dutch corporate lines of 123 on Euronext Amsterdam; assembled drops 2026-09-11-4 issuers, -5 disclosure)
| Engine | Duty | Calls | Fields touched |
|---|---|---|---|
| Claude (claude-sonnet-5) | LEI conflicts 4 against the GLEIF record, Confirm conflicts 58 | 62 | LEI ruled 4; conflicts ruled 42, blanked 16 |
| ChatGPT (gpt-4.1-mini, Batch) | Text windows from 46 issuer-published PDFs (annual reports, results) | 46 | auditor 33, registrar 1, period end 44, going concern 46 |
| Gemini (gemini-flash-latest) | 12-month announcement sets for 83 issuers | 83 | 1 dated meeting / record-date event |
| Perplexity (Agent API, low) | Company pages for all 84 issuers | 84 | 72 verified pages; page-title aliases 14 |
| Grok (grok-4.6, Responses + web/x search) | Live layer, 40 issuers asked (168-hour window) | 41 | halts 1; silent-issuer items 15 |
| Mistral (mistral-small-latest) | Review only: 72 of 72 Dutch-language targets reviewed | 71 | 70 confirmed, 1 disputed, 100 flags on the Review tab; no field written |
| Tavily | Rematch: no zero-event or ambiguous issuer (84 of 84 carry events) | — | 0 |

Aliases: 26 issuers carry a sourced "Also known as" (GLEIF LEI record 14, issuer page title 14, release pages 2). States after the rebuild: ISIN confirmed 83 / sourced 40; LEI sourced 119 / filled 4; KVK number sourced 83; auditor filled 32 / confirmed 1; registrar sourced 5 / filled 2; newswire filled 38 / confirmed 1. Auditor 0 → 33; registrar 6 → 7. Disclosure: 2,707 events (1 new from the passes), 100 confirmed by a second source family (AFM register row and a wire release within 45 days).

`run_refresh.ps1` is the weekly shape (node lock and global BUILD lock respected; no scheduled task registered). `rebuild_disclosure.py` writes the Review tab and the 17-column Events sheet (Language included).
