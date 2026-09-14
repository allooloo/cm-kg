# AEO SWEEP — report (CC to CEO, Sept 13 2026)

Order: `START_ME_UP_5` (`ALLOOLOO_START_ME_UP_5_AGENT_READINESS_AEO.md` v1.0). Build log: `START_ME_UP\AEO-BUILD-LOG.md` items 1–12. Surfaces **2026-09-13.15** on all 23 (two rolls: .14, .15). Snapshots `POND\estate\surfaces\2026-09-13-13` and `-14`. Scans: `AZURE\aeo-scan-2026-09-13-{baseline,after14,after15}\`.

## Done means (§8) — where it stands

- **23 of 23 surfaces Level 5 Agent-Native.** 22 checks on the scanner, none new, none gone.
- **Every check that the wire can carry passes on every surface:** 16 of the 17 scored checks on 19 surfaces, **17 of 17 on the four zones whose DNSSEC DS has landed** (kyp-model.ai, agentic-disclosure.ai, agentic-registries.ai, agentic-radar.ai). The one remaining fail is `dnsAid` on the other 19 — the DS is published by Cloudflare Registrar on its own clock; records and DNSSEC are in place and the four landed zones prove the shape passes. Not chased.
- **Commerce scored on every surface:** `x402` PASS on 23 of 23 ("x402 payment protocol detected on /api", v2, scheme exact, eip155:8453). The four other commerce protocols stay neutral by design (see the §17 finding below).
- **webMcp** fail→pass on 23 of 23: one script by ruling, registering the contact form as the surface's one tool (`contact_us`).
- Twins: what a 301 zone can carry is DNSSEC + DNS-AID records; the rail for the ~60 twin zones was refused by the permission classifier (DNS change) — your word (HITL 1).

## Per-surface, before → after (isitagentready.com, pass · neutral · fail of 22)

| surface | before | after (.15) | moved |
|---|---|---|---|
| allooloo.io | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| agentic-trades.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| agentic-ask.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| agentic-coverage.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| agentic-esg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| agentic-issuers.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| agentic-disclosure.ai | 15 · 6 · 1 | **17 · 5 · 0** | webMcp → pass, x402 → pass |
| agentic-registries.ai | 15 · 6 · 1 | **17 · 5 · 0** | webMcp → pass, x402 → pass |
| agentic-radar.ai | 15 · 6 · 1 | **17 · 5 · 0** | webMcp → pass, x402 → pass |
| agentic-x402.ai | 15 · 5 · 2 | **16 · 5 · 1** | webMcp → pass (x402 already pass) |
| kyp-model.ai | 15 · 6 · 1 | **17 · 5 · 0** | webMcp → pass, x402 → pass |
| ca-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| us-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| uk-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| fr-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| nl-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| ch-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| de-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| au-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| sg-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| jp-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| kr-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |
| hk-cm-kg.ai | 14 · 6 · 2 | **16 · 5 · 1** | webMcp → pass, x402 → pass |

The one fail on the 16 · 5 · 1 rows is `dnsAid` (DS pending). The five neutrals everywhere are webBotAuth (informational) and mpp · ucp · acp · ap2 (not answered, so not declared). The API returns no numeric score; the site's UI number is its rendering of the same 22 checks.

## The seventeen checks (§4) — what changed on the wire this order

1–3 robots.txt / sitemap / llms.txt: robots.txt gains `Agentmap:` (ARD) and an llms.txt pointer; `/api` in every sitemap; llms.txt line 13 "Paid door" on every surface. 4 Link headers: now ten entries — llms.txt, markdown twin, agent card, api-catalog, mcp server card (both paths), ai-catalog, ard, service-desc, and the keyring (agentic-x402.ai/x402/jwks.json). 5 markdown twin unchanged. 6 `Content-Signal` is now also a response header on every response, agreeing with robots.txt. 7 AI-bot posture read back on all 23 zones (protection disabled, crawler protection disabled, fight mode off) and four crawler user-agents 200 everywhere — nothing to change. 8 mcp.json carries `scope` (node: `<node> only`; product: its title). 9–10 unchanged (pass). 11 ARD rebuilt to the spec: host block (did:web), publisher, seven entries with `urn:air:<host>:…` identifiers (7 of 7 conformant on the scanner), IANA types, 2–4 representativeQueries each, a paid-call entry; also at `/.well-known/ard.json`. 12 WebMCP: `public/webmcp.js`, one script, one tool. 13 `/.well-known/skills.json` alias of the skills index. 14 DNS-AID: records in place; DS landing is the registrar's clock (4 of 23 landed). 15 security.txt unchanged. 16 x402: `/api` answers 402 on every surface — same facilitator (Coinbase CDP, Base mainnet), same payTo, same receipt key, $0.01; the settled call returns the surface's own one-resource statement (node: its list_nodes line; product: its record of record; allooloo.io: the estate scale block) and an EdDSA receipt that resolves on the surface that served it (`/x402/receipt/{nonce}`, key at `/x402/jwks.json`); every settlement counts on RADAR's paid-calls line. 17 see the finding.

## Finding — §17 offer signals, withdrawn on the evidence

The scanner counts schema.org `Product` and `Offer` in the head as two commerce signals and flips a surface to "commerce" at three. With the Offer markup in (.14), agentic-x402.ai (already carrying `prices:multiple`) and ca-cm-kg.ai (carrying `platform:shopify` + `meta:shopify` because its captured wire example is TSX:SHOP, Shopify Inc.) flipped, and mpp · ucp · acp · ap2 went neutral→fail on both (16 · 1 · 5). Withdrawn estate-wide in .15; the offer data stays where machines read it (ARD paid-call entry, agent card `x-cmkg.x402`, the 402 body). AP2 is not declared on any Agent Card: no AP2 mandate is answered, and §6 says nothing invented. If you want Commerce to count in the denominator (isCommerce true), the price is four fails until those four protocols are answered — your call.

## Counts

- Surfaces: 23 at 2026-09-13.15 · rolls 2 · snapshots 2 (87 files each) · scans 3 × 23 + 1 (radar rescan) · check names 22 → 22
- Pass moves: webMcp 23 · x402 22 · fails removed 45 · fails added 0 (the two commerce flips in .14 reverted in .15)
- New paths on every surface: `/api` · `/x402/jwks.json` · `/x402/receipt/{nonce}` · `/webmcp.js` · `/.well-known/ard.json` · `/.well-known/skills.json`
- Rails: `aeo_scan.py` · `aeo_diff.py` · `aeo_weekly.py` · `bot_posture.py` · `dnssec_check.py` (landed test fixed)
- Cadence: "Allooloo AEO weekly scan" Sunday 12:00 build-machine time (18:00 UTC), exceptions only to `AEO-BUILD-LOG.md`

## HITL

1. **Twins** — `RAILS\twin_dns.py` (DNSSEC on + DNS-AID `_agents` records on the ~60 twin zones, additive, pointing at the canonical surface and its doors) was refused by the permission classifier as a DNS change and the file was not written. Allow the DNS write (a Bash permission rule) or run it by your hand; the design is in build-log item 11.
2. **DNSSEC landing** — 19 of 23 pending at Cloudflare Registrar; a one-off Sept 14 check was refused as persistence. The Sunday scan will report the flips; nothing for you to do at the registrar.
3. **Paid door proof on a non-x402 surface** — one mainnet $0.01 call from your wallet, e.g. `node x402_pay.mjs https://uk-cm-kg.ai/api` from `CM-KG\RAILS`; CC ran none (mainnet is your hand). The receipt then resolves at uk-cm-kg.ai/x402/receipt/{nonce} and RADAR counts it.
4. **ARD media type** — the scanner's `correctMediaType` flag is false under both `application/json` and `application/ard+json`; the check passes; left at ard+json (spec name) until the scanner publishes what it wants.
5. Standing from earlier orders: Cloudflare Web Analytics beacon on allooloo.io (today's fetch shows one script only, no beacon injected); listings; legal@ sign-off; Zone Analytics Read scope; ch/kr gap; Azure cost figure; Anthropic admin key; door `booted` rename.

## Spend line

No LLM engine calls this order (scans, deploys, DNS reads, wire reads only). Cloudflare Workers/DNS: within plan, $0 incremental. Azure: untouched. x402 settled this order: $0.00 (no paid call made). Tavily: 0 credits used this order; plan Growth, 93,727 of 100,000 used (API `/usage`). Anthropic balance: not readable (admin key HITL).
