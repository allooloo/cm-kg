# ORDER-012 — Australia Fill + Confirm (passes 2 and 3)
Date: Sept 11 2026 · Node: au-cm-kg · Fly by wire · pond-native. Same shape as ORDER-009 (UK), Australian pockets.

## Pass 2 — Fill (named duties; label every touched field)
1. Aliases — sourced only: ASIC former names (bulk file), the issuer's ASX profile name, GLEIF other names, wire page names.
   Re-run the announcement/wire title match for zero-event issuers and Gaps "ambiguous" rows.
2. Claude — adjudicate ISIN/LEI conflicts, GLEIF mis-maps, ACN/ABN mismatches between ASX and ASIC, auditor strings:
   rule, or blank with reason. "adjudicated by Claude."
3. ChatGPT (Batches) — read each issuer's latest annual report PDF (link from Width 0) for auditor, share registry,
   period end, going-concern language; and the Appendix 4E/4D releases for period end and statement date. "read by ChatGPT (batch)."
4. Gemini — long-context read of each issuer's 12-month announcement set for AGM/record dates and registry where missed. "read by Gemini."
5. Perplexity (Agent API, preset low) — grounded recovery of stale/missing issuer pages. "read by Perplexity (agent · low)."
6. Grok — wired into the weekly as the live layer (halts, suspensions, reinstatements). "read by Grok (live)."
7. Mistral — non-English releases (expect zero; report zero, no padding).

## Pass 3 — Confirm
Every filled/sourced identity field (ISIN, LEI, ACN, ABN, share registry, auditor, newswire, state, alias) against a second
independent source → confirmed / conflict / blank with reason. Events: results and AGM rows confirmed across ASX vs annual
report vs wire where two exist. "State" column on both workbooks.

## Output + Report
Rebuilt au-issuers.xlsx and au-disclosure.xlsx (+ jsonl) with read-by and State, versioned in the pond; Method tab with all
eight engines and exact counts (zero if zero). Rails under CM-KG\RAILS\au-fill-confirm\, joined to the weekly refresh.
Report: fields filled per engine · confirmed vs conflict vs blank · auditor and registry fill before/after · large caps
recovered by alias · HITL list · what is broken · spend line.

## Don't
No guessed aliases. No login fetches. No prices. No reference to any other company's estate.
