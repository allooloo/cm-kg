# Anthropic connector directory — submission pack (Allooloo)
Prepared September 13, 2026 · CEO submits · every URL below answered 200 on September 13, 2026
Practice key: [1] one description of record · [2] every URL answers · [3] auth stated plainly · [4] demo with nothing set up · [5] assets to spec · [6] version tied to the card · [7] no "signed", acronyms spelled out

## Connector identity
- Connector name: Capital Markets Knowledge Graph — Allooloo [1]
- Short tagline (under 80 chars): KYP Agentic Trading with the Capital Markets Knowledge Graph [1]
- Developer / organization: Allooloo Technologies Corp. [5]
- Website: https://allooloo.io [2]
- Documentation: https://capitalmarketsknowledgegraph.ai/ [2]
- Category: Finance · Data & research · Compliance
- Version: registry card io.github.allooloo/cm-kg 0.12.0 [6]

## Description (paste verbatim) [1][7]
What: KYP Agentic Trading with the Capital Markets Knowledge Graph — one public-record file per listed company across eleven national markets, identity through disclosure trail, each field carrying its source and the date it was read, served from the issuer's own jurisdiction over the Model Context Protocol (MCP) and the Agent-to-Agent protocol (A2A).

Why: So an agent acting for a licensed capital markets participant with a Know Your Product (KYP) obligation hands back a fact that can be defended. The KYP model runs on this record. No prices, no quotes, no licensed data.

Markets: Canada, United States, United Kingdom, France, Netherlands, Switzerland, Germany, Australia, Singapore, Japan, South Korea. Hong Kong is a beacon.

## Server
- MCP server URL: https://mcp.capitalmarketsknowledgegraph.ai/mcp [2]
- Transport: Streamable HTTP (JSON-RPC over HTTPS) [3]
- Authentication: None on the public door — read-only, no key, no account. Licensed routes are gated by Agentic Registries (OAuth 2.0; authorization server metadata at https://agentic-registries.ai/.well-known/oauth-authorization-server; agent guidance at https://agentic-registries.ai/auth.md). [3][2]
- OpenAPI (service description): https://mcp.capitalmarketsknowledgegraph.ai/openapi.json [2]
- MCP server card: https://capitalmarketsknowledgegraph.ai/.well-known/mcp/server-card.json [2]
- A2A agent card: https://capitalmarketsknowledgegraph.ai/.well-known/agent-card.json [2]
- llms.txt: https://allooloo.io/llms.txt [2]
- Data residency: records stored and served in the issuer's own jurisdiction; eleven Azure regions; the apex router holds an index and forwards, nothing more.

## Tools [1]
| Tool | What it does |
|---|---|
| resolve_issuer | Find a listed company by ticker (with exchange prefix or suffix), International Securities Identification Number (ISIN), Legal Entity Identifier (LEI), legal name or sourced alias; returns the record summary, node and version |
| get_record | Return the full Capital Markets Record for an issuer, every field with its source URL and read date |
| list_events_since | Dated, sourced disclosure events for an issuer since a date |
| list_aliases | Sourced trade and former names for an issuer |
| list_nodes | The twelve market nodes, which are live, their regional doors and agent cards |

## Demo — nothing to set up, runs in Claude with no key [4]
1. Add the connector: https://mcp.capitalmarketsknowledgegraph.ai/mcp
2. Ask: "Resolve the issuer LSE:BARC" → resolve_issuer returns Barclays PLC, node uk-cm-kg, record version.
3. Ask: "Read its record" → get_record returns the file with a source URL and read date on every field.
4. Ask: "What has it disclosed since 2026-06-01?" → list_events_since returns the dated, sourced trail.
5. Ask: "Which markets are live?" → list_nodes returns eleven live nodes and the Hong Kong beacon.
Expected time: under two minutes. No prices or quotes are returned at any step — that is by design.

## Policies and support [2]
- Privacy: https://allooloo.io/privacy
- Terms of use: https://allooloo.io/terms
- Security / responsible disclosure: https://allooloo.io/security
- Status: https://allooloo.io/status
- Support: contact form at https://allooloo.io/#contact
- Contact email: mk@allooloo.ai [5]
- Operator header on every response: X-CMR-Operator: Allooloo Technologies Corp.

## Commercial [3]
- Public read: free, no registration.
- Per-record machine payment: x402 on Base, https://agentic-x402.ai/ (documentation and live endpoint).
- Firm-wide use: signed licence — Dealer MCP access, Issuer record, Knowledge Graph API, Node operator. Licence only, no services.

## Assets [5]
- Logo (square, 400×400): C:\ALLOOLOO\SITE\avatar-400.png
- Logo (vector): C:\ALLOOLOO\SITE\allooloo-logo.svg (dark variant allooloo-logo-dark.svg)
- Icon (512): https://capitalmarketsknowledgegraph.ai/icon-512.png
- Company name for the form, exactly: Allooloo Technologies Corp.
- Location: Vancouver & Toronto, Canada

## Notes for the submitter
- The agent card at the apex currently reports version 0.11.0 while the registry card is 0.12.0; if the form asks for one number, use the registry card (0.12.0) and ask CC to bump the apex card to match. [6]
- Do not write "signed" anywhere on the form; records are confirmed against the public filing. [7]
