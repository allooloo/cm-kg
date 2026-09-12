# ORDER-015 — Switzerland + Germany to the doors (Mistral's seat)
Date: Sept 11 2026 · Nodes: ch-cm-kg, de-cm-kg · Fly by wire · pond-native · both locks held; released at Part C.
PRECONDITION: if ORDER-014 Part C reported the file cap would breach, STOP before Part C and report; A and B still run.

## Part A — Width 0 (shape of ORDER-007), both nodes in parallel
- Switzerland: SIX Swiss Exchange issuer list (public), BX Swiss. Zefix (federal commercial register) has a FREE public
  API — UID, legal seat, canton, status. GLEIF. Registrar (Computershare/areg/ShareCommService from issuer pages). Duty line: FinSA.
- Germany: Deutsche Börse / Xetra listed-companies list (public), plus Regulated Market and Scale segments.
  Handelsregister (public search; note if machine access needs a key — HITL). Bundesanzeiger is scrape-hostile — link only.
  GLEIF (DE ISINs are well mapped). Duty line: MiFID II product governance.
Output ch-issuers.xlsx, de-issuers.xlsx; rails per node.

## Part B — Width 1 + Fill + Confirm (shape of ORDER-011/012)
- Switzerland: SIX regulatory announcements (ad hoc, public RSS/list) as the primary; wires; Zefix register events.
- Germany: EQS / DGAP ad-hoc and corporate news feeds (public, per issuer) as the primary; wires; Handelsregister events
  where public. Mistral reads German and French releases natively — label "read by Mistral (de/fr)"; report its count,
  it should be large here. ChatGPT batch on annual-report PDFs for auditor/registrar. Confirm; State everywhere.
Output ch-/de-disclosure.xlsx + jsonl; rails per node.

## Part C — Doors
mcp.ch-cm-kg.ai and mcp.de-cm-kg.ai from the node-generic loader; prove by MCP call (SIX blue chip, a DAX name, a Scale name).
Stage registry v0.5.0/v0.6.0; do not publish. Report per part with HITL and spend line.
