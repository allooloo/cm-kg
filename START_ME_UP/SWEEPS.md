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
