# ORDER-013 — Light the Australia node door, then Singapore Width 0
Date: Sept 11 2026 · Fly by wire · pond-native.

## Part A — Australia node on the doors
1. Load au-issuers.xlsx + au-events.jsonl (latest versioned outputs from the pond) as CMRs under node au-cm-kg via the
   node-generic loader. Deploy mcp.au-cm-kg.ai from the same codebase (custom domain on the au-cm-kg.ai zone).
2. Global door: list_nodes reports au-cm-kg live with its count; resolve_issuer routes AU ISINs and ASX/NSX codes to the
   Australia node. au-cm-kg.org and .ai flip to live by themselves.
3. Prove with a real MCP client call: list_nodes, resolve_issuer for one ASX 200 name, one small-cap, one NSX name.
4. File-cap check: report the total asset file count against the 20,000 cap with three nodes. If the fourth node would
   breach it, say so — STOP is not needed yet, but the D1 token decision is the CEO's and must be on the report.
5. Registry: stage v0.3.0 (three nodes) in server.json; do NOT publish — CEO's go.

## Part B — Singapore Width 0
Same as ORDER-007 pointed at Singapore: SGX Mainboard and Catalist (SGX public company list / screener). Enrich: name ·
SGX code · ISIN · LEI · ACRA UEN (ACRA public search; note if the API needs a key — HITL) · registered office ·
incorporation jurisdiction (Singapore / foreign) · sector (SGX) · auditor (annual report — source link only) ·
share registrar (Boardroom / Tricor / M&C / KCK — from the issuer page) · newswire of habit (SGXNet is primary; then wires) ·
SGXNet announcements link · ACRA link. Output CM-KG\ISSUERS\sg-issuers.xlsx; rails CM-KG\RAILS\sg-width0\.
Same rules, same report shape, HITL list, spend line. MAS product due-diligence is the duty name on the node page.

## Don't
No test harness. No prices. No login fetches. No reference to any other company's estate.
