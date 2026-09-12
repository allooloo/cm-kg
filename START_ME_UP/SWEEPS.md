# SWEEPS — standing cadence for every node
Allooloo · opened Sept 10 2026 · read every session alongside MISSION.md

## Rule
Every node runs the same sweep set on the same clock once it has passed Width 1. The sweep is a standing duty,
not an order: it runs whether or not a session is open. Orders change what a sweep does; they never start or stop it.
Passes always run in order: Harvest → Fill → Confirm. Nothing lands unconfirmed on the wire without its State.

## Cadence (per node)
| Clock | Sweep | Width | Engines | Output |
|---|---|---|---|---|
| Daily, 48-hour window | Live layer: wires, halts, resumes, bulletins, corporate actions | 1 | Tavily · Grok (live) · deterministic bulletins/APIs | events jsonl, idempotent on (ticker, type, date, URL) |
| Daily, on new rows | Fill + Confirm on anything the daily sweep added | 2–3 | Claude · ChatGPT · Gemini · Mistral (fr/de/nl) · Perplexity | State on every new field |
| Weekly | Edges rebuild: insiders across boards, shared auditors/transfer agents, dual listings, sector peers | 2 | deterministic + Claude adjudication | graph edges refreshed |
| Monthly | Full identity re-harvest: exchange lists, GLEIF, registry links, aliases; new listings and delistings in, tiers and sectors refreshed | 0 | Tavily · Perplexity · GLEIF · exchange lists | issuers workbook rebuilt, CMR versions bumped |
| Monthly | Funds and ETFs disclosure (Width 1-F) once ordered | 1-F | same as Width 1 | fund events |
| On each new filing | Lab reads: extracted facts per filing | 3 | ChatGPT (batch) · Gemini · Mistral · Claude adjudicates | read fields, labelled |

## Current setting — Canada (set Sept 10 2026)
Weekly: live layer + Fill + Confirm over a 7-day window — Task Scheduler "Allooloo CM-KG Canada weekly", Friday 18:00 build-machine time (Central Standard Time (Mexico), no daylight shift) = 19:00 EST / 20:00 EDT Toronto, after TSX close.
Monthly: full identity re-harvest, jurisdiction from the GLEIF legal-jurisdiction field, unclassified fund rows out of corporate scope — Task Scheduler "Allooloo CM-KG Canada monthly", 15th 18:00 build-machine time, after the TMX monthly listed-companies workbook is out.
Daily not switched on. Alias channels: GLEIF other names · wire company page · exchange profile · issuer website <title> (site from the exchange profile's website field).

## Current setting — United Kingdom (set Sept 11 2026)
Weekly: Width 1 refresh over a 7-day window (Investegate RNS, Companies House filings, wire search), then Fill + Confirm (Grok live layer 168 h, aliases, bodies, ChatGPT batch, Gemini, Mistral, confirm, rebuilds, spend), then the door reload and deploy — Task Scheduler "Allooloo CM-KG UK weekly", Friday 12:00 build-machine time (Central Standard Time (Mexico)) = 18:00 London in summer, after the LSE close. Rail: CM-KG\RAILS\uk-weekly.ps1.
Monthly identity re-harvest: CM-KG\RAILS\uk-width0\run_refresh.ps1, run on order until the first month turns (no Task Scheduler clock yet). Aquis: aquis.eu refuses plain clients, so the roster and the announcements feed are read in a browser session before a run (standing HITL).
Alias channels: Companies House previous names · GLEIF other names · Investegate page display name · LSE issuer profile display name · issuer news page title found by Perplexity.

## Current setting — Australia (set Sept 11 2026)
Weekly: Width 1 refresh over a 7-day window (ASX announcements search, ASIC bulk register, NSX news feed, wire search), then Fill + Confirm (Grok live layer 168 h, aliases, annual reports, ChatGPT batch, Gemini, Perplexity agent, Mistral, confirm, rebuilds, spend), then the door reload and deploy — Task Scheduler "Allooloo CM-KG AU weekly", Friday 02:00 build-machine time (Central Standard Time (Mexico)) = Friday 18:00 AEST, after the ASX close. Rail: CM-KG\RAILS\au-weekly.ps1; skips while POND\au-cm-kg\.lock exists.
Monthly identity re-harvest: CM-KG\RAILS\au-width0\run_refresh.ps1, run on order until the first month turns. TMX Australia: no machine-readable list (standing HITL).
Alias channels: ASIC previous names · GLEIF other names · ASX company record · issuer page <title> · wire release pages.

## Current setting — Singapore, Switzerland, Germany, France, Netherlands (set Sept 11–12 2026)
No scheduled task on any of these nodes (global BUILD lock). Each node has the weekly shape written and lock-guarded: `CM-KG\RAILS\<cc>-width1\run_refresh.ps1` (new pond drop, 7-day window, assemble) and `CM-KG\RAILS\<cc>-fill-confirm\run_refresh.ps1` (Fill + Confirm on the refreshed set, rebuilds, spend). Reading order on the European nodes: Perplexity (agent, low) → Grok → Mistral (review only). Singapore: English-language filings only, Mistral zero. Germany also carries the Eurex reference-data door (`CM-KG\RAILS\de-eurex`: rerun fetch + assemble into a new drop, then the door loader).

## Current setting — Japan, South Korea, Hong Kong (set Sept 12 2026)
No scheduled task (global BUILD lock). Japan weekly: `jp-width1\run_refresh.ps1` (EDINET daily lists, 7 days) then the Fill pass parts (`jp-fill-confirm`: document shards → Gemini loop → Perplexity fast → Grok → Mistral review → rebuilds → spend). Korea weekly: `kr-width1\run_refresh.ps1` (DART list per corp code, 7 days) then `kr-fill-confirm` (DART auditor endpoint → document shards → Gemini loop → Perplexity fast → Grok → Mistral review → rebuilds → spend); DART cap 20,000 calls a day. Hong Kong: Width 0 only by order (`hk-width0`, re-run into a new drop on order); no Width 1, no Fill, no door until a local partner. The GLEIF golden copy (`gleif-golden\download.py` + `extract.py`) refreshes once per build day and serves every local LEI join. United States: EDGAR blocks this address (HITL); the `us-width0` rails wait for a declared route.

## Global BUILD lock (CEO rule, Sept 11 2026)
No scheduled sweep runs on any node while any build order is in flight. The lock is the file CM-KG\POND\.build-lock (set at the start of a build chain, removed when the chain has reported and the CEO re-enables the sweeps); every sweep script and pond_open.py check it first and skip. It sits above the per-node lock (POND\<node>\.lock), which still guards a single node between orders. Why: on Sept 11 the Canada weekly fired at 18:00 in the middle of the 014–018 chain and shared the Tavily plan and the labs with the build; the UK weekly had already collided with a build earlier that day.
Sept 11 2026: every scheduled sweep (Canada weekly and monthly, United Kingdom weekly, Australia weekly) is DISABLED until the 014–018 chain reports; re-enabled on the CEO's word.

## Node clock
Every node sweeps in its own market's business day, in the market's time zone, after close. Twelve nodes = twelve clocks.
Never a global run at one hour.

## Where it runs
Today: CM-KG\RAILS\<node>-<width>\run_refresh.ps1 on the build machine, Windows Task Scheduler, one task per node per cadence.
Later: Azure Container Apps job in the Allooloo tenant, same scripts, same clock — its own order when the CEO calls it.

## Spend
Each sweep writes its lab spend per engine into CM-KG\SPEND\<node>-<yyyy-mm>.jsonl. Reported monthly. Never gates a run.

## Broken sources
Each node's README carries its known-broken list (registries that refuse machines). A sweep never retries a broken
source on a loop; a broken source is re-tested once per monthly sweep and its status re-recorded.

## What a sweep never does
No prices, quotes or market data. No fetch behind a login. No guessed aliases or inferred fields. No test rigs.
No reference to any other company's estate.
