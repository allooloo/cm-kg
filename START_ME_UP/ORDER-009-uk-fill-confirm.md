# ORDER-009 — United Kingdom Fill + Confirm (passes 2 and 3)
Date: Sept 11 2026 · Node: uk-cm-kg · Fly by wire. Same shape as ORDER-004 (Canada), UK pockets.

## Pass 2 — Fill (named duties; label every touched field)
1. Aliases — sourced only: Companies House previous names (API), the issuer's own wire/RNS page name, GLEIF other names,
   the exchange profile name. Re-run the wire/RNS title match for zero-event issuers and Gaps "ambiguous" rows.
2. Claude — adjudicate ISIN and LEI conflicts (incl. the GLEIF mis-mapped LEIs flagged in Width 0), auditor strings,
   and the 393 unmatched Companies House rows: rule, or blank with reason. "adjudicated by Claude."
3. ChatGPT (Batches) — read each issuer's latest accounts PDF (link from Width 0) for: auditor name, period end,
   going-concern language, registrar if named. "read by ChatGPT (batch)." This is the auditor lift.
4. Gemini — long-context read of each issuer's 12-month RNS set for AGM/record dates and registrar where missed. "read by Gemini."
5. Perplexity — grounded recovery of stale/missing issuer news pages. "read by Perplexity (agent)."
6. Grok — wire into the weekly refresh as the live layer (RNS, suspensions, restorations). "read by Grok (live)."
7. Mistral — any non-English releases (few in the UK); otherwise report zero, no padding.

## Pass 3 — Confirm
Every filled/sourced identity field (ISIN, LEI, CH number, registrar, auditor, newswire, jurisdiction, alias) checked
against a second independent source → confirmed / conflict / blank with reason. Events: results and AGM rows confirmed
across RNS vs Companies House vs wire where two exist. "State" column on both workbooks.

## Output + Report
Rebuilt uk-issuers.xlsx and uk-disclosure.xlsx (+ jsonl) with read-by and State; Method tab listing all eight engines
with exact duty and count on the UK (zero if zero). Rails under CM-KG\RAILS\uk-fill-confirm\, joined to the weekly refresh.
Report: fields filled per engine · confirmed vs conflict vs blank · auditor fill before/after · large caps recovered by
alias · lab spend per engine · HITL list · what is broken.

## Don't
No guessed aliases. No login fetches. No prices. No reference to any other company's estate.
