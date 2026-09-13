# Google — Gemini Enterprise / A2A agent listing — submission pack (Allooloo)
Prepared September 13, 2026 · CEO submits · every URL below answered 200 on September 13, 2026
Practice key: [1] one description of record · [2] every URL answers · [3] auth stated plainly · [4] demo with nothing set up · [5] assets to spec · [6] version tied to the card · [7] no "signed", acronyms spelled out

## Agent identity
- Agent name: Capital Markets Knowledge Graph — Allooloo [1]
- Short tagline: KYP Agentic Trading with the Capital Markets Knowledge Graph [1]
- Provider organization: Allooloo Technologies Corp. [5]
- Provider URL: https://allooloo.io [2]
- Documentation URL: https://capitalmarketsknowledgegraph.ai/ [2]
- Agent card URL (A2A): https://capitalmarketsknowledgegraph.ai/.well-known/agent-card.json [2]
- A2A endpoint: https://mcp.capitalmarketsknowledgegraph.ai/mcp (JSON-RPC) [2]
- A2A protocol version: 0.3.0 (as published in the card)
- Category: Finance · Compliance · Reference data
- Version: registry card io.github.allooloo/cm-kg 0.12.0 [6]

## Description (paste verbatim) [1][7]
What: KYP Agentic Trading with the Capital Markets Knowledge Graph — one public-record file per listed company across eleven national markets, identity through disclosure trail, each field carrying its source and the date it was read, served from the issuer's own jurisdiction over the Model Context Protocol (MCP) and the Agent-to-Agent protocol (A2A).

Why: So an agent acting for a licensed capital markets participant with a Know Your Product (KYP) obligation hands back a fact that can be defended. The KYP model runs on this record. No prices, no quotes, no licensed data.

Markets: Canada, United States, United Kingdom, France, Netherlands, Switzerland, Germany, Australia, Singapore, Japan, South Korea. Hong Kong is a beacon.

## Skills (from the agent card) [1]
| Skill id | Name | Description |
|---|---|---|
| resolve_issuer | Resolve an issuer | Find a listed company by ticker (with exchange prefix or suffix), International Securities Identification Number (ISIN), Legal Entity Identifier (LEI), legal name or sourced alias; returns the record summary, node and version |
| get_record | Read the record | Return the full Capital Markets Record for an issuer, every field with its source URL and read date |
| list_events_since | Disclosure trail | Dated, sourced disclosure events for an issuer since a date |
| list_aliases | Aliases | Sourced trade and former names for an issuer |
| list_nodes | Nodes | The twelve market nodes, which are live, their regional doors and agent cards |

Input modes: application/json, text/plain. Output modes: application/json. Streaming: no. Push notifications: no.

## Authentication [3]
- Public door: none — read-only, no key, no account. securitySchemes in the card is empty by design.
- Licensed routes: OAuth 2.0 via Agentic Registries. Authorization server metadata: https://agentic-registries.ai/.well-known/oauth-authorization-server. Agent guidance: https://agentic-registries.ai/auth.md. [2]

## Demo — nothing to set up [4]
1. Fetch the agent card: https://capitalmarketsknowledgegraph.ai/.well-known/agent-card.json
2. Send an A2A task to resolve_issuer with identifier "LSE:BARC" → Barclays PLC, node uk-cm-kg.
3. get_record for that issuer → the full file, source URL and read date on every field.
4. list_events_since with date 2026-06-01 → dated, sourced trail.
5. list_nodes → eleven live nodes and the Hong Kong beacon.
Under two minutes. No prices or quotes at any step — by design.

## Data residency and provenance
- Records stored and served in the issuer's own jurisdiction across eleven Azure regions: Canada Central (Toronto), East US (Virginia), UK South (London), France Central (Paris), West Europe (Amsterdam), Switzerland North (Zurich), Germany West Central (Frankfurt), Australia East (Sydney), Southeast Asia (Singapore), Japan East (Tokyo), Korea Central (Seoul).
- Every field carries source URL and read date; 100 percent provenance coverage at render.
- Operator and provenance headers on every response (X-CMR-Node, X-CMR-As-Of, X-CMR-Version, X-CMR-Source: public-record, X-CMR-Operator, X-CMR-Contact).

## Policies and support [2]
- Privacy: https://allooloo.io/privacy
- Terms of use: https://allooloo.io/terms
- Security / responsible disclosure: https://allooloo.io/security
- Status: https://allooloo.io/status
- Support: contact form at https://allooloo.io/#contact
- Contact email: mk@allooloo.ai [5]

## Commercial [3]
- Public read: free, no registration.
- Per-record machine payment: x402 on Base — documentation and live endpoint at https://agentic-x402.ai/ (A2A payment extension to follow the same terms).
- Firm-wide use: signed licence — Dealer MCP access, Issuer record, Knowledge Graph API, Node operator. Licence only, no services.

## Assets [5]
- Logo (square, 400×400): C:\ALLOOLOO\SITE\avatar-400.png
- Logo (vector): C:\ALLOOLOO\SITE\allooloo-logo.svg (dark variant allooloo-logo-dark.svg)
- Icon (512): https://capitalmarketsknowledgegraph.ai/icon-512.png
- Company name for the form, exactly: Allooloo Technologies Corp.
- Location: Vancouver & Toronto, Canada

## Notes for the submitter
- The apex agent card reports version 0.11.0 while the registry card is 0.12.0; use 0.12.0 on the form and have CC bump the card. [6]
- Do not write "signed" anywhere on the form; records are confirmed against the public filing. [7]
