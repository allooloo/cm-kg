# LISTINGS — Allooloo doors — report (CC to CEO, Sept 13 2026, ~17:45 UTC)

Build log: `START_ME_UP\X402-TO100-BUILD-LOG.md` item 33. Commits `e2d5892` and the close. Surfaces 2026-09-13.9.

## 1. MCP Registry — io.github.allooloo/cm-kg, same card, now 0.12.0

- Confirmed current before the update: apex door `https://mcp.capitalmarketsknowledgegraph.ai/mcp` (streamable-http), five tools (resolve_issuer, get_record, list_events_since, list_aliases, list_nodes), description of record "Know every Canadian and UK issuer, agent-ready. Instantly. Provably. Eleven markets, in-country." The live card carried no "signed" anywhere; the new card states it: records confirmed against the public filing, not signed by it (a `confirmed` line in the metadata).
- Added to the card's publisher-provided metadata: `x402` (endpoint agentic-x402.ai/api, price $0.01 USDC, network eip155:8453, scheme exact/EIP-3009, trades record route, receipts pattern, jwks) and `registries_gate` (authorization server, metadata, register, token, auth.md, grants, licensed routes). Mojibake em-dashes in the older description_of_record fixed.
- Published as version 0.12.0 ("Successfully published"). The registry's 4 KB metadata cap bit once (4,296 bytes); trimmed to 3,915 and republished. Login: the stored registry JWT had expired; re-login with the allooloo GitHub token (no browser). Old card kept beside the new: `CM-KG\DOOR\server-0.11.0.json`.
- Registry version of record: **0.12.0** (0.11.0 and earlier stay as history on the same card).

## 2. Azure API Center — allooloo-apic (Allooloo subscription, eastus)

Tenant checked (04a24e43…). No cross-estate entries added. Entries now:

| API | kind | version | OpenAPI definition (imported by link from the door's own spec) | deployment |
|---|---|---|---|---|
| cm-kg-ca … cm-kg-kr (eleven node doors) | mcp | v0-11-0 | `https://mcp.<cc>-cm-kg.ai/openapi.json` — import accepted, export reads back "cm-kg <cc>-cm-kg door" | prod → `https://mcp.<cc>-cm-kg.ai/mcp` |
| cm-kg-apex | mcp | v0-11-0 | `https://mcp.capitalmarketsknowledgegraph.ai/openapi.json` — reads back "cm-kg apex router" | prod → apex `/mcp` |
| agentic-x402-api (new) | rest | v1 | `https://agentic-x402.ai/openapi.json` (authored this order: /api, /x402/jwks.json, /x402/receipt/{nonce}) — reads back "Agentic x402 — a paid call with a signed receipt" | prod → `https://agentic-x402.ai/api` |

- Corrections made on the way: the twelve MCP entries' externalDocumentation "openapi" links were malformed (`https://openapi.json.<host>/openapi.json`) — repointed to the doors' real specs; the apex entry's title said "Canada" — now "apex router".
- Not touched: `swagger-petstore` (the API Center sample, cross-estate by nature). Flagged for your deletion order; nothing deleted.
- Count: 13 Allooloo entries (12 MCP + 1 REST), 13 OpenAPI definitions, 13 production deployments.

## 3. x402 Bazaar — Coinbase CDP discovery

- Both paid resources now carry the Bazaar discovery extension in their 402 (x402 v2 `extensions.bazaar`: input method/params, output example, schema) with a description under 500 characters, price, network eip155:8453, and the receipt URL pattern:
  - `https://agentic-x402.ai/api` (GET, optional `?record=node/exchange/code`)
  - `https://agentic-trades.ai/x402/record/{node}/{exchange}/{code}` (GET, path params node · exchange · code)
- CDP's validation endpoint reads both and returns the extension (`bazaarExtension` populated, no errors) — the resources are valid for listing.
- How the Bazaar indexes: on the first **settled call through the CDP facilitator** on mainnet (documented; testnet and other facilitators do not count). Both routes settle through CDP with the rotated key. That first $0.01 mainnet call is your hand:

```
node x402_pay.mjs https://agentic-x402.ai/api
```

- Listing URLs (public, no key): `https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources` (all; paginated) — the entries will show `resource: https://agentic-x402.ai/api` and `resource: https://agentic-trades.ai/x402/record/…`; per-merchant view via the CDP SDK `listX402DiscoveryMerchant` with your pay-to address. `agentic-x402.ai/api` present since the 18:10 UTC settlement; the trades route follows its own first settled call. Delisting rule: 30 days without a settlement.

## HITL

1. Bazaar: both resources indexed by CDP (validate `index.active`); the public list shows `/api`, the trades route pending in the list — scheduled check 21:30 UTC.
2. `swagger-petstore` in API Center — sample entry, delete on your paste.
3. Standing from earlier: DNSSEC landing check (fires 18:30 UTC), webMcp, Web Analytics beacon, door image agent cards, legal sign-off, Zone Analytics scope, ch/kr gap, Azure cost, Anthropic admin key.

## Counts and spend

- Registry: 1 card, version 0.12.0, 5 tools, 11 live nodes, 2 new metadata blocks.
- API Center: 13 entries · 13 OpenAPI imports · 12 doc-link corrections · 1 title correction · 0 deletions.
- Bazaar: 2 resources validated; `agentic-x402.ai/api` INDEXED after the CEO's mainnet call (18:10 UTC; in the discovery list); the trades record route lists on its own first settled call (CEO's hand).
- Spend: no engine calls; Azure API Center within the free tier; Cloudflare $0 incremental; x402 mainnet settled $0.02 (two calls: /api receipt 772c00ad…, trades route tx 0xcea5…7f10).
