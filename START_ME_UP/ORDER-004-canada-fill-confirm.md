# ORDER-004 — Canada Fill + Confirm (passes 2 and 3)
Date: Sept 10 2026 · Node: ca-cm-kg · Fly by wire.

## What it is
The second and third passes on Canada. Pass 2 (Fill) puts the labs on the pockets the harvest left: aliases,
conflicts, unrecognised strings, missed dates, French. Pass 3 (Confirm) checks every filled field against a
second independent source. Output: every field carries a state — sourced · filled · confirmed — and the
Method tab lists all eight engines with what each did on Canada.

## Inputs
CM-KG\ISSUERS\ca-issuers.xlsx · CM-KG\DISCLOSURE\ca-disclosure.xlsx · ca-events.jsonl · the Gaps tabs of both.

## Pass 2 — Fill (named duties; label every touched field with the engine)
1. Aliases — new column "Also known as" on the issuer record. Sourced only: the name on the issuer's own wire
   company page (Cision / CNW / PRN / Newsfile), GLEIF "other entity names," the exchange profile name. Never a guess.
   Then re-run the wire title match for the 229 zero-event issuers and the 93 "ambiguous match" Gaps rows using
   legal name OR alias. Read-by: the source; adjudication of any remaining conflict: "adjudicated by Claude."
2. Claude — adjudicate the 61 conflicting ISINs and the 53 unrecognised auditor strings from Width 0: read the
   cited sources, rule, or leave blank with a one-line reason in Gaps. "adjudicated by Claude."
3. ChatGPT (Responses API, Batches) — structured extraction over the 2,182 financial_statement releases:
   period end, statement date, auditor named in the release, going-concern language present (yes/no).
   One batch. New columns on Events. "read by ChatGPT (batch)."
4. Gemini — long-context read of each issuer's full 12-month release set for issuers missing AGM/record dates
   (Events has 451; corporate issuers number 2,851). Fill agm_record_date where a release states it. "read by Gemini."
5. Mistral — French-language releases (Québec issuers, French wires): extract the same fields as 3 and 4 from the
   French text. "read by Mistral (fr)."
6. Grok — wire into run_refresh.ps1 as the 48-hour live layer: newswire, halt, resume signal via the Agent Tools
   endpoint, deduped on the existing key. "read by Grok (live)." Runs from tomorrow's refresh onward.
7. Perplexity — grounded cold read on the 79 stale/missing wire company pages: find the issuer's current release
   page. "read by Perplexity (agent)."

## Pass 3 — Confirm
1. For every field that is filled or sourced on the issuer record (ISIN, LEI, transfer agent, auditor, newswire,
   jurisdiction, alias), find one second, independent source. Agree → state = confirmed, with both sources cited.
   Disagree → state = conflict, to Claude for adjudication, else blank with reason.
2. For Events: confirm financial_statement and agm_record_date rows against a second source where one exists
   (exchange bulletin vs wire, or two wires). Same states.
3. New column "State" on both workbooks: sourced · filled · confirmed · conflict.

## Output
- Rebuilt ca-issuers.xlsx and ca-disclosure.xlsx (+ jsonl) with read-by and State on every enriched cell.
- Method tab on each: all eight engines listed — Claude, ChatGPT, Gemini, Perplexity, Grok, Mistral, Tavily,
  Cloudflare — with the exact duty performed on Canada and the count of fields touched. If an engine touched
  nothing, say so; do not pad.
- Rails under CM-KG\RAILS\ca-fill-confirm\ with README. Passes 2 and 3 join the daily refresh.

## Report
Fields filled per engine · fields confirmed vs conflict vs blank · large caps recovered by alias (name the 20 biggest)
· lab spend per engine · what is broken. Nothing else.

## Don't
- No guessed aliases, no fuzzy anything. Sourced or blank.
- No SEDAR+ / SEDI / CIRO / CDS fetch attempts.
- No prices or market data.
- No reference to any other company's estate, code, or canon.
