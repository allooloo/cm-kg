# sg-fill-confirm — Singapore passes 2 (Fill) and 3 (Confirm), ORDER-014 Part B

Built from the Australia rail (`au-fill-confirm`) with the Singapore pockets: ACRA (UEN) instead of ASIC, SGXNet announcement pages on links.sgx.com instead of the ASX viewer, Singapore registrars and audit firms in the closed lists. Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\sg-cm-kg\fill-confirm\<date>\`; rebuilds write versioned copies to `POND\sg-cm-kg\assembled\<date>\` and mirror to `CM-KG\ISSUERS\sg-issuers.xlsx`, `CM-KG\DISCLOSURE\sg-disclosure.xlsx` (+ `events\sg-events.jsonl`).

## Language rule (CEO, 2026-09-11)
English-language filings only on this node. Announcements and reports whose title carries Chinese characters are skipped at Width 1 assembly, never read, never counted; `mistral_reads.py` has no targets by rule and reports zero. The Method tabs say so.

## First run — 2026-09-11 (563 corporates; assembled drops 2026-09-11-7 issuers-side inputs, -8 disclosure)
| Engine | Duty | Calls | Fields touched |
|---|---|---|---|
| Claude (claude-sonnet-5) | LEI conflicts 4, UEN gaps 87 against ACRA candidates, Confirm conflicts | 156 | LEI ruled 4; UEN ruled 7, blank with reason 80; conflicts ruled 34, blanked 26 |
| ChatGPT (gpt-4.1-mini, Batch) | Text windows from 755 SGXNet PDFs (annual reports 174, results announcements 581) found via the Width 1 SGXNet pages | 755 | auditor 109, registrar 58, period end 367, going concern 390 |
| Gemini (gemini-flash-latest) | 12-month announcement sets for 473 issuers | 473 | registrar 39; 55 dated meeting / record-date events |
| Perplexity (Agent API, low) | Company pages for 400 issuers (no website column at Width 0) | 400 | page-title aliases 35 |
| Grok (grok-4.6) | Live layer (halts, silent issuers); ran past the rebuilds, events merge at the next rebuild | — | — |
| Mistral | zero by rule | 0 | — |

States: ISIN confirmed 346 / sourced 293; LEI confirmed 128 / sourced 28 / filled 4 / conflict 1; UEN sourced 551 / filled 7; auditor filled 93 / confirmed 16; registrar confirmed 70 / filled 99 / sourced 128; newswire confirmed 477. Auditor Mainboard 0 → 67, Catalist 0 → 42; registrar Mainboard 144 → 202, Catalist 64 → 95. Disclosure: 3,510 events, 59 new from the passes, 21 confirmed.

`run_build.ps1` / `run_build2.ps1` are the build-day chains; `run_refresh.ps1` is the weekly (called by `sg-weekly.ps1`). `annual_reports.py` supports `SHARD=i/n` helper shards.
