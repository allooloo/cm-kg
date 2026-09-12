# kr-fill-confirm — South Korea Fill pass (ORDER-017 re-cut)

Built from the Japan fill rail with the Korean pockets. Pond-native: `raw\` is a junction to the open drop `CM-KG\POND\kr-cm-kg\fill-confirm\<date>\`; rebuilds write versioned copies to `POND\kr-cm-kg\assembled\<date>\` beside the Width 0 and Width 1 outputs and refresh the mirrors `CM-KG\ISSUERS\kr-issuers.xlsx`, `CM-KG\DISCLOSURE\kr-disclosure.xlsx` (+ `events\kr-events.jsonl`). Korean as primary; machine-translated English never a source; values copied verbatim.

## Reading order (ORDER-017 re-cut)
1. `dart_auditor.py` — the auditor from DART's structured endpoint 회계감사인의 명칭 및 감사의견 (annual report, last two business years): audit firm, opinion, period end, emphasis of matter / going concern, receipt number. Sourced from the regulator's API, not a lab read.
2. `dart_docs.py` — the 사업보고서 main document through the DART document API (a zip of XML; ~30 s a document, three shards of four threads) reduced to Korean text windows: 명의개서대리인, 회계감사인, 사업연도, 계속기업.
3. `gemini_reads.py` — **Gemini reads the Korean windows as primary**: 명의개서대리인 (transfer agent / register administrator), period end, going-concern language; auditor only as a fallback to the DART fact. Label "read by Gemini (ko) — DART 사업보고서 text windows".
4. `perplexity_pages.py` — the search layer, Perplexity Agent API preset **fast**: the issuer's own page, verified by fetch; the page title becomes a sourced alias.
5. `grok_live.py` — second engine, the live layer (40 issuers, 168-hour window) written into the Width 1 drop.
6. `mistral_reads.py` — **review only** in Korean: confirms or disputes each Gemini value, reviews the located pages, flags to the Review tab. Never writes a field.
7. `rebuild_issuers.py` (from the Width 0 base workbook) → `rebuild_disclosure.py` (Grok events merged, Review tab) → `spend.py`.

## First run — 2026-09-12 (2,802 companies; assembled drops 2026-09-12-14 issuers, -15 disclosure)
| Engine | Duty | Calls | Result |
|---|---|---|---|
| DART auditor endpoint | 2,742 issuers | 2,742 | auditor 2,724 (2,604 unqualified opinions, 48 disclaimers), period end 2,724, emphasis / going concern 334 — State sourced |
| DART document API | 사업보고서 main documents | 2,683 | Korean windows for 2,683 |
| Gemini (gemini-flash-latest) | Korean windows, primary | 2,683 | 명의개서대리인 2,057, going-concern reading 2,392; auditor fallback 3 |
| Perplexity (agent, fast) | company pages | 2,759 | 1,354 verified pages; 354 title aliases (first pass lost 1,619 results to a helper crash; rerun kept beside as `perplexity_pages_run1.jsonl`) |
| Grok (grok-4.6) | live layer, 40 issuers | 42 | 2 halt items, 1 silent-issuer item |
| Mistral (mistral-small-latest) | review only | 3,992 | 2,682 document reviews (registrar disputed 362; the going-concern check disputes most reports on the audit boilerplate) and 1,345 page reviews (1,277 confirm, 36 dispute); 3,990 flags on the Review tab |

States after the rebuild: auditor sourced 2,724 / filled 3; share registrar filled 2,057 (362 marked disputed on review); LEI sourced 299; aliases 356. Auditor KOSPI 0 → 840, KOSDAQ 0 → 1,775, KONEX 0 → 112; registrar KOSPI 0 → 686, KOSDAQ 0 → 1,312, KONEX 0 → 59. Disclosure: 143,297 events (3 Grok). Top registrars as read: 한국예탁결제원 620, 국민은행 증권대행부 325 (+121 as KB국민은행), 하나은행 증권대행부 159.

HITL: the 362 registrar disputes on the Review tab; ISIN blank on every line (not derived by rule); DART daily cap 20,000 calls (this pass used about 8,200 with the Width 1 sweep).
