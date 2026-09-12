# de-fill-confirm — Germany passes 2 (Fill) and 3 (Confirm), ORDER-015 Part B

Built from the Swiss rail (`ch-fill-confirm`) with the German pockets: Handelsregister number and court from the GLEIF record instead of Zefix, EQS News pages instead of SIX ad hoc, German registrars (Link Market Services, Computershare Deutschland, ADEUS, Better Orange, Clearstream) and audit firms in the closed lists, Xetra as the single exchange tab. Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\de-cm-kg\fill-confirm\<date>\`; rebuilds write versioned copies to `POND\de-cm-kg\assembled\<date>\` and mirror to `CM-KG\ISSUERS\de-issuers.xlsx`, `CM-KG\DISCLOSURE\de-disclosure.xlsx` (+ `events\de-events.jsonl`).

## Reading order (CEO rule for the European nodes, 2026-09-11)
Perplexity (Agent API, preset low) → Grok (live layer) → Mistral. Mistral is translation and review only and never writes a field: `mistral_reads.py` reviews the native-language items Perplexity and Grok sourced, confirms or disputes each in German, and puts Mistral-only findings on the **Review** tab of the Disclosure workbook as flags. Label "review by Mistral (de/fr)". The pre-rule extraction pass is kept aside as `raw\mistral_reads_old-extraction.jsonl`, never written to a record. Chains: `run_build.ps1` (aliases → Claude → annual reports → ChatGPT batch submit → Gemini AGM → Perplexity → rematch → Grok live → Mistral review) and `run_build2.ps1` (Confirm → conflict adjudication → rebuilds → spend) after the batch completed.

## First run — 2026-09-11 (409 corporates on Xetra; assembled drops 2026-09-11-9 issuers, -10 disclosure)
| Engine | Duty | Calls | Fields touched |
|---|---|---|---|
| Claude (claude-sonnet-5) | LEI conflicts 29 against the GLEIF record, Confirm conflicts 25 | 439 | LEI ruled 29; conflicts ruled 22, blanked 3 |
| ChatGPT (gpt-4.1-mini, Batch) | Text windows from 117 issuer-published PDFs (annual reports, results) | 117 | auditor 87, registrar 4, period end 112, going concern 116 |
| Gemini (gemini-flash-latest) | 12-month announcement sets for 306 issuers | 306 | 9 dated meeting / record-date events |
| Perplexity (Agent API, low) | Company pages for 400 issuers (cap PPLX_MAX=400) | 400 | 294 verified pages; page-title aliases 44 |
| Grok (grok-4.6, Responses + web/x search) | Live layer, 40 issuers asked (168-hour window) | 41 | halts 0; silent-issuer items 15 |
| Mistral (mistral-small-latest) | Review only: 293 of 294 native-language targets reviewed | 291 | 289 confirmed, 2 disputed, 433 flags on the Review tab; no field written |
| Tavily | Rematch on legal name or sourced alias for 254 zero-event and ambiguous issuers | — | 202 events added |

Aliases: 409 issuers carry a sourced "Also known as" (GLEIF LEI record 85, issuer page title 44, release pages 6, the rest from the roster's display names). States after the rebuild: ISIN confirmed 409 / sourced 11; LEI sourced 385 / filled 29; Handelsregister number sourced 380; auditor filled 84 / confirmed 2; registrar sourced 17 / confirmed 2 / filled 2; newswire confirmed 203 / filled 20 / sourced 75. Auditor Xetra 0 → 86; registrar Xetra 17 → 21. Disclosure: 1,703 events (211 new from the passes; rematch collisions ruled 385 through Claude); confirmed-by-second-family 0.

`run_refresh.ps1` is the weekly shape (node lock and global BUILD lock respected; no scheduled task registered). `rebuild_disclosure.py` writes the Review tab and the 17-column Events sheet (Language included).
