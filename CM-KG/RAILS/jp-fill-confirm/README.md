# jp-fill-confirm — Japan Fill pass (ORDER-017 re-cut)

Built from the Swiss fill rail with the Japanese pockets. Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\jp-cm-kg\fill-confirm\<date>\`; rebuilds write versioned copies to `POND\jp-cm-kg\assembled\<date>\` beside the Width 0 and Width 1 outputs and refresh the mirrors `CM-KG\ISSUERS\jp-issuers.xlsx`, `CM-KG\DISCLOSURE\jp-disclosure.xlsx` (+ `events\jp-events.jsonl`). Japanese as primary; machine-translated English never a source; values copied verbatim.

## Reading order (ORDER-017 re-cut)
1. `edinet_xbrl.py` — the latest 有価証券報告書 per issuer as EDINET's XBRL-to-CSV download (type=5): the audit firm as the tagged fact `jpcrp_cor:AuditFirm1…` (sourced, not a lab read), the fiscal year end (`jpdei_cor:CurrentFiscalYearEndDateDEI`), the going-concern note when a GoingConcern-named text block exists, and the 株式事務の概要 text block as the registrar window.
2. `edinet_docs.py` — the same report as PDF reduced to Japanese text windows (auditor, 株主名簿管理人, period, 継続企業の前提); pypdf is slow on Japanese PDFs, so it runs as six shard processes (`run_docs_shard<i>.ps1`).
3. `gemini_reads.py` — **Gemini reads the Japanese windows as primary**: 株主名簿管理人 (share-register administrator), period end, going-concern language; auditor only as a fallback to the XBRL fact. Label "read by Gemini (ja) — EDINET 有価証券報告書 text windows".
4. `perplexity_pages.py` — the search layer, Perplexity Agent API preset **fast**: the issuer's own page, verified by fetch; the page title becomes a sourced alias.
5. `grok_live.py` — second engine, the live layer (halts, silent issuers; 40 issuers, 168-hour window) written into the Width 1 drop.
6. `mistral_reads.py` — **review only**: re-reads the same windows in Japanese and confirms or disputes each Gemini value; reviews the pages Perplexity located; flags to the Review tab. Never writes a field.
7. `rebuild_issuers.py` (from the Width 0 base workbook, `BASE_XLSX`) → `rebuild_disclosure.py` (Grok events merged, Review tab) → `spend.py`. Chains: `run_docs_shard*.ps1`, `run_gemini_loop.ps1`, `run_build_a.ps1`, `run_final*.ps1`.

## First run — 2026-09-12 (3,962 carried lines; assembled drops 2026-09-12-14 issuers, -15 disclosure)
| Engine | Duty | Calls | Result |
|---|---|---|---|
| EDINET XBRL facts | 3,684 reports | 3,684 | auditor 3,678 (18 joint audits), fiscal year end 3,680, going-concern notes 344 — State sourced |
| EDINET PDF windows | 3,684 reports, six shards | 3,684 | windows for 3,683 |
| Gemini (gemini-flash-latest) | Japanese windows, primary | 3,683 | share-register administrator 3,639, going-concern reading 3,339; auditor fallback 5 |
| Perplexity (agent, fast) | company pages | 3,943 | 3,128 verified pages; 258 title aliases (the first pass lost 3,050 results to a helper crash after the calls; rerun kept beside as `perplexity_pages_run1.jsonl`) |
| Grok (grok-4.6) | live layer, 40 issuers | 43 | 8 halt / suspension items, 0 silent-issuer items |
| Mistral (mistral-small-latest) | review only | 6,794 | 3,683 document reviews (registrar disputed 11, auditor 1; the going-concern check disputes almost every report because the audit-report boilerplate carries the phrase) and 3,127 page reviews (3,094 confirm, 18 dispute); 8,532 flags on the Review tab |

States after the rebuild: auditor sourced 3,678 / filled 5; share registrar filled 3,639; ISIN sourced 537; LEI sourced 891; aliases 258. Auditor Prime 0 → 1,540, Standard 0 → 1,552, Growth 0 → 589; registrar Prime 0 → 1,526, Standard 0 → 1,532, Growth 0 → 579. Disclosure: 39,274 events (8 Grok). Top audit firms as tagged: EY新日本 679, あずさ 520, トーマツ 426, 太陽 327. Top registrars as read: 三井住友信託銀行 1,415, 三菱ＵＦＪ信託銀行 1,148 (+353 in another spelling), みずほ信託銀行 551.

HITL: Mistral disputes on the Review tab (registrar 11); PRO Market lines (187) have no EDINET filer; no ISIN for issuers without an LEI; TDnet not read.
