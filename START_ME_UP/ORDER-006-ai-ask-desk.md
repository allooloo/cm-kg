# ORDER-006 — AI ASK, the desk
Date: Sept 10 2026 · Host: ask.allooloo.io · Folder: C:\ALLOOLOO\AI-ASK\ (repo allooloo/cm-kg, folder AI-ASK) · Fly by wire.

## What it is
The human front door onto the Capital Markets Knowledge Graph. A compliance officer or banker asks about a listed
company; the desk parses the identifier, opens the node through the MCP door, and answers from the record — field,
source, reader, state. Product name: AI ASK ("AI assistant ask" in copy). Reads through mcp.ca-cm-kg.ai and
mcp.capitalmarketsknowledgegraph.ai only; it holds no data of its own.

## How it answers (in this order — never skip to the model)
1. Parse the identifier first: ticker (SHOP, TSX:SHOP, SHOP.TO), ISIN, LEI, or a sourced alias via list_aliases.
   No identifier → answer only from list_nodes / facts (what the desk is, what nodes are live) or ask for one.
   Ambiguous across exchanges → show the matches, let the user pick. Never guess.
2. Field questions ("who is the transfer agent", "what's the ISIN", "auditor", "which newswire", "where is it
   incorporated") → answered deterministically from get_record. No model call. Answer = value + source link +
   read-by + state. Null field → say the field is blank on the record and why (the Gaps reason).
3. List questions ("halts in the last 12 months", "releases since June", "record dates") → list_events_since,
   rendered as dated rows with source links. No model call.
4. Prose questions (anything else about the issuer) → Claude (Messages API) with the door attached as an MCP
   connector, system instruction: answer only from tool results, cite the field or event used, never add a fact
   the record doesn't hold, say "not on the record" otherwise. Label the answer "read by Claude · from the record".
5. Every answer carries: node · as_of · version · read-by · state summary, and a copy link.
   Share links encode identifier + question; the desk re-answers on open (no answer store — KV is not available).

## Design (differentiated — not a clone of any other desk)
- Two panes. Left: question and answer. Right: the resolved issuer record — name, ticker, exchange, ISIN, LEI,
  sector, transfer agent, auditor, newswire, jurisdiction — filled the moment the identifier parses, before the answer.
- Identifier bar above the question showing what was parsed: `SHOP · TSX · CA82509L1076 · Canada node`. Editable.
- Twelve market chips under the identifier bar; Canada lit; the other eleven visible, dimmed, "not live".
- Answer pane fixed at ~60vh, internal scroll, pinned footer: `sourced · ca-cm-kg · read by <x> · copy link · open record`.
- Under the answer: "Also on record" — the other field and list questions already answerable for this issuer, as
  record-shaped chips (`SHOP · halts 12m`, `SHOP · auditor`). "Suggested" — the issuer's own sources from the record:
  newswire page, exchange profile, SEDAR+ profile (marked unverified), node record URL. Source name after the link.
- Onboard pill at top: "Onboard your agent to the Capital Markets Knowledge Graph" with the eight engine marks —
  links to the door's /llms.txt, nothing else.
- Notice line: "NOTICE: AI ASK is AI and can make mistakes. Public-record data only; no prices or market data."
- Sample chips: What is a Capital Markets Record? · SHOP · transfer agent · ATD · halts 12m · AUMB.V · auditor ·
  Is this issuer dual-listed? · Who runs Allooloo?
- Type IBM Plex Sans, palette paper / ink / signed green / grey / rule. No orange, no pill buttons, no numbered eyebrows,
  no per-section motion. One moment: the record pane fills once on parse.
- Favicon set from SITE\.

## Machine surface
/llms.txt, /facts.json, robots allowing agents, JSON-LD WebApplication. CMR headers v1 on every response.

## Deploy
Cloudflare Worker on the same account; custom domain ask.allooloo.io; HTTPS-only + HSTS; edge cache on static.
Claude key from AGENT KEYS\claude.txt in-process. Not linked from allooloo.io nav in this order — that link is a CEO go.

## Report
URL live · a screenshot of the two-pane desk with SHOP resolved · one deterministic answer, one list answer, one
Claude-read answer, each pasted with its footer line · Lighthouse mobile · what is broken. Nothing else.

## Don't
- No answer without an identifier-scoped record behind it. No model call for field or list questions.
- No prices or market data. No stubbed signature. No forward in front of the host. No test harness before the roll.
- No reference to any other company's estate, code, or canon.
