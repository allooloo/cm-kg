# ORDER-014 — Singapore to the door (Width 1 → Fill + Confirm → door)
Date: Sept 11 2026 · Node: sg-cm-kg · Fly by wire · pond-native · sg lock held throughout, released at Part C report.

## Part A — Width 1: Disclosure (shape of ORDER-011)
Corporates in sg-issuers.xlsx (541). 12-month backfill, then weekly.
Sources: SGXNet is 401 to machines (HITL stands) — so: the issuer's newswire of habit + the other wires (Tavily);
ACRA monthly files for register events (name/status changes); Business Times / Edge Singapore are NOT sources (paywalled).
Where an issuer's own IR site carries an announcements page, that page is a source (fetch, no login).
Types: results, AGM/EGM, dividend, halt/suspension, substantial shareholder, director change, name change.
Output sg-disclosure.xlsx + sg-events.jsonl; rails RAILS\sg-width1\. Expect thin coverage; report it as thin, not padded.

## Part B — Fill + Confirm (shape of ORDER-012)
Aliases sourced (ACRA former names, GLEIF other names, wire pages). Claude adjudicates conflicts. ChatGPT batch reads
annual-report PDFs where a link exists (auditor, registrar, period end). Gemini on 12-month sets. Perplexity (Agent API,
preset low) recovers pages. Grok live. Mistral: Chinese-language releases if any (report count). Confirm pass; State on
every field. Rails RAILS\sg-fill-confirm\.

## Part C — Door
Load into the node-generic loader; deploy mcp.sg-cm-kg.ai; global door lists sg-cm-kg live; prove with a real MCP call
(one Mainboard, one Catalist, one REIT). FILE CAP: report total asset files with four nodes against 20,000. If the next
node would breach, say so — the D1 token is the CEO's. Stage registry v0.4.0; do not publish.
Report per part: counts, fill, Gaps, sources answered/refused, HITL, spend line.
