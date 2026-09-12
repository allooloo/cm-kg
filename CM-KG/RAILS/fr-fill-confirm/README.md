# fr-fill-confirm — France passes 2 (Fill) and 3 (Confirm), ORDER-016 Part B

Built from the Swiss rail (`ch-fill-confirm`) with the French pockets: SIREN from the register route (recherche-entreprises, GLEIF RA000189 / RA000192) instead of Zefix, AMF BDIF regulated information instead of EQS / SHAB, French registrars (Uptevia, Société Générale Securities Services, CACEIS, BNP Paribas Securities Services, Euroclear France, CIC, Computershare) and audit firms in the closed lists. Records are keyed by ISIN (the FIRDS roster carries no exchange symbol). Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\fr-cm-kg\fill-confirm\<date>\`; rebuilds write versioned copies to `POND\fr-cm-kg\assembled\<date>\` and mirror to `CM-KG\ISSUERS\fr-issuers.xlsx`, `CM-KG\DISCLOSURE\fr-disclosure.xlsx` (+ `events\fr-events.jsonl`).

## Reading order (CEO rule for the European nodes, 2026-09-11)
Perplexity (Agent API, preset low) → Grok (live layer) → Mistral. Mistral is translation and review only and never writes a field: `mistral_reads.py` reviews the French-language items Perplexity and Grok sourced, confirms or disputes each in French, and puts Mistral-only findings on the **Review** tab of the Disclosure workbook as flags. Label "review by Mistral (fr)". Chains: `run_build.ps1` (aliases → Claude → annual reports → ChatGPT batch submit, guarded against resubmission → Gemini AGM → Perplexity (cap 600) → rematch → Grok live → Mistral review) and `run_build2.ps1` (Confirm → conflict adjudication → rebuilds → spend) after the batch completed.

## First run — 2026-09-11/12 (590 French corporate lines of 712 on Euronext Paris, Growth and Access; assembled drops 2026-09-12 issuers, 2026-09-12-2 disclosure)
| Engine | Duty | Calls | Fields touched |
|---|---|---|---|
| Claude (claude-sonnet-5) | LEI conflicts 21 against the GLEIF record, Confirm conflicts 176 | 776 | LEI ruled 21; conflicts ruled 159, blanked 17 |
| ChatGPT (gpt-4.1-mini, Batch) | Text windows from 102 issuer-published PDFs (universal registration documents, annual and half-year reports) | 102 | auditor 24, registrar 1, period end 96, going concern 102 |
| Gemini (gemini-flash-latest) | 12-month announcement sets for 418 issuers | 418 | 4 dated meeting / record-date events |
| Perplexity (Agent API, low) | Company pages for all 590 issuers | 590 | 492 verified pages; page-title aliases 55 |
| Grok (grok-4.6, Responses + web/x search) | Live layer, 40 issuers asked (168-hour window) | 42 | halts 0; silent-issuer items 16 |
| Mistral (mistral-small-latest) | Review only: 493 of 494 French-language targets reviewed | 494 | 474 confirmed, 11 disputed, 726 flags on the Review tab; no field written |
| Tavily | Rematch on legal name or sourced alias for 168 zero-event and ambiguous issuers | — | 103 events added; 544 collisions ruled through Claude |

Aliases: 191 issuers carry a sourced "Also known as" (GLEIF LEI record 155, issuer page title 55, release pages 9). States after the rebuild: ISIN confirmed 588 / sourced 124; LEI sourced 688 / filled 21 / conflict 3; SIREN sourced 583; auditor filled 24; registrar sourced 108 / confirmed 2 / filled 1; newswire confirmed 160 / filled 158 / sourced 64. Auditor Paris 0 → 21, Growth 0 → 2, Access 0 → 1; registrar Paris 73 → 74, Growth 33, Access 5 → 4 (one blanked by a Claude conflict ruling, reason in Gaps). Disclosure: 9,999 events (107 new from the passes), 17 confirmed by a second source family.

`run_refresh.ps1` is the weekly shape (node lock and global BUILD lock respected; no scheduled task registered). `rebuild_disclosure.py` writes the Review tab and the 17-column Events sheet (Language included).
