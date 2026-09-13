# AGENTIC-X402.AI — 23rd surface — report (CC to CEO, Sept 13 2026, ~15:40 UTC)

Build log: `START_ME_UP\X402-TO100-BUILD-LOG.md` items 20–27. Commits `e6842ea`, next. Surfaces 2026-09-13.6 on all 23; snapshots `2026-09-13-6`, `-7`.

## FLAG FIRST — CDP secret exposed in the transcript, rotate it

While reading the shape of `AGENT KEYS\cdp-api-key-secret.txt` (to tell Ed25519 from PEM) CC's own check printed the secret, minus its last character, into the session transcript. That is a leak under the standing rule. The key works and is loaded on the Worker, and the mainnet facilitator answers with it, so the test can run now — but rotate it in the CDP portal at your convenience, drop the new secret in the same file, and CC re-uploads in one command. The key id, pay-to address and every other key stayed unprinted.

## Page live by fetch

- `https://agentic-x402.ai/` — 200, shared template, title "Agentic x402 for AI agents — a paid call with a signed receipt", H1 "One call, one cent, one receipt."; sections: what x402 is · what this endpoint does · the exchange (402 → signed authorization → 200 + receipt) · the 402 challenge as protocol fact · receipts · machine surfaces · identity headers · access · provenance · estate · machine kit · contact. No pay-to address on the page (checked). Markdown twin on `Accept: text/markdown` 200.
- `.com/.org/.io` → 301 → agentic-x402.ai, path preserved. Four zones bound to the estate Worker, SSL full (strict). AI-bot block: read back OFF on all four (protection disabled, fight mode off, crawler protection disabled).
- `X-CMR-X402: ready` on every response of all 23 surfaces (verified on agentic-x402.ai and a node). Every node and product agent card links the endpoint under `x-cmkg.x402` (endpoint, surface, price, receipts, jwks).
- Machine kit of record on the new host: llms.txt, facts.json, agent card, MCP server card, api-catalog, auth.md, AS metadata, robots, security.txt, sitemap listing `/api`. DNSSEC enabled and DNS-AID records on agentic-x402.ai; the 18:30 UTC landing check now covers 23 zones.
- isitagentready.com: agentic-x402.ai Level 5, 15 pass / 5 neutral / 2 fail; `commerce.x402` PASS ("x402 payment protocol detected on /api"). Fails are the estate-wide two: dnsAid (waits on DS) and webMcp (zero-script rule).

## Endpoint

- `GET https://agentic-x402.ai/api` (and `?record=node/exchange/code`) answers 402 with the offer in the body and the `PAYMENT-REQUIRED` header: scheme exact (EIP-3009 transferWithAuthorization), $0.01 USDC (10000 units), 60 s window, payTo from your file, resource stated. Network: **Base Sepolia** (testnet first, x402.org facilitator); mainnet on your word by one secret.
- What it buys: the estate index, or one Capital Markets Record — the same data the free routes serve.
- Receipts: EdDSA-signed JWT, kid `allooloo-x402-receipts-2026-09`, public key at `/x402/jwks.json`, stored forever, resolve at `/x402/receipt/{nonce}` (immutable, 404 for unknown). Every settlement counts on RADAR's paid-calls line with the receipt URL.
- Coinbase CDP is now the facilitator of record on Base mainnet (key id + secret loaded as Worker secrets; a dummy payment through the trades route reached CDP and was refused as invalid payload, not as unauthorized). The trades route `agentic-trades.ai/x402/record/…` rides mainnet; `/api` rides testnet until you say.

## One settled test with receipt URL — your leg

CC holds no wallet key and signs no transfer. The client is on disk: `CM-KG\RAILS\x402_pay.mjs`. From `C:\ALLOOLOO\CM-KG\RAILS`:

```
npm i x402-fetch viem
set X402_PRIVATE_KEY=<your Base Sepolia wallet key>
node x402_pay.mjs https://agentic-x402.ai/api
```

It prints the status, the PAYMENT-RESPONSE (tx hash, network, amount) and the receipt URL, never the key. Test USDC on Base Sepolia: the Circle faucet. For the mainnet trades route use a Base wallet with $0.01 USDC. When the first call lands, the receipt URL and RADAR line close this report.

## Counts

- 23 surfaces at 2026-09-13.6 · 4 zones bound · 3 forwards · 1 new endpoint · 2 receipt routes · 1 new header estate-wide · agent cards updated: 23
- Secrets on the Worker: X402_PAYTO, X402_NETWORK, X402_RECEIPT_JWK, CDP_API_KEY_ID, CDP_API_KEY_SECRET, OAUTH_JWK (values never printed except the flagged CDP secret)
- Settled calls: 0 (awaiting your wallet)

## HITL

1. **Rotate the CDP secret** (flag above); new file → one re-upload.
2. Run the settled test (client above); mainnet switch for `/api` on your word.
3. Door images: the Azure door agent cards (`agent.<cc>-cm-kg.ai`) get the x402 link at the next image build; the estate-served cards have it now.
4. Standing: Cloudflare Web Analytics beacon (the second `<script>` on every product page), webMcp, DNSSEC landing check at 18:30 UTC, listings, legal sign-off, Zone Analytics scope, ch/kr gap, Azure cost, Anthropic admin key, door `booted` rename.

## Spend line

No engine calls this order; Cloudflare $0 incremental (custom domains and DNS within plan); x402 settled $0.00; Tavily 0; Anthropic balance unreadable (admin key HITL).
