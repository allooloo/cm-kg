# hk-fill-confirm — Hong Kong passes 2 (Fill) and 3 (Confirm), ORDER-035 (2026-10-22)

Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\hk-cm-kg\fill-confirm\<date>\`. The rebuild writes a versioned `hk-issuers.xlsx` to `POND\hk-cm-kg\assembled\<date>\` and mirrors it to `CM-KG\ISSUERS\hk-issuers.xlsx` (the previous mirror beside as `.pre-<stamp>`). English-language filings only. Reading order of record: Perplexity → Grok second (the cost driver) → Mistral review only. Tavily is used for page extraction; this month's ceiling is 400,000 (the pay-as-you-go limit, read live).

| Pass | Worker | What it reads | State it writes |
|---|---|---|---|
| 2.1 | annual_reports.py | The newest English annual report Width 1 found on HKEXnews, read once by Tavily page extraction. The auditor and the Hong Kong share registrar are taken from the passages that name them (closed lists of Hong Kong audit firms and registrars, regex fallback). A second pass covers the combined "Annual Report / ESG" heading. | sourced (from the filing) |
| 2.2 | perplexity_fill.py | Perplexity Agent API (preset low): auditor, Hong Kong share registrar and HQ city, each with the page it was read from. The page must be one of the search_results; the prose is never a source. | filled |
| 2.3 | grok_fill.py | grok-4.6 with web search, only on lines still missing the auditor or the registrar. A value is kept only with a cited page. | filled |
| 3 | confirm.py | Filing and lab name the same firm → confirmed (two sources). Filing only → sourced. Lab only → filled. They disagree → conflict, both kept, the filing's value stands. Mistral reviews the conflicts only; it writes a flag, never a field. | confirmed · sourced · filled · conflict |
| — | rebuild_issuers.py | Writes the workbook (Width 0 columns carried as read) plus the Annual report, Newswire of habit (HKEXnews, with the count) and the second-source columns. The Gaps line is rewritten per line. | — |

`financialfilings.com` is never a source (terms). The run's counts and spend are in the ORDER-035 report (`START_ME_UP\ORDER-035-REPORT-2026-10-22.md`).
