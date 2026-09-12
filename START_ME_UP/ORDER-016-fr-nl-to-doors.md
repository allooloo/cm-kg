# ORDER-016 — France + Netherlands to the doors
Date: Sept 11 2026 · Nodes: fr-cm-kg, nl-cm-kg · Fly by wire · pond-native · locks held; released at Part C.
PRECONDITION as ORDER-015: file-cap check; STOP before Part C if breach; A and B still run.

## Part A — Width 0 (shape of ORDER-007), both nodes in parallel
- France: Euronext Paris issuer list (public, incl. Growth and Access). AMF BDIF (regulatory information database — public)
  for filer identity. INPI / Infogreffe for the company register (Infogreffe per-company pages are public; note key needs — HITL).
  GLEIF (FR ISINs mapped). Registrar (Uptevia/Euroclear France agents). Duty line: MiFID II product governance.
- Netherlands: Euronext Amsterdam list. AFM public registers (issuers, notifications — public). KVK register (paid API — HITL;
  public search pages only). GLEIF. Duty line: MiFID II product governance.

## Part B — Width 1 + Fill + Confirm
- France: AMF BDIF is the primary trail (regulated information, public); wires (Actusnews, GlobeNewswire FR); Mistral reads
  French natively — "read by Mistral (fr)".
- Netherlands: AFM notifications (substantial holdings, insider dealings — public registers) as the primary; issuer IR pages;
  wires; Mistral reads Dutch. ChatGPT batch on annual reports. Confirm; State everywhere.

## Part C — Doors
mcp.fr-cm-kg.ai and mcp.nl-cm-kg.ai; prove by MCP call (a CAC name, a Growth name; an AEX name, a small-cap).
Stage registry versions; do not publish. Report per part with HITL and spend line.
