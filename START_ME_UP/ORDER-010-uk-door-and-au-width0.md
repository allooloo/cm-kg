# ORDER-010 — Light the UK node door, then Australia Width 0
Date: Sept 11 2026 · Fly by wire.

## Part A — UK node on the doors
1. Extend the door loader rail (CM-KG\RAILS\ca-door) into a node-generic loader: load uk-issuers.xlsx + uk-events.jsonl
   as CMRs under node uk-cm-kg. Deploy mcp.uk-cm-kg.ai from the same codebase (custom domain on the uk-cm-kg.ai zone).
2. The global door's list_nodes now reports uk-cm-kg live with its record count; resolve_issuer routes GB ISINs and
   LSE/AIM/Aquis tickers to the UK node. uk-cm-kg.org and .ai pages flip to live by themselves.
3. Prove with a real MCP client call: list_nodes, resolve_issuer for one Main Market, one AIM, one Aquis name.
4. If the Workers static-assets file cap is hit with two nodes, STOP and report the cap and the count — do not split
   the deploy or invent a workaround; that is the D1 token decision, which is the CEO's.

## Part B — Australia Width 0
Same as ORDER-007 pointed at Australia: ASX (all listed entities from the ASX public list) plus NSX and Cboe Australia
where public. Enrich: name · ASX code · ISIN · LEI · ACN/ABN (ASIC register — public search; note if the API needs a key,
HITL) · registered office · state · GICS sector (ASX list) · auditor (annual report — source link only at Width 0) ·
share registry (Computershare / Link-MUFG / Boardroom / Automic — from the issuer page) · newswire of habit
(ASX announcements platform is the primary; then wires) · ASX announcements link · ASIC link.
Output CM-KG\ISSUERS\au-issuers.xlsx; rails CM-KG\RAILS\au-width0\. Same rules, same report shape, HITL list.

## Don't
No test harness. No prices. No login fetches. No reference to any other company's estate.
